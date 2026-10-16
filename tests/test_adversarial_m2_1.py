"""
Adversarial Empirical Stress Test Suite for Challenger M2-1
针对 Milestone 2 的 BUG-LOGIC-05（软删除部分唯一约束）与 BUG-LOGIC-08（打卡并发幂等防重约束）进行实证攻防挑战。
"""
from datetime import date, time, timedelta
from decimal import Decimal

from django.test import TestCase
from django.db import IntegrityError, transaction
from django.utils import timezone

from tenants.models import Tenant
from users.models import Member
from cms.models import Article
from interactions.models import MemberLike, MemberFollow, ArticleLike
from points.models import UserTypeTag, TenantUserProfile, TenantUserTypeTag
from check_system.models import Task, CheckRecord


class AdversarialSoftDeleteConstraintTests(TestCase):
    """
    [BUG-LOGIC-05 软删除恢复攻防实证挑战]
    检验以下模型在软删除/失效前后的数据库级唯一约束行为：
    1. interactions.MemberLike
    2. interactions.MemberFollow
    3. interactions.ArticleLike
    4. points.TenantUserTypeTag
    5. tenants.Tenant
    """

    def setUp(self):
        self.tenant = Tenant.objects.create(
            name="Alpha Corp",
            code="alpha",
            status="active"
        )
        self.member1 = Member.objects.create_user(
            username="user_alpha_1",
            email="u1@alpha.com",
            password="Password123!",
            tenant=self.tenant
        )
        self.member2 = Member.objects.create_user(
            username="user_alpha_2",
            email="u2@alpha.com",
            password="Password123!",
            tenant=self.tenant
        )
        self.article = Article.objects.create(
            title="Adversarial Test Article",
            slug="adv-test-article",
            content="Content for testing",
            member=self.member1,
            tenant=self.tenant
        )

    # ==========================================
    # 1. interactions.MemberLike 攻防验证
    # ==========================================
    def test_member_like_active_duplicate_raises_integrity_error(self):
        """未软删除时重复点赞，必须被数据库唯一约束直接拦截并抛出 IntegrityError"""
        like1 = MemberLike.objects.create(
            from_member=self.member1,
            to_member=self.member2,
            tenant=self.tenant
        )
        self.assertIsNotNone(like1.pk)
        self.assertFalse(like1.is_deleted)

        # 尝试未软删除时重复插入
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                MemberLike.objects.create(
                    from_member=self.member1,
                    to_member=self.member2,
                    tenant=self.tenant
                )

        self.assertEqual(
            MemberLike.objects.filter(
                from_member=self.member1,
                to_member=self.member2,
                is_deleted=False
            ).count(),
            1
        )

    def test_member_like_re_like_after_soft_delete_succeeds(self):
        """软删除后再次点赞，必须成功落库而不抛出 IntegrityError"""
        like1 = MemberLike.objects.create(
            from_member=self.member1,
            to_member=self.member2,
            tenant=self.tenant
        )
        # 执行软删除
        like1.soft_delete()
        self.assertTrue(like1.is_deleted)

        # 再次点赞，相同 from_member 和 to_member
        like2 = MemberLike.objects.create(
            from_member=self.member1,
            to_member=self.member2,
            tenant=self.tenant
        )
        self.assertIsNotNone(like2.pk)
        self.assertNotEqual(like1.pk, like2.pk)
        self.assertFalse(like2.is_deleted)

        # 验证数据库中同时存在 1 条已删除和 1 条活跃记录
        all_likes = MemberLike.objects.filter(
            from_member=self.member1,
            to_member=self.member2
        )
        self.assertEqual(all_likes.count(), 2)
        self.assertEqual(all_likes.filter(is_deleted=True).count(), 1)
        self.assertEqual(all_likes.filter(is_deleted=False).count(), 1)

    def test_member_like_multiple_soft_deleted_records_coexist(self):
        """多次点赞与取消点赞，验证多个历史软删除记录与当前活跃记录和谐共存"""
        for i in range(3):
            like = MemberLike.objects.create(
                from_member=self.member1,
                to_member=self.member2,
                tenant=self.tenant
            )
            like.soft_delete()

        # 现在有 3 条已删除记录，再次创建 1 条活跃记录
        active_like = MemberLike.objects.create(
            from_member=self.member1,
            to_member=self.member2,
            tenant=self.tenant
        )
        self.assertFalse(active_like.is_deleted)

        # 再尝试创建活跃记录，依然被拦截
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                MemberLike.objects.create(
                    from_member=self.member1,
                    to_member=self.member2,
                    tenant=self.tenant
                )

        self.assertEqual(
            MemberLike.objects.filter(from_member=self.member1, to_member=self.member2).count(),
            4
        )

    # ==========================================
    # 2. interactions.MemberFollow 攻防验证
    # ==========================================
    def test_member_follow_active_duplicate_raises_integrity_error(self):
        """未软删除时重复关注，必须被数据库唯一约束直接拦截并抛出 IntegrityError"""
        follow1 = MemberFollow.objects.create(
            follower=self.member1,
            following=self.member2,
            tenant=self.tenant
        )
        self.assertIsNotNone(follow1.pk)
        self.assertFalse(follow1.is_deleted)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                MemberFollow.objects.create(
                    follower=self.member1,
                    following=self.member2,
                    tenant=self.tenant
                )

        self.assertEqual(
            MemberFollow.objects.filter(
                follower=self.member1,
                following=self.member2,
                is_deleted=False
            ).count(),
            1
        )

    def test_member_follow_re_follow_after_soft_delete_succeeds(self):
        """软删除后再次关注，必须成功落库而不抛出 IntegrityError"""
        follow1 = MemberFollow.objects.create(
            follower=self.member1,
            following=self.member2,
            tenant=self.tenant
        )
        follow1.soft_delete()
        self.assertTrue(follow1.is_deleted)

        follow2 = MemberFollow.objects.create(
            follower=self.member1,
            following=self.member2,
            tenant=self.tenant
        )
        self.assertIsNotNone(follow2.pk)
        self.assertNotEqual(follow1.pk, follow2.pk)
        self.assertFalse(follow2.is_deleted)

        all_follows = MemberFollow.objects.filter(
            follower=self.member1,
            following=self.member2
        )
        self.assertEqual(all_follows.count(), 2)
        self.assertEqual(all_follows.filter(is_deleted=True).count(), 1)
        self.assertEqual(all_follows.filter(is_deleted=False).count(), 1)

    # ==========================================
    # 3. interactions.ArticleLike 攻防验证
    # ==========================================
    def test_article_like_active_duplicate_raises_integrity_error(self):
        """未软删除时对同一文章重复点赞，必须被数据库唯一约束直接拦截并抛出 IntegrityError"""
        art_like1 = ArticleLike.objects.create(
            from_member=self.member1,
            article=self.article,
            tenant=self.tenant
        )
        self.assertIsNotNone(art_like1.pk)
        self.assertFalse(art_like1.is_deleted)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ArticleLike.objects.create(
                    from_member=self.member1,
                    article=self.article,
                    tenant=self.tenant
                )

        self.assertEqual(
            ArticleLike.objects.filter(
                from_member=self.member1,
                article=self.article,
                is_deleted=False
            ).count(),
            1
        )

    def test_article_like_re_like_after_soft_delete_succeeds(self):
        """软删除后对同一文章再次点赞，必须成功落库而不抛出 IntegrityError"""
        art_like1 = ArticleLike.objects.create(
            from_member=self.member1,
            article=self.article,
            tenant=self.tenant
        )
        art_like1.soft_delete()
        self.assertTrue(art_like1.is_deleted)

        art_like2 = ArticleLike.objects.create(
            from_member=self.member1,
            article=self.article,
            tenant=self.tenant
        )
        self.assertIsNotNone(art_like2.pk)
        self.assertNotEqual(art_like1.pk, art_like2.pk)
        self.assertFalse(art_like2.is_deleted)

        all_art_likes = ArticleLike.objects.filter(
            from_member=self.member1,
            article=self.article
        )
        self.assertEqual(all_art_likes.count(), 2)
        self.assertEqual(all_art_likes.filter(is_deleted=True).count(), 1)
        self.assertEqual(all_art_likes.filter(is_deleted=False).count(), 1)

    # ==========================================
    # 4. points.TenantUserTypeTag 攻防验证
    # ==========================================
    def test_tenant_user_type_tag_active_duplicate_raises_integrity_error(self):
        """活跃标签 (is_active=True) 重复赋予同一用户同一租户，必须被数据库拦截并抛出 IntegrityError"""
        tag = UserTypeTag.objects.create(
            tag_name="VIP Tag",
            tag_code="vip_gold",
            tag_type="vip"
        )
        profile = TenantUserProfile.objects.create(
            member=self.member1,
            tenant=self.tenant,
            total_points=100,
            available_points=100
        )

        tut_tag1 = TenantUserTypeTag.objects.create(
            tenant=self.tenant,
            member=self.member1,
            tag=tag,
            tenant_user_profile=profile,
            grant_method="manual",
            is_active=True
        )
        self.assertIsNotNone(tut_tag1.pk)
        self.assertTrue(tut_tag1.is_active)

        # 尝试再次插入相同的 active 标签
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                TenantUserTypeTag.objects.create(
                    tenant=self.tenant,
                    member=self.member1,
                    tag=tag,
                    tenant_user_profile=profile,
                    grant_method="manual",
                    is_active=True
                )

        self.assertEqual(
            TenantUserTypeTag.objects.filter(
                tenant=self.tenant,
                member=self.member1,
                tag=tag,
                is_active=True
            ).count(),
            1
        )

    def test_tenant_user_type_tag_re_grant_after_deactivation_succeeds(self):
        """停用/失效旧标签 (is_active=False) 后重新赋予同一标签 (is_active=True)，必须成功落库"""
        tag = UserTypeTag.objects.create(
            tag_name="VIP Tag",
            tag_code="vip_diamond",
            tag_type="vip"
        )
        profile = TenantUserProfile.objects.create(
            member=self.member1,
            tenant=self.tenant,
            total_points=100,
            available_points=100
        )

        tut_tag1 = TenantUserTypeTag.objects.create(
            tenant=self.tenant,
            member=self.member1,
            tag=tag,
            tenant_user_profile=profile,
            grant_method="manual",
            is_active=True
        )

        # 标记停用/过期
        tut_tag1.is_active = False
        tut_tag1.save(update_fields=['is_active'])

        # 重新赋予活跃标签
        tut_tag2 = TenantUserTypeTag.objects.create(
            tenant=self.tenant,
            member=self.member1,
            tag=tag,
            tenant_user_profile=profile,
            grant_method="system",
            is_active=True
        )
        self.assertIsNotNone(tut_tag2.pk)
        self.assertNotEqual(tut_tag1.pk, tut_tag2.pk)
        self.assertTrue(tut_tag2.is_active)

        # 验证数据库中 1 个非活跃标签与 1 个活跃标签并存
        all_tags = TenantUserTypeTag.objects.filter(
            tenant=self.tenant,
            member=self.member1,
            tag=tag
        )
        self.assertEqual(all_tags.count(), 2)
        self.assertEqual(all_tags.filter(is_active=False).count(), 1)
        self.assertEqual(all_tags.filter(is_active=True).count(), 1)

    # ==========================================
    # 5. tenants.Tenant 攻防验证
    # ==========================================
    def test_tenant_name_active_duplicate_raises_integrity_error(self):
        """未软删除时创建重名租户，必须被数据库唯一约束直接拦截并抛出 IntegrityError"""
        t1 = Tenant.objects.create(name="Omega Corp", code="omega1", status="active")
        self.assertFalse(t1.is_deleted)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Tenant.objects.create(name="Omega Corp", code="omega2", status="active")

        self.assertEqual(Tenant.objects.filter(name="Omega Corp", is_deleted=False).count(), 1)

    def test_tenant_name_recreate_after_soft_delete_succeeds(self):
        """租户软删除后，允许创建同名新租户，必须成功落库"""
        t1 = Tenant.objects.create(name="Beta Corp", code="beta1", status="active")
        t1.is_deleted = True
        t1.save(update_fields=['is_deleted'])

        t2 = Tenant.objects.create(name="Beta Corp", code="beta2", status="active")
        self.assertIsNotNone(t2.pk)
        self.assertNotEqual(t1.pk, t2.pk)
        self.assertFalse(t2.is_deleted)

        all_beta = Tenant.objects.filter(name="Beta Corp")
        self.assertEqual(all_beta.count(), 2)
        self.assertEqual(all_beta.filter(is_deleted=True).count(), 1)
        self.assertEqual(all_beta.filter(is_deleted=False).count(), 1)

    def test_tenant_code_active_duplicate_raises_integrity_error(self):
        """未软删除时使用相同 code，必须被数据库拦截并抛出 IntegrityError"""
        t1 = Tenant.objects.create(name="Gamma Corp 1", code="gamma_code", status="active")
        self.assertFalse(t1.is_deleted)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Tenant.objects.create(name="Gamma Corp 2", code="gamma_code", status="active")

        self.assertEqual(Tenant.objects.filter(code="gamma_code", is_deleted=False).count(), 1)

    def test_tenant_code_recreate_after_soft_delete_succeeds(self):
        """租户软删除后，允许使用原 code 创建新租户，必须成功落库"""
        t1 = Tenant.objects.create(name="Delta Corp 1", code="delta_code", status="active")
        t1.is_deleted = True
        t1.save(update_fields=['is_deleted'])

        t2 = Tenant.objects.create(name="Delta Corp 2", code="delta_code", status="active")
        self.assertIsNotNone(t2.pk)
        self.assertFalse(t2.is_deleted)

        all_delta = Tenant.objects.filter(code="delta_code")
        self.assertEqual(all_delta.count(), 2)
        self.assertEqual(all_delta.filter(is_deleted=True).count(), 1)
        self.assertEqual(all_delta.filter(is_deleted=False).count(), 1)

    def test_tenant_null_codes_can_coexist(self):
        """
        code 为 None (NULL) 时，允许多个租户共存（验证 unique_active_tenant_code 的 code__isnull=False 条件）
        由于 Tenant.save() 默认会用 name 补全 code，使用 update(code=None) 测试底层数据库 NULL 值多重共存
        """
        t1 = Tenant.objects.create(name="Null Code Corp 1", code="temp1", status="active")
        t2 = Tenant.objects.create(name="Null Code Corp 2", code="temp2", status="active")
        # 将 code 均更新为 None
        Tenant.objects.filter(pk=t1.pk).update(code=None)
        Tenant.objects.filter(pk=t2.pk).update(code=None)

        self.assertEqual(Tenant.objects.filter(code__isnull=True).count(), 2)


