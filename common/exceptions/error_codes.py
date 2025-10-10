"""
错误码常量定义

集中管理所有业务错误码，便于维护和查找。

错误码结构：4位数字 XYZZ
- X: 错误类别（4=客户端错误, 5=服务端错误）
- Y: 业务模块（0=认证, 1=租户, 2=许可证, 3=用户, 4=积分, 5=CMS, 6=订单）
- ZZ: 具体错误序号（01-99）

参考文档：docs/exception/03_error_code_specification.md
"""


class ErrorCodes:
    """
    错误码常量类
    
    所有错误码统一定义在这里，避免魔数散落在代码中。
    """
    
    # ==================== 认证授权 (40XX) ====================
    
    # 通用认证错误
    AUTH_NOT_AUTHENTICATED = 4001  # 用户未认证
    AUTH_TOKEN_INVALID = 4002      # Token无效
    AUTH_PERMISSION_DENIED = 4003  # 权限不足
    AUTH_TOKEN_EXPIRED = 4004      # Token已过期
    
    # ==================== 租户管理 (41XX) ====================
    
    TENANT_ERROR = 4100                 # 租户通用错误
    TENANT_NOT_FOUND = 4101             # 租户不存在
    TENANT_INACTIVE = 4102              # 租户未激活
    TENANT_QUOTA_EXCEEDED = 4103        # 租户配额超限
    TENANT_ACCESS_DENIED = 4104         # 租户访问拒绝
    TENANT_INVALID_ID = 4105            # 租户ID无效
    
    # ==================== 许可证管理 (42XX) ====================
    
    LICENSE_ERROR = 4200                # 许可证通用错误
    LICENSE_EXPIRED = 4201              # 许可证已过期
    LICENSE_NOT_FOUND = 4202            # 许可证不存在
    LICENSE_QUOTA_EXCEEDED = 4203       # 许可证配额超限
    LICENSE_REVOKED = 4204              # 许可证已撤销
    LICENSE_ACTIVATION_FAILED = 4205    # 许可证激活失败
    LICENSE_ALREADY_ASSIGNED = 4206     # 许可证已分配
    LICENSE_INVALID_KEY = 4207          # 许可证密钥无效
    LICENSE_PLAN_NOT_FOUND = 4208       # 许可证方案不存在
    
    # ==================== 用户管理 (43XX) ====================
    
    USER_ERROR = 4300                   # 用户通用错误
    USER_NOT_FOUND = 4301               # 用户不存在
    USER_INACTIVE = 4302                # 用户未激活
    USER_PERMISSION_DENIED = 4303       # 用户权限拒绝
    USER_ALREADY_EXISTS = 4304          # 用户已存在
    USER_INVALID_CREDENTIALS = 4305     # 用户凭证无效
    
    # ==================== 积分系统 (44XX) ====================
    
    POINTS_ERROR = 4400                 # 积分通用错误
    POINTS_INSUFFICIENT = 4401          # 积分余额不足
    POINTS_EXPIRED = 4402               # 积分已过期
    POINTS_NOT_ENABLED = 4403           # 积分功能未启用
    POINTS_DAILY_LIMIT_EXCEEDED = 4404  # 每日积分上限
    
    # ==================== CMS系统 (45XX) ====================
    
    CMS_ERROR = 4500                    # CMS通用错误
    ARTICLE_NOT_FOUND = 4501            # 文章不存在
    CATEGORY_NOT_FOUND = 4502           # 分类不存在
    TAG_NOT_FOUND = 4503                # 标签不存在
    COMMENT_NOT_FOUND = 4504            # 评论不存在
    
    # ==================== 订单系统 (46XX) ====================
    
    ORDER_ERROR = 4600                  # 订单通用错误
    ORDER_NOT_FOUND = 4601              # 订单不存在
    ORDER_CANCELLED = 4602              # 订单已取消
    ORDER_ALREADY_PAID = 4603           # 订单已支付
    
    # ==================== 预留 (47XX-49XX) ====================
    # 为未来模块预留
    
    # ==================== 服务器错误 (50XX) ====================
    
    INTERNAL_SERVER_ERROR = 5000        # 服务器内部错误
    DATABASE_ERROR = 5001               # 数据库错误
    EXTERNAL_SERVICE_ERROR = 5002       # 第三方服务错误
    CONFIGURATION_ERROR = 5003          # 配置错误


