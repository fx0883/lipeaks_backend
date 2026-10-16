"""
许可证模块专属业务异常

遵循依赖倒置原则（DIP）：业务模块依赖底层抽象基类 BusinessException
"""
from common.exceptions.base import BusinessException
from common.exceptions.error_codes import ErrorCodes, ErrorMessages


class LicenseException(BusinessException):
    """
    许可证模块异常基类
    """
    business_code = ErrorCodes.LICENSE_ERROR
    error_code = 'LICENSE_ERROR'
    default_detail = ErrorMessages.LICENSE_ERROR


class LicenseExpiredException(LicenseException):
    """
    许可证已过期异常
    """
    status_code = 400
    business_code = ErrorCodes.LICENSE_EXPIRED
    error_code = 'LICENSE_EXPIRED'
    default_detail = ErrorMessages.LICENSE_EXPIRED


class LicenseNotFoundException(LicenseException):
    """
    许可证不存在异常
    """
    status_code = 404
    business_code = ErrorCodes.LICENSE_NOT_FOUND
    error_code = 'LICENSE_NOT_FOUND'
    default_detail = ErrorMessages.LICENSE_NOT_FOUND


class LicenseQuotaExceededException(LicenseException):
    """
    许可证配额超限异常
    """
    status_code = 429
    business_code = ErrorCodes.LICENSE_QUOTA_EXCEEDED
    error_code = 'LICENSE_QUOTA_EXCEEDED'
    default_detail = ErrorMessages.LICENSE_QUOTA_EXCEEDED


class LicenseRevokedException(LicenseException):
    """
    许可证已被撤销异常
    """
    status_code = 400
    business_code = ErrorCodes.LICENSE_REVOKED
    error_code = 'LICENSE_REVOKED'
    default_detail = ErrorMessages.LICENSE_REVOKED


class LicenseActivationFailedException(LicenseException):
    """
    许可证激活失败异常
    """
    status_code = 400
    business_code = ErrorCodes.LICENSE_ACTIVATION_FAILED
    error_code = 'LICENSE_ACTIVATION_FAILED'
    default_detail = ErrorMessages.LICENSE_ACTIVATION_FAILED
