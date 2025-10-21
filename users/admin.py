"""
用户模型的Admin配置
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _
from users.models import User, Member, PasswordResetToken
from common.admin import TenantAdminMixin

# 添加调试信息
print("=== Running users/admin.py ===")

@admin.register(User)
class UserAdmin(TenantAdminMixin, DjangoUserAdmin):
    """
    管理员用户模型的Admin配置
    """
    list_display = ('id', 'username', 'email', 'display_role', 'is_active', 'tenant', 'date_joined')
    list_filter = ('is_active', 'is_super_admin', 'tenant__name', 'status')
    search_fields = ('username', 'email', 'nick_name', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('个人信息'), {'fields': ('first_name', 'last_name', 'email', 'phone', 'nick_name', 'avatar', 'wechat_id')}),
        (_('权限'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'is_super_admin', 
                     'groups', 'user_permissions'),
        }),
        (_('租户信息'), {'fields': ('tenant', 'status', 'is_deleted')}),
        (_('重要日期'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'tenant'),
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """
        重写保存方法，处理特殊情况：
        - 超级管理员不需要关联租户
        - 普通用户保存时自动关联current用户的租户（如果没有指定）
        """
        # 如果是超级管理员，清除租户关联
        if obj.is_super_admin and obj.tenant:
            obj.tenant = None
        
        # 如果非超级管理员没有指定租户，使用current用户的租户
        if not obj.is_super_admin and not obj.tenant:
            obj.tenant = getattr(request.user, 'tenant', None)
        
        super().save_model(request, obj, form, change)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        重写formfield_for_foreignkey方法，过滤租户选项
        """
        if db_field.name == "tenant":
            # 超级管理员可以选择所有租户
            if request.user.is_superuser or getattr(request.user, 'is_super_admin', False):
                pass  # 不做过滤
            else:
                # 非超级管理员只能选择自己所属的租户
                tenant = getattr(request.user, 'tenant', None)
                if tenant:
                    kwargs["queryset"] = db_field.related_model.objects.filter(id=tenant.id)
                else:
                    kwargs["queryset"] = db_field.related_model.objects.none()
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def display_role(self, obj):
        """
        显示用户角色
        """
        return obj.display_role
    display_role.short_description = _('角色')

@admin.register(Member)
class MemberAdmin(TenantAdminMixin, DjangoUserAdmin):
    """
    普通成员模型的Admin配置
    """
    list_display = ('id', 'username', 'email', 'display_role', 'is_active', 'tenant', 'parent', 'date_joined')
    list_filter = ('is_active', 'tenant__name', 'status', 'parent')
    search_fields = ('username', 'email', 'nick_name', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('个人信息'), {'fields': ('first_name', 'last_name', 'email', 'phone', 'nick_name', 'avatar', 'wechat_id')}),
        (_('权限'), {
            'fields': ('is_active', 'groups', 'user_permissions'),
        }),
        (_('租户和账号关系'), {'fields': ('tenant', 'status', 'is_deleted', 'parent')}),
        (_('重要日期'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'tenant', 'parent'),
        }),
    )
    
    def save_model(self, request, obj, form, change):
        """
        重写保存方法，处理特殊情况：
        - 普通成员保存时自动关联current用户的租户（如果没有指定）
        """
        # 如果没有指定租户，使用current用户的租户
        if not obj.tenant:
            obj.tenant = getattr(request.user, 'tenant', None)
        
        super().save_model(request, obj, form, change)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        重写formfield_for_foreignkey方法，过滤租户和父账号选项
        """
        if db_field.name == "tenant":
            # 超级管理员可以选择所有租户
            if request.user.is_superuser or getattr(request.user, 'is_super_admin', False):
                pass  # 不做过滤
            else:
                # 非超级管理员只能选择自己所属的租户
                tenant = getattr(request.user, 'tenant', None)
                if tenant:
                    kwargs["queryset"] = db_field.related_model.objects.filter(id=tenant.id)
                else:
                    kwargs["queryset"] = db_field.related_model.objects.none()
        elif db_field.name == "parent":
            # 过滤父账号选项，只显示同一租户下的普通成员（非子账号）
            tenant = getattr(request.user, 'tenant', None)
            if tenant:
                kwargs["queryset"] = Member.objects.filter(
                    tenant=tenant,
                    parent__isnull=True,
                    is_deleted=False
                )
            else:
                # 超级管理员可以选择所有非子账号的成员作为父账号
                kwargs["queryset"] = Member.objects.filter(
                    parent__isnull=True,
                    is_deleted=False
                )
        
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def display_role(self, obj):
        """
        显示用户角色
        """
        return obj.display_role
    display_role.short_description = _('角色')

@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    """
    密码重置令牌管理
    """
    list_display = ('user', 'token', 'created_at', 'expires_at', 'is_used', 'is_expired')
    list_filter = ('is_used', 'created_at')
    search_fields = ('user__username', 'user__email', 'token')
    readonly_fields = ('token', 'created_at')
    
    def is_expired(self, obj):
        """
        检查令牌是否已过期
        """
        return obj.is_expired()
    is_expired.boolean = True
    is_expired.short_description = "是否过期"

# 添加调试信息
print("=== users/admin.py execution completed ===")
print(f"=== admin._registry contains User model: {User in admin.site._registry.keys()} ===")
print(f"=== admin._registry contains Member model: {Member in admin.site._registry.keys()} ===")
