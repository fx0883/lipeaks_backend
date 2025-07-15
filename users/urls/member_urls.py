"""
普通用户(Member)相关URL配置
"""
from django.urls import path
from users.views import member_views

app_name = 'members'

urlpatterns = [
    # 普通用户管理
    path('', member_views.MemberListCreateView.as_view(), name='member-list-create'),
    path('<int:pk>/', member_views.MemberRetrieveUpdateDeleteView.as_view(), name='member-detail'),
    
    # 当前登录的普通用户操作
    path('me/', member_views.CurrentMemberView.as_view(), name='current-member'),
    path('me/password/', member_views.MemberPasswordUpdateView.as_view(), name='member-password-update'),
    
    # 子账号管理
    path('sub-accounts/', member_views.SubAccountListCreateView.as_view(), name='sub-account-list-create'),
    path('sub-accounts/<int:pk>/', member_views.SubAccountDetailView.as_view(), name='sub-account-detail'),
    
    # 头像上传
    path('avatar/upload/', member_views.MemberAvatarUploadView.as_view(), name='member-avatar-upload'),
    path('<int:pk>/avatar/upload/', member_views.MemberSpecificAvatarUploadView.as_view(), name='member-specific-avatar-upload'),
] 