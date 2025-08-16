"""
测试Check_System租户过滤功能
"""
import os
import sys
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from check_system.models import TaskCategory, Task, TaskTemplate
from tenants.models import Tenant
from users.models import User

def test_check_system_tenant_filter():
    """
    测试Check_System租户过滤功能
    """
    print("=== 测试Check_System租户过滤功能 ===")
    
    # 获取所有租户
    tenants = Tenant.objects.filter(is_deleted=False).order_by('name')
    print(f"系统中的租户数量: {tenants.count()}")
    
    for tenant in tenants:
        print(f"\n--- 租户: {tenant.name} (ID: {tenant.id}) ---")
        
        # 测试TaskCategory
        categories = TaskCategory.objects.filter(tenant=tenant)
        print(f"  打卡类型数量: {categories.count()}")
        for category in categories[:3]:  # 只显示前3个
            print(f"    - {category.name}")
        
        # 测试Task
        tasks = Task.objects.filter(tenant=tenant)
        print(f"  打卡任务数量: {tasks.count()}")
        for task in tasks[:3]:  # 只显示前3个
            print(f"    - {task.name} ({task.get_status_display()})")
        
        # 测试TaskTemplate
        templates = TaskTemplate.objects.filter(tenant=tenant)
        print(f"  任务模板数量: {templates.count()}")
        for template in templates[:3]:  # 只显示前3个
            print(f"    - {template.name}")
    
    # 测试超级管理员可以看到所有租户的数据
    print("\n=== 测试超级管理员权限 ===")
    all_categories = TaskCategory.objects.all()
    all_tasks = Task.objects.all()
    all_templates = TaskTemplate.objects.all()
    
    print(f"超级管理员可以看到:")
    print(f"  - 所有打卡类型: {all_categories.count()}")
    print(f"  - 所有打卡任务: {all_tasks.count()}")
    print(f"  - 所有任务模板: {all_templates.count()}")
    
    # 测试普通用户只能看到自己租户的数据
    print("\n=== 测试普通用户权限 ===")
    # 获取第一个有租户的用户
    user_with_tenant = User.objects.filter(tenant__isnull=False).first()
    if user_with_tenant:
        print(f"测试用户: {user_with_tenant.username} (租户: {user_with_tenant.tenant.name})")
        
        user_categories = TaskCategory.objects.filter(tenant=user_with_tenant.tenant)
        user_tasks = Task.objects.filter(tenant=user_with_tenant.tenant)
        user_templates = TaskTemplate.objects.filter(tenant=user_with_tenant.tenant)
        
        print(f"  用户只能看到:")
        print(f"    - 打卡类型: {user_categories.count()}")
        print(f"    - 打卡任务: {user_tasks.count()}")
        print(f"    - 任务模板: {user_templates.count()}")
    else:
        print("没有找到关联租户的用户")
    
    print("\n=== 测试完成 ===")

if __name__ == '__main__':
    test_check_system_tenant_filter()
