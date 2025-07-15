"""
租户模型的Admin配置
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from tenants.models import Tenant, TenantQuota
from common.admin import TenantAdminMixin

# 添加调试信息
print("=== Running tenants/admin.py ===")

class TenantQuotaInline(admin.StackedInline):
    """
    在租户详情页面内嵌显示配额信息
    """
    model = TenantQuota
    can_delete = False
    verbose_name = _("配额")
    verbose_name_plural = _("配额")
    fields = (
        ('max_users', 'max_admins'), 
        ('max_storage_mb', 'current_storage_used_mb'),
        'max_products',
    )
    readonly_fields = ('current_storage_used_mb',)


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    """
    租户管理界面配置
    """
    list_display = ('name', 'code', 'status', 'contact_name', 'contact_phone', 
                    'user_count', 'storage_usage', 'customer_relations_count', 'created_at')
    list_filter = ('status', 'is_deleted', 'created_at')
    search_fields = ('name', 'code', 'contact_name', 'contact_email', 'contact_phone')
    readonly_fields = ('created_at', 'updated_at', 'customer_relations_display')
    inlines = (TenantQuotaInline,)
    
    fieldsets = (
        (_('基本信息'), {
            'fields': ('name', 'code', 'status', 'is_deleted')
        }),
        (_('联系人信息'), {
            'fields': ('contact_name', 'contact_email', 'contact_phone')
        }),
        (_('客户关系'), {
            'fields': ('customer_relations_display',),
        }),
        (_('时间信息'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_tenants', 'suspend_tenants', 'delete_tenants']
    
    def user_count(self, obj):
        """
        显示租户的用户数
        """
        # 避免循环导入
        from users.models import User
        count = User.objects.filter(tenant=obj).count()
        max_users = getattr(obj.quota, 'max_users', 0)
        
        if max_users > 0:
            percentage = (count / max_users) * 100
            if percentage >= 90:
                color = 'red'
            elif percentage >= 70:
                color = 'orange'
            else:
                color = 'green'
                
            return format_html(
                '<span style="color: {}">{} / {}</span>',
                color, count, max_users
            )
        return count
    
    user_count.short_description = _("用户数")
    
    def storage_usage(self, obj):
        """
        显示租户的存储使用情况
        """
        try:
            used = obj.quota.current_storage_used_mb
            total = obj.quota.max_storage_mb
            
            if total > 0:
                percentage = (used / total) * 100
                if percentage >= 90:
                    color = 'red'
                elif percentage >= 70:
                    color = 'orange'
                else:
                    color = 'green'
                    
                # 转换为更易读的格式
                if used >= 1024:
                    used_str = f"{used/1024:.1f} GB"
                else:
                    used_str = f"{used} MB"
                    
                if total >= 1024:
                    total_str = f"{total/1024:.1f} GB"
                else:
                    total_str = f"{total} MB"
                    
                return format_html(
                    '<span style="color: {}">{} / {} ({:.1f}%)</span>',
                    color, used_str, total_str, percentage
                )
            return f"{used} MB"
        except:
            return _("未设置")
    
    storage_usage.short_description = _("存储使用")
    
    def customer_relations_count(self, obj):
        """显示租户的客户关系数量"""
        count = obj.customer_relations.count()
        if count > 0:
            return format_html(
                '<a href="{}?tenant__id__exact={}">{}</a>',
                '/admin/customers/customertenantrelation/',
                obj.id,
                count
            )
        return count
    customer_relations_count.short_description = _('客户关系数')
    
    def customer_relations_display(self, obj):
        """在详情页显示租户的客户关系列表"""
        relations = obj.customer_relations.all()
        if not relations:
            return _('无客户关系')
        
        html = '<table style="width:100%"><tr><th>客户</th><th>关系类型</th><th>主要关系</th><th>合同编号</th><th>开始日期</th><th>结束日期</th></tr>'
        for relation in relations:
            html += f'<tr><td>{relation.customer.name}</td><td>{relation.get_relation_type_display()}</td><td>{"是" if relation.is_primary else "否"}</td><td>{relation.contract_number or "-"}</td><td>{relation.start_date or "-"}</td><td>{relation.end_date or "长期"}</td></tr>'
        html += '</table>'
        return format_html(html)
    customer_relations_display.short_description = _('客户关系')
    
    def activate_tenants(self, request, queryset):
        """
        批量激活租户
        """
        updated = queryset.update(status='active', is_deleted=False)
        self.message_user(request, _('成功激活 {} 个租户').format(updated))
    
    activate_tenants.short_description = _("激活选中的租户")
    
    def suspend_tenants(self, request, queryset):
        """
        批量暂停租户
        """
        updated = queryset.update(status='suspended')
        self.message_user(request, _('成功暂停 {} 个租户').format(updated))
    
    suspend_tenants.short_description = _("暂停选中的租户")
    
    def delete_tenants(self, request, queryset):
        """
        批量软删除租户
        """
        updated = queryset.update(status='deleted', is_deleted=True)
        self.message_user(request, _('成功删除 {} 个租户').format(updated))
    
    delete_tenants.short_description = _("删除选中的租户")


@admin.register(TenantQuota)
class TenantQuotaAdmin(TenantAdminMixin, admin.ModelAdmin):
    """
    租户配额模型的Admin配置
    每个租户只有一个配额记录，与租户是一对一关系
    """
    list_display = ('id', 'tenant', 'max_users', 'max_admins', 'max_storage_mb', 'current_storage_used_mb')
    list_filter = ('tenant__status',)
    search_fields = ('tenant__name',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('tenant',)
        }),
        (_('配额设置'), {
            'fields': ('max_users', 'max_admins', 'max_storage_mb', 'max_products')
        }),
        (_('使用情况'), {
            'fields': ('current_storage_used_mb',)
        }),
        (_('时间信息'), {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_queryset(self, request):
        """
        重写get_queryset，租户配额与租户是一对一关系
        需要特殊处理查询逻辑
        """
        qs = super(admin.ModelAdmin, self).get_queryset(request)
        
        # 超级管理员可以看到所有租户配额
        if request.user.is_superuser or getattr(request.user, 'is_super_admin', False):
            return qs
        
        # 普通用户只能看到自己所属租户的配额
        tenant = getattr(request.user, 'tenant', None)
        if tenant:
            return qs.filter(tenant=tenant)
        
        # 没有租户的用户看不到任何配额
        return qs.none()
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        重写formfield_for_foreignkey方法，限制租户选择
        对于租户字段，限制只能选择当前用户关联的租户（除非是超级管理员）
        """
        if db_field.name == 'tenant':
            # 超级管理员可以选择所有租户
            if request.user.is_superuser or getattr(request.user, 'is_super_admin', False):
                pass  # 不做限制，可以选择任何租户
            else:
                # 非超级管理员只能选择自己所属的租户
                tenant = getattr(request.user, 'tenant', None)
                if tenant:
                    kwargs["queryset"] = Tenant.objects.filter(id=tenant.id)
                else:
                    kwargs["queryset"] = Tenant.objects.none()
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def save_model(self, request, obj, form, change):
        """
        重写save_model方法，确保租户配额关联到正确的租户
        """
        # 如果是新建记录且没有指定租户
        if not change and not obj.tenant:
            # 非超级管理员用户，使用当前用户的租户
            if not (request.user.is_superuser or getattr(request.user, 'is_super_admin', False)):
                obj.tenant = getattr(request.user, 'tenant', None)
        
        super().save_model(request, obj, form, change)
    
    def has_add_permission(self, request):
        """
        控制添加权限：
        - 超级管理员可以添加任何租户的配额
        - 普通用户只能为自己所属的租户添加配额（如果尚不存在）
        """
        # 超级管理员始终可以添加
        if request.user.is_superuser or getattr(request.user, 'is_super_admin', False):
            return True
        
        # 获取当前用户关联的租户
        tenant = getattr(request.user, 'tenant', None)
        if not tenant:
            return False
        
        # 检查该租户是否已有配额记录
        has_quota = TenantQuota.objects.filter(tenant=tenant).exists()
        
        # 只有在租户没有配额记录的情况下才允许添加
        return not has_quota
        
    def has_change_permission(self, request, obj=None):
        """
        控制修改权限：
        - 超级管理员可以修改任何租户的配额
        - 普通用户只能修改自己所属租户的配额
        """
        # 超级管理员始终可以修改
        if request.user.is_superuser or getattr(request.user, 'is_super_admin', False):
            return True
        
        # 如果没有指定对象，返回通用权限
        if obj is None:
            return True
        
        # 获取当前用户关联的租户
        tenant = getattr(request.user, 'tenant', None)
        if not tenant:
            return False
        
        # 只能修改自己租户的配额
        return obj.tenant == tenant

# 添加调试信息
print("=== tenants/admin.py execution completed ===")
print(f"=== admin._registry contains Tenant model: {Tenant in admin.site._registry.keys()} ===")
print(f"=== admin._registry contains TenantQuota model: {TenantQuota in admin.site._registry.keys()} ===")
