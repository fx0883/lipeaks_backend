"""
多租户积分系统模型定义
"""
import logging
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)


class TenantUserProfile(models.Model):
    """
    租户用户档案表，存储用户在特定租户下的积分和等级信息
    
    这是多租户积分系统的核心表，确保同一用户在不同租户下拥有独立的积分和等级
    """
    
    # 关联信息
    member = models.ForeignKey(
        'users.Member', 
        on_delete=models.CASCADE, 
        verbose_name=_("关联成员")
    )
    tenant = models.ForeignKey(
        'tenants.Tenant', 
        on_delete=models.CASCADE, 
        verbose_name=_("关联租户")
    )
    
    # 积分信息
    total_points = models.PositiveIntegerField(_("总积分"), default=0)
    available_points = models.PositiveIntegerField(_("可用积分"), default=0)
    
    # 等级信息
    current_level = models.ForeignKey(
        'UserLevel', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name=_("current等级")
    )
    level_updated_at = models.DateTimeField(_("等级更新时间"), null=True, blank=True)
    
    # 统计信息
    points_earned_total = models.PositiveIntegerField(_("历史总获得积分"), default=0)
    points_spent_total = models.PositiveIntegerField(_("历史总消费积分"), default=0)
    points_expired_total = models.PositiveIntegerField(_("历史总过期积分"), default=0)
    
    # 活跃度信息
    last_points_update = models.DateTimeField(_("最后积分Change时间"), null=True, blank=True)
    last_level_check = models.DateTimeField(_("最后等级检查时间"), null=True, blank=True)
    consecutive_login_days = models.PositiveIntegerField(_("连续登录天数"), default=0)
    last_login_date = models.DateField(_("最后登录日期"), null=True, blank=True)
    
    # 配置信息
    points_multiplier = models.DecimalField(
        _("积分倍数"), 
        max_digits=3, 
        decimal_places=2, 
        default=Decimal('1.00'),
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    is_points_enabled = models.BooleanField(_("是否启用积分功能"), default=True)
    
    # 审计字段
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)
    
    class Meta:
        db_table = 'tenant_user_profile'
        verbose_name = _('租户用户档案')
        verbose_name_plural = _('租户用户档案')
        constraints = [
            models.UniqueConstraint(
                fields=['member', 'tenant'],
                name='unique_member_tenant'
            ),
            models.CheckConstraint(
                check=models.Q(total_points__gte=0) & models.Q(available_points__gte=0),
                name='valid_points'
            ),
            models.CheckConstraint(
                check=models.Q(available_points__lte=models.F('total_points')),
                name='available_points_check'
            ),
        ]
        indexes = [
            models.Index(fields=['member'], name='idx_tenant_user_profile_member'),
            models.Index(fields=['tenant'], name='idx_tenant_user_profile_tenant'),
            models.Index(fields=['tenant', 'total_points'], name='idx_tenant_user_profile_points'),
            models.Index(fields=['current_level'], name='idx_tenant_user_profile_level'),
            models.Index(fields=['tenant', 'last_points_update'], name='idx_tenant_user_profile_active'),
        ]
    
    def __str__(self):
        member_name = self.member.username if self.member else "Unknown"
        tenant_name = self.tenant.name if self.tenant else "Unknown"
        level_name = self.current_level.level_name if self.current_level else "无等级"
        return f"{member_name}@{tenant_name} - {self.total_points}分 ({level_name})"
    
    def save(self, *args, **kwargs):
        """重写保存方法，添加业务逻辑"""
        is_new = self.pk is None
        
        # 确保可用积分不超过总积分
        if self.available_points > self.total_points:
            self.available_points = self.total_points
        
        # 新建时记录日志
        if is_new:
            logger.info(f"创建租户用户档案: {self.member.username}@{self.tenant.name}")
        
        super().save(*args, **kwargs)
    
    def add_points(self, points, reason="", source_type="system"):
        """
        增加积分
        
        Args:
            points: 增加的积分数量
            reason: 积分增加原因
            source_type: 来源类型
        """
        if points <= 0:
            raise ValueError("Points amount must be greater than 0")
        
        # 应用积分倍数
        actual_points = int(points * self.points_multiplier)
        
        # 更新积分
        self.total_points += actual_points
        self.available_points += actual_points
        self.points_earned_total += actual_points
        self.last_points_update = timezone.now()
        
        self.save()
        
        logger.info(f"用户 {self.member.username}@{self.tenant.name} 获得 {actual_points} 积分: {reason}")
        
        return actual_points
    
    def spend_points(self, points, reason=""):
        """
        消费积分
        
        Args:
            points: 消费的积分数量
            reason: 消费原因
        """
        if points <= 0:
            raise ValueError("Points amount must be greater than 0")
        
        if self.available_points < points:
            raise ValueError(f"积分不足，Available points: {self.available_points}, Required: {points}")
        
        # 更新积分
        self.available_points -= points
        self.points_spent_total += points
        self.last_points_update = timezone.now()
        
        self.save()
        
        logger.info(f"用户 {self.member.username}@{self.tenant.name} 消费 {points} 积分: {reason}")
        
        return points
    
    def check_level_upgrade(self):
        """
        检查是否需要等级升级
        
        Returns:
            bool: 是否发生了等级变化
        """
        from .services import UserLevelService  # 避免循环导入
        
        level_service = UserLevelService()
        new_level = level_service.calculate_user_level(self.total_points)
        
        if new_level and (not self.current_level or new_level.level_order > self.current_level.level_order):
            old_level = self.current_level
            self.current_level = new_level
            self.level_updated_at = timezone.now()
            self.last_level_check = timezone.now()
            self.save()
            
            logger.info(f"用户 {self.member.username}@{self.tenant.name} 等级升级: {old_level} -> {new_level}")
            return True
        
        # 更新检查时间
        self.last_level_check = timezone.now()
        self.save(update_fields=['last_level_check'])
        
        return False
    
    def update_login_streak(self):
        """
        更新连续登录天数
        
        Returns:
            int: current连续登录天数
        """
        today = timezone.now().date()
        
        if self.last_login_date == today:
            # 今天已经登录过了
            return self.consecutive_login_days
        elif self.last_login_date == today - timedelta(days=1):
            # 昨天登录了，连续登录天数+1
            self.consecutive_login_days += 1
        elif not self.last_login_date or self.last_login_date < today - timedelta(days=1):
            # 超过一天没有登录，重置连续登录天数
            self.consecutive_login_days = 1
        
        self.last_login_date = today
        self.save(update_fields=['consecutive_login_days', 'last_login_date'])
        
        logger.info(f"用户 {self.member.username}@{self.tenant.name} 连续登录 {self.consecutive_login_days} 天")
        
        return self.consecutive_login_days


