from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from common.models import BaseModel
import hashlib
import json
import uuid


class SoftwareProduct(BaseModel):
    """软件产品模型"""
    
    name = models.CharField(_("产品名称"), max_length=100)
    code = models.CharField(_("产品代码"), max_length=50, unique=True)
    description = models.TextField(_("产品描述"), blank=True)
    version = models.CharField(_("版本号"), max_length=20, default="1.0.0")
    
    # RSA密钥对（公钥存储，私钥哈希）
    public_key = models.TextField(_("RSA公钥"))
    private_key_hash = models.CharField(_("私钥哈希"), max_length=64)
    
    # 安全配置
    max_activations = models.PositiveIntegerField(_("最大激活数"), default=5)
    offline_days = models.PositiveIntegerField(_("离线允许天数"), default=30)
    
    # 状态管理
    status = models.CharField(_("状态"), max_length=20, choices=[
        ('active', '启用'),
        ('inactive', '禁用'),
        ('deprecated', '已弃用')
    ], default='active')
    
    class Meta:
        db_table = 'licenses_software_product'
        verbose_name = _("软件产品")
        verbose_name_plural = _("软件产品")
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class LicensePlan(BaseModel):
    """许可证方案模型"""
    
    PLAN_TYPES = [
        ('trial', '试用版'),
        ('basic', '基础版'),
        ('professional', '专业版'),
        ('enterprise', '企业版'),
        ('custom', '定制版')
    ]
    
    product = models.ForeignKey(SoftwareProduct, on_delete=models.CASCADE, 
                               related_name='license_plans', verbose_name=_("关联产品"))
    name = models.CharField(_("方案名称"), max_length=100)
    code = models.CharField(_("方案代码"), max_length=50)
    plan_type = models.CharField(_("方案类型"), max_length=20, choices=PLAN_TYPES)
    
    # 许可证限制
    max_machines = models.PositiveIntegerField(_("最大机器数"), default=1)
    validity_days = models.PositiveIntegerField(_("有效天数"), default=365)
    
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
        unique_together = [['product', 'code']]
        indexes = [
            models.Index(fields=['product', 'plan_type']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.product.name} - {self.name}"


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
    product = models.ForeignKey(SoftwareProduct, on_delete=models.CASCADE,
                               related_name='licenses', verbose_name=_("关联产品"))
    plan = models.ForeignKey(LicensePlan, on_delete=models.CASCADE,
                            related_name='licenses', verbose_name=_("许可方案"))
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
    current_activations = models.PositiveIntegerField(_("当前激活数"), default=0)
    
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
            models.Index(fields=['product', 'status']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def clean(self):
        """数据验证"""
        super().clean()
        
        # 验证plan和product的一致性
        if self.plan and self.product:
            if self.plan.product != self.product:
                from django.core.exceptions import ValidationError
                raise ValidationError({
                    'product': f'所选产品({self.product.name})与方案所属产品({self.plan.product.name})不一致',
                    'plan': f'方案({self.plan.name})属于产品({self.plan.product.name})，不能用于产品({self.product.name})'
                })
        
        # 如果只有plan没有product，自动设置product
        if self.plan and not self.product:
            self.product = self.plan.product

    def save(self, *args, **kwargs):
        """保存时自动生成许可证哈希并验证数据"""
        # 先进行数据验证
        self.clean()
        
        # 生成许可证哈希
        if self.license_key and not self.license_hash:
            self.license_hash = hashlib.sha256(self.license_key.encode()).hexdigest()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.product.name} - {self.customer_name or 'Unknown'} ({self.status})"


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
        return f"{self.license.product.name} - {self.event_type} ({self.timestamp})"


class TenantLicenseQuota(BaseModel):
    """租户许可证配额模型"""
    
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE,
                              related_name='license_quotas', verbose_name=_("租户"))
    product = models.ForeignKey(SoftwareProduct, on_delete=models.CASCADE,
                               related_name='tenant_quotas', verbose_name=_("产品"))
    
    # 配额限制
    max_licenses = models.PositiveIntegerField(_("最大许可证数"), default=10)
    current_licenses = models.PositiveIntegerField(_("当前许可证数"), default=0)
    
    # 时间限制
    quota_start_date = models.DateField(_("配额开始日期"))
    quota_end_date = models.DateField(_("配额结束日期"))
    
    # 状态管理
    is_active = models.BooleanField(_("是否激活"), default=True)
    
    class Meta:
        db_table = 'licenses_tenant_quota'
        verbose_name = _("租户许可证配额")
        verbose_name_plural = _("租户许可证配额")
        unique_together = [['tenant', 'product']]
        indexes = [
            models.Index(fields=['tenant', 'is_active']),
            models.Index(fields=['product', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.tenant.name} - {self.product.name} ({self.current_licenses}/{self.max_licenses})"


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
