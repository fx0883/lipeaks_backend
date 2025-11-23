from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from common.models import BaseModel
import hashlib
import json
import uuid


# SoftwareProduct模型已删除，现在使用applications.Application
# 许可证相关配置（RSA密钥等）存储在Application.metadata中


class LicensePlan(BaseModel):
    """许可证方案模型"""
    
    PLAN_TYPES = [
        ('trial', '试用版'),
        ('basic', '基础版'),
        ('professional', '专业版'),
        ('enterprise', '企业版'),
        ('custom', '定制版')
    ]
    
    application = models.ForeignKey(
        'applications.Application',
        on_delete=models.CASCADE, 
        related_name='license_plans',
        verbose_name=_("关联应用"),
        null=True,
        blank=True
    )
    name = models.CharField(_("方案名称"), max_length=100)
    code = models.CharField(_("方案代码"), max_length=50)
    plan_type = models.CharField(_("方案类型"), max_length=20, choices=PLAN_TYPES)
    
    # 许可证模板配置（默认值）
    default_max_activations = models.PositiveIntegerField(_("默认最大激活数"), default=1)
    default_validity_days = models.PositiveIntegerField(_("默认有效天数"), default=365)
    
    # 功能配置
    features = models.JSONField(_("功能配置"), default=dict, blank=True)
    
    # 定价信息
    price = models.DecimalField(_("价格"), max_digits=10, decimal_places=2, default=0)
    currency = models.CharField(_("货币"), max_length=3, default='CNY')
    
    status = models.CharField(_("状态"), max_length=20, choices=[
        ('active', '启用'),
        ('inactive', '禁用')
    ], default='active')
    
    class Meta:
        db_table = 'licenses_license_plan'
        verbose_name = _("许可证方案")
        verbose_name_plural = _("许可证方案")
        unique_together = [['application', 'code']]
        indexes = [
            models.Index(fields=['application', 'plan_type']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.application.name} - {self.name}"


class License(BaseModel):
    """许可证模型"""
    
    STATUS_CHOICES = [
        ('generated', '已生成'),
        ('activated', '已激活'),
        ('suspended', '已挂起'),
        ('revoked', '已撤销'),
        ('expired', '已过期')
    ]
    
    # 基本信息
    application = models.ForeignKey(
        'applications.Application',
        on_delete=models.CASCADE,
        related_name='licenses',
        verbose_name=_("关联应用"),
        null=True,
        blank=True
    )
    plan = models.ForeignKey(
        LicensePlan,
        on_delete=models.CASCADE,
        related_name='licenses',
        verbose_name=_("许可方案")
    )
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE,
                              related_name='licenses', verbose_name=_("租户"))
    
    # 许可证标识
    license_key = models.CharField(_("许可证密钥"), max_length=200, unique=True)
    license_hash = models.CharField(_("许可证哈希"), max_length=64, unique=True, db_index=True)
    
    # 客户信息（加密存储）
    customer_name = models.CharField(_("客户名称"), max_length=100, blank=True)
    customer_email = models.EmailField(_("客户邮箱"), blank=True)
    encrypted_customer_info = models.TextField(_("加密客户信息"), blank=True)
    
    # 许可证配置
    max_activations = models.PositiveIntegerField(_("最大激活数"), default=1)
    current_activations = models.PositiveIntegerField(_("current激活数"), default=0)
    
    # 时间控制
    issued_at = models.DateTimeField(_("签发时间"), auto_now_add=True)
    expires_at = models.DateTimeField(_("过期时间"))
    last_verified_at = models.DateTimeField(_("最后验证时间"), null=True, blank=True)
    
    # 状态管理
    status = models.CharField(_("状态"), max_length=20, choices=STATUS_CHOICES, default='generated')
    
    # 元数据
    metadata = models.JSONField(_("元数据"), default=dict, blank=True)
    notes = models.TextField(_("备注"), blank=True)
    
    class Meta:
        db_table = 'licenses_license'
        verbose_name = _("许可证")
        verbose_name_plural = _("许可证")
        indexes = [
            models.Index(fields=['license_hash']),
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['application', 'status']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def clean(self):
        """数据验证"""
        super().clean()
        
        # 验证plan和application的一致性
        if self.plan and self.application:
            if self.plan.application != self.application:
                from django.core.exceptions import ValidationError
                raise ValidationError({
                    'application': f'所选应用({self.application.name})与方案所属应用({self.plan.application.name})不一致',
                    'plan': f'方案({self.plan.name})属于应用({self.plan.application.name})，不能用于应用({self.application.name})'
                })
        
        # 如果只有plan没有application，自动设置application
        if self.plan and not self.application:
            self.application = self.plan.application

    def save(self, *args, **kwargs):
        """保存时自动生成许可证哈希并验证数据"""
        # 先进行数据验证
        self.clean()
        
        # 生成许可证哈希
        if self.license_key and not self.license_hash:
            self.license_hash = hashlib.sha256(self.license_key.encode()).hexdigest()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.application.name} - {self.customer_name or 'Unknown'} ({self.status})"
    
    def update_from_plan(self, force=False):
        """
        从计划更新配置（仅在必要时）
        
        Args:
            force (bool): 是否强制更新，无论值是否相同
        
        Returns:
            bool: 是否进行了更新
        """
        from django.utils import timezone
        
        updated = False
        update_fields = []
        
        # 检查并更新最大激活数
        if force or self.max_activations != self.plan.default_max_activations:
            self.max_activations = self.plan.default_max_activations
            update_fields.append('max_activations')
            updated = True
        
        # 如果有更新，保存并记录
        if updated:
            update_fields.append('updated_at')
            self.save(update_fields=update_fields)
            
            # 记录更新日志
            import logging
            logger = logging.getLogger('licenses.business')
            logger.info(f"许可证 {self.id} 从计划 {self.plan.id} 更新配置: {update_fields}")
        
        return updated
    
    def extend_validity(self, days):
        """
        延长有效期
        
        Args:
            days (int): 延长的天数
        """
        from datetime import timedelta
        
        if days <= 0:
            raise ValueError("Extension days must be greater than 0")
        
        old_expires_at = self.expires_at
        self.expires_at += timedelta(days=days)
        self.save(update_fields=['expires_at', 'updated_at'])
        
        # 记录延期日志
        import logging
        logger = logging.getLogger('licenses.business')
        logger.info(f"许可证 {self.id} 延期 {days} 天: {old_expires_at} -> {self.expires_at}")
    
    def upgrade_to_plan(self, new_plan):
        """
        升级到新计划
        
        Args:
            new_plan (LicensePlan): 新的许可证计划
        """
        if new_plan.product != self.product:
            raise ValueError(f"New plan {new_plan.id} does not belong to current product {self.product.id}")
        
        old_plan = self.plan
        self.plan = new_plan
        
        # 更新相关配置
        self.max_activations = new_plan.default_max_activations
        self.save(update_fields=['plan', 'max_activations', 'updated_at'])
        
        # 记录升级日志
        import logging
        logger = logging.getLogger('licenses.business')
        logger.info(f"许可证 {self.id} 从计划 {old_plan.id} 升级到 {new_plan.id}")
    
    def is_outdated_config(self):
        """
        检查许可证配置是否过时（与计划不一致）
        
        Returns:
            bool: 配置是否过时
        """
        return (
            self.max_activations != self.plan.default_max_activations or
            self.updated_at < self.plan.updated_at
        )


