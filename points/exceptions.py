"""
积分模块专属业务异常

遵循依赖倒置原则（DIP）：业务模块依赖底层抽象基类 BusinessException
"""
from common.exceptions.base import BusinessException
from common.exceptions.error_codes import ErrorCodes, ErrorMessages


class PointsException(BusinessException):
    """
    积分模块异常基类
    """
    business_code = ErrorCodes.POINTS_ERROR
    error_code = 'POINTS_ERROR'
    default_detail = ErrorMessages.POINTS_ERROR


class PointsInsufficientException(PointsException):
    """
    积分余额不足异常
    """
    status_code = 400
    business_code = ErrorCodes.POINTS_INSUFFICIENT
    error_code = 'POINTS_INSUFFICIENT'
    default_detail = ErrorMessages.POINTS_INSUFFICIENT


class PointsExpiredException(PointsException):
    """
    积分已过期异常
    """
    status_code = 400
    business_code = ErrorCodes.POINTS_EXPIRED
    error_code = 'POINTS_EXPIRED'
    default_detail = ErrorMessages.POINTS_EXPIRED
