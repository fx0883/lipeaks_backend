"""
CMS相关异常

定义CMS模块的业务异常
"""
from .base import BusinessException
from .error_codes import ErrorCodes, ErrorMessages


class CMSException(BusinessException):
    """
    CMS模块异常基类
    
    所有CMS相关异常都应该继承此类。
    可以直接使用并传入error_code，也可以继承创建具体异常类。
    
    Examples:
        # 方式1：使用具体异常类（高频错误）
        raise ArticleNotFoundException(
            detail=f'文章ID {article_id} 不存在',
            article_id=article_id
        )
        
        # 方式2：使用通用类+错误码（低频错误）
        raise CMSException(
            error_code='EXPORT_FORMAT_UNSUPPORTED',
            detail=f'不支持的导出格式: {format}',
            requested_format=format,
            supported_formats=['pdf', 'docx', 'html']
        )
    """
    business_code = ErrorCodes.CMS_ERROR
    error_code = 'CMS_ERROR'
    default_detail = ErrorMessages.CMS_ERROR


class ArticleNotFoundException(CMSException):
    """
    文章不存在异常
    
    当尝试访问不存在的文章时抛出此异常。
    
    Attributes:
        status_code: 404 Not Found
        business_code: 4501
        error_code: 'ARTICLE_NOT_FOUND'
    
    Examples:
        >>> raise ArticleNotFoundException(
        ...     detail=f'文章ID {article_id} 不存在',
        ...     article_id=article_id,
        ...     requested_by=user.id
        ... )
    """
    status_code = 404
    business_code = ErrorCodes.ARTICLE_NOT_FOUND
    error_code = 'ARTICLE_NOT_FOUND'
    default_detail = ErrorMessages.ARTICLE_NOT_FOUND


class CategoryNotFoundException(CMSException):
    """
    分类不存在异常
    
    当尝试访问不存在的分类时抛出此异常。
    
    Attributes:
        status_code: 404 Not Found
        business_code: 4502
        error_code: 'CATEGORY_NOT_FOUND'
    
    Examples:
        >>> raise CategoryNotFoundException(
        ...     detail=f'分类ID {category_id} 不存在',
        ...     category_id=category_id
        ... )
    """
    status_code = 404
    business_code = ErrorCodes.CATEGORY_NOT_FOUND
    error_code = 'CATEGORY_NOT_FOUND'
    default_detail = ErrorMessages.CATEGORY_NOT_FOUND

