"""
许可证系统配置文件
"""

# 试用许可证配额配置
TRIAL_LICENSE_QUOTAS = {
    'default': 15,           # 默认配额：每个Member用户可以同时持有5个试用许可证
    'vip_users': 10,        # VIP用户配额（预留，可扩展）
    'enterprise': 20,       # 企业用户配额（预留，可扩展）
}

# 申请频率限制配置
APPLICATION_RATE_LIMITS = {
    'daily_limit': 15,           # API级别：每天最多申请5次
    'business_limit': 13,        # 业务级别：24小时内最多申请3次
    'cooldown_hours': 24,       # 冷却时间：24小时
}

# 其他配置（可扩展）
LICENSE_SETTINGS = {
    'auto_approve_trial': True,     # 试用申请是否自动通过
    'send_notification': True,      # 是否发送申请通知
    'enable_quota_check': True,     # 是否启用配额检查
}
