from tenants.models import Tenant
from users.models import Member
from applications.models import Application

print("租户总数:", Tenant.objects.count())
print("用户总数:", Member.objects.count())
print("应用总数:", Application.objects.count())

if Tenant.objects.exists():
    t = Tenant.objects.first()
    print(f"\n第一个租户: {t.name} (ID: {t.id})")
    print(f"该租户的用户数: {Member.objects.filter(tenant=t).count()}")
    print(f"该租户的应用数: {Application.objects.filter(tenant=t).count()}")
