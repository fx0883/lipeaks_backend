"""
手动导入所有应用的admin模块，确保模型被注册到admin站点
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _

# 自定义Admin站点标题和header
admin.site.site_header = _('多租户用户管理系统')
admin.site.site_title = _('多租户用户管理系统')
admin.site.index_title = _('站点管理')

# 输出已注册的模型
print("=== Models in admin._registry before import ===")
for model, model_admin in admin.site._registry.items():
    print(f"{model._meta.app_label}.{model._meta.model_name}: {model_admin.__class__.__name__}")

# 导入模型
print("=== Trying to import and register models directly ===")
try:
    # 导入users模型
    from users.models import User
    
    # 导入tenants模型
    from tenants.models import Tenant, TenantQuota
    
    # 导入common模型
    from common.models import APILog, Config
    
    # 如果模型不在admin._registry中，重新注册
    from django.contrib.auth.admin import UserAdmin
    if User not in admin.site._registry:
        print("Manually registering User model to admin")
        admin.site.register(User, UserAdmin)
    
    if Tenant not in admin.site._registry:
        print("Manually registering Tenant model to admin")
        admin.site.register(Tenant)
    
    if TenantQuota not in admin.site._registry:
        print("Manually registering TenantQuota model to admin")
        admin.site.register(TenantQuota)
    
    # 确保Config模型被注册到admin
    if Config not in admin.site._registry:
        print("Manually registering Config model to admin")
        
        class ConfigAdmin(admin.ModelAdmin):
            """
            系统配置的Admin配置
            """
            list_display = ('name', 'key', 'type', 'is_active', 'created_at', 'updated_at')
            list_filter = ('type', 'is_active', 'created_at', 'updated_at')
            search_fields = ('name', 'key', 'description')
            readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
            fieldsets = (
                (None, {
                    'fields': ('name', 'key', 'type', 'is_active')
                }),
                (_('配置内容'), {
                    'fields': ('value', 'description')
                }),
                (_('审计信息'), {
                    'fields': ('created_by', 'created_at', 'updated_by', 'updated_at')
                }),
            )
            
            def save_model(self, request, obj, form, change):
                """
                重写save_model方法，自动设置创建人和更新人
                """
                if not change:
                    obj.created_by = request.user
                obj.updated_by = request.user
                super().save_model(request, obj, form, change)
            
            def has_delete_permission(self, request, obj=None):
                """
                只允许超级管理员删除配置
                """
                return request.user.is_superuser or getattr(request.user, 'is_super_admin', False)
        
        admin.site.register(Config, ConfigAdmin)
    
    # 输出注册后的模型
    print("=== Models in admin._registry after import and registration ===")
    for model, model_admin in admin.site._registry.items():
        print(f"{model._meta.app_label}.{model._meta.model_name}: {model_admin.__class__.__name__}")
        
except Exception as e:
    print(f"Error registering models: {e}") 