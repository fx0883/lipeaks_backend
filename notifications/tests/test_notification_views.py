"""
通知系统管理端与成员端视图 API 集成测试
覆盖 NotificationViewSet (管理端生命周期、接收者管理、发布广播、归档与统计)
以及 MemberNotificationViewSet (成员端列表过滤、详情自动已读、read/read-all/unread-count、草稿不可见)。
"""
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from tenants.models import Tenant
from users.models import User, Member
from applications.models import Application
from notifications.models import Notification, NotificationRecipient
from common.authentication.jwt_auth import generate_jwt_token


def _unwrap_data(resp_data):
    """兼容标准响应包装器或原始 DRF 响应数据提取"""
    if isinstance(resp_data, dict) and 'data' in resp_data and 'code' in resp_data:
        return resp_data['data']
    return resp_data


@override_settings(ALLOWED_HOSTS=['*'])
class AdminNotificationViewSetTestCase(TestCase):
    """
    管理端 NotificationViewSet (/api/v1/admin/notifications/) 集成测试
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

        self.app_a = Application.objects.create(
            tenant=self.tenant_a,
            name='App Alpha',
            code='app_alpha',
            status='active'
        )

        self.member_a1 = Member.objects.create_user(
            username='member_a1',
            email='a1@example.com',
            password='password123',
            tenant=self.tenant_a,
            is_active=True
        )
        self.member_a2 = Member.objects.create_user(
            username='member_a2',
            email='a2@example.com',
            password='password123',
            tenant=self.tenant_a,
            is_active=True
        )
        self.member_a_inactive = Member.objects.create_user(
            username='member_a_inactive',
            email='inactive@example.com',
            password='password123',
            tenant=self.tenant_a,
            is_active=False
        )
        self.member_b1 = Member.objects.create_user(
            username='member_b1',
            email='b1@example.com',
            password='password123',
            tenant=self.tenant_b,
            is_active=True
        )

        self.client = APIClient()
        self.token_admin_a = generate_jwt_token(self.admin_a)['access_token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_admin_a}')

    def test_admin_create_notification_and_scope_validation(self):
        """
        测试管理端创建通知：自动注入 tenant 与 created_by，以及 scope='application' 校验
        """
        # 1. 创建 scope='tenant' 通知成功
        resp = self.client.post('/api/v1/admin/notifications/', {
            'title': '系统维护通知',
            'content': '今晚进行系统升级',
            'scope': 'tenant',
            'notification_type': 'announcement',
            'priority': 'high',
            'send_email': False
        }, format='json')
        self.assertEqual(resp.status_code, 201)

        notice = Notification.objects.get(title='系统维护通知')
        self.assertEqual(notice.tenant, self.tenant_a)
        self.assertEqual(notice.created_by, self.admin_a)
        self.assertEqual(notice.status, 'draft')

        # 2. 创建 scope='application' 但未提供 application -> 400
        resp_invalid = self.client.post('/api/v1/admin/notifications/', {
            'title': '缺失应用的通知',
            'content': '内容',
            'scope': 'application'
        }, format='json')
        self.assertEqual(resp_invalid.status_code, 400)

        # 3. 创建 scope='application' 且提供 application -> 201
        resp_app = self.client.post('/api/v1/admin/notifications/', {
            'title': '应用专属通知',
            'content': 'App Alpha 更新',
            'scope': 'application',
            'application': self.app_a.id
        }, format='json')
        self.assertEqual(resp_app.status_code, 201)

    def test_admin_list_filters(self):
        """
        测试管理端通知列表按 scope、status、type、priority、application 筛选及跨租户隔离
        """
        n_a1 = Notification.objects.create(
            tenant=self.tenant_a,
            title='A租户草稿警告',
            content='C1',
            scope='tenant',
            notification_type='warning',
            priority='urgent',
            status='draft'
        )
        n_a2 = Notification.objects.create(
            tenant=self.tenant_a,
            title='A租户应用发布通知',
            content='C2',
            scope='application',
            application=self.app_a,
            notification_type='update',
            priority='normal',
            status='published'
        )
        # B 租户通知不应出现在 A 租户列表中
        Notification.objects.create(
            tenant=self.tenant_b,
            title='B租户通知',
            content='CB',
            scope='tenant',
            status='published'
        )

        # 按 type=warning & priority=urgent 过滤
        resp_1 = self.client.get('/api/v1/admin/notifications/?type=warning&priority=urgent')
        self.assertEqual(resp_1.status_code, 200)
        results_1 = _unwrap_data(resp_1.data).get('results', [])
        self.assertEqual(len(results_1), 1)
        self.assertEqual(results_1[0]['id'], n_a1.id)

        # 按 scope=application & application={app_a.id} & status=published 过滤
        resp_2 = self.client.get(
            f'/api/v1/admin/notifications/?scope=application&application={self.app_a.id}&status=published'
        )
        self.assertEqual(resp_2.status_code, 200)
        results_2 = _unwrap_data(resp_2.data).get('results', [])
        self.assertEqual(len(results_2), 1)
        self.assertEqual(results_2[0]['id'], n_a2.id)

    def test_admin_update_draft_only_restriction(self):
        """
        测试管理端编辑限制：仅 draft 状态可更新，published 或 archived 状态更新返回 400
        """
        notice = Notification.objects.create(
            tenant=self.tenant_a,
            title='初始草稿标题',
            content='初始内容',
            status='draft'
        )

        # 1. 草稿状态更新成功 -> 200
        resp_ok = self.client.patch(
            f'/api/v1/admin/notifications/{notice.id}/',
            {'title': '修改后的草稿标题'},
            format='json'
        )
        self.assertEqual(resp_ok.status_code, 200)
        notice.refresh_from_db()
        self.assertEqual(notice.title, '修改后的草稿标题')

        # 2. 改为 published 状态后再次更新 -> 400
        notice.status = 'published'
        notice.save()
        resp_pub_edit = self.client.patch(
            f'/api/v1/admin/notifications/{notice.id}/',
            {'title': '尝试篡改已发布通知'},
            format='json'
        )
        self.assertEqual(resp_pub_edit.status_code, 400)

        # 3. 改为 archived 状态后再次更新 -> 400
        notice.status = 'archived'
        notice.save()
        resp_arch_edit = self.client.patch(
            f'/api/v1/admin/notifications/{notice.id}/',
            {'title': '尝试篡改已归档通知'},
            format='json'
        )
        self.assertEqual(resp_arch_edit.status_code, 400)

    def test_admin_recipients_add_and_cross_tenant_filtering(self):
        """
        测试 scope='members' 手动添加接收者、跨租户与非活跃成员自动过滤、幂等去重及非 members 范围 400 拦截
        """
        notice_tenant = Notification.objects.create(
            tenant=self.tenant_a,
            title='租户范围通知',
            content='内容',
            scope='tenant',
            status='draft'
        )
        # 1. 非 members 范围调用 add-recipients 返回 400
        resp_wrong_scope = self.client.post(
            f'/api/v1/admin/notifications/{notice_tenant.id}/add-recipients/',
            {'member_ids': [self.member_a1.id]},
            format='json'
        )
        self.assertEqual(resp_wrong_scope.status_code, 400)

        # 2. 创建 scope='members' 通知并添加接收者（混入跨租户成员 member_b1 与停用成员 member_a_inactive）
        notice_members = Notification.objects.create(
            tenant=self.tenant_a,
            title='指定成员通知',
            content='内容',
            scope='members',
            status='draft'
        )
        resp_add = self.client.post(
            f'/api/v1/admin/notifications/{notice_members.id}/add-recipients/',
            {
                'member_ids': [
                    self.member_a1.id,
                    self.member_a2.id,
                    self.member_a_inactive.id,
                    self.member_b1.id,
                ]
            },
            format='json'
        )
        self.assertEqual(resp_add.status_code, 200)
        # 只有本租户活跃成员 member_a1 和 member_a2 被添加
        self.assertEqual(_unwrap_data(resp_add.data)['added_count'], 2)

        # 3. 重复添加相同成员应幂等（added_count 为 0）
        resp_add_dup = self.client.post(
            f'/api/v1/admin/notifications/{notice_members.id}/add-recipients/',
            {'member_ids': [self.member_a1.id]},
            format='json'
        )
        self.assertEqual(resp_add_dup.status_code, 200)
        self.assertEqual(_unwrap_data(resp_add_dup.data)['added_count'], 0)

    def test_admin_recipients_list_and_remove_validation(self):
        """
        测试接收者列表查询、软删除过滤及 remove-recipients 参数校验
        """
        notice_members = Notification.objects.create(
            tenant=self.tenant_a,
            title='接收者列表测试通知',
            content='内容',
            scope='members',
            status='draft'
        )
        r1 = NotificationRecipient.objects.create(
            tenant=self.tenant_a, notification=notice_members, member=self.member_a1
        )
        NotificationRecipient.objects.create(
            tenant=self.tenant_a, notification=notice_members, member=self.member_a2
        )

        # 1. 查看接收者列表，包含 2 位成员
        resp_list = self.client.get(f'/api/v1/admin/notifications/{notice_members.id}/recipients/')
        self.assertEqual(resp_list.status_code, 200)
        recip_results = _unwrap_data(resp_list.data).get('results', [])
        self.assertEqual(len(recip_results), 2)

        # 2. remove-recipients 空列表参数校验 -> 400
        resp_remove_empty = self.client.post(
            f'/api/v1/admin/notifications/{notice_members.id}/remove-recipients/',
            {'member_ids': []},
            format='json'
        )
        self.assertEqual(resp_remove_empty.status_code, 400)

        # 3. 软删除 r1 后，再次查询有效接收者列表仅剩 member_a2
        r1.soft_delete()
        resp_list_after = self.client.get(f'/api/v1/admin/notifications/{notice_members.id}/recipients/')
        recip_after = _unwrap_data(resp_list_after.data).get('results', [])
        self.assertEqual(len(recip_after), 1)
        self.assertEqual(recip_after[0]['member'], self.member_a2.id)

    def test_admin_publish_broadcast_and_non_draft_rejected(self):
        """
        测试 publish 发布动作：自动为本租户活跃成员生成接收记录，非草稿重复发布返回 400
        """
        notice = Notification.objects.create(
            tenant=self.tenant_a,
            title='全员广播通知',
            content='广播内容',
            scope='tenant',
            status='draft'
        )

        # 1. 发布草稿通知 -> 200
        resp_pub = self.client.post(f'/api/v1/admin/notifications/{notice.id}/publish/')
        self.assertEqual(resp_pub.status_code, 200)
        pub_data = _unwrap_data(resp_pub.data)
        self.assertEqual(pub_data['status'], 'published')
        self.assertIsNotNone(pub_data['published_at'])

        # 验证仅本租户活跃成员 (member_a1, member_a2) 自动生成了接收记录
        recipient_member_ids = list(
            NotificationRecipient.objects.filter(notification=notice).values_list('member_id', flat=True)
        )
        self.assertCountEqual(recipient_member_ids, [self.member_a1.id, self.member_a2.id])

        # 2. 对已发布通知重复调用 publish -> 400
        resp_repub = self.client.post(f'/api/v1/admin/notifications/{notice.id}/publish/')
        self.assertEqual(resp_repub.status_code, 400)

    def test_admin_archive_and_statistics(self):
        """
        测试 archive 归档动作（含重复归档 400）与 statistics 阅读率统计接口
        """
        notice = Notification.objects.create(
            tenant=self.tenant_a,
            title='统计与归档测试通知',
            content='内容',
            scope='tenant',
            status='published'
        )
        NotificationRecipient.objects.create(
            tenant=self.tenant_a, notification=notice, member=self.member_a1, is_read=True
        )
        NotificationRecipient.objects.create(
            tenant=self.tenant_a, notification=notice, member=self.member_a2, is_read=False
        )

        # 1. 查询统计信息：总数 2，已读 1，未读 1，阅读率 50.0%
        resp_stats = self.client.get(f'/api/v1/admin/notifications/{notice.id}/statistics/')
        self.assertEqual(resp_stats.status_code, 200)
        stats = _unwrap_data(resp_stats.data)
        self.assertEqual(stats['total_recipients'], 2)
        self.assertEqual(stats['read_count'], 1)
        self.assertEqual(stats['unread_count'], 1)
        self.assertEqual(stats['read_rate'], 50.0)

        # 2. 归档通知 -> 200
        resp_arch = self.client.post(f'/api/v1/admin/notifications/{notice.id}/archive/')
        self.assertEqual(resp_arch.status_code, 200)
        self.assertEqual(_unwrap_data(resp_arch.data)['status'], 'archived')

        # 3. 重复归档 -> 400
        resp_rearch = self.client.post(f'/api/v1/admin/notifications/{notice.id}/archive/')
        self.assertEqual(resp_rearch.status_code, 400)


@override_settings(ALLOWED_HOSTS=['*'])
class MemberNotificationViewSetTestCase(TestCase):
    """
    成员端 MemberNotificationViewSet (/api/v1/notifications/) 功能测试
    """

    def setUp(self):
        self.tenant_a = Tenant.objects.create(name='Tenant A', code='tenant_a', status='active')
        self.app_a = Application.objects.create(
            tenant=self.tenant_a, name='App Alpha', code='app_alpha', status='active'
        )
        self.member_a = Member.objects.create_user(
            username='member_a',
            email='member_a@example.com',
            password='password123',
            tenant=self.tenant_a
        )

        # 创建 2 条已发布通知与 1 条草稿通知
        self.notice_1 = Notification.objects.create(
            tenant=self.tenant_a,
            title='通知一：系统公告',
            content='公告详情内容',
            scope='tenant',
            notification_type='announcement',
            priority='high',
            status='published'
        )
        self.notice_2 = Notification.objects.create(
            tenant=self.tenant_a,
            title='通知二：应用更新',
            content='应用更新内容',
            scope='application',
            application=self.app_a,
            notification_type='update',
            priority='normal',
            status='published'
        )
        self.notice_draft = Notification.objects.create(
            tenant=self.tenant_a,
            title='未发布草稿通知',
            content='草稿机密内容',
            scope='members',
            status='draft'
        )

        self.recip_1 = NotificationRecipient.objects.create(
            tenant=self.tenant_a,
            notification=self.notice_1,
            member=self.member_a,
            is_read=False
        )
        self.recip_2 = NotificationRecipient.objects.create(
            tenant=self.tenant_a,
            notification=self.notice_2,
            member=self.member_a,
            is_read=False
        )
        self.recip_draft = NotificationRecipient.objects.create(
            tenant=self.tenant_a,
            notification=self.notice_draft,
            member=self.member_a,
            is_read=False
        )

        self.client = APIClient()
        self.token_member_a = generate_jwt_token(self.member_a)['access_token']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token_member_a}')

    def test_member_draft_invisible_and_list_filtering(self):
        """
        测试成员端草稿通知不可见，以及按 is_read、application、type、priority 筛选列表
        """
        # 1. 默认列表仅返回 2 条已发布通知，不包含草稿
        resp_all = self.client.get('/api/v1/notifications/')
        self.assertEqual(resp_all.status_code, 200)
        results_all = _unwrap_data(resp_all.data).get('results', [])
        returned_ids = [item['id'] for item in results_all]
        self.assertEqual(len(returned_ids), 2)
        self.assertNotIn(self.recip_draft.id, returned_ids)

        # 2. 直接请求草稿接收记录详情返回 404
        resp_draft_detail = self.client.get(f'/api/v1/notifications/{self.recip_draft.id}/')
        self.assertEqual(resp_draft_detail.status_code, 404)

        # 3. 按 application 筛选
        resp_app = self.client.get(f'/api/v1/notifications/?application={self.app_a.id}')
        self.assertEqual(resp_app.status_code, 200)
        results_app = _unwrap_data(resp_app.data).get('results', [])
        self.assertEqual(len(results_app), 1)
        self.assertEqual(results_app[0]['id'], self.recip_2.id)

        # 4. 按 type 和 priority 筛选
        resp_type = self.client.get('/api/v1/notifications/?type=announcement&priority=high')
        self.assertEqual(resp_type.status_code, 200)
        results_type = _unwrap_data(resp_type.data).get('results', [])
        self.assertEqual(len(results_type), 1)
        self.assertEqual(results_type[0]['id'], self.recip_1.id)

    def test_member_retrieve_auto_marks_as_read(self):
        """
        测试成员端 retrieve 获取详情时自动将通知标记为已读并记录 read_at
        """
        self.assertFalse(self.recip_1.is_read)
        resp = self.client.get(f'/api/v1/notifications/{self.recip_1.id}/')
        self.assertEqual(resp.status_code, 200)
        detail = _unwrap_data(resp.data)
        self.assertTrue(detail['is_read'])
        self.assertEqual(detail['content'], '公告详情内容')

        self.recip_1.refresh_from_db()
        self.assertTrue(self.recip_1.is_read)
        self.assertIsNotNone(self.recip_1.read_at)

        # 按 is_read=true 过滤应只查出 recip_1
        resp_read = self.client.get('/api/v1/notifications/?is_read=true')
        results_read = _unwrap_data(resp_read.data).get('results', [])
        self.assertEqual(len(results_read), 1)
        self.assertEqual(results_read[0]['id'], self.recip_1.id)

    def test_member_explicit_read_read_all_and_unread_count(self):
        """
        测试成员端 unread-count 接口、单条 read 动作与 read-all 批量已读动作
        """
        # 1. 初始未读数量为 2
        resp_count_1 = self.client.get('/api/v1/notifications/unread-count/')
        self.assertEqual(resp_count_1.status_code, 200)
        self.assertEqual(_unwrap_data(resp_count_1.data)['unread_count'], 2)

        # 2. 调用 POST /{id}/read/ 标记 recip_1 为已读
        resp_read_1 = self.client.post(f'/api/v1/notifications/{self.recip_1.id}/read/')
        self.assertEqual(resp_read_1.status_code, 200)
        self.recip_1.refresh_from_db()
        self.assertTrue(self.recip_1.is_read)

        # 未读数量减为 1
        resp_count_2 = self.client.get('/api/v1/notifications/unread-count/')
        self.assertEqual(_unwrap_data(resp_count_2.data)['unread_count'], 1)

        # 3. 调用 POST /read-all/ 将剩余未读全部标记为已读
        resp_read_all = self.client.post('/api/v1/notifications/read-all/')
        self.assertEqual(resp_read_all.status_code, 200)
        self.assertEqual(_unwrap_data(resp_read_all.data)['updated_count'], 1)

        self.recip_2.refresh_from_db()
        self.assertTrue(self.recip_2.is_read)

        # 未读数量变为 0
        resp_count_3 = self.client.get('/api/v1/notifications/unread-count/')
        self.assertEqual(_unwrap_data(resp_count_3.data)['unread_count'], 0)
