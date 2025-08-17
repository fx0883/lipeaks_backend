"""
用户序列化器
"""
import logging
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from users.models import User, Member, PasswordResetToken
from tenants.models import Tenant
from common.utils.image_url import add_domain_to_image_url

# 添加日志器
logger = logging.getLogger(__name__)

class UserSerializer(serializers.ModelSerializer):
    """
    用户序列化器
    """
    tenant_name = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    is_member = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone', 'nick_name', 'first_name', 
            'last_name', 'is_active', 'avatar', 'tenant', 'tenant_name', 
            'is_admin', 'is_member', 'is_super_admin', 'role', 'date_joined',
            'wechat_id'
        ]
        read_only_fields = ['id', 'date_joined', 'role', 'tenant_name', 'is_member']
        extra_kwargs = {
            'is_admin': {'read_only': True},
            'is_super_admin': {'read_only': True},
        }
    
    def get_tenant_name(self, obj) -> str:
        """获取租户名称"""
        if obj.tenant:
            return obj.tenant.name
        return None
    
    def get_role(self, obj) -> str:
        """获取用户角色"""
        return obj.display_role
    
    def get_is_member(self, obj) -> bool:
        """获取是否为普通成员"""
        # 对于User模型实例，默认不是普通成员
        return getattr(obj, 'is_member', False)
    
    def get_avatar(self, obj) -> str:
        """获取完整的头像URL"""
        if not obj.avatar:
            return ""
            
        # 如果已经是完整URL，直接返回
        if obj.avatar.startswith(('http://', 'https://')):
            return obj.avatar
            
        # 获取请求对象
        request = self.context.get('request')
        if request is not None:
            # 从请求中获取域名和协议
            protocol = 'https' if request.is_secure() else 'http'
            domain = request.get_host()
            # 确保路径以/开头
            path = obj.avatar if obj.avatar.startswith('/') else f'/{obj.avatar}'
            return f"{protocol}://{domain}{path}"
            
        # 如果无法获取请求对象，使用配置中的BASE_URL
        from django.conf import settings
        base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
        # 确保路径以/开头
        path = obj.avatar if obj.avatar.startswith('/') else f'/{obj.avatar}'
        return f"{base_url}{path}"


class UserCreateSerializer(serializers.ModelSerializer):
    """
    用户创建序列化器
    """
    password_confirm = serializers.CharField(write_only=True)
    tenant_id = serializers.PrimaryKeyRelatedField(
        queryset=Tenant.objects.all(),
        required=False,
        source='tenant',
        write_only=True
    )
    is_member = serializers.BooleanField(write_only=True, required=False, default=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'phone', 'nick_name', 'first_name',
            'last_name', 'password', 'password_confirm', 'tenant_id',
            'is_admin', 'is_member', 'avatar', 'wechat_id'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'id': {'read_only': True},
            'is_admin': {'write_only': True}
        }
    
    def validate(self, data):
        """
        验证密码一致性
        """
        if data['password'] != data.pop('password_confirm'):
            raise serializers.ValidationError({"password_confirm": "两次输入的密码不一致"})
        
        # 验证密码强度
        validate_password(data['password'])
        
        return data
    
    def create(self, validated_data):
        """
        创建用户
        """
        # 从validated_data中移除is_member字段，因为User模型中实际不存在这个字段
        is_member = validated_data.pop('is_member', True)
        
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        
        # 设置其他字段
        for field in ['phone', 'nick_name', 'first_name', 'last_name', 'tenant', 'avatar', 'wechat_id']:
            if field in validated_data:
                setattr(user, field, validated_data[field])
        
        # 设置角色
        user.is_admin = validated_data.get('is_admin', False)
        # 不需要设置is_member，因为User模型中没有这个字段
        
        user.save()
        return user