class MachineBinding(BaseModel):
    """机器绑定模型"""
    
    STATUS_CHOICES = [
        ('active', '活跃'),
        ('inactive', '非活跃'),
        ('blocked', '已阻止')
    ]
    
    license = models.ForeignKey(License, on_delete=models.CASCADE,
                               related_name='machine_bindings', verbose_name=_("关联许可证"))
    
    # 机器标识
    machine_id = models.CharField(_("机器ID"), max_length=100, db_index=True)
    machine_fingerprint = models.CharField(_("机器指纹"), max_length=64, db_index=True)
    
    # 硬件信息（加密存储）
    encrypted_hardware_info = models.TextField(_("加密硬件信息"))
    
    # 系统信息
    os_info = models.JSONField(_("操作系统信息"), default=dict)
    hardware_summary = models.JSONField(_("硬件摘要"), default=dict)
    
    # 网络信息
    last_ip_address = models.GenericIPAddressField(_("最后IP地址"), null=True, blank=True)
    last_location = models.JSONField(_("最后位置"), default=dict, blank=True)
    
    # 状态管理
    status = models.CharField(_("状态"), max_length=20, choices=STATUS_CHOICES, default='active')
    first_seen_at = models.DateTimeField(_("首次绑定时间"), auto_now_add=True)
    last_seen_at = models.DateTimeField(_("最后活跃时间"), auto_now=True)
    
    class Meta:
        db_table = 'licenses_machine_binding'
        verbose_name = _("机器绑定")
        verbose_name_plural = _("机器绑定")
        unique_together = [['license', 'machine_fingerprint']]
        indexes = [
            models.Index(fields=['license', 'status']),
            models.Index(fields=['machine_fingerprint']),
            models.Index(fields=['status', 'last_seen_at']),
        ]
    
    def __str__(self):
        return f"{self.license.product.name} - {self.machine_id[:8]}..."


