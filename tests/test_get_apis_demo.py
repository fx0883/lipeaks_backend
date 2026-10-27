"""
实际 GET API 接口调用测试脚本
验证在真实 Django 视图流水线中：
1. 多个真实业务 GET API 的请求与响应
2. Redis 全局缓存状态：X-Cache: MISS (首次) -> X-Cache: HIT (二次极速命中)
3. 响应时间对比（MISS vs HIT）
4. 排除黑名单接口（健康检查）的穿透不缓存
5. 客户端请求头 Cache-Control: no-cache 主动穿透
"""

import time
import pytest
from rest_framework.test import APIClient
from django.conf import settings
from django.core.cache import caches
from tenants.models import Tenant
from users.models import User
from menus.models import Menu
from cms.models import Category, Article


@pytest.mark.django_db
def test_real_get_apis_with_redis_cache():
    print("\n" + "=" * 80)
    print("           REAL GET APIs REDIS CACHE VERIFICATION RUN")
    print("=" * 80)

    # 启用真实 Redis 缓存 (DB 1)
    from core.settings import _get_cache_backend_config
    settings.CACHES['default'] = _get_cache_backend_config('redis://127.0.0.1:6379/1')
    settings.API_CACHE_ENABLED = True
    if 'common.middleware.api_cache_middleware.APICacheMiddleware' not in settings.MIDDLEWARE:
        settings.MIDDLEWARE = [
            'common.middleware.api_auth_middleware.APIAuthMiddleware',
            'common.middleware.tenant_middleware.TenantMiddleware',
            'common.middleware.api_cache_middleware.APICacheMiddleware',
            'common.middleware.response_standardization_middleware.ResponseStandardizationMiddleware',
        ]
    cache = caches['default']
    cache.clear()

    # 1. 初始化测试数据
    tenant = Tenant.objects.create(name="LiPeaks Tech Corp", code="lipeaks_tech", status="active")
    admin_user = User.objects.create_user(
        username="tech_admin",
        password="password123",
        is_admin=True,
        is_super_admin=True,
        tenant=tenant
    )

    # 菜单数据 (系统全局)
    m1 = Menu.objects.create(name="dashboard", code="dashboard", title="仪表盘", path="/admin/dashboard", component="Dashboard")
    m2 = Menu.objects.create(name="cms", code="cms", title="内容管理", path="/admin/cms", component="CMS")
    m3 = Menu.objects.create(name="settings", code="settings", title="系统设置", path="/admin/settings", component="Settings")

    # 分类与文章数据
    cat1 = Category.objects.create(name="人工智能", slug="ai-tech", tenant=tenant)
    cat2 = Category.objects.create(name="云原生与架构", slug="cloud-architecture", tenant=tenant)
    for i in range(1, 6):
        Article.objects.create(
            title=f"企业级架构实践深度探索 第 {i} 讲",
            slug=f"enterprise-arch-practice-{i}",
            content=f"这是文章 {i} 的正文内容，涵盖 Redis 与微服务架构最佳实践。",
            tenant=tenant,
            user=admin_user,
            status="published"
        )

    from common.authentication.jwt_auth import generate_jwt_token
    token = generate_jwt_token(admin_user)['access_token']
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}", HTTP_X_TENANT_ID=str(tenant.id))

    test_endpoints = [
        {
            "name": "API 1: 菜单列表接口 (Menus Catalog)",
            "url": "/api/v1/menus/",
            "expect_cache": True,
        },
        {
            "name": "API 2: 文章分类接口 (CMS Categories)",
            "url": "/api/v1/cms/categories/",
            "expect_cache": True,
        },
        {
            "name": "API 3: 文章列表分页接口 (CMS Articles with Pagination)",
            "url": "/api/v1/cms/articles/?status=published&page=1&page_size=10",
            "expect_cache": True,
        },
        {
            "name": "API 4: 健康检查探针接口 (Health Check - 黑名单应豁免缓存)",
            "url": "/api/v1/feedbacks/health/",
            "expect_cache": False,
        },
    ]

    for item in test_endpoints:
        print(f"\n--- 测试接口: {item['name']} ---")
        print(f"URL: {item['url']}")

        # 第一次请求 (First Request)
        t0 = time.perf_counter()
        resp1 = client.get(item['url'])
        dur1 = (time.perf_counter() - t0) * 1000

        cache_status1 = resp1.get('X-Cache', 'NONE')
        cache_key1 = resp1.get('X-Cache-Key', 'NONE')
        print(f"  [第 1 次请求 - 查库写缓存]")
        print(f"    Status: {resp1.status_code}")
        print(f"    X-Cache: {cache_status1}")
        print(f"    X-Cache-Key: {cache_key1}")
        print(f"    耗时: {dur1:.2f} ms")
        print(f"    数据摘要: {resp1.content[:100]}...")

        if item['expect_cache']:
            assert resp1.status_code == 200
            assert cache_status1 == 'MISS', f"首次请求预期为 MISS，实测为 {cache_status1}"

            # 第二次请求 (Second Request - Identical)
            t1 = time.perf_counter()
            resp2 = client.get(item['url'])
            dur2 = (time.perf_counter() - t1) * 1000

            cache_status2 = resp2.get('X-Cache', 'NONE')
            print(f"  [第 2 次请求 - Redis 直接直出]")
            print(f"    Status: {resp2.status_code}")
            print(f"    X-Cache: {cache_status2}")
            print(f"    耗时: {dur2:.2f} ms (提速 {(dur1 / max(dur2, 0.001)):.1f} 倍)")
            assert resp2.status_code == 200
            assert cache_status2 == 'HIT', f"二次请求预期为 HIT，实测为 {cache_status2}"
            assert resp1.content == resp2.content, "缓存数据必须与首次响应完全一致"

            # 第三次请求：携带 Cache-Control: no-cache 主动穿透
            t2 = time.perf_counter()
            resp3 = client.get(item['url'], HTTP_CACHE_CONTROL='no-cache')
            dur3 = (time.perf_counter() - t2) * 1000
            cache_status3 = resp3.get('X-Cache', 'NONE')
            print(f"  [第 3 次请求 - 带 Cache-Control: no-cache 穿透]")
            print(f"    Status: {resp3.status_code}")
            print(f"    X-Cache: {cache_status3} (成功穿透 Redis)")
            assert cache_status3 == 'MISS'
        else:
            # 黑名单接口，不生成 X-Cache 头
            print(f"  [黑名单接口验证]: 成功跳过缓存处理，X-Cache={cache_status1}")
            assert cache_status1 == 'NONE'

    print("\n" + "=" * 80)
    print("           ALL GET APIs PASSED REAL REDIS CACHING TESTS!")
    print("=" * 80 + "\n")
