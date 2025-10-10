"""
租户相关异常

定义租户模块的业务异常
"""
from .base import BusinessException
from .error_codes import ErrorCodes, ErrorMessages


class TenantException(BusinessException):
    """
    租户模块异常基类
    
    所有租户相关异常都应该继承此类。
    可以直接使用并传入error_code，也可以继承创建具体异常类。
    
    Examples:
        # 方式1：使用具体异常类（高频错误）
        raise TenantNotFoundException(detail='租户ID 123 不存在', tenant_id=123)
        
        # 方式2：使用通用类+错误码（低频错误）
        raise TenantException(
            error_code='TENANT_SUSPENDED',
            detail='租户已被暂停',
            tenant_id=123,
            reason='payment_overdue'
        )
    """
    business_code = ErrorCodes.TENANT_ERROR
    error_code = 'TENANT_ERROR'
    default_detail = ErrorMessages.TENANT_ERROR


class TenantNotFoundException(TenantException):
    """
    租户不存在异常
    
    当尝试访问不存在的租户时抛出此异常。
    
    Attributes:
        status_code: 404 Not Found
        business_code: 4101
        error_code: 'TENANT_NOT_FOUND'
    
    Examples:
        >>> raise TenantNotFoundException(
        ...     detail=f'租户ID {tenant_id} 不存在',
        ...     tenant_id=tenant_id,
        ...     requested_by=user.id
        ... )
    """
    status_code = 404
    business_code = ErrorCodes.TENANT_NOT_FOUND
    error_code = 'TENANT_NOT_FOUND'
    default_detail = ErrorMessages.TENANT_NOT_FOUND


class TenantInactiveException(TenantException):
    """
    租户未激活异常
    
    当尝试访问未激活或已被禁用的租户时抛出此异常。
    
    Attributes:
        status_code: 403 Forbidden
        business_code: 4102
        error_code: 'TENANT_INACTIVE'
    
    Examples:
        >>> raise TenantInactiveException(
        ...     detail=f'租户 {tenant.name} 已被禁用（状态: {tenant.status}）',
        ...     tenant_id=tenant.id,
        ...     status=tenant.status
        ... )
    """
    status_code = 403
    business_code = ErrorCodes.TENANT_INACTIVE
    error_code = 'TENANT_INACTIVE'
    default_detail = ErrorMessages.TENANT_INACTIVE


class TenantQuotaExceededException(TenantException):
    """
    租户配额超限异常
    
    当租户使用的资源超过配额限制时抛出此异常。
    
    Attributes:
        status_code: 429 Too Many Requests
        business_code: 4103
        error_code: 'TENANT_QUOTA_EXCEEDED'
    
    Examples:
        >>> raise TenantQuotaExceededException(
        ...     detail=f'租户许可证配额已满（{current}/{max_licenses}）',
        ...     tenant_id=tenant.id,
        ...     current_count=current,
        ...     max_count=max_licenses,
        ...     resource_type='licenses'
        ... )
    """
    status_code = 429
    business_code = ErrorCodes.TENANT_QUOTA_EXCEEDED
    error_code = 'TENANT_QUOTA_EXCEEDED'
    default_detail = ErrorMessages.TENANT_QUOTA_EXCEEDED


class TenantAccessDeniedException(TenantException):
    """
    租户访问拒绝异常
    
    当用户尝试访问其他租户的资源时抛出此异常。
    
    Attributes:
        status_code: 403 Forbidden
        business_code: 4104
        error_code: 'TENANT_ACCESS_DENIED'
    
    Examples:
        >>> raise TenantAccessDeniedException(
        ...     detail='无法访问其他租户的资源',
        ...     user_id=user.id,
        ...     user_tenant_id=user.tenant_id,
        ...     requested_tenant_id=tenant_id
        ... )
    """
    status_code = 403
    business_code = ErrorCodes.TENANT_ACCESS_DENIED
    error_code = 'TENANT_ACCESS_DENIED'
    default_detail = ErrorMessages.TENANT_ACCESS_DENIED

