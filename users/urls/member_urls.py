"""
Member端URL配置（Member自用）
注意：管理员管理Member的API已移至 /api/v1/admin/members/
"""
from django.urls import path
from users.views import member_views, member_password_reset_views

app_name = 'members'

urlpatterns = [
    # current登录的Member操作
    path('me/', member_views.CurrentMemberView.as_view(), name='current-member'),
    path('me/password/', member_views.MemberPasswordUpdateView.as_view(), name='member-password-update'),
    
    # Member的子账号管理
    path('sub-accounts/', member_views.SubAccountListCreateView.as_view(), name='sub-account-list-create'),
    path('sub-accounts/<int:pk>/', member_views.SubAccountDetailView.as_view(), name='sub-account-detail'),
    
    # Member头像上传
    path('avatar/upload/', member_views.MemberAvatarUploadView.as_view(), name='member-avatar-upload'),
    
    # Member密码重置（服务端页面）
    # 注意：具体路径必须放在动态路径之前，否则会被 <str:token> 匹配
    path('password/reset/request/', member_password_reset_views.MemberPasswordResetRequestPageView.as_view(), name='password-reset-request'),
    path('password/reset/request/sent/', member_password_reset_views.MemberPasswordResetRequestSentView.as_view(), name='password-reset-request-sent'),
    path('password/reset/complete/', member_password_reset_views.MemberPasswordResetCompleteView.as_view(), name='password-reset-complete'),
    path('password/reset/<str:token>/', member_password_reset_views.MemberPasswordResetFormView.as_view(), name='password-reset-form'),
] 