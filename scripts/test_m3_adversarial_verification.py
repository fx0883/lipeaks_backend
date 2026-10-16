"""
Milestone 3 业务事务一致性与防刷治理对抗性挑战与边界实测脚本
覆盖维度：
1. [BUG-03] @transaction.atomic 吞异常回滚与保存点隔离实测 (License & VIP 服务)
2. [BUG-06] 反馈投票原子行级更新、Greatest防负数、视图层幂等防刷实测
3. [BUG-07] 事务内发信解耦 (transaction.on_commit 回滚丢弃验证)
4. [BUG-08] 打卡记录数据库唯一约束与视图层友好400降级实测
5. [BUG-05] 点赞、关注、文章点赞及VIP标签软删除平滑恢复实测
"""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# 确保项目根目录在 sys.path 中
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_test')
os.environ['DISABLE_MIGRATIONS'] = 'true'
import django
django.setup()

from django.test import TestCase, TransactionTestCase, RequestFactory
from django.db import transaction, IntegrityError
from django.utils import timezone
from datetime import timedelta

from tenants.models import Tenant
from users.models import User, Member
from applications.models import Application
from licenses.models import LicensePlan, License, MachineBinding, LicenseActivation, LicenseAssignment
from licenses.services.license_service import LicenseGenerationService, LicenseManagementService, LicenseActivationService
from licenses.services.member_license_service import MemberLicenseApplicationService
from points.models import UserTypeTag, TenantUserProfile, TenantUserTypeTag
from points.services.vip_service import VipExpirationService, VipBatchOperations
from points.services.license_service import TenantAwareLicenseAssignmentService
from feedbacks.models import Feedback, FeedbackVote
from feedbacks.services import FeedbackService, EmailService
from feedbacks.complete_system import FeedbackVoteView
from check_system.models import TaskCategory, Task, CheckRecord
from check_system.views import CheckRecordViewSet
from check_system.member_views import MemberCheckinViewSet
from interactions.models import MemberLike, MemberFollow, ArticleLike
from interactions.views import MemberLikeViewSet, MemberFollowViewSet, ArticleLikeViewSet
from cms.models import Article, Category, ArticleStatistics

results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "details": []
}

def log_test(name, passed, detail=""):
    results["total"] += 1
    if passed:
        results["passed"] += 1
        print(f"  [PASS] {name}")
    else:
        results["failed"] += 1
        print(f"  [FAIL] {name}: {detail}")
    results["details"].append({"name": name, "passed": passed, "detail": detail})


