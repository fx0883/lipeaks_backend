"""
基础模型定义，用于提供租户隔离和软删除等共通功能
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from common.utils.tenant_manager import TenantManager

class BaseModel(models.Model):
    """
    基础模型，所有需要租户隔离的模型都应该继承此模型
    """
    tenant = models.ForeignKey(
        'tenants.Tenant', 
        on_delete=models.CASCADE, 
        verbose_name=_("租户"),
        related_name="%(class)s_set",
        db_index=True,
        null=True
    )
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True, null=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True, null=True)
    is_deleted = models.BooleanField(_("是否删除"), default=False)
    
    # 默认管理器 - 按租户过滤
    objects = TenantManager()
    
    # 原始管理器 - 不过滤，用于管理员访问所有数据
    original_objects = models.Manager()
    
    class Meta:
        abstract = True
        ordering = ['-created_at']

    def soft_delete(self):
        """
        软删除方法
        """
        self.is_deleted = True
        self.save(update_fields=['is_deleted', 'updated_at'])
        return self


class APILog(models.Model):
    """
    API访问日志模型
    用于记录API请求信息，便于审计和排查问题
    """
    REQUEST_METHOD_CHOICES = (
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('PATCH', 'PATCH'),
        ('DELETE', 'DELETE'),
        ('OPTIONS', 'OPTIONS'),
        ('HEAD', 'HEAD'),
    )
    
    STATUS_TYPE_CHOICES = (
        ('success', '成功'),
        ('error', '错误'),
    )
    
    # 请求信息
    user = models.ForeignKey(
        'users.User', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='api_logs',
        verbose_name=_("用户")
    )
    tenant = models.ForeignKey(
        'tenants.Tenant', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='api_logs',
        verbose_name=_("租户")
    )
    ip_address = models.CharField(_("IP地址"), max_length=50)
    request_method = models.CharField(_("请求方法"), max_length=10, choices=REQUEST_METHOD_CHOICES)
    request_path = models.CharField(_("请求路径"), max_length=255)
    view_name = models.CharField(_("视图名称"), max_length=255, null=True, blank=True)
    query_params = models.JSONField(_("查询参数"), null=True, blank=True)
    request_body = models.JSONField(_("请求体"), null=True, blank=True)
    
    # 响应信息
    status_code = models.IntegerField(_("状态码"))
    response_time = models.IntegerField(_("响应时间(ms)"))
    status_type = models.CharField(_("状态类型"), max_length=10, choices=STATUS_TYPE_CHOICES)
    response_body = models.JSONField(_("响应体"), null=True, blank=True)
    error_message = models.TextField(_("错误信息"), null=True, blank=True)
    
    # 其他信息
    user_agent = models.CharField(_("用户代理"), max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    
    class Meta:
        verbose_name = _('API日志')
        verbose_name_plural = _('API日志')
        db_table = 'common_api_log'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['tenant']),
            models.Index(fields=['request_path']),
            models.Index(fields=['status_code']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.request_method} {self.request_path} - {self.status_code}"


class Config(models.Model):
    """
    系统配置模型
    用于存储系统级别的配置信息，包括超级管理员菜单配置等
    """
    CONFIG_TYPE_CHOICES = (
        ('menu', '菜单配置'),
        ('system', '系统配置'),
        ('feature', '功能配置'),
        ('other', '其他配置'),
    )
    
    name = models.CharField(_("配置名称"), max_length=100, unique=True)
    key = models.CharField(_("配置键"), max_length=100, unique=True)
    value = models.JSONField(_("配置值"), default=dict)
    type = models.CharField(_("配置类型"), max_length=20, choices=CONFIG_TYPE_CHOICES, default='other')
    description = models.TextField(_("配置描述"), null=True, blank=True)
    is_active = models.BooleanField(_("是否启用"), default=True)
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_configs',
        verbose_name=_('创建人')
    )
    updated_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='updated_configs',
        verbose_name=_('更新人')
    )
    
    class Meta:
        verbose_name = _('系统配置')
        verbose_name_plural = _('系统配置')
        db_table = 'common_config'
        ordering = ['type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.key})"
