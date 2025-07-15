"""
RBAC URL路由配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    PermissionViewSet,
    RoleViewSet,
    UserRoleViewSet,
    UserRolesViewSet,
    UserRoleDetailViewSet,
    UserPermissionsViewSet,
    CacheRefreshViewSet,
    UserCacheRefreshViewSet,
    TenantRolesViewSet
)

app_name = 'rbac'

# 创建权限和角色的路由
router = DefaultRouter()
router.register(r'permissions', PermissionViewSet, basename='permission')
router.register(r'roles', RoleViewSet, basename='role')
router.register(r'user-roles', UserRoleViewSet, basename='user-role')

urlpatterns = [
    # API路由前缀为 /api/v1/rbac/
    # 基本API路由
    path('', include(router.urls)),
    
    # 用户角色管理
    path('users/<str:user_type>/<int:user_id>/roles/', UserRolesViewSet.as_view({
        'get': 'list',
        'post': 'create',
    }), name='user-roles'),
    path('users/<str:user_type>/<int:user_id>/roles/<int:role_id>/', UserRoleDetailViewSet.as_view({
        'get': 'retrieve',
        'put': 'update',
        'patch': 'partial_update',
        'delete': 'destroy',
    }), name='user-role-detail'),
    
    # 获取用户权限
    path('users/<str:user_type>/<int:user_id>/permissions/', UserPermissionsViewSet.as_view({
        'get': 'list',
    }), name='user-permissions'),
    
    # 权限缓存管理
    path('cache/refresh/', CacheRefreshViewSet.as_view({
        'post': 'create',
    }), name='cache-refresh'),
    path('cache/refresh/user/<str:user_type>/<int:user_id>/', UserCacheRefreshViewSet.as_view({
        'post': 'create',
    }), name='user-cache-refresh'),
    
    # 租户权限管理
    path('tenants/<int:tenant_id>/roles/', TenantRolesViewSet.as_view({
        'get': 'list',
    }), name='tenant-roles'),
    path('tenants/<int:tenant_id>/roles/from-template/', TenantRolesViewSet.as_view({
        'post': 'create_from_template',
    }), name='tenant-role-from-template'),
] 