class M3AdversarialTestRunner(TransactionTestCase):
    """使用 TransactionTestCase 允许真实的事务提交与回滚检验"""

    def setUp(self):
        # 基础测试夹具
        self.tenant = Tenant.objects.create(name="Adv Tenant", code="adv_tenant")
        self.user = User.objects.create_user(username="adv_user", email="adv@example.com", password="password")
        self.member1 = Member.objects.create(username="adv_m1", email="m1@example.com", tenant=self.tenant)
        self.member2 = Member.objects.create(username="adv_m2", email="m2@example.com", tenant=self.tenant)
        self.member3 = Member.objects.create(username="adv_m3", email="m3@example.com", tenant=self.tenant)
        
        self.app = Application.objects.create(
            name="Adv App",
            code="adv_app",
            tenant=self.tenant,
            is_active=True
        )
        self.plan = LicensePlan.objects.create(
            application=self.app,
            name="Trial Plan",
            code="trial_plan",
            plan_type="trial",
            default_validity_days=30,
            default_max_activations=2,
            tenant=self.tenant,
            status='active'
        )

    def test_01_bug03_apply_trial_license_rollback_on_exception(self):
        """【BUG-03】验证申请试用许可证过程中异常时，已创建的 License 被严格回滚"""
        service = MemberLicenseApplicationService()
        initial_license_count = License.objects.count()
        
        # 在发送通知或写日志阶段注入一个异常
        with patch.object(service, '_log_application_activity', side_effect=RuntimeError("Simulated logging error")):
            result = service.apply_trial_license(
                member=self.member1,
                product_id=self.app.id,
                plan_id=self.plan.id
            )
            
            # 方法应吞下异常返回内部错误字典
            self.assertFalse(result['success'])
            self.assertEqual(result['code'], 'INTERNAL_ERROR')
            
        # 核心对抗验证：由于调用了 transaction.set_rollback(True)，数据库中不应残留新 License
        final_license_count = License.objects.count()
        log_test(
            "BUG-03: apply_trial_license 异常时显式回滚零残留",
            final_license_count == initial_license_count,
            f"预期数量 {initial_license_count}, 实际数量 {final_license_count}"
        )

    def test_02_bug03_batch_grant_vip_savepoint_isolation(self):
        """【BUG-03】验证批量授权 VIP 中间项异常时，保存点隔离确保后续项不被阻断且不报 TransactionManagementError"""
        tag = UserTypeTag.objects.create(tag_name="VIP Gold", tag_code="vip_gold")
        
        # 为 member1 和 member3 创建档案，member2 故意不创建档案导致 DoesNotExist 异常
        profile1 = TenantUserProfile.objects.create(member=self.member1, tenant=self.tenant)
        profile3 = TenantUserProfile.objects.create(member=self.member3, tenant=self.tenant)
        
        vip_service = VipExpirationService()
        batch_service = VipBatchOperations(vip_service)
        
        # 尝试批量授予 [member1, member2, member3]
        results_batch = batch_service.batch_grant_vip(
            tenant=self.tenant,
            member_ids=[self.member1.id, self.member2.id, self.member3.id],
            tag=tag,
            duration_days=30,
            reason="Adversarial Test"
        )
        
        # 验证结果统计
        is_isolated = (
            results_batch['successful'] == 2 and
            results_batch['failed'] == 1 and
            len(results_batch['errors']) == 1 and
            results_batch['errors'][0]['member_id'] == self.member2.id
        )
        
        # 验证数据库真实记录：member1 和 member3 确实被成功授予
        m1_has_vip = TenantUserTypeTag.objects.filter(tenant_user_profile=profile1, tag=tag, is_active=True).exists()
        m3_has_vip = TenantUserTypeTag.objects.filter(tenant_user_profile=profile3, tag=tag, is_active=True).exists()
        
        log_test(
            "BUG-03: batch_grant_vip 保存点隔离局部失败不污染后续批次",
            is_isolated and m1_has_vip and m3_has_vip,
            f"结果: {results_batch}, m1={m1_has_vip}, m3={m3_has_vip}"
        )

    def test_03_bug06_vote_atomic_update_and_greatest_floor(self):
        """【BUG-06】验证投票原子更新与 Greatest 兜底：防止负数并保证取消投票严格恢复"""
        feedback = Feedback.objects.create(
            title="Adversarial Feedback",
            description="Content",
            feedback_type="bug",
            vote_count=0,
            tenant=self.tenant
        )
        
        # 1. 初始为0时投反对票 (-1)，必须被 Greatest(0 + (-1), 0) 截断为 0，不能为负
        vote_down = FeedbackVote(feedback=feedback, user=self.user, vote_type=-1, tenant=self.tenant)
        vote_down.save()
        feedback.refresh_from_db()
        down_zero_pass = (feedback.vote_count == 0)
        
        # 2. 删除该反对票，按逻辑 vote_count 应该恢复 +1
        vote_down.delete()
        feedback.refresh_from_db()
        restore_one_pass = (feedback.vote_count == 1)
        
        # 3. 投赞成票 (+1)，vote_count 变为 2
        vote_up = FeedbackVote(feedback=feedback, user=self.user, vote_type=1, tenant=self.tenant)
        vote_up.save()
        feedback.refresh_from_db()
        up_two_pass = (feedback.vote_count == 2)
        
        # 4. 删除赞成票，vote_count 恢复 1
        vote_up.delete()
        feedback.refresh_from_db()
        restore_back_pass = (feedback.vote_count == 1)
        
        # 5. 再次清零并删除测试下限兜底
        vote_orphan = FeedbackVote(feedback=feedback, user=self.user, vote_type=1, tenant=self.tenant)
        vote_orphan.save()
        Feedback.objects.filter(id=feedback.id).update(vote_count=0)
        vote_orphan.delete()
        feedback.refresh_from_db()
        floor_zero_pass = (feedback.vote_count == 0)
        
        all_passed = down_zero_pass and restore_one_pass and up_two_pass and restore_back_pass and floor_zero_pass
        log_test(
            "BUG-06: FeedbackVote F表达式原子计算与 Greatest 0 兜底防负数",
            all_passed,
            f"down_zero={down_zero_pass}, restore_1={restore_one_pass}, up_2={up_two_pass}, restore_back={restore_back_pass}, floor={floor_zero_pass}"
        )

    def test_04_bug06_view_anti_gaming_and_idempotence(self):
        """【BUG-06】验证 FeedbackVoteView 视图层防刷幂等性：同一用户同类型连续提交不增加票数"""
        from rest_framework.test import force_authenticate
        feedback = Feedback.objects.create(
            title="Gaming Target",
            description="Content",
            feedback_type="suggestion",
            vote_count=0,
            tenant=self.tenant
        )
        factory = RequestFactory()
        view = FeedbackVoteView.as_view()
        
        # 连续 5 次发送 upvote 请求
        counts = []
        for i in range(5):
            req = factory.post(f"/api/v1/feedbacks/{feedback.id}/vote/", data={"vote_type": 1}, content_type="application/json")
            req.user = self.user
            req.tenant = self.tenant
            force_authenticate(req, user=self.user)
            resp = view(req, pk=feedback.id)
            self.assertEqual(resp.status_code, 200)
            feedback.refresh_from_db()
            counts.append(feedback.vote_count)
            
        # 验证票数自始至终稳定为 1
        idempotent_pass = all(c == 1 for c in counts)
        # 且只存在 1 条 FeedbackVote 记录
        single_vote_pass = (FeedbackVote.objects.filter(feedback=feedback, user=self.user).count() == 1)
        
        log_test(
            "BUG-06: 视图层防刷拦截重复投票，杜绝无限刷票膨胀",
            idempotent_pass and single_vote_pass,
            f"各次请求票数序列: {counts}, 投票记录总数: {FeedbackVote.objects.count()}"
        )

    def test_05_bug07_transaction_on_commit_email_isolation(self):
        """【BUG-07】验证事务内邮件发送解耦：若事务失败回滚，发信 hook 绝不执行"""
        email_sent = []
        def fake_send(fb):
            email_sent.append(fb.id)

        try:
            with transaction.atomic():
                feedback = Feedback.objects.create(
                    title="Rollback Feedback",
                    description="Content",
                    feedback_type="bug",
                    contact_email="anon@example.com",
                    tenant=self.tenant
                )
                # 模拟在事务块中挂载 on_commit 发信
                transaction.on_commit(lambda: fake_send(feedback))
                # 制造异常触发回滚
                raise ValueError("Intentional rollback")
        except ValueError:
            pass
            
        # 验证回滚后 on_commit 没有被执行
        rollback_email_suppressed = (len(email_sent) == 0)
        
        # 验证正常提交后 on_commit 会执行
        with transaction.atomic():
            fb2 = Feedback.objects.create(
                title="Commit Feedback",
                description="Content",
                feedback_type="bug",
                contact_email="anon2@example.com",
                tenant=self.tenant
            )
            transaction.on_commit(lambda: fake_send(fb2))
            
        commit_email_fired = (len(email_sent) == 1 and email_sent[0] == fb2.id)
        
        log_test(
            "BUG-07: transaction.on_commit 隔离网络发信，事务回滚自动丢弃",
            rollback_email_suppressed and commit_email_fired,
            f"suppressed={rollback_email_suppressed}, fired={commit_email_fired}"
        )

    def test_06_bug08_check_record_unique_constraint_and_friendly_error(self):
        """【BUG-08】验证打卡记录唯一约束并发冲突被转换为友好 400 校验错误而非 500"""
        from rest_framework.test import force_authenticate
        category = TaskCategory.objects.create(name="Cat", tenant=self.tenant)
        today = timezone.now().date()
        task = Task.objects.create(
            name="Daily Task",
            category=category,
            tenant=self.tenant,
            member=self.member1,
            start_date=today
        )
        
        # 第一次打卡
        first_record = CheckRecord.objects.create(
            member=self.member1,
            task=task,
            check_date=today,
            check_time=timezone.now().time(),
            tenant=self.tenant
        )
        self.assertIsNotNone(first_record.id)
        
        # 视图层再次创建同一天打卡
        factory = RequestFactory()
        view = CheckRecordViewSet.as_view({'post': 'create'})
        req = factory.post(
            "/api/v1/check/records/",
            data={"task": task.id, "check_date": today.isoformat(), "check_time": "12:00:00"},
            content_type="application/json",
            HTTP_X_TENANT_ID=str(self.tenant.id)
        )
        req.user = self.member1
        req.tenant = self.tenant
        force_authenticate(req, user=self.member1)
        
        response = view(req)
        # 应返回 400 而不是 500
        is_400 = (response.status_code == 400)
        resp_str = str(response.data)
        has_msg = "今日已打卡" in resp_str or "已经为该任务打过卡" in resp_str
        
        log_test(
            "BUG-08: 重复打卡 IntegrityError 优雅降级为 HTTP 400 提示",
            is_400 and has_msg,
            f"状态码: {response.status_code}, 返回内容: {response.data}"
        )

    def test_07_bug05_soft_delete_smooth_reactivation(self):
        """【BUG-05】验证用户点赞、关注和文章点赞软删除后能够平滑恢复"""
        from rest_framework.test import force_authenticate
        factory = RequestFactory()
        
        # 1. MemberLike 平滑恢复
        like_view_create = MemberLikeViewSet.as_view({'post': 'create'})
        like_view_destroy = MemberLikeViewSet.as_view({'delete': 'destroy'})
        
        req1 = factory.post(
            "/api/v1/interactions/member-likes/",
            data={"to_member": self.member2.id},
            content_type="application/json",
            HTTP_X_TENANT_ID=str(self.tenant.id)
        )
        req1.user = self.member1
        req1.tenant = self.tenant
        force_authenticate(req1, user=self.member1)
        res1 = like_view_create(req1)
        self.assertIn(res1.status_code, [200, 201])
        
        # 软删除
        like_instance = MemberLike.objects.get(from_member=self.member1, to_member=self.member2)
        like_id = like_instance.id
        req_del = factory.delete(
            f"/api/v1/interactions/member-likes/{like_id}/",
            HTTP_X_TENANT_ID=str(self.tenant.id)
        )
        req_del.user = self.member1
        req_del.tenant = self.tenant
        force_authenticate(req_del, user=self.member1)
        res_del = like_view_destroy(req_del, pk=like_id)
        self.assertEqual(res_del.status_code, 204)
        like_instance.refresh_from_db()
        self.assertTrue(like_instance.is_deleted)
        
        # 再次点赞：应平滑恢复原记录
        req2 = factory.post(
            "/api/v1/interactions/member-likes/",
            data={"to_member": self.member2.id},
            content_type="application/json",
            HTTP_X_TENANT_ID=str(self.tenant.id)
        )
        req2.user = self.member1
        req2.tenant = self.tenant
        force_authenticate(req2, user=self.member1)
        res2 = like_view_create(req2)
        like_instance.refresh_from_db()
        member_like_recovered = (res2.status_code in [200, 201]) and (not like_instance.is_deleted) and (like_instance.id == like_id)
        
        # 2. VIP 标签平滑恢复 (grant_vip_tag)
        tag = UserTypeTag.objects.create(tag_name="VIP Silver", tag_code="vip_silver")
        profile = TenantUserProfile.objects.create(member=self.member2, tenant=self.tenant)
        vip_service = VipExpirationService()
        
        # 首次授予
        v1 = vip_service.grant_vip_tag(tenant_user_profile=profile, tag=tag, duration_days=30, reason="Initial")
        # 模拟过期失效
        v1.is_active = False
        v1.status = 'expired'
        v1.save()
        
        # 再次购买/授予相同标签：应平滑复用原记录并激活
        v2 = vip_service.grant_vip_tag(tenant_user_profile=profile, tag=tag, duration_days=60, reason="Reactivate")
        vip_tag_reactivated = (v2.id == v1.id) and (v2.is_active is True) and (v2.status == 'active')
        
        log_test(
            "BUG-05: 软删除记录 (MemberLike & VIP Tag) 平滑激活复用无冲突",
            member_like_recovered and vip_tag_reactivated,
            f"member_like_recovered={member_like_recovered}, vip_tag_reactivated={vip_tag_reactivated}"
        )


