"""
通用Admin Mixins
提供租户过滤等通用功能
"""
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class BaseTenantFilterMixin:
    """
    通用租户过滤Mixin，为Admin提供租户过滤功能
    """
    
    def changelist_view(self, request, extra_context=None):
        """
        重写changelist_view，添加租户过滤功能
        """
        # 获取current用户
        user = request.user
        
        # 根据用户类型获取可用租户
        if user.is_superuser:
            # 超级管理员可以看到所有租户
            from tenants.models import Tenant
            available_tenants = Tenant.objects.filter(is_deleted=False).select_related().order_by('name')
        else:
            # 普通用户只能看到自己关联的租户
            if hasattr(user, 'tenant') and user.tenant:
                available_tenants = [user.tenant]
            else:
                available_tenants = []
        
        # 获取current选中的租户ID
        selected_tenant = request.GET.get('tenant_id')
        selected_tenant_name = None
        
        if selected_tenant:
            try:
                selected_tenant = int(selected_tenant)
                # 查找选中的租户名称
                for tenant in available_tenants:
                    if tenant.id == selected_tenant:
                        selected_tenant_name = tenant.name
                        break
            except (ValueError, TypeError):
                selected_tenant = None
        
        # 准备额外的上下文
        extra_context = extra_context or {}
        extra_context.update({
            'available_tenants': available_tenants,
            'selected_tenant': selected_tenant,
            'selected_tenant_name': selected_tenant_name,
        })
        
        # 调用父类方法
        return super().changelist_view(request, extra_context)
    
    def get_queryset(self, request):
        """
        重写get_queryset，根据租户过滤数据
        """
        qs = super().get_queryset(request)
        
        # 获取租户ID参数
        tenant_id = request.GET.get('tenant_id')
        
        if tenant_id and request.user.is_superuser:
            # 超级管理员可以按租户过滤
            try:
                tenant_id = int(tenant_id)
                qs = qs.filter(tenant_id=tenant_id)
            except (ValueError, TypeError):
                pass
        elif not request.user.is_superuser:
            # 普通用户只能看到自己租户的数据
            if hasattr(request.user, 'tenant') and request.user.tenant:
                qs = qs.filter(tenant=request.user.tenant)
            else:
                # 如果没有关联租户，返回空查询集
                qs = qs.none()
        
        return qs
