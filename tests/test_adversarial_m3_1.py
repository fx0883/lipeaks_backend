"""
Adversarial Empirical Stress Test Suite for Challenger M3-1
针对 Milestone 3 的三项核心能力进行对抗攻防实证验证：
1. [BUG-03 攻防] 事务原子性与回滚实证 (activate_license / assign_license_to_member / apply_trial_license / batch_grant_vip)
2. [BUG-06 攻防] 反馈投票原子扣减与非负下限实证 (FeedbackVote Greatest(..., 0) 与防刷幂等)
3. [BUG-08 攻防] 打卡记录防重友好转译实证 (CheckRecordViewSet 与 MemberCheckinViewSet 友好 400，无 500)
"""
from datetime import date, timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from tenants.models import Tenant
from users.models import User, Member
from applications.models import Application
from licenses.models import (
    LicensePlan, License, MachineBinding, LicenseActivation, LicenseAssignment, TenantLicenseQuota
)
from licenses.services.license_service import LicenseActivationService
from licenses.services.member_license_service import MemberLicenseApplicationService
from points.services.license_service import TenantAwareLicenseAssignmentService
from points.services.vip_service import VipExpirationService, VipBatchOperations
from points.models import UserTypeTag, TenantUserProfile, TenantUserTypeTag

from feedbacks.models import Feedback, FeedbackVote
from check_system.models import TaskCategory, Task, CheckRecord


