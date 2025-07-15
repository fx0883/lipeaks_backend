"""
租户和租户配额的序列化器
"""
from rest_framework import serializers
from tenants.models import Tenant, TenantQuota
from users.serializers import UserMinimalSerializer
from django.utils.translation import gettext_lazy as _

class TenantSerializer(serializers.ModelSerializer):
    """
    租户序列化器，用于列表展示
    """
    quota = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    has_business_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Tenant
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'is_deleted')
    
    def get_quota(self, obj):
        """获取租户配额"""
        try:
            return TenantQuotaSerializer(obj.quota).data
        except TenantQuota.DoesNotExist:
            return None
    
    def get_has_business_info(self, obj):
        """检查租户是否有企业信息"""
        # 始终返回 False，因为 TenantBusinessInfo 模型已被删除
        return False


class TenantCreateSerializer(serializers.ModelSerializer):
    """
    租户创建序列化器
    """
    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'contact_name', 'contact_email',
            'contact_phone', 'status'
        ]
        read_only_fields = ['id']


class TenantDetailSerializer(serializers.ModelSerializer):
    """
    租户详情序列化器，包含完整信息
    """
    user_count = serializers.SerializerMethodField()
    admin_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'status', 'contact_name', 'contact_email',
            'contact_phone', 'created_at', 'updated_at', 'user_count', 'admin_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user_count', 'admin_count']
    
    def get_user_count(self, obj) -> int:
        """获取租户用户数量"""
        return obj.users.filter(is_deleted=False).count()
    
    def get_admin_count(self, obj) -> int:
        """获取租户管理员数量"""
        return obj.users.filter(is_deleted=False, is_admin=True).count()


class TenantQuotaSerializer(serializers.ModelSerializer):
    """
    租户配额序列化器
    """
    usage_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = TenantQuota
        exclude = ('tenant',)
        read_only_fields = ('current_storage_used_mb', 'created_at', 'updated_at')
    
    def get_usage_percentage(self, obj):
        """
        计算各项资源的使用百分比
        """
        return {
            'users': obj.get_usage_percentage('users'),
            'admins': obj.get_usage_percentage('admins'),
            'storage': obj.get_usage_percentage('storage'),
            'products': obj.get_usage_percentage('products')
        }


class TenantQuotaUpdateSerializer(serializers.ModelSerializer):
    """
    租户配额更新序列化器
    """
    class Meta:
        model = TenantQuota
        fields = ['max_users', 'max_admins', 'max_storage_mb', 'max_products']


class TenantQuotaUsageSerializer(serializers.ModelSerializer):
    """
    租户配额使用情况序列化器
    """
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    usage_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = TenantQuota
        fields = [
            'tenant', 'tenant_name', 'max_users', 'max_admins', 
            'max_storage_mb', 'max_products', 'current_storage_used_mb',
            'usage_percentage'
        ]
        read_only_fields = fields
    
    def get_usage_percentage(self, obj):
        """
        获取各项资源的使用百分比
        """
        return {
            'users': obj.get_usage_percentage('users'),
            'admins': obj.get_usage_percentage('admins'),
            'storage': obj.get_usage_percentage('storage'),
            'products': obj.get_usage_percentage('products')
        }


class TenantSimpleSerializer(serializers.ModelSerializer):
    """
    简化版租户序列化器，用于列表展示
    """
    class Meta:
        model = Tenant
        fields = ('id', 'name', 'code', 'status')


class TenantComprehensiveSerializer(serializers.ModelSerializer):
    """
    全面的租户详细信息序列化器，包含租户所有关联信息
    """
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    quota = serializers.SerializerMethodField()
    business_info = serializers.SerializerMethodField()
    user_count = serializers.SerializerMethodField()
    admin_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'code', 'status', 'status_display', 
            'contact_name', 'contact_email', 'contact_phone', 
            'created_at', 'updated_at', 'is_active',
            'user_count', 'admin_count', 'quota', 'business_info'
        ]
        read_only_fields = fields
    
    def get_user_count(self, obj) -> int:
        """获取租户用户数量"""
        return obj.users.filter(is_deleted=False).count()
    
    def get_admin_count(self, obj) -> int:
        """获取租户管理员数量"""
        return obj.users.filter(is_deleted=False, is_admin=True).count()
    
    def get_quota(self, obj):
        """获取租户配额信息"""
        try:
            quota = obj.quota
            return {
                'max_users': quota.max_users,
                'max_admins': quota.max_admins,
                'max_storage_mb': quota.max_storage_mb,
                'max_products': quota.max_products,
                'current_storage_used_mb': quota.current_storage_used_mb,
                'usage_percentage': {
                    'users': quota.get_usage_percentage('users'),
                    'admins': quota.get_usage_percentage('admins'),
                    'storage': quota.get_usage_percentage('storage'),
                    'products': quota.get_usage_percentage('products')
                }
            }
        except TenantQuota.DoesNotExist:
            return None
    
    def get_business_info(self, obj):
        """获取租户企业信息"""
        # TenantBusinessInfo 模型已被删除，始终返回 None
        return None 