"""
验证反馈管理权限隔离：
1. 超级管理员 (super_admin) 不可查看/管理租户反馈数据
2. 租户主管理员 (tenant_owner) 可查看/管理当前租户下全部应用的反馈
3. 租户应用管理员 (app_admin) 仅可查看/管理其管辖应用 (UserApplication) 下的反馈、回复、统计与通知配置
"""
import pytest
from rest_framework import status
from rest_framework.test import APIClient

from applications.models import Application, UserApplication
from common.authentication.jwt_auth import generate_jwt_token
from feedbacks.models import Feedback, FeedbackNotificationConfig
from tenants.models import Tenant
from users.models import User


@pytest.mark.django_db
def test_feedback_role_and_app_scoping():
    tenant = Tenant.objects.create(name="Scope Tenant", code="scope_tenant", status="active")
    quota = tenant.ensure_quota()
    quota.max_admins = 10
    quota.save()

    app1 = Application.objects.create(tenant=tenant, name="App One", code="APP_ONE")
    app2 = Application.objects.create(tenant=tenant, name="App Two", code="APP_TWO")

    super_admin = User.objects.create_superuser(
        username="fb_super",
        email="super@scope.com",
        password="Password123!",
    )
    super_admin.is_super_admin = True
    super_admin.save()

    tenant_owner = User.objects.create_user(
        username="fb_owner",
        email="owner@scope.com",
        password="Password123!",
        tenant=tenant,
        is_admin=True,
        admin_type="tenant_owner",
    )

    app_admin = User.objects.create_user(
        username="fb_app_admin",
        email="appadmin@scope.com",
        password="Password123!",
        tenant=tenant,
        is_admin=True,
        admin_type="app_admin",
    )
    UserApplication.objects.create(tenant=tenant, user=app_admin, application=app1, role="admin")

    fb1 = Feedback.objects.create(
        tenant=tenant,
        application=app1,
        title="App1 Bug",
        description="Bug in app1",
        feedback_type="bug",
        status="submitted",
    )
    fb2 = Feedback.objects.create(
        tenant=tenant,
        application=app2,
        title="App2 Bug",
        description="Bug in app2",
        feedback_type="bug",
        status="submitted",
    )

    FeedbackNotificationConfig.objects.create(tenant=tenant, application=app1, is_enabled=True)
    FeedbackNotificationConfig.objects.create(tenant=tenant, application=app2, is_enabled=True)

    client = APIClient()

    # 1. super_admin 不可查看反馈列表或统计
    super_token = generate_jwt_token(super_admin)["access_token"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {super_token}", HTTP_X_TENANT_ID=str(tenant.id))
    res_super_list = client.get("/api/v1/feedbacks/feedbacks/")
    assert res_super_list.status_code == status.HTTP_200_OK
    super_payload = res_super_list.json()
    super_results = super_payload.get("data", super_payload).get("results", [])
    assert super_results == []
    assert client.get("/api/v1/feedbacks/statistics/").status_code == status.HTTP_403_FORBIDDEN

    # 2. tenant_owner 可查看全部 2 个应用的反馈与统计
    owner_token = generate_jwt_token(tenant_owner)["access_token"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {owner_token}", HTTP_X_TENANT_ID=str(tenant.id))
    res_owner_list = client.get("/api/v1/feedbacks/feedbacks/")
    assert res_owner_list.status_code == status.HTTP_200_OK
    owner_payload = res_owner_list.json()
    owner_results = owner_payload.get("data", owner_payload).get("results", [])
    assert {item["id"] for item in owner_results} == {fb1.id, fb2.id}

    res_owner_stats = client.get("/api/v1/feedbacks/statistics/")
    assert res_owner_stats.status_code == status.HTTP_200_OK
    owner_stats = res_owner_stats.json().get("data", res_owner_stats.json())
    assert owner_stats["total_feedbacks"] == 2

    # 3. app_admin 仅可查看/操作其管辖的 app1 反馈，对 app2 隔离返回 404/403
    app_token = generate_jwt_token(app_admin)["access_token"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {app_token}", HTTP_X_TENANT_ID=str(tenant.id))

    res_app_list = client.get("/api/v1/feedbacks/feedbacks/")
    assert res_app_list.status_code == status.HTTP_200_OK
    app_payload = res_app_list.json()
    app_results = app_payload.get("data", app_payload).get("results", [])
    assert [item["id"] for item in app_results] == [fb1.id]

    assert client.get(f"/api/v1/feedbacks/feedbacks/{fb1.id}/").status_code == status.HTTP_200_OK
    assert client.get(f"/api/v1/feedbacks/feedbacks/{fb2.id}/").status_code == status.HTTP_404_NOT_FOUND

    # 修改状态：app1 成功，app2 被拒
    assert (
        client.patch(
            f"/api/v1/feedbacks/feedbacks/{fb1.id}/status/",
            {"status": "confirmed"},
            format="json",
        ).status_code
        == status.HTTP_200_OK
    )
    assert (
        client.patch(
            f"/api/v1/feedbacks/feedbacks/{fb2.id}/status/",
            {"status": "confirmed"},
            format="json",
        ).status_code
        == status.HTTP_403_FORBIDDEN
    )

    # 统计与通知配置：仅包含 app1
    res_app_stats = client.get("/api/v1/feedbacks/statistics/")
    assert res_app_stats.status_code == status.HTTP_200_OK
    app_stats = res_app_stats.json().get("data", res_app_stats.json())
    assert app_stats["total_feedbacks"] == 1

    res_configs = client.get("/api/v1/feedbacks/notification-configs/")
    assert res_configs.status_code == status.HTTP_200_OK
    configs_payload = res_configs.json()
    configs_list = configs_payload.get("data", configs_payload)
    if isinstance(configs_list, dict):
        configs_list = configs_list.get("results", [])
    assert [c["application"] for c in configs_list] == [app1.id]
