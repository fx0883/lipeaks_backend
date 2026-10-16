"""
CMS模块专属业务异常

遵循依赖倒置原则（DIP）：业务模块依赖底层抽象基类 BusinessException
"""
from common.exceptions.base import BusinessException
from common.exceptions.error_codes import ErrorCodes, ErrorMessages


class CMSException(BusinessException):
    """
    CMS模块异常基类
    """
    business_code = ErrorCodes.CMS_ERROR
    error_code = 'CMS_ERROR'
    default_detail = ErrorMessages.CMS_ERROR


class ArticleNotFoundException(CMSException):
    """
    文章不存在异常
    """
    status_code = 404
    business_code = ErrorCodes.ARTICLE_NOT_FOUND
    error_code = 'ARTICLE_NOT_FOUND'
    default_detail = ErrorMessages.ARTICLE_NOT_FOUND


class CategoryNotFoundException(CMSException):
    """
    分类不存在异常
    """
    status_code = 404
    business_code = ErrorCodes.CATEGORY_NOT_FOUND
    error_code = 'CATEGORY_NOT_FOUND'
    default_detail = ErrorMessages.CATEGORY_NOT_FOUND
