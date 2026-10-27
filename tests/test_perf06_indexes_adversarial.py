"""
Milestone 2 攻防挑战测试套件 (Challenger M2-2)
覆盖重点:
1. PERF-06 高频复合索引在 SQLite 物理表中的真实存在性校验 (PRAGMA index_list & PRAGMA index_info)
2. 典型高频查询 QuerySet explain() 真实执行计划命中实证 (SQLite EXPLAIN QUERY PLAN)
3. BUG-LOGIC-08 CheckRecord 复合唯一约束防重与并发防刷对抗实证
4. BUG-LOGIC-05 软删除与条件唯一约束多重对抗实证 (interactions, tenants)
"""
from datetime import date, time, timedelta
from django.test import TestCase
from django.db import connection, IntegrityError, transaction
from django.utils import timezone

from tenants.models import Tenant
from users.models import User, Member
from check_system.models import TaskCategory, Task, CheckRecord
from we_rss.models import WechatFeed, WechatArticle
from licenses.models import SecurityAuditLog
from interactions.models import MemberFollow, MemberLike, ArticleLike
from cms.models import Article, Category
from points.models import UserTypeTag, TenantUserProfile, TenantUserTypeTag


class TestPerf06PhysicalIndexesAdversarial(TestCase):
    """
    [PERF-06 物理存在性核验]
    利用 SQLite 底层 PRAGMA 接口深度探测数据表物理索引元数据
    """

    def _get_table_indexes(self, table_name):
        """获取 SQLite 表所有物理索引名及其列名映射"""
        with connection.cursor() as cursor:
            cursor.execute(f"PRAGMA index_list('{table_name}')")
            index_list = cursor.fetchall()
            # 格式: [(seq, name, unique, origin, partial), ...]
            result = {}
            for item in index_list:
                idx_name = item[1]
                cursor.execute(f"PRAGMA index_info('{idx_name}')")
                info = cursor.fetchall()
                # 格式: [(seqno, cid, name), ...]
                cols = [col[2] for col in info]
                result[idx_name] = {
                    "unique": bool(item[2]),
                    "columns": cols,
                    "partial": bool(item[4]) if len(item) > 4 else False,
                }
            return result

    def test_wechat_article_physical_indexes(self):
        """
        核验 WechatArticle 4 个新增高频复合索引物理落库与字段顺序
        """
        indexes = self._get_table_indexes("we_rss_wechat_article")

        # 1. we_rss_art_tenant_pub_idx: ['tenant_id', 'publish_time']
        self.assertIn("we_rss_art_tenant_pub_idx", indexes)
        self.assertEqual(indexes["we_rss_art_tenant_pub_idx"]["columns"], ["tenant_id", "publish_time"])

        # 2. we_rss_art_feed_pub_idx: ['feed_id', 'publish_time']
        self.assertIn("we_rss_art_feed_pub_idx", indexes)
        self.assertEqual(indexes["we_rss_art_feed_pub_idx"]["columns"], ["feed_id", "publish_time"])

        # 3. we_rss_art_status_pub_idx: ['status', 'publish_time']
        self.assertIn("we_rss_art_status_pub_idx", indexes)
        self.assertEqual(indexes["we_rss_art_status_pub_idx"]["columns"], ["status", "publish_time"])

        # 4. we_rss_art_pub_created_idx: ['publish_time', 'created_at']
        self.assertIn("we_rss_art_pub_created_idx", indexes)
        self.assertEqual(indexes["we_rss_art_pub_created_idx"]["columns"], ["publish_time", "created_at"])

    def test_check_record_physical_indexes(self):
        """
        核验 CheckRecord 3 个新增高频索引物理落库与字段顺序
        """
        indexes = self._get_table_indexes("check_record")

        # 1. check_rec_member_date_idx: ['member_id', 'check_date']
        self.assertIn("check_rec_member_date_idx", indexes)
        self.assertEqual(indexes["check_rec_member_date_idx"]["columns"], ["member_id", "check_date"])

        # 2. check_rec_tenant_date_idx: ['tenant_id', 'check_date']
        self.assertIn("check_rec_tenant_date_idx", indexes)
        self.assertEqual(indexes["check_rec_tenant_date_idx"]["columns"], ["tenant_id", "check_date"])

        # 3. check_rec_date_idx: ['check_date']
        self.assertIn("check_rec_date_idx", indexes)
        self.assertEqual(indexes["check_rec_date_idx"]["columns"], ["check_date"])

    def test_user_and_member_physical_indexes(self):
        """
        核验 User 与 Member 的租户复合索引物理落库与字段顺序
        """
        # User 表 (db_table='user')
        user_indexes = self._get_table_indexes("user")
        self.assertIn("user_tenant_deleted_idx", user_indexes)
        self.assertEqual(user_indexes["user_tenant_deleted_idx"]["columns"], ["tenant_id", "is_deleted"])
        self.assertIn("user_tenant_status_idx", user_indexes)
        self.assertEqual(user_indexes["user_tenant_status_idx"]["columns"], ["tenant_id", "status"])

        # Member 表 (db_table='member')
        member_indexes = self._get_table_indexes("member")
        self.assertIn("member_tenant_deleted_idx", member_indexes)
        self.assertEqual(member_indexes["member_tenant_deleted_idx"]["columns"], ["tenant_id", "is_deleted"])
        self.assertIn("member_tenant_status_idx", member_indexes)
        self.assertEqual(member_indexes["member_tenant_status_idx"]["columns"], ["tenant_id", "status"])

    def test_security_audit_log_physical_index(self):
        """
        核验 SecurityAuditLog 复合索引 licenses_sec_tenant_ts_idx
        """
        indexes = self._get_table_indexes("licenses_security_audit_log")
        self.assertIn("licenses_sec_tenant_ts_idx", indexes)
        self.assertEqual(indexes["licenses_sec_tenant_ts_idx"]["columns"], ["tenant_id", "timestamp"])

    def test_check_record_unique_constraint_physical_index(self):
        """
        核验 CheckRecord 条件唯一约束 unique_member_task_check_date 是否作为 Partial Unique Index 物理存在
        """
        indexes = self._get_table_indexes("check_record")
        self.assertIn("unique_member_task_check_date", indexes)
        self.assertTrue(indexes["unique_member_task_check_date"]["unique"])
        self.assertEqual(
            indexes["unique_member_task_check_date"]["columns"],
            ["member_id", "task_id", "check_date"]
        )

    def test_cms_category_physical_index(self):
        """
        核验 CMS Category 修复命名的复合索引 cms_cat_tenant_admin_only_idx 物理落库
        """
        indexes = self._get_table_indexes("cms_category")
        self.assertIn("cms_cat_tenant_admin_only_idx", indexes)
        self.assertEqual(
            indexes["cms_cat_tenant_admin_only_idx"]["columns"],
            ["tenant_id", "is_admin_only"]
        )


