"""
Applications 模型单元测试与 API 视图集成测试
覆盖：
1. Application 模型默认值、(tenant, code) 租户内唯一与跨租户允许同 code；
2. 关联统计方法 (get_license_count, get_active_license_count, get_feedback_count, get_open_feedback_count, get_article_count)；
3. ApplicationViewSet 读写权限分级 (Member 只读 200 / 写操作 403，租户管理员可写)；
4. 跨租户数据物理隔离、statistics 统计动作与 articles 关联文章动作。
"""
from datetime import timedelta
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from applications.models import Application
from cms.models import Article, ArticleApplication
from common.authentication.jwt_auth import generate_jwt_token
from feedbacks.models import Feedback
from licenses.models import License, LicensePlan
from tenants.models import Tenant
from users.models import Member, User


class ApplicationModelTests(TestCase):
    """Application 模型与关联统计方法单元测试"""

    def setUp(self):
        self.tenant_a = Tenant.objects.create(name="App Tenant A", code="app_tenant_a")
        self.tenant_b = Tenant.objects.create(name="App Tenant B", code="app_tenant_b")
        self.admin_a = User.objects.create(
            username="app_admin_a",
            email="admin@appa.com",
            tenant=self.tenant_a,
            is_admin=True,
        )

    def test_application_default_fields(self):
        """验证创建 Application 时的默认字段值与 __str__ 方法"""
        app = Application.objects.create(
            tenant=self.tenant_a,
            name="LiPeaks Studio",
            code="lipeaks_studio",
        )
        self.assertEqual(app.current_version, "1.0.0")
        self.assertEqual(app.status, "active")
        self.assertTrue(app.is_active)
        self.assertEqual(app.tags, [])
        self.assertEqual(app.metadata, {})
        self.assertEqual(str(app), "LiPeaks Studio (lipeaks_studio)")

    def test_application_unique_together_tenant_and_code(self):
        """验证同一租户下相同 code 触发 IntegrityError，不同租户下允许相同 code"""
        Application.objects.create(
            tenant=self.tenant_a,
            name="CRM Pro A",
            code="crm_pro",
        )

        # 同一租户内重复 code 触发数据库唯一约束异常
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Application.objects.create(
                    tenant=self.tenant_a,
                    name="CRM Pro A Duplicate",
                    code="crm_pro",
                )

        # 不同租户下允许使用相同 code
        app_b = Application.objects.create(
            tenant=self.tenant_b,
            name="CRM Pro B",
            code="crm_pro",
        )
        self.assertIsNotNone(app_b.pk)
        self.assertEqual(app_b.code, "crm_pro")

    def test_application_related_statistics_methods(self):
        """验证 get_license_count / get_active_license_count / get_feedback_count / get_open_feedback_count / get_article_count"""
        app = Application.objects.create(
            tenant=self.tenant_a,
            name="Stats App",
            code="stats_app",
        )

        # 初始空关联时全部返回 0
        self.assertEqual(app.get_license_count(), 0)
        self.assertEqual(app.get_active_license_count(), 0)
        self.assertEqual(app.get_feedback_count(), 0)
        self.assertEqual(app.get_open_feedback_count(), 0)
        self.assertEqual(app.get_article_count(), 0)

        # 1. 创建 2 个许可证（1 个 activated，1 个 generated）
        plan = LicensePlan.objects.create(
            tenant=self.tenant_a,
            application=app,
            name="Pro Plan",
            code="pro_plan",
            plan_type="professional",
        )
        License.objects.create(
            tenant=self.tenant_a,
            application=app,
            plan=plan,
            license_key="KEY-ACT-0001",
            status="activated",
            expires_at=timezone.now() + timedelta(days=30),
        )
        License.objects.create(
            tenant=self.tenant_a,
            application=app,
            plan=plan,
            license_key="KEY-GEN-0002",
            status="generated",
            expires_at=timezone.now() + timedelta(days=30),
        )
        self.assertEqual(app.get_license_count(), 2)
        self.assertEqual(app.get_active_license_count(), 1)

        # 2. 创建 2 条反馈（1 条 submitted 未关闭，1 条 closed 已关闭）
        Feedback.objects.create(
            tenant=self.tenant_a,
            application=app,
            title="Bug 1",
            description="Open bug",
            status="submitted",
        )
        Feedback.objects.create(
            tenant=self.tenant_a,
            application=app,
            title="Bug 2",
            description="Closed bug",
            status="closed",
        )
        self.assertEqual(app.get_feedback_count(), 2)
        self.assertEqual(app.get_open_feedback_count(), 1)

        # 3. 创建 1 篇关联文章
        article = Article.objects.create(
            tenant=self.tenant_a,
            title="Release Notes v1.0",
            slug="release-notes-v1-0",
            content="Welcome to v1.0",
            user=self.admin_a,
            status="published",
        )
        ArticleApplication.objects.create(
            tenant=self.tenant_a,
            article=article,
            application=app,
        )
        self.assertEqual(app.get_article_count(), 1)