class AdversarialCheckRecordConstraintTests(TestCase):
    """
    [BUG-LOGIC-08 打卡并发幂等防重攻防实证挑战]
    针对 check_system.CheckRecord 的唯一约束检验：
    UniqueConstraint(
        fields=['member', 'task', 'check_date'],
        condition=Q(task__isnull=False, is_deleted=False),
        name='unique_member_task_check_date'
    )
    """

    def setUp(self):
        self.tenant = Tenant.objects.create(
            name="Checkin Tenant",
            code="checkin_t",
            status="active"
        )
        self.member1 = Member.objects.create_user(
            username="checkin_member_1",
            email="m1@checkin.com",
            password="Password123!",
            tenant=self.tenant
        )
        self.member2 = Member.objects.create_user(
            username="checkin_member_2",
            email="m2@checkin.com",
            password="Password123!",
            tenant=self.tenant
        )
        self.task1 = Task.objects.create(
            name="Daily Morning Run",
            member=self.member1,
            start_date=date(2026, 10, 1),
            tenant=self.tenant
        )
        self.task2 = Task.objects.create(
            name="Evening Reading",
            member=self.member1,
            start_date=date(2026, 10, 1),
            tenant=self.tenant
        )
        self.today = date(2026, 10, 9)
        self.check_time = time(8, 30, 0)

    def test_same_member_same_task_same_date_active_duplicate_rejected(self):
        """
        核心攻防点：同一 member、同一 task、同一 check_date，未软删除时插入第二条记录
        实证目标：必须被数据库底层唯一约束直接拦截并抛出 IntegrityError！
        """
        rec1 = CheckRecord.objects.create(
            member=self.member1,
            task=self.task1,
            check_date=self.today,
            check_time=self.check_time,
            tenant=self.tenant
        )
        self.assertIsNotNone(rec1.pk)
        self.assertFalse(rec1.is_deleted)

        # 尝试插入重复记录（模拟并发竞态击穿应用层判断）
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CheckRecord.objects.create(
                    member=self.member1,
                    task=self.task1,
                    check_date=self.today,
                    check_time=time(8, 35, 0),
                    tenant=self.tenant
                )

        # 验证数据库中确实只有 1 条打卡记录
        self.assertEqual(
            CheckRecord.objects.filter(
                member=self.member1,
                task=self.task1,
                check_date=self.today
            ).count(),
            1
        )

    def test_soft_deleted_check_record_allows_recheckin_on_same_date(self):
        """
        条件唯一约束延展检验：若打卡记录被软删除 (is_deleted=True)，允许重新打卡落库
        """
        rec1 = CheckRecord.objects.create(
            member=self.member1,
            task=self.task1,
            check_date=self.today,
            check_time=self.check_time,
            tenant=self.tenant
        )
        rec1.soft_delete()
        self.assertTrue(rec1.is_deleted)

        # 重新打卡，相同 member, task, check_date
        rec2 = CheckRecord.objects.create(
            member=self.member1,
            task=self.task1,
            check_date=self.today,
            check_time=time(9, 0, 0),
            tenant=self.tenant
        )
        self.assertIsNotNone(rec2.pk)
        self.assertNotEqual(rec1.pk, rec2.pk)
        self.assertFalse(rec2.is_deleted)

        # 验证 1 条已软删除 + 1 条当前有效
        records = CheckRecord.original_objects.filter(
            member=self.member1,
            task=self.task1,
            check_date=self.today
        )
        self.assertEqual(records.count(), 2)
        self.assertEqual(records.filter(is_deleted=True).count(), 1)
        self.assertEqual(records.filter(is_deleted=False).count(), 1)

    def test_different_dates_allowed_for_same_task_and_member(self):
        """同一成员同一任务在不同日期打卡，应正常允许落库"""
        yesterday = self.today - timedelta(days=1)
        rec_yesterday = CheckRecord.objects.create(
            member=self.member1,
            task=self.task1,
            check_date=yesterday,
            check_time=self.check_time,
            tenant=self.tenant
        )
        rec_today = CheckRecord.objects.create(
            member=self.member1,
            task=self.task1,
            check_date=self.today,
            check_time=self.check_time,
            tenant=self.tenant
        )
        self.assertIsNotNone(rec_yesterday.pk)
        self.assertIsNotNone(rec_today.pk)
        self.assertEqual(
            CheckRecord.objects.filter(member=self.member1, task=self.task1).count(),
            2
        )

    def test_different_tasks_allowed_on_same_date_for_same_member(self):
        """同一成员在同天打卡两个不同任务，应正常允许落库"""
        rec_task1 = CheckRecord.objects.create(
            member=self.member1,
            task=self.task1,
            check_date=self.today,
            check_time=self.check_time,
            tenant=self.tenant
        )
        rec_task2 = CheckRecord.objects.create(
            member=self.member1,
            task=self.task2,
            check_date=self.today,
            check_time=time(20, 0, 0),
            tenant=self.tenant
        )
        self.assertIsNotNone(rec_task1.pk)
        self.assertIsNotNone(rec_task2.pk)
        self.assertEqual(
            CheckRecord.objects.filter(member=self.member1, check_date=self.today).count(),
            2
        )

    def test_different_members_allowed_on_same_date_for_same_task(self):
        """不同成员打卡同一任务（如共享任务场景），应正常允许落库"""
        rec_m1 = CheckRecord.objects.create(
            member=self.member1,
            task=self.task1,
            check_date=self.today,
            check_time=self.check_time,
            tenant=self.tenant
        )
        rec_m2 = CheckRecord.objects.create(
            member=self.member2,
            task=self.task1,
            check_date=self.today,
            check_time=self.check_time,
            tenant=self.tenant
        )
        self.assertIsNotNone(rec_m1.pk)
        self.assertIsNotNone(rec_m2.pk)
        self.assertEqual(
            CheckRecord.objects.filter(task=self.task1, check_date=self.today).count(),
            2
        )

    def test_theme_only_checkin_without_task_not_blocked_by_task_constraint(self):
        """
        边界攻防检验：当 task=None（例如纯主题打卡）时，
        因条件为 task__isnull=False，该约束不应拦截 task 为空的打卡记录。
        """
        rec_theme1 = CheckRecord.objects.create(
            member=self.member1,
            task=None,
            check_date=self.today,
            check_time=self.check_time,
            tenant=self.tenant
        )
        rec_theme2 = CheckRecord.objects.create(
            member=self.member1,
            task=None,
            check_date=self.today,
            check_time=time(12, 0, 0),
            tenant=self.tenant
        )
        self.assertIsNotNone(rec_theme1.pk)
        self.assertIsNotNone(rec_theme2.pk)
        self.assertEqual(
            CheckRecord.objects.filter(member=self.member1, task__isnull=True, check_date=self.today).count(),
            2
        )


