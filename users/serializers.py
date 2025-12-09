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
from common.mixins import ImageFieldNormalizerMixin
from common.utils.tenant_header import get_header_tenant_id, require_member_header_match
from common.permissions import IsSuperAdmin, IsAdmin
from common.utils.user_permissions import is_super_admin, is_admin
from common.exceptions import TenantHeaderInvalidOrMissing, TenantMismatchOrNoPermission

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
            'is_admin', 'is_super_admin', 'is_member', 'role', 'date_joined',
            'wechat_id'
        ]
        read_only_fields = ['id', 'date_joined', 'role', 'tenant_name', 'is_member', 'is_super_admin']
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
            raise serializers.ValidationError({"password_confirm": "Passwords do not match"})
        
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


class UserUpdateSerializer(ImageFieldNormalizerMixin, serializers.ModelSerializer):
    """
    用户更新序列化器
    """
    image_fields = ['avatar']  # 需要标准化的图片字段
    
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
            raise serializers.ValidationError("Incorrect old password")
        return value
    
    def validate(self, data):
        """
        验证新密码的一致性和强度
        """
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({"new_password_confirm": "New passwords do not match"})
        
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
            raise serializers.ValidationError("Incorrect old password")
        return value
    
    def validate(self, data):
        """
        验证新密码的一致性和强度
        """
        if data['new_password'] != data['new_password_confirm']:
            raise serializers.ValidationError({"new_password_confirm": "New passwords do not match"})
        
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
        # 检查current用户是否有权限更改角色
        request_user = self.context['request'].user
        target_user = self.instance
        
        # 只有超级管理员或同一租户的管理员可以更改角色
        if not is_super_admin(request_user) and (
            not is_admin(request_user) or 
            request_user.tenant != target_user.tenant
        ):
            raise serializers.ValidationError("You do not have permission to change this user's role")
        
        # 不能取消自己的管理员权限
        if request_user == target_user and not data['is_admin'] and is_admin(request_user):
            raise serializers.ValidationError("You cannot remove your own admin privileges")
        
        # 租户管理员不能修改超级管理员的角色
        if is_super_admin(target_user) and not is_super_admin(request_user):
            raise serializers.ValidationError("You cannot modify the super admin role")
        
        return data
    
    def update(self, instance, validated_data):
        """
        更新用户角色
        """
        # 如果用户变成管理员，检查配额
        if validated_data['is_admin'] and not is_admin(instance) and instance.tenant:
            quota = instance.tenant.quota
            if not quota.can_add_user(is_admin=True):
                raise serializers.ValidationError({"is_admin": "Tenant admin quota is full"})
        
        # 更新角色
        instance.is_admin = validated_data['is_admin']
        
        # 如果取消管理员角色，确保用户至少是普通成员
        if not instance.is_admin:
            instance.is_member = True
        
        instance.save()
        return instance


