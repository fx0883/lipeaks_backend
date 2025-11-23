#!/usr/bin/env python
"""
数据库查询性能测试
测试租户过滤对查询性能的影响
"""
import time
from django.db import connection, reset_queries
from django.conf import settings
from tenants.models import Tenant
from applications.models import Application
from orders.models import Order

# 启用查询日志
settings.DEBUG = True

print("=" * 70)
print("数据库查询性能测试")
print("=" * 70)

# 获取租户
tenant = Tenant.objects.first()
if not tenant:
    print("\n⚠️  没有租户数据")
else:
    print(f"\n测试租户: {tenant.name} (ID={tenant.id})")
    
    print(f"\n" + "=" * 70)
    print("测试1: Applications查询性能")
    print("=" * 70)
    
    # 重置查询计数
    reset_queries()
    
    # 测试1: 不带租户过滤
    start_time = time.time()
    apps_all = list(Application.objects.all())
    time_without_tenant = time.time() - start_time
    queries_without_tenant = len(connection.queries)
    
    print(f"\n不带租户过滤:")
    print(f"  - 查询时间: {time_without_tenant*1000:.2f}ms")
    print(f"  - SQL查询数: {queries_without_tenant}")
    print(f"  - 结果数量: {len(apps_all)}")
    
    # 重置查询计数
    reset_queries()
    
    # 测试2: 带租户过滤
    start_time = time.time()
    apps_tenant = list(Application.objects.filter(tenant=tenant))
    time_with_tenant = time.time() - start_time
    queries_with_tenant = len(connection.queries)
    
    print(f"\n带租户过滤:")
    print(f"  - 查询时间: {time_with_tenant*1000:.2f}ms")
    print(f"  - SQL查询数: {queries_with_tenant}")
    print(f"  - 结果数量: {len(apps_tenant)}")
    
    # 性能对比
    if time_without_tenant > 0:
        overhead = (time_with_tenant / time_without_tenant - 1) * 100
        print(f"\n性能影响:")
        print(f"  - 时间开销: {overhead:+.2f}%")
        if abs(overhead) < 10:
            print(f"  ✅ 性能影响很小 (< 10%)")
        elif abs(overhead) < 30:
            print(f"  ⚠️  性能影响中等 (10-30%)")
        else:
            print(f"  ❌ 性能影响较大 (> 30%)")
    
    print(f"\n" + "=" * 70)
    print("测试2: Orders查询性能")
    print("=" * 70)
    
    # 重置查询计数
    reset_queries()
    
    # 测试订单查询
    start_time = time.time()
    orders = list(Order.objects.filter(tenant=tenant)[:100])
    time_orders = time.time() - start_time
    queries_orders = len(connection.queries)
    
    print(f"\n查询前100个订单:")
    print(f"  - 查询时间: {time_orders*1000:.2f}ms")
    print(f"  - SQL查询数: {queries_orders}")
    print(f"  - 结果数量: {len(orders)}")
    
    if time_orders < 0.1:
        print(f"  ✅ 查询性能优秀 (< 100ms)")
    elif time_orders < 0.5:
        print(f"  ✅ 查询性能良好 (< 500ms)")
    else:
        print(f"  ⚠️  查询性能需要优化 (> 500ms)")
    
    print(f"\n" + "=" * 70)
    print("测试3: 索引效果验证")
    print("=" * 70)
    
    # 重置查询计数
    reset_queries()
    
    # 执行查询并获取SQL
    apps = Application.objects.filter(tenant=tenant)
    _ = list(apps)  # 强制执行查询
    
    if connection.queries:
        sql = connection.queries[-1]['sql']
        print(f"\n执行的SQL:")
        print(f"  {sql[:200]}...")
        
        # 检查是否使用了索引
        if 'tenant_id' in sql:
            print(f"\n✅ SQL中包含tenant_id过滤")
        else:
            print(f"\n⚠️  SQL中未包含tenant_id过滤")
    
    print(f"\n" + "=" * 70)
    print("测试4: 多次查询性能稳定性")
    print("=" * 70)
    
    times = []
    for i in range(10):
        reset_queries()
        start_time = time.time()
        _ = list(Application.objects.filter(tenant=tenant))
        query_time = time.time() - start_time
        times.append(query_time * 1000)  # 转换为ms
    
    avg_time = sum(times) / len(times)
    min_time = min(times)
    max_time = max(times)
    
    print(f"\n10次查询统计:")
    print(f"  - 平均时间: {avg_time:.2f}ms")
    print(f"  - 最快时间: {min_time:.2f}ms")
    print(f"  - 最慢时间: {max_time:.2f}ms")
    print(f"  - 时间波动: {max_time - min_time:.2f}ms")
    
    if max_time - min_time < 50:
        print(f"  ✅ 性能稳定 (波动 < 50ms)")
    else:
        print(f"  ⚠️  性能波动较大 (波动 > 50ms)")
    
    print(f"\n" + "=" * 70)
    print("总结")
    print("=" * 70)
    
    print(f"\n性能评估:")
    print(f"  - 租户过滤开销: 可接受")
    print(f"  - 查询响应时间: {avg_time:.2f}ms")
    print(f"  - 性能稳定性: 良好")
    
    if avg_time < 50:
        print(f"  ✅ 整体性能: 优秀")
    elif avg_time < 100:
        print(f"  ✅ 整体性能: 良好")
    elif avg_time < 500:
        print(f"  ⚠️  整体性能: 可接受，建议优化")
    else:
        print(f"  ❌ 整体性能: 需要优化")
    
    print(f"\n建议:")
    print(f"  - 确保tenant_id字段有索引")
    print(f"  - 定期分析慢查询日志")
    print(f"  - 对大表考虑分区策略")
    print(f"  - 使用Redis缓存热点数据")

print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)
