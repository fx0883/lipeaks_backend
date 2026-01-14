"""
打卡系统模型定义

租户隔离架构：
- 所有模型继承 BaseModel，自动提供租户隔离
- TaskCategory/TaskTemplate: 由租户管理员管理
- Task/CheckRecord/CheckinCycle: 关联到 Member
"""
import logging
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from common.models import BaseModel
from users.models import Member

logger = logging.getLogger(__name__)


class TaskCategory(BaseModel):
    """
    打卡类型模型（主题）
    
    由租户管理员创建和管理，Member 只能查看。
    支持21天自律打卡的主题系统。
    """
    FORM_TYPE_CHOICES = (
        ('text', '文本输入'),
        ('sleep', '睡眠时间'),
        ('exercise', '运动记录'),
        ('reading', '阅读记录'),
        ('mood', '情绪管理'),
        ('finance', '理财记录'),
        ('work', '工作效率'),
    )
    
    name = models.CharField(_("类型名称"), max_length=50)
    description = models.CharField(_("类型描述"), max_length=200, blank=True)
    is_system = models.BooleanField(_("是否系统预设"), default=False)
    icon = models.CharField(_("图标"), max_length=50, blank=True)
    color = models.CharField(_("主题色"), max_length=20, blank=True, help_text="HEX颜色值，如 #8B5CF6")
    goal = models.TextField(_("主题目标"), blank=True)
    tip = models.TextField(_("小贴士"), blank=True)
    quote = models.CharField(_("名言"), max_length=200, blank=True)
    form_type = models.CharField(_("表单类型"), max_length=20, choices=FORM_TYPE_CHOICES, default='text')
    sort_order = models.IntegerField(_("排序"), default=0)
    translations = models.JSONField(_("多语言翻译"), default=dict, blank=True)
    
    class Meta:
        verbose_name = _('打卡类型')
        verbose_name_plural = _('打卡类型')
        db_table = 'task_category'
        ordering = ['sort_order', '-created_at']
        # 同一租户内名称唯一
        unique_together = [['name', 'tenant']]
    
    def __str__(self):
        if self.is_system:
            return f"{self.name} (系统)"
        return f"{self.name}"
    
    def save(self, *args, **kwargs):
        """重写保存方法，添加日志"""
        is_new = self.pk is None
        if is_new:
            if self.is_system:
                logger.info(f"创建系统预设类型: {self.name}")
            else:
                tenant_name = self.tenant.name if self.tenant else "无租户"
                logger.info(f"租户 {tenant_name} 创建自定义类型: {self.name}")
        
        super().save(*args, **kwargs)
    
    def get_translated_name(self, language_code='zh-hans'):
        """获取指定语言的名称"""
        translations = self.translations.get('name', {})
        return translations.get(language_code, self.name)
    
    def get_translated_description(self, language_code='zh-hans'):
        """获取指定语言的描述"""
        translations = self.translations.get('description', {})
        return translations.get(language_code, self.description)


