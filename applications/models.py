"""
应用管理模型
整合licenses.SoftwareProduct和feedbacks.Software
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from common.models import BaseModel


class Application(BaseModel):
    """
    租户应用（精简版）
    整合了licenses.SoftwareProduct和feedbacks.Software
    """
    # === 基本信息 ===
    name = models.CharField(
        _("应用名称"), 
        max_length=100,
        help_text="应用的显示名称"
    )
    code = models.CharField(
        _("应用代码"), 
        max_length=50,
        help_text="应用的唯一标识符（租户内唯一）"
    )
    description = models.TextField(
        _("应用描述"),
        blank=True
    )
    
    # === 展示信息 ===
    logo = models.CharField(
        _("Logo"),
        max_length=255,
        blank=True,
        null=True,
        help_text="应用Logo地址（可使用CDN或OSS链接）"
    )
    website = models.URLField(
        _("官网"),
        blank=True,
        null=True,
        help_text="应用官方网站"
    )
    contact_email = models.EmailField(
        _("联系邮箱"),
        blank=True,
        null=True
    )
    
    # === 版本管理 ===
    current_version = models.CharField(
        _("当前版本"),
        max_length=50,
        default="1.0.0",
        blank=True,
        help_text="当前发布的版本号，如: v1.2.3"
    )
    
    # === 团队信息 ===
    owner = models.CharField(
        _("负责人"),
        max_length=100,
        blank=True,
        help_text="应用负责人姓名"
    )
    team = models.CharField(
        _("开发团队"),
        max_length=200,
        blank=True,
        help_text="开发团队名称"
    )
    
    # === 状态管理 ===
    STATUS_CHOICES = [
        ('development', '开发中'),
        ('testing', '测试中'),
        ('active', '运行中'),
        ('maintenance', '维护中'),
        ('deprecated', '已弃用'),
        ('archived', '已归档'),
    ]
    status = models.CharField(
        _("状态"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        db_index=True
    )
    is_active = models.BooleanField(
        _("启用"),
        default=True,
        help_text="是否启用该应用"
    )
    
    # === 元数据 ===
    tags = models.JSONField(
        _("标签"),
        default=list,
        blank=True,
        help_text="应用标签列表，用于分类和搜索"
    )
    metadata = models.JSONField(
        _("元数据"),
        default=dict,
        blank=True,
        help_text="其他自定义元数据"
    )
    
    class Meta:
        db_table = 'app_application'
        verbose_name = _('应用')
        verbose_name_plural = _('应用')
        ordering = ['name']
        indexes = [
            models.Index(fields=['tenant', 'code']),
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['tenant', 'is_active']),
        ]
        unique_together = [['tenant', 'code']]
    
    def __str__(self):
        return f"{self.name} ({self.code})"
    
    # === 统计方法（查询时计算）===
    
    def get_license_count(self):
        """获取许可证数量（查询时计算）"""
        return self.licenses.count()
    
    def get_active_license_count(self):
        """获取活跃许可证数量"""
        return self.licenses.filter(status='activated').count()
    
    def get_feedback_count(self):
        """获取反馈数量"""
        return self.feedbacks.count()
    
    def get_open_feedback_count(self):
        """获取未关闭反馈数量"""
        return self.feedbacks.filter(
            status__in=['submitted', 'reviewing', 'confirmed']
        ).count()
    
    def get_article_count(self):
        """获取关联文章数量"""
        return self.articleapplication_set.count()
