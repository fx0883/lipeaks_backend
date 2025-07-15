"""
认证相关的URL路由
"""
from django.urls import path
from users.views import auth_views

app_name = 'auth'

urlpatterns = [
    # 注册
    path('register/', auth_views.RegisterView.as_view(), name='register'),
    
    # 登录
    path('login/', auth_views.LoginView.as_view(), name='login'),
    
    # 刷新token
    path('refresh/', auth_views.TokenRefreshView.as_view(), name='token-refresh'),
    
    # 验证token
    path('verify/', auth_views.TokenVerifyView.as_view(), name='token-verify'),
    
    # 修改自己的密码
    path('me/change-password/', auth_views.ChangePasswordView.as_view(), name='change-password'),
    
    # 管理员修改用户密码
    path('<int:user_id>/change-password/', auth_views.AdminChangePasswordView.as_view(), name='admin-change-password'),
    
    # 密码重置
    path('password-reset/request/', auth_views.PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset/verify/', auth_views.PasswordResetVerifyView.as_view(), name='password-reset-verify'),
    path('password-reset/confirm/', auth_views.PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
] 