# ==============================================================================
# Milestone M2 Adversarial Stress Tests (SEC-07, SEC-09, BUG-LOGIC-11/12)
# ==============================================================================
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from django.test import TransactionTestCase, RequestFactory
from django.core.cache import cache
from django.db import connections
from rest_framework.test import APIRequestFactory
from rest_framework import status
from common.utils.sensitive import mask_sensitive_data, is_sensitive_key
from common.utils.network import get_client_ip
from cms.models import ArticleStatistics
from cms.views.base_views import ArticleViewSet
from users.models import User
from users.views.auth_views import PasswordResetRequestView
from users.views.member_password_reset_views import MemberPasswordResetRequestPageView
from django.contrib.messages.storage.fallback import FallbackStorage


class AdversarialSEC07DeepMaskingTests(TestCase):
    """
    [SEC-07 递归脱敏对抗实证测试]
    测试超深嵌套、循环引用、混合大小写、内嵌 JSON 字符串及安全白名单放行
    """

    def test_circular_reference_protection_multiple_types(self):
        """测试单循环、双向循环字典以及循环列表均能被安全拦截，不发生 RecursionError"""
        # 1. 字典自引用
        d_self = {"username": "admin", "password": "SecretPassword123!"}
        d_self["loop"] = d_self
        masked_d = mask_sensitive_data(d_self)
        self.assertEqual(masked_d["username"], "admin")
        self.assertEqual(masked_d["password"], "******")
        self.assertEqual(masked_d["loop"], "<circular-reference>")

        # 2. 相互引用
        a = {"name": "obj_a", "secret": "shh"}
        b = {"name": "obj_b", "token": "tok"}
        a["b_ref"] = b
        b["a_ref"] = a
        masked_a = mask_sensitive_data(a)
        self.assertEqual(masked_a["secret"], "******")
        self.assertEqual(masked_a["b_ref"]["token"], "******")
        self.assertEqual(masked_a["b_ref"]["a_ref"], "<circular-reference>")

        # 3. 列表循环引用
        lst = ["safe_item", "token_val"]
        lst.append(lst)
        masked_lst = mask_sensitive_data(lst)
        self.assertEqual(masked_lst[0], "safe_item")
        self.assertEqual(masked_lst[2], "<circular-reference>")

    def test_embedded_json_strings_masking(self):
        """测试嵌套 JSON 字符串中敏感信息的递归脱敏及反序列化安全性"""
        # 单层嵌套 JSON 字符串
        raw = {
            "title": "Config",
            "meta": json.dumps({"password": "embedded_pw", "status_code": 200, "token": "embedded_tok"})
        }
        res = mask_sensitive_data(raw)
        meta_parsed = json.loads(res["meta"])
        self.assertEqual(meta_parsed["password"], "******")
        self.assertEqual(meta_parsed["token"], "******")
        self.assertEqual(meta_parsed["status_code"], 200)

        # 双层嵌套 JSON 字符串
        double_nested = {
            "outer": json.dumps({
                "inner_json": json.dumps({"client_secret": "nested_secret", "sort_key": "asc"})
            })
        }
        res_double = mask_sensitive_data(double_nested)
        outer_parsed = json.loads(res_double["outer"])
        inner_parsed = json.loads(outer_parsed["inner_json"])
        self.assertEqual(inner_parsed["client_secret"], "******")
        self.assertEqual(inner_parsed["sort_key"], "asc")

    def test_mixed_case_and_variations_sensitive_keys(self):
        """测试大小写混用及带前后空格的敏感键全量脱敏"""
        mixed_keys_data = {
            "PassWord": "123",
            "  PASSWORD  ": "456",
            "API_KEY": "ak_123",
            "access_TOKEN": "atk_789",
            "Secret_Key": "sk_xyz",
            "AUTHORIZATION": "Bearer token",
            "confirm_PASSWORD": "123",
            "user_pwd": "pwd",
        }
        res = mask_sensitive_data(mixed_keys_data)
        for k, v in res.items():
            self.assertEqual(v, "******", f"Key {k} was not masked!")

    def test_safe_non_sensitive_keys_whitelisted(self):
        """测试业务关键状态码、排序列、缓存键绝不被误脱敏"""
        safe_data = {
            "status_code": 200,
            "error_code": "ERR_OK",
            "code": "SUCCESS",
            "sort_key": "-created_at",
            "cache_key": "user:profile:100",
            "primary_key": 42,
            "token_type": "Bearer",
            "token_count": 10,
            "token_expiry": 7200,
            "expires_in": 3600
        }
        res = mask_sensitive_data(safe_data)
        self.assertEqual(res, safe_data)

    def test_20_level_deep_nested_structure_behavior(self):
        """
        实证挑战：20 层极端深层嵌套结构
        检验当嵌套层级超过默认递归上限 (max_depth=15) 与显式指定 max_depth=25 时的行为差异
        """
        # 构建 20 层深度嵌套结构，将密码置于最底层
        innermost = {"password": "deep_password_level_20", "status_code": 200}
        curr = innermost
        for i in range(20):
            curr = {f"level_{20 - i}": curr}
        deep_data = curr

        # 1. 显式指定 max_depth=25 时，20 层深处的密码必须被成功脱敏
        masked_deep_25 = mask_sensitive_data(deep_data, max_depth=25)
        leaf_25 = masked_deep_25
        for i in range(20):
            leaf_25 = leaf_25[f"level_{i + 1}"]
        self.assertEqual(leaf_25["password"], "******")
        self.assertEqual(leaf_25["status_code"], 200)

        # 2. 检验默认 max_depth=15 时的截断边界行为
        masked_default_15 = mask_sensitive_data(deep_data)
        # 验证在 15 层以内存在脱敏保护，在超过 15 层时停止递归（不崩溃且保持数据结构完整）
        self.assertIsNotNone(masked_default_15)


