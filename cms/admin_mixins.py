"""
CMS Admin的通用Mixin类
"""
from django.contrib import admin
from django.utils.translation import gettext_lazy as _


class TenantFilterMixin:
    """
    租户过滤Mixin，为CMS Admin类提供租户过滤功能
    """
    
    def changelist_view(self, request, extra_context=None):
        """
        重写changelist_view方法，添加租户过滤支持
        """
        # 获取查询参数中的租户ID
        tenant_id = request.GET.get('tenant_id')
        
        # 准备额外的上下文数据
        extra_context = extra_context or {}
        
        # 获取可用的租户列表（仅超级管理员可以看到所有租户）
        if request.user.is_superuser:
            from tenants.models import Tenant
            available_tenants = Tenant.objects.filter(is_deleted=False).order_by('name')
        else:
            # 普通用户只能看到自己的租户
            available_tenants = []
            if hasattr(request.user, 'tenant') and request.user.tenant:
                available_tenants = [request.user.tenant]
        
        extra_context.update({
            'available_tenants': available_tenants,
            'selected_tenant': tenant_id,
            'selected_tenant_name': None,
        })
        
        # 如果有选中的租户，获取租户名称
        if tenant_id and available_tenants:
            try:
                selected_tenant = next((t for t in available_tenants if str(t.id) == tenant_id), None)
                if selected_tenant:
                    extra_context['selected_tenant_name'] = selected_tenant.name
            except (ValueError, TypeError):
                pass
        
        return super().changelist_view(request, extra_context)
    
    def get_queryset(self, request):
        """
        重写get_queryset方法，支持租户过滤
        """
        qs = super().get_queryset(request)
        
        # 获取查询参数中的租户ID
        tenant_id = request.GET.get('tenant_id')
        
        # 如果是超级管理员，显示所有租户的数据
        if request.user.is_superuser:
            # 如果指定了租户ID，则按租户过滤
            if tenant_id:
                try:
                    qs = qs.filter(tenant_id=tenant_id)
                except (ValueError, TypeError):
                    pass
            return qs
        # 如果是普通用户，只显示其关联租户的数据
        elif hasattr(request.user, 'tenant') and request.user.tenant:
            return qs.filter(tenant=request.user.tenant)
        # 如果用户没有关联租户，返回空查询集
        else:
            return qs.none()


class CMSAdminMixin(TenantFilterMixin):
    """
    CMS Admin的通用Mixin，包含租户过滤和自定义模板
    """
    change_list_template = 'admin/cms/change_list.html'
