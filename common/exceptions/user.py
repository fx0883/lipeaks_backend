"""
用户相关异常

定义用户模块的业务异常
"""
from .base import BusinessException
from .error_codes import ErrorCodes, ErrorMessages


class UserException(BusinessException):
    """
    用户模块异常基类
    
    所有用户相关异常都应该继承此类。
    可以直接使用并传入error_code，也可以继承创建具体异常类。
    
    Examples:
        # 方式1：使用具体异常类（高频错误）
        raise UserNotFoundException(
            detail=f'用户ID {user_id} 不存在',
            user_id=user_id
        )
        
        # 方式2：使用通用类+错误码（低频错误）
        raise UserException(
            error_code='USER_EMAIL_NOT_VERIFIED',
            detail='邮箱未验证，请先验证邮箱',
            user_id=user.id,
            email=user.email
        )
    """
    business_code = ErrorCodes.USER_ERROR
    error_code = 'USER_ERROR'
    default_detail = ErrorMessages.USER_ERROR


class UserNotFoundException(UserException):
    """
    用户不存在异常
    
    当尝试访问不存在的用户时抛出此异常。
    
    Attributes:
        status_code: 404 Not Found
        business_code: 4301
        error_code: 'USER_NOT_FOUND'
    
    Examples:
        >>> raise UserNotFoundException(
        ...     detail=f'用户ID {user_id} 不存在',
        ...     user_id=user_id,
        ...     requested_by=request.user.id
        ... )
    """
    status_code = 404
    business_code = ErrorCodes.USER_NOT_FOUND
    error_code = 'USER_NOT_FOUND'
    default_detail = ErrorMessages.USER_NOT_FOUND


class UserInactiveException(UserException):
    """
    用户未激活异常
    
    当尝试访问未激活或已被禁用的用户时抛出此异常。
    
    Attributes:
        status_code: 403 Forbidden
        business_code: 4302
        error_code: 'USER_INACTIVE'
    
    Examples:
        >>> raise UserInactiveException(
        ...     detail=f'用户 {user.username} 已被禁用',
        ...     user_id=user.id,
        ...     username=user.username,
        ...     status=user.status
        ... )
    """
    status_code = 403
    business_code = ErrorCodes.USER_INACTIVE
    error_code = 'USER_INACTIVE'
    default_detail = ErrorMessages.USER_INACTIVE


class UserPermissionDeniedException(UserException):
    """
    用户权限拒绝异常
    
    当用户没有执行某个操作的权限时抛出此异常。
    
    Attributes:
        status_code: 403 Forbidden
        business_code: 4303
        error_code: 'USER_PERMISSION_DENIED'
    
    Examples:
        >>> raise UserPermissionDeniedException(
        ...     detail='无权限更改其他租户的用户角色',
        ...     user_id=user.id,
        ...     target_user_id=target_user.id,
        ...     target_tenant_id=target_user.tenant_id,
        ...     required_permission='change_user_role'
        ... )
    """
    status_code = 403
    business_code = ErrorCodes.USER_PERMISSION_DENIED
    error_code = 'USER_PERMISSION_DENIED'
    default_detail = ErrorMessages.USER_PERMISSION_DENIED

