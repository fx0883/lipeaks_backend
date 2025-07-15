from django.urls import path
from . import views

app_name = 'charts'
 
urlpatterns = [
    path('tenant-trend/', views.TenantTrendChartView.as_view(), name='tenant-trend'),
    path('tenant-status-distribution/', views.TenantStatusDistributionView.as_view(), name='tenant-status-distribution'),
    path('tenant-creation-rate/', views.TenantCreationRateView.as_view(), name='tenant-creation-rate'),
    
    # 用户统计图表API
    path('user-growth-trend/', views.UserGrowthTrendView.as_view(), name='user-growth-trend'),
    path('user-role-distribution/', views.UserRoleDistributionView.as_view(), name='user-role-distribution'),
    path('active-users/', views.ActiveUsersView.as_view(), name='active-users'),
    path('login-heatmap/', views.LoginHeatmapView.as_view(), name='login-heatmap'),
] 