class LicenseActivation(BaseModel):
    """许可证激活记录模型"""
    
    ACTIVATION_TYPES = [
        ('online', '在线激活'),
        ('offline', '离线激活')
    ]
    
    RESULT_CHOICES = [
        ('success', '成功'),
        ('failed', '失败'),
        ('pending', '待处理')
    ]
    
    license = models.ForeignKey(License, on_delete=models.CASCADE,
                               related_name='activations', verbose_name=_("关联许可证"))
    machine_binding = models.ForeignKey(MachineBinding, on_delete=models.CASCADE,
                                       related_name='activations', verbose_name=_("机器绑定"))
    
    # 激活信息
    activation_type = models.CharField(_("激活类型"), max_length=20, choices=ACTIVATION_TYPES)
    activation_code = models.CharField(_("激活码"), max_length=100, unique=True)
    
    # 请求信息
    client_version = models.CharField(_("客户端版本"), max_length=50, blank=True)
    user_agent = models.TextField(_("用户代理"), blank=True)
    ip_address = models.GenericIPAddressField(_("IP地址"), null=True, blank=True)
    
    # 结果信息
    result = models.CharField(_("激活结果"), max_length=20, choices=RESULT_CHOICES, default='pending')
    error_message = models.TextField(_("错误消息"), blank=True)
    
    # 时间记录
    activated_at = models.DateTimeField(_("激活时间"), auto_now_add=True)
    expires_at = models.DateTimeField(_("过期时间"), null=True, blank=True)
    
    class Meta:
        db_table = 'licenses_activation'
        verbose_name = _("许可证激活")
        verbose_name_plural = _("许可证激活")
        indexes = [
            models.Index(fields=['license', 'result']),
            models.Index(fields=['activation_code']),
            models.Index(fields=['result', 'activated_at']),
            models.Index(fields=['ip_address', 'activated_at']),
        ]
    
    def __str__(self):
        return f"{self.license.product.name} - {self.result} ({self.activated_at})"


class LicenseUsageLog(BaseModel):
    """许可证使用日志模型"""
    
    EVENT_TYPES = [
        ('startup', '软件启动'),
        ('heartbeat', '心跳检测'),
        ('feature_use', '功能使用'),
        ('shutdown', '软件关闭'),
        ('verification', '在线验证')
    ]
    
    license = models.ForeignKey(License, on_delete=models.CASCADE,
                               related_name='usage_logs', verbose_name=_("关联许可证"))
    machine_binding = models.ForeignKey(MachineBinding, on_delete=models.CASCADE,
                                       related_name='usage_logs', verbose_name=_("机器绑定"))
    
    # 事件信息
    event_type = models.CharField(_("事件类型"), max_length=20, choices=EVENT_TYPES)
    event_data = models.JSONField(_("事件数据"), default=dict, blank=True)
    
    # 软件信息
    software_version = models.CharField(_("软件版本"), max_length=50, blank=True)
    session_id = models.CharField(_("会话ID"), max_length=100, blank=True)
    
    # 系统状态
    cpu_usage = models.FloatField(_("CPU使用率"), null=True, blank=True)
    memory_usage = models.FloatField(_("内存使用率"), null=True, blank=True)
    
    # 网络信息
    ip_address = models.GenericIPAddressField(_("IP地址"), null=True, blank=True)
    
    # 时间记录
    timestamp = models.DateTimeField(_("时间戳"), auto_now_add=True)
    
    class Meta:
        db_table = 'licenses_usage_log'
        verbose_name = _("使用日志")
        verbose_name_plural = _("使用日志")
        indexes = [
            models.Index(fields=['license', 'event_type', 'timestamp']),
            models.Index(fields=['machine_binding', 'timestamp']),
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.license.application.name} - {self.event_type} ({self.timestamp})"


