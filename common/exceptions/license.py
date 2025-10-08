"""
许可证相关异常

定义许可证模块的业务异常
"""
from .base import BusinessException
from .error_codes import ErrorCodes, ErrorMessages


class LicenseException(BusinessException):
    """
    许可证模块异常基类
    
    所有许可证相关异常都应该继承此类。
    可以直接使用并传入error_code，也可以继承创建具体异常类。
    
    Examples:
        # 方式1：使用具体异常类（高频错误）
        raise LicenseExpiredException(
            detail=f'许可证已于 {expired_at} 过期',
            license_id=license.id
        )
        
        # 方式2：使用通用类+错误码（低频错误）
        raise LicenseException(
            error_code='ACTIVATION_DEVICE_MISMATCH',
            detail='设备指纹不匹配',
            expected=expected_fp,
            actual=actual_fp
        )
    """
    business_code = ErrorCodes.LICENSE_ERROR
    error_code = 'LICENSE_ERROR'
    default_detail = ErrorMessages.LICENSE_ERROR


class LicenseExpiredException(LicenseException):
    """
    许可证已过期异常
    
    当尝试使用已过期的许可证时抛出此异常。
    
    Attributes:
        status_code: 400 Bad Request
        business_code: 4201
        error_code: 'LICENSE_EXPIRED'
    
    Examples:
        >>> from datetime import datetime
        >>> raise LicenseExpiredException(
        ...     detail=f'许可证已于 {expired_at.strftime("%Y-%m-%d")} 过期',
        ...     license_id=license.id,
        ...     license_key=license.license_key,
        ...     expired_at=expired_at.isoformat()
        ... )
    """
    status_code = 400
    business_code = ErrorCodes.LICENSE_EXPIRED
    error_code = 'LICENSE_EXPIRED'
    default_detail = ErrorMessages.LICENSE_EXPIRED


class LicenseNotFoundException(LicenseException):
    """
    许可证不存在异常
    
    当尝试访问不存在的许可证时抛出此异常。
    
    Attributes:
        status_code: 404 Not Found
        business_code: 4202
        error_code: 'LICENSE_NOT_FOUND'
    
    Examples:
        >>> raise LicenseNotFoundException(
        ...     detail=f'许可证ID {license_id} 不存在',
        ...     license_id=license_id
        ... )
    """
    status_code = 404
    business_code = ErrorCodes.LICENSE_NOT_FOUND
    error_code = 'LICENSE_NOT_FOUND'
    default_detail = ErrorMessages.LICENSE_NOT_FOUND


class LicenseQuotaExceededException(LicenseException):
    """
    许可证配额超限异常
    
    当许可证使用超过配额限制时抛出此异常。
    
    Attributes:
        status_code: 429 Too Many Requests
        business_code: 4203
        error_code: 'LICENSE_QUOTA_EXCEEDED'
    
    Examples:
        >>> raise LicenseQuotaExceededException(
        ...     detail=f'您的试用许可证数量已达上限（{max_licenses}个）',
        ...     current_count=current,
        ...     max_count=max_licenses,
        ...     member_id=member.id
        ... )
    """
    status_code = 429
    business_code = ErrorCodes.LICENSE_QUOTA_EXCEEDED
    error_code = 'LICENSE_QUOTA_EXCEEDED'
    default_detail = ErrorMessages.LICENSE_QUOTA_EXCEEDED


class LicenseRevokedException(LicenseException):
    """
    许可证已撤销异常
    
    当尝试使用已被撤销的许可证时抛出此异常。
    
    Attributes:
        status_code: 400 Bad Request
        business_code: 4204
        error_code: 'LICENSE_REVOKED'
    
    Examples:
        >>> raise LicenseRevokedException(
        ...     detail=f'许可证已被撤销（原因: {reason}）',
        ...     license_id=license.id,
        ...     revoked_at=license.revoked_at.isoformat(),
        ...     reason=reason
        ... )
    """
    status_code = 400
    business_code = ErrorCodes.LICENSE_REVOKED
    error_code = 'LICENSE_REVOKED'
    default_detail = ErrorMessages.LICENSE_REVOKED


class LicenseActivationFailedException(LicenseException):
    """
    许可证激活失败异常
    
    当许可证激活失败时抛出此异常。
    
    Attributes:
        status_code: 400 Bad Request
        business_code: 4205
        error_code: 'LICENSE_ACTIVATION_FAILED'
    
    Examples:
        >>> raise LicenseActivationFailedException(
        ...     detail='许可证激活失败：激活配额已满',
        ...     license_id=license.id,
        ...     current_activations=license.current_activations,
        ...     max_activations=license.max_activations
        ... )
    """
    status_code = 400
    business_code = ErrorCodes.LICENSE_ACTIVATION_FAILED
    error_code = 'LICENSE_ACTIVATION_FAILED'
    default_detail = ErrorMessages.LICENSE_ACTIVATION_FAILED

