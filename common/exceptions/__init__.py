"""
异常处理模块

统一异常处理系统，包含：
- 业务异常基类和各模块异常类
- 全局异常处理器
- 错误码常量定义
- 向后兼容的旧异常类别名

参考文档：docs/exception/
"""

# ==================== 新异常系统导入 ====================

# 基础类和工具
from .base import BusinessException
from .error_codes import ErrorCodes, ErrorMessages, ERROR_CODE_TO_STRING
from .handler import custom_exception_handler

# 租户模块异常
from .tenant import (
    TenantException,
    TenantNotFoundException,
    TenantInactiveException,
    TenantQuotaExceededException,
    TenantAccessDeniedException,
)

# 许可证模块异常
from .license import (
    LicenseException,
    LicenseExpiredException,
    LicenseNotFoundException,
    LicenseQuotaExceededException,
    LicenseRevokedException,
    LicenseActivationFailedException,
)

# 用户模块异常
from .user import (
    UserException,
    UserNotFoundException,
    UserInactiveException,
    UserPermissionDeniedException,
)

# 积分模块异常
from .points import (
    PointsException,
    PointsInsufficientException,
    PointsExpiredException,
)

# CMS模块异常
from .cms import (
    CMSException,
    ArticleNotFoundException,
    CategoryNotFoundException,
)


# ==================== 向后兼容性别名 ====================
# 保留旧异常类的导入路径，避免破坏现有代码
# ⚠️ 这些别名在v2.0版本将被移除，请使用新异常类

# 租户相关异常（旧名称）
TenantNotFound = TenantNotFoundException  # ⚠️ Deprecated: Use TenantNotFoundException
TenantInactive = TenantInactiveException  # ⚠️ Deprecated: Use TenantInactiveException

# 配额相关异常（旧名称）
QuotaExceeded = LicenseQuotaExceededException  # ⚠️ Deprecated: Use LicenseQuotaExceededException

# 租户头错误（保留用于中间件）
TenantHeaderInvalidOrMissing = TenantException
TenantMismatchOrNoPermission = TenantAccessDeniedException


# ==================== 导出列表 ====================

__all__ = [
    # 基础类
    'BusinessException',
    'ErrorCodes',
    'ErrorMessages',
    'ERROR_CODE_TO_STRING',
    'custom_exception_handler',
    
    # 租户模块异常
    'TenantException',
    'TenantNotFoundException',
    'TenantInactiveException',
    'TenantQuotaExceededException',
    'TenantAccessDeniedException',
    
    # 许可证模块异常
    'LicenseException',
    'LicenseExpiredException',
    'LicenseNotFoundException',
    'LicenseQuotaExceededException',
    'LicenseRevokedException',
    'LicenseActivationFailedException',
    
    # 用户模块异常
    'UserException',
    'UserNotFoundException',
    'UserInactiveException',
    'UserPermissionDeniedException',
    
    # 积分模块异常
    'PointsException',
    'PointsInsufficientException',
    'PointsExpiredException',
    
    # CMS模块异常
    'CMSException',
    'ArticleNotFoundException',
    'CategoryNotFoundException',
    
    # 向后兼容的旧异常类（已废弃）
    'TenantNotFound',  # ⚠️ Deprecated
    'TenantInactive',  # ⚠️ Deprecated
    'QuotaExceeded',  # ⚠️ Deprecated
    'TenantHeaderInvalidOrMissing',  # 保留用于中间件
    'TenantMismatchOrNoPermission',  # 保留用于中间件
]