class TenantLicenseQuota(BaseModel):
    """租户许可证配额模型"""
    
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE,
                              related_name='license_quotas', verbose_name=_("租户"))
    application = models.ForeignKey(
        'applications.Application',
        on_delete=models.CASCADE,
        related_name='tenant_quotas',
        verbose_name=_("应用"),
        null=True,
        blank=True
    )
    
    # 配额限制
    max_licenses = models.PositiveIntegerField(_("最大许可证数"), default=10)
    current_licenses = models.PositiveIntegerField(_("current许可证数"), default=0)
    
    # 时间限制
    quota_start_date = models.DateField(_("配额开始日期"))
    quota_end_date = models.DateField(_("配额结束日期"))
    
    # 状态管理
    is_active = models.BooleanField(_("是否激活"), default=True)
    
    class Meta:
        db_table = 'licenses_tenant_quota'
        verbose_name = _("租户许可证配额")
        verbose_name_plural = _("租户许可证配额")
        unique_together = [['tenant', 'application']]
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
            models.Index(fields=['application', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.tenant.name} - {self.application.name} ({self.current_licenses}/{self.max_licenses})"


class SecurityAuditLog(BaseModel):
    """安全审计日志模型"""
    
    EVENT_TYPES = [
        ('license_generated', '许可证生成'),
        ('license_activated', '许可证激活'),
        ('license_revoked', '许可证撤销'),
        ('keypair_generated', '密钥对生成'),
        ('suspicious_activity', '可疑活动'),
        ('authentication_failed', '认证失败'),
        ('privilege_escalation', '权限提升'),
        ('data_access', '数据访问'),
        ('system_change', '系统变更')
    ]
    
    SEVERITY_LEVELS = [
        ('LOW', '低'),
        ('MEDIUM', '中'),
        ('HIGH', '高'),
        ('CRITICAL', '严重'),
    ]
    
    # 事件信息
    event_type = models.CharField(_("事件类型"), max_length=50, choices=EVENT_TYPES)
    severity = models.CharField(_("严重级别"), max_length=10, choices=SEVERITY_LEVELS)
    
    # 关联对象
    user = models.ForeignKey('users.User', on_delete=models.SET_NULL, 
                            null=True, blank=True, verbose_name=_("用户"))
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.SET_NULL,
                              null=True, blank=True, verbose_name=_("租户"))
    
    # 请求信息
    ip_address = models.GenericIPAddressField(_("IP地址"), null=True, blank=True)
    user_agent = models.TextField(_("用户代理"), blank=True)
    
    # 详细信息
    details = models.JSONField(_("事件详情"), default=dict)
    
    # 时间记录
    timestamp = models.DateTimeField(_("时间戳"), auto_now_add=True)
    
    class Meta:
        db_table = 'licenses_security_audit_log'
        verbose_name = _("安全审计日志")
        verbose_name_plural = _("安全审计日志")
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['event_type', 'timestamp']),
            models.Index(fields=['severity', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.severity} ({self.timestamp})"


class LicenseAssignment(BaseModel):
    """
    许可证分配关联模型，管理Member和License之间的分配关系
    
    这是一个多对多关联表，实现了许可证与用户的分配管理，支持多租户权限检查，
    确保与现有的License和Member模型完全解耦，不修改任何现有代码
    """
    
    ASSIGNMENT_TYPE_CHOICES = [
        ('direct', '直接分配'),
        ('inherited', '继承分配'),
        ('shared', '共享分配'),
        ('temporary', '临时分配'),
    ]
    
    ASSIGNMENT_STATUS_CHOICES = [
        ('active', '有效'),
        ('suspended', '已挂起'),
        ('revoked', '已撤销'),
        ('expired', '已过期'),
        ('pending', '待激活'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', '低'),
        ('normal', '普通'),
        ('high', '高'),
        ('urgent', '紧急'),
    ]
    
    # 核心关联 - 保持与现有模型完全解耦
    member = models.ForeignKey(
        'users.Member', 
        on_delete=models.CASCADE,
        related_name='license_assignments',
        verbose_name=_("分配成员")
    )
    license = models.ForeignKey(
        License, 
        on_delete=models.CASCADE,
        related_name='member_assignments',
        verbose_name=_("分配许可证")
    )
    tenant = models.ForeignKey(
        'tenants.Tenant', 
        on_delete=models.CASCADE,
        verbose_name=_("关联租户")  # 冗余字段，确保租户隔离
    )
    
    # 分配配置
    assignment_type = models.CharField(_("分配类型"), max_length=20, choices=ASSIGNMENT_TYPE_CHOICES, default='direct')
    assignment_reason = models.TextField(_("分配原因"), blank=True)
    priority = models.CharField(_("优先级"), max_length=10, choices=PRIORITY_CHOICES, default='normal')
    
    # 权限级别设置
    can_activate = models.BooleanField(_("允许激活"), default=True)
    can_deactivate = models.BooleanField(_("允许停用"), default=False)
    can_share = models.BooleanField(_("允许共享"), default=False)
    max_devices_per_user = models.PositiveIntegerField(_("用户最大设备数"), default=1)
    
    # 时间控制
    assigned_at = models.DateTimeField(_("分配时间"), auto_now_add=True)
    activated_at = models.DateTimeField(_("激活时间"), null=True, blank=True)
    expires_at = models.DateTimeField(_("分配过期时间"), null=True, blank=True)
    last_used_at = models.DateTimeField(_("最后使用时间"), null=True, blank=True)
    
    # 状态管理
    status = models.CharField(_("分配状态"), max_length=20, choices=ASSIGNMENT_STATUS_CHOICES, default='active')
    is_primary = models.BooleanField(_("是否主要分配"), default=False)  # 一个许可证可以有一个主要分配者
    
    # 使用统计
    usage_count = models.PositiveIntegerField(_("使用次数"), default=0)
    last_heartbeat = models.DateTimeField(_("最后心跳时间"), null=True, blank=True)
    
    # 操作审计
    assigned_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_licenses',
        verbose_name=_("分配操作员")
    )
    revoked_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='revoked_license_assignments',
        verbose_name=_("撤销操作员")
    )
    revoked_at = models.DateTimeField(_("撤销时间"), null=True, blank=True)
    revoke_reason = models.TextField(_("撤销原因"), blank=True)
    
    # 扩展配置
    assignment_metadata = models.JSONField(_("分配元数据"), default=dict, blank=True)
    
    class Meta:
        db_table = 'licenses_license_assignment'
        verbose_name = _('许可证分配')
        verbose_name_plural = _('许可证分配')
        constraints = [
            models.UniqueConstraint(
                fields=['member', 'license'],
                name='unique_member_license_assignment'
            ),
            models.CheckConstraint(
                check=models.Q(max_devices_per_user__gte=1),
                name='valid_max_devices'
            ),
            models.CheckConstraint(
                check=models.Q(usage_count__gte=0),
                name='valid_usage_count'
            ),
            models.CheckConstraint(
                check=models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=models.F('assigned_at')),
                name='valid_assignment_expiry'
            ),
        ]
        indexes = [
            models.Index(fields=['member', 'status'], name='la_member_status'),
            models.Index(fields=['license', 'status'], name='la_license_status'),
            models.Index(fields=['tenant', 'status'], name='la_tenant_status'),
            models.Index(fields=['tenant', 'member', 'status'], name='la_tenant_member'),
            models.Index(fields=['assigned_at'], name='la_assigned_at'),
            models.Index(fields=['expires_at'], name='la_expires_at',
                        condition=models.Q(expires_at__isnull=False)),
            models.Index(fields=['is_primary', 'license'], name='la_primary'),
            models.Index(fields=['last_used_at'], name='la_last_used',
                        condition=models.Q(last_used_at__isnull=False)),
        ]
    
    def __str__(self):
        member_name = self.member.username if self.member else "Unknown"
        license_key = self.license.license_key[-8:] if self.license and self.license.license_key else "Unknown"
        status_display = self.get_status_display()
        return f"{member_name} → {license_key}*** ({status_display})"
    
    def clean(self):
        """数据验证"""
        super().clean()
        
        # 验证租户一致性
        if self.member and self.license:
            if self.member.tenant_id != self.license.tenant_id:
                from django.core.exceptions import ValidationError
                raise ValidationError({
                    'tenant': f'成员所属租户({self.member.tenant_id})与许可证租户({self.license.tenant_id})不一致'
                })
        
        # 设置租户ID（确保一致性）
        if self.member and not self.tenant_id:
            self.tenant = self.member.tenant
        
        # 验证过期时间
        if self.expires_at and self.license and self.license.expires_at:
            if self.expires_at > self.license.expires_at:
                from django.core.exceptions import ValidationError
                raise ValidationError({
                    'expires_at': '分配过期时间不能超过许可证过期时间'
                })
    
    def save(self, *args, **kwargs):
        """保存时进行数据验证和业务逻辑处理"""
        # 先进行数据验证
        self.clean()
        
        is_new = self.pk is None
        
        # 新建分配时的处理
        if is_new:
            # 检查License的激活配额
            if self.license:
                current_assignments = LicenseAssignment.objects.filter(
                    license=self.license,
                    status='active'
                ).exclude(pk=self.pk).count()
                
                if current_assignments >= self.license.max_activations:
                    raise ValueError(f"许可证激活配额已满，最大支持 {self.license.max_activations} 个激活")
                
                # 自动更新License的current_activations计数
                self.license.current_activations = current_assignments + 1
                self.license.save(update_fields=['current_activations'])
        
        super().save(*args, **kwargs)
    
    def activate(self):
        """激活分配"""
        if self.status != 'pending':
            raise ValueError(f"只能激活待激活状态的分配，Current status: {self.get_status_display()}")
        
        if not self.can_activate:
            raise ValueError("Current assignment does not allow activation")
        
        # 检查许可证状态
        if self.license.status not in ['generated', 'activated']:
            raise ValueError(f"许可证状态不允许激活: {self.license.get_status_display()}")
        
        # 检查过期时间
        from django.utils import timezone
        now = timezone.now()
        if self.expires_at and now > self.expires_at:
            raise ValueError("Assignment has expired and cannot be activated")
        
        if self.license.expires_at and now > self.license.expires_at:
            raise ValueError("License has expired and cannot be activated")
        
        # 执行激活
        self.status = 'active'
        self.activated_at = now
        self.save()
        
        return True
    
    def revoke(self, reason="", operator=None):
        """撤销分配"""
        if self.status in ['revoked', 'expired']:
            raise ValueError(f"无法撤销已撤销或已过期的分配，Current status: {self.get_status_display()}")
        
        from django.utils import timezone
        import logging
        
        logger = logging.getLogger('licenses.models')
        
        self.status = 'revoked'
        self.revoked_at = timezone.now()
        self.revoke_reason = reason
        if operator:
            self.revoked_by = operator
        
        # ✅ 删除该许可证的所有激活记录，防止继续使用 activation_code
        if self.license:
            deleted_activations = LicenseActivation.objects.filter(
                license=self.license,
                result='success'
            ).delete()
            
            activation_count = deleted_activations[0] if deleted_activations else 0
            if activation_count > 0:
                logger.info(
                    f"撤销许可证分配 {self.id}：删除了 {activation_count} 条激活记录"
                )
            
            # 禁用该许可证的所有机器绑定
            updated_bindings = MachineBinding.objects.filter(
                license=self.license,
                status='active'
            ).update(status='inactive')
            
            if updated_bindings > 0:
                logger.info(
                    f"撤销许可证分配 {self.id}：禁用了 {updated_bindings} 个机器绑定"
                )
            
            # 更新License的current_activations计数
            active_assignments = LicenseAssignment.objects.filter(
                license=self.license,
                status='active'
            ).exclude(pk=self.pk).count()
            
            self.license.current_activations = active_assignments
            self.license.save(update_fields=['current_activations'])
        
        self.save()
        
        return True
    
    def record_usage(self):
        """记录使用情况"""
        from django.utils import timezone
        
        self.usage_count += 1
        self.last_used_at = timezone.now()
        self.last_heartbeat = timezone.now()
        
        self.save(update_fields=['usage_count', 'last_used_at', 'last_heartbeat'])
    
    def is_expired(self):
        """检查是否已过期"""
        from django.utils import timezone
        now = timezone.now()
        
        # 检查分配过期时间
        if self.expires_at and now > self.expires_at:
            return True
        
        # 检查许可证过期时间
        if self.license and self.license.expires_at and now > self.license.expires_at:
            return True
        
        return False
    
    def get_effective_permissions(self):
        """
        获取有效权限（结合用户等级和VIP标签的权限增强）
        
        Returns:
            dict: 有效权限配置
        """
        base_permissions = {
            'can_activate': self.can_activate,
            'can_deactivate': self.can_deactivate,
            'can_share': self.can_share,
            'max_devices_per_user': self.max_devices_per_user,
        }
        
        try:
            # 尝试获取用户的积分档案（需要points app）
            from points.models import TenantUserProfile
            
            profile = TenantUserProfile.objects.filter(
                member=self.member,
                tenant=self.tenant
            ).first()
            
            if profile:
                # 应用等级权限增强
                if profile.current_level:
                    level_permissions = profile.current_level.permissions or {}
                    for key, modifier in level_permissions.items():
                        if key in base_permissions:
                            if isinstance(modifier, (int, float)) and isinstance(base_permissions[key], (int, float)):
                                # 数值类型应用倍数
                                base_permissions[key] = int(base_permissions[key] * modifier)
                            elif isinstance(modifier, bool):
                                # 布尔类型直接覆盖
                                base_permissions[key] = modifier
                
                # 应用VIP标签权限增强
                for user_tag in profile.user_tags.filter(is_active=True, status='active'):
                    tag_permissions = user_tag.tag.permission_modifiers or {}
                    for key, modifier in tag_permissions.items():
                        if key in base_permissions:
                            if isinstance(modifier, (int, float)) and isinstance(base_permissions[key], (int, float)):
                                # VIP标签通常提供额外的倍数增强
                                base_permissions[key] = int(base_permissions[key] * modifier)
                            elif isinstance(modifier, bool):
                                # VIP通常解锁更多权限
                                base_permissions[key] = base_permissions[key] or modifier
        
        except ImportError:
            # points app未安装，使用基础权限
            pass
        
        return base_permissions
    
    @classmethod
    def create_assignment(cls, member, license, assignment_type='direct', reason="", operator=None, **kwargs):
        """
        创建许可证分配的工厂方法
        
        Args:
            member: Member实例
            license: License实例  
            assignment_type: 分配类型
            reason: 分配原因
            operator: 操作员
            **kwargs: 其他配置参数
            
        Returns:
            LicenseAssignment: 创建的分配实例
        """
        # 验证租户一致性
        if member.tenant_id != license.tenant_id:
            raise ValueError(f"Member tenant({member.tenant_id})does not match license tenant({license.tenant_id})不一致")
        
        # 检查是否已存在分配
        existing = cls.objects.filter(member=member, license=license).first()
        if existing and existing.status == 'active':
            raise ValueError(f"Member {member.username} already assigned license {license.license_key}")
        
        # 创建分配
        assignment = cls.objects.create(
            member=member,
            license=license,
            tenant=member.tenant,
            assignment_type=assignment_type,
            assignment_reason=reason,
            assigned_by=operator,
            **kwargs
        )
        
        return assignment
    
    @classmethod
    def get_tenant_assignments(cls, tenant, include_inactive=False):
        """
        获取租户下的所有分配
        
        Args:
            tenant: Tenant实例
            include_inactive: 是否包含非活跃分配
            
        Returns:
            QuerySet: 分配查询集
        """
        queryset = cls.objects.filter(tenant=tenant)
        
        if not include_inactive:
            queryset = queryset.filter(status='active')
        
        return queryset.select_related('member', 'license', 'assigned_by')
