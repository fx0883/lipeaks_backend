"""
客户管理模块视图与 API 集成测试
覆盖 CustomerViewSet、CustomerMemberRelationViewSet、CustomerTenantRelationViewSet、TenantCustomerViewSet。
"""
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from tenants.models import Tenant
from users.models import User, Member
from customers.models import Customer, CustomerMemberRelation, CustomerTenantRelation
from common.authentication.jwt_auth import generate_jwt_token


def _unwrap_data(resp_data):
    """兼容标准响应包装器或原始 DRF 响应数据提取"""
    if isinstance(resp_data, dict) and 'data' in resp_data and 'code' in resp_data:
        return resp_data['data']
    return resp_data


@override_settings(ALLOWED_HOSTS=['*'])
class CustomerViewSetAPITestCase(TestCase):
    """
    CustomerViewSet 标准 CRUD、防重校验、搜索、统计与批量操作 API 测试
    """

    def setUp(self):
        self.tenant_a = Tenant.objects.create(name='Tenant A', code='tenant_a', status='active')
        self.tenant_b = Tenant.objects.create(name='Tenant B', code='tenant_b', status='active')

        self.admin_a = User.objects.create_user(
            username='admin_a',
            email='admin_a@example.com',
            password='password123',
            tenant=self.tenant_a,
            is_admin=True
        )
        self.normal_user = User.objects.create_user(
            username='normal_user',
            email='normal@example.com',
            password='password123',
            tenant=self.tenant_a,
            is_admin=False
        )

        self.customer_1 = Customer.objects.create(
            tenant=self.tenant_a,
            name='阿尔法科技',
            type='enterprise',
            value_level='platinum',
            status='active',
            company_size='large',
            primary_contact_name='张伟',
            primary_contact_phone='13811112222',
            primary_contact_email='zhangwei@alpha.com',
            tax_identification_number='91110108MA001111XX'
        )
        self.customer_2 = Customer.objects.create(
            tenant=self.tenant_a,
            name='贝塔教育',
            type='education',
            value_level='gold',
            status='potential',
            company_size='medium',
            primary_contact_name='李娜',
            primary_contact_phone='13933334444',
            primary_contact_email='lina@beta.edu.cn',
            tax_identification_number='91110108MA002222YY'
        )

        self.client = APIClient()
        self.token_admin_a = generate_jwt_token(self.admin_a)['access_token']
        self.token_normal = generate_jwt_token(self.normal_user)['access_token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin_a}')

    def test_non_admin_forbidden(self):
        """测试非管理员用户访问 CustomerViewSet 被 403 拒绝"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_normal}')
        resp = self.client.get('/api/v1/customers/')
        self.assertEqual(resp.status_code, 403)

    def test_customer_crud_and_soft_delete(self):
        """测试客户的创建、列表查询、详情获取、更新与软删除"""
        # 1. 创建客户
        create_payload = {
            'name': '伽马医疗有限',
            'type': 'enterprise',
            'value_level': 'silver',
            'status': 'active',
            'company_size': 'small',
            'primary_contact_name': '王五',
            'primary_contact_phone': '13755556666'
        }
        resp_create = self.client.post('/api/v1/customers/', create_payload, format='json')
        self.assertEqual(resp_create.status_code, 201)
        created_data = _unwrap_data(resp_create.data)
        self.assertEqual(created_data['name'], '伽马医疗有限')
        self.assertEqual(created_data['created_by'], 'admin_a')
        customer_id = created_data['id']

        # 为新创建的客户绑定租户以便后续租户隔离查询
        Customer.original_objects.filter(id=customer_id).update(tenant=self.tenant_a)

        # 2. 获取详情
        resp_detail = self.client.get(f'/api/v1/customers/{customer_id}/')
        self.assertEqual(resp_detail.status_code, 200)
        self.assertEqual(_unwrap_data(resp_detail.data)['name'], '伽马医疗有限')

        # 3. PATCH 部分更新
        resp_patch = self.client.patch(
            f'/api/v1/customers/{customer_id}/',
            {'notes': '战略合作客户', 'value_level': 'gold'},
            format='json'
        )
        self.assertEqual(resp_patch.status_code, 200)
        patched_data = _unwrap_data(resp_patch.data)
        self.assertEqual(patched_data['value_level'], 'gold')
        self.assertEqual(patched_data['updated_by'], 'admin_a')

        # 4. DELETE 软删除
        resp_del = self.client.delete(f'/api/v1/customers/{customer_id}/')
        self.assertEqual(resp_del.status_code, 204)

        deleted_obj = Customer.original_objects.get(id=customer_id)
        self.assertTrue(deleted_obj.is_deleted)
        self.assertEqual(deleted_obj.status, 'inactive')

    def test_customer_duplicate_name_validation(self):
        """测试客户名称防重校验：未删除同名客户拒绝，软删除同名客户允许"""
        # 1. 同名未删除客户拒绝创建
        resp_dup = self.client.post('/api/v1/customers/', {
            'name': '阿尔法科技',
            'type': 'enterprise',
            'value_level': 'gold',
            'status': 'active'
        }, format='json')
        self.assertEqual(resp_dup.status_code, 400)

        # 2. 将阿尔法科技软删除后，允许同名重建
        self.customer_1.soft_delete()
        resp_recreate = self.client.post('/api/v1/customers/', {
            'name': '阿尔法科技',
            'type': 'enterprise',
            'value_level': 'gold',
            'status': 'active'
        }, format='json')
        self.assertEqual(resp_recreate.status_code, 201)

    def test_customer_list_filters_and_show_deleted_param(self):
        """测试客户列表按字段过滤及 ?show_deleted=true 参数"""
        # 按 type 过滤
        resp_type = self.client.get('/api/v1/customers/?type=education')
        self.assertEqual(resp_type.status_code, 200)
        results = _unwrap_data(resp_type.data).get('results', [])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name'], '贝塔教育')

        # 软删除后默认不出现在列表中
        self.customer_2.soft_delete()
        resp_default = self.client.get('/api/v1/customers/')
        default_names = [c['name'] for c in _unwrap_data(resp_default.data).get('results', [])]
        self.assertNotIn('贝塔教育', default_names)

        # 携带 show_deleted=true 参数请求正常响应
        resp_show_deleted = self.client.get('/api/v1/customers/?show_deleted=true')
        self.assertEqual(resp_show_deleted.status_code, 200)

    def test_customer_search_action(self):
        """测试 search 动作：多字段模糊搜索与空参数 400 拦截"""
        # 1. 空参数返回 400
        resp_empty = self.client.get('/api/v1/customers/search/')
        self.assertEqual(resp_empty.status_code, 400)

        # 2. 按客户名称搜索
        resp_name = self.client.get('/api/v1/customers/search/?q=阿尔法')
        self.assertEqual(resp_name.status_code, 200)
        results_name = _unwrap_data(resp_name.data).get('results', [])
        self.assertEqual(len(results_name), 1)
        self.assertEqual(results_name[0]['id'], self.customer_1.id)

        # 3. 按联系人手机号搜索
        resp_phone = self.client.get('/api/v1/customers/search/?q=1393333')
        self.assertEqual(resp_phone.status_code, 200)
        results_phone = _unwrap_data(resp_phone.data).get('results', [])
        self.assertEqual(len(results_phone), 1)
        self.assertEqual(results_phone[0]['id'], self.customer_2.id)

        # 4. 按税号搜索
        resp_tax = self.client.get('/api/v1/customers/search/?q=MA001111XX')
        self.assertEqual(resp_tax.status_code, 200)
        results_tax = _unwrap_data(resp_tax.data).get('results', [])
        self.assertEqual(len(results_tax), 1)
        self.assertEqual(results_tax[0]['id'], self.customer_1.id)

    def test_customer_statistics_action(self):
        """测试 statistics 分类聚合统计接口"""
        resp = self.client.get('/api/v1/customers/statistics/')
        self.assertEqual(resp.status_code, 200)
        stats = _unwrap_data(resp.data)
        self.assertEqual(stats['total_count'], 2)
        self.assertEqual(stats['active_count'], 1)
        self.assertEqual(stats['potential_count'], 1)
        self.assertEqual(stats['by_type']['enterprise'], 1)
        self.assertEqual(stats['by_type']['education'], 1)
        self.assertEqual(stats['by_value_level']['platinum'], 1)
        self.assertEqual(stats['by_value_level']['gold'], 1)

    def test_customer_bulk_create_update_delete(self):
        """测试批量创建、批量更新、批量软删除及异常校验（重名、缺失id、空ids）"""
        # 1. 批量创建内部重名 -> 400
        resp_dup_internal = self.client.post('/api/v1/customers/bulk-create/', {
            'customers': [
                {'name': '同名批量客户', 'type': 'enterprise', 'value_level': 'silver', 'status': 'active'},
                {'name': '同名批量客户', 'type': 'individual', 'value_level': 'bronze', 'status': 'active'},
            ]
        }, format='json')
        self.assertEqual(resp_dup_internal.status_code, 400)

        # 2. 批量创建与数据库已有客户重名 -> 400
        resp_dup_db = self.client.post('/api/v1/customers/bulk-create/', {
            'customers': [
                {'name': '阿尔法科技', 'type': 'enterprise', 'value_level': 'silver', 'status': 'active'},
            ]
        }, format='json')
        self.assertEqual(resp_dup_db.status_code, 400)

        # 3. 批量创建成功 -> 201
        resp_bulk_create = self.client.post('/api/v1/customers/bulk-create/', {
            'customers': [
                {'name': '批量客户A', 'type': 'enterprise', 'value_level': 'silver', 'status': 'active'},
                {'name': '批量客户B', 'type': 'individual', 'value_level': 'bronze', 'status': 'potential'},
            ]
        }, format='json')
        self.assertEqual(resp_bulk_create.status_code, 201)
        created_list = _unwrap_data(resp_bulk_create.data)
        self.assertEqual(len(created_list), 2)
        bulk_ids = [item['id'] for item in created_list]
        Customer.original_objects.filter(id__in=bulk_ids).update(tenant=self.tenant_a)

        # 4. 批量更新缺失 id -> 400
        resp_update_no_id = self.client.post('/api/v1/customers/bulk-update/', {
            'customers': [
                {'name': '缺少ID的客户', 'status': 'inactive'}
            ]
        }, format='json')
        self.assertEqual(resp_update_no_id.status_code, 400)

        # 5. 批量更新成功 -> 200
        resp_bulk_update = self.client.post('/api/v1/customers/bulk-update/', {
            'customers': [
                {'id': bulk_ids[0], 'name': '批量客户A_已更新', 'status': 'active'},
                {'id': bulk_ids[1], 'status': 'lost'},
            ]
        }, format='json')
        self.assertEqual(resp_bulk_update.status_code, 200)
        updated_list = _unwrap_data(resp_bulk_update.data)
        self.assertEqual(len(updated_list), 2)

        # 6. 批量软删除空 ids -> 400
        resp_del_empty = self.client.post('/api/v1/customers/bulk-delete/', {'ids': []}, format='json')
        self.assertEqual(resp_del_empty.status_code, 400)

        # 7. 批量软删除成功 -> 204
        resp_bulk_del = self.client.post('/api/v1/customers/bulk-delete/', {'ids': bulk_ids}, format='json')
        self.assertEqual(resp_bulk_del.status_code, 204)
        for bid in bulk_ids:
            obj = Customer.original_objects.get(id=bid)
            self.assertTrue(obj.is_deleted)
            self.assertEqual(obj.status, 'inactive')


@override_settings(ALLOWED_HOSTS=['*'])
class CustomerRelationsAndTenantViewTestCase(TestCase):
    """
    CustomerMemberRelationViewSet、CustomerTenantRelationViewSet 与 TenantCustomerViewSet 集成测试
    """

    def setUp(self):
        self.tenant_a = Tenant.objects.create(name='Tenant A', code='tenant_a', status='active')
        self.tenant_b = Tenant.objects.create(name='Tenant B', code='tenant_b', status='active')

        self.admin_a = User.objects.create_user(
            username='admin_a',
            email='admin_a@example.com',
            password='password123',
            tenant=self.tenant_a,
            is_admin=True
        )
        self.member_1 = Member.objects.create_user(
            username='member_1',
            email='m1@example.com',
            phone='13800000011',
            password='password123',
            tenant=self.tenant_a
        )
        self.member_2 = Member.objects.create_user(
            username='member_2',
            email='m2@example.com',
            phone='13800000022',
            password='password123',
            tenant=self.tenant_a
        )

        self.customer_a = Customer.objects.create(
            tenant=self.tenant_a,
            name='关联客户A',
            type='enterprise',
            value_level='gold',
            status='active'
        )
        self.customer_unlinked = Customer.objects.create(
            tenant=self.tenant_a,
            name='未关联租户客户',
            type='individual',
            value_level='silver',
            status='active'
        )

        self.client = APIClient()
        self.token_admin_a = generate_jwt_token(self.admin_a)['access_token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin_a}')

    def test_customer_member_relation_endpoints(self):
        """
        测试 CustomerMemberRelationViewSet：创建、set-primary、primary、双向查询与批量解绑
        """
        # 1. 创建联系人关系 1 (主要联系人)
        resp_c1 = self.client.post('/api/v1/customers/members/relations/', {
            'customer_id': self.customer_a.id,
            'member_id': self.member_1.id,
            'role': 'CEO',
            'is_primary': True
        }, format='json')
        self.assertEqual(resp_c1.status_code, 201)
        rel_1_id = _unwrap_data(resp_c1.data)['id']

        # 2. 创建联系人关系 2 (非主要联系人)
        resp_c2 = self.client.post('/api/v1/customers/members/relations/', {
            'customer_id': self.customer_a.id,
            'member_id': self.member_2.id,
            'role': 'CTO',
            'is_primary': False
        }, format='json')
        self.assertEqual(resp_c2.status_code, 201)
        rel_2_id = _unwrap_data(resp_c2.data)['id']

        # 3. 调用 set-primary 将关系 2 设为主要联系人
        resp_set_primary = self.client.post(f'/api/v1/customers/members/relations/{rel_2_id}/set-primary/')
        self.assertEqual(resp_set_primary.status_code, 200)
        self.assertTrue(_unwrap_data(resp_set_primary.data)['is_primary'])

        # 4. 调用 primary 接口查询主要联系人
        resp_primary = self.client.get(
            f'/api/v1/customers/members/relations/primary/?customer_id={self.customer_a.id}'
        )
        self.assertEqual(resp_primary.status_code, 200)
        self.assertEqual(_unwrap_data(resp_primary.data)['member_id'], self.member_2.id)

        # 5. 查询 customer-members 与 member-customers
        resp_cm = self.client.get(
            f'/api/v1/customers/members/relations/customer-members/?customer_id={self.customer_a.id}'
        )
        self.assertEqual(resp_cm.status_code, 200)
        self.assertEqual(len(_unwrap_data(resp_cm.data)), 2)

        resp_mc = self.client.get(
            f'/api/v1/customers/members/relations/member-customers/?member_id={self.member_1.id}'
        )
        self.assertEqual(resp_mc.status_code, 200)
        self.assertEqual(len(_unwrap_data(resp_mc.data)), 1)

        # 6. 批量解绑客户的联系人关系
        resp_del_cm = self.client.post('/api/v1/customers/members/relations/customer-members/delete/', {
            'customer_id': self.customer_a.id,
            'member_ids': [self.member_1.id]
        }, format='json')
        self.assertEqual(resp_del_cm.status_code, 204)
        self.assertFalse(CustomerMemberRelation.objects.filter(id=rel_1_id).exists())

    def test_customer_tenant_relation_endpoints_and_date_validation(self):
        """
        测试 CustomerTenantRelationViewSet：end_date < start_date 校验、创建、set-primary、primary、between
        """
        # 1. end_date 早于 start_date -> 400
        resp_invalid_date = self.client.post('/api/v1/customers/tenants/relations/', {
            'customer_id': self.customer_a.id,
            'tenant_id': self.tenant_a.id,
            'relation_type': 'client',
            'start_date': '2026-10-10',
            'end_date': '2026-01-01'
        }, format='json')
        self.assertEqual(resp_invalid_date.status_code, 400)

        # 2. 正常创建客户-租户关系
        resp_create = self.client.post('/api/v1/customers/tenants/relations/', {
            'customer_id': self.customer_a.id,
            'tenant_id': self.tenant_a.id,
            'relation_type': 'client',
            'is_primary': False,
            'start_date': '2026-01-01',
            'end_date': '2026-12-31'
        }, format='json')
        self.assertEqual(resp_create.status_code, 201)
        rel_id = _unwrap_data(resp_create.data)['id']

        # 3. 调用 set-primary 设为主要租户关系
        resp_set_primary = self.client.post(f'/api/v1/customers/tenants/relations/{rel_id}/set-primary/')
        self.assertEqual(resp_set_primary.status_code, 200)
        self.assertTrue(_unwrap_data(resp_set_primary.data)['is_primary'])

        # 4. 查询客户的主要租户关系 primary
        resp_primary = self.client.get(
            f'/api/v1/customers/tenants/relations/primary/?customer_id={self.customer_a.id}&relation_type=client'
        )
        self.assertEqual(resp_primary.status_code, 200)
        self.assertEqual(_unwrap_data(resp_primary.data)['id'], rel_id)

        # 5. 查询特定客户与租户的关系 between
        resp_between = self.client.get(
            f'/api/v1/customers/tenants/relations/between/?customer_id={self.customer_a.id}&tenant_id={self.tenant_a.id}'
        )
        self.assertEqual(resp_between.status_code, 200)
        self.assertEqual(len(_unwrap_data(resp_between.data)), 1)

    def test_tenant_customer_view_isolation(self):
        """
        测试 TenantCustomerViewSet 租户视角隔离：
        仅返回与该租户建立关系的客户，访问未关联客户详情返回 404
        """
        CustomerTenantRelation.objects.create(
            customer=self.customer_a,
            tenant=self.tenant_a,
            relation_type='client',
            is_primary=True
        )

        # 1. 列表仅包含与 tenant_a 建立关联的 customer_a，不包含 customer_unlinked
        resp_list = self.client.get(f'/api/v1/customers/tenants/view/?tenant_id={self.tenant_a.id}')
        self.assertEqual(resp_list.status_code, 200)
        results = _unwrap_data(resp_list.data).get('results', [])
        returned_ids = [c['id'] for c in results]
        self.assertIn(self.customer_a.id, returned_ids)
        self.assertNotIn(self.customer_unlinked.id, returned_ids)

        # 2. 访问已关联客户详情 -> 200
        resp_detail_ok = self.client.get(
            f'/api/v1/customers/tenants/view/{self.customer_a.id}/?tenant_id={self.tenant_a.id}'
        )
        self.assertEqual(resp_detail_ok.status_code, 200)
        self.assertEqual(_unwrap_data(resp_detail_ok.data)['id'], self.customer_a.id)

        # 3. 访问未关联客户详情 -> 404
        resp_detail_404 = self.client.get(
            f'/api/v1/customers/tenants/view/{self.customer_unlinked.id}/?tenant_id={self.tenant_a.id}'
        )
        self.assertEqual(resp_detail_404.status_code, 404)

        # 4. 租户视角下的客户统计与关系列表
        resp_stats = self.client.get(
            f'/api/v1/customers/tenants/view/statistics/?tenant_id={self.tenant_a.id}'
        )
        self.assertEqual(resp_stats.status_code, 200)
        self.assertEqual(_unwrap_data(resp_stats.data)['total_count'], 1)

        resp_rels = self.client.get(
            f'/api/v1/customers/tenants/view/{self.customer_a.id}/relations/?tenant_id={self.tenant_a.id}'
        )
        self.assertEqual(resp_rels.status_code, 200)
        self.assertEqual(len(_unwrap_data(resp_rels.data)), 1)
