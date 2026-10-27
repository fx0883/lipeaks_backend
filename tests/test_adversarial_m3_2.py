"""
Adversarial Empirical Stress Test Suite for Challenger M3-2
=============================================================================
针对 Milestone 3 交付物进行高强度对抗实证验证：
1. [BUG-05 攻防] 业务层软删除平滑恢复实证：
   - interactions: 用户点赞 (MemberLike), 用户关注 (MemberFollow), 文章点赞 (ArticleLike)
   - 创建 -> 取消 (软删除) -> 再次调用创建接口
   - 接口平滑放行并复用旧记录 (is_deleted -> False)，返回 201/200，杜绝 IntegrityError
   - 验证点赞/关注计数统计精确排除软删除记录
   - points.services.vip_service.VipExpirationService.grant_vip_tag: 失效标签平滑复用
2. [BUG-07 攻防] 邮件发信解耦实证：
   - feedbacks.services.FeedbackService: 创建匿名反馈、流转状态、添加回复
   - 事务成功 COMMIT 时: on_commit 钩子触发网络发信
   - 事务中途 ROLLBACK 时: 发信钩子自动废弃，杜绝网络幽灵通知与长事务阻塞
=============================================================================
"""
from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.test import TransactionTestCase
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from tenants.models import Tenant
from users.models import Member
from cms.models import Article, ArticleStatistics
from interactions.models import MemberLike, MemberFollow, ArticleLike
from points.models import UserTypeTag, TenantUserProfile, TenantUserTypeTag
from points.services.vip_service import VipExpirationService
from feedbacks.models import Feedback, FeedbackStatusHistory, FeedbackReply
from feedbacks.services import FeedbackService, EmailService

User = get_user_model()


