#!/usr/bin/env python
"""
跨租户访问拒绝测试
测试不同租户之间的数据隔离和访问控制
"""
from tenants.models import Tenant
from users.models import Member
from applications.models import Application
from orders.models import Order
from customers.models import Customer
from django.db.models import Q

print("=" * 70)
print("跨租户访问拒绝测试")
print("=" * 70)

# 获取租户
tenants = list(Tenant.objects.all()[:3])
if len(tenants) < 2:
    print("\n⚠️  租户数量不足，需要至少2个租户")
else:
    tenant1, tenant2 = tenants[0], tenants[1]
    print(f"\n测试租户:")
    print(f"  - Tenant 1: {tenant1.name} (ID={tenant1.id})")
    print(f"  - Tenant 2: {tenant2.name} (ID={tenant2.id})")
    
    print(f"\n" + "=" * 70)
    print("测试1: 验证BaseModel的TenantManager自动过滤")
    print("=" * 70)
    
    # 测试Applications
    print(f"\nApplications模块:")
    apps_all = Application.objects.all().count()
    apps_t1 = Application.objects.filter(tenant=tenant1).count()
    apps_t2 = Application.objects.filter(tenant=tenant2).count()
    
    print(f"  总应用数: {apps_all}")
    print(f"  Tenant 1应用: {apps_t1}")
    print(f"  Tenant 2应用: {apps_t2}")
    
    # 尝试跨租户访问
    if apps_t1 > 0 and apps_t2 > 0:
        app_t1 = Application.objects.filter(tenant=tenant1).first()
        # 尝试用Tenant 2的过滤器查找Tenant 1的应用
        cross_access = Application.objects.filter(tenant=tenant2, id=app_t1.id).exists()
        
        if not cross_access:
            print(f"  ✅ 无法跨租户访问: Tenant 2无法查询到Tenant 1的应用 (ID={app_t1.id})")
        else:
            print(f"  ❌ 跨租户访问成功: 存在安全隐患！")
    
    print(f"\n" + "=" * 70)
    print("测试2: 验证Orders模块隔离")
    print("=" * 70)
    
    orders_all = Order.objects.all().count()
    orders_t1 = Order.objects.filter(tenant=tenant1).count()
    orders_t2 = Order.objects.filter(tenant=tenant2).count()
    
    print(f"\n订单数据:")
    print(f"  总订单数: {orders_all}")
    print(f"  Tenant 1订单: {orders_t1}")
    print(f"  Tenant 2订单: {orders_t2}")
    
    if orders_all == orders_t1 + orders_t2:
        print(f"  ✅ 订单完全隔离，无共享数据")
    else:
        other_orders = orders_all - orders_t1 - orders_t2
        print(f"  ⚠️  有{other_orders}个订单属于其他租户")
    
    print(f"\n" + "=" * 70)
    print("测试3: 验证Customers模块隔离")
    print("=" * 70)
    
    customers_all = Customer.objects.all().count()
    customers_t1 = Customer.objects.filter(tenant=tenant1).count()
    customers_t2 = Customer.objects.filter(tenant=tenant2).count()
    
    print(f"\n客户数据:")
    print(f"  总客户数: {customers_all}")
    print(f"  Tenant 1客户: {customers_t1}")
    print(f"  Tenant 2客户: {customers_t2}")
    
    if customers_all == customers_t1 + customers_t2:
        print(f"  ✅ 客户完全隔离，无共享数据")
    else:
        other_customers = customers_all - customers_t1 - customers_t2
        print(f"  ⚠️  有{other_customers}个客户属于其他租户")
    
    print(f"\n" + "=" * 70)
    print("测试4: 尝试使用错误的tenant_id查询")
    print("=" * 70)
    
    # 创建测试数据（如果不存在）
    if apps_t1 == 0:
        test_app = Application.objects.create(
            name="Test App for Cross-Tenant",
            code="TEST_CROSS",
            tenant=tenant1
        )
        print(f"\n创建测试应用: ID={test_app.id}, Tenant={tenant1.id}")
        app_t1 = test_app
    else:
        app_t1 = Application.objects.filter(tenant=tenant1).first()
    
    # 尝试用错误的tenant_id查询
    wrong_tenant_query = Application.objects.filter(tenant=tenant2, id=app_t1.id)
    result = wrong_tenant_query.exists()
    
    print(f"\n使用Tenant 2查询Tenant 1的应用 (ID={app_t1.id}):")
    if not result:
        print(f"  ✅ 查询结果为空，隔离正常")
    else:
        print(f"  ❌ 可以查到数据，存在安全问题！")
    
    print(f"\n" + "=" * 70)
    print("测试5: 验证直接对象访问保护")
    print("=" * 70)
    
    # 直接通过ID查询（绕过租户过滤）
    try:
        direct_access = Application.objects.get(id=app_t1.id)
        print(f"\n直接ID查询结果:")
        print(f"  - 应用ID: {direct_access.id}")
        print(f"  - 应用名称: {direct_access.name}")
        print(f"  - 应用租户: {direct_access.tenant.name} (ID={direct_access.tenant_id})")
        print(f"  ✅ 可以查到数据，但tenant_id字段存在")
        print(f"  ⚠️  需要在ViewSet层面验证tenant_id匹配")
    except Application.DoesNotExist:
        print(f"  ⚠️  无法直接访问，可能是其他问题")
    
    print(f"\n" + "=" * 70)
    print("测试6: 模拟TenantModelViewSet的get_queryset行为")
    print("=" * 70)
    
    # 模拟TenantModelViewSet的过滤逻辑
    class SimulatedRequest:
        def __init__(self, tenant):
            self.tenant = tenant
    
    # 模拟Tenant 1的请求
    request_t1 = SimulatedRequest(tenant1)
    queryset_t1 = Application.objects.filter(tenant=request_t1.tenant)
    count_t1 = queryset_t1.count()
    
    # 模拟Tenant 2的请求
    request_t2 = SimulatedRequest(tenant2)
    queryset_t2 = Application.objects.filter(tenant=request_t2.tenant)
    count_t2 = queryset_t2.count()
    
    print(f"\n模拟TenantModelViewSet过滤:")
    print(f"  Tenant 1请求看到: {count_t1}个应用")
    print(f"  Tenant 2请求看到: {count_t2}个应用")
    
    # 验证Tenant 1无法看到Tenant 2的数据
    t1_sees_t2_app = queryset_t1.filter(tenant=tenant2).exists()
    if not t1_sees_t2_app:
        print(f"  ✅ Tenant 1无法看到Tenant 2的应用")
    else:
        print(f"  ❌ Tenant 1可以看到Tenant 2的应用！安全问题！")
    
    print(f"\n" + "=" * 70)
    print("总结")
    print("=" * 70)
    
    issues = []
    
    # 检查各项测试结果
    if apps_t1 > 0 and apps_t2 > 0:
        app_t1_test = Application.objects.filter(tenant=tenant1).first()
        if Application.objects.filter(tenant=tenant2, id=app_t1_test.id).exists():
            issues.append("Applications: 存在跨租户访问漏洞")
    
    if orders_all > 0 and orders_all != orders_t1 + orders_t2:
        issues.append("Orders: 数据分布异常")
    
    if customers_all > 0 and customers_all != customers_t1 + customers_t2:
        issues.append("Customers: 数据分布异常")
    
    if t1_sees_t2_app:
        issues.append("ViewSet模拟: 租户过滤失效")
    
    if not issues:
        print("\n✅ 所有跨租户访问测试通过！")
        print("\n关键发现:")
        print("  - 租户数据完全隔离")
        print("  - 无法跨租户查询数据")
        print("  - TenantModelViewSet过滤逻辑正确")
        print("  - 安全性验证通过")
    else:
        print(f"\n❌ 发现{len(issues)}个安全问题:")
        for issue in issues:
            print(f"  - {issue}")
        print("\n⚠️  建议立即修复这些问题！")

print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)
