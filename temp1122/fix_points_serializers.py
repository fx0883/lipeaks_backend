#!/usr/bin/env python3
"""
为points/api/serializers.py添加类型提示
"""
import re

file_path = '/Users/fengxuan/Documents/Github/lipeaks_backend/points/api/serializers.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 添加导入
if 'from drf_spectacular.utils import extend_schema_field' not in content:
    content = content.replace(
        'from rest_framework import serializers',
        'from rest_framework import serializers\nfrom drf_spectacular.utils import extend_schema_field'
    )

# 2. 为每个方法添加装饰器
method_types = {
    'get_member_info': 'DictField(allow_null=True)',
    'get_tenant_info': 'DictField(allow_null=True)',
    'get_profile_info': 'DictField(allow_null=True)',
    'get_is_expired': 'BooleanField',
    'get_days_until_expiry': 'IntegerField(allow_null=True)',
    'get_current_level_info': 'DictField(allow_null=True)',
    'get_points_summary': 'DictField',
    'get_active_tags': 'ListField(child=serializers.DictField())',
    'get_effective_permissions': 'DictField',
    'get_tag_info': 'DictField(allow_null=True)',
    'get_vip_status': 'DictField',
    'get_usage_summary': 'DictField',
}

for method_name, field_type in method_types.items():
    pattern = r'(\n    )(def ' + re.escape(method_name) + r'\(self, obj\):)'
    replacement = r'\1@extend_schema_field(serializers.' + field_type + r')\n    \2'
    content = re.sub(pattern, replacement, content)

# 写回文件
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✅ 已为 points/api/serializers.py 添加类型提示")
