"""
应用管理员 CMS 内容与应用范围严格隔离测试
"""
import pytest
from rest_framework import status
from rest_framework.test import APIClient

from applications.models import Application, UserApplication
from cms.models import Article, ArticleApplication, ArticleCategory, Category
from tenants.models import Tenant
from users.models import User

CAT_URL = "/api/v1/cms/categories/"
ART_URL = "/api/v1/cms/articles/"
APP_URL = "/api/v1/applications/"


@pytest.fixture
def tenant(db):
    t = Tenant.objects.create(name="CMS Tenant", code="cms_tenant")
    quota = t.ensure_quota()
    quota.max_admins = 10
    quota.save()
    return t


@pytest.fixture
def app1(tenant):
    return Application.objects.create(tenant=tenant, name="App One", code="app_one")


@pytest.fixture
def app2(tenant):
    return Application.objects.create(tenant=tenant, name="App Two", code="app_two")


@pytest.fixture
def owner(tenant):
    return User.objects.create_user(
        username="tenant_owner",
        email="owner@cms.com",
        password="Password123!",
        tenant=tenant,
        is_admin=True,
        admin_type="tenant_owner",
    )


@pytest.fixture
def app_admin(tenant, app1):
    admin = User.objects.create_user(
        username="app_admin_cms",
        email="app_admin@cms.com",
        password="Password123!",
        tenant=tenant,
        is_admin=True,
        admin_type="app_admin",
    )
    UserApplication.objects.create(
        tenant=tenant,
        user=admin,
        application=app1,
        role="admin",
    )
    return admin


@pytest.fixture
def categories(tenant, app1, app2):
    # 1. 全局公共分类
    global_cat = Category.objects.create(
        tenant=tenant,
        name="全局分类",
        slug="global-cat",
        application=None,
    )
    # 2. App 1 分类
    app1_cat = Category.objects.create(
        tenant=tenant,
        name="App1分类",
        slug="app1-cat",
        application=app1,
    )
    # 3. App 2 分类
    app2_cat = Category.objects.create(
        tenant=tenant,
        name="App2分类",
        slug="app2-cat",
        application=app2,
    )
    return global_cat, app1_cat, app2_cat


@pytest.fixture
def articles(tenant, owner, app1, app2, categories):
    global_cat, app1_cat, app2_cat = categories

    art1 = Article.objects.create(
        tenant=tenant,
        user=owner,
        title="App1 Article",
        slug="app1-art",
        content="App1 content",
    )
    ArticleApplication.objects.create(
        tenant=tenant, article=art1, application=app1
    )
    ArticleCategory.objects.create(
        tenant=tenant, article=art1, category=app1_cat
    )

    art2 = Article.objects.create(
        tenant=tenant,
        user=owner,
        title="App2 Article",
        slug="app2-art",
        content="App2 content",
    )
    ArticleApplication.objects.create(
        tenant=tenant, article=art2, application=app2
    )
    ArticleCategory.objects.create(
        tenant=tenant, article=art2, category=app2_cat
    )

    return art1, art2


@pytest.mark.django_db
def test_category_list_hides_global_and_other_apps_for_app_admin(
    tenant, app_admin, owner, categories
):
    global_cat, app1_cat, app2_cat = categories
    client = APIClient()

    # 1. 主管理员能看到全部 3 个分类
    client.force_authenticate(user=owner)
    res_owner = client.get(CAT_URL, HTTP_X_TENANT_ID=str(tenant.id))
    assert res_owner.status_code == status.HTTP_200_OK
    owner_cat_ids = [c["id"] for c in res_owner.data.get("data", res_owner.data)]
    assert global_cat.id in owner_cat_ids
    assert app1_cat.id in owner_cat_ids
    assert app2_cat.id in owner_cat_ids

    # 2. 应用管理员只能看到 App1 分类，全局分类和 App2 分类均完全不可见
    client.force_authenticate(user=app_admin)
    res_admin = client.get(CAT_URL, HTTP_X_TENANT_ID=str(tenant.id))
    assert res_admin.status_code == status.HTTP_200_OK
    admin_cat_ids = [c["id"] for c in res_admin.data.get("data", res_admin.data)]
    assert app1_cat.id in admin_cat_ids
    assert global_cat.id not in admin_cat_ids
    assert app2_cat.id not in admin_cat_ids


