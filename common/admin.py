"""
通用应用的Admin配置
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from common.models import APILog, Config
from common.utils.tenant_manager import get_current_tenant

class TenantAdminMixin:
    """
    租户Admin混入类，用于实现租户隔离
    所有需要租户隔离的ModelAdmin都应该继承这个类
    """
    
    def get_queryset(self, request):
        """
        重写get_queryset方法，根据用户权限过滤查询集
        - 超级管理员可以看到所有数据
        - 其他用户只能看到关联租户的数据
        """
        qs = super().get_queryset(request)
        
        # 如果用户是超级管理员，返回所有数据
        if request.user.is_superuser or getattr(request.user, 'is_super_admin', False):
            return qs
        
        # 获取用户关联的租户
        tenant = getattr(request.user, 'tenant', None)
        if tenant:
            # 如果有租户字段，按租户过滤
            if hasattr(qs.model, 'tenant'):
                return qs.filter(tenant=tenant)
        
        # 如果用户没有关联租户或模型没有租户字段，则不显示任何数据
        return qs.none()
    
    def save_model(self, request, obj, form, change):
        """
        重写save_model方法，自动设置租户
        """
        # 如果是新对象且模型有租户字段，则设置当前用户的租户
        if not change and hasattr(obj, 'tenant') and obj.tenant is None:
            obj.tenant = getattr(request.user, 'tenant', None)
        
        super().save_model(request, obj, form, change)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        重写formfield_for_foreignkey方法，过滤外键选项
        对于租户相关的外键字段，只显示当前租户的数据
        """
        # 获取用户关联的租户
        tenant = getattr(request.user, 'tenant', None)
        
        # 如果用户不是超级管理员，且有租户关联
        if not (request.user.is_superuser or getattr(request.user, 'is_super_admin', False)) and tenant:
            # 检查外键的目标模型是否有tenant字段
            related_model = db_field.related_model
            if hasattr(related_model, 'tenant'):
                kwargs["queryset"] = related_model.objects.filter(tenant=tenant)
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(APILog)
class APILogAdmin(TenantAdminMixin, admin.ModelAdmin):
    """
    API日志的Admin配置
    """
    list_display = ('id', 'request_method', 'request_path', 'status_code', 'user', 'tenant', 'response_time', 'created_at')
    list_filter = ('request_method', 'status_code', 'status_type', 'created_at', 'tenant')
    search_fields = ('request_path', 'ip_address', 'user__username', 'tenant__name')
    readonly_fields = (
        'user', 'tenant', 'ip_address', 'request_method', 'request_path', 
        'query_params', 'request_body', 'status_code', 'response_time', 
        'status_type', 'error_message', 'user_agent', 'created_at'
    )
    fieldsets = (
        (None, {
            'fields': ('user', 'tenant', 'ip_address')
        }),
        (_('请求信息'), {
            'fields': ('request_method', 'request_path', 'query_params', 'request_body', 'user_agent')
        }),
        (_('响应信息'), {
            'fields': ('status_code', 'status_type', 'response_time', 'error_message')
        }),
        (_('时间信息'), {
            'fields': ('created_at',)
        }),
    )
    
    def has_add_permission(self, request):
        """
        禁止手动添加日志记录
        """
        return False
    
    def has_change_permission(self, request, obj=None):
        """
        禁止修改日志记录
        """
        return False

@admin.register(Config)
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