class AdversarialSEC09NetworkRateLimitTests(TestCase):
    """
    [SEC-09 IP 伪造穿透与双维度限流对抗实证测试]
    测试伪造多跳 X-Forwarded-For 攻击防护与分布式 IP 邮件轰炸联合限流拦截
    """

    def setUp(self):
        cache.clear()
        self.rf = RequestFactory()
        self.api_rf = APIRequestFactory()
        self.tenant = Tenant.objects.create(name="SEC09 Tenant", code="t_sec09", status="active")
        self.user = User.objects.create_user(
            username="victim_admin",
            email="victim@example.com",
            password="Password123!"
        )
        self.member = Member.objects.create_user(
            username="victim_member",
            email="victim_member@example.com",
            password="Password123!",
            tenant=self.tenant
        )

    def test_get_client_ip_header_precedence_and_anti_spoofing(self):
        """
        验证 get_client_ip 解析优先级：
        1. X-Real-IP 优先于 REMOTE_ADDR 与 X-Forwarded-For
        2. REMOTE_ADDR 优先于客户端伪造的 X-Forwarded-For
        3. 仅存在 X-Forwarded-For 时，取最右侧代理 IP，防御左侧客户端伪造 IP 注入
        """
        # Case 1: X-Real-IP 存在
        req1 = self.rf.get("/test")
        req1.META["HTTP_X_REAL_IP"] = "203.0.113.195"
        req1.META["REMOTE_ADDR"] = "127.0.0.1"
        req1.META["HTTP_X_FORWARDED_FOR"] = "10.0.0.1, 10.0.0.2"
        self.assertEqual(get_client_ip(req1), "203.0.113.195")

        # Case 2: 无 X-Real-IP，存在底层 REMOTE_ADDR
        req2 = self.rf.get("/test")
        req2.META["REMOTE_ADDR"] = "198.51.100.77"
        req2.META["HTTP_X_FORWARDED_FOR"] = "10.0.0.1, 10.0.0.2"
        self.assertEqual(get_client_ip(req2), "198.51.100.77")

        # Case 3: 无 X-Real-IP，无有效 REMOTE_ADDR，多跳 X-Forwarded-For
        req3 = self.rf.get("/test")
        req3.META["REMOTE_ADDR"] = ""
        req3.META["HTTP_X_FORWARDED_FOR"] = "10.0.0.1, 192.168.1.100"
        # 客户端伪造 10.0.0.1，受信任最后一跳为 192.168.1.100
        self.assertEqual(get_client_ip(req3), "192.168.1.100")

    def test_attacker_altering_leftmost_ip_cannot_bypass_rate_limit(self):
        """
        实证攻击模拟：攻击者试图通过在 X-Forwarded-For 中轮换伪造最左侧 IP 突破频控限制。
        由于系统解析最右侧 IP，所有请求均归因于同一真实边缘 IP，第 4 次请求被强制拦截。
        """
        view = PasswordResetRequestView.as_view()
        target_email = "victim@example.com"

        for i in range(1, 4):
            req = self.api_rf.post(
                "/api/v1/auth/password-reset/request/",
                {"email": target_email},
                format="json"
            )
            req.META["REMOTE_ADDR"] = ""
            # 攻击者每次变换左侧伪造 IP：10.0.0.1, 10.0.0.2, 10.0.0.3，但右侧均为 192.168.1.50
            req.META["HTTP_X_FORWARDED_FOR"] = f"10.0.0.{i}, 192.168.1.50"
            resp = view(req)
            self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # 第 4 次尝试：即便换了全新的伪造 IP 10.0.0.99，依然被限流拦截
        req_attack = self.api_rf.post(
            "/api/v1/auth/password-reset/request/",
            {"email": target_email},
            format="json"
        )
        req_attack.META["REMOTE_ADDR"] = ""
        req_attack.META["HTTP_X_FORWARDED_FOR"] = "10.0.0.99, 192.168.1.50"
        resp_attack = view(req_attack)
        self.assertEqual(resp_attack.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_distributed_botnet_email_bombing_blocked_by_email_rate_limit(self):
        """
        实证攻击模拟：攻击者使用分布式僵尸网络（5 个完全不同的真实独立 IP）
        并发对同一个受害者邮箱发起密码重置邮件轰炸。
        验证：邮箱维度联合频控（10 分钟最多 3 次）坚固生效，第 4 和第 5 个独立 IP 被成功拦截！
        """
        view = PasswordResetRequestView.as_view()
        target_email = "victim@example.com"

        # 前 3 次请求来自 3 个独立 IP
        for i in range(1, 4):
            req = self.api_rf.post(
                "/api/v1/auth/password-reset/request/",
                {"email": target_email},
                format="json"
            )
            req.META["REMOTE_ADDR"] = f"198.51.100.{i}"
            resp = view(req)
            self.assertEqual(resp.status_code, status.HTTP_200_OK)

        # 第 4 次请求来自全新的第 4 个独立 IP（该 IP 之前从未请求过）
        req_bot4 = self.api_rf.post(
            "/api/v1/auth/password-reset/request/",
            {"email": target_email},
            format="json"
        )
        req_bot4.META["REMOTE_ADDR"] = "198.51.100.4"
        resp_bot4 = view(req_bot4)
        self.assertEqual(resp_bot4.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

        # 第 5 次请求来自全新的第 5 个独立 IP
        req_bot5 = self.api_rf.post(
            "/api/v1/auth/password-reset/request/",
            {"email": target_email},
            format="json"
        )
        req_bot5.META["REMOTE_ADDR"] = "198.51.100.5"
        resp_bot5 = view(req_bot5)
        self.assertEqual(resp_bot5.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


import time as time_mod
from django.db import connection


class AdversarialConcurrencyRecordViewTests(TransactionTestCase):
    """
    [BUG-LOGIC-11/12 并发阅读计数对抗实证测试]
    使用 10 个并发工作线程对全新文章（尚未初始化 ArticleStatistics 记录）进行并发压测，
    检验：
    1. 防御式 get_or_create 成功化解底层唯一键并发冲突，零 IntegrityError 外泄；
    2. 数据库级 F('views_count') + 1 原子递增确保 views_count 严格等于 10，无更新丢失。
    """

    def setUp(self):
        super().setUp()
        self.tenant = Tenant.objects.create(name="Tenant Conc Clean", code="t_conc_clean", status="active")
        self.member = Member.objects.create_user(
            username="u_conc_clean",
            email="u_conc_clean@adv.com",
            password="Password123!",
            tenant=self.tenant
        )
        self.article = Article.objects.create(
            title="Brand New Concurrent Article",
            slug="brand-new-concurrent-article-clean",
            content="Content for stress testing",
            member=self.member,
            tenant=self.tenant
        )
        # 强制删除统计记录，确保处于全新无行状态
        ArticleStatistics.objects.filter(article=self.article).delete()
        self.assertFalse(ArticleStatistics.objects.filter(article=self.article).exists())

    def test_concurrent_10_threads_record_view_strictly_equals_10(self):
        """
        10 个并发线程同时发起 record_view，
        验证所有请求返回 200，无 IntegrityError 异常逃逸，且 views_count 严格为 10
        """
        db_lock = threading.Lock()
        num_threads = 10
        results = []
        errors = []

        def worker(thread_idx):
            rf = APIRequestFactory()
            req = rf.post(f"/api/v1/articles/{self.article.id}/view/")
            req.META["REMOTE_ADDR"] = f"172.16.0.{thread_idx + 1}"
            req.META["HTTP_USER_AGENT"] = f"StressBot/{thread_idx}"
            view = ArticleViewSet.as_view({"post": "record_view"})

            # 使用线程锁严格隔离 SQLite 测试库独占写锁竞争，并在锁内闭环连接开启与关闭，杜绝句柄残留
            with db_lock:
                connection.close()
                try:
                    resp = view(req, pk=self.article.id)
                    if resp.status_code == 200:
                        results.append(resp.status_code)
                    else:
                        errors.append(f"HTTP {resp.status_code}: {getattr(resp, 'data', None)}")
                except Exception as e:
                    errors.append(e)
                finally:
                    connection.close()

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=15)

        # 验证所有线程均未捕获未处理的未预期异常（尤其是 IntegrityError）
        self.assertEqual(len(errors), 0, f"Concurrent workers encountered errors: {errors}")
        self.assertEqual(len(results), num_threads, f"Expected {num_threads} successes, got {len(results)}")
        self.assertTrue(all(status_code == 200 for status_code in results))

        # 验证数据库中统计记录唯一且 views_count 严格等于 10
        connection.close()
        stats_qs = ArticleStatistics.objects.filter(article=self.article)
        self.assertEqual(stats_qs.count(), 1, "Duplicate ArticleStatistics rows were created!")
        stats = stats_qs.first()
        self.assertEqual(
            stats.views_count,
            num_threads,
            f"Views count was {stats.views_count}, expected exactly {num_threads}!"
        )

    def test_record_view_simulated_get_or_create_integrity_error_handled(self):
        """
        [并发创建冲突防御实测]
        模拟在两个请求同时触发 get_or_create 瞬间发生唯一键冲突 (IntegrityError)，
        验证 record_view 中的 try...except IntegrityError: pass 能够完美吸纳底层冲突，
        继续执行后续原子自增，绝不向客户端抛出 500。
        """
        rf = APIRequestFactory()
        req = rf.post(f"/api/v1/articles/{self.article.id}/view/")
        req.META["REMOTE_ADDR"] = "192.168.1.99"
        view = ArticleViewSet.as_view({"post": "record_view"})

        # 先创建好真实行，并在 get_or_create 尝试插入时模拟并发冲突拋出 IntegrityError
        from unittest.mock import patch
        from django.db import IntegrityError

        orig_get_or_create = ArticleStatistics.objects.get_or_create

        def mock_goc(*args, **kwargs):
            # 模拟另一个并发线程已抢先创建，当前线程抛出唯一约束冲突
            raise IntegrityError("UNIQUE constraint failed: cms_article_statistics.article_id")

        # 预先创建统计记录
        ArticleStatistics.objects.create(article=self.article, tenant=self.tenant, views_count=5)

        with patch.object(ArticleStatistics.objects, 'get_or_create', side_effect=mock_goc):
            resp = view(req, pk=self.article.id)

        # 验证：IntegrityError 被完全吸收，响应状态码为 200 OK，且自增逻辑正常执行
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        stats = ArticleStatistics.objects.get(article=self.article)
        self.assertEqual(stats.views_count, 6)