class SuperAdminCreateSerializer(UserCreateSerializer):
    """
    超级管理员创建序列化器
    """
    class Meta(UserCreateSerializer.Meta):
        fields = [
            'id', 'username', 'email', 'phone', 'nick_name', 'first_name',
            'last_name', 'password', 'password_confirm', 'avatar'
        ]
    
    def create(self, validated_data):
        """
        创建超级管理员
        """
        user = super().create(validated_data)
        user.is_super_admin = True
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.tenant = None  # 超级管理员不属于任何租户
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    用户更新序列化器
    """
    class Meta:
        model = User
        fields = [
            'id', 'phone', 'nick_name', 'first_name', 'last_name', 
            'avatar', 'is_active', 'status', 'wechat_id'
        ]
        read_only_fields = ['id']


class UserPasswordUpdateSerializer(serializers.Serializer):
    """
    用户密码更新序列化器
    """
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    new_password_confirm = serializers.CharField(required=True, write_only=True)
    
    def validate_old_password(self, value):
        """
        验证旧密码是否正确
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("旧密码不正确")
        return value
    
    def validate(self, data):
        """
        验证新密码的一致性和强度
        """
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({"new_password_confirm": "两次输入的新密码不一致"})
        
        # 验证新密码强度
        validate_password(data['new_password'])
        
        return data
    
    def save(self, **kwargs):
        """
        保存新密码
        """
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class ChangePasswordSerializer(serializers.Serializer):
    """
    修改密码序列化器
    """
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    new_password_confirm = serializers.CharField(required=True, write_only=True)
    
    def validate_old_password(self, value):
        """
        验证旧密码是否正确
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("旧密码不正确")
        return value
    
    def validate(self, data):
        """
        验证新密码的一致性和强度
        """
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({"new_password_confirm": "两次输入的新密码不一致"})
        
        # 验证新密码强度
        validate_password(data['new_password'])
        
        return data


class UserRoleUpdateSerializer(serializers.Serializer):
    """
    用户角色更新序列化器
    """
    is_admin = serializers.BooleanField(required=True)
    
    def validate(self, data):
        """
        验证角色变更权限
        """
        # 检查当前用户是否有权限更改角色
        request_user = self.context['request'].user
        target_user = self.instance
        
        # 只有超级管理员或同一租户的管理员可以更改角色
        if not request_user.is_super_admin and (
            not request_user.is_admin or 
            request_user.tenant != target_user.tenant
        ):
            raise serializers.ValidationError("您没有权限更改此用户的角色")
        
        # 不能取消自己的管理员权限
        if request_user == target_user and not data['is_admin'] and request_user.is_admin:
            raise serializers.ValidationError("您不能取消自己的管理员权限")
        
        # 租户管理员不能修改超级管理员的角色
        if target_user.is_super_admin and not request_user.is_super_admin:
            raise serializers.ValidationError("您不能修改超级管理员的角色")
        
        return data
    
    def update(self, instance, validated_data):
        """
        更新用户角色
        """
        # 如果用户变成管理员，检查配额
        if validated_data['is_admin'] and not instance.is_admin and instance.tenant:
            quota = instance.tenant.quota
            if not quota.can_add_user(is_admin=True):
                raise serializers.ValidationError({"is_admin": "租户管理员配额已满"})
        
        # 更新角色
        instance.is_admin = validated_data['is_admin']
        
        # 如果取消管理员角色，确保用户至少是普通成员
        if not instance.is_admin:
            instance.is_member = True
        
        instance.save()
        return instance


class UserRoleSerializer(serializers.ModelSerializer):
    """
    用户角色序列化器，用于更新用户角色
    """
    is_member = serializers.BooleanField(required=False)
    
    class Meta:
        model = User
        fields = ['id', 'is_admin', 'is_member']
        read_only_fields = ['id']
        
    def validate(self, data):
        """
        验证角色数据
        """
        # 检查是否至少有一个角色
        if not data.get('is_admin') and not data.get('is_member', True):
            raise serializers.ValidationError({"non_field_errors": "用户必须至少有一个角色"})
        return data
    
    def update(self, instance, validated_data):
        """
        更新用户角色
        """
        # 更新Admin角色
        instance.is_admin = validated_data.get('is_admin', instance.is_admin)
        
        # 移除is_member字段，因为User模型中实际不存在
        if 'is_member' in validated_data:
            validated_data.pop('is_member')
        
        # 设置普通管理员还是超级管理员
        if instance.is_super_admin and not instance.is_admin:
            instance.is_super_admin = False
            instance.is_staff = False
            instance.is_superuser = False
            
        instance.save()
        return instance


class LoginSerializer(serializers.Serializer):
    """
    登录序列化器
    """
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, style={'input_type': 'password'})
    
    def validate(self, data):
        """
        验证用户名/邮箱和密码
        从User和Member两个模型中查找用户
        """
        username_or_email = data['username']
        password = data['password']
        
        # 尝试通过用户名登录
        user = authenticate(username=username_or_email, password=password)
        
        # 如果用户名登录失败，尝试通过邮箱登录
        if not user:
            # 从User模型中查找邮箱匹配的用户
            try:
                user_by_email = User.objects.get(email=username_or_email, is_deleted=False)
                # 验证密码
                if user_by_email.check_password(password):
                    user = user_by_email
            except User.DoesNotExist:
                # 尝试从Member模型中查找
                from users.models import Member
                try:
                    member_by_email = Member.objects.get(email=username_or_email, is_deleted=False)
                    # 验证密码
                    if member_by_email.check_password(password):
                        user = member_by_email
                except Member.DoesNotExist:
                    # 邮箱也找不到，保持user = None
                    pass
        
        # 如果仍未找到用户，尝试在Member模型中通过用户名查找
        if not user:
            from users.models import Member
            try:
                member = Member.objects.get(username=username_or_email, is_deleted=False)
                # 验证密码
                if member.check_password(password):
                    user = member
            except Member.DoesNotExist:
                # 用户名也找不到，保持user = None
                pass
        
        if not user:
            raise serializers.ValidationError("用户名/邮箱或密码错误")
        
        # 验证用户状态
        if not user.is_active:
            raise serializers.ValidationError("用户已被禁用")
        
        if user.is_deleted:
            raise serializers.ValidationError("用户已被删除")
            
        # 检查用户是否为子账号（适用于Member模型）
        if hasattr(user, 'parent') and user.parent:
            raise serializers.ValidationError("子账号不允许登录")
            
        # 验证租户状态
        if user.tenant and not getattr(user, 'is_super_admin', False):
            if user.tenant.status != 'active':
                raise serializers.ValidationError("所属租户已被禁用或暂停")
        
        data['user'] = user
        return data


class TokenRefreshSerializer(serializers.Serializer):
    """
    Token刷新序列化器
    """
    refresh_token = serializers.CharField(required=True)


class UserMinimalSerializer(serializers.ModelSerializer):
    """
    用户最小化序列化器，用于嵌套在其他序列化器中
    """
    display_name = serializers.CharField(read_only=True)
    avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'display_name', 'avatar', 'email', 'phone', 'wechat_id']
        read_only_fields = ['id', 'username', 'display_name', 'avatar', 'email', 'phone', 'wechat_id']
        
    def get_avatar(self, obj) -> str:
        """获取完整的头像URL"""
        if not obj.avatar:
            return ""
        
        # 获取请求对象
        request = self.context.get('request')
        if request is not None:
            return add_domain_to_image_url(request, obj.avatar)
        
        # 如果无法获取请求对象，使用配置中的BASE_URL
        from django.conf import settings
        base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
        # 确保路径以/开头
        path = obj.avatar if obj.avatar.startswith('/') else f'/{obj.avatar}'
        return f"{base_url}{path}"


class MemberMinimalSerializer(serializers.ModelSerializer):
    """
    普通会员最小化序列化器，用于嵌套在其他序列化器中
    """
    display_name = serializers.CharField(read_only=True)
    avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = Member
        fields = ['id', 'username', 'display_name', 'avatar', 'email', 'phone', 'wechat_id']
        read_only_fields = ['id', 'username', 'display_name', 'avatar', 'email', 'phone', 'wechat_id']
        
    def get_avatar(self, obj) -> str:
        """获取完整的头像URL"""
        if not obj.avatar:
            return ""
        
        # 获取请求对象
        request = self.context.get('request')
        if request is not None:
            return add_domain_to_image_url(request, obj.avatar)
        
        # 如果无法获取请求对象，使用配置中的BASE_URL
        from django.conf import settings
        base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
        # 确保路径以/开头
        path = obj.avatar if obj.avatar.startswith('/') else f'/{obj.avatar}'
        return f"{base_url}{path}"


class UserListSerializer(serializers.ModelSerializer):
    """
    用户列表序列化器，用于租户用户列表显示
    """
    tenant_name = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    is_member = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'nick_name', 'email', 'phone', 'wechat_id',
            'is_active', 'avatar', 'tenant', 'tenant_name', 
            'is_admin', 'is_member', 'role', 'date_joined'
        ]
        read_only_fields = fields
    
    def get_tenant_name(self, obj) -> str:
        """获取租户名称"""
        if obj.tenant:
            return obj.tenant.name
        return None
    
    def get_role(self, obj) -> str:
        """获取用户角色"""
        return obj.display_role
        
    def get_is_member(self, obj) -> bool:
        """获取是否为普通成员"""
        # 对于User模型实例，默认不是普通成员
        return getattr(obj, 'is_member', False)
        
    def get_avatar(self, obj) -> str:
        """获取完整的头像URL"""
        if not obj.avatar:
            return ""
        
        # 获取请求对象
        request = self.context.get('request')
        if request is not None:
            return add_domain_to_image_url(request, obj.avatar)
        
        # 如果无法获取请求对象，使用配置中的BASE_URL
        from django.conf import settings
        base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
        # 确保路径以/开头
        path = obj.avatar if obj.avatar.startswith('/') else f'/{obj.avatar}'
        return f"{base_url}{path}"


class RegisterSerializer(serializers.ModelSerializer):
    """
    用户注册序列化器
    """
    password_confirm = serializers.CharField(write_only=True, required=True)
    tenant_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'phone', 'nick_name', 'wechat_id',
            'password', 'password_confirm', 'tenant_id'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'email': {'required': True},
            'phone': {'required': False},
            'nick_name': {'required': False},
            'wechat_id': {'required': False}
        }
    
    def validate_email(self, value):
        """
        验证邮箱是否已被同一租户下使用
        """
        tenant_id = self.initial_data.get('tenant_id')
        if tenant_id:
            if User.objects.filter(email=value, tenant_id=tenant_id, is_deleted=False).exists():
                raise serializers.ValidationError("该租户下此邮箱已被注册")
        else:
            # 对于没有指定租户的情况，只检查超级管理员（无租户用户）中是否有重复
            if User.objects.filter(email=value, tenant__isnull=True, is_deleted=False).exists():
                raise serializers.ValidationError("该邮箱已被注册")
        return value
    
    def validate_username(self, value):
        """
        验证用户名是否已被同一租户下使用
        """
        tenant_id = self.initial_data.get('tenant_id')
        if tenant_id:
            if User.objects.filter(username=value, tenant_id=tenant_id, is_deleted=False).exists():
                raise serializers.ValidationError("该租户下此用户名已被使用")
        else:
            # 对于没有指定租户的情况，只检查超级管理员（无租户用户）中是否有重复
            if User.objects.filter(username=value, tenant__isnull=True, is_deleted=False).exists():
                raise serializers.ValidationError("该用户名已被使用")
        return value
    
    def validate_phone(self, value):
        """
        验证手机号是否已被同一租户下使用
        """
        tenant_id = self.initial_data.get('tenant_id')
        if value and tenant_id:
            if User.objects.filter(phone=value, tenant_id=tenant_id, is_deleted=False).exists():
                raise serializers.ValidationError("该租户下此手机号已被注册")
        elif value and not tenant_id:
            # 对于没有指定租户的情况，只检查超级管理员（无租户用户）中是否有重复
            if User.objects.filter(phone=value, tenant__isnull=True, is_deleted=False).exists():
                raise serializers.ValidationError("该手机号已被注册")
        return value
    
    def validate(self, data):
        """
        验证密码一致性和强度
        """
        if data['password'] != data.pop('password_confirm'):
            raise serializers.ValidationError({"password_confirm": "两次输入的密码不一致"})
        
        # 验证密码强度
        validate_password(data['password'])
        
        # 处理租户ID
        tenant_id = data.pop('tenant_id', None)
        if tenant_id:
            try:
                tenant = Tenant.objects.get(id=tenant_id, status='active', is_deleted=False)
                data['tenant'] = tenant
            except Tenant.DoesNotExist:
                raise serializers.ValidationError({"tenant_id": "无效的租户ID"})
        
        return data
    
    def create(self, validated_data):
        """
        创建用户
        """
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        
        # 设置其他字段
        for field in ['phone', 'nick_name', 'tenant']:
            if field in validated_data:
                setattr(user, field, validated_data[field])
        
        # 设置管理员状态
        user.is_admin = False
        user.status = 'active'
        
        user.save()
        return user


class SubAccountCreateSerializer(serializers.ModelSerializer):
    """
    子账号创建序列化器
    """
    
    class Meta:
        model = Member
        fields = [
            'id', 'username', 'email', 'phone', 'nick_name', 'first_name',
            'last_name', 'avatar', 'wechat_id'
        ]
        extra_kwargs = {
            'id': {'read_only': True},
        }
    
    def validate_username(self, value):
        """
        验证用户名是否已存在
        """
        if Member.objects.filter(username=value).exists():
            raise serializers.ValidationError("该用户名已被使用")
        return value

    def validate_email(self, value):
        """
        验证邮箱是否已存在
        """
        if Member.objects.filter(email=value).exists():
            raise serializers.ValidationError("该邮箱已被使用")
        return value
    
    def create(self, validated_data):
        """
        创建子账号
        """
        # 获取当前用户作为父账号
        parent = self.context['request'].user
        
        # 创建子账号，不设置密码
        member = Member(
            username=validated_data['username'],
            email=validated_data['email'],
            parent=parent,
            tenant=parent.tenant,
            is_active=False  # 子账号默认不可登录
        )
        
        # 设置其他字段
        for field in ['phone', 'nick_name', 'first_name', 'last_name', 'avatar']:
            if field in validated_data:
                setattr(member, field, validated_data[field])
        
        # 保存子账号
        member.save()
        
        return member 


class PasswordResetRequestSerializer(serializers.Serializer):
    """
    请求密码重置的序列化器
    """
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        """
        验证邮箱是否存在
        """
        from users.models import User
        user = User.objects.filter(email=value, is_active=True, is_deleted=False).first()
        if not user:
            raise serializers.ValidationError("未找到使用此邮箱的活跃账户")
        return value


class PasswordResetVerifySerializer(serializers.Serializer):
    """
    验证密码重置令牌的序列化器
    """
    token = serializers.CharField(required=True)
    
    def validate_token(self, value):
        """
        验证令牌是否有效
        """
        from users.models import PasswordResetToken
        token_obj = PasswordResetToken.objects.filter(token=value, is_used=False).first()
        if not token_obj:
            raise serializers.ValidationError("无效的重置令牌")
        if token_obj.is_expired():
            raise serializers.ValidationError("重置令牌已过期")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    确认密码重置的序列化器
    """
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, data):
        """
        验证数据
        """
        # 验证密码是否匹配
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": ["两次输入的密码不一致"]})
        
        # 验证令牌是否有效
        from users.models import PasswordResetToken
        token_obj = PasswordResetToken.objects.filter(token=data['token'], is_used=False).first()
        if not token_obj:
            raise serializers.ValidationError({"token": ["无效的重置令牌"]})
        if token_obj.is_expired():
            raise serializers.ValidationError({"token": ["重置令牌已过期"]})
        
        # 将token对象添加到验证后的数据中
        data['token_obj'] = token_obj
        return data 


