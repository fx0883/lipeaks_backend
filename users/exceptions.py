"""
用户模块专属业务异常

遵循依赖倒置原则（DIP）：业务模块依赖底层抽象基类 BusinessException
"""
from common.exceptions.base import BusinessException
from common.exceptions.error_codes import ErrorCodes, ErrorMessages


class UserException(BusinessException):
    """
    用户模块异常基类
    """
    business_code = ErrorCodes.USER_ERROR
    error_code = 'USER_ERROR'
    default_detail = ErrorMessages.USER_ERROR


class UserNotFoundException(UserException):
    """
    用户不存在异常
    """
    status_code = 404
    business_code = ErrorCodes.USER_NOT_FOUND
    error_code = 'USER_NOT_FOUND'
    default_detail = ErrorMessages.USER_NOT_FOUND


class UserInactiveException(UserException):
    """
    用户已禁用异常
    """
    status_code = 403
    business_code = ErrorCodes.USER_INACTIVE
    error_code = 'USER_INACTIVE'
    default_detail = ErrorMessages.USER_INACTIVE


class UserPermissionDeniedException(UserException):
    """
    用户权限不足异常
    """
    status_code = 403
    business_code = ErrorCodes.USER_PERMISSION_DENIED
    error_code = 'USER_PERMISSION_DENIED'
    default_detail = ErrorMessages.USER_PERMISSION_DENIED
