"""
客户应用URL配置
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from customers.views import (
    CustomerViewSet, CustomerMemberRelationViewSet, 
    CustomerTenantRelationViewSet, TenantCustomerViewSet
)

# 应用名称，用于URL命名空间
app_name = 'customers'

# 主路由
router = DefaultRouter()

# 客户基础操作路由
router.register(r'', CustomerViewSet, basename='customer')

# 客户-联系人关系路由
router.register(r'members/relations', CustomerMemberRelationViewSet, basename='customer-member-relation')

# 客户-租户关系路由
router.register(r'tenants/relations', CustomerTenantRelationViewSet, basename='customer-tenant-relation')

# 租户视角的客户路由
router.register(r'tenants/view', TenantCustomerViewSet, basename='tenant-customer')

urlpatterns = [
    path('', include(router.urls)),
] 