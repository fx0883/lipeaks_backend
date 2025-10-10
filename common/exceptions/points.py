"""
积分相关异常

定义积分模块的业务异常
"""
from .base import BusinessException
from .error_codes import ErrorCodes, ErrorMessages


class PointsException(BusinessException):
    """
    积分模块异常基类
    
    所有积分相关异常都应该继承此类。
    可以直接使用并传入error_code，也可以继承创建具体异常类。
    
    Examples:
        # 方式1：使用具体异常类（高频错误）
        raise PointsInsufficientException(
            detail=f'积分余额不足，当前: {available}，需要: {required}',
            available=available,
            required=required
        )
        
        # 方式2：使用通用类+错误码（低频错误）
        raise PointsException(
            error_code='POINTS_TRANSFER_FAILED',
            detail='积分转账失败',
            from_user=from_user.id,
            to_user=to_user.id
        )
    """
    business_code = ErrorCodes.POINTS_ERROR
    error_code = 'POINTS_ERROR'
    default_detail = ErrorMessages.POINTS_ERROR


class PointsInsufficientException(PointsException):
    """
    积分余额不足异常
    
    当用户可用积分不足以完成操作时抛出此异常。
    
    Attributes:
        status_code: 400 Bad Request
        business_code: 4401
        error_code: 'POINTS_INSUFFICIENT'
    
    Examples:
        >>> raise PointsInsufficientException(
        ...     detail=f'积分余额不足，当前可用: {available}，需要: {required}',
        ...     user_id=user.id,
        ...     available_points=available,
        ...     required_points=required,
        ...     operation='redeem_coupon'
        ... )
    """
    status_code = 400
    business_code = ErrorCodes.POINTS_INSUFFICIENT
    error_code = 'POINTS_INSUFFICIENT'
    default_detail = ErrorMessages.POINTS_INSUFFICIENT


class PointsExpiredException(PointsException):
    """
    积分已过期异常
    
    当尝试使用已过期的积分时抛出此异常。
    
    Attributes:
        status_code: 400 Bad Request
        business_code: 4402
        error_code: 'POINTS_EXPIRED'
    
    Examples:
        >>> raise PointsExpiredException(
        ...     detail=f'积分已于 {expired_at} 过期',
        ...     user_id=user.id,
        ...     points_record_id=record.id,
        ...     expired_at=expired_at.isoformat(),
        ...     expired_points=record.points
        ... )
    """
    status_code = 400
    business_code = ErrorCodes.POINTS_EXPIRED
    error_code = 'POINTS_EXPIRED'
    default_detail = ErrorMessages.POINTS_EXPIRED