class UserLevel(models.Model):
    """
    用户等级配置表，定义积分阈值和权限配置
    """
    
    level_name = models.CharField(_("等级名称"), max_length=50)
    level_code = models.CharField(_("等级代码"), max_length=20, unique=True)
    level_order = models.PositiveIntegerField(_("等级序号"), unique=True)
    
    # 积分要求
    min_points = models.PositiveIntegerField(_("最低积分要求"), default=0)
    max_points = models.PositiveIntegerField(_("最高积分上限"), null=True, blank=True)
    
    # 权限配置 (JSON字段存储权限配置)
    permissions = models.JSONField(_("权限配置"), default=dict, blank=True)
    quota_config = models.JSONField(_("配额配置"), default=dict, blank=True)
    
    # 等级配置
    level_color = models.CharField(_("等级颜色"), max_length=7, default="#999999")  # 十六进制颜色
    level_icon = models.CharField(_("等级图标"), max_length=100, blank=True)
    level_description = models.TextField(_("等级描述"), blank=True)
    
    # 状态管理
    is_active = models.BooleanField(_("是否启用"), default=True)
    is_default = models.BooleanField(_("是否默认等级"), default=False)
    
    # 审计字段
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)
    
    class Meta:
        db_table = 'user_level'
        verbose_name = _('用户等级')
        verbose_name_plural = _('用户等级')
        ordering = ['level_order']
        constraints = [
            models.CheckConstraint(
                check=models.Q(min_points__gte=0),
                name='valid_min_points'
            ),
            models.CheckConstraint(
                check=models.Q(max_points__isnull=True) | models.Q(max_points__gt=models.F('min_points')),
                name='valid_max_points'
            ),
        ]
        indexes = [
            models.Index(fields=['is_active', 'level_order'], name='idx_user_level_active_order'),
            models.Index(fields=['min_points'], name='idx_user_level_min_points'),
        ]
    
    def __str__(self):
        return f"{self.level_name} (序号: {self.level_order})"
    
    def save(self, *args, **kwargs):
        """重写保存方法，确保只有一个默认等级"""
        if self.is_default:
            # 取消其他等级的默认状态
            UserLevel.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        
        super().save(*args, **kwargs)
    
    def is_points_in_range(self, points):
        """
        检查积分是否在current等级范围内
        
        Args:
            points: 积分数量
            
        Returns:
            bool: 是否在范围内
        """
        if points < self.min_points:
            return False
        
        if self.max_points is not None and points > self.max_points:
            return False
        
        return True
    
    def get_quota_value(self, quota_key, default=None):
        """
        获取配额配置值
        
        Args:
            quota_key: 配额键名
            default: 默认值
            
        Returns:
            配额值
        """
        return self.quota_config.get(quota_key, default)
    
    def get_permission_value(self, permission_key, default=None):
        """
        获取权限配置值
        
        Args:
            permission_key: 权限键名
            default: 默认值
            
        Returns:
            权限值
        """
        return self.permissions.get(permission_key, default)


