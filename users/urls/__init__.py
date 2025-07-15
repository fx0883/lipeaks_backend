"""
用户相关URL路由包
"""
from django.urls import path, include

app_name = 'users'

urlpatterns = [
    # 认证相关URL
    path('auth/', include('users.urls.auth_urls', namespace='auth')),
    
    # 管理员用户相关URL
    path('admin-users/', include('users.urls.admin_user_urls', namespace='admin_users')),
    
    # 普通用户相关URL
    path('members/', include('users.urls.member_urls', namespace='members')),
    
    # 向后兼容的用户相关URL
    path('users/', include('users.urls.compat_urls', namespace='users')),
] 