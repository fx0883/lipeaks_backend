"""
敏感数据脱敏工具
用于对 API 审计日志中的敏感字段（如密码、Token、密钥等）进行递归脱敏处理
"""

import json
from typing import Any

# 明确的直接凭证敏感键（全小写精确匹配）
DIRECT_SENSITIVE_KEYS = {
    'password', 'old_password', 'new_password', 'password_confirm',
    'new_password_confirm', 'confirm_password', 'passwd', 'pwd',
    'secret', 'app_secret', 'client_secret', 'secret_key',
    'token', 'access_token', 'refresh_token', 'auth_token',
    'reset_token', 'csrf_token', 'csrftoken', 'authorization',
    'api_key', 'apikey', 'private_key', 'access_key', 'signature',
    'credential', 'credentials'
}

# 安全放行的非敏感键（避免误脱敏业务码或排序列）
SAFE_NON_SENSITIVE_KEYS = {
    'status_code', 'error_code', 'code', 'token_type', 'token_count',
    'token_expiry', 'token_expires_at', 'expires_in',
    'sort_key', 'cache_key', 'primary_key', 'foreign_key', 'unique_key'
}


def is_sensitive_key(key: Any) -> bool:
    """
    判断键名是否属于敏感字段（忽略大小写与前后空格）
    """
    if not isinstance(key, str):
        key = str(key)
    k = key.strip().lower()

    if k in SAFE_NON_SENSITIVE_KEYS:
        return False
    if k in DIRECT_SENSITIVE_KEYS:
        return True

    # 包含特定强敏感词
    if any(sub in k for sub in ('password', 'passwd', 'pwd', 'secret')):
        return True

    # 后缀模式匹配
    if k.endswith(('_token', 'token')):
        return True
    if k.endswith(('_key', 'api_key', 'apikey')) and not k.endswith(('sort_key', 'cache_key')):
        return True

    return False


def mask_sensitive_data(data: Any, seen: set = None, max_depth: int = 15) -> Any:
    """
    深度递归脱敏工具函数
    支持 dict、list、tuple、基础类型以及嵌套 JSON 字符串。
    具备循环引用防护与递归深度上限限制。
    """
    if data is None or max_depth <= 0:
        return data

    if isinstance(data, (int, float, bool)):
        return data

    if seen is None:
        seen = set()

    obj_id = id(data)
    if isinstance(data, (dict, list, tuple)):
        if obj_id in seen:
            return '<circular-reference>'
        seen.add(obj_id)

    try:
        # 处理字典类型
        if isinstance(data, dict):
            masked_dict = {}
            for k, v in data.items():
                if is_sensitive_key(k):
                    masked_dict[k] = '******'
                else:
                    masked_dict[k] = mask_sensitive_data(v, seen, max_depth - 1)
            return masked_dict

        # 处理列表与元组类型
        elif isinstance(data, (list, tuple)):
            masked_list = [mask_sensitive_data(item, seen, max_depth - 1) for item in data]
            return type(data)(masked_list) if isinstance(data, tuple) else masked_list

        # 处理嵌套 JSON 字符串
        elif isinstance(data, str):
            stripped = data.strip()
            if (stripped.startswith('{') and stripped.endswith('}')) or \
               (stripped.startswith('[') and stripped.endswith(']')):
                try:
                    parsed = json.loads(stripped)
                    if isinstance(parsed, (dict, list)):
                        masked_parsed = mask_sensitive_data(parsed, seen, max_depth - 1)
                        return json.dumps(masked_parsed, ensure_ascii=False)
                except Exception:
                    pass
            return data

        return data
    finally:
        if isinstance(data, (dict, list, tuple)) and obj_id in seen:
            seen.remove(obj_id)