class TenantUserPoints(models.Model):
    """
    租户用户积分记录表，记录用户在租户下的积分Change记录
    
    这个表记录所有积分Change的历史，支持积分获取、消费、过期、调整等操作
    """
    
    POINT_TYPE_CHOICES = [
        ('earn', '获得'),
        ('spend', '消费'),
        ('expire', '过期'),
        ('adjust', '调整'),
    ]
    
    CATEGORY_CHOICES = [
        ('login', '登录奖励'),
        ('license', '许可证相关'),
        ('referral', '推荐奖励'),
        ('payment', '支付奖励'),
        ('community', '社区活动'),
        ('manual', '手动调整'),
        ('system', '系统操作'),
    ]
    
    SOURCE_TYPE_CHOICES = [
        ('manual', '手动操作'),
        ('system', '系统操作'),
        ('api', 'API操作'),
        ('migration', '数据迁移'),
    ]
    
    STATUS_CHOICES = [
        ('active', '有效'),
        ('expired', '已过期'),
        ('cancelled', '已取消'),
        ('adjusted', '已调整'),
    ]
    
    # 关联信息
    tenant_user_profile = models.ForeignKey(
        TenantUserProfile, 
        on_delete=models.CASCADE,
        related_name='points_records',
        verbose_name=_("租户用户档案")
    )
    tenant = models.ForeignKey(
        'tenants.Tenant', 
        on_delete=models.CASCADE, 
        verbose_name=_("租户")  # 冗余字段，便于查询优化
    )
    member = models.ForeignKey(
        'users.Member', 
        on_delete=models.CASCADE, 
        verbose_name=_("成员")  # 冗余字段，便于查询优化
    )
    
    # 积分类型分类
    point_type = models.CharField(_("积分类型"), max_length=10, choices=POINT_TYPE_CHOICES)
    category = models.CharField(_("业务分类"), max_length=20, choices=CATEGORY_CHOICES)
    subcategory = models.CharField(_("子分类"), max_length=50, blank=True)
    
    # 积分数值
    points = models.IntegerField(_("积分Change数量"))  # 正数为获得，负数为消费
    balance_before = models.PositiveIntegerField(_("操作前积分余额"))
    balance_after = models.PositiveIntegerField(_("操作后积分余额"))
    
    # 租户特定信息
    tenant_multiplier = models.DecimalField(
        _("租户积分倍数"), 
        max_digits=3, 
        decimal_places=2, 
        default=Decimal('1.00')
    )
    original_points = models.PositiveIntegerField(_("倍数调整前的原始积分"), null=True, blank=True)
    
    # 关联信息
    source_type = models.CharField(_("来源类型"), max_length=20, choices=SOURCE_TYPE_CHOICES, default='system')
    source_id = models.PositiveBigIntegerField(_("关联的源记录ID"), null=True, blank=True)
    source_description = models.TextField(_("来源描述"), blank=True)
    
    # 积分生命周期
    earned_at = models.DateTimeField(_("积分获得时间"), auto_now_add=True)
    expires_at = models.DateTimeField(_("积分过期时间"), null=True, blank=True)  # NULL表示永不过期
    expired_at = models.DateTimeField(_("实际过期时间"), null=True, blank=True)
    
    # 操作信息
    operation_reason = models.TextField(_("操作原因说明"), blank=True)
    operator_id = models.PositiveBigIntegerField(_("操作人员ID"), null=True, blank=True)  # 系统操作为NULL
    batch_id = models.CharField(_("批量操作标识"), max_length=100, blank=True)
    
    # 状态管理
    status = models.CharField(_("状态"), max_length=20, choices=STATUS_CHOICES, default='active')
    is_manual = models.BooleanField(_("是否手动调整"), default=False)
    
    # 审计字段
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    created_by_id = models.PositiveBigIntegerField(_("创建人ID"), null=True, blank=True)
    
    class Meta:
        db_table = 'tenant_user_points'
        verbose_name = _('租户用户积分记录')
        verbose_name_plural = _('租户用户积分记录')
        ordering = ['-created_at']
        constraints = [
            models.CheckConstraint(
                check=models.Q(points__gt=0) | models.Q(points__lt=0),  # 积分Change不能为0
                name='points_not_zero'
            ),
            models.CheckConstraint(
                check=models.Q(balance_after=models.F('balance_before') + models.F('points')),
                name='valid_balance'
            ),
            models.CheckConstraint(
                check=models.Q(balance_after__gte=0),
                name='valid_balance_positive'
            ),
            models.CheckConstraint(
                check=models.Q(tenant_multiplier__gt=0),
                name='valid_tenant_multiplier'
            ),
        ]
        indexes = [
            models.Index(
                fields=['tenant_user_profile', 'created_at'], 
                name='idx_tenant_user_points_profile'
            ),
            models.Index(
                fields=['tenant', 'member', 'created_at'], 
                name='tup_tenant_member'
            ),
            models.Index(
                fields=['tenant', 'point_type', 'category'], 
                name='idx_tenant_user_points_type'
            ),
            models.Index(
                fields=['tenant', 'expires_at'], 
                name='tup_expires',
                condition=models.Q(expires_at__isnull=False, status='active')
            ),
            models.Index(
                fields=['tenant', 'source_type', 'source_id'], 
                name='idx_tenant_user_points_source',
                condition=models.Q(source_id__isnull=False)
            ),
        ]
    
    def __str__(self):
        member_name = self.member.username if self.member else "Unknown"
        tenant_name = self.tenant.name if self.tenant else "Unknown"
        points_str = f"+{self.points}" if self.points > 0 else str(self.points)
        return f"{member_name}@{tenant_name}: {points_str}分 ({self.get_category_display()})"
    
    def save(self, *args, **kwargs):
        """重写保存方法，添加验证逻辑"""
        # 验证余额计算
        if self.balance_after != self.balance_before + self.points:
            raise ValueError(f"余额计算错误: {self.balance_before} + {self.points} != {self.balance_after}")
        
        # 记录日志
        if self.pk is None:  # 新记录
            logger.info(
                f"积分记录: {self.member.username}@{self.tenant.name} "
                f"{'+' if self.points > 0 else ''}{self.points}分 "
                f"({self.get_category_display()}) - {self.operation_reason}"
            )
        
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """
        检查积分是否已过期
        
        Returns:
            bool: 是否已过期
        """
        if not self.expires_at:
            return False  # 永不过期
        
        return timezone.now() > self.expires_at
    
    def expire_points(self, reason="系统自动过期"):
        """
        标记积分为过期
        
        Args:
            reason: 过期原因
        """
        if self.status != 'active':
            raise ValueError(f"只能标记有效积分为过期，Current status: {self.status}")
        
        self.status = 'expired'
        self.expired_at = timezone.now()
        self.operation_reason = f"{self.operation_reason} | 过期原因: {reason}"
        
        self.save()
        
        logger.info(f"积分过期: {self.member.username}@{self.tenant.name} {self.points}分 - {reason}")
    
    def cancel_points(self, reason=""):
        """
        取消积分记录
        
        Args:
            reason: 取消原因
        """
        if self.status != 'active':
            raise ValueError(f"只能取消有效积分，Current status: {self.status}")
        
        self.status = 'cancelled'
        self.operation_reason = f"{self.operation_reason} | 取消原因: {reason}"
        
        self.save()
        
        logger.info(f"积分取消: {self.member.username}@{self.tenant.name} {self.points}分 - {reason}")
    
    @classmethod
    def create_points_record(cls, tenant_user_profile, point_type, category, points, **kwargs):
        """
        创建积分记录的工厂方法
        
        Args:
            tenant_user_profile: 租户用户档案
            point_type: 积分类型
            category: 业务分类
            points: 积分Change数量
            **kwargs: 其他可选参数
            
        Returns:
            TenantUserPoints: 创建的积分记录
        """
        # 计算余额
        balance_before = tenant_user_profile.total_points
        balance_after = balance_before + points
        
        if balance_after < 0:
            raise ValueError(f"积分余额不足: current{balance_before}, Change{points}")
        
        # 创建记录
        record = cls.objects.create(
            tenant_user_profile=tenant_user_profile,
            tenant=tenant_user_profile.tenant,
            member=tenant_user_profile.member,
            point_type=point_type,
            category=category,
            points=points,
            balance_before=balance_before,
            balance_after=balance_after,
            tenant_multiplier=tenant_user_profile.points_multiplier,
            **kwargs
        )
        
        return record
    
    @classmethod
    def get_points_summary(cls, tenant_user_profile, days=30):
        """
        获取积分统计摘要
        
        Args:
            tenant_user_profile: 租户用户档案
            days: 统计天数
            
        Returns:
            dict: 积分统计数据
        """
        from django.db.models import Sum, Count
        from django.utils import timezone
        from datetime import timedelta
        
        start_date = timezone.now() - timedelta(days=days)
        
        queryset = cls.objects.filter(
            tenant_user_profile=tenant_user_profile,
            created_at__gte=start_date
        )
        
        # 按类型统计
        earn_points = queryset.filter(point_type='earn').aggregate(
            total=Sum('points'), count=Count('id')
        )
        spend_points = queryset.filter(point_type='spend').aggregate(
            total=Sum('points'), count=Count('id')
        )
        
        # 按分类统计
        category_stats = queryset.values('category').annotate(
            total_points=Sum('points'),
            record_count=Count('id')
        ).order_by('-total_points')
        
        return {
            'period_days': days,
            'earned': {
                'total_points': abs(earn_points['total'] or 0),
                'record_count': earn_points['count']
            },
            'spent': {
                'total_points': abs(spend_points['total'] or 0),
                'record_count': spend_points['count']
            },
            'net_change': (earn_points['total'] or 0) + (spend_points['total'] or 0),
            'category_breakdown': list(category_stats)
        }


