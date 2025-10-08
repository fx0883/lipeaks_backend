"""
许可证系统API序列化器
提供数据序列化和验证功能
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from licenses.models import (
    SoftwareProduct, LicensePlan, License, MachineBinding, 
    LicenseActivation, LicenseUsageLog, TenantLicenseQuota, 
    SecurityAuditLog, LicenseAssignment
)
import json

User = get_user_model()


class SoftwareProductSerializer(serializers.ModelSerializer):
    """软件产品序列化器"""
    
    license_plans_count = serializers.SerializerMethodField()
    total_licenses = serializers.SerializerMethodField()
    
    class Meta:
        model = SoftwareProduct
        fields = [
            'id', 'name', 'code', 'description', 'version',
            'max_activations', 'offline_days', 'status',
            'license_plans_count', 'total_licenses',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_license_plans_count(self, obj):
        """获取许可方案数量"""
        return obj.license_plans.filter(status='active').count()
    
    def get_total_licenses(self, obj):
        """获取许可证总数"""
        return obj.licenses.count()
    
    def validate_code(self, value):
        """验证产品代码唯一性"""
        if self.instance and self.instance.code == value:
            return value
        
        if SoftwareProduct.objects.filter(code=value, is_deleted=False).exists():
            raise serializers.ValidationError("产品代码已存在")
        return value


class SoftwareProductCreateSerializer(serializers.ModelSerializer):
    """软件产品创建序列化器"""
    
    generate_keypair = serializers.BooleanField(default=True, write_only=True)
    
    class Meta:
        model = SoftwareProduct
        fields = [
            'name', 'code', 'description', 'version',
            'max_activations', 'offline_days', 'generate_keypair'
        ]
    
    def create(self, validated_data):
        """创建产品时自动生成密钥对"""
        generate_keypair = validated_data.pop('generate_keypair', True)
        
        if generate_keypair:
            from licenses.services.security_service import SecurityService
            security_service = SecurityService()
            
            # 生成RSA密钥对
            private_key_pem, public_key_pem = security_service.rsa_manager.generate_keypair()
            
            # 计算私钥哈希
            private_key_hash = security_service.hash_manager.hash_data(
                private_key_pem.decode()
            )
            
            validated_data['public_key'] = public_key_pem.decode()
            validated_data['private_key_hash'] = private_key_hash
        
        return super().create(validated_data)


class LicensePlanSerializer(serializers.ModelSerializer):
    """许可证方案序列化器"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    licenses_count = serializers.SerializerMethodField()
    
    class Meta:
        model = LicensePlan
        fields = [
            'id', 'product', 'product_name', 'name', 'code', 'plan_type',
            'default_max_activations', 'default_validity_days', 'features', 'price', 'currency',
            'status', 'licenses_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_licenses_count(self, obj):
        """获取该方案的许可证数量"""
        return obj.licenses.count()
    
    def validate(self, data):
        """验证方案代码在产品内唯一"""
        if self.instance:
            product = data.get('product', self.instance.product)
            code = data.get('code', self.instance.code)
            
            existing = LicensePlan.objects.filter(
                product=product, 
                code=code,
                is_deleted=False
            ).exclude(id=self.instance.id)
        else:
            product = data.get('product')
            code = data.get('code')
            
            existing = LicensePlan.objects.filter(
                product=product,
                code=code, 
                is_deleted=False
            )
        
        if existing.exists():
            raise serializers.ValidationError("方案代码在该产品下已存在")
        
        return data


class LicenseSerializer(serializers.ModelSerializer):
    """许可证序列化器（列表显示）"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    plan_name = serializers.CharField(source='plan.name', read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    machine_bindings_count = serializers.SerializerMethodField()
    days_until_expiry = serializers.SerializerMethodField()
    
    class Meta:
        model = License
        fields = [
            'id', 'product', 'product_name', 'plan', 'plan_name',
            'tenant', 'tenant_name', 'license_key', 'customer_name',
            'customer_email', 'max_activations', 'current_activations',
            'issued_at', 'expires_at', 'last_verified_at', 'status',
            'machine_bindings_count', 'days_until_expiry', 'notes'
        ]
        read_only_fields = [
            'id', 'license_key', 'issued_at', 'current_activations',
            'last_verified_at'
        ]
    
    def get_machine_bindings_count(self, obj):
        """获取活跃机器绑定数量"""
        return obj.machine_bindings.filter(status='active').count()
    
    def get_days_until_expiry(self, obj):
        """获取距离过期的天数"""
        if obj.expires_at:
            delta = obj.expires_at - timezone.now()
            return delta.days
        return None
    
    def validate(self, data):
        """验证product和plan的一致性"""
        product = data.get('product')
        plan = data.get('plan')
        
        # 对于更新操作，如果没有提供某个字段，使用实例的现有值
        if self.instance:
            if not product:
                product = self.instance.product
            if not plan:
                plan = self.instance.plan
        
        if product and plan:
            if plan.product != product:
                raise serializers.ValidationError({
                    'plan': f'所选方案({plan.name})属于产品({plan.product.name})，与所选产品({product.name})不一致，请重新选择正确的方案。'
                })
        
        # 如果只有plan没有product，自动设置product
        if plan and not product:
            data['product'] = plan.product
        
        return data


class LicenseDetailSerializer(LicenseSerializer):
    """许可证详情序列化器"""
    
    machine_bindings = serializers.SerializerMethodField()
    recent_activations = serializers.SerializerMethodField()
    usage_stats = serializers.SerializerMethodField()
    
    class Meta(LicenseSerializer.Meta):
        fields = LicenseSerializer.Meta.fields + [
            'machine_bindings', 'recent_activations', 'usage_stats', 'metadata'
        ]
    
    def get_machine_bindings(self, obj):
        """获取机器绑定信息"""
        bindings = obj.machine_bindings.all()[:5]  # 最多显示5个
        return MachineBindingSerializer(bindings, many=True).data
    
    def get_recent_activations(self, obj):
        """获取最近激活记录"""
        activations = obj.activations.order_by('-activated_at')[:5]
        return LicenseActivationSerializer(activations, many=True).data
    
    def get_usage_stats(self, obj):
        """获取使用统计"""
        thirty_days_ago = timezone.now() - timedelta(days=30)
        return {
            'total_usage_logs': obj.usage_logs.count(),
            'recent_usage_logs': obj.usage_logs.filter(
                timestamp__gte=thirty_days_ago
            ).count()
        }


class LicenseCreateSerializer(serializers.ModelSerializer):
    """许可证创建序列化器"""
    
    customer_info = serializers.JSONField(write_only=True)
    validity_days = serializers.IntegerField(required=False, write_only=True)
    product = serializers.PrimaryKeyRelatedField(
        queryset=SoftwareProduct.objects.filter(is_deleted=False),
        required=False,
        help_text="产品ID，如果未提供将从plan字段自动获取"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 动态添加tenant字段
        from tenants.models import Tenant
        self.fields['tenant'] = serializers.PrimaryKeyRelatedField(
            queryset=Tenant.objects.filter(is_deleted=False),
            required=False,
            allow_null=True,
            help_text="租户ID，如果未提供将从当前用户自动获取"
        )
    
    class Meta:
        model = License
        fields = [
            'product', 'plan', 'tenant', 'customer_info',
            'max_activations', 'validity_days', 'notes'
        ]
    
    def validate_customer_info(self, value):
        """验证客户信息格式"""
        required_fields = ['name', 'email']
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"客户信息缺少必要字段: {field}")
        return value
    
    def validate(self, data):
        """验证product和plan的一致性"""
        product = data.get('product')
        plan = data.get('plan')
        
        if product and plan:
            if plan.product != product:
                raise serializers.ValidationError({
                    'plan': f'所选方案({plan.name})属于产品({plan.product.name})，与所选产品({product.name})不一致，请重新选择正确的方案。'
                })
        
        # 如果只有plan没有product，自动设置product
        if plan and not product:
            data['product'] = plan.product
        
        return data
    
    def create(self, validated_data):
        """创建许可证"""
        from licenses.services.license_service import LicenseManagementService
        
        customer_info = validated_data.pop('customer_info')
        validity_days = validated_data.pop('validity_days', None)
        
        # 从validated_data中获取必要字段（这些字段可能通过perform_create自动填充）
        product = validated_data.get('product')
        plan = validated_data.get('plan')  
        tenant = validated_data.get('tenant')
        
        # 验证必要字段是否存在
        if not product:
            raise serializers.ValidationError("product字段是必需的")
        if not plan:
            raise serializers.ValidationError("plan字段是必需的") 
        if not tenant:
            raise serializers.ValidationError("tenant字段是必需的")
        
        # 计算过期时间
        expires_at = None
        if validity_days:
            expires_at = timezone.now() + timedelta(days=validity_days)
        
        # 使用服务创建许可证
        management_service = LicenseManagementService()
        license_obj = management_service.create_license(
            product_id=product.id,
            plan_id=plan.id,
            tenant_id=tenant.id,
            customer_info=customer_info,
            expires_at=expires_at,
            max_activations=validated_data.get('max_activations')
        )
        
        return license_obj


class MachineBindingSerializer(serializers.ModelSerializer):
    """机器绑定序列化器"""
    
    license_key_preview = serializers.SerializerMethodField()
    hardware_summary = serializers.JSONField(read_only=True)
    days_since_last_seen = serializers.SerializerMethodField()
    
    class Meta:
        model = MachineBinding
        fields = [
            'id', 'license', 'license_key_preview', 'machine_id',
            'hardware_summary', 'os_info', 'last_ip_address',
            'status', 'first_seen_at', 'last_seen_at', 'days_since_last_seen'
        ]
        read_only_fields = [
            'id', 'machine_id', 'first_seen_at', 'last_seen_at'
        ]
    
    def get_license_key_preview(self, obj):
        """获取许可证密钥预览"""
        key = obj.license.license_key
        if len(key) > 10:
            return f"{key[:5]}...{key[-5:]}"
        return key
    
    def get_days_since_last_seen(self, obj):
        """获取距离最后活跃的天数"""
        if obj.last_seen_at:
            delta = timezone.now() - obj.last_seen_at
            return delta.days
        return None


class LicenseActivationSerializer(serializers.ModelSerializer):
    """许可证激活序列化器"""
    
    license_key_preview = serializers.SerializerMethodField()
    machine_id = serializers.CharField(source='machine_binding.machine_id', read_only=True)
    
    class Meta:
        model = LicenseActivation
        fields = [
            'id', 'license', 'license_key_preview', 'machine_id',
            'activation_type', 'activation_code', 'client_version',
            'ip_address', 'result', 'error_message',
            'activated_at', 'expires_at'
        ]
        read_only_fields = [
            'id', 'activation_code', 'activated_at'
        ]
    
    def get_license_key_preview(self, obj):
        """获取许可证密钥预览"""
        key = obj.license.license_key
        if len(key) > 10:
            return f"{key[:5]}...{key[-5:]}"
        return key


class ActivateLicenseSerializer(serializers.Serializer):
    """激活许可证请求序列化器"""
    
    license_key = serializers.CharField(max_length=200)
    hardware_info = serializers.JSONField()
    client_info = serializers.JSONField(required=False)
    
    def validate_license_key(self, value):
        """验证许可证密钥格式"""
        # 移除格式化字符
        clean_key = value.replace('-', '').replace(' ', '')
        if len(clean_key) < 10:
            raise serializers.ValidationError("许可证密钥格式无效")
        return value
    
    def validate_hardware_info(self, value):
        """验证硬件信息完整性"""
        required_fields = ['hardware_uuid', 'system_info']
        for field in required_fields:
            if field not in value:
                raise serializers.ValidationError(f"硬件信息缺少必要字段: {field}")
        return value


class VerifyActivationSerializer(serializers.Serializer):
    """验证激活状态请求序列化器"""
    
    activation_code = serializers.CharField(max_length=100)
    machine_fingerprint = serializers.CharField(
        max_length=64, 
        required=False, 
        allow_blank=True,
        help_text="机器指纹（可选，不进行验证）"
    )


class LicenseUsageLogSerializer(serializers.ModelSerializer):
    """许可证使用日志序列化器"""
    
    license_key_preview = serializers.SerializerMethodField()
    machine_id = serializers.CharField(source='machine_binding.machine_id', read_only=True)
    
    class Meta:
        model = LicenseUsageLog
        fields = [
            'id', 'license', 'license_key_preview', 'machine_id',
            'event_type', 'event_data', 'software_version', 'session_id',
            'cpu_usage', 'memory_usage', 'ip_address', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']
    
    def get_license_key_preview(self, obj):
        """获取许可证密钥预览"""
        key = obj.license.license_key
        if len(key) > 10:
            return f"{key[:5]}...{key[-5:]}"
        return key


class HeartbeatSerializer(serializers.Serializer):
    """心跳检测请求序列化器"""
    
    activation_code = serializers.CharField(max_length=100)
    event_type = serializers.ChoiceField(choices=LicenseUsageLog.EVENT_TYPES)
    event_data = serializers.JSONField(required=False, default=dict)
    software_version = serializers.CharField(max_length=50, required=False)
    session_id = serializers.CharField(max_length=100, required=False)
    system_status = serializers.JSONField(required=False, default=dict)


class UnbindLicenseSerializer(serializers.Serializer):
    """许可证解绑请求序列化器"""
    
    activation_code = serializers.CharField(
        max_length=100,
        help_text="激活码，格式：XXXX-XXXX-XXXX-XXXX"
    )
    license_key = serializers.CharField(
        max_length=200,
        help_text="许可证密钥，格式：XXXXX-XXXXX-XXXXX-XXXXX-XXXXX"
    )
    machine_fingerprint = serializers.CharField(
        max_length=128,  # 增加长度限制，允许更灵活的格式
        required=False,  # 改为可选字段
        allow_blank=True,  # 允许空白
        help_text="机器指纹，用于记录和日志（可选，不进行格式验证）"
    )
    hardware_info = serializers.JSONField(
        required=False,
        help_text="机器硬件信息，用于额外验证"
    )
    reason = serializers.CharField(
        max_length=500,
        required=False,
        default="用户主动解绑",
        help_text="解绑原因"
    )
    
    def validate_activation_code(self, value):
        """验证激活码格式"""
        # 移除格式化字符
        clean_code = value.replace('-', '').replace(' ', '')
        if len(clean_code) < 8:
            raise serializers.ValidationError("激活码格式无效")
        return value
    
    def validate_license_key(self, value):
        """验证许可证密钥格式"""
        # 移除格式化字符
        clean_key = value.replace('-', '').replace(' ', '')
        if len(clean_key) < 10:
            raise serializers.ValidationError("许可证密钥格式无效")
        return value
    
    def validate_machine_fingerprint(self, value):
        """验证机器指纹格式（已禁用验证）"""
        # TODO: 指纹码验证已完全禁用
        # if len(value) != 64:
        #     raise serializers.ValidationError("机器指纹长度必须为64位")
        return value


class TenantLicenseQuotaSerializer(serializers.ModelSerializer):
    """租户许可证配额序列化器"""
    
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    usage_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = TenantLicenseQuota
        fields = [
            'id', 'tenant', 'tenant_name', 'product', 'product_name',
            'max_licenses', 'current_licenses', 'quota_start_date',
            'quota_end_date', 'is_active', 'usage_percentage'
        ]
        read_only_fields = ['id', 'current_licenses']
    
    def get_usage_percentage(self, obj):
        """获取配额使用百分比"""
        if obj.max_licenses > 0:
            return round((obj.current_licenses / obj.max_licenses) * 100, 2)
        return 0


class SecurityAuditLogSerializer(serializers.ModelSerializer):
    """安全审计日志序列化器"""
    
    user_name = serializers.CharField(source='user.username', read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    
    class Meta:
        model = SecurityAuditLog
        fields = [
            'id', 'event_type', 'severity', 'user', 'user_name',
            'tenant', 'tenant_name', 'ip_address', 'user_agent',
            'details', 'timestamp'
        ]
        read_only_fields = ['id', 'timestamp']


class LicenseReportSerializer(serializers.Serializer):
    """许可证报告序列化器"""
    
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    product_id = serializers.IntegerField(required=False)
    tenant_id = serializers.IntegerField(required=False)
    report_type = serializers.ChoiceField(
        choices=['usage', 'activation', 'security', 'summary'],
        default='summary'
    )
    
    def validate(self, data):
        """验证日期范围"""
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date:
            if start_date > end_date:
                raise serializers.ValidationError("开始日期不能晚于结束日期")
            
            # 限制报告时间范围不超过1年
            if (end_date - start_date).days > 365:
                raise serializers.ValidationError("报告时间范围不能超过1年")
        
        return data


class BatchOperationSerializer(serializers.Serializer):
    """批量操作序列化器"""
    
    license_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        max_length=100
    )
    operation = serializers.ChoiceField(
        choices=['revoke', 'suspend', 'activate', 'extend', 'delete']
    )
    parameters = serializers.JSONField(required=False, default=dict)
    reason = serializers.CharField(max_length=500, required=False)
    
    def validate_license_ids(self, value):
        """验证许可证ID存在"""
        existing_ids = License.objects.filter(
            id__in=value,
            is_deleted=False
        ).values_list('id', flat=True)
        
        invalid_ids = set(value) - set(existing_ids)
        if invalid_ids:
            raise serializers.ValidationError(
                f"以下许可证ID不存在: {list(invalid_ids)}"
            )
        
        return value


class LicenseAssignmentSerializer(serializers.ModelSerializer):
    """许可证分配序列化器"""
    
    # 关联对象信息
    member_info = serializers.SerializerMethodField()
    license_info = serializers.SerializerMethodField()
    tenant_info = serializers.SerializerMethodField()
    assigned_by_info = serializers.SerializerMethodField()
    revoked_by_info = serializers.SerializerMethodField()
    
    # 计算字段
    is_expired = serializers.SerializerMethodField()
    days_until_expiry = serializers.SerializerMethodField()
    effective_permissions = serializers.SerializerMethodField()
    usage_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = LicenseAssignment
        fields = [
            'id', 'member', 'license', 'tenant', 'assignment_type',
            'assignment_reason', 'priority', 'can_activate', 'can_deactivate',
            'can_share', 'max_devices_per_user', 'assigned_at', 'activated_at',
            'expires_at', 'last_used_at', 'status', 'is_primary', 'usage_count',
            'last_heartbeat', 'revoked_at', 'revoke_reason', 'assignment_metadata',
            'assigned_by', 'revoked_by', 'created_at', 'updated_at',
            # 计算字段
            'member_info', 'license_info', 'tenant_info', 'assigned_by_info',
            'revoked_by_info', 'is_expired', 'days_until_expiry',
            'effective_permissions', 'usage_summary'
        ]
        read_only_fields = [
            'id', 'assigned_at', 'activated_at', 'last_used_at', 'usage_count',
            'last_heartbeat', 'revoked_at', 'created_at', 'updated_at',
            'member_info', 'license_info', 'tenant_info', 'assigned_by_info',
            'revoked_by_info', 'is_expired', 'days_until_expiry',
            'effective_permissions', 'usage_summary'
        ]
    
    def get_member_info(self, obj):
        """获取成员基本信息"""
        if obj.member:
            return {
                'id': obj.member.id,
                'username': obj.member.username,
                'email': obj.member.email,
                'is_active': obj.member.is_active,
            }
        return None
    
    def get_license_info(self, obj):
        """获取许可证基本信息"""
        if obj.license:
            return {
                'id': obj.license.id,
                'license_key': obj.license.license_key[-8:] if obj.license.license_key else None,  # 只显示后8位
                'product_name': obj.license.product.name if obj.license.product else None,
                'plan_name': obj.license.plan.name if obj.license.plan else None,
                'status': obj.license.status,
                'max_activations': obj.license.max_activations,
                'current_activations': obj.license.current_activations,
                'expires_at': obj.license.expires_at,
            }
        return None
    
    def get_tenant_info(self, obj):
        """获取租户基本信息"""
        if obj.tenant:
            return {
                'id': obj.tenant.id,
                'name': obj.tenant.name,
                'is_active': obj.tenant.is_active,
            }
        return None
    
    def get_assigned_by_info(self, obj):
        """获取分配操作员信息"""
        if obj.assigned_by:
            return {
                'id': obj.assigned_by.id,
                'username': obj.assigned_by.username,
            }
        return None
    
    def get_revoked_by_info(self, obj):
        """获取撤销操作员信息"""
        if obj.revoked_by:
            return {
                'id': obj.revoked_by.id,
                'username': obj.revoked_by.username,
            }
        return None
    
    def get_is_expired(self, obj):
        """检查分配是否已过期"""
        return obj.is_expired()
    
    def get_days_until_expiry(self, obj):
        """计算距离过期的天数"""
        if obj.expires_at and obj.status == 'active':
            days = (obj.expires_at - timezone.now()).days
            return max(0, days)
        return None
    
    def get_effective_permissions(self, obj):
        """获取分配的有效权限"""
        return obj.get_effective_permissions()
    
    def get_usage_summary(self, obj):
        """获取使用情况摘要"""
        return {
            'usage_count': obj.usage_count,
            'last_used_at': obj.last_used_at,
            'last_heartbeat': obj.last_heartbeat,
            'is_primary': obj.is_primary,
            'can_activate': obj.can_activate,
            'can_deactivate': obj.can_deactivate,
            'can_share': obj.can_share,
            'max_devices_per_user': obj.max_devices_per_user,
        }


class LicenseAssignmentCreateSerializer(serializers.ModelSerializer):
    """许可证分配创建序列化器"""
    
    member_id = serializers.IntegerField(write_only=True, help_text="成员ID")
    license_id = serializers.IntegerField(write_only=True, help_text="许可证ID")
    
    class Meta:
        model = LicenseAssignment
        fields = [
            'member_id', 'license_id', 'assignment_type', 'assignment_reason',
            'priority', 'can_activate', 'can_deactivate', 'can_share',
            'max_devices_per_user', 'expires_at', 'assignment_metadata'
        ]
    
    def validate(self, data):
        """验证分配数据"""
        from users.models import Member
        
        # 获取当前用户的租户
        request = self.context.get('request')
        if not request or not hasattr(request.user, 'tenant'):
            raise serializers.ValidationError("无法确定当前用户的租户")
        
        user_tenant = request.user.tenant
        
        # 验证成员存在且属于同一租户
        try:
            member = Member.objects.get(id=data['member_id'], tenant=user_tenant)
            data['member'] = member
        except Member.DoesNotExist:
            raise serializers.ValidationError("指定的成员不存在或不属于当前租户")
        
        # 验证许可证存在且属于同一租户
        try:
            license_obj = License.objects.get(id=data['license_id'], tenant=user_tenant)
            data['license'] = license_obj
        except License.DoesNotExist:
            raise serializers.ValidationError("指定的许可证不存在或不属于当前租户")
        
        # 设置租户
        data['tenant'] = user_tenant
        
        # 检查是否已存在活跃分配
        existing = LicenseAssignment.objects.filter(
            member=member,
            license=license_obj,
            status='active'
        ).exists()
        
        if existing:
            raise serializers.ValidationError("该成员已拥有此许可证的活跃分配")
        
        # 检查许可证激活配额
        if license_obj.current_activations >= license_obj.max_activations:
            raise serializers.ValidationError("许可证激活配额已满")
        
        return data
    
    def create(self, validated_data):
        """创建许可证分配"""
        # 移除辅助字段
        validated_data.pop('member_id', None)
        validated_data.pop('license_id', None)
        
        # 设置分配操作员
        request = self.context.get('request')
        if request and request.user:
            validated_data['assigned_by'] = request.user
        
        return super().create(validated_data)


# =============================================================================
# Member用户试用申请相关序列化器
# =============================================================================

class AvailableProductSerializer(serializers.ModelSerializer):
    """可申请产品序列化器"""
    
    trial_plans = serializers.SerializerMethodField()  # 改为复数，返回所有方案
    already_applied = serializers.SerializerMethodField()
    
    class Meta:
        model = SoftwareProduct
        fields = [
            'id', 'name', 'code', 'description', 'version', 
            'trial_plans',  # 改为复数
            'already_applied'
        ]
    
    def get_trial_plans(self, obj):
        """获取所有试用方案（按有效期从长到短排序）"""
        trial_plans = obj.license_plans.filter(
            plan_type='trial', 
            status='active'
        ).order_by(
            '-default_validity_days',   # 优先：有效期从长到短
            '-default_max_activations'  # 其次：激活数从多到少
        )
        
        plans_data = []
        for index, plan in enumerate(trial_plans):
            plans_data.append({
                'id': plan.id,
                'name': plan.name,
                'default_validity_days': plan.default_validity_days,
                'default_max_activations': plan.default_max_activations,
                'features': plan.features,
                'price': float(plan.price) if plan.price else 0,
                'currency': plan.currency,
                'is_recommended': index == 0  # 第一个（有效期最长）标记为推荐
            })
        
        return plans_data if plans_data else None
    
    def get_already_applied(self, obj):
        """检查是否已经申请过（排除已删除的许可证）"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        return LicenseAssignment.objects.filter(
            member=request.user,
            license__product=obj,
            license__is_deleted=False,  # 排除已删除的许可证
            status__in=['active', 'pending']
        ).exists()