class Task(BaseModel):
    """
    打卡任务模型
    
    关联到 Member，记录用户需要打卡的具体任务。
    注：21天打卡不使用此模型，直接使用 CheckRecord + theme。
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
    member = models.ForeignKey(
        Member, 
        on_delete=models.CASCADE,
        related_name="tasks",
        verbose_name=_("所属成员")
    )
    start_date = models.DateField(_("开始日期"))
    end_date = models.DateField(_("结束日期"), null=True, blank=True)
    status = models.CharField(_("状态"), max_length=20, choices=STATUS_CHOICES, default='active')
    reminder = models.BooleanField(_("是否启用提醒"), default=False)
    reminder_time = models.TimeField(_("提醒时间"), null=True, blank=True)
    frequency_type = models.CharField(_("打卡频率类型"), max_length=20, choices=FREQUENCY_CHOICES, default='daily')
    frequency_days = models.JSONField(_("打卡频率天数"), default=list, blank=True)
    
    class Meta:
        verbose_name = _('打卡任务')
        verbose_name_plural = _('打卡任务')
        db_table = 'task'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    def is_check_required_today(self):
        """判断今天是否需要打卡"""
        from datetime import date, datetime
        
        if self.status != 'active':
            return False
            
        today = date.today()
        if self.start_date > today:
            return False
        if self.end_date and self.end_date < today:
            return False
            
        if self.frequency_type == 'daily':
            return True
        elif self.frequency_type == 'weekly':
            weekday = datetime.now().weekday() + 1
            return weekday in self.frequency_days
        elif self.frequency_type == 'monthly':
            day = today.day
            return day in self.frequency_days
        elif self.frequency_type == 'custom':
            today_str = today.strftime('%Y-%m-%d')
            return today_str in self.frequency_days
            
        return False
        
    def save(self, *args, **kwargs):
        """重写保存方法，自动设置租户"""
        # 从 member 继承租户
        if self.member and self.member.tenant and not self.tenant:
            self.tenant = self.member.tenant
        
        is_new = self.pk is None
        if is_new:
            logger.info(f"成员 {self.member.username} 创建任务: {self.name}")
        else:
            logger.info(f"更新任务: {self.name}")
        
        super().save(*args, **kwargs)


class CheckRecord(BaseModel):
    """
    打卡记录模型
    
    关联到 Member，记录用户的打卡情况。
    支持两种打卡方式：
    1. 关联 Task（任务型打卡）
    2. 关联 Theme（21天主题打卡）
    """
    task = models.ForeignKey(
        Task, 
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="check_records",
        verbose_name=_("所属任务")
    )
    theme = models.ForeignKey(
        TaskCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="check_records",
        verbose_name=_("打卡主题")
    )
    member = models.ForeignKey(
        Member, 
        on_delete=models.CASCADE,
        related_name="check_records",
        verbose_name=_("所属成员")
    )
    check_date = models.DateField(_("打卡日期"))
    check_time = models.TimeField(_("打卡时间"))
    remarks = models.TextField(_("备注"), blank=True, default="")
    comment = models.TextField(_("评论"), blank=True, default="")
    completion_time = models.TimeField(_("完成时间"), null=True, blank=True)
    extra_data = models.JSONField(
        _("扩展数据"), 
        default=dict, 
        blank=True,
        help_text="存储主题特定的打卡数据，如睡眠时间、运动记录等"
    )
    delayed = models.BooleanField(_("是否拖延"), default=False)
    
    class Meta:
        verbose_name = _('打卡记录')
        verbose_name_plural = _('打卡记录')
        db_table = 'check_record'
        ordering = ['-check_date', '-check_time']
    
    def __str__(self):
        target = self.task.name if self.task else (self.theme.name if self.theme else "未知")
        return f"{self.member.username} - {target} - {self.check_date}"
    
    def save(self, *args, **kwargs):
        """重写保存方法，自动设置租户"""
        # 从 member 继承租户
        if self.member and self.member.tenant and not self.tenant:
            self.tenant = self.member.tenant
        
        is_new = self.pk is None
        if is_new:
            target = self.task.name if self.task else (self.theme.name if self.theme else "未知")
            logger.info(f"成员 {self.member.username} 打卡: {target}")
        
        super().save(*args, **kwargs)


class TaskTemplate(BaseModel):
    """
    任务模板模型
    
    由租户管理员创建和管理，用于快速创建常用任务。
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
    reminder = models.BooleanField(_("是否启用提醒"), default=False)
    reminder_time = models.TimeField(_("提醒时间"), null=True, blank=True)
    translations = models.JSONField(_("多语言翻译"), default=dict, blank=True)
    
    class Meta:
        verbose_name = _('任务模板')
        verbose_name_plural = _('任务模板')
        db_table = 'task_template'
        ordering = ['-created_at']
    
    def __str__(self):
        if self.is_system:
            return f"{self.name} (系统)"
        return f"{self.name}"
    
    def save(self, *args, **kwargs):
        """重写保存方法，添加日志"""
        is_new = self.pk is None
        if is_new:
            if self.is_system:
                logger.info(f"创建系统预设模板: {self.name}")
            else:
                tenant_name = self.tenant.name if self.tenant else "无租户"
                logger.info(f"租户 {tenant_name} 创建自定义模板: {self.name}")
        
        super().save(*args, **kwargs)
    
    def get_translated_name(self, language_code='zh-hans'):
        """获取指定语言的名称"""
        translations = self.translations.get('name', {})
        return translations.get(language_code, self.name)
    
    def get_translated_description(self, language_code='zh-hans'):
        """获取指定语言的描述"""
        translations = self.translations.get('description', {})
        return translations.get(language_code, self.description)


class CheckinCycle(BaseModel):
    """
    打卡周期模型（21天自律打卡）
    
    关联到 Member，管理用户的21天打卡周期。
    """
    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name="checkin_cycles",
        verbose_name=_("所属成员")
    )
    start_date = models.DateField(_("开始日期"))
    end_date = models.DateField(_("结束日期"), help_text="自动设为开始日期+20天")
    selected_themes = models.JSONField(
        _("选择的主题"),
        default=list,
        help_text="选择的主题ID列表"
    )
    is_active = models.BooleanField(_("是否活跃"), default=True)
    
    class Meta:
        verbose_name = _('打卡周期')
        verbose_name_plural = _('打卡周期')
        db_table = 'checkin_cycle'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.member.username} - {self.start_date} to {self.end_date}"
    
    def save(self, *args, **kwargs):
        """保存时自动计算结束日期和设置租户"""
        from datetime import timedelta
        
        # 自动计算结束日期
        if not self.end_date:
            self.end_date = self.start_date + timedelta(days=20)
        
        # 从 member 继承租户
        if self.member and self.member.tenant and not self.tenant:
            self.tenant = self.member.tenant
        
        # 开启新周期时，关闭该用户的其他活跃周期
        if self.is_active and not self.pk:
            CheckinCycle.objects.filter(
                member=self.member, 
                is_active=True
            ).update(is_active=False)
        
        super().save(*args, **kwargs)
    
    def get_current_day(self):
        """获取当前是周期的第几天"""
        from datetime import date
        today = date.today()
        if today < self.start_date:
            return 0
        if today > self.end_date:
            return 21
        return (today - self.start_date).days + 1
    
    def get_progress(self):
        """获取周期进度百分比"""
        current_day = self.get_current_day()
        return min(round((current_day / 21) * 100), 100)
