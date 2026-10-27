"""
通知系统模型约束与服务层单元测试
覆盖 Notification.clean()、NotificationRecipient 状态与计数、以及 services.py 核心函数。
"""
from django.core import mail
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from tenants.models import Tenant
from users.models import Member
from applications.models import Application
from notifications.models import Notification, NotificationRecipient
from notifications.services import (
    get_member_unread_count,
    mark_notification_as_read,
    mark_all_as_read,
    _send_notification_email_sync,
)


class NotificationModelsAndServicesTestCase(TestCase):
    """
    通知模型与服务层单元测试套件
    """

    def setUp(self):
        self.tenant_a = Tenant.objects.create(name='Tenant A', code='tenant_a', status='active')
        self.tenant_b = Tenant.objects.create(name='Tenant B', code='tenant_b', status='active')

        self.app_a = Application.objects.create(
            tenant=self.tenant_a,
            name='App Alpha',
            code='app_alpha',
            status='active'
        )

        self.member_1 = Member.objects.create_user(
            username='notify_m1',
            email='notify_m1@example.com',
            password='password123',
            tenant=self.tenant_a
        )
        self.member_2 = Member.objects.create_user(
            username='notify_m2',
            email='notify_m2@example.com',
            password='password123',
            tenant=self.tenant_a
        )
        self.member_no_email = Member.objects.create_user(
            username='notify_no_email',
            email='',
            password='password123',
            tenant=self.tenant_a
        )

    def test_notification_clean_application_scope_requires_application(self):
        """
        测试 Notification.clean()：当 scope='application' 且未关联 application 时抛出 ValidationError
        """
        notice = Notification(
            tenant=self.tenant_a,
            scope='application',
            application=None,
            title='应用通知缺失应用',
            content='内容'
        )
        with self.assertRaises(ValidationError) as ctx:
            notice.save()
        self.assertIn('application', ctx.exception.message_dict)

    def test_notification_clean_non_application_scope_forbids_application(self):
        """
        测试 Notification.clean()：当 scope!='application' 却关联了 application 时抛出 ValidationError
        """
        notice_tenant = Notification(
            tenant=self.tenant_a,
            scope='tenant',
            application=self.app_a,
            title='租户通知误带应用',
            content='内容'
        )
        with self.assertRaises(ValidationError) as ctx:
            notice_tenant.save()
        self.assertIn('application', ctx.exception.message_dict)

        notice_members = Notification(
            tenant=self.tenant_a,
            scope='members',
            application=self.app_a,
            title='成员通知误带应用',
            content='内容'
        )
        with self.assertRaises(ValidationError) as ctx2:
            notice_members.save()
        self.assertIn('application', ctx2.exception.message_dict)

    def test_notification_clean_valid_application_scope_saves(self):
        """
        测试 Notification.clean()：当 scope='application' 且提供有效 application 时正常保存
        """
        notice = Notification.objects.create(
            tenant=self.tenant_a,
            scope='application',
            application=self.app_a,
            title='版本更新通知',
            content='v2.0 已发布'
        )
        self.assertEqual(notice.scope, 'application')
        self.assertEqual(notice.application, self.app_a)
        self.assertIn('版本更新通知', str(notice))

    def test_notification_recipient_mark_as_read_and_counts(self):
        """
        测试 NotificationRecipient.mark_as_read()、唯一性约束及 Notification 的接收/已读/未读计数方法
        """
        notice = Notification.objects.create(
            tenant=self.tenant_a,
            scope='tenant',
            title='计数测试通知',
            content='计数测试内容',
            status='published'
        )
        r1 = NotificationRecipient.objects.create(
            tenant=self.tenant_a,
            notification=notice,
            member=self.member_1
        )
        r2 = NotificationRecipient.objects.create(
            tenant=self.tenant_a,
            notification=notice,
            member=self.member_2
        )

        # 验证唯一性约束
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                NotificationRecipient.objects.create(
                    tenant=self.tenant_a,
                    notification=notice,
                    member=self.member_1
                )

        # 初始计数：2 接收，0 已读，2 未读
        self.assertEqual(notice.get_recipient_count(), 2)
        self.assertEqual(notice.get_read_count(), 0)
        self.assertEqual(notice.get_unread_count(), 2)

        # 标记 r1 为已读
        r1.mark_as_read()
        r1.refresh_from_db()
        self.assertTrue(r1.is_read)
        self.assertIsNotNone(r1.read_at)
        first_read_at = r1.read_at

        # 再次调用 mark_as_read() 幂等，不覆盖原 read_at
        r1.mark_as_read()
        r1.refresh_from_db()
        self.assertEqual(r1.read_at, first_read_at)

        # 此时 1 已读，1 未读
        self.assertEqual(notice.get_recipient_count(), 2)
        self.assertEqual(notice.get_read_count(), 1)
        self.assertEqual(notice.get_unread_count(), 1)
        self.assertFalse(r2.is_read)

    def test_service_get_member_unread_count(self):
        """
        测试 services.get_member_unread_count：仅统计已发布且未软删除的未读通知
        """
        notice_pub = Notification.objects.create(
            tenant=self.tenant_a,
            title='已发布通知',
            content='内容',
            status='published'
        )
        notice_draft = Notification.objects.create(
            tenant=self.tenant_a,
            title='草稿通知',
            content='内容',
            status='draft'
        )
        notice_deleted = Notification.objects.create(
            tenant=self.tenant_a,
            title='已删除通知',
            content='内容',
            status='published',
            is_deleted=True
        )

        NotificationRecipient.objects.create(
            tenant=self.tenant_a,
            notification=notice_pub,
            member=self.member_1,
            is_read=False
        )
        NotificationRecipient.objects.create(
            tenant=self.tenant_a,
            notification=notice_draft,
            member=self.member_1,
            is_read=False
        )
        NotificationRecipient.objects.create(
            tenant=self.tenant_a,
            notification=notice_deleted,
            member=self.member_1,
            is_read=False
        )

        self.assertEqual(get_member_unread_count(self.member_1), 1)

    def test_service_mark_notification_as_read(self):
        """
        测试 services.mark_notification_as_read：单条标记成功、他人记录或不存在记录返回 False
        """
        notice = Notification.objects.create(
            tenant=self.tenant_a,
            title='单条已读测试',
            content='内容',
            status='published'
        )
        recip = NotificationRecipient.objects.create(
            tenant=self.tenant_a,
            notification=notice,
            member=self.member_1,
            is_read=False
        )

        # member_2 尝试标记 member_1 的记录 -> False
        self.assertFalse(mark_notification_as_read(recip.id, self.member_2))
        recip.refresh_from_db()
        self.assertFalse(recip.is_read)

        # 不存在的 ID -> False
        self.assertFalse(mark_notification_as_read(999999, self.member_1))

        # member_1 正常标记 -> True
        self.assertTrue(mark_notification_as_read(recip.id, self.member_1))
        recip.refresh_from_db()
        self.assertTrue(recip.is_read)
        self.assertIsNotNone(recip.read_at)

    def test_service_mark_all_as_read(self):
        """
        测试 services.mark_all_as_read：批量更新成员未读已发布通知，返回更新条数且不影响其他成员
        """
        n1 = Notification.objects.create(
            tenant=self.tenant_a, title='N1', content='C1', status='published'
        )
        n2 = Notification.objects.create(
            tenant=self.tenant_a, title='N2', content='C2', status='published'
        )
        r1_m1 = NotificationRecipient.objects.create(
            tenant=self.tenant_a, notification=n1, member=self.member_1, is_read=False
        )
        r2_m1 = NotificationRecipient.objects.create(
            tenant=self.tenant_a, notification=n2, member=self.member_1, is_read=False
        )
        r1_m2 = NotificationRecipient.objects.create(
            tenant=self.tenant_a, notification=n1, member=self.member_2, is_read=False
        )

        updated_count = mark_all_as_read(self.member_1)
        self.assertEqual(updated_count, 2)
        self.assertEqual(get_member_unread_count(self.member_1), 0)

        r1_m1.refresh_from_db()
        r2_m1.refresh_from_db()
        r1_m2.refresh_from_db()
        self.assertTrue(r1_m1.is_read)
        self.assertTrue(r2_m1.is_read)
        self.assertFalse(r1_m2.is_read)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_service_send_notification_email_sync(self):
        """
        测试 services._send_notification_email_sync：提取有效邮箱发送邮件并更新 email_sent_at
        """
        notice = Notification.objects.create(
            tenant=self.tenant_a,
            title='邮件通知标题',
            content='邮件通知正文内容',
            notification_type='announcement',
            send_email=True,
            status='published'
        )
        NotificationRecipient.objects.create(
            tenant=self.tenant_a, notification=notice, member=self.member_1
        )
        NotificationRecipient.objects.create(
            tenant=self.tenant_a, notification=notice, member=self.member_2
        )
        NotificationRecipient.objects.create(
            tenant=self.tenant_a, notification=notice, member=self.member_no_email
        )

        mail.outbox.clear()
        _send_notification_email_sync(notice.id)

        # 仅 2 个成员有有效邮箱，应发送 2 封邮件
        self.assertEqual(len(mail.outbox), 2)
        sent_to = [m.to[0] for m in mail.outbox]
        self.assertCountEqual(sent_to, ['notify_m1@example.com', 'notify_m2@example.com'])
        self.assertIn('邮件通知标题', mail.outbox[0].subject)

        notice.refresh_from_db()
        self.assertIsNotNone(notice.email_sent_at)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_service_send_notification_email_sync_no_valid_emails_or_missing_id(self):
        """
        测试 _send_notification_email_sync 在无有效邮箱或通知不存在时安全返回
        """
        mail.outbox.clear()
        # 1. 不存在的通知 ID
        _send_notification_email_sync(888888)
        self.assertEqual(len(mail.outbox), 0)

        # 2. 接收者无有效邮箱
        notice_no_email = Notification.objects.create(
            tenant=self.tenant_a,
            title='无邮箱通知',
            content='正文',
            send_email=True,
            status='published'
        )
        NotificationRecipient.objects.create(
            tenant=self.tenant_a, notification=notice_no_email, member=self.member_no_email
        )
        _send_notification_email_sync(notice_no_email.id)
        self.assertEqual(len(mail.outbox), 0)
        notice_no_email.refresh_from_db()
        self.assertIsNone(notice_no_email.email_sent_at)