class AdversarialTransactionRollbackTests(TestCase):
    """
    [BUG-03 攻防] 事务原子性与回滚实证挑战
    验证被 @transaction.atomic 装饰的服务方法在捕获异常并返回错误字典时，
    是否显式调用了 transaction.set_rollback(True)，确保事务真实回滚、保存点有效隔离、无脏数据落盘。
    """

    def setUp(self):
        self.tenant = Tenant.objects.create(name="Tenant M3-1", code="tenant_m3_1", status="active")
        self.member = Member.objects.create_user(
            username="member_m3_1",
            email="m3_1@example.com",
            password="Password123!",
            tenant=self.tenant
        )
        self.app = Application.objects.create(
            name="App M3-1",
            code="APP_M3_1",
            status="active"
        )
        self.plan = LicensePlan.objects.create(
            name="Pro Plan",
            code="PRO_PLAN",
            plan_type="subscription",
            application=self.app,
            default_validity_days=30,
            default_max_activations=2,
            price=200
        )
        self.activation_service = LicenseActivationService()

    def test_activate_license_internal_failure_rolls_back_cleanly(self):
        """
        攻防验证：activate_license 在已创建 MachineBinding/LicenseActivation 后遭遇异常，
        验证是否由于 set_rollback(True) 完整回滚，数据库无任何机器绑定与激活脏记录残留。
        """
        license_key = "LIC-ADV-M3-1001"
        license_hash = self.activation_service.security_service.hash_manager.hash_data(license_key)
        license_obj = License.objects.create(
            tenant=self.tenant,
            application=self.app,
            plan=self.plan,
            license_key=license_key,
            license_hash=license_hash,
            status="generated",
            max_activations=2,
            expires_at=timezone.now() + timedelta(days=30)
        )

        hardware_info = {
            "hardware_uuid": "HW-ADV-001",
            "network_info": {"mac_addresses": ["AA:BB:CC:11:22:33"]},
            "disk_info": {"serial": "DISK-ADV-001"}
        }

        # 模拟在激活末尾写安全审计日志时抛出底层数据库错误
        with patch('licenses.services.license_service.SecurityAuditLog.objects.create', side_effect=RuntimeError("Simulated DB Disk Full during SecurityAuditLog")):
            res = self.activation_service.activate_license(
                license_key=license_key,
                hardware_info=hardware_info
            )

        # 1. 验证业务返回失败，无未捕获崩溃
        self.assertFalse(res.get("success"), "activate_license 在内部失败时必须返回 success=False")
        self.assertEqual(res.get("code"), "ACTIVATION_ERROR")

        # 2. 实证验证：事务确实回滚，机器绑定记录零落盘
        bindings_count = MachineBinding.objects.filter(license=license_obj).count()
        self.assertEqual(bindings_count, 0, f"事务未生效回滚！发现残留机器绑定脏数据: {bindings_count} 条")

        # 3. 实证验证：激活历史记录零落盘
        activations_count = LicenseActivation.objects.filter(license=license_obj).count()
        self.assertEqual(activations_count, 0, f"事务未生效回滚！发现残留激活历史脏数据: {activations_count} 条")

        # 4. 实证验证：许可证状态未被篡改为 activated
        license_obj.refresh_from_db()
        self.assertEqual(license_obj.status, "generated", f"许可证状态被脏提交为 {license_obj.status}")
        self.assertEqual(license_obj.current_activations, 0)

    def test_assign_license_to_member_points_failure_rolls_back_cleanly(self):
        """
        攻防验证：assign_license_to_member 在创建 LicenseAssignment 后积分奖励抛出异常，
        验证是否由于 set_rollback(True) 完整回滚，分配记录不落盘。
        """
        license_key = "LIC-ADV-M3-1002"
        license_hash = self.activation_service.security_service.hash_manager.hash_data(license_key)
        license_obj = License.objects.create(
            tenant=self.tenant,
            application=self.app,
            plan=self.plan,
            license_key=license_key,
            license_hash=license_hash,
            status="generated",
            max_activations=1,
            expires_at=timezone.now() + timedelta(days=30)
        )

        service = TenantAwareLicenseAssignmentService()

        # 模拟权限检查通过，_apply_permission_enhancements 返回标准配置，在积分赠送步骤抛出系统异常
        with patch.object(service.permission_validator, 'validate_license_assignment', return_value={'is_valid': True, 'message': 'OK'}), \
             patch.object(service, '_validate_license_for_assignment', return_value={'is_valid': True, 'message': 'OK'}), \
             patch.object(service.permission_service, 'calculate_user_permissions', return_value={'max_activations': 1, 'features': [], '_metadata': {'user_level': 'basic', 'active_tags': []}}), \
             patch.object(service, '_apply_permission_enhancements', return_value={}), \
             patch.object(service, '_award_license_points', side_effect=RuntimeError("Points Service Down")):
            res = service.assign_license_to_member(
                member=self.member,
                license=license_obj,
                assignment_type='standard',
                status='pending'
            )

        # 1. 验证业务响应返回失败
        self.assertFalse(res.get("success"))
        self.assertEqual(res.get("error"), "assignment_failed")

        # 2. 实证验证：LicenseAssignment 记录零落盘
        assignments_count = LicenseAssignment.objects.filter(license=license_obj, member=self.member).count()
        self.assertEqual(assignments_count, 0, f"事务未生效回滚！发现残留分配记录: {assignments_count} 条")

        # 3. 实证验证：许可证状态未变为 assigned
        license_obj.refresh_from_db()
        self.assertEqual(license_obj.status, "generated")

    def test_apply_trial_license_internal_failure_rolls_back_cleanly(self):
        """
        攻防验证：apply_trial_license 在创建许可证后若审计日志抛出异常，
        验证是否由 set_rollback(True) 保证不留下孤立许可证或分配记录。
        """
        trial_plan = LicensePlan.objects.create(
            name="Trial Plan",
            code="TRIAL_PLAN",
            plan_type="trial",
            application=self.app,
            default_validity_days=7,
            default_max_activations=1,
            price=0
        )
        TenantLicenseQuota.objects.create(
            tenant=self.tenant,
            application=self.app,
            max_licenses=10,
            current_licenses=0,
            quota_start_date=timezone.now().date(),
            quota_end_date=timezone.now().date() + timedelta(days=30),
            is_active=True
        )

        service = MemberLicenseApplicationService()

        # 模拟在记录活动日志时崩溃
        with patch.object(service, '_log_application_activity', side_effect=RuntimeError("Activity Log Service Down")):
            res = service.apply_trial_license(
                member=self.member,
                product_id=self.app.id,
                plan_id=trial_plan.id
            )

        self.assertFalse(res.get("success"))
        self.assertEqual(res.get("code"), "INTERNAL_ERROR")

        # 验证数据库无半成功许可证孤立落盘
        licenses_count = License.objects.filter(plan=trial_plan, tenant=self.tenant).count()
        self.assertEqual(licenses_count, 0, f"事务未回滚！残留试用许可证: {licenses_count} 条")
        assignments_count = LicenseAssignment.objects.filter(member=self.member).count()
        self.assertEqual(assignments_count, 0, f"事务未回滚！残留试用分配关系: {assignments_count} 条")

    def test_batch_vip_grant_savepoint_isolation(self):
        """
        攻防验证：VipBatchOperations.batch_grant_vip 在批量授予时使用 with transaction.atomic(): 保存点隔离，
        单个成员发生错误不破坏外层连接与其它成员授予。
        """
        member2 = Member.objects.create_user(
            username="member_m3_2",
            email="m3_2@example.com",
            password="Password123!",
            tenant=self.tenant
        )
        tag = UserTypeTag.objects.create(
            tag_name="VIP Silver",
            tag_code="VIP_SILVER"
        )
        # 为 member1 和 member2 创建 TenantUserProfile
        TenantUserProfile.objects.create(tenant=self.tenant, member=self.member)
        TenantUserProfile.objects.create(tenant=self.tenant, member=member2)

        batch_service = VipBatchOperations(VipExpirationService())

        # 构造包含不存在成员 ID 的批量列表: [有效1, 无效ID 999999, 有效2]
        member_ids = [self.member.id, 999999, member2.id]

        results = batch_service.batch_grant_vip(
            tenant=self.tenant,
            member_ids=member_ids,
            tag=tag,
            duration_days=30,
            operator_id=self.member.id,
            reason="Adversarial Batch VIP Test"
        )

        # 验证批量隔离：成功 2 个，失败 1 个，没有抛出 TransactionManagementError
        self.assertEqual(results['successful'], 2)
        self.assertEqual(results['failed'], 1)
        self.assertEqual(len(results['errors']), 1)
        self.assertEqual(results['errors'][0]['member_id'], 999999)

        # 验证两个有效成员成功持久化了 VIP 标签
        self.assertTrue(TenantUserTypeTag.objects.filter(member=self.member, tag=tag, is_active=True).exists())
        self.assertTrue(TenantUserTypeTag.objects.filter(member=member2, tag=tag, is_active=True).exists())


