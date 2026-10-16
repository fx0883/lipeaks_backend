"""
客户管理模块模型层单元测试
覆盖 Customer、CustomerMemberRelation、CustomerTenantRelation 模型约束与业务方法。
"""
import datetime
from django.db import IntegrityError, transaction
from django.test import TestCase
from tenants.models import Tenant
from users.models import Member
from customers.models import Customer, CustomerMemberRelation, CustomerTenantRelation


class CustomerModelsTestCase(TestCase):
    """
    客户模型、客户-联系人关系、客户-租户关系模型单元测试
    """

    def setUp(self):
        self.tenant_a = Tenant.objects.create(name='Tenant A', code='tenant_a', status='active')
        self.tenant_b = Tenant.objects.create(name='Tenant B', code='tenant_b', status='active')
        self.tenant_c = Tenant.objects.create(name='Tenant C', code='tenant_c', status='active')

        self.member_1 = Member.objects.create_user(
            username='member_1',
            email='m1@example.com',
            phone='13800000001',
            password='password123',
            tenant=self.tenant_a
        )
        self.member_2 = Member.objects.create_user(
            username='member_2',
            email='m2@example.com',
            phone='13800000002',
            password='password123',
            tenant=self.tenant_a
        )

    def test_customer_create_and_soft_delete(self):
        """
        测试 Customer 创建、基本字段默认值与 soft_delete() 软删除状态联动
        """
        customer = Customer.objects.create(
            tenant=self.tenant_a,
            name='测试科技有限公司',
            type='enterprise',
            value_level='gold',
            status='active',
            company_size='medium'
        )
        self.assertFalse(customer.is_deleted)
        self.assertEqual(customer.status, 'active')
        self.assertIn('测试科技有限公司', str(customer))

        # 执行软删除
        customer.soft_delete()
        customer.refresh_from_db()
        self.assertTrue(customer.is_deleted)
        self.assertEqual(customer.status, 'inactive')

        # 默认 TenantManager 自动过滤已软删除记录，original_objects 仍可查出
        self.assertFalse(Customer.objects.filter(id=customer.id).exists())
        self.assertTrue(Customer.original_objects.filter(id=customer.id, is_deleted=True).exists())

    def test_customer_member_relation_unique_together(self):
        """
        测试 CustomerMemberRelation 的 (customer, member) 唯一性约束
        """
        customer = Customer.objects.create(tenant=self.tenant_a, name='唯一约束测试客户')
        CustomerMemberRelation.objects.create(
            tenant=self.tenant_a,
            customer=customer,
            member=self.member_1,
            role='采购经理',
            is_primary=True
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CustomerMemberRelation.objects.create(
                    tenant=self.tenant_a,
                    customer=customer,
                    member=self.member_1,
                    role='技术总监'
                )

    def test_customer_member_relation_primary_exclusivity(self):
        """
        测试 CustomerMemberRelation 设置 is_primary=True 时自动将同客户其他联系人置为 False，且不影响其他客户
        """
        customer_1 = Customer.objects.create(tenant=self.tenant_a, name='客户一号')
        customer_2 = Customer.objects.create(tenant=self.tenant_a, name='客户二号')

        rel_c1_m1 = CustomerMemberRelation.objects.create(
            tenant=self.tenant_a,
            customer=customer_1,
            member=self.member_1,
            role='负责人A',
            is_primary=True
        )
        rel_c2_m1 = CustomerMemberRelation.objects.create(
            tenant=self.tenant_a,
            customer=customer_2,
            member=self.member_1,
            role='客户二号主联系人',
            is_primary=True
        )

        # 为 customer_1 添加新的主要联系人 member_2
        rel_c1_m2 = CustomerMemberRelation.objects.create(
            tenant=self.tenant_a,
            customer=customer_1,
            member=self.member_2,
            role='负责人B',
            is_primary=True
        )

        rel_c1_m1.refresh_from_db()
        rel_c1_m2.refresh_from_db()
        rel_c2_m1.refresh_from_db()

        self.assertFalse(rel_c1_m1.is_primary)
        self.assertTrue(rel_c1_m2.is_primary)
        # 其他客户的主要联系人不受影响
        self.assertTrue(rel_c2_m1.is_primary)

    def test_customer_tenant_relation_unique_together(self):
        """
        测试 CustomerTenantRelation 的 (customer, tenant, relation_type) 唯一性约束
        """
        customer = Customer.objects.create(tenant=self.tenant_a, name='租户关系唯一性客户')
        CustomerTenantRelation.objects.create(
            customer=customer,
            tenant=self.tenant_a,
            relation_type='client',
            is_primary=True
        )

        # 相同 (customer, tenant, relation_type) 抛 IntegrityError
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CustomerTenantRelation.objects.create(
                    customer=customer,
                    tenant=self.tenant_a,
                    relation_type='client',
                    is_primary=False
                )

        # 相同 (customer, tenant) 但不同 relation_type 允许创建
        rel_partner = CustomerTenantRelation.objects.create(
            customer=customer,
            tenant=self.tenant_a,
            relation_type='partner',
            is_primary=True
        )
        self.assertEqual(rel_partner.relation_type, 'partner')

    def test_customer_tenant_relation_primary_exclusivity_by_type(self):
        """
        测试 CustomerTenantRelation 按 relation_type 同类型 is_primary=True 自动排他，不同类型互不影响
        """
        customer = Customer.objects.create(tenant=self.tenant_a, name='多租户关系客户')

        rel_client_a = CustomerTenantRelation.objects.create(
            customer=customer,
            tenant=self.tenant_a,
            relation_type='client',
            is_primary=True
        )
        rel_partner_a = CustomerTenantRelation.objects.create(
            customer=customer,
            tenant=self.tenant_a,
            relation_type='partner',
            is_primary=True
        )

        # 新增同为 client 类型的主要关系 (tenant_b)
        rel_client_b = CustomerTenantRelation.objects.create(
            customer=customer,
            tenant=self.tenant_b,
            relation_type='client',
            is_primary=True
        )

        rel_client_a.refresh_from_db()
        rel_client_b.refresh_from_db()
        rel_partner_a.refresh_from_db()

        # 同为 client 类型的旧关系变为 False
        self.assertFalse(rel_client_a.is_primary)
        self.assertTrue(rel_client_b.is_primary)
        # partner 类型的关系保持 True
        self.assertTrue(rel_partner_a.is_primary)

    def test_customer_tenant_relation_is_active(self):
        """
        测试 CustomerTenantRelation.is_active() 在长期有效、生效期、未来开始、已过期下的判断
        """
        customer = Customer.objects.create(tenant=self.tenant_a, name='有效期测试客户')
        today = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        tomorrow = today + datetime.timedelta(days=1)

        # 1. 无开始/结束日期（长期有效）
        rel_no_dates = CustomerTenantRelation.objects.create(
            customer=customer,
            tenant=self.tenant_a,
            relation_type='client'
        )
        self.assertTrue(rel_no_dates.is_active())

        # 2. 当前处于生效期内 (yesterday <= today <= tomorrow)
        rel_active = CustomerTenantRelation.objects.create(
            customer=customer,
            tenant=self.tenant_a,
            relation_type='partner',
            start_date=yesterday,
            end_date=tomorrow
        )
        self.assertTrue(rel_active.is_active())

        # 3. 未来才开始 (start_date = tomorrow)
        rel_future = CustomerTenantRelation.objects.create(
            customer=customer,
            tenant=self.tenant_b,
            relation_type='provider',
            start_date=tomorrow,
            end_date=tomorrow + datetime.timedelta(days=10)
        )
        self.assertFalse(rel_future.is_active())

        # 4. 已过期 (end_date = yesterday)
        rel_expired = CustomerTenantRelation.objects.create(
            customer=customer,
            tenant=self.tenant_c,
            relation_type='supplier',
            start_date=yesterday - datetime.timedelta(days=10),
            end_date=yesterday
        )
        self.assertFalse(rel_expired.is_active())

    def test_customer_relation_helper_methods(self):
        """
        测试 Customer 的 get_primary_tenant_relation、get_tenant_relations_by_type、get_all_tenants 辅助方法
        """
        customer = Customer.objects.create(tenant=self.tenant_a, name='辅助方法测试客户')

        rel_client_a = CustomerTenantRelation.objects.create(
            customer=customer,
            tenant=self.tenant_a,
            relation_type='client',
            is_primary=False
        )
        rel_client_b = CustomerTenantRelation.objects.create(
            customer=customer,
            tenant=self.tenant_b,
            relation_type='client',
            is_primary=True
        )
        rel_partner_c = CustomerTenantRelation.objects.create(
            customer=customer,
            tenant=self.tenant_c,
            relation_type='partner',
            is_primary=True
        )

        # get_primary_tenant_relation 指定类型与不指定类型
        primary_client = customer.get_primary_tenant_relation(relation_type='client')
        self.assertEqual(primary_client, rel_client_b)

        primary_partner = customer.get_primary_tenant_relation(relation_type='partner')
        self.assertEqual(primary_partner, rel_partner_c)

        primary_any = customer.get_primary_tenant_relation()
        self.assertIn(primary_any, [rel_client_b, rel_partner_c])

        primary_none = customer.get_primary_tenant_relation(relation_type='distributor')
        self.assertIsNone(primary_none)

        # get_tenant_relations_by_type
        client_relations = customer.get_tenant_relations_by_type('client')
        self.assertEqual(client_relations.count(), 2)
        self.assertCountEqual(list(client_relations), [rel_client_a, rel_client_b])

        # get_all_tenants
        all_tenants = customer.get_all_tenants()
        self.assertEqual(all_tenants.count(), 3)
        self.assertCountEqual(list(all_tenants), [self.tenant_a, self.tenant_b, self.tenant_c])