class UserTypeTag(models.Model):
    """
    用户标签定义表，定义不同类型的用户标签（如VIP、企业用户、教育用户等）
    
    这个表定义标签的基础信息和权限配置，实际的用户标签关联通过TenantUserTypeTag管理
    """
    
    TAG_TYPE_CHOICES = [
        ('vip', 'VIP用户'),
        ('enterprise', '企业用户'),
        ('education', '教育用户'),
        ('developer', '开发者'),
        ('partner', '合作伙伴'),
        ('trial', '试用用户'),
        ('custom', '自定义'),
    ]
    
    tag_name = models.CharField(_("标签名称"), max_length=50)
    tag_code = models.CharField(_("标签代码"), max_length=20, unique=True)
    tag_type = models.CharField(_("标签类型"), max_length=20, choices=TAG_TYPE_CHOICES)
    
    # 标签显示
    tag_color = models.CharField(_("标签颜色"), max_length=7, default="#007bff")  # 十六进制颜色
    tag_icon = models.CharField(_("标签图标"), max_length=100, blank=True)
    tag_description = models.TextField(_("标签描述"), blank=True)
    
    # 权限配置
    permission_modifiers = models.JSONField(_("权限修改器"), default=dict, blank=True)
    quota_modifiers = models.JSONField(_("配额修改器"), default=dict, blank=True)
    
    # 价格配置 (用于付费标签如VIP)
    price_config = models.JSONField(_("价格配置"), default=dict, blank=True)
    
    # 期限配置
    default_duration_days = models.PositiveIntegerField(_("默认有效期天数"), null=True, blank=True)
    max_duration_days = models.PositiveIntegerField(_("最大有效期天数"), null=True, blank=True)
    
    # 标签等级
    tag_level = models.PositiveIntegerField(_("标签等级"), default=1)  # 用于标签优先级排序
    
    # 状态管理
    is_active = models.BooleanField(_("是否启用"), default=True)
    is_assignable = models.BooleanField(_("是否可分配"), default=True)
    requires_payment = models.BooleanField(_("是否需要付费"), default=False)
    
    # 审计字段
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)
    
    class Meta:
        db_table = 'user_type_tag'
        verbose_name = _('用户标签定义')
        verbose_name_plural = _('用户标签定义')
        ordering = ['-tag_level', 'tag_name']
        indexes = [
            models.Index(fields=['tag_type', 'is_active'], name='idx_user_type_tag_type_active'),
            models.Index(fields=['is_active', 'is_assignable'], name='idx_user_type_tag_assignable'),
        ]
    
    def __str__(self):
        return f"{self.tag_name} ({self.tag_code})"
    
    def get_permission_value(self, permission_key, default=None):
        """
        获取权限修改器值
        
        Args:
            permission_key: 权限键名
            default: 默认值
            
        Returns:
            权限值
        """
        return self.permission_modifiers.get(permission_key, default)
    
    def get_quota_multiplier(self, quota_key, default=1.0):
        """
        获取配额倍数
        
        Args:
            quota_key: 配额键名
            default: 默认倍数
            
        Returns:
            配额倍数
        """
        return self.quota_modifiers.get(quota_key, default)
    
    def get_price(self, currency='CNY'):
        """
        获取标签价格
        
        Args:
            currency: 货币类型
            
        Returns:
            price: 价格，None表示免费
        """
        if not self.requires_payment:
            return None
        
        prices = self.price_config.get('prices', {})
        return prices.get(currency)


