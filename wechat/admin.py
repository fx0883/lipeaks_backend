"""
微信用户管理后台配置
"""
from django.contrib import admin
from wechat.models import WechatUser


@admin.register(WechatUser)
class WechatUserAdmin(admin.ModelAdmin):
    """微信用户管理"""
    list_display = ['id', 'member', 'openid_short', 'nickname', 'created_at', 'updated_at']
    list_filter = ['created_at']
    search_fields = ['openid', 'unionid', 'nickname', 'member__username']
    readonly_fields = ['openid', 'unionid', 'session_key', 'created_at', 'updated_at']
    raw_id_fields = ['member']
    
    def openid_short(self, obj):
        """显示缩略的 openid"""
        return f"{obj.openid[:8]}..." if obj.openid else '-'
    openid_short.short_description = 'OpenID'