class AdversarialFeedbackVoteDeductionTests(TestCase):
    """
    [BUG-06 攻防] 反馈投票原子扣减与非负下限实证挑战
    验证 FeedbackVote.save() 与 delete() 使用 F 表达式和 Greatest(..., 0) 保护：
    1. 连续投票、取消投票、连续删除时 vote_count 准确扣减
    2. 当初始为 0 或扣减量超额时，坚固维持 0 而绝不变为负数
    3. 视图层提交相同票型时幂等拦截防刷
    """

    def setUp(self):
        self.tenant = Tenant.objects.create(name="Feedback Tenant", code="fb_tenant", status="active")
        self.user1 = User.objects.create_user(
            username="fb_user_1",
            email="fb1@example.com",
            password="Password123!",
            tenant=self.tenant
        )
        self.user2 = User.objects.create_user(
            username="fb_user_2",
            email="fb2@example.com",
            password="Password123!",
            tenant=self.tenant
        )
        self.feedback = Feedback.objects.create(
            tenant=self.tenant,
            user=self.user1,
            title="Adversarial Feedback Title",
            description="Testing vote count integrity",
            vote_count=0
        )
        self.client = APIClient()

    def test_feedback_vote_accurate_lifecycle_deduction(self):
        """
        实证验证点赞、点赞、取消点赞、取消点赞生命周期中 vote_count 的原子准确扣减
        """
        # 1. user1 投赞成票 (+1)
        vote1 = FeedbackVote.objects.create(
            feedback=self.feedback,
            user=self.user1,
            tenant=self.tenant,
            vote_type=1
        )
        self.feedback.refresh_from_db()
        self.assertEqual(self.feedback.vote_count, 1)

        # 2. user2 投赞成票 (+1)
        vote2 = FeedbackVote.objects.create(
            feedback=self.feedback,
            user=self.user2,
            tenant=self.tenant,
            vote_type=1
        )
        self.feedback.refresh_from_db()
        self.assertEqual(self.feedback.vote_count, 2)

        # 3. user1 取消点赞 (delete)
        vote1.delete()
        self.feedback.refresh_from_db()
        self.assertEqual(self.feedback.vote_count, 1, "取消点赞后 vote_count 未正确原子扣减至 1")

        # 4. user2 取消点赞 (delete)
        vote2.delete()
        self.feedback.refresh_from_db()
        self.assertEqual(self.feedback.vote_count, 0, "全部取消点赞后 vote_count 未正确原子扣减至 0")

    def test_feedback_vote_greatest_zero_boundary_protection_on_delete(self):
        """
        极限对抗验证：当反馈 vote_count 被人为或并发重置为 0 时，删除投赞成票记录，
        验证 Greatest(models.F('vote_count') - 1, 0) 是否坚固防守，绝不跌破 0 变成负数。
        """
        vote = FeedbackVote.objects.create(
            feedback=self.feedback,
            user=self.user1,
            tenant=self.tenant,
            vote_type=1
        )
        # 强制将 feedback 的 vote_count 篡改/重置为 0（模拟极端边界状态）
        Feedback.objects.filter(id=self.feedback.id).update(vote_count=0)
        self.feedback.refresh_from_db()
        self.assertEqual(self.feedback.vote_count, 0)

        # 执行删除：原数学运算 0 - 1 = -1
        vote.delete()

        # 实证验证：必须被 Greatest 截断为 0，绝不为 -1！
        self.feedback.refresh_from_db()
        self.assertEqual(
            self.feedback.vote_count, 0,
            f"安全防线击穿！vote_count 跌破下限变为负数: {self.feedback.vote_count}"
        )

    def test_feedback_vote_transition_from_upvote_to_downvote_with_lower_bound(self):
        """
        极限对抗验证：票型切换时的 diff 计算与非负下限。
        当 vote_count=1，用户从 +1 改投 -1 时，diff = -1 - 1 = -2。
        原计算 1 + (-2) = -1，必须被 Greatest(..., 0) 截断为 0。
        """
        vote = FeedbackVote.objects.create(
            feedback=self.feedback,
            user=self.user1,
            tenant=self.tenant,
            vote_type=1
        )
        self.feedback.refresh_from_db()
        self.assertEqual(self.feedback.vote_count, 1)

        # 用户修改为反对票 (-1)
        vote.vote_type = -1
        vote.save()

        self.feedback.refresh_from_db()
        self.assertEqual(
            self.feedback.vote_count, 0,
            f"安全防线击穿！赞成票切换为反对票导致 vote_count 变为负数: {self.feedback.vote_count}"
        )

    def test_feedback_vote_api_anti_gaming_idempotency(self):
        """
        防刷攻防验证：通过 API 连续重复提交同类型投票，验证幂等拦截与票数稳定不被无限刷高
        """
        self.client.force_authenticate(user=self.user1)
        url = f"/api/v1/feedbacks/feedbacks/{self.feedback.id}/vote/"

        # 第一次投票 (+1)
        resp1 = self.client.post(url, {'vote_type': 1}, format='json')
        self.assertEqual(resp1.status_code, status.HTTP_200_OK)
        self.feedback.refresh_from_db()
        self.assertEqual(self.feedback.vote_count, 1)

        # 连续发起 5 次相同投票攻击
        for _ in range(5):
            resp = self.client.post(url, {'vote_type': 1}, format='json')
            self.assertEqual(resp.status_code, status.HTTP_200_OK)
            self.assertEqual(resp.data.get('message'), 'Vote already recorded')

        # 最终实证：票数依然稳固为 1，防刷成功！
        self.feedback.refresh_from_db()
        self.assertEqual(
            self.feedback.vote_count, 1,
            f"防刷漏洞！重复投票导致票数被无限刷高至 {self.feedback.vote_count}"
        )


