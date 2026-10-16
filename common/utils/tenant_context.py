"""
租户上下文管理工具，用于存储和获取当前租户信息
基于 Python 原生 contextvars.ContextVar 实现，支持同步多线程与 ASGI/asyncio 协程上下文安全隔离
"""
import contextlib
import logging
from contextvars import ContextVar, Token
from typing import Any, Optional

logger = logging.getLogger(__name__)

# 创建全局租户上下文 ContextVar，默认值为 None
_tenant_context_var: ContextVar[Optional[Any]] = ContextVar('current_tenant', default=None)
_tenant_context = _tenant_context_var


def get_current_tenant() -> Optional[Any]:
    """
    获取当前上下文（线程/协程）中存储的租户

    Returns:
        当前租户对象，如果未设置则返回 None
    """
    return _tenant_context_var.get()


def set_current_tenant(tenant: Optional[Any]) -> None:
    """
    设置当前上下文（线程/协程）的租户

    Args:
        tenant: 租户对象，设置为 None 表示清除租户上下文
    """
    if tenant:
        tenant_name = getattr(tenant, 'name', str(tenant))
        tenant_id = getattr(tenant, 'id', 'unknown')
        logger.debug(f"设置当前租户: {tenant_name} (ID: {tenant_id})")
    else:
        logger.debug("清除当前租户上下文")

    _tenant_context_var.set(tenant)


def clear_current_tenant() -> None:
    """
    清除当前上下文（线程/协程）的租户上下文
    """
    logger.debug("清除当前租户上下文")
    _tenant_context_var.set(None)


@contextlib.contextmanager
def tenant_context(tenant: Optional[Any]):
    """
    租户上下文管理器 (Context Manager)
    用于在 with 代码块内临时设置指定租户，退出代码块时自动恢复先前租户上下文。

    使用示例:
        with tenant_context(target_tenant):
            # 块内所有 ORM 查询与逻辑自动绑定 target_tenant
            do_tenant_work()
        # 退出后自动恢复原有上下文，即使抛出异常也保证恢复
    """
    token: Token = _tenant_context_var.set(tenant)
    try:
        yield tenant
    finally:
        _tenant_context_var.reset(token)