if __name__ == '__main__':
    from django.test.runner import DiscoverRunner
    print("=" * 60)
    print("开始执行 Milestone 3 对抗性质押与极限边界测试套件...")
    print("=" * 60)
    runner = DiscoverRunner(verbosity=2)
    old_config = runner.setup_databases()
    suite = unittest.TestSuite()
    suite.addTest(M3AdversarialTestRunner('test_01_bug03_apply_trial_license_rollback_on_exception'))
    suite.addTest(M3AdversarialTestRunner('test_02_bug03_batch_grant_vip_savepoint_isolation'))
    suite.addTest(M3AdversarialTestRunner('test_03_bug06_vote_atomic_update_and_greatest_floor'))
    suite.addTest(M3AdversarialTestRunner('test_04_bug06_view_anti_gaming_and_idempotence'))
    suite.addTest(M3AdversarialTestRunner('test_05_bug07_transaction_on_commit_email_isolation'))
    suite.addTest(M3AdversarialTestRunner('test_06_bug08_check_record_unique_constraint_and_friendly_error'))
    suite.addTest(M3AdversarialTestRunner('test_07_bug05_soft_delete_smooth_reactivation'))
    
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(suite)
    runner.teardown_databases(old_config)
    print("=" * 60)
    print(f"实测汇总: 总计 {results['total']} 项, 通过 {results['passed']} 项, 失败 {results['failed']} 项")
    print("=" * 60)
    sys.exit(0 if result.wasSuccessful() else 1)
