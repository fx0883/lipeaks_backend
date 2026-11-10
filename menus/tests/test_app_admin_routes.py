"""
应用管理员动态路由与菜单自适应测试
"""
import pytest
from rest_framework import status
from rest_framework.test import APIClient

from applications.models import Application, UserApplication
from menus.models import Menu, UserMenu
from tenants.models import Tenant
from users.models import User

ROUTES_URL = "/api/v1/menus/admin/routes/"


@pytest.fixture
def tenant(db):
    t = Tenant.objects.create(name="Route Tenant", code="route_tenant")
    quota = t.ensure_quota()
    quota.max_admins = 10
    quota.save()
    return t


@pytest.fixture
def app1(tenant):
    return Application.objects.create(tenant=tenant, name="Route App", code="route_app")


@pytest.fixture
def owner(tenant):
    return User.objects.create_user(
        username="route_owner",
        email="owner@route.com",
        password="Password123!",
        tenant=tenant,
        is_admin=True,
        admin_type="tenant_owner",
    )


@pytest.fixture
def app_admin(tenant, app1):
    admin = User.objects.create_user(
        username="route_app_admin",
        email="admin@route.com",
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
def mock_menus(db):
    dashboard = Menu.objects.create(
        name="Dashboard",
        code="dashboard",
        title="仪表盘",
        path="/dashboard",
        component="layout/Dashboard",
        rank=1,
        is_active=True,
    )
    cms = Menu.objects.create(
        name="CMS",
        code="cms",
        title="内容管理",
        path="/cms",
        component="layout/Cms",
        rank=2,
        is_active=True,
    )
    cms_article = Menu.objects.create(
        name="ArticleList",
        code="cms_article",
        title="文章管理",
        path="/cms/article",
        parent=cms,
        component="cms/article/index",
        rank=1,
        is_active=True,
    )
    users = Menu.objects.create(
        name="UserManagement",
        code="user_management",
        title="用户管理",
        path="/users",
        component="layout/User",
        rank=3,
        is_active=True,
    )
    apps = Menu.objects.create(
        name="ApplicationManagement",
        code="application",
        title="应用管理",
        path="/application",
        component="layout/App",
        rank=4,
        is_active=True,
    )
    return [dashboard, cms, cms_article, users, apps]


@pytest.mark.django_db
def test_admin_routes_adaptation_for_app_admin_and_owner(
    tenant, owner, app_admin, mock_menus
):
    client = APIClient()

    # 1. 主管理员获取所有菜单 (包含用户管理和应用管理)
    client.force_authenticate(user=owner)
    res_owner = client.get(ROUTES_URL)
    assert res_owner.status_code == status.HTTP_200_OK
    owner_paths = [r["path"] for r in res_owner.data.get("data", [])]
    assert "/dashboard" in owner_paths
    assert "/cms" in owner_paths
    assert "/users" in owner_paths
    assert "/application" in owner_paths

    # 2. 应用管理员未在【用户菜单设置】中勾选任何菜单时，路由列表严格为空
    client.force_authenticate(user=app_admin)
    res_admin = client.get(ROUTES_URL)
    assert res_admin.status_code == status.HTTP_200_OK
    admin_paths = [r["path"] for r in res_admin.data.get("data", [])]
    assert admin_paths == []

    # 3. 为应用管理员勾选 CMS 后，仅展示 CMS 菜单；即使误勾选了用户管理，依然被路由安全过滤器拦截
    dashboard, cms, cms_art, users_menu, apps_menu = mock_menus
    UserMenu.objects.create(user=app_admin, menu=cms, is_active=True)
    UserMenu.objects.create(user=app_admin, menu=users_menu, is_active=True)
    res_explicit = client.get(ROUTES_URL)
    assert res_explicit.status_code == status.HTTP_200_OK
    explicit_paths = [r["path"] for r in res_explicit.data.get("data", [])]
    assert "/cms" in explicit_paths
    assert "/users" not in explicit_paths


@pytest.mark.django_db
def test_feedback_dynamic_menus_visibility_by_role(tenant, owner, app_admin):
    """验证 load_feedback_menus 导入后，super_admin 不可见，tenant_owner 全量可见，app_admin 仅见授权的应用级反馈菜单"""
    from django.core.management import call_command

    call_command("init_super_admin_menu")
    call_command("load_feedback_menus")

    super_admin = User.objects.create_superuser(
        username="route_super_admin",
        email="super@route.com",
        password="Password123!",
    )
    super_admin.is_super_admin = True
    super_admin.save()

    client = APIClient()

    # 1. 超级管理员不包含反馈管理菜单
    client.force_authenticate(user=super_admin)
    res_super = client.get(ROUTES_URL)
    assert res_super.status_code == status.HTTP_200_OK
    super_paths = [r["path"] for r in res_super.data.get("data", [])]
    assert "/feedback" not in super_paths

    # 2. 租户主管理员可见完整反馈管理菜单及子菜单
    client.force_authenticate(user=owner)
    res_owner = client.get(ROUTES_URL)
    assert res_owner.status_code == status.HTTP_200_OK
    owner_routes = {r["path"]: r for r in res_owner.data.get("data", [])}
    assert "/feedback" in owner_routes
    owner_fb_child_paths = [c["path"] for c in owner_routes["/feedback"].get("children", [])]
    assert "/feedback/list" in owner_fb_child_paths
    assert "/feedback/email/templates" in owner_fb_child_paths

    # 3. 应用管理员勾选反馈菜单后，可见应用级反馈菜单，但租户级邮件模板配置被过滤
    fb_menus = Menu.objects.filter(path__startswith="/feedback")
    for m in fb_menus:
        UserMenu.objects.create(user=app_admin, menu=m, is_active=True)

    client.force_authenticate(user=app_admin)
    res_app_admin = client.get(ROUTES_URL)
    assert res_app_admin.status_code == status.HTTP_200_OK
    app_admin_routes = {r["path"]: r for r in res_app_admin.data.get("data", [])}
    assert "/feedback" in app_admin_routes
    app_admin_fb_child_paths = [c["path"] for c in app_admin_routes["/feedback"].get("children", [])]
    assert "/feedback/list" in app_admin_fb_child_paths
    assert "/feedback/statistics" in app_admin_fb_child_paths
    assert "/feedback/email/templates" not in app_admin_fb_child_paths
