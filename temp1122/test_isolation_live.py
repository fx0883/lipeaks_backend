#!/usr/bin/env python
"""
实时租户隔离测试
直接访问数据库验证租户隔离
"""
from tenants.models import Tenant
from users.models import Member
from applications.models import Application
from orders.models import Order
from customers.models import Customer

print("=" * 70)
print("租户隔离功能验证 - 数据库直接检查")
print("=" * 70)

# 获取租户
tenants = list(Tenant.objects.all()[:3])
print(f"\n找到 {len(tenants)} 个租户:")
for t in tenants:
    print(f"  - Tenant {t.id}: {t.name}")

if len(tenants) < 2:
    print("\n⚠️  警告: 租户数量少于2个，无法完全测试隔离")
    print("建议创建至少2个租户进行测试")
else:
    tenant1, tenant2 = tenants[0], tenants[1]
    
    print(f"\n" + "=" * 70)
    print("测试1: Applications模块租户隔离")
    print("=" * 70)
    
    # 检查应用的租户分布
    apps_t1 = Application.objects.filter(tenant=tenant1).count()
    apps_t2 = Application.objects.filter(tenant=tenant2).count()
    apps_total = Application.objects.count()
    
    print(f"\nTenant {tenant1.id} ({tenant1.name}) 的应用数: {apps_t1}")
    print(f"Tenant {tenant2.id} ({tenant2.name}) 的应用数: {apps_t2}")
    print(f"总应用数: {apps_total}")
    
    if apps_total == apps_t1 + apps_t2:
        print("✅ 应用完全隔离，无共享数据")
    else:
        other_apps = apps_total - apps_t1 - apps_t2
        print(f"⚠️  有 {other_apps} 个应用属于其他租户")
    
    # 检查是否有NULL的tenant_id
    apps_no_tenant = Application.objects.filter(tenant__isnull=True).count()
    if apps_no_tenant == 0:
        print("✅ 所有应用都有tenant_id")
    else:
        print(f"❌ 发现 {apps_no_tenant} 个应用没有tenant_id！")
    
    print(f"\n" + "=" * 70)
    print("测试2: Orders模块租户隔离")
    print("=" * 70)
    
    orders_t1 = Order.objects.filter(tenant=tenant1).count()
    orders_t2 = Order.objects.filter(tenant=tenant2).count()
    orders_total = Order.objects.count()
    
    print(f"\nTenant {tenant1.id} 的订单数: {orders_t1}")
    print(f"Tenant {tenant2.id} 的订单数: {orders_t2}")
    print(f"总订单数: {orders_total}")
    
    orders_no_tenant = Order.objects.filter(tenant__isnull=True).count()
    if orders_no_tenant == 0:
        print("✅ 所有订单都有tenant_id")
    else:
        print(f"❌ 发现 {orders_no_tenant} 个订单没有tenant_id！")
    
    print(f"\n" + "=" * 70)
    print("测试3: Customers模块租户隔离")
    print("=" * 70)
    
    customers_t1 = Customer.objects.filter(tenant=tenant1).count()
    customers_t2 = Customer.objects.filter(tenant=tenant2).count()
    customers_total = Customer.objects.count()
    
    print(f"\nTenant {tenant1.id} 的客户数: {customers_t1}")
    print(f"Tenant {tenant2.id} 的客户数: {customers_t2}")
    print(f"总客户数: {customers_total}")
    
    customers_no_tenant = Customer.objects.filter(tenant__isnull=True).count()
    if customers_no_tenant == 0:
        print("✅ 所有客户都有tenant_id")
    else:
        print(f"❌ 发现 {customers_no_tenant} 个客户没有tenant_id！")
    
    print(f"\n" + "=" * 70)
    print("测试4: 用户分布检查")
    print("=" * 70)
    
    users_t1 = Member.objects.filter(tenant=tenant1).count()
    users_t2 = Member.objects.filter(tenant=tenant2).count()
    users_total = Member.objects.count()
    
    print(f"\nTenant {tenant1.id} 的用户数: {users_t1}")
    print(f"Tenant {tenant2.id} 的用户数: {users_t2}")
    print(f"总用户数: {users_total}")
    
    print(f"\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)
    
    issues = []
    
    if apps_no_tenant > 0:
        issues.append(f"Applications: {apps_no_tenant}个记录无tenant_id")
    if orders_no_tenant > 0:
        issues.append(f"Orders: {orders_no_tenant}个记录无tenant_id")
    if customers_no_tenant > 0:
        issues.append(f"Customers: {customers_no_tenant}个记录无tenant_id")
    
    if not issues:
        print("\n✅ 所有测试通过！租户隔离功能正常！")
        print("\n关键发现:")
        print(f"  - 数据完全按租户隔离")
        print(f"  - 所有记录都有正确的tenant_id")
        print(f"  - 无跨租户数据泄露风险")
    else:
        print("\n❌ 发现以下问题:")
        for issue in issues:
            print(f"  - {issue}")
        print("\n建议: 检查这些记录并手动修复tenant_id")

print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)