@pytest.mark.django_db
def test_category_create_forbidden_for_global_or_other_app(
    tenant, app_admin, app1, app2
):
    client = APIClient()
    client.force_authenticate(user=app_admin)

    # 1. 尝试创建全局公共分类 -> 403 拒绝
    res1 = client.post(
        CAT_URL,
        {
            "translations": {"zh-hans": {"name": "非法全局分类"}},
            "slug": "bad-global",
            "application": None,
        },
        format="json",
        HTTP_X_TENANT_ID=str(tenant.id),
    )
    assert res1.status_code in (
        status.HTTP_403_FORBIDDEN,
        status.HTTP_400_BAD_REQUEST,
    )

    # 2. 尝试创建非管辖 App2 分类 -> 403 拒绝
    res2 = client.post(
        CAT_URL,
        {
            "translations": {"zh-hans": {"name": "非法App2分类"}},
            "slug": "bad-app2",
            "application": app2.id,
        },
        format="json",
        HTTP_X_TENANT_ID=str(tenant.id),
    )
    assert res2.status_code in (
        status.HTTP_403_FORBIDDEN,
        status.HTTP_400_BAD_REQUEST,
    )

    # 3. 创建管辖 App1 分类 -> 201 成功
    res3 = client.post(
        CAT_URL,
        {
            "translations": {"zh-hans": {"name": "合法App1分类"}},
            "slug": "good-app1",
            "application": app1.id,
        },
        format="json",
        HTTP_X_TENANT_ID=str(tenant.id),
    )
    assert res3.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_article_list_scopes_to_managed_apps_for_app_admin(
    tenant, app_admin, owner, articles
):
    art1, art2 = articles
    client = APIClient()

    # 1. 主管理员看到全部文章
    client.force_authenticate(user=owner)
    res_owner = client.get(ART_URL, HTTP_X_TENANT_ID=str(tenant.id))
    assert res_owner.status_code == status.HTTP_200_OK
    owner_art_ids = [
        a["id"]
        for a in (
            res_owner.data.get("results")
            or res_owner.data.get("data", {}).get("results")
            or res_owner.data
        )
    ]
    assert art1.id in owner_art_ids
    assert art2.id in owner_art_ids

    # 2. 应用管理员只能看到 App1 的文章，看不到 App2 的文章
    client.force_authenticate(user=app_admin)
    res_admin = client.get(ART_URL, HTTP_X_TENANT_ID=str(tenant.id))
    assert res_admin.status_code == status.HTTP_200_OK
    admin_art_ids = [
        a["id"]
        for a in (
            res_admin.data.get("results")
            or res_admin.data.get("data", {}).get("results")
            or res_admin.data
        )
    ]
    assert art1.id in admin_art_ids
    assert art2.id not in admin_art_ids


@pytest.mark.django_db
def test_application_list_and_update_for_app_admin(tenant, app_admin, app1, app2):
    client = APIClient()
    client.force_authenticate(user=app_admin)

    # 1. 列表仅返回管辖的 app1
    res = client.get(APP_URL, HTTP_X_TENANT_ID=str(tenant.id))
    assert res.status_code == status.HTTP_200_OK
    app_ids = [
        a["id"]
        for a in (
            res.data.get("results")
            or res.data.get("data", {}).get("results")
            or res.data
        )
    ]
    assert app1.id in app_ids
    assert app2.id not in app_ids

    # 2. 应用管理员禁止修改应用设置 (PATCH/PUT -> 403)
    patch_res = client.patch(
        f"{APP_URL}{app1.id}/",
        {"name": "Hacked App"},
        format="json",
        HTTP_X_TENANT_ID=str(tenant.id),
    )
    assert patch_res.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_article_create_and_update_restrictions_for_app_admin(
    tenant, app_admin, app1, app2, categories
):
    global_cat, app1_cat, app2_cat = categories
    client = APIClient()
    client.force_authenticate(user=app_admin)

    # 1. 创建文章未传应用 -> 400 拒绝
    res_no_app = client.post(
        ART_URL,
        {
            "title": "No App Article",
            "content": "Content",
            "category_ids": [app1_cat.id],
        },
        format="json",
        HTTP_X_TENANT_ID=str(tenant.id),
    )
    assert res_no_app.status_code == status.HTTP_400_BAD_REQUEST

    # 2. 创建文章关联非管辖应用 app2 -> 400 拒绝
    res_bad_app = client.post(
        ART_URL,
        {
            "title": "Bad App Article",
            "content": "Content",
            "applications": [app2.id],
            "category_ids": [app1_cat.id],
        },
        format="json",
        HTTP_X_TENANT_ID=str(tenant.id),
    )
    assert res_bad_app.status_code == status.HTTP_400_BAD_REQUEST

    # 3. 创建文章使用全局公共分类 -> 400 拒绝
    res_global_cat = client.post(
        ART_URL,
        {
            "title": "Global Cat Article",
            "content": "Content",
            "applications": [app1.id],
            "category_ids": [global_cat.id],
        },
        format="json",
        HTTP_X_TENANT_ID=str(tenant.id),
    )
    assert res_global_cat.status_code == status.HTTP_400_BAD_REQUEST

    # 4. 创建文章使用 app2 分类 -> 400 拒绝
    res_app2_cat = client.post(
        ART_URL,
        {
            "title": "App2 Cat Article",
            "content": "Content",
            "applications": [app1.id],
            "category_ids": [app2_cat.id],
        },
        format="json",
        HTTP_X_TENANT_ID=str(tenant.id),
    )
    assert res_app2_cat.status_code == status.HTTP_400_BAD_REQUEST

    # 5. 合法创建管辖应用文章 (app1 + app1_cat) -> 201 成功
    res_good = client.post(
        ART_URL,
        {
            "title": "Good App1 Article",
            "content": "Valid Content",
            "applications": [app1.id],
            "category_ids": [app1_cat.id],
        },
        format="json",
        HTTP_X_TENANT_ID=str(tenant.id),
    )
    assert res_good.status_code == status.HTTP_201_CREATED
    art_id = res_good.data.get("data", {}).get("id") or res_good.data.get("id")

    # 6. 修改自己管辖的文章 -> 200 成功
    patch_good = client.patch(
        f"{ART_URL}{art_id}/",
        {"title": "Updated Good App1 Article"},
        format="json",
        HTTP_X_TENANT_ID=str(tenant.id),
    )
    assert patch_good.status_code == status.HTTP_200_OK

    # 7. 删除自己管辖的文章 -> 204 成功
    del_good = client.delete(
        f"{ART_URL}{art_id}/",
        HTTP_X_TENANT_ID=str(tenant.id),
    )
    assert del_good.status_code in (status.HTTP_204_NO_CONTENT, status.HTTP_200_OK)


