"""
用户互动Admin配置
"""
from django.contrib import admin
from .models import ArticleFavorite, MemberLike, MemberFollow, ArticleLike


@admin.register(ArticleFavorite)
class ArticleFavoriteAdmin(admin.ModelAdmin):
    """文章收藏Admin"""
    list_display = ['id', 'user', 'article', 'tenant', 'created_at']
    list_filter = ['created_at', 'tenant']
    search_fields = ['user__username', 'article__title']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']
    raw_id_fields = ['user', 'article', 'tenant']
    
    def get_queryset(self, request):
        """优化查询"""
        qs = super().get_queryset(request)
        return qs.select_related('user', 'article', 'tenant')


@admin.register(MemberLike)
class MemberLikeAdmin(admin.ModelAdmin):
    """用户点赞Admin"""
    list_display = ['id', 'from_member', 'to_member', 'tenant', 'created_at']
    list_filter = ['created_at', 'tenant']
    search_fields = ['from_member__username', 'to_member__username']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']
    raw_id_fields = ['from_member', 'to_member', 'tenant']
    
    def get_queryset(self, request):
        """优化查询"""
        qs = super().get_queryset(request)
        return qs.select_related('from_member', 'to_member', 'tenant')


@admin.register(MemberFollow)
class MemberFollowAdmin(admin.ModelAdmin):
    """用户关注Admin"""
    list_display = ['id', 'follower', 'following', 'tenant', 'created_at']
    list_filter = ['created_at', 'tenant']
    search_fields = ['follower__username', 'following__username']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']
    raw_id_fields = ['follower', 'following', 'tenant']
    
    def get_queryset(self, request):
        """优化查询"""
        qs = super().get_queryset(request)
        return qs.select_related('follower', 'following', 'tenant')


@admin.register(ArticleLike)
class ArticleLikeAdmin(admin.ModelAdmin):
    """文章点赞Admin"""
    list_display = ['id', 'from_member', 'article', 'tenant', 'created_at', 'ip_address']
    list_filter = ['created_at', 'tenant']
    search_fields = ['from_member__username', 'article__title', 'ip_address']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'ip_address', 'user_agent']
    raw_id_fields = ['from_member', 'article', 'tenant']
    
    def get_queryset(self, request):
        """优化查询"""
        qs = super().get_queryset(request)
        return qs.select_related('from_member', 'article', 'tenant')