class ApplicationViewSetTests(APITestCase):
    """ApplicationViewSet 读写权限、跨租户隔离与自定义动作集成测试"""

    def setUp(self):
        self.tenant_a = Tenant.objects.create(name="View Tenant A", code="view_tenant_a")
        self.tenant_b = Tenant.objects.create(name="View Tenant B", code="view_tenant_b")

        self.admin_a = User.objects.create(
            username="view_admin_a",
            email="admin@viewa.com",
            tenant=self.tenant_a,
            is_admin=True,
        )
        self.regular_user_a = User.objects.create(
            username="view_regular_a",
            email="regular@viewa.com",
            tenant=self.tenant_a,
            is_admin=False,
        )
        self.member_a = Member.objects.create(
            username="view_member_a",
            email="member@viewa.com",
            tenant=self.tenant_a,
        )
        self.admin_b = User.objects.create(
            username="view_admin_b",
            email="admin@viewb.com",
            tenant=self.tenant_b,
            is_admin=True,
        )

        self.app_a = Application.objects.create(
            tenant=self.tenant_a,
            name="Alpha App",
            code="alpha_app",
            description="Alpha application description",
            status="active",
            is_active=True,
        )
        self.app_b = Application.objects.create(
            tenant=self.tenant_b,
            name="Beta App",
            code="beta_app",
            description="Beta application description",
            status="active",
            is_active=True,
        )

    def _auth_admin(self, admin_user=None):
        user = admin_user or self.admin_a
        token = generate_jwt_token(user)["access_token"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    def _auth_member(self, member_user=None):
        user = member_user or self.member_a
        token = generate_jwt_token(user)["access_token"]
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {token}",
            HTTP_X_TENANT_ID=str(user.tenant_id),
        )

    def test_member_read_allowed_and_write_forbidden(self):
        """验证普通 Member / 非管理员用户可读列表与详情 (200)，但 POST/PATCH/DELETE 写操作被拦截 (403)"""
        # 1. Member 用户只读访问列表与详情返回 200
        self._auth_member(self.member_a)
        res_list = self.client.get("/api/v1/applications/")
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)

        res_detail = self.client.get(f"/api/v1/applications/{self.app_a.id}/")
        self.assertEqual(res_detail.status_code, status.HTTP_200_OK)

        # 2. 非管理员用户尝试发起写操作 (POST/PATCH/DELETE) 均被 IsTenantAdmin 拦截返回 403
        self._auth_member(self.regular_user_a)
        res_post = self.client.post(
            "/api/v1/applications/",
            {"name": "Illegal App", "code": "illegal_app"},
            format="json",
        )
        self.assertEqual(res_post.status_code, status.HTTP_403_FORBIDDEN)

        res_patch = self.client.patch(
            f"/api/v1/applications/{self.app_a.id}/",
            {"name": "Hacked App"},
            format="json",
        )
        self.assertEqual(res_patch.status_code, status.HTTP_403_FORBIDDEN)

        res_del = self.client.delete(f"/api/v1/applications/{self.app_a.id}/")
        self.assertEqual(res_del.status_code, status.HTTP_403_FORBIDDEN)

    def test_tenant_admin_crud_full_lifecycle(self):
        """验证租户管理员创建、更新与软删除应用"""
        self._auth_admin(self.admin_a)

        # 1. 创建新应用
        res_create = self.client.post(
            "/api/v1/applications/",
            {
                "name": "Alpha New App",
                "code": "alpha_new",
                "description": "Created by tenant admin",
                "current_version": "2.0.0",
                "status": "development",
            },
            format="json",
        )
        self.assertEqual(res_create.status_code, status.HTTP_201_CREATED)
        created_app = Application.objects.get(tenant=self.tenant_a, code="alpha_new")
        self.assertEqual(created_app.current_version, "2.0.0")

        # 2. 更新应用
        res_patch = self.client.patch(
            f"/api/v1/applications/{created_app.id}/",
            {"status": "active", "current_version": "2.1.0"},
            format="json",
        )
        self.assertEqual(res_patch.status_code, status.HTTP_200_OK)
        created_app.refresh_from_db()
        self.assertEqual(created_app.status, "active")
        self.assertEqual(created_app.current_version, "2.1.0")

        # 3. 软删除应用
        res_del = self.client.delete(f"/api/v1/applications/{created_app.id}/")
        self.assertEqual(res_del.status_code, status.HTTP_204_NO_CONTENT)
        created_app.refresh_from_db()
        self.assertTrue(created_app.is_deleted)

    def test_cross_tenant_data_isolation_and_search_filter(self):
        """验证跨租户数据严格隔离（无法看到或操作其他租户的应用）及搜索过滤"""
        self._auth_admin(self.admin_a)

        # 列表仅返回租户 A 的应用
        res_list = self.client.get("/api/v1/applications/?search=Alpha&status=active")
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        list_data = res_list.data.get("data", res_list.data)
        results = list_data.get("results", list_data)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["code"], "alpha_app")

        # 尝试访问租户 B 的应用详情、统计或删除均返回 404
        self.assertEqual(
            self.client.get(f"/api/v1/applications/{self.app_b.id}/").status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            self.client.get(f"/api/v1/applications/{self.app_b.id}/statistics/").status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            self.client.delete(f"/api/v1/applications/{self.app_b.id}/").status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_application_statistics_and_articles_actions(self):
        """验证 /applications/{id}/statistics/ 与 /applications/{id}/articles/ 动作返回准确数据且遵守租户隔离"""
        # 为 app_a 创建关联文章与反馈
        article_a = Article.objects.create(
            tenant=self.tenant_a,
            title="Alpha Guide",
            slug="alpha-guide",
            content="Guide content",
            user=self.admin_a,
            status="published",
        )
        ArticleApplication.objects.create(
            tenant=self.tenant_a,
            article=article_a,
            application=self.app_a,
        )
        # 在租户 B 创建一篇异常跨租户绑定的文章，验证 TenantManager 与 articles 动作均严格排除跨租户文章
        article_b = Article.objects.create(
            tenant=self.tenant_b,
            title="Beta Secret Guide",
            slug="beta-secret-guide",
            content="Secret content",
            user=self.admin_b,
            status="published",
        )
        ArticleApplication.objects.create(
            tenant=self.tenant_b,
            article=article_b,
            application=self.app_a,
        )

        Feedback.objects.create(
            tenant=self.tenant_a,
            application=self.app_a,
            title="UI Issue",
            description="Button misaligned",
            status="reviewing",
        )

        self._auth_member(self.member_a)

        # 1. 验证 statistics 动作
        res_stats = self.client.get(f"/api/v1/applications/{self.app_a.id}/statistics/")
        self.assertEqual(res_stats.status_code, status.HTTP_200_OK)
        stats_data = res_stats.data.get("data", res_stats.data)
        self.assertEqual(stats_data["licenses"]["total"], 0)
        self.assertEqual(stats_data["licenses"]["active"], 0)
        self.assertEqual(stats_data["feedbacks"]["total"], 1)
        self.assertEqual(stats_data["feedbacks"]["open"], 1)
        self.assertEqual(stats_data["articles"]["total"], 1)

        # 2. 验证 articles 动作仅返回属于本租户 (tenant_a) 的关联文章
        res_articles = self.client.get(f"/api/v1/applications/{self.app_a.id}/articles/")
        self.assertEqual(res_articles.status_code, status.HTTP_200_OK)
        articles_data = res_articles.data.get("data", res_articles.data)
        self.assertEqual(len(articles_data), 1)
        self.assertEqual(articles_data[0]["title"], "Alpha Guide")