@pytest.mark.django_db
def test_app_admin_sees_all_articles_under_managed_app_and_category(
    tenant, app_admin, owner, app1, app2, categories
):
    global_cat, app1_cat, app2_cat = categories
    client = APIClient()

    # 1. 租户所有者创建由其发布的属于 App1 的两篇文章（包含分类 app1_cat）
    art_owner1 = Article.objects.create(
        tenant=tenant,
        user=owner,
        title="Owner App1 Published Article",
        slug="owner-app1-pub",
        content="Published content",
        status="published",
    )
    ArticleApplication.objects.create(tenant=tenant, article=art_owner1, application=app1)
    ArticleCategory.objects.create(tenant=tenant, article=art_owner1, category=app1_cat)

    art_owner2 = Article.objects.create(
        tenant=tenant,
        user=owner,
        title="Owner App1 Another Article",
        slug="owner-app1-another",
        content="Another content",
        status="archived",
    )
    ArticleApplication.objects.create(tenant=None, article=art_owner2, application=app1)  # 模拟中间表 tenant 为 None
    ArticleCategory.objects.create(tenant=None, article=art_owner2, category=app1_cat)

    # 2. 属于 App2 的文章
    art_app2 = Article.objects.create(
        tenant=tenant,
        user=owner,
        title="App2 Hidden Article",
        slug="app2-hidden",
        content="Hidden content",
        status="published",
    )
    ArticleApplication.objects.create(tenant=tenant, article=art_app2, application=app2)
    ArticleCategory.objects.create(tenant=tenant, article=art_app2, category=app2_cat)

    # 3. app_admin 查询全部文章：必须看到 App1 下的两篇文章（无论谁创建、无论中间表 tenant 是否为 None），绝不能看到 App2 的文章
    client.force_authenticate(user=app_admin)
    res = client.get(ART_URL, HTTP_X_TENANT_ID=str(tenant.id))
    assert res.status_code == status.HTTP_200_OK
    items = res.data.get("data", {}).get("results", res.data.get("results", []))
    ids = [item["id"] for item in items]
    assert art_owner1.id in ids
    assert art_owner2.id in ids
    assert art_app2.id not in ids

    # 4. app_admin 按 category_id 过滤
    res_cat = client.get(f"{ART_URL}?category_id={app1_cat.id}", HTTP_X_TENANT_ID=str(tenant.id))
    assert res_cat.status_code == status.HTTP_200_OK
    cat_items = res_cat.data.get("data", {}).get("results", res_cat.data.get("results", []))
    cat_ids = [item["id"] for item in cat_items]
    assert art_owner1.id in cat_ids
    assert art_owner2.id in cat_ids
    assert art_app2.id not in cat_ids
