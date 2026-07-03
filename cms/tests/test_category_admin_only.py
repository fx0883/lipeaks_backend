"""
分类级管理员专属文章控制功能测试

覆盖需求文档 docs/cms/category_admin_only_requirement.md 中的 13 个场景 (T-1 ~ T-13)。
使用 pytest-django + DRF APIClient，通过 X-Tenant-ID header 模拟多租户请求。

测试矩阵:
  T-1  管理员创建标记 is_admin_only=True 的分类              → 201
  T-2  Member 尝试创建 is_admin_only=True 的分类              → 403
  T-3  Member 在管理员专属分类下创建文章                       → 400 (含"管理员专属")
  T-4  Member 在开放分类下创建文章                             → 201
  T-5  Member 创建文章时关联混合分类(1专属+2开放)              → 400 (含"管理员专属")
  T-6  Member 编辑关联管理员专属分类的自己文章                 → 403
  T-7  Member 删除关联管理员专属分类的自己文章                 → 403
  T-8  Member 发布关联管理员专属分类的草稿                     → 403
  T-9  管理员编辑管理员专属分类下的文章                        → 200
  T-10 游客 GET 管理员专属分类下的公开文章                     → 200
  T-11 管理员取消 is_admin_only 标记后 Member 恢复操作权限     → 成功
  T-12 文章未关联任何分类 Member 正常操作                     → 成功
  T-13 子分类父级是管理员专属但子分类未标记 Member 创建        → 201 (不继承)
"""
import json

import pytest
from rest_framework.test import APIClient

from common.authentication.jwt_auth import generate_jwt_token
from tenants.models import Tenant
from users.models import User, Member
from applications.models import Application
from cms.models import Category, Article, ArticleCategory


# ─── API endpoints ────────────────────────────────────────────────────────────

CAT_URL = "/api/v1/cms/categories/"
MEMBER_ART_URL = "/api/v1/cms/member/articles/"
ADMIN_ART_URL = "/api/v1/cms/articles/"


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def tenant(db):
    """创建测试租户"""
    return Tenant.objects.create(name="测试租户", code="tt01", status="active")


@pytest.fixture
def admin_user(tenant):
    """创建租户管理员(非超级管理员)"""
    user = User.objects.create(
        username="admin01",
        email="admin01@test.com",
        is_admin=True,
        is_super_admin=False,
        is_active=True,
        is_deleted=False,
        tenant=tenant,
    )
    user.set_password("AdminPass123!")
    user.save()
    return user


@pytest.fixture
def member_user(tenant):
    """创建普通 Member 用户"""
    member = Member.objects.create(
        username="member01",
        email="member01@test.com",
        is_active=True,
        is_deleted=False,
        tenant=tenant,
    )
    member.set_password("MemberPass123!")
    member.save()
    return member


@pytest.fixture
def application(tenant):
    """创建测试应用(文章创建时必须关联)"""
    return Application.objects.create(
        name="测试应用",
        code="test_app_01",
        tenant=tenant,
    )


# ─── Helper functions ─────────────────────────────────────────────────────────

def _auth_client(user, tenant):
    """创建已认证的 APIClient(JWT + X-Tenant-ID header)

    用于 Member / 游客 — 这类用户必须携带 X-Tenant-ID header。
    """
    client = APIClient()
    token = generate_jwt_token(user)["access_token"]
    client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {token}",
        HTTP_X_TENANT_ID=str(tenant.id),
    )
    return client


