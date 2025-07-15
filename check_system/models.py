"""
打卡系统模型定义
"""
import logging
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from users.models import User
from tenants.models import Tenant

logger = logging.getLogger(__name__)


class TaskCategory(models.Model):
    """
    打卡类型模型，用于对打卡任务进行分类
    """
    name = models.CharField(_("类型名称"), max_length=50)
    description = models.CharField(_("类型描述"), max_length=200, blank=True)
    is_system = models.BooleanField(_("是否系统预设"), default=False)
    icon = models.CharField(_("图标"), max_length=50, blank=True)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name="task_categories",
        verbose_name=_("创建用户")
    )
    tenant = models.ForeignKey(
        Tenant, 
        on_delete=models.CASCADE, 
        related_name="task_categories",
        verbose_name=_("所属租户"),
        null=True,
        blank=True
    )
    translations = models.JSONField(_("多语言翻译"), default=dict, blank=True)
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)
    
    class Meta:
        verbose_name = _('打卡类型')
        verbose_name_plural = _('打卡类型')
        db_table = 'task_category'
        ordering = ['-created_at']
        unique_together = [['name', 'user', 'tenant']]
    
    def __str__(self):
        if self.is_system:
            return f"{self.name} (系统)"
        return f"{self.name}"
    
    def clean(self):
        """
        数据验证：系统预设类型必须由租户管理员创建
        """
        # 系统预设类型允许关联租户，但创建者可以为空
        if self.is_system and self.user:
            raise ValidationError(_("系统预设类型不能关联用户"))
    
    def save(self, *args, **kwargs):
        """
        重写保存方法，添加验证和日志
        """
        self.clean()
        is_new = self.pk is None
        if is_new:
            if self.is_system:
                logger.info(f"创建系统预设类型: {self.name}")
            else:
                user_name = self.user.username if self.user else "未知用户"
                logger.info(f"用户 {user_name} 创建自定义类型: {self.name}")
        
        super().save(*args, **kwargs)
    
    def get_translated_name(self, language_code='zh-hans'):
        """
        获取指定语言的名称
        """
        translations = self.translations.get('name', {})
        return translations.get(language_code, self.name)
    
    def get_translated_description(self, language_code='zh-hans'):
        """
        获取指定语言的描述
        """
        translations = self.translations.get('description', {})
        return translations.get(language_code, self.description)


class Task(models.Model):
    """
    打卡任务模型，记录用户需要打卡的具体任务
    """
    STATUS_CHOICES = (
        ('active', '进行中'),
        ('completed', '已完成'),
        ('paused', '已暂停'),
        ('archived', '已归档'),
    )
    
    FREQUENCY_CHOICES = (
        ('daily', '每天'),
        ('weekly', '每周'),
        ('monthly', '每月'),
        ('custom', '自定义'),
    )
    
    name = models.CharField(_("任务名称"), max_length=100)
    description = models.TextField(_("任务描述"), blank=True)
    category = models.ForeignKey(
        TaskCategory, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name="tasks",
        verbose_name=_("所属类型")
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name="tasks",
        verbose_name=_("所属用户")
    )
    tenant = models.ForeignKey(
        Tenant, 
        on_delete=models.CASCADE, 
        related_name="tasks",
        verbose_name=_("所属租户"),
        null=True,
        blank=True
    )
    start_date = models.DateField(_("开始日期"))
    end_date = models.DateField(_("结束日期"), null=True, blank=True)
    status = models.CharField(_("状态"), max_length=20, choices=STATUS_CHOICES, default='active')
    reminder = models.BooleanField(_("是否启用提醒"), default=False)
    reminder_time = models.TimeField(_("提醒时间"), null=True, blank=True)
    frequency_type = models.CharField(_("打卡频率类型"), max_length=20, choices=FREQUENCY_CHOICES, default='daily')
    frequency_days = models.JSONField(_("打卡频率天数"), default=list, blank=True)
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)
    
    class Meta:
        verbose_name = _('打卡任务')
        verbose_name_plural = _('打卡任务')
        db_table = 'task'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    def is_check_required_today(self):
        """
        判断今天是否需要打卡
        """
        from datetime import date, datetime
        
        # 如果任务未激活，不需要打卡
        if self.status != 'active':
            return False
            
        # 检查日期范围
        today = date.today()
        if self.start_date > today:
            return False
        if self.end_date and self.end_date < today:
            return False
            
        # 根据频率类型判断
        if self.frequency_type == 'daily':
            return True
        elif self.frequency_type == 'weekly':
            # 获取今天是周几 (1-7 表示周一到周日)
            weekday = datetime.now().weekday() + 1
            return weekday in self.frequency_days
        elif self.frequency_type == 'monthly':
            # 获取今天是几号
            day = today.day
            return day in self.frequency_days
        elif self.frequency_type == 'custom':
            # 自定义日期需要单独处理
            today_str = today.strftime('%Y-%m-%d')
            return today_str in self.frequency_days
            
        return False
        
    def save(self, *args, **kwargs):
        """
        重写保存方法，添加日志和自动关联租户
        """
        is_new = self.pk is None
        
        # 如果用户关联了租户，自动设置任务的租户
        if self.user and self.user.tenant and not self.tenant:
            self.tenant = self.user.tenant
        
        if is_new:
            logger.info(f"用户 {self.user.username} 创建任务: {self.name}")
        else:
            logger.info(f"更新任务: {self.name}")
        
        super().save(*args, **kwargs)