# 添加Member专用序列化器
class MemberSerializer(serializers.ModelSerializer):
    """
    普通用户序列化器
    """
    tenant_name = serializers.SerializerMethodField()
    is_sub_account = serializers.SerializerMethodField()
    parent_username = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = Member
        fields = [
            'id', 'username', 'email', 'phone', 'nick_name', 'first_name', 
            'last_name', 'is_active', 'avatar', 'tenant', 'tenant_name', 
            'is_sub_account', 'parent', 'parent_username', 'date_joined',
            'status', 'wechat_id'
        ]
        read_only_fields = ['id', 'date_joined', 'tenant_name', 'is_sub_account', 'parent_username']
    
    def get_tenant_name(self, obj) -> str:
        """获取租户名称"""
        if obj.tenant:
            return obj.tenant.name
        return None
    
    def get_is_sub_account(self, obj) -> bool:
        """获取是否为子账号"""
        return obj.is_sub_account
    
    def get_parent_username(self, obj) -> str:
        """获取父账号用户名"""
        if obj.parent:
            return obj.parent.username
        return None
    
    def get_avatar(self, obj) -> str:
        """获取完整的头像URL"""
        if not obj.avatar:
            return ""
        
        # 获取请求对象
        request = self.context.get('request')
        if request is not None:
            return add_domain_to_image_url(request, obj.avatar)
        
        # 如果无法获取请求对象，使用配置中的BASE_URL
        from django.conf import settings
        base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
        # 确保路径以/开头
        path = obj.avatar if obj.avatar.startswith('/') else f'/{obj.avatar}'
        return f"{base_url}{path}"