def _admin_client(user):
    """创建管理员 APIClient(JWT only，不携带 X-Tenant-ID)

    TenantModelViewSet 规则：租户管理员/超管禁止携带 X-Tenant-ID header，
    否则触发 TenantHeaderInvalidOrMissing。管理员租户由 user.tenant 自动推断。
    """
    client = APIClient()
    token = generate_jwt_token(user)["access_token"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
    return client


def _guest_client(tenant):
    """创建未认证的 APIClient(仅 X-Tenant-ID header)"""
    client = APIClient()
    client.credentials(HTTP_X_TENANT_ID=str(tenant.id))
    return client


_slug_seq = [0]


def _unique_slug(prefix="slug"):
    """生成唯一 slug(Category.slug 字段有 unique=True 约束)"""
    _slug_seq[0] += 1
    return f"{prefix}-{_slug_seq[0]}"


def _make_category(tenant, name="测试分类", is_admin_only=False, parent=None):
    """直接在数据库中创建 Category(绕过 API，用于测试前置数据准备)"""
    cat = Category(
        slug=_unique_slug("cat"),
        tenant=tenant,
        is_admin_only=is_admin_only,
        parent=parent,
    )
    cat.set_current_language("zh-hans")
    cat.name = name
    cat.save()
    return cat


def _make_article(tenant, *, member=None, user=None,
                  status="draft", visibility="public", title="测试文章"):
    """直接在数据库中创建 Article"""
    return Article.objects.create(
        title=title,
        content="测试内容正文",
        tenant=tenant,
        member=member,
        user=user,
        status=status,
        visibility=visibility,
    )


def _link_article_category(article, category, tenant):
    """创建文章-分类关联(ArticleCategory)"""
    return ArticleCategory.objects.create(
        article=article,
        category=category,
        tenant=tenant,
    )


def _response_text(resp):
    """将 response.data 序列化为文本，便于关键字断言"""
    try:
        return json.dumps(resp.data, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(resp.data)


def _resp_data(resp):
    """提取 response 中的业务数据，兼容 StandardJSONRenderer 包装格式。

    StandardJSONRenderer 将响应包装为 {"success":..., "code":..., "message":..., "data":{...}}。
    本函数返回内层 data 字典；若响应未包装则直接返回 resp.data。
    """
    data = resp.data
    if isinstance(data, dict) and "success" in data and "data" in data:
        inner = data["data"]
        return inner if isinstance(inner, dict) else {}
    if isinstance(data, dict):
        return data
    return {}


# ─── T-1: 管理员创建标记 is_admin_only=True 的分类 → 成功 201 ─────────────────

@pytest.mark.django_db
def test_T01_admin_creates_admin_only_category(tenant, admin_user):
    """管理员可以创建 is_admin_only=True 的分类，返回 201"""
    client = _admin_client(admin_user)
    resp = client.post(
        CAT_URL,
        {
            "translations": {"zh-hans": {"name": "管理员专属"}},
            "is_admin_only": True,
        },
        format="json",
    )
    assert resp.status_code == 201
    # 兼容 StandardJSONRenderer 包装格式
    payload = _resp_data(resp)
    assert payload.get("is_admin_only") is True


# ─── T-2: Member 尝试创建 is_admin_only=True 的分类 → 403 ──────────────────────

@pytest.mark.django_db
def test_T02_member_creates_admin_only_category_forbidden(tenant, member_user):
    """Member 不应创建 is_admin_only=True 的分类，返回 403"""
    client = _auth_client(member_user, tenant)
    resp = client.post(
        CAT_URL,
        {
            "translations": {"zh-hans": {"name": "管理员专属"}},
            "is_admin_only": True,
        },
        format="json",
    )
    assert resp.status_code == 403


# ─── T-3: Member 在管理员专属分类下创建文章 → 400 含"管理员专属" ────────────────

@pytest.mark.django_db
def test_T03_member_create_article_in_admin_only_category(
    tenant, member_user, application
):
    """Member 在管理员专属分类下创建文章应返回 400 且错误消息含"管理员专属" """
    admin_cat = _make_category(tenant, name="管理员专属", is_admin_only=True)
    client = _auth_client(member_user, tenant)
    resp = client.post(
        MEMBER_ART_URL,
        {
            "title": "专属分类文章",
            "content": "内容",
            "application": application.id,
            "category_ids": [admin_cat.id],
        },
        format="json",
    )
    assert resp.status_code == 400
    assert "管理员专属" in _response_text(resp)


# ─── T-4: Member 在开放分类下创建文章 → 成功 201 ──────────────────────────────

@pytest.mark.django_db
def test_T04_member_create_article_in_open_category(
    tenant, member_user, application
):
    """Member 在开放分类(is_admin_only=False)下创建文章应返回 201"""
    open_cat = _make_category(tenant, name="开放分类", is_admin_only=False)
    client = _auth_client(member_user, tenant)
    resp = client.post(
        MEMBER_ART_URL,
        {
            "title": "开放分类文章",
            "content": "内容",
            "application": application.id,
            "category_ids": [open_cat.id],
        },
        format="json",
    )
    assert resp.status_code == 201


# ─── T-5: Member 创建文章时关联混合分类(1专属+2开放) → 400 含"管理员专属" ──────

@pytest.mark.django_db
def test_T05_member_create_article_with_mixed_categories(
    tenant, member_user, application
):
    """混合分类中含管理员专属分类时创建文章应返回 400 且含"管理员专属" """
    admin_cat = _make_category(tenant, name="管理员专属", is_admin_only=True)
    open_cat_1 = _make_category(tenant, name="开放分类A", is_admin_only=False)
    open_cat_2 = _make_category(tenant, name="开放分类B", is_admin_only=False)
    client = _auth_client(member_user, tenant)
    resp = client.post(
        MEMBER_ART_URL,
        {
            "title": "混合分类文章",
            "content": "内容",
            "application": application.id,
            "category_ids": [admin_cat.id, open_cat_1.id, open_cat_2.id],
        },
        format="json",
    )
    assert resp.status_code == 400
    assert "管理员专属" in _response_text(resp)


# ─── T-6: Member 编辑关联管理员专属分类的自己文章 → 403 ────────────────────────

@pytest.mark.django_db
def test_T06_member_edit_article_in_admin_only_category(tenant, member_user):
    """Member 编辑关联管理员专属分类的自己文章应返回 403"""
    admin_cat = _make_category(tenant, name="管理员专属", is_admin_only=True)
    article = _make_article(tenant, member=member_user, status="draft")
    _link_article_category(article, admin_cat, tenant)

    client = _auth_client(member_user, tenant)
    resp = client.patch(
        f"{MEMBER_ART_URL}{article.id}/",
        {"title": "修改后的标题"},
        format="json",
    )
    assert resp.status_code == 403


# ─── T-7: Member 删除关联管理员专属分类的自己文章 → 403 ────────────────────────

@pytest.mark.django_db
def test_T07_member_delete_article_in_admin_only_category(tenant, member_user):
    """Member 删除关联管理员专属分类的自己文章应返回 403"""
    admin_cat = _make_category(tenant, name="管理员专属", is_admin_only=True)
    article = _make_article(tenant, member=member_user, status="draft")
    _link_article_category(article, admin_cat, tenant)

    client = _auth_client(member_user, tenant)
    resp = client.delete(f"{MEMBER_ART_URL}{article.id}/")
    assert resp.status_code == 403


# ─── T-8: Member 发布关联管理员专属分类的草稿 → 403 ────────────────────────────

@pytest.mark.django_db
def test_T08_member_publish_article_in_admin_only_category(tenant, member_user):
    """Member 发布关联管理员专属分类的草稿文章应返回 403"""
    admin_cat = _make_category(tenant, name="管理员专属", is_admin_only=True)
    article = _make_article(tenant, member=member_user, status="draft")
    _link_article_category(article, admin_cat, tenant)

    client = _auth_client(member_user, tenant)
    resp = client.post(f"{MEMBER_ART_URL}{article.id}/publish/")
    assert resp.status_code == 403


# ─── T-9: 管理员编辑管理员专属分类下的文章 → 成功 200 ──────────────────────────

@pytest.mark.django_db
def test_T09_admin_edit_article_in_admin_only_category(tenant, admin_user):
    """管理员编辑管理员专属分类下的文章应返回 200(管理员不受限制)"""
    admin_cat = _make_category(tenant, name="管理员专属", is_admin_only=True)
    article = _make_article(tenant, user=admin_user, status="published")
    _link_article_category(article, admin_cat, tenant)

    client = _admin_client(admin_user)
    resp = client.patch(
        f"{ADMIN_ART_URL}{article.id}/",
        {"title": "管理员修改的标题"},
        format="json",
    )
    assert resp.status_code == 200


# ─── T-10: 游客 GET 管理员专属分类下的公开文章 → 200 ──────────────────────────

@pytest.mark.django_db
def test_T10_guest_get_public_article_in_admin_only_category(tenant, admin_user):
    """游客可以 GET 管理员专属分类下的已发布公开文章，返回 200"""
    admin_cat = _make_category(tenant, name="管理员专属", is_admin_only=True)
    article = _make_article(
        tenant,
        user=admin_user,
        status="published",
        visibility="public",
        title="公开文章",
    )
    _link_article_category(article, admin_cat, tenant)

    client = _guest_client(tenant)
    resp = client.get(f"{ADMIN_ART_URL}{article.id}/")
    assert resp.status_code == 200


# ─── T-11: 管理员取消 is_admin_only 标记后 Member 恢复操作权限 → 成功 ──────────

@pytest.mark.django_db
def test_T11_admin_unset_admin_only_member_restored(
    tenant, admin_user, member_user
):
    """管理员取消 is_admin_only 标记后 Member 恢复编辑权限"""
    admin_cat = _make_category(tenant, name="管理员专属", is_admin_only=True)
    article = _make_article(tenant, member=member_user, status="draft")
    _link_article_category(article, admin_cat, tenant)

    # 管理员取消 is_admin_only 标记
    admin_client = _admin_client(admin_user)
    resp = admin_client.patch(
        f"{CAT_URL}{admin_cat.id}/",
        {"is_admin_only": False},
        format="json",
    )
    assert resp.status_code == 200

    # Member 恢复编辑权限
    member_client = _auth_client(member_user, tenant)
    resp = member_client.patch(
        f"{MEMBER_ART_URL}{article.id}/",
        {"title": "恢复编辑后的标题"},
        format="json",
    )
    assert resp.status_code == 200


# ─── T-12: 文章未关联任何分类 Member 正常操作 → 成功 ──────────────────────────

@pytest.mark.django_db
def test_T12_article_without_categories_member_operates(
    tenant, member_user, application
):
    """文章未关联任何分类时 Member 可以正常创建和编辑"""
    client = _auth_client(member_user, tenant)

    # 创建无分类文章
    create_resp = client.post(
        MEMBER_ART_URL,
        {
            "title": "无分类文章",
            "content": "内容",
            "application": application.id,
        },
        format="json",
    )
    assert create_resp.status_code == 201
    article_id = _resp_data(create_resp).get("id")
    assert article_id is not None

    # Member 编辑无分类文章
    edit_resp = client.patch(
        f"{MEMBER_ART_URL}{article_id}/",
        {"title": "修改无分类文章"},
        format="json",
    )
    assert edit_resp.status_code == 200


# ─── T-13: 子分类父级是管理员专属但子分类未标记 Member 创建 → 201(不继承) ──────

@pytest.mark.django_db
def test_T13_child_of_admin_only_not_inherited(
    tenant, member_user, application
):
    """子分类的父级是管理员专属但子分类未标记时 Member 可创建文章(不继承)"""
    parent = _make_category(tenant, name="管理员专属父", is_admin_only=True)
    child = _make_category(
        tenant, name="开放子分类", is_admin_only=False, parent=parent
    )
    client = _auth_client(member_user, tenant)
    resp = client.post(
        MEMBER_ART_URL,
        {
            "title": "子分类文章",
            "content": "内容",
            "application": application.id,
            "category_ids": [child.id],
        },
        format="json",
    )
    assert resp.status_code == 201