class LicenseApplicationSerializer(serializers.Serializer):
    """许可证申请序列化器"""
    
    product_id = serializers.IntegerField(
        help_text="产品ID"
    )
    plan_id = serializers.IntegerField(
        required=False,
        help_text="方案ID（可选）。如果产品有多个试用方案，可以指定要申请的方案ID；如果不指定，系统会自动选择有效期最长的方案"
    )
    reason = serializers.CharField(
        max_length=500, 
        required=False, 
        default="试用版申请",
        help_text="申请原因"
    )
    user_info = serializers.JSONField(
        required=False,
        help_text="用户补充信息，如：{'company': '公司名称', 'job_title': '职位', 'phone': '手机号', 'intended_use': '使用用途'}"
    )
    
    def validate_product_id(self, value):
        """验证产品ID"""
        try:
            product = SoftwareProduct.objects.get(
                id=value, 
                status='active',
                is_deleted=False
            )
            
            # 检查是否有试用方案
            trial_plan = product.license_plans.filter(
                plan_type='trial',
                status='active'
            ).first()
            
            if not trial_plan:
                raise serializers.ValidationError("该产品没有可用的试用方案")
            
            return value
            
        except SoftwareProduct.DoesNotExist:
            raise serializers.ValidationError("产品不存在或不可用")
    
    def validate_user_info(self, value):
        """验证用户补充信息"""
        if value:
            # 检查必要字段格式
            if 'phone' in value:
                phone = value['phone']
                if phone and len(phone) > 20:
                    raise serializers.ValidationError("手机号格式无效")
            
            if 'company' in value:
                company = value['company']
                if company and len(company) > 100:
                    raise serializers.ValidationError("公司名称过长")
            
            if 'intended_use' in value:
                intended_use = value['intended_use']
                if intended_use and len(intended_use) > 500:
                    raise serializers.ValidationError("使用用途描述过长")
        
        return value
    
    def validate(self, data):
        """验证申请数据"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("用户未认证")
        
        user = request.user
        product_id = data['product_id']
        
        # 检查重复申请（排除已删除的许可证）
        existing_application = LicenseAssignment.objects.filter(
            member=user,
            license__product_id=product_id,
            license__is_deleted=False,  # 排除已删除的许可证
            status__in=['active', 'pending']
        ).exists()
        
        if existing_application:
            raise serializers.ValidationError("您已经申请过该产品的许可证")
        
        # 检查申请频率（从配置文件获取限制）
        from datetime import timedelta
        from django.utils import timezone
        from licenses.config import APPLICATION_RATE_LIMITS
        
        business_limit = APPLICATION_RATE_LIMITS.get('business_limit', 3)
        cooldown_hours = APPLICATION_RATE_LIMITS.get('cooldown_hours', 24)
        
        recent_applications = LicenseAssignment.objects.filter(
            member=user,
            created_at__gte=timezone.now() - timedelta(hours=cooldown_hours)
        ).count()
        
        if recent_applications >= business_limit:
            raise serializers.ValidationError(f"{cooldown_hours}小时内申请次数过多，请稍后再试（当前限制: {business_limit}次）")
        
        # 检查用户当前试用许可证数量（默认限制：1个）
        current_trial_count = LicenseAssignment.objects.filter(
            member=user,
            license__plan__plan_type='trial',
            status='active'
        ).count()
        
        # 从配置文件获取默认配额
        from licenses.config import TRIAL_LICENSE_QUOTAS
        default_quota = TRIAL_LICENSE_QUOTAS.get('default', 1)
        max_trial_licenses = getattr(user, 'max_trial_licenses', default_quota)
        
        if current_trial_count >= max_trial_licenses:
            raise serializers.ValidationError(f"您的试用许可证数量已达上限（{max_trial_licenses}个）")
        
        return data


class MemberLicenseSerializer(serializers.ModelSerializer):
    """Member用户许可证序列化器"""
    
    product_name = serializers.CharField(source='license.product.name', read_only=True)
    product_code = serializers.CharField(source='license.product.code', read_only=True)
    product_version = serializers.CharField(source='license.product.version', read_only=True)
    plan_name = serializers.CharField(source='license.plan.name', read_only=True)
    plan_type = serializers.CharField(source='license.plan.plan_type', read_only=True)
    license_key_preview = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    days_until_expiry = serializers.SerializerMethodField()
    can_activate_license = serializers.SerializerMethodField()
    activation_info = serializers.SerializerMethodField()
    
    class Meta:
        model = LicenseAssignment
        fields = [
            'id', 'product_name', 'product_code', 'product_version',
            'plan_name', 'plan_type', 'license_key_preview', 
            'status', 'status_display', 'assignment_type',
            'assigned_at', 'activated_at', 'expires_at', 'days_until_expiry',
            'assignment_reason', 'can_activate_license', 'activation_info',
            'usage_count', 'last_used_at', 'last_heartbeat',
            'can_activate', 'can_deactivate', 'can_share', 'max_devices_per_user'
        ]
        read_only_fields = [
            'id', 'assigned_at', 'activated_at', 'usage_count',
            'last_used_at', 'last_heartbeat'
        ]
    
    def get_license_key_preview(self, obj):
        """许可证密钥预览（只显示部分）"""
        if obj.license and obj.license.license_key:
            key = obj.license.license_key
            if len(key) > 10:
                return f"{key[:5]}...{key[-5:]}"
            else:
                return f"{key[:3]}...{key[-2:]}"
        return None
    
    def get_days_until_expiry(self, obj):
        """距离过期的天数"""
        if obj.expires_at:
            from django.utils import timezone
            delta = obj.expires_at - timezone.now()
            return max(0, delta.days) if delta.total_seconds() > 0 else 0
        return None
    
    def get_can_activate_license(self, obj):
        """检查是否可以激活许可证"""
        if obj.status != 'active':
            return False
        
        # 检查许可证状态
        if obj.license.status not in ['generated', 'activated']:
            return False
        
        # 检查过期时间
        from django.utils import timezone
        now = timezone.now()
        if obj.expires_at and now > obj.expires_at:
            return False
        
        if obj.license.expires_at and now > obj.license.expires_at:
            return False
        
        return obj.can_activate
    
    def get_activation_info(self, obj):
        """获取激活信息"""
        if obj.license:
            return {
                'current_activations': obj.license.current_activations,
                'max_activations': obj.license.max_activations,
                'available_slots': max(0, obj.license.max_activations - obj.license.current_activations)
            }
        return None


class MemberLicenseListSerializer(serializers.Serializer):
    """Member许可证列表响应序列化器"""
    
    count = serializers.IntegerField(help_text="许可证总数")
    active_count = serializers.IntegerField(help_text="有效许可证数量")
    trial_count = serializers.IntegerField(help_text="试用版许可证数量")
    expiring_soon_count = serializers.IntegerField(help_text="即将过期许可证数量（7天内）")
    licenses = MemberLicenseSerializer(many=True, help_text="许可证列表")
    
    class Meta:
        fields = ['count', 'active_count', 'trial_count', 'expiring_soon_count', 'licenses']