class AdversarialSoftDeleteResurrectionApiTests(APITestCase):
    """
    [BUG-05 对抗实证挑战 1]
    业务表现层（REST API）软删除平滑恢复与精准计数对抗测试
    """

    def setUp(self):
        # 创建多租户与测试成员
        self.tenant = Tenant.objects.create(
            name="M3 Corp",
            code="m3corp",
            status="active"
        )
        self.member_a = Member.objects.create_user(
            username="user_m3_a",
            email="user_a@m3.com",
            password="Password123!",
            tenant=self.tenant
        )
        self.member_b = Member.objects.create_user(
            username="user_m3_b",
            email="user_b@m3.com",
            password="Password123!",
            tenant=self.tenant
        )
        self.member_c = Member.objects.create_user(
            username="user_m3_c",
            email="user_c@m3.com",
            password="Password123!",
            tenant=self.tenant
        )
        self.article = Article.objects.create(
            title="M3 Empirical Article",
            slug="m3-empirical-article",
            content="Empirical verification content",
            member=self.member_a,
            tenant=self.tenant
        )
        self.client.credentials(HTTP_X_TENANT_ID=str(self.tenant.id))

    def _extract_results(self, resp_data):
        """解析标准响应结构中的列表数据"""
        if isinstance(resp_data, dict):
            if 'data' in resp_data:
                inner = resp_data['data']
                if isinstance(inner, dict) and 'results' in inner:
                    return inner['results']
                if isinstance(inner, list):
                    return inner
            if 'results' in resp_data:
                return resp_data['results']
        elif isinstance(resp_data, list):
            return resp_data
        return []

    # =========================================================================
    # 1. MemberLike 用户点赞软删除平滑恢复对抗验证
    # =========================================================================
    def test_member_like_soft_delete_and_resurrection_api(self):
        """
        验证点：Member A 点赞 Member B -> 取消点赞 (软删除) -> 再次点赞
        实证目标：
        1. 首次点赞返回 201；
        2. 未取消时重复点赞被 400 拦截；
        3. 取消点赞 (unlike_by_member) 返回 204，is_deleted 变为 True；
        4. 再次调用创建接口放行并返回 201（非 400/500），主键 ID 原地复用，无新记录插入；
        5. 列表接口与 check-like 状态同步更新。
        """
        self.client.force_authenticate(user=self.member_a)

        # Step 1: 首次点赞
        create_url = '/api/v1/interactions/likes/'
        resp = self.client.post(create_url, {'to_member': self.member_b.id}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, f"首次点赞失败: {resp.data}")
        self.assertEqual(MemberLike.objects.filter(from_member=self.member_a, to_member=self.member_b).count(), 1)
        orig_like = MemberLike.objects.get(from_member=self.member_a, to_member=self.member_b)
        orig_like_id = orig_like.id
        self.assertFalse(orig_like.is_deleted)

        # Step 2: 活跃状态下重复点赞应被 400 校验拦截
        resp_dup = self.client.post(create_url, {'to_member': self.member_b.id}, format='json')
        self.assertEqual(resp_dup.status_code, status.HTTP_400_BAD_REQUEST, "重复点赞应被拦截")

        # Step 3: 取消点赞（软删除）
        unlike_url = f'/api/v1/interactions/likes/by-member/{self.member_b.id}/'
        resp_del = self.client.delete(unlike_url)
        self.assertEqual(resp_del.status_code, status.HTTP_204_NO_CONTENT, "取消点赞失败")

        orig_like.refresh_from_db()
        self.assertTrue(orig_like.is_deleted, "软删除后 is_deleted 应为 True")
        self.assertEqual(MemberLike.objects.filter(from_member=self.member_a, to_member=self.member_b).count(), 1, "总行数不应变化")

        # 检查列表接口应过滤软删除记录
        resp_list = self.client.get(create_url)
        self.assertEqual(resp_list.status_code, status.HTTP_200_OK)
        results = self._extract_results(resp_list.data)
        self.assertEqual(len(results), 0, "点赞列表应排除已软删除记录")

        # 检查 check 接口
        check_url = f'/api/v1/interactions/likes/check/{self.member_b.id}/'
        resp_check = self.client.get(check_url)
        self.assertEqual(resp_check.status_code, status.HTTP_200_OK)
        check_data = resp_check.data.get('data', resp_check.data)
        self.assertFalse(check_data.get('is_liked'), "check 应判定为未点赞")

        # Step 4: 软删除后再次调用创建接口（平滑恢复实证）
        resp_resurrect = self.client.post(create_url, {'to_member': self.member_b.id}, format='json')
        self.assertEqual(resp_resurrect.status_code, status.HTTP_201_CREATED, f"平滑恢复点赞失败: {resp_resurrect.data}")

        # 数据库严格校验原地复用
        current_like = MemberLike.objects.get(from_member=self.member_a, to_member=self.member_b)
        self.assertEqual(current_like.id, orig_like_id, "必须原地复用旧记录主键 ID，绝不能产生新行！")
        self.assertEqual(
            MemberLike.objects.filter(from_member=self.member_a, to_member=self.member_b).count(),
            1,
            "平滑恢复后数据库记录数必须严格保持为 1，严禁垃圾数据堆积！"
        )
        self.assertFalse(current_like.is_deleted, "平滑恢复后 is_deleted 必须重置为 False")

        # 再次检查 check 接口
        resp_check_again = self.client.get(check_url)
        check_data_again = resp_check_again.data.get('data', resp_check_again.data)
        self.assertTrue(check_data_again.get('is_liked'), "恢复后 check 应判定为已点赞")

    def test_member_like_repeated_toggling_stress_cycle(self):
        """
        高频循环点赞/取消对抗压力测试：
        连续执行 5 次 点赞 -> 取消 -> 点赞 循环，验证数据库行数永不膨胀且无并发/主键冲突。
        """
        self.client.force_authenticate(user=self.member_a)
        create_url = '/api/v1/interactions/likes/'
        unlike_url = f'/api/v1/interactions/likes/by-member/{self.member_b.id}/'

        # 首次创建
        first_resp = self.client.post(create_url, {'to_member': self.member_b.id}, format='json')
        self.assertEqual(first_resp.status_code, status.HTTP_201_CREATED)
        canonical_id = MemberLike.objects.get(from_member=self.member_a, to_member=self.member_b).id

        for cycle in range(5):
            # 取消
            del_resp = self.client.delete(unlike_url)
            self.assertEqual(del_resp.status_code, status.HTTP_204_NO_CONTENT, f"Cycle {cycle} 取消失败")
            # 恢复
            post_resp = self.client.post(create_url, {'to_member': self.member_b.id}, format='json')
            self.assertEqual(post_resp.status_code, status.HTTP_201_CREATED, f"Cycle {cycle} 平滑恢复失败: {post_resp.data}")
            current_id = MemberLike.objects.get(from_member=self.member_a, to_member=self.member_b).id
            self.assertEqual(current_id, canonical_id, f"Cycle {cycle} 主键未复用")

        # 最终断言：数据库仅有 1 条记录
        self.assertEqual(MemberLike.objects.filter(from_member=self.member_a, to_member=self.member_b).count(), 1)
        self.assertFalse(MemberLike.objects.get(id=canonical_id).is_deleted)

    # =========================================================================
    # 2. MemberFollow 用户关注软删除平滑恢复对抗验证
    # =========================================================================
    def test_member_follow_soft_delete_and_resurrection_api(self):
        """
        验证点：Member A 关注 Member B -> 取消关注 (软删除) -> 再次关注
        实证目标：平滑复用旧关注记录，is_deleted 平滑恢复为 False，粉丝列表与关注列表精确过滤。
        """
        self.client.force_authenticate(user=self.member_a)
        create_url = '/api/v1/interactions/follows/'
        unfollow_url = f'/api/v1/interactions/follows/by-member/{self.member_b.id}/'

        # Step 1: 首次关注
        resp = self.client.post(create_url, {'following': self.member_b.id}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED, f"首次关注失败: {resp.data}")
        self.assertEqual(MemberFollow.objects.filter(follower=self.member_a, following=self.member_b).count(), 1)
        orig_follow = MemberFollow.objects.get(follower=self.member_a, following=self.member_b)
        orig_follow_id = orig_follow.id

        # Step 2: 活跃状态下重复关注拦截
        resp_dup = self.client.post(create_url, {'following': self.member_b.id}, format='json')
        self.assertEqual(resp_dup.status_code, status.HTTP_400_BAD_REQUEST)

        # Step 3: 取消关注
        resp_del = self.client.delete(unfollow_url)
        self.assertEqual(resp_del.status_code, status.HTTP_204_NO_CONTENT)

        orig_follow.refresh_from_db()
        self.assertTrue(orig_follow.is_deleted, "软删除后 is_deleted 应为 True")

        # 检查 A 的关注列表应为空
        resp_list = self.client.get(create_url)
        results = self._extract_results(resp_list.data)
        self.assertEqual(len(results), 0, "关注列表应过滤软删除记录")

        # 切换到 B，检查 B 的粉丝列表应为空
        self.client.force_authenticate(user=self.member_b)
        resp_followers = self.client.get('/api/v1/interactions/follows/followers/')
        followers = self._extract_results(resp_followers.data)
        self.assertEqual(len(followers), 0, "粉丝列表应过滤软删除记录")

        # Step 4: 切换回 A，再次关注 B（平滑恢复）
        self.client.force_authenticate(user=self.member_a)
        resp_resurrect = self.client.post(create_url, {'following': self.member_b.id}, format='json')
        self.assertEqual(resp_resurrect.status_code, status.HTTP_201_CREATED, f"平滑恢复关注失败: {resp_resurrect.data}")

        current_follow = MemberFollow.objects.get(follower=self.member_a, following=self.member_b)
        self.assertEqual(current_follow.id, orig_follow_id, "关注记录必须原地复用")
        self.assertEqual(MemberFollow.objects.filter(follower=self.member_a, following=self.member_b).count(), 1)
        self.assertFalse(current_follow.is_deleted)

        # 切换到 B，粉丝列表重新能看到 A
        self.client.force_authenticate(user=self.member_b)
        resp_followers_again = self.client.get('/api/v1/interactions/follows/followers/')
        followers_again = self._extract_results(resp_followers_again.data)
        self.assertEqual(len(followers_again), 1, "恢复关注后粉丝列表必须重新出现")

    # =========================================================================
    # 3. ArticleLike 文章点赞软删除平滑恢复与精准计数对抗验证
    # =========================================================================
    def test_article_like_soft_delete_resurrection_and_accurate_count_api(self):
        """
        验证点：文章点赞软删除平滑恢复与 ArticleStatistics.likes_count 精准统计。
        实证目标：
        1. Member A 与 Member B 分别点赞，likes_count 精确递增至 2；
        2. Member A 取消点赞 (软删除)，likes_count 精确递减至 1（精确排除软删除记录）；
        3. Member A 再次点赞，接口放行返回 201 并原地复用旧记录，likes_count 精确恢复至 2；
        4. 数据库中总记录数始终保持为 2，不产生垃圾记录。
        """
        stats, _ = ArticleStatistics.objects.get_or_create(article=self.article, tenant=self.tenant)
        self.assertEqual(stats.likes_count, 0)

        create_url = '/api/v1/interactions/article-likes/'
        unlike_a_url = f'/api/v1/interactions/article-likes/by-article/{self.article.id}/'

        # Step 1: Member A 点赞文章
        self.client.force_authenticate(user=self.member_a)
        resp_a = self.client.post(create_url, {'article': self.article.id}, format='json')
        self.assertEqual(resp_a.status_code, status.HTTP_201_CREATED)
        like_a_id = ArticleLike.objects.get(from_member=self.member_a, article=self.article).id

        stats.refresh_from_db()
        self.assertEqual(stats.likes_count, 1, "A 点赞后 likes_count 必须为 1")

        # Step 2: Member B 点赞文章
        self.client.force_authenticate(user=self.member_b)
        resp_b = self.client.post(create_url, {'article': self.article.id}, format='json')
        self.assertEqual(resp_b.status_code, status.HTTP_201_CREATED)
        like_b_id = ArticleLike.objects.get(from_member=self.member_b, article=self.article).id

        stats.refresh_from_db()
        self.assertEqual(stats.likes_count, 2, "B 点赞后 likes_count 必须为 2")

        # Step 3: Member A 取消点赞文章
        self.client.force_authenticate(user=self.member_a)
        resp_del_a = self.client.delete(unlike_a_url)
        self.assertEqual(resp_del_a.status_code, status.HTTP_204_NO_CONTENT)

        like_a = ArticleLike.objects.get(id=like_a_id)
        self.assertTrue(like_a.is_deleted, "Member A 的点赞记录必须被软删除")

        # 核心断言：文章统计 likes_count 必须精确排除了软删除记录，变为 1
        stats.refresh_from_db()
        self.assertEqual(stats.likes_count, 1, "取消点赞后统计计数必须精确排除软删除记录，恢复为 1！")

        # Step 4: Member A 再次点赞文章（平滑恢复实证）
        resp_resurrect_a = self.client.post(create_url, {'article': self.article.id}, format='json')
        self.assertEqual(resp_resurrect_a.status_code, status.HTTP_201_CREATED, f"平滑恢复文章点赞失败: {resp_resurrect_a.data}")

        current_like_a = ArticleLike.objects.get(from_member=self.member_a, article=self.article)
        self.assertEqual(current_like_a.id, like_a_id, "文章点赞记录必须原地复用旧主键！")
        self.assertFalse(current_like_a.is_deleted, "恢复后 is_deleted 必须为 False")

        # 核心断言：文章统计 likes_count 恢复为 2
        stats.refresh_from_db()
        self.assertEqual(stats.likes_count, 2, "平滑恢复后统计计数必须精确恢复为 2！")

        # 数据库总行数保持为 2
        self.assertEqual(ArticleLike.objects.filter(article=self.article).count(), 2)

    def test_article_like_multi_user_churn_stress(self):
        """
        多用户交替取消与恢复高频对抗压力：
        A 与 B 交替取消、恢复各 3 次，每一步断言 likes_count 始终等于 active 记录数。
        """
        create_url = '/api/v1/interactions/article-likes/'
        unlike_url = f'/api/v1/interactions/article-likes/by-article/{self.article.id}/'
        stats = ArticleStatistics.objects.get(article=self.article)

        # 初始两人都点赞
        self.client.force_authenticate(user=self.member_a)
        self.client.post(create_url, {'article': self.article.id}, format='json')
        self.client.force_authenticate(user=self.member_b)
        self.client.post(create_url, {'article': self.article.id}, format='json')

        for i in range(3):
            # A 取消
            self.client.force_authenticate(user=self.member_a)
            self.client.delete(unlike_url)
            stats.refresh_from_db()
            expected = ArticleLike.objects.filter(article=self.article, is_deleted=False).count()
            self.assertEqual(stats.likes_count, expected, f"Step {i}-1 计数不一致: expected {expected}, got {stats.likes_count}")

            # B 取消
            self.client.force_authenticate(user=self.member_b)
            self.client.delete(unlike_url)
            stats.refresh_from_db()
            expected = ArticleLike.objects.filter(article=self.article, is_deleted=False).count()
            self.assertEqual(stats.likes_count, expected, f"Step {i}-2 计数不一致: expected {expected}, got {stats.likes_count}")
            self.assertEqual(stats.likes_count, 0)

            # A 恢复
            self.client.force_authenticate(user=self.member_a)
            self.client.post(create_url, {'article': self.article.id}, format='json')
            stats.refresh_from_db()
            expected = ArticleLike.objects.filter(article=self.article, is_deleted=False).count()
            self.assertEqual(stats.likes_count, expected, f"Step {i}-3 计数不一致: expected {expected}, got {stats.likes_count}")

            # B 恢复
            self.client.force_authenticate(user=self.member_b)
            self.client.post(create_url, {'article': self.article.id}, format='json')
            stats.refresh_from_db()
            expected = ArticleLike.objects.filter(article=self.article, is_deleted=False).count()
            self.assertEqual(stats.likes_count, expected, f"Step {i}-4 计数不一致: expected {expected}, got {stats.likes_count}")
            self.assertEqual(stats.likes_count, 2)

        self.assertEqual(ArticleLike.objects.filter(article=self.article).count(), 2)

    # =========================================================================
    # 4. points.services.vip_service.VipExpirationService.grant_vip_tag 失效标签复用实证
    # =========================================================================
    def test_vip_tag_soft_delete_resurrection_service(self):
        """
        验证点：TenantVIPService / VipExpirationService.grant_vip_tag 失效标签平滑复用
        实证目标：
        1. 首次授予 VIP 标签，生成 active 记录；
        2. 模拟标签失效（is_active=False, status='expired'）；
        3. 再次调用 grant_vip_tag，系统平滑复用失效记录并将 is_active 置为 True，刷新有效期；
        4. 验证主键 ID 一致，数据库中仅保留 1 条记录，未违反条件唯一约束。
        """
        vip_service = VipExpirationService()
        profile, _ = TenantUserProfile.objects.get_or_create(
            member=self.member_a,
            tenant=self.tenant
        )
        tag = UserTypeTag.objects.create(
            tag_name="Golden VIP",
            tag_code="gold_vip",
            tag_type="vip"
        )

        # 首次授予
        tag_rel = vip_service.grant_vip_tag(
            tenant_user_profile=profile,
            tag=tag,
            duration_days=30,
            grant_method='payment',
            reason="Initial VIP purchase"
        )
        self.assertIsNotNone(tag_rel.pk)
        self.assertTrue(tag_rel.is_active)
        self.assertEqual(tag_rel.status, 'active')
        orig_tag_pk = tag_rel.pk
        orig_expiry = tag_rel.expires_at

        # 模拟失效（如用户到期或管理员标记失效）
        tag_rel.is_active = False
        tag_rel.status = 'expired'
        tag_rel.save(update_fields=['is_active', 'status'])

        # 再次授予（用户重新开通）
        renewed_tag_rel = vip_service.grant_vip_tag(
            tenant_user_profile=profile,
            tag=tag,
            duration_days=60,
            grant_method='payment',
            reason="Renew VIP after expiration"
        )

        # 核心断言：平滑复用
        self.assertEqual(renewed_tag_rel.pk, orig_tag_pk, "失效 VIP 标签必须原地平滑复用，绝不能创建重复记录！")
        self.assertTrue(renewed_tag_rel.is_active, "平滑恢复后 is_active 必须为 True")
        self.assertEqual(renewed_tag_rel.status, 'active', "平滑恢复后 status 必须为 active")
        self.assertEqual(renewed_tag_rel.original_duration_days, 60, "有效期参数必须更新")
        self.assertGreater(renewed_tag_rel.expires_at, orig_expiry, "到期时间必须根据新期限延展")

        # 数据库总记录数严格保持为 1
        self.assertEqual(
            TenantUserTypeTag.objects.filter(tenant_user_profile=profile, tag=tag).count(),
            1,
            "数据库中该用户该标签关联必须严格保持唯一记录！"
        )


