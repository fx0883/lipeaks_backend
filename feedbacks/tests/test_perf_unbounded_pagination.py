"""
[PERF-03 回归测试] 反馈系统无界查询治理与防 OOM 分页验证
"""
import pytest
from rest_framework.test import APIClient
from common.authentication.jwt_auth import generate_jwt_token
from tenants.models import Tenant
from users.models import User
from applications.models import Application
from feedbacks.models import Feedback, FeedbackReply, EmailTemplate


@pytest.mark.django_db
def test_feedback_list_pagination():
    """
    [PERF-03 回归测试]
    验证反馈列表接口具备标准分页能力，避免全量无界查询导致 OOM。
    """
    tenant = Tenant.objects.create(name="FB Perf Tenant", code="fb_perf", status="active")
    admin = User.objects.create(
        username="fb_admin_perf",
        email="fb@test.com",
        is_admin=True,
        is_super_admin=False,
        tenant=tenant
    )
    app = Application.objects.create(name="FB App", code="FB_APP", tenant=tenant)

    # 批量创建 15 条反馈记录
    for i in range(15):
        Feedback.objects.create(
            title=f"Feedback {i}",
            description=f"Desc {i}",
            feedback_type="bug",
            status="submitted",
            priority="medium",
            application=app,
            tenant=tenant,
            user=admin
        )

    client = APIClient()
    token = generate_jwt_token(admin)["access_token"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}", HTTP_X_TENANT_ID=str(tenant.id))

    # 1. 默认请求：每页最多 10 条
    response = client.get("/api/v1/feedbacks/feedbacks/")
    assert response.status_code == 200
    payload = response.json()
    inner = payload.get("data", payload) if isinstance(payload, dict) else payload

    assert "pagination" in inner
    assert inner["pagination"]["count"] == 15
    assert len(inner["results"]) == 10

    # 2. 自定义 page_size 参数请求
    response_p5 = client.get("/api/v1/feedbacks/feedbacks/?page_size=5")
    assert response_p5.status_code == 200
    payload_p5 = response_p5.json()
    inner_p5 = payload_p5.get("data", payload_p5) if isinstance(payload_p5, dict) else payload_p5
    assert len(inner_p5["results"]) == 5


@pytest.mark.django_db
def test_feedback_reply_list_pagination():
    """
    [PERF-03 回归测试]
    验证反馈回复列表接口具备标准分页能力。
    """
    tenant = Tenant.objects.create(name="Reply Perf Tenant", code="reply_perf", status="active")
    admin = User.objects.create(
        username="reply_admin_perf",
        email="reply@test.com",
        is_admin=True,
        is_super_admin=False,
        tenant=tenant
    )
    app = Application.objects.create(name="Reply App", code="REPLY_APP", tenant=tenant)
    fb = Feedback.objects.create(
        title="FB with many replies",
        description="Desc",
        application=app,
        tenant=tenant,
        user=admin
    )

    for i in range(12):
        FeedbackReply.objects.create(
            feedback=fb,
            user=admin,
            content=f"Reply {i}",
            is_internal_note=False,
            tenant=tenant
        )

    client = APIClient()
    token = generate_jwt_token(admin)["access_token"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}", HTTP_X_TENANT_ID=str(tenant.id))

    response = client.get(f"/api/v1/feedbacks/feedbacks/{fb.id}/replies/")
    assert response.status_code == 200
    payload = response.json()
    inner = payload.get("data", payload) if isinstance(payload, dict) else payload

    assert "pagination" in inner
    assert inner["pagination"]["count"] == 12
    assert len(inner["results"]) == 10


@pytest.mark.django_db
def test_email_template_list_pagination():
    """
    [PERF-03 回归测试]
    验证邮件模板列表接口具备标准分页能力。
    """
    tenant = Tenant.objects.create(name="Email Perf Tenant", code="email_perf", status="active")
    admin = User.objects.create(
        username="email_admin_perf",
        email="email@test.com",
        is_admin=True,
        is_super_admin=False,
        tenant=tenant
    )

    for i in range(12):
        EmailTemplate.objects.create(
            name=f"Template {i}",
            template_type="reply",
            subject=f"Subject {i}",
            body_html=f"<p>Body {i}</p>",
            body_text=f"Body {i}",
            tenant=tenant
        )

    client = APIClient()
    token = generate_jwt_token(admin)["access_token"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}", HTTP_X_TENANT_ID=str(tenant.id))

    response = client.get("/api/v1/feedbacks/email-templates/")
    assert response.status_code == 200
    payload = response.json()
    inner = payload.get("data", payload) if isinstance(payload, dict) else payload

    assert "pagination" in inner
    assert inner["pagination"]["count"] == 12
    assert len(inner["results"]) == 10
