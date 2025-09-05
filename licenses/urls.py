"""
许可证系统URL路由配置
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from licenses.views.admin_views import (
    SoftwareProductViewSet, LicensePlanViewSet, LicenseViewSet,
    MachineBindingViewSet, LicenseActivationViewSet, SecurityAuditLogViewSet,
    TenantLicenseQuotaViewSet
)
from licenses.views import activation_views, report_views

# 创建DRF路由器
router = DefaultRouter()

# 注册管理端ViewSet
router.register(r'products', SoftwareProductViewSet, basename='softwareproduct')
router.register(r'plans', LicensePlanViewSet, basename='licenseplan')
router.register(r'licenses', LicenseViewSet, basename='license')
router.register(r'machine-bindings', MachineBindingViewSet, basename='machinebinding')
router.register(r'activations', LicenseActivationViewSet, basename='licenseactivation')
router.register(r'audit-logs', SecurityAuditLogViewSet, basename='securityauditlog')
router.register(r'quotas', TenantLicenseQuotaViewSet, basename='tenantlicensequota')

# URL模式
urlpatterns = [
    # 管理端API路由
    path('admin/', include(router.urls)),
    
    # 客户端激活API
    path('activate/', activation_views.activate_license, name='activate_license'),
    path('verify/', activation_views.verify_activation, name='verify_activation'),
    path('heartbeat/', activation_views.heartbeat, name='heartbeat'),
    path('info/<str:license_key>/', activation_views.license_info, name='license_info'),
    path('status/', activation_views.server_status, name='server_status'),
    
    # 报告和统计API
    path('reports/generate/', report_views.generate_report, name='generate_report'),
    path('reports/dashboard/', report_views.dashboard_stats, name='dashboard_stats'),
]

# 为了向后兼容，也可以通过 'api/v1/licenses/' 前缀访问
app_name = 'licenses'
