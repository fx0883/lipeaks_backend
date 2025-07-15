"""
RBAC系统序列化器
"""
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field, OpenApiTypes, extend_schema_serializer

from .models import Permission, Role, RolePermission, UserRole

class PermissionSerializer(serializers.ModelSerializer):
    """
    权限序列化器
    """
    class Meta:
        model = Permission
        fields = ['id', 'code', 'name', 'description', 'category', 'is_system', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
        extra_kwargs = {
            'is_system': {'read_only': True}  # 防止API直接创建系统权限
        }

    def validate_code(self, value):
        """验证权限代码格式"""
        if ':' not in value:
            raise serializers.ValidationError("权限代码应采用'resource:action'格式")
        return value

    def validate(self, attrs):
        """
        验证权限数据
        - 系统权限不允许修改为非系统权限
        - 非管理员不允许创建系统权限
        """
        instance = getattr(self, 'instance', None)
        
        # 如果是更新操作且正在修改的是系统权限
        if instance and instance.is_system:
            # 不允许将系统权限改为非系统权限
            if 'is_system' in attrs and not attrs['is_system']:
                raise serializers.ValidationError({"is_system": "不允许将系统权限修改为非系统权限"})
        
        return attrs


class RoleSerializer(serializers.ModelSerializer):
    """
    角色序列化器
    """
    permissions_count = serializers.SerializerMethodField()
    tenant_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Role
        fields = ['id', 'name', 'code', 'description', 'tenant', 'tenant_name', 
                  'is_system', 'permissions_count', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'permissions_count', 'tenant_name']
        extra_kwargs = {
            'is_system': {'read_only': True}  # 防止API直接创建系统角色
        }

    @extend_schema_field(OpenApiTypes.INT)
    def get_permissions_count(self, obj):
        """获取角色拥有的权限数量"""
        return obj.permissions.count()

    @extend_schema_field(OpenApiTypes.STR)
    def get_tenant_name(self, obj):
        """获取租户名称"""
        if obj.tenant:
            return obj.tenant.name
        return "系统"
    
    def validate(self, attrs):
        """
        验证角色数据
        - 系统角色不允许修改租户
        """
        instance = getattr(self, 'instance', None)
        
        # 如果是更新操作且正在修改的是系统角色
        if instance and instance.is_system:
            # 不允许修改系统角色的租户
            if 'tenant' in attrs and attrs['tenant'] != instance.tenant:
                raise serializers.ValidationError({"tenant": "不允许修改系统角色的租户"})
        
        return attrs


class RoleDetailSerializer(RoleSerializer):
    """
    角色详情序列化器，包含权限详情
    """
    permissions = PermissionSerializer(many=True, read_only=True)
    
    class Meta(RoleSerializer.Meta):
        fields = RoleSerializer.Meta.fields + ['permissions']


class RolePermissionSerializer(serializers.Serializer):
    """
    角色权限管理序列化器
    """
    permission_ids = serializers.ListField(
        child=serializers.IntegerField(),
        help_text="权限ID列表"
    )

    def validate_permission_ids(self, value):
        """验证权限ID是否存在"""
        existing_ids = set(Permission.objects.filter(id__in=value).values_list('id', flat=True))
        missing_ids = set(value) - existing_ids
        if missing_ids:
            raise serializers.ValidationError(f"权限不存在: {', '.join(map(str, missing_ids))}")
        return value


class UserRoleSerializer(serializers.ModelSerializer):
    """
    用户角色关联序列化器
    """
    role_name = serializers.CharField(source='role.name', read_only=True)
    user_name = serializers.SerializerMethodField()
    
    class Meta:
        model = UserRole
        fields = ['id', 'user_type', 'user_id', 'role', 'role_name', 'user_name',
                  'is_active', 'start_date', 'end_date', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'user_name', 'role_name']

    @extend_schema_field(OpenApiTypes.STR)
    def get_user_name(self, obj):
        """获取用户名称"""
        user = obj.user
        if user:
            return getattr(user, 'username', str(user))
        return f"{obj.get_user_type_display()} ID:{obj.user_id}"
    
    def validate(self, attrs):
        """
        验证用户角色关联数据
        - 检查日期范围是否有效
        """
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({"end_date": "结束日期必须大于等于开始日期"})
        
        return attrs


class UserRoleCreateSerializer(serializers.Serializer):
    """
    创建用户角色关联序列化器
    """
    role_id = serializers.IntegerField()
    is_active = serializers.BooleanField(default=True)
    start_date = serializers.DateField(required=False, allow_null=True)
    end_date = serializers.DateField(required=False, allow_null=True)
    
    def validate_role_id(self, value):
        """验证角色ID是否存在"""
        if not Role.objects.filter(id=value).exists():
            raise serializers.ValidationError(f"角色ID {value} 不存在")
        return value
    
    def validate(self, attrs):
        """
        验证用户角色关联数据
        - 检查日期范围是否有效
        """
        start_date = attrs.get('start_date')
        end_date = attrs.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({"end_date": "结束日期必须大于等于开始日期"})
        
        return attrs


class PermissionBatchCheckSerializer(serializers.Serializer):
    """
    批量检查权限序列化器
    """
    codes = serializers.ListField(
        child=serializers.CharField(),
        help_text="权限代码列表"
    )


class PermissionCheckResponseSerializer(serializers.Serializer):
    """
    权限检查响应序列化器
    """
    has_permission = serializers.BooleanField(help_text="是否拥有权限")
    permission_code = serializers.CharField(help_text="权限代码")


class PermissionBatchCheckResponseSerializer(serializers.Serializer):
    """
    批量权限检查响应序列化器
    """
    permissions = serializers.DictField(
        child=serializers.BooleanField(),
        help_text="权限检查结果，键为权限代码，值为是否拥有权限"
    )


class CacheRefreshResponseSerializer(serializers.Serializer):
    """
    缓存刷新响应序列化器
    """
    success = serializers.BooleanField()
    message = serializers.CharField()


class TenantRoleCreateFromTemplateSerializer(serializers.Serializer):
    """
    从模板创建租户角色序列化器
    """
    template_role_id = serializers.IntegerField(help_text="系统角色模板ID")
    name = serializers.CharField(required=False, help_text="租户特定角色名称，默认使用模板名称")
    code = serializers.CharField(required=False, help_text="租户特定角色代码，默认使用模板代码") 
    description = serializers.CharField(required=False, help_text="租户特定角色描述，默认使用模板描述")
    
    def validate_template_role_id(self, value):
        """验证模板角色ID是否存在且是系统角色"""
        try:
            role = Role.objects.get(id=value)
            if role.tenant is not None:
                raise serializers.ValidationError("模板角色必须是系统角色")
            return value
        except Role.DoesNotExist:
            raise serializers.ValidationError(f"系统角色ID {value} 不存在") 