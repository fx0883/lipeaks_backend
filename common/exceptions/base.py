"""
业务异常基类模块

提供所有业务异常的根基类
"""
from rest_framework.exceptions import APIException


class BusinessException(APIException):
    """
    业务异常基类
    
    所有业务异常都应该继承此类。支持两种使用方式：
    1. 继承创建具体异常类（高频错误）
    2. 直接实例化并传入error_code（低频错误）
    
    Attributes:
        business_code (int): 业务错误码（4位数字），默认None
        error_code (str): 错误标识符（字符串常量）
        status_code (int): HTTP状态码，默认400
        default_detail (str): 默认错误消息
        extra (dict): 额外的上下文信息
    
    Examples:
        # 方式1：使用专门的异常类（高频错误）
        raise TenantNotFoundException(
            detail='租户ID 123 不存在',
            tenant_id=123
        )
        
        # 方式2：使用通用类+错误码（低频错误）
        raise LicenseException(
            error_code='ACTIVATION_DEVICE_MISMATCH',
            detail='Device fingerprint mismatch',
            expected=expected_fp,
            actual=actual_fp
        )
    """
    
    # 业务错误码（4位数字）
    business_code = None
    
    # 错误标识符（字符串常量）
    error_code = 'BUSINESS_ERROR'
    
    # HTTP状态码（默认400 Bad Request）
    status_code = 400
    
    # 默认错误消息
    default_detail = 'Business operation failed'
    
    def __init__(self, detail=None, code=None, **extra):
        """
        初始化业务异常
        
        Args:
            detail (str, optional): 错误详情消息。如果不提供，使用default_detail
            code (str, optional): 错误代码（DRF兼容参数，通常不使用）
            **extra: 额外的上下文信息，用于调试和日志记录
        
        Examples:
            >>> raise TenantNotFoundException(
            ...     detail='租户ID 123 不存在',
            ...     tenant_id=123,
            ...     requested_by='user_456'
            ... )
        """
        # 如果传入了error_code参数，使用它（支持通用类使用方式）
        if 'error_code' in extra:
            self.error_code = extra.pop('error_code')
        
        # 保存额外的上下文信息
        self.extra = extra
        
        # 调用父类初始化
        super().__init__(detail, code)
    
    def get_full_details(self):
        """
        获取完整的错误详情
        
        Returns:
            dict: 包含错误码、消息和额外信息的字典
        
        Examples:
            >>> exc = TenantNotFoundException(detail='租户不存在', tenant_id=123)
            >>> exc.get_full_details()
            {
                'detail': '租户不存在',
                'code': 'TENANT_NOT_FOUND',
                'business_code': 4101,
                'extra': {'tenant_id': 123}
            }
        """
        return {
            'detail': str(self.detail),
            'code': self.error_code,
            'business_code': self.business_code,
            'extra': self.extra
        }
    
    def __str__(self):
        """
        字符串表示
        
        Returns:
            str: 错误消息
        """
        return str(self.detail)
    
    def __repr__(self):
        """
        开发者友好的表示
        
        Returns:
            str: 类名和错误码
        """
        return f'{self.__class__.__name__}(code={self.error_code}, business_code={self.business_code})'

