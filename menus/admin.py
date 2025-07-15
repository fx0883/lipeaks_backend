from django.contrib import admin
from .models import Menu, UserMenu

@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ('title', 'name', 'code', 'path', 'rank', 'parent', 'is_active', 'created_at')
    list_filter = ('is_active', 'show_link', 'show_parent', 'keep_alive')
    search_fields = ('title', 'name', 'code', 'path')
    list_editable = ('rank', 'is_active')
    ordering = ('rank',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('基本路由配置', {
            'fields': ('name', 'code', 'path', 'component', 'redirect', 'is_active')
        }),
        ('元数据配置', {
            'fields': (
                'title', 'icon', 'extra_icon', 'rank', 'show_link', 'show_parent',
                'roles', 'auths', 'keep_alive', 'active_path'
            )
        }),
        ('iframe配置', {
            'fields': ('frame_src', 'frame_loading'),
            'classes': ('collapse',)
        }),
        ('标签页配置', {
            'fields': ('hidden_tag', 'dynamic_level'),
            'classes': ('collapse',)
        }),
        ('动画配置', {
            'fields': ('transition_name', 'enter_transition', 'leave_transition'),
            'classes': ('collapse',)
        }),
        ('层级关系', {
            'fields': ('parent',)
        }),
        ('其他信息', {
            'fields': ('remarks', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(UserMenu)
class UserMenuAdmin(admin.ModelAdmin):
    list_display = ('user', 'menu', 'is_active', 'created_at')
    list_filter = ('user__is_admin', 'user__is_super_admin', 'is_active')
    search_fields = ('user__username', 'user__email', 'menu__title', 'menu__name')
    list_editable = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('user', 'menu')
    fieldsets = (
        ('关联信息', {
            'fields': ('user', 'menu', 'is_active')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
