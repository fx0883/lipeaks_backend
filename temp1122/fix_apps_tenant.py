from applications.models import Application
from tenants.models import Tenant

print("检查Applications表中没有tenant_id的记录...")

apps_no_tenant = Application.objects.filter(tenant__isnull=True)
count = apps_no_tenant.count()

print(f"找到 {count} 个没有tenant_id的应用:")
for app in apps_no_tenant:
    print(f"  - App {app.id}: {app.name} (app_code: {app.app_code})")

if count > 0:
    print("\n这些是旧数据，需要手动分配tenant。")
    print("由于无法确定它们属于哪个租户，建议:")
    print("1. 分配给第一个租户（作为默认）")
    print("2. 或者删除这些测试数据")
    print("\n提示: 在生产环境中应该手动检查并分配正确的租户")