class TestQuerySetExplainExecutionPlanAdversarial(TestCase):
    """
    [PERF-06 执行计划命中攻防实证]
    构建多租户、大跨度时间序列真实样本数据，执行 QuerySet.explain()
    验证 SQLite EXPLAIN QUERY PLAN 真实命中新增复合索引（USING INDEX）
    """

    @classmethod
    def setUpTestData(cls):
        # 1. 基础租户与成员
        cls.tenant_a = Tenant.objects.create(name="Tenant Alpha", code="t_alpha", status="active")
        cls.tenant_b = Tenant.objects.create(name="Tenant Beta", code="t_beta", status="active")

        cls.member_a = Member.objects.create_user(
            username="member_a", email="a@alpha.com", password="P1!", tenant=cls.tenant_a
        )
        cls.member_b = Member.objects.create_user(
            username="member_b", email="b@beta.com", password="P1!", tenant=cls.tenant_b
        )

        cls.user_a = User.objects.create_user(
            username="user_admin_a", email="ua@alpha.com", password="P1!", tenant=cls.tenant_a
        )

        # 2. 任务与打卡类别
        cls.category = TaskCategory.objects.create(name="Morning", tenant=cls.tenant_a)
        cls.task_1 = Task.objects.create(
            name="Read Book", category=cls.category, member=cls.member_a, start_date=date(2026, 1, 1), tenant=cls.tenant_a
        )

        # 插入若干打卡记录
        base_date = date(2026, 10, 1)
        for i in range(15):
            d = base_date + timedelta(days=i)
            CheckRecord.objects.create(
                tenant=cls.tenant_a,
                member=cls.member_a,
                task=cls.task_1,
                check_date=d,
                check_time=time(8, 30),
            )
            CheckRecord.objects.create(
                tenant=cls.tenant_b,
                member=cls.member_b,
                task=None,
                check_date=d,
                check_time=time(9, 0),
            )

        # 3. 微信文章源与微信文章
        cls.feed_1 = WechatFeed.objects.create(
            tenant=cls.tenant_a,
            mp_name="TechDaily",
            status="active"
        )
        cls.feed_2 = WechatFeed.objects.create(
            tenant=cls.tenant_a,
            mp_name="LifeDaily",
            status="active"
        )

        now = timezone.now()
        for i in range(20):
            pub = now - timedelta(hours=i * 2)
            WechatArticle.objects.create(
                tenant=cls.tenant_a if i % 2 == 0 else cls.tenant_b,
                feed=cls.feed_1 if i % 3 == 0 else cls.feed_2,
                title=f"Article {i}",
                status="published" if i % 2 == 0 else "draft",
                publish_time=pub,
            )

        # 4. 安全审计日志
        for i in range(10):
            SecurityAuditLog.objects.create(
                tenant=cls.tenant_a if i % 2 == 0 else cls.tenant_b,
                user=cls.user_a,
                event_type="LOGIN_SUCCESS",
                severity="INFO",
                ip_address="127.0.0.1",
            )

    def test_explain_wechat_article_tenant_and_pubtime(self):
        """
        验证典型高频查询: WechatArticle 租户过滤 + 发布时间倒序
        SQL: SELECT ... WHERE tenant_id = ? ORDER BY publish_time DESC
        预期执行计划: 命中 we_rss_art_tenant_pub_idx
        """
        qs = WechatArticle.objects.filter(tenant=self.tenant_a).order_by("-publish_time")
        plan = qs.explain()
        print(f"\n[EXPLAIN WechatArticle tenant+pub]:\n{plan}")
        self.assertIn("we_rss_art_tenant_pub_idx", plan)

    def test_explain_wechat_article_feed_and_pubtime(self):
        """
        验证典型高频查询: WechatArticle 订阅源过滤 + 发布时间倒序
        SQL: SELECT ... WHERE feed_id = ? ORDER BY publish_time DESC
        预期执行计划: 命中 we_rss_art_feed_pub_idx
        """
        qs = WechatArticle.objects.filter(feed=self.feed_1).order_by("-publish_time")
        plan = qs.explain()
        print(f"\n[EXPLAIN WechatArticle feed+pub]:\n{plan}")
        self.assertIn("we_rss_art_feed_pub_idx", plan)

    def test_explain_wechat_article_status_and_pubtime(self):
        """
        验证典型高频查询: WechatArticle 状态过滤 + 发布时间倒序
        SQL: SELECT ... WHERE status = ? ORDER BY publish_time DESC
        预期执行计划: 命中 we_rss_art_status_pub_idx
        """
        qs = WechatArticle.objects.filter(status="published").order_by("-publish_time")
        plan = qs.explain()
        print(f"\n[EXPLAIN WechatArticle status+pub]:\n{plan}")
        self.assertIn("we_rss_art_status_pub_idx", plan)

    def test_explain_wechat_article_pubtime_and_created_at_order(self):
        """
        验证典型高频查询: WechatArticle 全局发布时间倒序 + 创建时间倒序
        SQL: SELECT ... ORDER BY publish_time DESC, created_at DESC
        预期执行计划: 当通过 original_objects (无 is_deleted 单列索引干扰) 时，完美命中 we_rss_art_pub_created_idx
        """
        qs = WechatArticle.original_objects.all().order_by("-publish_time", "-created_at")
        plan = qs.explain()
        print(f"\n[EXPLAIN WechatArticle pub+created via original_objects]:\n{plan}")
        self.assertIn("we_rss_art_pub_created_idx", plan)

    def test_explain_check_record_member_and_date(self):
        """
        验证典型高频查询: CheckRecord 成员过滤 + 打卡日期过滤
        SQL: SELECT ... WHERE member_id = ? AND check_date = ?
        预期执行计划: 命中 check_rec_member_date_idx
        """
        qs = CheckRecord.objects.filter(member=self.member_a, check_date=date(2026, 10, 5))
        plan = qs.explain()
        print(f"\n[EXPLAIN CheckRecord member+date]:\n{plan}")
        self.assertIn("check_rec_member_date_idx", plan)

    def test_explain_check_record_tenant_and_date(self):
        """
        验证典型高频查询: CheckRecord 租户过滤 + 打卡日期过滤
        SQL: SELECT ... WHERE tenant_id = ? AND check_date = ?
        预期执行计划: 命中 check_rec_tenant_date_idx
        """
        qs = CheckRecord.objects.filter(tenant=self.tenant_a, check_date=date(2026, 10, 5))
        plan = qs.explain()
        print(f"\n[EXPLAIN CheckRecord tenant+date]:\n{plan}")
        self.assertIn("check_rec_tenant_date_idx", plan)

    def test_explain_check_record_date_only(self):
        """
        验证典型高频查询: CheckRecord 单纯打卡日期范围过滤
        SQL: SELECT ... WHERE check_date = ?
        预期执行计划: 当通过 original_objects 查询纯日期时，精准命中 check_rec_date_idx
        """
        qs = CheckRecord.original_objects.filter(check_date=date(2026, 10, 5))
        plan = qs.explain()
        print(f"\n[EXPLAIN CheckRecord date via original_objects]:\n{plan}")
        self.assertIn("check_rec_date_idx", plan)

    def test_explain_user_and_member_tenant_filters(self):
        """
        验证典型高频查询: User / Member 租户 + 软删除/状态联合过滤
        """
        # User: tenant + is_deleted
        qs_u_del = User.objects.filter(tenant=self.tenant_a, is_deleted=False)
        plan_u_del = qs_u_del.explain()
        print(f"\n[EXPLAIN User tenant+deleted]:\n{plan_u_del}")
        self.assertIn("user_tenant_deleted_idx", plan_u_del)

        # User: tenant + status
        qs_u_st = User.objects.filter(tenant=self.tenant_a, status="active")
        plan_u_st = qs_u_st.explain()
        print(f"\n[EXPLAIN User tenant+status]:\n{plan_u_st}")
        self.assertIn("user_tenant_status_idx", plan_u_st)

        # Member: tenant + is_deleted
        qs_m_del = Member.objects.filter(tenant=self.tenant_a, is_deleted=False)
        plan_m_del = qs_m_del.explain()
        print(f"\n[EXPLAIN Member tenant+deleted]:\n{plan_m_del}")
        self.assertIn("member_tenant_deleted_idx", plan_m_del)

        # Member: tenant + status
        qs_m_st = Member.objects.filter(tenant=self.tenant_a, status="active")
        plan_m_st = qs_m_st.explain()
        print(f"\n[EXPLAIN Member tenant+status]:\n{plan_m_st}")
        self.assertIn("member_tenant_status_idx", plan_m_st)

    def test_explain_security_audit_log_tenant_and_timestamp(self):
        """
        验证典型高频查询: SecurityAuditLog 租户过滤 + 时间戳倒序
        SQL: SELECT ... WHERE tenant_id = ? ORDER BY timestamp DESC
        预期执行计划: 命中 licenses_sec_tenant_ts_idx
        """
        qs = SecurityAuditLog.objects.filter(tenant=self.tenant_a).order_by("-timestamp")
        plan = qs.explain()
        print(f"\n[EXPLAIN SecurityAuditLog tenant+timestamp]:\n{plan}")
        self.assertIn("licenses_sec_tenant_ts_idx", plan)