class CheckRecord(models.Model):
    """
    打卡记录模型，记录用户的打卡情况
    """
    task = models.ForeignKey(
        Task, 
        on_delete=models.CASCADE,
        related_name="check_records",
        verbose_name=_("所属任务")
    )
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name="check_records",
        verbose_name=_("所属用户")
    )
    check_date = models.DateField(_("打卡日期"))
    check_time = models.TimeField(_("打卡时间"))
    remarks = models.TextField(_("备注"), blank=True, default="")
    comment = models.TextField(_("评论"), blank=True, default="")
    completion_time = models.TimeField(_("完成时间"), null=True, blank=True)
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    
    class Meta:
        verbose_name = _('打卡记录')
        verbose_name_plural = _('打卡记录')
        db_table = 'check_record'
        ordering = ['-check_date', '-check_time']
        unique_together = [['user', 'task', 'check_date']]
    
    def __str__(self):
        return f"{self.user.username} - {self.task.name} - {self.check_date}"
    
    def save(self, *args, **kwargs):
        """
        重写保存方法，添加日志
        """
        is_new = self.pk is None
        if is_new:
            print(f"[CheckRecord] 用户 {self.user.username} 为任务 {self.task.name} 创建打卡记录")
        else:
            print(f"[CheckRecord] 用户 {self.user.username} 更新了任务 {self.task.name} 的打卡记录")
        super().save(*args, **kwargs)


class TaskTemplate(models.Model):
    """
    任务模板模型，用于快速创建常用任务
    """
    name = models.CharField(_("模板名称"), max_length=100)
    description = models.TextField(_("模板描述"), blank=True)
    category = models.ForeignKey(
        TaskCategory, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name="templates",
        verbose_name=_("所属类型")
    )
    is_system = models.BooleanField(_("是否系统预设"), default=False)
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name="task_templates",
        verbose_name=_("创建用户")
    )
    tenant = models.ForeignKey(
        Tenant, 
        on_delete=models.CASCADE, 
        related_name="task_templates",
        verbose_name=_("所属租户"),
        null=True,
        blank=True
    )
    reminder = models.BooleanField(_("是否启用提醒"), default=False)
    reminder_time = models.TimeField(_("提醒时间"), null=True, blank=True)
    translations = models.JSONField(_("多语言翻译"), default=dict, blank=True)
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)
    
    class Meta:
        verbose_name = _('任务模板')
        verbose_name_plural = _('任务模板')
        db_table = 'task_template'
        ordering = ['-created_at']
    
    def __str__(self):
        if self.is_system:
            return f"{self.name} (系统)"
        return f"{self.name}"
    
    def clean(self):
        """
        数据验证：系统预设模板必须由租户管理员创建
        """
        # 系统预设模板允许关联租户，但创建者可以为空
        if self.is_system and self.user:
            raise ValidationError(_("系统预设模板不能关联用户"))
    
    def save(self, *args, **kwargs):
        """
        重写保存方法，添加验证和日志
        """
        self.clean()
        is_new = self.pk is None
        if is_new:
            if self.is_system:
                logger.info(f"创建系统预设模板: {self.name}")
            else:
                user_name = self.user.username if self.user else "未知用户"
                logger.info(f"用户 {user_name} 创建自定义模板: {self.name}")
        
        super().save(*args, **kwargs)
    
    def get_translated_name(self, language_code='zh-hans'):
        """
        获取指定语言的名称
        """
        translations = self.translations.get('name', {})
        return translations.get(language_code, self.name)
    
    def get_translated_description(self, language_code='zh-hans'):
        """
        获取指定语言的描述
        """
        translations = self.translations.get('description', {})
        return translations.get(language_code, self.description)