class MemberCreateSerializer(serializers.ModelSerializer):
    """
    普通用户创建序列化器
    """
    password_confirm = serializers.CharField(write_only=True)
    tenant_id = serializers.PrimaryKeyRelatedField(
        queryset=Tenant.objects.all(),
        required=False,
        source='tenant',
        write_only=True
    )
    
    class Meta:
        model = Member
        fields = [
            'id', 'username', 'email', 'phone', 'nick_name', 'first_name',
            'last_name', 'password', 'password_confirm', 'tenant_id',
            'avatar', 'wechat_id'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'id': {'read_only': True}
        }
    
    def validate(self, data):
        """
        验证密码一致性
        """
        if data['password'] != data.pop('password_confirm'):
            raise serializers.ValidationError({"password_confirm": "两次输入的密码不一致"})
        
        # 验证密码强度
        validate_password(data['password'])
        
        return data
    
    def create(self, validated_data):
        """
        创建普通用户
        """
        member = Member.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )
        
        # 设置其他字段
        for field in ['phone', 'nick_name', 'first_name', 'last_name', 'tenant', 'avatar']:
            if field in validated_data:
                setattr(member, field, validated_data[field])
        
        member.save()
        return member


class SubAccountSerializer(serializers.ModelSerializer):
    """
    子账号序列化器
    """
    parent_username = serializers.SerializerMethodField(read_only=True)
    tenant_name = serializers.SerializerMethodField(read_only=True)
    is_sub_account = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Member
        fields = [
            'id', 'username', 'email', 'phone', 'nick_name', 'first_name',
            'last_name', 'avatar', 'parent', 'parent_username', 'tenant',
            'tenant_name', 'is_sub_account', 'date_joined', 'wechat_id'
        ]
        read_only_fields = ['id', 'parent', 'tenant', 'date_joined', 'parent_username', 'tenant_name', 'is_sub_account']
    
    def get_parent_username(self, obj) -> str:
        """获取父账号用户名"""
        if obj.parent:
            return obj.parent.username
        return None
    
    def get_tenant_name(self, obj) -> str:
        """获取租户名称"""
        if obj.tenant:
            return obj.tenant.name
        return None
    
    def get_is_sub_account(self, obj) -> bool:
        """获取是否为子账号"""
        return obj.is_sub_account