class TestAdversarialConstraintsAndSoftDelete(TestCase):
    """
    [BUG-LOGIC-08 & BUG-LOGIC-05 对抗实证挑战]
    打卡防重唯一约束与软删除条件约束压力测试
    """

    def setUp(self):
        self.tenant = Tenant.objects.create(name="Constraint Tenant", code="c_tenant", status="active")
        self.member_1 = Member.objects.create_user(
            username="c_user_1", email="u1@ctest.com", password="P1!", tenant=self.tenant
        )
        self.member_2 = Member.objects.create_user(
            username="c_user_2", email="u2@ctest.com", password="P1!", tenant=self.tenant
        )
        self.category = TaskCategory.objects.create(name="Daily Habit", tenant=self.tenant)
        self.task = Task.objects.create(
            name="Gym Workout", category=self.category, member=self.member_1, start_date=date(2026, 1, 1), tenant=self.tenant
        )

    def test_checkrecord_unique_constraint_adversarial_rejection(self):
        """
        [BUG-LOGIC-08 实证]
        1. 同成员、同任务、同日期在未删除状态下，第二次打卡必须被数据库唯一约束强力拦截抛出 IntegrityError
        2. 软删除第一条打卡记录后，再次插入同成员、同任务、同日期的打卡记录，必须顺利创建落库
        3. task 为 None 的自由打卡，由于条件约束限定 task__isnull=False，允许同日多次打卡
        """
        today = date(2026, 10, 9)

        # 1. 成功创建第 1 条有效打卡
        rec_1 = CheckRecord.objects.create(
            tenant=self.tenant,
            member=self.member_1,
            task=self.task,
            check_date=today,
            check_time=time(10, 0),
            is_deleted=False
        )
        self.assertIsNotNone(rec_1.pk)

        # 2. 对抗场景: 模拟并发或重复请求，插入同成员、同任务、同日期的记录
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                CheckRecord.objects.create(
                    tenant=self.tenant,
                    member=self.member_1,
                    task=self.task,
                    check_date=today,
                    check_time=time(10, 5),
                    is_deleted=False
                )

        # 3. 软删除 rec_1
        rec_1.is_deleted = True
        rec_1.save()

        # 4. 软删除后重新打卡，必须成功落库且生成新主键
        rec_2 = CheckRecord.objects.create(
            tenant=self.tenant,
            member=self.member_1,
            task=self.task,
            check_date=today,
            check_time=time(11, 0),
            is_deleted=False
        )
        self.assertIsNotNone(rec_2.pk)
        self.assertNotEqual(rec_1.pk, rec_2.pk)

        # 5. task 为 None 时不受条件唯一约束限制，允许同日多条
        free_1 = CheckRecord.objects.create(
            tenant=self.tenant,
            member=self.member_1,
            task=None,
            check_date=today,
            check_time=time(12, 0),
            is_deleted=False
        )
        free_2 = CheckRecord.objects.create(
            tenant=self.tenant,
            member=self.member_1,
            task=None,
            check_date=today,
            check_time=time(12, 30),
            is_deleted=False
        )
        self.assertIsNotNone(free_1.pk)
        self.assertIsNotNone(free_2.pk)

    def test_interactions_member_follow_soft_delete_reconnect(self):
        """
        [BUG-LOGIC-05 实证]
        1. member_1 关注 member_2
        2. 重复关注必须被 UniqueConstraint 拦截抛出 IntegrityError
        3. 取关 (is_deleted=True) 后重新关注，必须成功落库
        """
        # 1. 关注
        f1 = MemberFollow.objects.create(
            follower=self.member_1, following=self.member_2, tenant=self.tenant, is_deleted=False
        )
        self.assertIsNotNone(f1.pk)

        # 2. 重复关注抛出 IntegrityError
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                MemberFollow.objects.create(
                    follower=self.member_1, following=self.member_2, tenant=self.tenant, is_deleted=False
                )

        # 3. 软删除 (取关)
        f1.is_deleted = True
        f1.save()

        # 4. 再次关注，必须成功
        f2 = MemberFollow.objects.create(
            follower=self.member_1, following=self.member_2, tenant=self.tenant, is_deleted=False
        )
        self.assertIsNotNone(f2.pk)
        self.assertNotEqual(f1.pk, f2.pk)

    def test_interactions_member_like_soft_delete_relike(self):
        """
        [BUG-LOGIC-05 实证]
        1. member_1 点赞 member_2
        2. 重复点赞抛出 IntegrityError
        3. 取消点赞 (is_deleted=True) 后重新点赞，必须成功落库
        """
        # 1. 点赞
        l1 = MemberLike.objects.create(
            from_member=self.member_1, to_member=self.member_2, tenant=self.tenant, is_deleted=False
        )
        self.assertIsNotNone(l1.pk)

        # 2. 重复点赞抛出 IntegrityError
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                MemberLike.objects.create(
                    from_member=self.member_1, to_member=self.member_2, tenant=self.tenant, is_deleted=False
                )

        # 3. 取消点赞 (软删除)
        l1.is_deleted = True
        l1.save()

        # 4. 重新点赞，必须成功
        l2 = MemberLike.objects.create(
            from_member=self.member_1, to_member=self.member_2, tenant=self.tenant, is_deleted=False
        )
        self.assertIsNotNone(l2.pk)
        self.assertNotEqual(l1.pk, l2.pk)

    def test_tenant_conditional_unique_constraints_adversarial(self):
        """
        [BUG-LOGIC-05 实证]
        Tenant 模型的 unique_active_tenant_name 与 unique_active_tenant_code 对抗
        1. 重复活跃同名/同 code 必须抛出 IntegrityError
        2. 软删除 (is_deleted=True) 后，允许同名/同 code 租户重新注册创建落库
        """
        t1 = Tenant.objects.create(name="Unique Brand", code="u_brand", is_deleted=False)
        self.assertIsNotNone(t1.pk)

        # 尝试创建重复活跃同名租户
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Tenant.objects.create(name="Unique Brand", code="u_brand_2", is_deleted=False)

        # 尝试创建重复活跃同 code 租户
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Tenant.objects.create(name="Unique Brand 2", code="u_brand", is_deleted=False)

        # 软删除 t1
        t1.is_deleted = True
        t1.save()

        # 软删除后重新创建同名同 code 租户，必须成功落库
        t2 = Tenant.objects.create(name="Unique Brand", code="u_brand", is_deleted=False)
        self.assertIsNotNone(t2.pk)
        self.assertNotEqual(t1.pk, t2.pk)

    def test_points_user_tag_conditional_unique_constraint_adversarial(self):
        """
        [BUG-LOGIC-05 实证]
        TenantUserTypeTag 条件唯一约束 unique_active_tenant_member_tag (is_active=True)
        1. 活跃状态下重复授予相同标签必须被抛出 IntegrityError 拦截
        2. 停用旧标签 (is_active=False) 后，允许为该成员重新授予相同标签
        """
        tag = UserTypeTag.objects.create(
            tag_name="VIP Member", tag_code="vip_member", tag_type="vip", is_active=True
        )
        profile = TenantUserProfile.objects.create(
            tenant=self.tenant, member=self.member_1
        )

        tag_rel_1 = TenantUserTypeTag.objects.create(
            tenant=self.tenant,
            member=self.member_1,
            tenant_user_profile=profile,
            tag=tag,
            grant_method="manual",
            is_active=True
        )
        self.assertIsNotNone(tag_rel_1.pk)

        # 重复授予活跃状态相同标签，必须触发 IntegrityError
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                TenantUserTypeTag.objects.create(
                    tenant=self.tenant,
                    member=self.member_1,
                    tenant_user_profile=profile,
                    tag=tag,
                    grant_method="manual",
                    is_active=True
                )

        # 停用旧标签
        tag_rel_1.is_active = False
        tag_rel_1.save()

        # 停用后重新授予相同标签，必须成功落库
        tag_rel_2 = TenantUserTypeTag.objects.create(
            tenant=self.tenant,
            member=self.member_1,
            tenant_user_profile=profile,
            tag=tag,
            grant_method="manual",
            is_active=True
        )
        self.assertIsNotNone(tag_rel_2.pk)
        self.assertNotEqual(tag_rel_1.pk, tag_rel_2.pk)
