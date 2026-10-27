"""
[Milestone 4 对抗质押测试] 许可证管理模块查询次数对抗压测
测试人员: Challenger M4-1
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
from licenses.models import LicensePlan, License, MachineBinding


@pytest.mark.django_db
def test_license_list_constant_two_queries_adversarial():
    """
    【对抗压测 2.1】许可证列表单页查询是否稳定为常数级 (严格消除逐行 COUNT 查询)
    注入 25 个许可证，每个许可证绑定 3 个机器记录 (2 active, 1 inactive)。
    使用 CaptureQueriesContext 捕获并检查执行的 SQL 语句。
    """
    tenant = Tenant.objects.create(name="Adv Lic Tenant", code="adv_lic", status="active")
    admin = User.objects.create(
        username="adv_lic_admin",
        email="adv_lic@test.com",
        is_admin=True,
        is_super_admin=True,
        tenant=tenant
    )
    app = Application.objects.create(name="Adv App", code="ADV_APP", tenant=tenant)
    plan = LicensePlan.objects.create(name="Adv Pro Plan", code="ADV_PRO", plan_type="professional", application=app)
    expire_time = timezone.now() + timedelta(days=365)

    # 注入 25 个许可证，每个关联 3 个 MachineBinding
    for i in range(25):
        lic = License.objects.create(
            application=app,
            plan=plan,
            tenant=tenant,
            license_key=f"LIC-ADV-{i:04d}",
            license_hash=f"hash-adv-{i:04d}",
            customer_name=f"Customer {i}",
            status="activated",
            expires_at=expire_time
        )
        MachineBinding.objects.create(license=lic, tenant=tenant, machine_id=f"M-{i}-A", machine_fingerprint=f"fp-{i}-A", status="active")
        MachineBinding.objects.create(license=lic, tenant=tenant, machine_id=f"M-{i}-B", machine_fingerprint=f"fp-{i}-B", status="active")
        MachineBinding.objects.create(license=lic, tenant=tenant, machine_id=f"M-{i}-C", machine_fingerprint=f"fp-{i}-C", status="inactive")

    client = APIClient()
    token = generate_jwt_token(admin)["access_token"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}", HTTP_X_TENANT_ID=str(tenant.id))

    # 预热一次缓存与认证
    client.get("/api/v1/licenses/admin/licenses/?page=1&page_size=20")

    with CaptureQueriesContext(connection) as ctx:
        resp = client.get("/api/v1/licenses/admin/licenses/?page=1&page_size=20")
        assert resp.status_code == 200

    query_count = len(ctx.captured_queries)
    print(f"\n[License List Adv] 25 Licenses with 75 Bindings Captured Queries: {query_count}")
    for idx, q in enumerate(ctx.captured_queries, 1):
        print(f"  SQL {idx}: {q['sql'][:140]}... ({q['time']}s)")

    # 验证是否消除了逐行 COUNT 查询（杜绝任何 SELECT COUNT(*) FROM licenses_machinebinding WHERE license_id = ...）
    row_count_queries = [
        q for q in ctx.captured_queries
        if "licenses_machinebinding" in q["sql"] and "COUNT" in q["sql"] and "GROUP BY" not in q["sql"]
    ]
    assert len(row_count_queries) == 0, f"发现逐行 COUNT 机器绑定查询漏洞！数量: {len(row_count_queries)}"

    # 验证业务查询部分：1 次 count + 1 次带有 annotate 聚合的分页列表
    # 算上框架鉴权（如果有），总查询数也必须是极少数常数
    license_table_queries = [
        q for q in ctx.captured_queries if "licenses_license" in q["sql"]
    ]
    assert len(license_table_queries) == 2, f"许可证核心表查询次数预期为 2 次，实际为 {len(license_table_queries)} 次"

    # 验证活跃机器绑定数量注解计算准确（2 个 active，1 个 inactive）
    payload = resp.json()
    results = payload["data"]["results"] if "data" in payload else payload["results"]
    assert len(results) == 20
    assert results[0]["machine_bindings_count"] == 2
    assert results[0]["application_name"] == "Adv App"
    assert results[0]["plan_name"] == "Adv Pro Plan"


@pytest.mark.django_db
def test_license_viewset_direct_query_strictly_two():
    """
    【对抗压测 2.2】直接调用 LicenseViewSet list 逻辑，断言 SQL 查询次数严格为 2 次
    查询 1: COUNT(*) 分页计数
    查询 2: 主查询 (select_related + annotate active_bindings_count)
    """
    from rest_framework.test import APIRequestFactory
    from licenses.views.admin_views import LicenseViewSet

    tenant = Tenant.objects.create(name="Adv Direct Tenant", code="adv_direct", status="active")
    admin = User.objects.create(username="adv_direct_admin", email="direct@test.com", is_admin=True, tenant=tenant)
    app = Application.objects.create(name="Direct App", code="DIR_APP", tenant=tenant)
    plan = LicensePlan.objects.create(name="Direct Plan", code="DIR_P", plan_type="basic", application=app)

    # 注入 25 条带机器绑定的许可证
    for i in range(25):
        lic = License.objects.create(
            application=app,
            plan=plan,
            tenant=tenant,
            license_key=f"LIC-DIR-{i:04d}",
            license_hash=f"hash-dir-{i:04d}",
            customer_name=f"Customer {i}",
            status="activated",
            expires_at=timezone.now() + timedelta(days=30)
        )
        MachineBinding.objects.create(license=lic, tenant=tenant, machine_id=f"M-DIR-{i}", machine_fingerprint=f"fp-dir-{i}", status="active")

    factory = APIRequestFactory()
    request = factory.get("/api/v1/licenses/admin/licenses/?page=1&page_size=20", HTTP_X_TENANT_ID=str(tenant.id))
    from rest_framework.test import force_authenticate
    force_authenticate(request, user=admin)
    request.tenant = tenant

    view = LicenseViewSet.as_view({'get': 'list'})

    with CaptureQueriesContext(connection) as ctx:
        response = view(request)
        assert response.status_code == 200

    print(f"\n[License ViewSet Direct] Total Captured Queries: {len(ctx.captured_queries)}")
    for idx, q in enumerate(ctx.captured_queries, 1):
        print(f"  Direct SQL {idx}: {q['sql'][:140]}...")

    # 严格断言纯视图层查询稳定为 2 次
    assert len(ctx.captured_queries) == 2, f"ViewSet 预期产生 2 次 SQL（1次Count+1次数据），实际产生 {len(ctx.captured_queries)} 次"