class TenantUserTypeTag(models.Model):
    """
    租户用户标签关联表，管理用户在特定租户下的标签关联关系
    
    支持完整的VIP期限管理，包括过期时间、宽限期、自动续期等功能
    """
    
    GRANT_METHOD_CHOICES = [
        ('payment', '付费获得'),
        ('manual', '手动授予'),
        ('auto', '自动授予'),
        ('promotion', '促销活动'),
        ('migration', '数据迁移'),
    ]
    
    STATUS_CHOICES = [
        ('active', '有效'),
        ('expired', '已过期'),
        ('suspended', '已暂停'),
        ('cancelled', '已取消'),
        ('grace_period', '宽限期'),
    ]
    
    # 关联信息
    tenant_user_profile = models.ForeignKey(
        TenantUserProfile, 
        on_delete=models.CASCADE,
        related_name='user_tags',
        verbose_name=_("租户用户档案")
    )
    tag = models.ForeignKey(
        UserTypeTag, 
        on_delete=models.CASCADE,
        verbose_name=_("用户标签")
    )
    tenant = models.ForeignKey(
        'tenants.Tenant', 
        on_delete=models.CASCADE, 
        verbose_name=_("租户")  # 冗余字段
    )
    member = models.ForeignKey(
        'users.Member', 
        on_delete=models.CASCADE, 
        verbose_name=_("成员")  # 冗余字段
    )
    
    # 授予信息
    granted_at = models.DateTimeField(_("授予时间"), auto_now_add=True)
    granted_by_id = models.PositiveBigIntegerField(_("授予人ID"), null=True, blank=True)
    grant_reason = models.TextField(_("授予原因"), blank=True)
    grant_method = models.CharField(_("授予方式"), max_length=20, choices=GRANT_METHOD_CHOICES)
    
    # VIP期限管理
    expires_at = models.DateTimeField(_("过期时间"), null=True, blank=True)
    original_duration_days = models.PositiveIntegerField(_("原始有效期天数"), null=True, blank=True)
    extended_days = models.PositiveIntegerField(_("延期天数"), default=0)
    auto_renewal = models.BooleanField(_("是否自动续期"), default=False)
    renewal_count = models.PositiveIntegerField(_("续期次数"), default=0)
    
    # 期限计算辅助字段
    grace_period_days = models.PositiveIntegerField(_("宽限期天数"), default=0)
    reminder_sent_at = models.DateTimeField(_("过期提醒发送时间"), null=True, blank=True)
    renewal_reminder_sent = models.BooleanField(_("是否已发送续期提醒"), default=False)
    
    # 使用统计
    last_used_at = models.DateTimeField(_("最后使用时间"), null=True, blank=True)
    usage_count = models.PositiveIntegerField(_("使用次数"), default=0)
    benefits_used = models.JSONField(_("已使用的福利记录"), default=dict, blank=True)
    
    # 支付信息（用于VIP等付费标签）
    payment_id = models.PositiveBigIntegerField(_("关联的支付记录ID"), null=True, blank=True)
    payment_amount = models.DecimalField(_("支付金额"), max_digits=10, decimal_places=2, null=True, blank=True)
    payment_currency = models.CharField(_("支付货币"), max_length=3, default='CNY')
    
    # 状态管理
    is_active = models.BooleanField(_("是否有效"), default=True)
    status = models.CharField(_("状态"), max_length=20, choices=STATUS_CHOICES, default='active')
    
    # 备注信息
    notes = models.TextField(_("备注信息"), blank=True)
    metadata = models.JSONField(_("扩展元数据"), default=dict, blank=True)
    
    # 审计字段
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)
    
    class Meta:
        db_table = 'tenant_user_type_tag'
        verbose_name = _('租户用户标签关联')
        verbose_name_plural = _('租户用户标签关联')
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'member', 'tag'],
                name='unique_tenant_member_tag'
            ),
            models.CheckConstraint(
                check=models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=models.F('granted_at')),
                name='valid_expiry'
            ),
            models.CheckConstraint(
                check=models.Q(original_duration_days__isnull=True) | models.Q(original_duration_days__gt=0),
                name='valid_duration'
            ),
            models.CheckConstraint(
                check=models.Q(payment_amount__isnull=True) | models.Q(payment_amount__gte=0),
                name='valid_payment_amount'
            ),
        ]
        indexes = [
            models.Index(
                fields=['tenant_user_profile', 'is_active'], 
                name='tutt_profile'
            ),
            models.Index(
                fields=['tenant', 'member', 'is_active'], 
                name='tutt_tenant_member'
            ),
            models.Index(
                fields=['tenant', 'expires_at'], 
                name='tutt_expires',
                condition=models.Q(expires_at__isnull=False, is_active=True)
            ),
            models.Index(
                fields=['payment_id'], 
                name='tutt_payment',
                condition=models.Q(payment_id__isnull=False)
            ),
            models.Index(
                fields=['tenant', 'auto_renewal', 'expires_at'],
                name='tutt_renewal',
                condition=models.Q(auto_renewal=True, is_active=True)
            ),
        ]
    
    def __str__(self):
        member_name = self.member.username if self.member else "Unknown"
        tenant_name = self.tenant.name if self.tenant else "Unknown"
        tag_name = self.tag.tag_name if self.tag else "Unknown"
        status_str = self.get_status_display()
        return f"{member_name}@{tenant_name} - {tag_name} ({status_str})"
    
    def save(self, *args, **kwargs):
        """重写保存方法，添加业务逻辑"""
        is_new = self.pk is None
        
        # 新建时记录日志
        if is_new:
            logger.info(
                f"授予标签: {self.member.username}@{self.tenant.name} "
                f"获得 {self.tag.tag_name} 标签 ({self.grant_method})"
            )
        
        super().save(*args, **kwargs)
    
    def calculate_vip_status(self):
        """
        计算VIP状态
        
        Returns:
            dict: VIP状态信息
        """
        now = timezone.now()
        
        # 1. 检查基础过期时间
        if not self.expires_at:
            return {
                'status': 'permanent',
                'is_active': True,
                'days_remaining': None,
                'grace_period_remaining': None
            }
        
        expires_at = self.expires_at
        
        # 2. 未过期
        if now < expires_at:
            days_remaining = (expires_at - now).days
            return {
                'status': 'active',
                'is_active': True,
                'days_remaining': days_remaining,
                'expires_at': expires_at,
                'needs_renewal_reminder': days_remaining <= 7  # 7天内提醒续费
            }
        
        # 3. 已过期，检查宽限期
        grace_period_end = expires_at + timedelta(days=self.grace_period_days)
        
        if now <= grace_period_end:
            grace_days_remaining = (grace_period_end - now).days
            return {
                'status': 'grace_period',
                'is_active': True,  # 宽限期内仍可使用
                'days_remaining': 0,
                'grace_period_remaining': grace_days_remaining,
                'expires_at': expires_at,
                'grace_period_end': grace_period_end
            }
        
        # 4. 彻底过期
        return {
            'status': 'expired',
            'is_active': False,
            'days_remaining': 0,
            'grace_period_remaining': 0,
            'expired_days': (now - grace_period_end).days
        }
    
    def extend_period(self, extend_days, reason=""):
        """
        延长标签期限
        
        Args:
            extend_days: 延长天数
            reason: 延长原因
        """
        if extend_days <= 0:
            raise ValueError("Extension days must be greater than 0")
        
        if self.expires_at:
            # 从current过期时间延长
            self.expires_at = self.expires_at + timedelta(days=extend_days)
        else:
            # 永久标签设置过期时间
            self.expires_at = timezone.now() + timedelta(days=extend_days)
        
        self.extended_days = self.extended_days + extend_days
        self.notes = f"{self.notes}\n{timezone.now().strftime('%Y-%m-%d')}: 延长{extend_days}天 - {reason}".strip()
        
        self.save()
        
        logger.info(
            f"延长标签期限: {self.member.username}@{self.tenant.name} "
            f"{self.tag.tag_name} 延长{extend_days}天 - {reason}"
        )
    
    def setup_auto_renewal(self, payment_method_id):
        """
        设置自动续期
        
        Args:
            payment_method_id: 支付方式ID
        """
        self.auto_renewal = True
        if not self.metadata:
            self.metadata = {}
        self.metadata['auto_renewal_payment_method'] = payment_method_id
        
        self.save()
        
        logger.info(
            f"设置自动续期: {self.member.username}@{self.tenant.name} "
            f"{self.tag.tag_name} 设置自动续期"
        )
    
    def cancel_auto_renewal(self):
        """取消自动续期"""
        self.auto_renewal = False
        if self.metadata and 'auto_renewal_payment_method' in self.metadata:
            del self.metadata['auto_renewal_payment_method']
        
        self.save()
        
        logger.info(
            f"取消自动续期: {self.member.username}@{self.tenant.name} "
            f"{self.tag.tag_name} 取消自动续期"
        )
    
    def record_usage(self, benefit_type="", description=""):
        """
        记录标签使用
        
        Args:
            benefit_type: 福利类型
            description: 使用描述
        """
        self.last_used_at = timezone.now()
        self.usage_count += 1
        
        if benefit_type:
            if not self.benefits_used:
                self.benefits_used = {}
            
            if benefit_type not in self.benefits_used:
                self.benefits_used[benefit_type] = []
            
            self.benefits_used[benefit_type].append({
                'used_at': timezone.now().isoformat(),
                'description': description
            })
        
        self.save()
    
    def is_in_grace_period(self):
        """检查是否在宽限期内"""
        if not self.expires_at:
            return False
        
        now = timezone.now()
        if now <= self.expires_at:
            return False  # 还没过期
        
        grace_period_end = self.expires_at + timedelta(days=self.grace_period_days)
        return now <= grace_period_end