"""
CMS系统URL配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ArticleViewSet, CategoryViewSet, TagViewSet, 
    CommentViewSet, TagGroupViewSet
)

# 设置应用命名空间
app_name = 'cms'

# 创建路由器并注册视图集
router = DefaultRouter()
router.register(r'articles', ArticleViewSet, basename='article')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'tag-groups', TagGroupViewSet, basename='tag-group')
router.register(r'comments', CommentViewSet, basename='comment')

# API URLs
urlpatterns = [
    path('', include(router.urls)),
    # 添加专门的分类树API路由
    path('categories/tree/', CategoryViewSet.as_view({'get': 'get_category_tree'}), name='category-tree'),
] 