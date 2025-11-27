"""
Member 密码重置 URL 配置（公开页面）
路径: /api/v1/members/password-reset/
"""
from django.urls import path
from users.views import member_password_reset_views

app_name = 'member_password_reset'

urlpatterns = [
    # 密码重置请求页面 - GET: 显示表单, POST: 发送重置邮件
    # URL: /api/v1/members/password-reset/?tenant_id=xxx
    path('', 
         member_password_reset_views.MemberPasswordResetRequestPageView.as_view(), 
         name='request'),
    
    # 邮件发送成功页面
    # URL: /api/v1/members/password-reset/sent/?tenant_id=xxx
    path('sent/', 
         member_password_reset_views.MemberPasswordResetRequestSentView.as_view(), 
         name='sent'),
    
    # 设置新密码页面 - GET: 显示表单, POST: 设置密码
    # URL: /api/v1/members/password-reset/{token}/?tenant_id=xxx
    path('<str:token>/', 
         member_password_reset_views.MemberPasswordResetFormView.as_view(), 
         name='form'),
    
    # 密码重置完成页面
    # URL: /api/v1/members/password-reset/complete/?tenant_id=xxx
    path('complete/', 
         member_password_reset_views.MemberPasswordResetCompleteView.as_view(), 
         name='complete'),
]
