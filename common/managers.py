"""
租户管理器扩展
支持多语言翻译和租户隔离的融合Manager
"""
import logging
from django.db import models
from parler.managers import TranslatableManager
from common.utils.tenant_context import get_current_tenant

logger = logging.getLogger(__name__)


class TranslatableTenantManager(TranslatableManager):
    """
    融合TranslatableManager和TenantManager的功能
    
    同时支持：
    1. django-parler的多语言翻译功能
    2. 租户隔离过滤
    
    使用场景：
    需要同时支持多语言和租户隔离的模型，如Category
    
    使用示例：
        class Category(BaseModel, TranslatableModel):
            objects = TranslatableTenantManager()
    """
    
    def get_queryset(self):
        """
        重写查询集方法
        1. 先调用TranslatableManager的get_queryset获取翻译功能
        2. 再添加租户过滤逻辑
        
        Returns:
            按租户过滤并支持翻译的查询集
        """
        # 先获取TranslatableManager的queryset（保持翻译功能）
        queryset = super().get_queryset()
        
        # 添加租户过滤逻辑
        tenant = get_current_tenant()
        
        if tenant:
            # 如果有租户上下文，则过滤结果
            logger.debug(f"TranslatableTenantManager: 过滤租户 {tenant.name} (ID: {tenant.id}) 的数据")
            return queryset.filter(tenant=tenant)
        
        # 如果没有租户上下文（例如超级管理员访问），返回全部结果
        logger.debug("TranslatableTenantManager: 无租户上下文，返回全部数据")
        return queryset
