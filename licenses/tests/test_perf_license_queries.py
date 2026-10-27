"""
[PERF-02 回归测试] 许可证管理模块 ViewSet 全套预加载与查询次数优化验证
"""
import pytest
from rest_framework.test import APIClient
from django.test.utils import CaptureQueriesContext
from django.db import connection
from common.authentication.jwt_auth import generate_jwt_token
from tenants.models import Tenant
from users.models import User
from datetime import timedelta
from django.utils import timezone
from applications.models import Application
from licenses.models import LicensePlan, License, MachineBinding, LicenseActivation


@pytest.mark.django_db
def test_license_list_eliminates_n_plus_one():
    """
    [PERF-02 回归测试]
    创建 10 个许可证，每个许可证关联 2 个机器绑定 (1 active, 1 inactive)。
    验证许可证列表接口查询次数为常数级 (<= 8 次)，彻底消除跨表读取 application, plan, tenant 及绑定计数的 80+ 次查询风暴。
    """
    tenant = Tenant.objects.create(name="Lic Perf Tenant", code="lic_perf", status="active")
    admin = User.objects.create(
        username="lic_admin_perf",
        email="lic_perf@test.com",
        is_admin=True,
        is_super_admin=True,
        tenant=tenant
    )
    app = Application.objects.create(name="Perf App", code="PERF_APP", tenant=tenant)
    plan = LicensePlan.objects.create(name="Pro Plan", code="PRO", plan_type="professional", application=app)
    expire_time = timezone.now() + timedelta(days=365)

    for i in range(10):
        lic = License.objects.create(
            application=app,
            plan=plan,
            tenant=tenant,
            license_key=f"LIC-PERF-{i:04d}",
            license_hash=f"hash-{i:04d}",
            customer_name=f"Customer {i}",
            status="activated",
            expires_at=expire_time
        )
        MachineBinding.objects.create(license=lic, machine_id=f"M-{i}-A", machine_fingerprint=f"fp-{i}-A", status="active")
        MachineBinding.objects.create(license=lic, machine_id=f"M-{i}-B", machine_fingerprint=f"fp-{i}-B", status="inactive")

    client = APIClient()
    token = generate_jwt_token(admin)["access_token"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}", HTTP_X_TENANT_ID=str(tenant.id))

    # 未优化前产生 1 (count) + 1 (list) + 10*4 = 42~82 次查询；优化后常数级锁定在 <= 8 次
    with CaptureQueriesContext(connection) as ctx:
        response = client.get("/api/v1/licenses/admin/licenses/")
        assert response.status_code == 200
        payload = response.json()
        inner_data = payload.get("data", payload) if isinstance(payload, dict) else payload
        results = inner_data.get("results", [])
        assert len(results) == 10
        # 验证 active_bindings_count 准确统计为 1 (过滤 inactive)
        assert results[0]["machine_bindings_count"] == 1
        assert results[0]["application_name"] == "Perf App"
        assert results[0]["plan_name"] == "Pro Plan"

    assert len(ctx.captured_queries) <= 8


@pytest.mark.django_db
def test_machine_binding_list_preloads_license():
    """
    [PERF-02 回归测试]
    验证 MachineBindingViewSet 请求列表时对 license 外键预加载，单页查询 <= 8 次。
    """
    tenant = Tenant.objects.create(name="MB Perf Tenant", code="mb_perf", status="active")
    admin = User.objects.create(
        username="mb_admin_perf",
        email="mb_perf@test.com",
        is_admin=True,
        is_super_admin=False,
        tenant=tenant
    )
    app = Application.objects.create(name="MB App", code="MB_APP", tenant=tenant)
    plan = LicensePlan.objects.create(name="MB Plan", code="MBP", plan_type="basic", application=app)
    lic = License.objects.create(
        application=app,
        plan=plan,
        tenant=tenant,
        license_key="LIC-MB-0001",
        license_hash="hash-mb-0001",
        customer_name="MB Customer",
        status="activated",
        expires_at=timezone.now() + timedelta(days=365)
    )

    for i in range(10):
        MachineBinding.objects.create(
            license=lic,
            tenant=tenant,
            machine_id=f"MB-{i}",
            machine_fingerprint=f"fp-mb-{i}",
            status="active"
        )

    client = APIClient()
    token = generate_jwt_token(admin)["access_token"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}", HTTP_X_TENANT_ID=str(tenant.id))

    with CaptureQueriesContext(connection) as ctx:
        response = client.get("/api/v1/licenses/admin/machine-bindings/")
        assert response.status_code == 200
        payload = response.json()
        inner_data = payload.get("data", payload) if isinstance(payload, dict) else payload
        results = inner_data.get("results", [])
        assert len(results) == 10

    assert len(ctx.captured_queries) <= 8
