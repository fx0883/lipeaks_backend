"""
兼容性URL配置，用于保持与旧版API的向后兼容性
"""
from django.urls import path
from users.views import user_views

app_name = 'users'

urlpatterns = [
    # 角色管理
    path('role/<int:pk>/update/', user_views.UserRoleUpdateView.as_view(), name='user-role-update'),
] 