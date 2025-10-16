"""
管理员用户(User)相关URL配置
"""
from django.urls import path
from users.views import admin_user_views

app_name = 'admin_users'

urlpatterns = [
    # 管理员用户管理
    path('', admin_user_views.AdminUserListCreateView.as_view(), name='admin-user-list-create'),
    path('<int:pk>/', admin_user_views.AdminUserRetrieveUpdateDeleteView.as_view(), name='admin-user-detail'),
    
    # current登录的管理员用户操作
    path('me/', admin_user_views.CurrentAdminUserView.as_view(), name='current-admin-user'),
    path('me/password/', admin_user_views.AdminPasswordUpdateView.as_view(), name='admin-user-password-update'),
    
    # 超级管理员操作
    path('<int:pk>/grant-super-admin/', admin_user_views.GrantSuperAdminView.as_view(), name='grant-super-admin'),
    path('<int:pk>/revoke-super-admin/', admin_user_views.RevokeSuperAdminView.as_view(), name='revoke-super-admin'),
    path('super-admin/create/', admin_user_views.SuperAdminCreateView.as_view(), name='super-admin-create'),
    
    # 头像上传
    path('avatar/upload/', admin_user_views.AdminUserAvatarUploadView.as_view(), name='admin-user-avatar-upload'),
    path('<int:pk>/avatar/upload/', admin_user_views.AdminUserSpecificAvatarUploadView.as_view(), name='admin-user-specific-avatar-upload'),
    
    # 管理员状态控制
    path('<int:pk>/deactivate/', admin_user_views.DeactivateAdminUserView.as_view(), name='admin-user-deactivate'),
    path('<int:pk>/activate/', admin_user_views.ActivateAdminUserView.as_view(), name='admin-user-activate'),
] 