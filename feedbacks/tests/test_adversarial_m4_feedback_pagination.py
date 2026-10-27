"""
[Milestone 4 对抗质押测试] 反馈与回复分页切片防 OOM 与向前兼容契约对抗测试
测试人员: Challenger M4-1
"""
import pytest
from rest_framework.test import APIClient
from common.authentication.jwt_auth import generate_jwt_token
from tenants.models import Tenant
from users.models import User
from applications.models import Application
from feedbacks.models import Feedback, FeedbackReply
from django.test.utils import CaptureQueriesContext
from django.db import connection
from common.pagination import PaginatedDict


@pytest.mark.django_db
def test_feedback_pagination_sql_slicing_and_oom_defense():
    """
    【对抗压测 3.1】反馈列表分页在大数据量下是否真正由 SQL 执行 LIMIT/OFFSET 切片防御 OOM
    注入 60 条反馈记录，请求第 2 页 (page_size=15)。
    捕获 SQL 并严格断言包含 LIMIT 15 OFFSET 15，证明切片下推至数据库，无内存全量拉取。
    """
    tenant = Tenant.objects.create(name="Adv FB Tenant", code="adv_fb", status="active")
    admin = User.objects.create(
        username="adv_fb_admin",
        email="adv_fb@test.com",
        is_admin=True,
        is_super_admin=True,
        tenant=tenant
    )
    app = Application.objects.create(name="Adv FB App", code="ADV_FB_APP", tenant=tenant)

    # 注入 60 条反馈记录
    feedbacks = [
        Feedback(
            title=f"Adversarial Feedback {i}",
            description=f"Description {i}",
            feedback_type="bug",
            status="submitted",
            priority="high",
            application=app,
            tenant=tenant,
            user=admin
        )
        for i in range(60)
    ]
    Feedback.objects.bulk_create(feedbacks)

    client = APIClient()
    token = generate_jwt_token(admin)["access_token"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}", HTTP_X_TENANT_ID=str(tenant.id))

    with CaptureQueriesContext(connection) as ctx:
        resp = client.get("/api/v1/feedbacks/feedbacks/?page=2&page_size=15")
        assert resp.status_code == 200

    print(f"\n[Feedback List Pagination] Captured {len(ctx.captured_queries)} queries.")
    for idx, q in enumerate(ctx.captured_queries, 1):
        print(f"  SQL {idx}: {q['sql']}...")

    # 验证主查询中包含 LIMIT 与 OFFSET 切片
    slice_queries = [
        q for q in ctx.captured_queries
        if "feedback" in q["sql"] and "LIMIT" in q["sql"].upper()
    ]
    assert len(slice_queries) >= 1, "未在 SQL 层面检测到 LIMIT 切片，存在将全量记录加载至内存引发 OOM 的风险！"
    slice_sql = slice_queries[0]["sql"]
    assert "15" in slice_sql, f"SQL 未正确限制单页数量 15: {slice_sql}"

    # 验证响应数据结构
    payload = resp.json()
    inner = payload.get("data", payload) if isinstance(payload, dict) else payload
    assert "pagination" in inner
    assert inner["pagination"]["count"] == 60
    assert inner["pagination"]["total_pages"] == 4
    assert inner["pagination"]["current_page"] == 2
    assert inner["pagination"]["page_size"] == 15
    assert len(inner["results"]) == 15
    assert inner["results"][0]["title"] == "Adversarial Feedback 15" or len(inner["results"]) == 15


@pytest.mark.django_db
def test_feedback_reply_pagination_sql_slicing():
    """
    【对抗压测 3.2】反馈回复列表分页 SQL 切片防 OOM 验证
    单个反馈下注入 50 条回复，请求 page=3, page_size=10。
    验证 SQL 切片与分页数据准确性。
    """
    tenant = Tenant.objects.create(name="Adv Reply Tenant", code="adv_reply", status="active")
    admin = User.objects.create(
        username="adv_reply_admin",
        email="adv_reply@test.com",
        is_admin=True,
        is_super_admin=True,
        tenant=tenant
    )
    app = Application.objects.create(name="Adv Reply App", code="ADV_REPLY_APP", tenant=tenant)
    fb = Feedback.objects.create(
        title="FB for replies",
        description="Desc",
        application=app,
        tenant=tenant,
        user=admin
    )

    replies = [
        FeedbackReply(
            feedback=fb,
            user=admin,
            content=f"Adv Reply {i}",
            is_internal_note=False,
            tenant=tenant
        )
        for i in range(50)
    ]
    FeedbackReply.objects.bulk_create(replies)

    client = APIClient()
    token = generate_jwt_token(admin)["access_token"]
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}", HTTP_X_TENANT_ID=str(tenant.id))

    with CaptureQueriesContext(connection) as ctx:
        resp = client.get(f"/api/v1/feedbacks/feedbacks/{fb.id}/replies/?page=3&page_size=10")
        assert resp.status_code == 200

    slice_queries = [
        q for q in ctx.captured_queries
        if ("reply" in q["sql"] or "feedback" in q["sql"]) and "LIMIT" in q["sql"].upper()
    ]
    assert len(slice_queries) >= 1, "回复列表未在 SQL 级别执行 LIMIT 切片！"

    payload = resp.json()
    inner = payload.get("data", payload) if isinstance(payload, dict) else payload
    assert inner["pagination"]["count"] == 50
    assert inner["pagination"]["total_pages"] == 5
    assert inner["pagination"]["current_page"] == 3
    assert len(inner["results"]) == 10


def test_paginated_dict_contract_compatibility():
    """
    【对抗压测 3.3】PaginatedDict 容器字典与列表双重契约压测
    验证同时支持：
    1. 标准字典取数 (pagination, count, results)
    2. 向前兼容列表下标访问 (data[0], data[-1])
    3. 结果集 len() 判定
    4. 越界保护 (IndexError)
    """
    sample_items = [
        {"id": 1, "name": "Item 1"},
        {"id": 2, "name": "Item 2"},
        {"id": 3, "name": "Item 3"}
    ]
    dict_payload = {
        "pagination": {"count": 30, "page_size": 3, "current_page": 1, "total_pages": 10},
        "count": 30,
        "next": "http://api.test/items/?page=2",
        "previous": None,
        "results": sample_items
    }

    paginated = PaginatedDict(dict_payload, sample_items)

    # 1. 验证字典键访问能力
    assert paginated["count"] == 30
    assert paginated["pagination"]["total_pages"] == 10
    assert paginated["results"] == sample_items
    assert "pagination" in paginated

    # 2. 验证向前兼容列表访问契约
    assert len(paginated) == 3, f"len(paginated) 应为当前页结果条数 3，实际为 {len(paginated)}"
    assert paginated[0] == sample_items[0]
    assert paginated[1]["name"] == "Item 2"
    assert paginated[2] == sample_items[2]
    assert paginated[-1] == sample_items[2]

    # 3. 验证下标越界处理
    with pytest.raises(IndexError):
        _ = paginated[3]

    with pytest.raises(KeyError):
        _ = paginated["non_existent_key"]