class UserRoleUpdateSerializer(serializers.ModelSerializer):
    """
    用户角色更新序列化器，用于更新用户角色
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
            raise serializers.ValidationError({"non_field_errors": "User must have at least one role"})
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
        if is_super_admin(instance) and not instance.is_admin:
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
    
    def _header_tenant_id(self):
        request = self.context.get('request') if hasattr(self, 'context') else None
        if not request:
            return None
        return get_header_tenant_id(request)

    def _member_lookup_by_identifier(self, identifier: str, tenant_id: int):
        """
        在 Member 中按用户名或邮箱查找。
        - 若传入 tenant_id：限定租户；
        - 若未传入：允许唯一命中；多命中则返回 ('ambiguous', None)。
        返回: (status, member or None)
          status in {'found', 'not_found', 'ambiguous'}
        """
        from users.models import Member
        qs_email = Member.objects.filter(email=identifier, is_deleted=False)
        qs_username = Member.objects.filter(username=identifier, is_deleted=False)

        if tenant_id:
            qs_email = qs_email.filter(tenant_id=tenant_id)
            qs_username = qs_username.filter(tenant_id=tenant_id)

        # 优先邮箱，再用户名
        for qs in (qs_email, qs_username):
            count = qs.count()
            if count == 1:
                return ('found', qs.first())
            if count > 1 and not tenant_id:
                return ('ambiguous', None)
        return ('not_found', None)

    def validate(self, data):
        """
        验证用户名/邮箱和密码。支持 User 与 Member；Member 支持按租户消歧。
        """
        identifier = data['username']
        password = data['password']

        request = self.context.get('request') if hasattr(self, 'context') else None

        # 有 Header => 强制成员流程；管理员/超管携带 Header 禁止
        header_tid = self._header_tenant_id()
        if header_tid is not None:
            # 成员流程：忽略 body tenant_id 并记录（由工具函数负责日志）
            if request:
                require_member_header_match(request)  # 缺失/非法会抛4001；未认证用户仅校验Header格式
            status_key, member = self._member_lookup_by_identifier(identifier, header_tid)
            
            if status_key == 'found' and member and member.check_password(password):
                user = member
            else:
                # 记录成员登录失败详情
                logger.warning(f"成员登录失败: username={identifier}, tenant_id={header_tid}, status={status_key}, member_found={member is not None}")
                if member and not member.check_password(password):
                    logger.warning(f"成员密码验证失败: username={identifier}")
                
                # 若凭据命中了管理员账号，也应当禁止（管理员/超管禁头）
                possible_admin = authenticate(username=identifier, password=password)
                if not possible_admin:
                    try:
                        user_by_email = User.objects.get(email=identifier, is_deleted=False)
                        if user_by_email.check_password(password):
                            possible_admin = user_by_email
                    except User.DoesNotExist:
                        pass
                if possible_admin is not None:
                    # 管理员/超管携带Header登录，返回4001
                    logger.warning(f"管理员尝试携带Header登录: username={identifier}, tenant_id={header_tid}")
                    raise TenantHeaderInvalidOrMissing()
                # 其他情况按通用失败处理
                raise serializers.ValidationError("Invalid username/email or password")
        else:
            # 无 Header => 仅允许管理员/超管流程；成员必须使用Header
            user = authenticate(username=identifier, password=password)
            if not user:
                try:
                    user_by_email = User.objects.get(email=identifier, is_deleted=False)
                    if user_by_email.check_password(password):
                        user = user_by_email
                except User.DoesNotExist:
                    pass
            
            # 记录管理员登录失败详情
            if not user:
                logger.warning(f"管理员登录验证失败: username={identifier} (无Header流程)")
                # 检查是否存在该用户但密码错误
                try:
                    u = User.objects.filter(username=identifier).first() or User.objects.filter(email=identifier).first()
                    if u:
                        logger.warning(f"用户存在但验证失败: username={u.username}, is_active={u.is_active}, is_staff={u.is_staff}, check_password={u.check_password(password)}")
                    else:
                        logger.warning(f"用户不存在: username={identifier}")
                except Exception as e:
                    logger.error(f"检查用户状态时出错: {e}")

            # 若命中成员，则因无Header而拒绝
            if not user:
                # 不再进行成员查找，直接要求Header
                logger.warning(f"登录失败且未命中User，抛出TenantHeaderInvalidOrMissing以提示可能需要Header: username={identifier}")
                raise TenantHeaderInvalidOrMissing()

        if not user:
            raise serializers.ValidationError("Invalid username/email or password")

        # 通用状态校验
        if not user.is_active:
            raise serializers.ValidationError("User is disabled")
        if user.is_deleted:
            raise serializers.ValidationError("User has been deleted")
        # 子账号限制
        if hasattr(user, 'parent') and user.parent:
            raise serializers.ValidationError("Sub-accounts are not allowed to log in")
        # 租户状态校验（非超管）
        if user.tenant and not getattr(user, 'is_super_admin', False):
            if user.tenant.status != 'active':
                raise serializers.ValidationError("Tenant has been disabled or suspended")

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
                raise serializers.ValidationError("Email already registered in this tenant")
        else:
            # 对于没有指定租户的情况，只检查超级管理员（无租户用户）中是否有重复
            if User.objects.filter(email=value, tenant__isnull=True, is_deleted=False).exists():
                raise serializers.ValidationError("Email already registered")
        return value
    
    def validate_username(self, value):
        """
        验证用户名是否已被同一租户下使用
        """
        tenant_id = self.initial_data.get('tenant_id')
        if tenant_id:
            if User.objects.filter(username=value, tenant_id=tenant_id, is_deleted=False).exists():
                raise serializers.ValidationError("Username already used in this tenant")
        else:
            # 对于没有指定租户的情况，只检查超级管理员（无租户用户）中是否有重复
            if User.objects.filter(username=value, tenant__isnull=True, is_deleted=False).exists():
                raise serializers.ValidationError("Username already in use")
        return value
    
    def validate_phone(self, value):
        """
        验证手机号是否已被同一租户下使用
        """
        tenant_id = self.initial_data.get('tenant_id')
        if value and tenant_id:
            if User.objects.filter(phone=value, tenant_id=tenant_id, is_deleted=False).exists():
                raise serializers.ValidationError("Phone number already registered in this tenant")
        elif value and not tenant_id:
            # 对于没有指定租户的情况，只检查超级管理员（无租户用户）中是否有重复
            if User.objects.filter(phone=value, tenant__isnull=True, is_deleted=False).exists():
                raise serializers.ValidationError("Phone number already registered")
        return value
    
    def validate(self, data):
        """
        验证密码一致性和强度
        """
        # 管理员/超管注册接口禁用 Header：若携带 X-Tenant-ID 则报 4001
        request = self.context.get('request') if hasattr(self, 'context') else None
        if request is not None and get_header_tenant_id(request) is not None:
            raise TenantHeaderInvalidOrMissing()

        if data['password'] != data.pop('password_confirm'):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match"})
        
        # 验证密码强度
        validate_password(data['password'])
        
        # 处理租户ID
        tenant_id = data.pop('tenant_id', None)
        if tenant_id:
            try:
                tenant = Tenant.objects.get(id=tenant_id, status='active', is_deleted=False)
                data['tenant'] = tenant
            except Tenant.DoesNotExist:
                raise serializers.ValidationError({"tenant_id": "Invalid tenant ID"})
        
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


class SubAccountCreateSerializer(ImageFieldNormalizerMixin, serializers.ModelSerializer):
    """
    子账号创建序列化器
    """
    image_fields = ['avatar']  # 需要标准化的图片字段
    
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
            raise serializers.ValidationError("Username already in use")
        return value

    def validate_email(self, value):
        """
        验证邮箱是否已存在
        """
        if Member.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already in use")
        return value
    
    def create(self, validated_data):
        """
        创建子账号
        """
        # 获取current用户作为父账号
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
    请求密码重置的序列化器（统一 User/Member）
    - 仅校验基本字段格式，不泄露账号是否存在
    - account_type 可选：user / member，用于明确主体；不提供时由服务端尝试自动判定
    - tenant_id 可选：当 account_type=member 且邮箱在多租户下重复时需要提供
    """
    email = serializers.EmailField(required=True)
    account_type = serializers.ChoiceField(choices=["user", "member"], required=False)
    tenant_id = serializers.IntegerField(required=False)

    def validate(self, data):
        """
        根据 account_type 与 X-Tenant-ID 执行租户头规则：
        - account_type=member：强制使用 Header，忽略 body tenant_id
        - account_type=user：若携带 Header -> 4001
        - 未指定：若携带 Header -> 按成员流程；否则保持原有策略
        """
        request = self.context.get('request') if hasattr(self, 'context') else None
        header_tid = get_header_tenant_id(request) if request else None
        acct = data.get('account_type')

        if acct == 'member' or (acct is None and header_tid is not None):
            # 成员流程：要求并校验 Header，忽略 body 的 tenant_id
            if request:
                require_member_header_match(request)
            if header_tid is None:
                # 兜底：按规则这里应已抛错
                raise TenantHeaderInvalidOrMissing()
            # 覆盖为 Header 值
            data['tenant_id'] = header_tid
            return data

        if acct == 'user':
            # 管理员/超管禁用 Header
            if header_tid is not None:
                raise TenantHeaderInvalidOrMissing()
            return data

        # acct is None 且无 Header：保持既有策略，不做额外强制
        return data


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
            raise serializers.ValidationError("Invalid reset token")
        if token_obj.is_expired():
            raise serializers.ValidationError("Reset token has expired")
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
            raise serializers.ValidationError({"confirm_password": ["Passwords do not match"]})
        
        # 验证令牌是否有效
        from users.models import PasswordResetToken
        token_obj = PasswordResetToken.objects.filter(token=data['token'], is_used=False).first()
        if not token_obj:
            raise serializers.ValidationError({"token": ["Invalid reset token"]})
        if token_obj.is_expired():
            raise serializers.ValidationError({"token": ["Reset token has expired"]})
        
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
    管理端创建普通成员序列化器
    - 超级管理员可通过 body 的 tenant_id 指定租户；否则使用current管理员的 tenant
    - 校验密码一致性与强度
    - 在目标租户下校验 username/email/phone 唯一
    """
    password_confirm = serializers.CharField(write_only=True, required=True)
    tenant_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Member
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

    def _resolve_target_tenant_id(self) -> int:
        request = self.context.get('request') if hasattr(self, 'context') else None
        input_tenant_id = self.initial_data.get('tenant_id') if hasattr(self, 'initial_data') else None
        if input_tenant_id:
            try:
                return int(input_tenant_id)
            except (TypeError, ValueError):
                raise serializers.ValidationError({"tenant_id": "Invalid tenant ID"})
        # 未提供 tenant_id，则从请求用户推断
        if request and hasattr(request.user, 'is_super_admin'):
            if is_super_admin(request.user):
                # 超级管理员必须显式提供 tenant_id
                raise serializers.ValidationError({"tenant_id": "Super admin must provide tenant ID when creating member"})
            # 非超级管理员必须有绑定租户
            if not request.user.tenant:
                raise serializers.ValidationError({"tenant_id": "Current admin has no associated tenant and cannot create member"})
            return request.user.tenant.id
        return None

    def validate(self, data):
        # 密码一致性
        if data['password'] != data.pop('password_confirm'):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match"})

        # 密码强度
        validate_password(data['password'])

        # 解析并校验租户
        tenant_id = self._resolve_target_tenant_id()
        try:
            tenant = Tenant.objects.get(id=tenant_id, status='active', is_deleted=False)
        except Tenant.DoesNotExist:
            raise serializers.ValidationError({"tenant_id": "Invalid tenant ID"})

        # 唯一性校验（在该租户内）
        username = data.get('username')
        email = data.get('email')
        phone = data.get('phone')
        if username and Member.objects.filter(username=username, tenant_id=tenant_id, is_deleted=False).exists():
            raise serializers.ValidationError({"username": "Username already used in this tenant"})
        if email and Member.objects.filter(email=email, tenant_id=tenant_id, is_deleted=False).exists():
            raise serializers.ValidationError({"email": "Email already registered in this tenant"})
        if phone and Member.objects.filter(phone=phone, tenant_id=tenant_id, is_deleted=False).exists():
            raise serializers.ValidationError({"phone": "Phone number already registered in this tenant"})

        # 注入租户对象供 create 使用
        data['tenant'] = tenant
        return data

    def create(self, validated_data):
        member = Member.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )

        for field in ['phone', 'nick_name', 'tenant', 'wechat_id']:
            if field in validated_data:
                setattr(member, field, validated_data[field])

        member.status = 'active'
        member.is_active = True
        member.save()
        return member


class MemberSelfRegisterSerializer(serializers.ModelSerializer):
    """
    成员自助注册序列化器
    - 仅从请求头 X-Tenant-ID 获取租户ID（忽略 body 的 tenant_id）
    - 校验密码一致性与强度
    - 校验在同一租户内的 username/email/phone 唯一
    - 创建激活状态的 Member
    """
    password_confirm = serializers.CharField(write_only=True, required=True)
    tenant_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Member
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

    def _resolve_tenant_id_from_header(self) -> int:
        request = self.context.get('request') if hasattr(self, 'context') else None
        if not request:
            return None
        header_val = request.META.get('HTTP_X_TENANT_ID')
        if not header_val:
            return None
        try:
            return int(header_val)
        except (TypeError, ValueError):
            return None

    def validate(self, data):
        # 密码一致性
        if data['password'] != data.pop('password_confirm'):
            raise serializers.ValidationError({"password_confirm": "Passwords do not match"})

        # 密码强度
        validate_password(data['password'])

        # 成员注册仅允许并强制使用 Header 的租户ID，忽略 body 的 tenant_id
        # 移除并忽略 body 中的 tenant_id（如提供）
        data.pop('tenant_id', None)
        request = self.context.get('request') if hasattr(self, 'context') else None
        if request:
            # 统一校验与日志（缺失/非法->4001，已登录且租户不匹配->4003）
            require_member_header_match(request)
        tenant_id = get_header_tenant_id(request) if request else None
        if tenant_id is None:
            # 兜底：无有效 Header
            raise TenantHeaderInvalidOrMissing()

        # 校验租户有效
        try:
            tenant = Tenant.objects.get(id=tenant_id, status='active', is_deleted=False)
        except Tenant.DoesNotExist:
            raise serializers.ValidationError({"tenant_id": "Invalid tenant ID"})

        # 在该租户内做唯一性校验（仅针对 Member 模型）
        username = data.get('username')
        email = data.get('email')
        phone = data.get('phone')

        if username and Member.objects.filter(username=username, tenant_id=tenant_id, is_deleted=False).exists():
            raise serializers.ValidationError({"username": "Username already used in this tenant"})
        if email and Member.objects.filter(email=email, tenant_id=tenant_id, is_deleted=False).exists():
            raise serializers.ValidationError({"email": "Email already registered in this tenant"})
        if phone and Member.objects.filter(phone=phone, tenant_id=tenant_id, is_deleted=False).exists():
            raise serializers.ValidationError({"phone": "Phone number already registered in this tenant"})

        # 注入解析出的租户对象
        data['tenant'] = tenant
        return data

    def create(self, validated_data):
        member = Member.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )

        for field in ['phone', 'nick_name', 'tenant']:
            if field in validated_data:
                setattr(member, field, validated_data[field])

        # 设置为激活状态
        member.status = 'active'
        member.is_active = True
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
            raise serializers.ValidationError("Username already in use")
        return value

    def validate_email(self, value):
        """
        验证邮箱是否已存在
        """
        if Member.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already in use")
        return value
    
    def create(self, validated_data):
        """
        创建子账号
        """
        # 获取current用户作为父账号
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


class MemberDeactivateSerializer(serializers.Serializer):
    """
    会员账号注销序列化器
    
    用于验证注销请求，需要提供当前密码以确认操作
    """
    password = serializers.CharField(
        required=True, 
        write_only=True,
        style={'input_type': 'password'},
        help_text="当前账号密码，用于确认注销操作"
    )
    reason = serializers.CharField(
        required=False, 
        max_length=500, 
        allow_blank=True,
        help_text="注销原因（可选），用于统计分析"
    )
    
    def validate_password(self, value):
        """
        验证密码是否正确
        """
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("密码错误")
        return value