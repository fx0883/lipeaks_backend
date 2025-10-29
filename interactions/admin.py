"""
用户互动Admin配置
"""
from django.contrib import admin
from .models import ArticleFavorite


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
