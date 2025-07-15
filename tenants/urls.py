"""
租户相关的URL路由
"""
from django.urls import path
from tenants import views

app_name = 'tenants'

urlpatterns = [
    # 租户列表和创建
    path('', views.TenantListCreateView.as_view(), name='tenant-list-create'),
    
    # 租户详情、更新和删除
    path('<int:pk>/', views.TenantRetrieveUpdateDeleteView.as_view(), name='tenant-detail'),
    
    # 获取租户完整信息
    path('<int:pk>/comprehensive/', views.TenantComprehensiveView.as_view(), name='tenant-comprehensive'),
    
    # 租户配额管理
    path('<int:pk>/quota/', views.TenantQuotaUpdateView.as_view(), name='tenant-quota-update'),
    
    # 租户配额使用情况
    path('<int:pk>/quota/usage/', views.TenantQuotaUsageView.as_view(), name='tenant-quota-usage'),
    
    # 租户状态管理 - 暂停租户
    path('<int:pk>/suspend/', views.TenantSuspendView.as_view(), name='tenant-suspend'),
    
    # 租户状态管理 - 激活租户
    path('<int:pk>/activate/', views.TenantActivateView.as_view(), name='tenant-activate'),
    
    # 租户用户列表
    path('<int:pk>/users/', views.TenantUserListView.as_view(), name='tenant-user-list'),
] 