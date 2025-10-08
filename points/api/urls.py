# points/api/urls.py
"""
多租户积分系统的API路由配置
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from points.api.views import (
    UserLevelViewSet, UserTypeTagViewSet, TenantUserProfileViewSet,
    TenantUserPointsViewSet, TenantUserTypeTagViewSet, PointsStatisticsViewSet
)

# 创建API路由器
router = DefaultRouter()

# 注册视图集
router.register(r'user-levels', UserLevelViewSet, basename='user-levels')
router.register(r'user-type-tags', UserTypeTagViewSet, basename='user-type-tags')
router.register(r'profiles', TenantUserProfileViewSet, basename='tenant-user-profiles')
router.register(r'points-records', TenantUserPointsViewSet, basename='tenant-user-points')
router.register(r'vip-tags', TenantUserTypeTagViewSet, basename='tenant-user-type-tags')
router.register(r'statistics', PointsStatisticsViewSet, basename='points-statistics')

# URL模式
urlpatterns = [
    # API路由
    path('', include(router.urls)),
    
    # 自定义端点（如果需要）
    # path('custom-endpoint/', custom_view, name='custom-endpoint'),
]

# 为API文档添加应用名称
app_name = 'points-api'
