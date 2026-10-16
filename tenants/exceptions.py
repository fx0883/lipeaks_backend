"""
租户模块专属业务异常

遵循依赖倒置原则（DIP）：业务模块依赖底层抽象基类 BusinessException
"""
from common.exceptions.base import BusinessException
from common.exceptions.error_codes import ErrorCodes, ErrorMessages


class TenantException(BusinessException):
    """
    租户模块异常基类
    """
    business_code = ErrorCodes.TENANT_ERROR
    error_code = 'TENANT_ERROR'
    default_detail = ErrorMessages.TENANT_ERROR


class TenantNotFoundException(TenantException):
    """
    租户不存在异常
    """
    status_code = 404
    business_code = ErrorCodes.TENANT_NOT_FOUND
    error_code = 'TENANT_NOT_FOUND'
    default_detail = ErrorMessages.TENANT_NOT_FOUND


class TenantInactiveException(TenantException):
    """
    租户已禁用异常
    """
    status_code = 403
    business_code = ErrorCodes.TENANT_INACTIVE
    error_code = 'TENANT_INACTIVE'
    default_detail = ErrorMessages.TENANT_INACTIVE


class TenantQuotaExceededException(TenantException):
    """
    租户配额超限异常
    """
    status_code = 429
    business_code = ErrorCodes.TENANT_QUOTA_EXCEEDED
    error_code = 'TENANT_QUOTA_EXCEEDED'
    default_detail = ErrorMessages.TENANT_QUOTA_EXCEEDED


class TenantAccessDeniedException(TenantException):
    """
    租户访问被拒绝异常
    """
    status_code = 403
    business_code = ErrorCodes.TENANT_ACCESS_DENIED
    error_code = 'TENANT_ACCESS_DENIED'
    default_detail = ErrorMessages.TENANT_ACCESS_DENIED
