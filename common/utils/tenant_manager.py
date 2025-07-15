"""
租户管理器，用于自动过滤查询集
"""
import logging
from django.db import models
from common.utils.tenant_context import get_current_tenant, set_current_tenant, clear_current_tenant

logger = logging.getLogger(__name__)

class TenantManager(models.Manager):
    """
    租户模型管理器，自动根据当前租户过滤查询集
    """
    def get_queryset(self):
        """
        重写查询集方法，自动按当前租户过滤
        
        Returns:
            按当前租户过滤后的查询集，如果没有当前租户上下文则返回全部
        """
        queryset = super().get_queryset()
        tenant = get_current_tenant()
        
        if tenant:
            # 如果有租户上下文，则过滤结果
            logger.debug(f"TenantManager: 过滤租户 {tenant.name} (ID: {tenant.id}) 的数据")
            return queryset.filter(tenant=tenant)
        
        # 如果没有租户上下文（例如超级管理员访问），返回全部结果
        logger.debug("TenantManager: 无租户上下文，返回全部数据")
        return queryset 