class ErrorMessages:
    """
    错误消息常量类
    
    定义默认错误消息，支持国际化（未来）。
    """
    
    # ==================== 认证授权 ====================
    
    AUTH_NOT_AUTHENTICATED = '认证失败，请登录'
    AUTH_TOKEN_INVALID = '认证令牌无效或已过期'
    AUTH_PERMISSION_DENIED = '您没有执行该操作的权限'
    AUTH_TOKEN_EXPIRED = '认证令牌已过期，请重新登录'
    
    # ==================== 租户管理 ====================
    
    TENANT_ERROR = '租户操作失败'
    TENANT_NOT_FOUND = '租户不存在'
    TENANT_INACTIVE = '租户未激活或已被禁用'
    TENANT_QUOTA_EXCEEDED = '租户许可证配额已满'
    TENANT_ACCESS_DENIED = '无法访问其他租户的资源'
    TENANT_INVALID_ID = '无效的租户ID格式'
    
    # ==================== 许可证管理 ====================
    
    LICENSE_ERROR = '许可证操作失败'
    LICENSE_EXPIRED = '许可证已过期'
    LICENSE_NOT_FOUND = '许可证不存在'
    LICENSE_QUOTA_EXCEEDED = '许可证配额已达上限'
    LICENSE_REVOKED = '许可证已被撤销'
    LICENSE_ACTIVATION_FAILED = '许可证激活失败'
    LICENSE_ALREADY_ASSIGNED = '该用户已拥有该产品的许可证'
    LICENSE_INVALID_KEY = '无效的许可证密钥'
    LICENSE_PLAN_NOT_FOUND = '许可证方案不存在'
    
    # ==================== 用户管理 ====================
    
    USER_ERROR = '用户操作失败'
    USER_NOT_FOUND = '用户不存在'
    USER_INACTIVE = '用户账户已被禁用'
    USER_PERMISSION_DENIED = '用户权限不足'
    USER_ALREADY_EXISTS = '用户名或邮箱已存在'
    USER_INVALID_CREDENTIALS = '用户名或密码错误'
    
    # ==================== 积分系统 ====================
    
    POINTS_ERROR = '积分操作失败'
    POINTS_INSUFFICIENT = '积分余额不足'
    POINTS_EXPIRED = '积分已过期'
    POINTS_NOT_ENABLED = '该用户未启用积分功能'
    POINTS_DAILY_LIMIT_EXCEEDED = '今日积分已达上限'
    
    # ==================== CMS系统 ====================
    
    CMS_ERROR = 'CMS操作失败'
    ARTICLE_NOT_FOUND = '文章不存在'
    CATEGORY_NOT_FOUND = '分类不存在'
    TAG_NOT_FOUND = '标签不存在'
    COMMENT_NOT_FOUND = '评论不存在'
    
    # ==================== 订单系统 ====================
    
    ORDER_ERROR = '订单操作失败'
    ORDER_NOT_FOUND = '订单不存在'
    ORDER_CANCELLED = '订单已取消'
    ORDER_ALREADY_PAID = '订单已支付，无法修改'
    
    # ==================== 服务器错误 ====================
    
    INTERNAL_SERVER_ERROR = '服务器内部错误'
    DATABASE_ERROR = '数据库操作失败'
    EXTERNAL_SERVICE_ERROR = '第三方服务调用失败'
    CONFIGURATION_ERROR = '服务配置错误'


# 错误码到字符串标识符的映射（用于反向查找）
ERROR_CODE_TO_STRING = {
    # 认证授权
    4001: 'AUTH_NOT_AUTHENTICATED',
    4002: 'AUTH_TOKEN_INVALID',
    4003: 'AUTH_PERMISSION_DENIED',
    4004: 'AUTH_TOKEN_EXPIRED',
    
    # 租户管理
    4100: 'TENANT_ERROR',
    4101: 'TENANT_NOT_FOUND',
    4102: 'TENANT_INACTIVE',
    4103: 'TENANT_QUOTA_EXCEEDED',
    4104: 'TENANT_ACCESS_DENIED',
    4105: 'TENANT_INVALID_ID',
    
    # 许可证管理
    4200: 'LICENSE_ERROR',
    4201: 'LICENSE_EXPIRED',
    4202: 'LICENSE_NOT_FOUND',
    4203: 'LICENSE_QUOTA_EXCEEDED',
    4204: 'LICENSE_REVOKED',
    4205: 'LICENSE_ACTIVATION_FAILED',
    4206: 'LICENSE_ALREADY_ASSIGNED',
    4207: 'LICENSE_INVALID_KEY',
    4208: 'LICENSE_PLAN_NOT_FOUND',
    
    # 用户管理
    4300: 'USER_ERROR',
    4301: 'USER_NOT_FOUND',
    4302: 'USER_INACTIVE',
    4303: 'USER_PERMISSION_DENIED',
    4304: 'USER_ALREADY_EXISTS',
    4305: 'USER_INVALID_CREDENTIALS',
    
    # 积分系统
    4400: 'POINTS_ERROR',
    4401: 'POINTS_INSUFFICIENT',
    4402: 'POINTS_EXPIRED',
    4403: 'POINTS_NOT_ENABLED',
    4404: 'POINTS_DAILY_LIMIT_EXCEEDED',
    
    # CMS系统
    4500: 'CMS_ERROR',
    4501: 'ARTICLE_NOT_FOUND',
    4502: 'CATEGORY_NOT_FOUND',
    4503: 'TAG_NOT_FOUND',
    4504: 'COMMENT_NOT_FOUND',
    
    # 订单系统
    4600: 'ORDER_ERROR',
    4601: 'ORDER_NOT_FOUND',
    4602: 'ORDER_CANCELLED',
    4603: 'ORDER_ALREADY_PAID',
    
    # 服务器错误
    5000: 'INTERNAL_SERVER_ERROR',
    5001: 'DATABASE_ERROR',
    5002: 'EXTERNAL_SERVICE_ERROR',
    5003: 'CONFIGURATION_ERROR',
}

