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
    SecurityAuditLog
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
            'max_machines', 'validity_days', 'features', 'price', 'currency',
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
        
        # 计算过期时间
        expires_at = None
        if validity_days:
            expires_at = timezone.now() + timedelta(days=validity_days)
        
        # 使用服务创建许可证
        management_service = LicenseManagementService()
        license_obj = management_service.create_license(
            product_id=validated_data['product'].id,
            plan_id=validated_data['plan'].id,
            tenant_id=validated_data['tenant'].id,
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
    machine_fingerprint = serializers.CharField(max_length=64)


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
        choices=['revoke', 'suspend', 'activate', 'extend']
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