class AdversarialEmailDecouplingTransactionTests(TransactionTestCase):
    """
    [BUG-07 对抗实证挑战 2]
    邮件发信解耦实证（基于真实底层事务 COMMIT 与 ROLLBACK）
    验证 feedbacks.services.FeedbackService 的 on_commit 钩子机制：
    1. 事务成功 COMMIT 时，邮件回调被成功触发；
    2. 事务中途失败 ROLLBACK 时，邮件回调被自动废弃，绝不发出幽灵邮件；
    3. 邮件回调执行时，数据库数据已真正落库可查，杜绝子线程 DoesNotExist 竞态。
    """

    def setUp(self):
        self.tenant = Tenant.objects.create(
            name="Feedback Corp",
            code="fbcorp",
            status="active"
        )
        # 注意：FeedbackStatusHistory.changed_by 与 FeedbackReply.user 外键为 User (系统用户模型)
        self.sys_user = User.objects.create_user(
            username="fb_sys_admin",
            email="admin@fbcorp.com",
            password="Password123!"
        )

    # =========================================================================
    # 1. create_feedback 邮件发信解耦实证
    # =========================================================================
    @patch('feedbacks.services.EmailService.send_verification')
    def test_create_feedback_email_on_commit_success(self, mock_send_email):
        """
        验证点：创建匿名反馈在事务 COMMIT 成功时，on_commit 回调正常触发发信。
        """
        feedback_data = {
            'title': 'Test Feedback On Commit',
            'description': 'Description for on commit test',
            'feedback_type': 'bug',
            'priority': 'medium',
            'contact_email': 'anon_user@example.com',
            'contact_name': 'Anonymous User'
        }

        # 执行创建反馈（内部包裹 @transaction.atomic）
        feedback = FeedbackService.create_feedback(
            validated_data=feedback_data,
            user=None,
            tenant=self.tenant
        )

        # 在事务成功提交后，send_verification 必须被且仅被调用 1 次
        mock_send_email.assert_called_once()
        called_arg = mock_send_email.call_args[0][0]
        self.assertEqual(called_arg.id, feedback.id, "发信入参必须是已创建的 feedback 实例")
        self.assertTrue(Feedback.objects.filter(id=feedback.id).exists(), "数据库中必须已持久化")

    @patch('feedbacks.services.EmailService.send_verification')
    def test_create_feedback_email_dropped_on_transaction_rollback(self, mock_send_email):
        """
        验证点：事务中途抛出异常回滚时，挂载在 on_commit 的发信动作必须被废弃，绝不发出幽灵邮件！
        """
        feedback_data = {
            'title': 'Rollback Feedback Test',
            'description': 'Should not send email due to rollback',
            'feedback_type': 'bug',
            'priority': 'high',
            'contact_email': 'ghost_user@example.com'
        }

        # 模拟外部包裹事务中途崩溃回滚
        with self.assertRaises(RuntimeError):
            with transaction.atomic():
                feedback = FeedbackService.create_feedback(
                    validated_data=feedback_data,
                    user=None,
                    tenant=self.tenant
                )
                feedback_id = feedback.id
                # 模拟后续业务故障触发回滚
                raise RuntimeError("Simulated Database / Business Failure After Create")

        # 核心对抗断言：
        # 1. 数据库中不应存在此 feedback（已回滚）
        self.assertFalse(Feedback.objects.filter(title='Rollback Feedback Test').exists(), "事务回滚后数据不应落库")
        # 2. 邮件发信必须为 0 次调用！彻底杜绝网络幽灵通知！
        self.assertEqual(
            mock_send_email.call_count,
            0,
            "事务回滚后 on_commit 回调必须被完全废弃，绝不能触发外部发信！"
        )

    # =========================================================================
    # 2. change_status 邮件发信解耦实证
    # =========================================================================
    @patch('feedbacks.services.EmailService.send_status_notification')
    def test_change_status_email_on_commit_success_and_rollback(self, mock_send_status_email):
        """
        验证点：状态变更通知在事务成功提交时触发，事务回滚时自动作废。
        """
        feedback = Feedback.objects.create(
            title="Status Test Feedback",
            description="Testing status notifications",
            feedback_type="bug",
            priority="medium",
            status="submitted",
            tenant=self.tenant
        )

        # 场景 A: 正常流转为 resolved 并 COMMIT
        FeedbackService.change_status(
            feedback=feedback,
            new_status='resolved',
            changed_by=self.sys_user,
            reason="Bug fixed"
        )
        mock_send_status_email.assert_called_once()
        mock_send_status_email.reset_mock()

        # 场景 B: 在事务中流转为 closed 但中途抛出异常回滚
        with self.assertRaises(RuntimeError):
            with transaction.atomic():
                FeedbackService.change_status(
                    feedback=feedback,
                    new_status='closed',
                    changed_by=self.sys_user,
                    reason="Premature closure"
                )
                raise RuntimeError("Crash before status transaction completes")

        feedback.refresh_from_db()
        self.assertEqual(feedback.status, 'resolved', "回滚后 feedback 状态必须保持原样")
        self.assertEqual(mock_send_status_email.call_count, 0, "回滚时绝不能触发状态流转邮件！")

    # =========================================================================
    # 3. add_reply 邮件发信解耦实证
    # =========================================================================
    @patch('feedbacks.services.EmailService.send_reply_notification')
    def test_add_reply_email_on_commit_and_internal_note_isolation(self, mock_send_reply_email):
        """
        验证点：
        1. 公开回复正常提交时触发 on_commit 发信；
        2. 公开回复事务回滚时废弃发信；
        3. 内部备注（is_internal_note=True）即使提交也绝不发信。
        """
        feedback = Feedback.objects.create(
            title="Reply Test Feedback",
            description="Testing reply notifications",
            feedback_type="improvement",
            priority="low",
            status="in_progress",
            tenant=self.tenant
        )

        # 场景 1: 公开回复正常提交
        reply = FeedbackService.add_reply(
            feedback=feedback,
            content="We have processed your request.",
            user=self.sys_user,
            is_internal_note=False
        )
        mock_send_reply_email.assert_called_once()
        mock_send_reply_email.reset_mock()

        # 场景 2: 公开回复事务回滚
        with self.assertRaises(RuntimeError):
            with transaction.atomic():
                FeedbackService.add_reply(
                    feedback=feedback,
                    content="This reply will be rolled back.",
                    user=self.sys_user,
                    is_internal_note=False
                )
                raise RuntimeError("Abort reply transaction")

        self.assertEqual(mock_send_reply_email.call_count, 0, "回滚后回复发信必须被废弃！")

        # 场景 3: 内部备注（is_internal_note=True）即使提交也不发信
        FeedbackService.add_reply(
            feedback=feedback,
            content="Internal team review note only.",
            user=self.sys_user,
            is_internal_note=True
        )
        self.assertEqual(mock_send_reply_email.call_count, 0, "内部备注绝不能触发用户邮件发信！")

    # =========================================================================
    # 4. 数据立即可读性对抗实证 (消除 DoesNotExist 竞态)
    # =========================================================================
    def test_email_callback_sees_committed_db_data_immediately(self):
        """
        对抗验证：当 on_commit 回调执行时，数据库持久化必须已完毕，
        回调函数内直接从数据库查询 Feedback 绝不能抛出 DoesNotExist 异常。
        """
        observed_feedback_in_callback = []

        def custom_notification_receiver(fb):
            # 模拟发信进程/回调在数据库中重新读取记录
            fresh = Feedback.objects.get(id=fb.id)
            observed_feedback_in_callback.append(fresh.id)

        feedback_data = {
            'title': 'Immediate Readability Test',
            'description': 'Testing data availability at on_commit execution',
            'feedback_type': 'question',
            'priority': 'low',
            'contact_email': 'read@example.com'
        }

        with patch('feedbacks.services.EmailService.send_verification', side_effect=custom_notification_receiver):
            feedback = FeedbackService.create_feedback(
                validated_data=feedback_data,
                user=None,
                tenant=self.tenant
            )

        self.assertEqual(len(observed_feedback_in_callback), 1)
        self.assertEqual(observed_feedback_in_callback[0], feedback.id)