class AdversarialCheckRecordAntiDuplicateTests(TestCase):
    """
    [BUG-08 攻防] 打卡记录防重友好转译实证挑战
    针对 CheckRecordViewSet 与 MemberCheckinViewSet 接口：
    1. 模拟重复提交打卡请求，实证验证友好返回 HTTP 400 业务错误及包含“今日已打卡”/“打过卡”提示，而非未捕获的 HTTP 500
    2. 模拟高并发绕过序列化器内存 exists() 穿透触发底层 UniqueConstraint，验证 IntegrityError 被 perform_create 捕获并转译为 400
    3. 验证不同日期打卡或软删除后重新打卡合法通行
    """

    def setUp(self):
        self.tenant = Tenant.objects.create(name="Checkin Tenant", code="check_tenant", status="active")
        self.member = Member.objects.create_user(
            username="checkin_member",
            email="checkin@example.com",
            password="Password123!",
            tenant=self.tenant
        )
        self.category = TaskCategory.objects.create(
            name="Daily Habit",
            color="#FF5733"
        )
        self.today = timezone.now().date()
        self.task = Task.objects.create(
            name="Morning Run",
            category=self.category,
            member=self.member,
            tenant=self.tenant,
            start_date=self.today
        )
        self.client = APIClient()

    def test_check_record_viewset_duplicate_returns_400_not_500(self):
        """
        攻防验证：/api/v1/check-system/check-records/ 接口重复打卡，
        验证返回 HTTP 400 业务错误且包含打卡防重提示，绝不抛出 HTTP 500。
        """
        self.client.force_authenticate(user=self.member)
        url = "/api/v1/check-system/check-records/"

        payload = {
            "task": self.task.id,
            "check_date": str(self.today),
            "check_time": "08:30:00"
        }

        # 第一次打卡：必须成功 201
        res1 = self.client.post(url, payload, format='json')
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED, f"首次打卡失败: {res1.data}")
        self.assertEqual(CheckRecord.objects.filter(member=self.member, task=self.task, check_date=self.today).count(), 1)

        # 第二次打卡（模拟同一天重复提交）：必须返回 400，绝非 500！
        res2 = self.client.post(url, payload, format='json')
        self.assertNotEqual(
            res2.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR,
            "致命缺陷！重复打卡抛出未捕获的 HTTP 500 数据库崩溃异常！"
        )
        self.assertEqual(
            res2.status_code, status.HTTP_400_BAD_REQUEST,
            f"重复打卡未返回 400 业务错误，实际返回: {res2.status_code}"
        )

        # 验证返回内容包含友好提示（业务层序列化器防重提示）
        content_str = str(res2.data)
        has_hint = any(msg in content_str for msg in ["今日已打卡", "请勿重复打卡", "打过卡"])
        self.assertTrue(has_hint, f"响应内容缺失友好打卡防重提示: {content_str}")

    def test_check_record_viewset_concurrency_race_condition_falls_back_to_400(self):
        """
        极限竞态攻防验证：/api/v1/check-system/check-records/ 接口
        模拟高并发竞态绕过序列化器层的内存 exists() 校验，直接触发数据库底层 UniqueConstraint 抛出 IntegrityError，
        验证 CheckRecordViewSet.perform_create 是否成功捕获 IntegrityError 并转译为 HTTP 400 + “今日已打卡，请勿重复打卡”。
        """
        self.client.force_authenticate(user=self.member)
        url = "/api/v1/check-system/check-records/"

        payload = {
            "task": self.task.id,
            "check_date": str(self.today),
            "check_time": "08:30:00"
        }

        # 首次打卡
        res1 = self.client.post(url, payload, format='json')
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        # 绕过序列化器层的 validate 检查，模拟两个请求同时穿透验证进入 perform_create -> serializer.save()
        from check_system.serializers import CheckRecordSerializer
        with patch.object(CheckRecordSerializer, 'validate', side_effect=lambda data: data):
            res2 = self.client.post(url, payload, format='json')

        # 实证验证：perform_create 中的 except IntegrityError 成功转译为 HTTP 400，绝非 HTTP 500！
        self.assertNotEqual(
            res2.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR,
            "致命缺陷！并发竞态穿透序列化器检查后，数据库底层 IntegrityError 导致未捕获的 HTTP 500 崩溃！"
        )
        self.assertEqual(
            res2.status_code, status.HTTP_400_BAD_REQUEST,
            f"预期转译为 HTTP 400，实际状态码为: {res2.status_code}, data={res2.data}"
        )
        content_str = str(res2.data)
        self.assertTrue(
            "今日已打卡" in content_str or "请勿重复打卡" in content_str,
            f"底层 IntegrityError 转译错误提示不符合预期: {content_str}"
        )

    def test_member_checkin_viewset_concurrency_race_condition_falls_back_to_400(self):
        """
        极限竞态攻防验证：/api/v1/check-system/member/checkins/ 接口
        模拟高并发下两个请求同时穿透了视图层的内存 exists() 检查，
        第二个请求在 serializer.save() 时触发数据库底层 UniqueConstraint 抛出 IntegrityError，
        验证该 IntegrityError 是否被 views.py 优雅捕获并转译为 HTTP 400 + “今日已打卡”，绝不崩溃为 HTTP 500。
        """
        self.client.force_authenticate(user=self.member)
        url = "/api/v1/check-system/member/checkins/"

        payload = {
            "task": self.task.id,
            "check_date": str(self.today),
            "check_time": "09:00:00"
        }

        # 首次打卡成功
        res1 = self.client.post(url, payload, format='json')
        self.assertEqual(res1.status_code, status.HTTP_201_CREATED)

        # 模拟高并发穿透：通过 mock 让内存的 CheckRecord.objects.filter(...).exists 返回 False，
        # 强行使执行流下推进入 serializer.save() 触达数据库底层唯一约束
        original_filter = CheckRecord.objects.filter

        class FakeQuerySetWrapper:
            def __init__(self, qs):
                self._qs = qs
            def exists(self):
                return False  # 模拟内存检查被并发竞态穿透！
            def __getattr__(self, item):
                return getattr(self._qs, item)

        def fake_filter(*args, **kwargs):
            qs = original_filter(*args, **kwargs)
            if 'check_date' in kwargs:
                return FakeQuerySetWrapper(qs)
            return qs

        with patch('check_system.member_views.CheckRecord.objects.filter', side_effect=fake_filter):
            res2 = self.client.post(url, payload, format='json')

        # 实证验证：数据库层抛出 IntegrityError 后，被优雅转译为 HTTP 400，绝非 HTTP 500！
        self.assertNotEqual(
            res2.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR,
            "致命缺陷！并发竞态穿透内存检查后，数据库底层 IntegrityError 导致未捕获的 HTTP 500 崩溃！"
        )
        self.assertEqual(
            res2.status_code, status.HTTP_400_BAD_REQUEST,
            f"预期转译为 HTTP 400，实际状态码为: {res2.status_code}, data={res2.data}"
        )
        content_str = str(res2.data)
        self.assertTrue(
            "今日已打卡" in content_str or "请勿重复打卡" in content_str,
            f"转译错误提示不符合预期: {content_str}"
        )

    def test_check_record_different_date_and_soft_delete_recheck_allowed(self):
        """
        对比验证：同一任务在不同日期打卡，或者历史打卡软删除后重新打卡，合法通行返回 HTTP 201
        """
        self.client.force_authenticate(user=self.member)
        url = "/api/v1/check-system/check-records/"

        # 1. 今天的打卡
        res_today = self.client.post(url, {
            "task": self.task.id,
            "check_date": str(self.today),
            "check_time": "08:00:00"
        }, format='json')
        self.assertEqual(res_today.status_code, status.HTTP_201_CREATED)

        # 2. 明天的打卡：必须成功
        tomorrow = self.today + timedelta(days=1)
        res_tomorrow = self.client.post(url, {
            "task": self.task.id,
            "check_date": str(tomorrow),
            "check_time": "08:00:00"
        }, format='json')
        self.assertEqual(res_tomorrow.status_code, status.HTTP_201_CREATED)

        # 3. 软删除今天的打卡
        today_record = CheckRecord.objects.get(member=self.member, task=self.task, check_date=self.today)
        today_record.is_deleted = True
        today_record.save()

        # 4. 软删除后重新打卡同一天同一任务：条件唯一约束已排除 is_deleted=False，必须允许打卡成功！
        res_recheck = self.client.post(url, {
            "task": self.task.id,
            "check_date": str(self.today),
            "check_time": "12:00:00"
        }, format='json')
        self.assertEqual(res_recheck.status_code, status.HTTP_201_CREATED)
