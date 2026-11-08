# points/api/serializers.py
"""
多租户积分系统的API序列化器
"""

from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from django.utils import timezone
from decimal import Decimal

from points.models import (
    TenantUserProfile, TenantUserPoints, UserLevel, 
    UserTypeTag, TenantUserTypeTag, ApplicationUserLevel,
    AppUserPointsAccount, CheckinConfig, UserCheckinStreak,
    UserCheckinRecord
)
from users.models import Member
from tenants.models import Tenant


class UserLevelSerializer(serializers.ModelSerializer):
    """用户等级序列化器"""
    
    class Meta:
        model = UserLevel
        fields = [
            'id', 'level_name', 'level_code', 'level_order', 
            'min_points', 'max_points', 'permissions', 'quota_config',
            'level_color', 'level_icon', 'level_description', 
            'is_active', 'is_default', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserTypeTagSerializer(serializers.ModelSerializer):
    """用户标签序列化器"""
    
    class Meta:
        model = UserTypeTag
        fields = [
            'id', 'tag_name', 'tag_code', 'tag_type', 'tag_color', 
            'tag_icon', 'tag_description', 'permission_modifiers', 
            'quota_modifiers', 'price_config', 'default_duration_days',
            'max_duration_days', 'tag_level', 'is_active', 
            'is_assignable', 'requires_payment', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TenantUserProfileSerializer(serializers.ModelSerializer):
    """租户用户档案序列化器"""
    
    # 关联对象的详细信息
    member_info = serializers.SerializerMethodField()
    tenant_info = serializers.SerializerMethodField()
    current_level_info = serializers.SerializerMethodField()
    
    # 计算字段
    points_summary = serializers.SerializerMethodField()
    active_tags = serializers.SerializerMethodField()
    effective_permissions = serializers.SerializerMethodField()
    
    class Meta:
        model = TenantUserProfile
        fields = [
            'id', 'member', 'tenant', 'total_points', 'available_points',
            'current_level', 'level_updated_at', 'points_earned_total',
            'points_spent_total', 'points_expired_total', 'last_points_update',
            'last_level_check', 'consecutive_login_days', 'last_login_date',
            'points_multiplier', 'is_points_enabled', 'created_at', 'updated_at',
            # 计算字段
            'member_info', 'tenant_info', 'current_level_info', 
            'points_summary', 'active_tags', 'effective_permissions'
        ]
        read_only_fields = [
            'id', 'total_points', 'available_points', 'points_earned_total',
            'points_spent_total', 'points_expired_total', 'last_points_update',
            'last_level_check', 'level_updated_at', 'created_at', 'updated_at',
            'member_info', 'tenant_info', 'current_level_info', 
            'points_summary', 'active_tags', 'effective_permissions'
        ]
    
    @extend_schema_field(serializers.DictField(allow_null=True))
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
    
    @extend_schema_field(serializers.DictField(allow_null=True))
    def get_tenant_info(self, obj):
        """获取租户基本信息"""
        if obj.tenant:
            return {
                'id': obj.tenant.id,
                'name': obj.tenant.name,
                'is_active': obj.tenant.is_active,
            }
        return None
    
    @extend_schema_field(serializers.DictField(allow_null=True))
    def get_current_level_info(self, obj):
        """获取current等级详细信息"""
        if obj.current_level:
            return {
                'id': obj.current_level.id,
                'level_name': obj.current_level.level_name,
                'level_code': obj.current_level.level_code,
                'level_order': obj.current_level.level_order,
                'min_points': obj.current_level.min_points,
                'max_points': obj.current_level.max_points,
                'level_color': obj.current_level.level_color,
                'level_icon': obj.current_level.level_icon,
            }
        return None
    
    @extend_schema_field(serializers.DictField)
    def get_points_summary(self, obj):
        """获取积分统计摘要"""
        from points.models import TenantUserPoints
        return TenantUserPoints.get_points_summary(obj, days=30)
    
    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_active_tags(self, obj):
        """获取活跃的用户标签"""
        active_tags = TenantUserTypeTag.objects.filter(
            tenant_user_profile=obj,
            is_active=True,
            status__in=['active', 'grace_period']
        ).select_related('tag')
        
        return [
            {
                'id': tag.id,
                'tag_name': tag.tag.tag_name,
                'tag_code': tag.tag.tag_code,
                'tag_type': tag.tag.tag_type,
                'tag_color': tag.tag.tag_color,
                'expires_at': tag.expires_at,
                'status': tag.status,
                'vip_status': tag.calculate_vip_status(),
            }
            for tag in active_tags
        ]
    
    @extend_schema_field(serializers.DictField)
    def get_effective_permissions(self, obj):
        """获取用户的有效权限"""
        from points.services.permission_service import TenantAwarePermissionService
        return TenantAwarePermissionService.get_effective_permissions(
            obj.member, obj.tenant
        )


class TenantUserPointsSerializer(serializers.ModelSerializer):
    """租户用户积分记录序列化器"""
    
    # 关联对象信息
    member_info = serializers.SerializerMethodField()
    tenant_info = serializers.SerializerMethodField()
    profile_info = serializers.SerializerMethodField()
    
    # 计算字段
    is_expired = serializers.SerializerMethodField()
    days_until_expiry = serializers.SerializerMethodField()
    
    class Meta:
        model = TenantUserPoints
        fields = [
            'id', 'tenant_user_profile', 'member', 'tenant', 'point_type',
            'category', 'subcategory', 'points', 'balance_before', 'balance_after',
            'tenant_multiplier', 'original_points', 'source_type', 'source_id',
            'source_description', 'earned_at', 'expires_at', 'expired_at',
            'operation_reason', 'operator_id', 'batch_id', 'status', 'is_manual',
            'created_at', 'created_by_id',
            # 计算字段
            'member_info', 'tenant_info', 'profile_info', 'is_expired', 'days_until_expiry'
        ]
        read_only_fields = [
            'id', 'balance_before', 'balance_after', 'earned_at', 'expired_at',
            'created_at', 'member_info', 'tenant_info', 'profile_info', 
            'is_expired', 'days_until_expiry'
        ]
    
    @extend_schema_field(serializers.DictField(allow_null=True))
    def get_member_info(self, obj):
        """获取成员基本信息"""
        if obj.member:
            return {
                'id': obj.member.id,
                'username': obj.member.username,
            }
        return None
    
    @extend_schema_field(serializers.DictField(allow_null=True))
    def get_tenant_info(self, obj):
        """获取租户基本信息"""
        if obj.tenant:
            return {
                'id': obj.tenant.id,
                'name': obj.tenant.name,
            }
        return None
    
    @extend_schema_field(serializers.DictField(allow_null=True))
    def get_profile_info(self, obj):
        """获取用户档案基本信息"""
        if obj.tenant_user_profile:
            return {
                'id': obj.tenant_user_profile.id,
                'total_points': obj.tenant_user_profile.total_points,
                'current_level_name': obj.tenant_user_profile.current_level.level_name if obj.tenant_user_profile.current_level else None,
            }
        return None
    
    @extend_schema_field(serializers.BooleanField)
    def get_is_expired(self, obj):
        """检查积分是否已过期"""
        if obj.expires_at and obj.status == 'active':
            return timezone.now() > obj.expires_at
        return obj.status == 'expired'
    
    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_days_until_expiry(self, obj):
        """计算距离过期的天数"""
        if obj.expires_at and obj.status == 'active':
            days = (obj.expires_at - timezone.now()).days
            return max(0, days)
        return None


class TenantUserTypeTagSerializer(serializers.ModelSerializer):
    """租户用户标签关联序列化器"""
    
    # 关联对象信息
    tag_info = serializers.SerializerMethodField()
    member_info = serializers.SerializerMethodField()
    tenant_info = serializers.SerializerMethodField()
    
    # 计算字段
    vip_status = serializers.SerializerMethodField()
    days_until_expiry = serializers.SerializerMethodField()
    usage_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = TenantUserTypeTag
        fields = [
            'id', 'tenant_user_profile', 'tag', 'member', 'tenant',
            'granted_at', 'granted_by_id', 'grant_reason', 'grant_method',
            'expires_at', 'original_duration_days', 'extended_days', 'auto_renewal',
            'renewal_count', 'grace_period_days', 'reminder_sent_at', 'renewal_reminder_sent',
            'last_used_at', 'usage_count', 'benefits_used', 'payment_id',
            'payment_amount', 'payment_currency', 'is_active', 'status',
            'notes', 'metadata', 'created_at', 'updated_at',
            # 计算字段
            'tag_info', 'member_info', 'tenant_info', 'vip_status', 
            'days_until_expiry', 'usage_summary'
        ]
        read_only_fields = [
            'id', 'granted_at', 'reminder_sent_at', 'last_used_at', 'usage_count',
            'renewal_count', 'created_at', 'updated_at', 'tag_info', 'member_info',
            'tenant_info', 'vip_status', 'days_until_expiry', 'usage_summary'
        ]
    
    @extend_schema_field(serializers.DictField(allow_null=True))
    def get_tag_info(self, obj):
        """获取标签详细信息"""
        if obj.tag:
            return {
                'id': obj.tag.id,
                'tag_name': obj.tag.tag_name,
                'tag_code': obj.tag.tag_code,
                'tag_type': obj.tag.tag_type,
                'tag_color': obj.tag.tag_color,
                'tag_icon': obj.tag.tag_icon,
                'tag_description': obj.tag.tag_description,
                'requires_payment': obj.tag.requires_payment,
                'default_duration_days': obj.tag.default_duration_days,
            }
        return None
    
    @extend_schema_field(serializers.DictField(allow_null=True))
    def get_member_info(self, obj):
        """获取成员基本信息"""
        if obj.member:
            return {
                'id': obj.member.id,
                'username': obj.member.username,
            }
        return None
    
    @extend_schema_field(serializers.DictField(allow_null=True))
    def get_tenant_info(self, obj):
        """获取租户基本信息"""
        if obj.tenant:
            return {
                'id': obj.tenant.id,
                'name': obj.tenant.name,
            }
        return None
    
    @extend_schema_field(serializers.DictField)
    def get_vip_status(self, obj):
        """获取VIP状态详情"""
        return obj.calculate_vip_status()
    
    @extend_schema_field(serializers.IntegerField(allow_null=True))
    def get_days_until_expiry(self, obj):
        """计算距离过期的天数"""
        if obj.expires_at and obj.is_active:
            days = (obj.expires_at - timezone.now()).days
            return max(0, days)
        return None
    
    @extend_schema_field(serializers.DictField)
    def get_usage_summary(self, obj):
        """获取使用情况摘要"""
        return {
            'usage_count': obj.usage_count,
            'last_used_at': obj.last_used_at,
            'total_benefits_used': len(obj.benefits_used) if obj.benefits_used else 0,
            'renewal_count': obj.renewal_count,
            'auto_renewal': obj.auto_renewal,
        }


# 专用于API操作的序列化器

class PointsOperationSerializer(serializers.Serializer):
    """积分操作序列化器（获得、消费、调整）"""
    
    points_amount = serializers.IntegerField(min_value=1, help_text="积分数量")
    category = serializers.ChoiceField(
        choices=TenantUserPoints.CATEGORY_CHOICES,
        help_text="业务分类"
    )
    subcategory = serializers.CharField(
        max_length=50, required=False, allow_blank=True,
        help_text="子分类"
    )
    reason = serializers.CharField(
        max_length=500, required=False, allow_blank=True,
        help_text="操作原因"
    )
    expires_at = serializers.DateTimeField(
        required=False, allow_null=True,
        help_text="过期时间（仅适用于获得积分）"
    )
    source_type = serializers.ChoiceField(
        choices=TenantUserPoints.SOURCE_TYPE_CHOICES,
        default='manual',
        help_text="来源类型"
    )
    source_id = serializers.IntegerField(
        required=False, allow_null=True,
        help_text="关联的源记录ID"
    )


class VipTagGrantSerializer(serializers.Serializer):
    """VIP标签授予序列化器"""
    
    tag_id = serializers.IntegerField(help_text="标签ID")
    duration_days = serializers.IntegerField(
        required=False, allow_null=True, min_value=1,
        help_text="有效期天数（可选，使用标签默认值）"
    )
    grant_method = serializers.ChoiceField(
        choices=TenantUserTypeTag.GRANT_METHOD_CHOICES,
        default='manual',
        help_text="授予方式"
    )
    reason = serializers.CharField(
        max_length=500, required=False, allow_blank=True,
        help_text="授予原因"
    )
    payment_info = serializers.JSONField(
        required=False, allow_null=True,
        help_text="支付信息（金额、货币、支付ID等）"
    )


class VipTagRenewalSerializer(serializers.Serializer):
    """VIP标签续期序列化器"""
    
    duration_days = serializers.IntegerField(min_value=1, help_text="续期天数")
    renewal_method = serializers.ChoiceField(
        choices=['auto', 'manual'],
        default='manual',
        help_text="续期方式"
    )
    reason = serializers.CharField(
        max_length=500, required=False, allow_blank=True,
        help_text="续期原因"
    )
    payment_info = serializers.JSONField(
        required=False, allow_null=True,
        help_text="支付信息"
    )


class UserPointsSummarySerializer(serializers.Serializer):
    """用户积分摘要序列化器"""
    
    total_points = serializers.IntegerField(help_text="总积分")
    current_level = serializers.CharField(help_text="current等级", allow_null=True)
    points_multiplier = serializers.DecimalField(max_digits=3, decimal_places=2, help_text="积分倍数")
    summary_period_days = serializers.IntegerField(help_text="统计周期天数")
    
    earned = serializers.DictField(help_text="获得积分统计")
    spent = serializers.DictField(help_text="消费积分统计")
    net_change = serializers.IntegerField(help_text="净变化")
    category_breakdown = serializers.ListField(help_text="分类明细")


class ApplicationUserLevelSerializer(serializers.ModelSerializer):
    """应用专属积分等级序列化器"""
    application_name = serializers.CharField(source='application.name', read_only=True)
    application_code = serializers.CharField(source='application.code', read_only=True)
    icon_url = serializers.SerializerMethodField()

    class Meta:
        model = ApplicationUserLevel
        fields = [
            'id', 'tenant', 'application', 'application_name', 'application_code',
            'level_name', 'level_code', 'level_order', 'min_points', 'max_points',
            'icon', 'icon_url', 'level_color', 'level_description', 'permissions',
            'quota_config', 'is_active', 'is_default', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'tenant', 'created_at', 'updated_at', 'application_name', 'application_code', 'icon_url']

    def validate(self, attrs):
        min_p = attrs.get('min_points', getattr(self.instance, 'min_points', None))
        max_p = attrs.get('max_points', getattr(self.instance, 'max_points', None) if self.instance else None)
        if min_p is not None and max_p is not None and max_p <= min_p:
            raise serializers.ValidationError({"max_points": "最高积分上限必须大于最低积分门槛"})
        return attrs

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_icon_url(self, obj):
        if not obj.icon:
            return None
        request = self.context.get('request')
        if obj.icon.startswith('http://') or obj.icon.startswith('https://'):
            return obj.icon
        # 兼容相对路径 /media/
        icon_path = obj.icon if obj.icon.startswith('/') else f"/media/{obj.icon}"
        if request:
            return request.build_absolute_uri(icon_path)
        return icon_path


class AppUserPointsAccountSerializer(serializers.ModelSerializer):
    """应用用户积分账户序列化器"""
    application_name = serializers.CharField(source='application.name', read_only=True)
    application_code = serializers.CharField(source='application.code', read_only=True)
    member_username = serializers.CharField(source='member.username', read_only=True)
    member_email = serializers.CharField(source='member.email', read_only=True)
    current_level_info = serializers.SerializerMethodField()

    class Meta:
        model = AppUserPointsAccount
        fields = [
            'id', 'tenant_user_profile', 'tenant', 'application', 'application_name', 'application_code',
            'member', 'member_username', 'member_email', 'total_points', 'available_points',
            'points_earned_total', 'points_spent_total', 'current_level', 'current_level_info',
            'level_updated_at', 'is_enabled', 'last_points_update', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'application_name', 'application_code',
            'member_username', 'member_email', 'current_level_info', 'points_earned_total',
            'points_spent_total', 'last_points_update', 'level_updated_at'
        ]

    @extend_schema_field(serializers.DictField(allow_null=True))
    def get_current_level_info(self, obj):
        if obj.current_level:
            return {
                'id': obj.current_level.id,
                'level_name': obj.current_level.level_name,
                'level_code': obj.current_level.level_code,
                'level_order': obj.current_level.level_order,
                'level_color': obj.current_level.level_color,
                'icon': obj.current_level.icon,
            }
        return None


class AppPointsAdjustSerializer(serializers.Serializer):
    """应用积分调整序列化器"""
    points = serializers.IntegerField(help_text="积分调整数值（正数为增，负数为减）")
    reason = serializers.CharField(max_length=255, default="管理员手动调账", help_text="调账原因")
    category = serializers.ChoiceField(
        choices=TenantUserPoints.CATEGORY_CHOICES,
        default='manual',
        help_text="业务分类"
    )


class CheckinConfigSerializer(serializers.ModelSerializer):
    """签到规则配置序列化器"""
    application_name = serializers.CharField(source='application.name', read_only=True)
    application_code = serializers.CharField(source='application.code', read_only=True)

    class Meta:
        model = CheckinConfig
        fields = [
            'id', 'tenant', 'application', 'application_name', 'application_code',
            'name', 'cycle_days', 'cycle_mode', 'reward_ladder',
            'allow_recheckin', 'recheckin_cost', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'tenant', 'application_name', 'application_code', 'created_at', 'updated_at']

    def validate_reward_ladder(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("阶梯奖励配置必须是数组格式")
        for item in value:
            if not isinstance(item, dict) or 'day' not in item or 'points' not in item:
                raise serializers.ValidationError("阶梯项必须包含 day 和 points 字段")
            if not isinstance(item['day'], int) or item['day'] < 1:
                raise serializers.ValidationError("阶梯 day 必须为大于 0 的整数")
            if not isinstance(item['points'], int) or item['points'] < 0:
                raise serializers.ValidationError("阶梯 points 必须为非负整数")
        return value


class UserCheckinStreakSerializer(serializers.ModelSerializer):
    """用户连续签到统计序列化器（后台管理及用户状态）"""
    application_name = serializers.CharField(source='application.name', read_only=True)
    member_username = serializers.CharField(source='member.username', read_only=True)
    member_email = serializers.CharField(source='member.email', read_only=True)
    has_checked_in_today = serializers.SerializerMethodField()

    class Meta:
        model = UserCheckinStreak
        fields = [
            'id', 'tenant', 'application', 'application_name',
            'member', 'member_username', 'member_email',
            'current_streak', 'max_streak', 'total_days',
            'last_checkin_date', 'has_checked_in_today',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'tenant', 'application_name', 'member_username',
            'member_email', 'has_checked_in_today', 'created_at', 'updated_at'
        ]

    def get_has_checked_in_today(self, obj):
        from django.utils import timezone
        return obj.last_checkin_date == timezone.localdate()


class UserCheckinRecordSerializer(serializers.ModelSerializer):
    """用户签到记录序列化器"""
    application_name = serializers.CharField(source='application.name', read_only=True)
    member_username = serializers.CharField(source='member.username', read_only=True)
    member_email = serializers.CharField(source='member.email', read_only=True)

    class Meta:
        model = UserCheckinRecord
        fields = [
            'id', 'tenant', 'application', 'application_name',
            'member', 'member_username', 'member_email', 'checkin_date',
            'streak_day', 'reward_points', 'is_recheckin', 'extra_data',
            'created_at'
        ]
        read_only_fields = ['id', 'tenant', 'application_name', 'member_username', 'member_email', 'created_at']


class CheckinExecuteSerializer(serializers.Serializer):
    """执行签到请求参数"""
    application_id = serializers.IntegerField(required=False, allow_null=True, help_text="目标应用ID（不传表示租户全局签到）")


class CheckinRecheckinSerializer(serializers.Serializer):
    """执行补签请求参数"""
    application_id = serializers.IntegerField(required=False, allow_null=True, help_text="目标应用ID（不传表示租户全局签到）")
    target_date = serializers.DateField(help_text="需要补签的目标日期（YYYY-MM-DD）")



