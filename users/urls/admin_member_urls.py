"""
管理员端Member管理URL配置
用于管理员管理普通用户(Member)的API路由
"""
from django.urls import path
from users.views import member_admin_views

app_name = 'admin_members'

urlpatterns = [
    # Member管理（管理员端）
    path('', member_admin_views.AdminMemberListCreateView.as_view(), name='admin-member-list-create'),
    path('<int:pk>/', member_admin_views.AdminMemberRetrieveUpdateDeleteView.as_view(), name='admin-member-detail'),
    
    # 子账号管理（管理员端）
    path('sub-accounts/', member_admin_views.AdminSubAccountListView.as_view(), name='admin-subaccount-list'),
    path('sub-accounts/<int:pk>/', member_admin_views.AdminSubAccountDetailView.as_view(), name='admin-subaccount-detail'),
    
    # 头像上传（管理员端）
    path('<int:pk>/avatar/upload/', member_admin_views.AdminMemberAvatarUploadView.as_view(), name='admin-member-avatar-upload'),
]

