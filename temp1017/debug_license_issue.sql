-- 诊断许可证 7 的问题
-- 请在 Django shell 中运行以下代码，或在数据库中运行相应的 SQL

-- 方法 1: Django Shell (推荐)
-- 在项目根目录运行: python manage.py shell

-- 复制以下代码到 shell:
"""
from licenses.models import LicenseAssignment, License
from users.models import Member

# 查找用户
member = Member.objects.get(id=1, username='fx0883')
print(f"用户信息: ID={member.id}, 用户名={member.username}, 租户ID={member.tenant_id if member.tenant else None}")

# 查找许可证
try:
    license_obj = License.objects.get(id=7)
    print(f"\n许可证信息: ID={license_obj.id}, 产品={license_obj.product.name}, 租户ID={license_obj.tenant_id if hasattr(license_obj, 'tenant') else 'N/A'}")
except License.DoesNotExist:
    print("\n❌ 许可证 7 不存在")

# 查找所有与许可证 7 相关的分配记录
print("\n=== 许可证 7 的所有分配记录 ===")
assignments = LicenseAssignment.objects.filter(license_id=7).select_related('member', 'tenant')
if assignments.exists():
    for assignment in assignments:
        print(f"  - ID: {assignment.id}")
        print(f"    Member ID: {assignment.member_id} (用户名: {assignment.member.username})")
        print(f"    Tenant ID: {assignment.tenant_id}")
        print(f"    Status: {assignment.status}")
        print(f"    Created: {assignment.created_at}")
        print(f"    Expires: {assignment.expires_at}")
        print()
else:
    print("  ❌ 没有找到任何分配记录")

# 查找用户 1 的所有分配记录
print("\n=== 用户 fx0883 的所有许可证分配 ===")
user_assignments = LicenseAssignment.objects.filter(member_id=1).select_related('license')
for assignment in user_assignments:
    print(f"  - License ID: {assignment.license_id}")
    print(f"    Status: {assignment.status}")
    print(f"    Tenant ID: {assignment.tenant_id}")
    print(f"    Product: {assignment.license.product.name}")
    print()

# 检查具体的查询条件
print("\n=== 检查查询条件 ===")
target_assignment = LicenseAssignment.objects.filter(
    member=member,
    license_id=7,
    status='active',
    tenant=member.tenant
).first()

if target_assignment:
    print("✅ 找到了符合所有条件的分配记录")
    print(f"   Assignment ID: {target_assignment.id}")
else:
    print("❌ 没有找到符合所有条件的分配记录")
    print("\n正在逐个检查条件...")
    
    # 检查 member 条件
    check1 = LicenseAssignment.objects.filter(member=member, license_id=7).first()
    print(f"  member=用户1 AND license_id=7: {'✅ 有记录' if check1 else '❌ 无记录'}")
    if check1:
        print(f"    - Status: {check1.status} (需要: active)")
        print(f"    - Tenant ID: {check1.tenant_id} (需要: {member.tenant_id if member.tenant else None})")
    
    # 检查 status 条件
    check2 = LicenseAssignment.objects.filter(member=member, license_id=7, status='active').first()
    print(f"  member=用户1 AND license_id=7 AND status='active': {'✅ 有记录' if check2 else '❌ 无记录'}")
    if check2 and member.tenant:
        print(f"    - Tenant ID: {check2.tenant_id} (需要: {member.tenant_id})")
    
    # 检查 tenant 条件
    if member.tenant:
        check3 = LicenseAssignment.objects.filter(member=member, license_id=7, tenant=member.tenant).first()
        print(f"  member=用户1 AND license_id=7 AND tenant=租户{member.tenant_id}: {'✅ 有记录' if check3 else '❌ 无记录'}")
        if check3:
            print(f"    - Status: {check3.status} (需要: active)")
"""

-- 方法 2: 直接 SQL 查询 (如果使用 PostgreSQL/MySQL)
-- 查看许可证 7 的分配情况
SELECT 
    la.id AS assignment_id,
    la.member_id,
    la.license_id,
    la.tenant_id,
    la.status,
    la.created_at,
    la.expires_at,
    m.username,
    l.license_key,
    sp.name AS product_name
FROM licenses_licenseassignment la
LEFT JOIN users_member m ON la.member_id = m.id
LEFT JOIN licenses_license l ON la.license_id = l.id
LEFT JOIN licenses_softwareproduct sp ON l.product_id = sp.id
WHERE la.license_id = 7;

-- 查看用户 1 的租户信息
SELECT id, username, tenant_id, is_active, status
FROM users_member
WHERE id = 1;

-- 查看用户 1 的所有许可证
SELECT 
    la.id AS assignment_id,
    la.license_id,
    la.status,
    la.tenant_id,
    sp.name AS product_name,
    la.expires_at
FROM licenses_licenseassignment la
LEFT JOIN licenses_license l ON la.license_id = l.id
LEFT JOIN licenses_softwareproduct sp ON l.product_id = sp.id
WHERE la.member_id = 1
ORDER BY la.created_at DESC;