class SubAccountCreateSerializer(serializers.ModelSerializer):
    """
    子账号创建序列化器
    """
    class Meta:
        model = Member
        fields = [
            'id', 'username', 'email', 'phone', 'nick_name', 'first_name',
            'last_name', 'avatar'
        ]
        extra_kwargs = {
            'id': {'read_only': True}
        }
    
    def validate_username(self, value):
        """
        验证用户名是否已存在
        """
        if Member.objects.filter(username=value).exists():
            raise serializers.ValidationError("该用户名已被使用")
        return value

    def validate_email(self, value):
        """
        验证邮箱是否已存在
        """
        if Member.objects.filter(email=value).exists():
            raise serializers.ValidationError("该邮箱已被使用")
        return value
    
    def create(self, validated_data):
        """
        创建子账号
        """
        # 获取当前用户作为父账号
        parent = self.context['request'].user
        
        # 创建子账号，不设置密码
        member = Member(
            username=validated_data['username'],
            email=validated_data['email'],
            parent=parent,
            tenant=parent.tenant,
            is_active=False  # 子账号默认不可登录
        )
        
        # 设置其他字段
        for field in ['phone', 'nick_name', 'first_name', 'last_name', 'avatar']:
            if field in validated_data:
                setattr(member, field, validated_data[field])
        
        # 保存子账号
        member.save()
        
        return member 