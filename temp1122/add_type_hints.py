#!/usr/bin/env python3
"""
批量为licenses/serializers.py添加类型提示
"""
import re

# 定义需要添加装饰器的方法及其返回类型
method_types = {
    # SoftwareProductSerializer / ApplicationSerializer  
    'get_license_plans_count': 'IntegerField',
    'get_total_licenses': 'IntegerField',
    'get_max_activations': 'IntegerField',
    'get_offline_days': 'IntegerField',
    
    # LicensePlanSerializer
    'get_licenses_count': 'IntegerField',
    
    # LicenseSerializer / LicenseDetailSerializer
    'get_machine_bindings_count': 'IntegerField',
    'get_days_until_expiry': 'IntegerField(allow_null=True)',
    'get_machine_bindings': 'ListField(child=serializers.DictField())',
    'get_recent_activations': 'ListField(child=serializers.DictField())',
    'get_usage_stats': 'DictField',
    
    # MachineBindingSerializer
    'get_license_key_preview': 'CharField',
    'get_days_since_last_seen': 'IntegerField(allow_null=True)',
    
    # LicenseActivationSerializer (get_license_key_preview重复)
    
    # SecurityAuditLogSerializer (get_license_key_preview重复)
    
    # TenantLicenseQuotaSerializer
    'get_usage_percentage': 'FloatField',
    
    # LicenseAssignmentSerializer
    'get_member_info': 'DictField(allow_null=True)',
    'get_license_info': 'DictField(allow_null=True)',
    'get_tenant_info': 'DictField(allow_null=True)',
    'get_assigned_by_info': 'DictField(allow_null=True)',
    'get_revoked_by_info': 'DictField(allow_null=True)',
    'get_is_expired': 'BooleanField',
    'get_effective_permissions': 'DictField',
    'get_usage_summary': 'DictField',
    
    # ApplicationTrialInfoSerializer
    'get_trial_plans': 'ListField(child=serializers.DictField(), allow_null=True)',
    'get_already_applied': 'BooleanField',
    
    # UserMemberLicenseAssignmentSerializer
    'get_can_activate_license': 'BooleanField',
    'get_activation_info': 'DictField',
    
    # MachineBindingDetailSerializer
    'get_os_name': 'CharField',
}

file_path = '/Users/fengxuan/Documents/Github/lipeaks_backend/licenses/serializers.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 为每个方法添加装饰器
for method_name, field_type in method_types.items():
    # 构造正则表达式，匹配没有装饰器的方法定义
    pattern = r'(\n    )(def ' + re.escape(method_name) + r'\(self, obj\):)'
    replacement = r'\1@extend_schema_field(serializers.' + field_type + r'())\n    \2'
    
    content = re.sub(pattern, replacement, content)

# 写回文件
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print(f"✅ 已为 {len(method_types)} 个方法添加类型提示")
