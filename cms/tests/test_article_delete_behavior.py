import os
import pytest
from django.conf import settings
from rest_framework.test import APIClient
from rest_framework import status
from tenants.models import Tenant
from users.models import User
from cms.models import Article
from cms.utils.media_cleanup import cleanup_article_media_files


@pytest.mark.django_db(transaction=True)
class TestArticleDeleteBehavior:
    @pytest.fixture(autouse=True)
    def setup_method(self, db):
        self.tenant = Tenant.objects.create(
            name="Test Tenant",
            code="test_tenant_del"
        )
        self.admin = User.objects.create_user(
            username="test_admin_del",
            email="admin_del@example.com",
            password="password123",
            tenant=self.tenant,
            is_admin=True,
            is_active=True
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)
        self.client.defaults['HTTP_X_TENANT_ID'] = str(self.tenant.id)

    def test_normal_article_delete_archives(self):
        """测试正常已发布文章删除时转为归档状态（软删除）"""
        article = Article.objects.create(
            tenant=self.tenant,
            user=self.admin,
            title="Normal Article",
            slug="normal-article-1",
            content="Normal content",
            status="published"
        )

        response = self.client.delete(f"/api/v1/cms/articles/{article.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["data"]["action"] == "archive"

        article.refresh_from_db()
        assert article.status == "archived"
        assert Article.objects.filter(id=article.id).exists()

    def test_archived_article_delete_permanently_removes_data_and_files(self):
        """测试已归档文章再点击删除时，物理彻底删除数据及关联图片资源"""
        # 在 MEDIA_ROOT 下创建测试图片文件
        test_dir = os.path.join(settings.MEDIA_ROOT, "uploads", "test_del")
        os.makedirs(test_dir, exist_ok=True)

        cover_file = os.path.join(test_dir, "cover_sample.jpg")
        with open(cover_file, "w") as f:
            f.write("fake cover image bytes")

        content_file = os.path.join(test_dir, "content_sample.png")
        with open(content_file, "w") as f:
            f.write("fake content image bytes")

        assert os.path.isfile(cover_file)
        assert os.path.isfile(content_file)

        article = Article.objects.create(
            tenant=self.tenant,
            user=self.admin,
            title="Archived Article To Purge",
            slug="archived-article-purge",
            content=f"Article with image: ![sample](/media/uploads/test_del/content_sample.png)",
            cover_image="media/uploads/test_del/cover_sample.jpg",
            status="archived"
        )

        response = self.client.delete(f"/api/v1/cms/articles/{article.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["data"]["action"] == "permanent_delete"

        # 验证数据库记录彻底删除
        assert not Article.objects.filter(id=article.id).exists()

        # 验证物理图片资源已被安全清理
        assert not os.path.isfile(cover_file)
        assert not os.path.isfile(content_file)

    def test_batch_delete_handles_archived_and_active_articles(self):
        """测试批量删除时，已归档文章彻底物理删除，未归档文章转为归档"""
        # 文章 1：普通文章
        a1 = Article.objects.create(
            tenant=self.tenant,
            user=self.admin,
            title="Batch Active Article",
            slug="batch-active-1",
            content="Active content",
            status="published"
        )
        # 文章 2：已归档文章
        a2 = Article.objects.create(
            tenant=self.tenant,
            user=self.admin,
            title="Batch Archived Article",
            slug="batch-archived-2",
            content="Archived content",
            status="archived"
        )

        response = self.client.post(
            "/api/v1/cms/articles/batch-delete/",
            {"article_ids": [a1.id, a2.id], "force": False},
            format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        data = response.data["data"]
        assert data["archived_count"] == 1
        assert data["permanently_deleted_count"] == 1

        # a1 应该变为 archived
        a1.refresh_from_db()
        assert a1.status == "archived"

        # a2 应该在数据库中彻底物理删除
        assert not Article.objects.filter(id=a2.id).exists()

    def test_app_admin_delete_multi_app_article_only_unlinks(self):
        """测试多应用共享文章时，应用管理员删除只解除当前应用绑定，不破坏其他应用"""
        from applications.models import Application, UserApplication
        from cms.models import ArticleApplication

        app1 = Application.objects.create(tenant=self.tenant, name="App 1", code="app1")
        app2 = Application.objects.create(tenant=self.tenant, name="App 2", code="app2")

        # 创建应用管理员，只管辖 app1
        app_admin = User.objects.create_user(
            username="app_admin_multi",
            email="app_admin_multi@example.com",
            password="password123",
            tenant=self.tenant,
            is_admin=True,
            admin_type="app_admin",
            is_active=True
        )
        UserApplication.objects.create(user=app_admin, application=app1, role="admin", tenant=self.tenant)

        # 创建一篇文章，同时关联 app1 和 app2
        shared_article = Article.objects.create(
            tenant=self.tenant,
            user=self.admin,
            title="Shared Article Across Apps",
            slug="shared-article-apps",
            content="Shared Content",
            status="archived"
        )
        ArticleApplication.objects.create(article=shared_article, application=app1, tenant=self.tenant)
        ArticleApplication.objects.create(article=shared_article, application=app2, tenant=self.tenant)

        # 使用 app_admin 身份进行删除
        client = APIClient()
        client.force_authenticate(user=app_admin)
        client.defaults['HTTP_X_TENANT_ID'] = str(self.tenant.id)

        response = client.delete(f"/api/v1/cms/articles/{shared_article.id}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert response.data["data"]["action"] == "unlinked"

        # 验证文章本身并未被全局物理删除
        assert Article.objects.filter(id=shared_article.id).exists()

        # 验证与 app1 的关联已解除，但与 app2 的关联完好保留
        assert not ArticleApplication.objects.filter(article=shared_article, application=app1).exists()
        assert ArticleApplication.objects.filter(article=shared_article, application=app2).exists()
