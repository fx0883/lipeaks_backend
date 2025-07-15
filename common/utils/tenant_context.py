"""
租户上下文管理工具，用于存储和获取当前租户信息
"""
import threading
import logging

# 创建线程本地存储
_thread_local = threading.local()
logger = logging.getLogger(__name__)

def get_current_tenant():
    """
    获取当前线程中存储的租户
    
    Returns:
        当前租户对象，如果未设置则返回None
    """
    return getattr(_thread_local, 'tenant', None)

def set_current_tenant(tenant):
    """
    设置当前线程的租户
    
    Args:
        tenant: 租户对象，设置为None表示清除租户上下文
    """
    if tenant:
        logger.debug(f"设置当前租户: {tenant.name} (ID: {tenant.id})")
    else:
        logger.debug("清除当前租户上下文")
    
    _thread_local.tenant = tenant

def clear_current_tenant():
    """
    清除当前线程的租户上下文
    """
    if hasattr(_thread_local, 'tenant'):
        logger.debug("清除当前租户上下文")
        del _thread_local.tenant 