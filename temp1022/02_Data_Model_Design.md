# 用户反馈系统数据模型设计

## 文档信息
- **版本**: v1.0
- **创建日期**: 2025-10-22
- **数据库**: MySQL 5.7+
- **ORM**: Django ORM

## 1. 模型概览

### 1.1 模型列表

| 模型名称 | 说明 | 继承 | 优先级 |
|---------|------|------|-------|
| **软件管理模块** | | | |
| SoftwareCategory | 软件分类 | BaseModel | P0 |
| Software | 软件主表 | BaseModel | P0 |
| SoftwareVersion | 软件版本 | BaseModel | P1 |
| **反馈管理模块** | | | |
| Feedback | 反馈主表 | BaseModel | P0 |
| FeedbackReply | 反馈回复 | BaseModel | P0 |
| FeedbackStatusHistory | 状态历史 | BaseModel | P1 |
| FeedbackAttachment | 反馈附件 | BaseModel | P2 |
| FeedbackVote | 反馈投票 | BaseModel | P2 |
| **邮件管理模块** | | | |
| FeedbackEmailLog | 邮件日志 | models.Model | P1 |
| EmailTemplate | 邮件模板 | BaseModel | P1 |

### 1.2 模型关系图

```
Tenant (租户)
    ├── SoftwareCategory (软件分类)
    ├── Software (软件) ←─── SoftwareCategory
    │       ↓
    │   SoftwareVersion (软件版本)
    │       ↓
    └── Feedback (反馈) ←─── User/Member (提交人)
            │                     ↑
            ├── FeedbackReply ────┘ (回复人)
            ├── FeedbackStatusHistory
            ├── FeedbackAttachment
            ├── FeedbackVote ←─── User/Member (投票人)
            └── FeedbackEmailLog

EmailTemplate ←─── Tenant
```

### 1.3 系统独立性说明

⚠️ **重要**: 本反馈系统是一个**完全独立**的应用，不依赖于任何外部系统：
- ✅ 拥有自己的软件管理模块
- ✅ 不依赖 licenses.SoftwareProduct
- ✅ 可以独立部署和使用
- ✅ 每个租户独立管理自己的软件

---

## 2. 详细模型设计

### 2.1 SoftwareCategory（软件分类）⭐⭐⭐⭐

**继承**: `BaseModel` (自动获得 tenant, created_at, updated_at, is_deleted)

**说明**: 软件分类管理，支持Web应用、移动APP、桌面软件等分类

```python
class SoftwareCategory(BaseModel):
    """
    软件分类模型
    
    预定义分类：Web应用、移动APP、桌面软件、API服务、内部工具、其他
    """
    
    name = models.CharField(
        _("分类名称"),
        max_length=50,
        help_text="如：Web应用、移动APP等"
    )
    
    code = models.CharField(
        _("分类代码"),
        max_length=20,
        unique=True,
        help_text="唯一标识符，如：web、mobile"
    )
    
    description = models.TextField(
        _("分类描述"),
        blank=True,
        null=True
    )
    
    icon = models.CharField(
        _("图标"),
        max_length=50,
        blank=True,
        null=True,
        help_text="Material Icon名称"
    )
    
    sort_order = models.IntegerField(
        _("排序"),
        default=0,
        help_text="数值越小越靠前"
    )
    
    is_active = models.BooleanField(
        _("是否启用"),
        default=True
    )
    
    class Meta:
        db_table = 'feedback_software_category'
        verbose_name = _('软件分类')
        verbose_name_plural = _('软件分类')
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['tenant', 'is_active']),
        ]
        unique_together = [['tenant', 'code']]
    
    def __str__(self):
        return self.name
```

---

### 2.2 Software（软件主表）⭐⭐⭐⭐⭐

**继承**: `BaseModel`

**说明**: 系统的核心软件管理，支持各种类型的软件、服务、产品

```python
class Software(BaseModel):
    """
    软件/产品/服务模型
    
    独立的软件管理，不依赖外部系统
    支持Web应用、移动APP、桌面软件、API服务等各种类型
    """
    
    # ============ 软件状态枚举 ============
    STATUS_CHOICES = [
        ('development', '开发中'),
        ('testing', '测试中'),
        ('released', '已发布'),
        ('maintenance', '维护中'),
        ('deprecated', '已废弃'),
    ]
    
    # ============ 基础信息 ============
    name = models.CharField(
        _("软件名称"),
        max_length=100,
        help_text="软件/产品/服务的名称"
    )
    
    code = models.CharField(
        _("软件代码"),
        max_length=50,
        help_text="唯一标识符，如：crm_system"
    )
    
    description = models.TextField(
        _("软件描述"),
        help_text="详细描述软件的功能和用途"
    )
    
    # ============ 分类信息 ============
    category = models.ForeignKey(
        SoftwareCategory,
        on_delete=models.SET_NULL,
        related_name='software_list',
        verbose_name=_("软件分类"),
        null=True,
        blank=True
    )
    
    # ============ 展示信息 ============
    logo = models.ImageField(
        _("Logo图片"),
        upload_to='feedbacks/software/logos/%Y/%m/',
        blank=True,
        null=True,
        help_text="建议尺寸：200x200px"
    )
    
    website = models.URLField(
        _("官网链接"),
        blank=True,
        null=True,
        help_text="软件的官方网站"
    )
    
    # ============ 版本信息 ============
    current_version = models.CharField(
        _("当前版本"),
        max_length=50,
        blank=True,
        null=True,
        help_text="如：v1.2.3"
    )
    
    # ============ 管理信息 ============
    owner = models.CharField(
        _("负责人"),
        max_length=100,
        blank=True,
        null=True,
        help_text="产品负责人姓名"
    )
    
    team = models.CharField(
        _("开发团队"),
        max_length=200,
        blank=True,
        null=True,
        help_text="负责开发的团队名称"
    )
    
    contact_email = models.EmailField(
        _("联系邮箱"),
        blank=True,
        null=True,
        help_text="技术支持邮箱"
    )
    
    # ============ 扩展信息 ============
    tags = models.JSONField(
        _("标签"),
        default=list,
        blank=True,
        help_text="自定义标签，如：['企业级', '开源', 'SaaS']"
    )
    
    metadata = models.JSONField(
        _("元数据"),
        default=dict,
        blank=True,
        help_text="其他扩展信息"
    )
    
    # ============ 状态信息 ============
    status = models.CharField(
        _("状态"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='released'
    )
    
    is_active = models.BooleanField(
        _("是否启用"),
        default=True,
        help_text="是否接收反馈"
    )
    
    # ============ 统计信息 ============
    total_feedbacks = models.PositiveIntegerField(
        _("反馈总数"),
        default=0
    )
    
    open_feedbacks = models.PositiveIntegerField(
        _("待处理反馈数"),
        default=0
    )
    
    class Meta:
        db_table = 'feedback_software'
        verbose_name = _('软件')
        verbose_name_plural = _('软件')
        ordering = ['name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['tenant', 'category']),
            models.Index(fields=['tenant', 'is_active']),
        ]
        unique_together = [['tenant', 'code']]
    
    def __str__(self):
        return f"{self.name} ({self.current_version or 'N/A'})"
    
    def update_statistics(self):
        """更新统计信息"""
        from django.db.models import Q
        self.total_feedbacks = self.feedbacks.count()
        self.open_feedbacks = self.feedbacks.filter(
            Q(status='submitted') | Q(status='reviewing') | Q(status='confirmed')
        ).count()
        self.save(update_fields=['total_feedbacks', 'open_feedbacks'])
```

---

### 2.3 SoftwareVersion（软件版本）⭐⭐⭐

**继承**: `BaseModel`

**说明**: 管理软件的版本信息

```python
class SoftwareVersion(BaseModel):
    """
    软件版本模型
    
    记录软件的各个版本信息
    """
    
    software = models.ForeignKey(
        Software,
        on_delete=models.CASCADE,
        related_name='versions',
        verbose_name=_("关联软件")
    )
    
    version = models.CharField(
        _("版本号"),
        max_length=50,
        help_text="如：v1.2.3、2.0.0-beta"
    )
    
    version_code = models.IntegerField(
        _("版本代码"),
        default=0,
        help_text="用于版本比较的数字代码"
    )
    
    release_date = models.DateField(
        _("发布日期"),
        blank=True,
        null=True
    )
    
    release_notes = models.TextField(
        _("版本说明"),
        blank=True,
        null=True,
        help_text="版本更新内容、修复的问题等"
    )
    
    is_stable = models.BooleanField(
        _("是否稳定版"),
        default=True,
        help_text="区分稳定版和测试版"
    )
    
    is_active = models.BooleanField(
        _("是否启用"),
        default=True
    )
    
    download_url = models.URLField(
        _("下载链接"),
        blank=True,
        null=True
    )
    
    class Meta:
        db_table = 'feedback_software_version'
        verbose_name = _('软件版本')
        verbose_name_plural = _('软件版本')
        ordering = ['-version_code', '-release_date']
        indexes = [
            models.Index(fields=['software', 'version']),
            models.Index(fields=['software', 'is_stable']),
            models.Index(fields=['release_date']),
        ]
        unique_together = [['software', 'version']]
    
    def __str__(self):
        return f"{self.software.name} - {self.version}"
    
    def save(self, *args, **kwargs):
        """保存时更新软件的当前版本"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # 如果是新版本且是稳定版，更新软件的当前版本
        if is_new and self.is_stable and self.is_active:
            latest_version = self.software.versions.filter(
                is_stable=True,
                is_active=True
            ).order_by('-version_code').first()
            
            if latest_version == self:
                self.software.current_version = self.version
                self.software.save(update_fields=['current_version'])
```

---

### 2.4 Feedback（反馈主表）⭐⭐⭐⭐⭐

**继承**: `BaseModel` (自动获得 tenant, created_at, updated_at, is_deleted)

**说明**: 存储用户反馈的核心信息

```python
class Feedback(BaseModel):
    """
    用户反馈模型
    
    支持注册用户、Member和匿名用户提交反馈
    """
    
    # ============ 反馈类型枚举 ============
    TYPE_CHOICES = [
        ('bug', 'Bug报告'),
        ('feature', '功能请求'),
        ('experience', '使用体验'),
        ('performance', '性能问题'),
        ('security', '安全问题'),
        ('other', '其他'),
    ]
    
    # ============ 反馈状态枚举 ============
    STATUS_CHOICES = [
        ('submitted', '已提交'),      # 初始状态
        ('reviewing', '审阅中'),       # 管理员查看中
        ('confirmed', '已确认'),       # 确认问题存在
        ('in_progress', '处理中'),     # 正在处理
        ('resolved', '已解决'),        # 问题已解决
        ('closed', '已关闭'),          # 反馈已关闭
        ('rejected', '已拒绝'),        # 拒绝处理
        ('duplicate', '重复'),         # 重复反馈
    ]
    
    # ============ 优先级枚举 ============
    PRIORITY_CHOICES = [
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
        ('urgent', '紧急'),
    ]
    
    # ============ 基本信息 ============
    tracking_number = models.CharField(
        _("追踪编号"),
        max_length=50,
        unique=True,
        editable=False,
        db_index=True,
        help_text="格式: FB-YYYYMMDD-NNN"
    )
    
    title = models.CharField(
        _("反馈标题"),
        max_length=200,
        help_text="简要描述问题或建议"
    )
    
    description = models.TextField(
        _("详细描述"),
        help_text="详细描述问题或建议的具体内容"
    )
    
    feedback_type = models.CharField(
        _("反馈类型"),
        max_length=20,
        choices=TYPE_CHOICES,
        default='other',
        db_index=True
    )
    
    status = models.CharField(
        _("状态"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='submitted',
        db_index=True
    )
    
    priority = models.CharField(
        _("优先级"),
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium',
        db_index=True
    )
    
    # ============ 关联信息 ============
    software = models.ForeignKey(
        Software,  # 使用独立的Software模型
        on_delete=models.CASCADE,
        related_name='feedbacks',
        verbose_name=_("关联软件"),
        db_index=True
    )
    
    software_version = models.ForeignKey(
        SoftwareVersion,  # 关联到具体版本
        on_delete=models.SET_NULL,
        related_name='feedbacks',
        verbose_name=_("软件版本"),
        blank=True,
        null=True,
        help_text="关联到具体的软件版本"
    )
    
    # 移除对licenses的依赖
    # license 和 license_assignment 字段已删除
    
    # ============ 提交人信息 ============
    # 三种提交者类型：User(管理员)、Member(会员)、匿名用户
    
    submitted_by_user = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        related_name='submitted_feedbacks',
        verbose_name=_("提交人(User)"),
        blank=True,
        null=True,
        help_text="管理员提交"
    )
    
    submitted_by_member = models.ForeignKey(
        'users.Member',
        on_delete=models.SET_NULL,
        related_name='submitted_feedbacks',
        verbose_name=_("提交人(Member)"),
        blank=True,
        null=True,
        help_text="会员提交"
    )
    
    # 匿名用户信息
    anonymous_name = models.CharField(
        _("匿名用户名称"),
        max_length=100,
        blank=True,
        null=True,
        help_text="匿名用户的昵称（可选）"
    )
    
    contact_email = models.EmailField(
        _("联系邮箱"),
        blank=True,
        null=True,
        db_index=True,
        help_text="匿名用户必填，注册用户自动使用账号邮箱"
    )
    
    email_verified = models.BooleanField(
        _("邮箱已验证"),
        default=False,
        help_text="匿名用户需验证邮箱"
    )
    
    email_verification_token = models.CharField(
        _("邮箱验证令牌"),
        max_length=100,
        blank=True,
        null=True
    )
    
    email_verification_sent_at = models.DateTimeField(
        _("验证邮件发送时间"),
        blank=True,
        null=True
    )
    
    # ============ 环境信息 ============
    environment_info = models.JSONField(
        _("环境信息"),
        default=dict,
        blank=True,
        help_text="操作系统、浏览器、硬件等信息"
    )
    # JSON格式示例:
    # {
    #     "os": "Windows 10",
    #     "os_version": "21H2",
    #     "browser": "Chrome",
    #     "browser_version": "120.0",
    #     "screen_resolution": "1920x1080",
    #     "language": "zh-CN",
    #     "timezone": "Asia/Shanghai",
    #     "app_version": "1.2.3",
    #     "device_type": "Desktop",
    #     "cpu": "Intel Core i7",
    #     "memory": "16GB"
    # }
    
    ip_address = models.GenericIPAddressField(
        _("IP地址"),
        blank=True,
        null=True,
        help_text="提交时的IP地址"
    )
    
    user_agent = models.TextField(
        _("User Agent"),
        blank=True,
        null=True
    )
    
    # ============ 统计信息 ============
    views_count = models.PositiveIntegerField(
        _("查看次数"),
        default=0
    )
    
    votes_count = models.PositiveIntegerField(
        _("投票数"),
        default=0
    )
    
    replies_count = models.PositiveIntegerField(
        _("回复数"),
        default=0
    )
    
    # ============ 时间信息 ============
    first_replied_at = models.DateTimeField(
        _("首次回复时间"),
        blank=True,
        null=True,
        help_text="用于统计响应时间"
    )
    
    last_replied_at = models.DateTimeField(
        _("最后回复时间"),
        blank=True,
        null=True
    )
    
    resolved_at = models.DateTimeField(
        _("解决时间"),
        blank=True,
        null=True,
        help_text="状态变更为已解决的时间"
    )
    
    closed_at = models.DateTimeField(
        _("关闭时间"),
        blank=True,
        null=True
    )
    
    # ============ 邮件通知设置 ============
    email_notification_enabled = models.BooleanField(
        _("允许邮件通知"),
        default=True,
        help_text="用户可选择不接收邮件通知"
    )
    
    # ============ 其他 ============
    internal_notes = models.TextField(
        _("内部备注"),
        blank=True,
        null=True,
        help_text="仅内部可见的备注"
    )
    
    class Meta:
        db_table = 'feedback_feedback'
        verbose_name = _('用户反馈')
        verbose_name_plural = _('用户反馈')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tracking_number']),
            models.Index(fields=['software', 'status']),
            models.Index(fields=['tenant', 'status']),
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['feedback_type', 'status']),
            models.Index(fields=['contact_email']),
            models.Index(fields=['created_at']),
            models.Index(fields=['-votes_count']),  # 热门排序
        ]
    
    def __str__(self):
        return f"{self.tracking_number} - {self.title}"
    
    def save(self, *args, **kwargs):
        """保存时自动生成追踪编号"""
        if not self.tracking_number:
            self.tracking_number = self._generate_tracking_number()
        super().save(*args, **kwargs)
    
    def _generate_tracking_number(self):
        """生成唯一追踪编号: FB-YYYYMMDD-NNN"""
        from django.utils import timezone
        import random
        
        now = timezone.now()
        date_str = now.strftime('%Y%m%d')
        random_num = str(random.randint(100, 999))
        return f"FB-{date_str}-{random_num}"
    
    def get_submitter_email(self):
        """获取提交人邮箱"""
        if self.submitted_by_user:
            return self.submitted_by_user.email
        elif self.submitted_by_member:
            return self.submitted_by_member.email
        else:
            return self.contact_email
    
    def get_submitter_name(self):
        """获取提交人名称"""
        if self.submitted_by_user:
            return self.submitted_by_user.username
        elif self.submitted_by_member:
            return self.submitted_by_member.username
        else:
            return self.anonymous_name or '匿名用户'
    
    def can_reply_by_email(self):
        """是否可以通过邮件回复"""
        return bool(self.get_submitter_email())
    
    def increment_views(self):
        """增加查看次数"""
        self.views_count += 1
        self.save(update_fields=['views_count'])
    
    def update_replies_count(self):
        """更新回复数"""
        self.replies_count = self.replies.filter(is_internal=False).count()
        self.save(update_fields=['replies_count'])
    
    def update_votes_count(self):
        """更新投票数"""
        self.votes_count = self.votes.count()
        self.save(update_fields=['votes_count'])
```

**字段说明**:
- `tracking_number`: 追踪编号，自动生成，唯一
- `submitted_by_user/member`: 支持三种提交者类型
- `contact_email`: 关键字段，用于邮件回复
- `email_verified`: 匿名用户邮箱验证状态
- `environment_info`: JSON存储环境信息
- `first_replied_at`: 用于计算响应时间SLA

---

### 2.5 FeedbackReply（反馈回复）⭐⭐⭐⭐⭐

**继承**: `BaseModel`

**说明**: 存储对反馈的所有回复，包括官方回复和内部备注

```python
class FeedbackReply(BaseModel):
    """
    反馈回复模型
    
    支持两种回复类型：官方回复（发送邮件）和内部备注（仅内部可见）
    """
    
    # ============ 回复类型枚举 ============
    REPLY_TYPE_CHOICES = [
        ('official', '官方回复'),  # 发送邮件给用户
        ('internal', '内部备注'),  # 仅内部可见
    ]
    
    # ============ 关联信息 ============
    feedback = models.ForeignKey(
        Feedback,
        on_delete=models.CASCADE,
        related_name='replies',
        verbose_name=_("关联反馈")
    )
    
    # ============ 回复人信息 ============
    replied_by_user = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        related_name='feedback_replies',
        verbose_name=_("回复人(User)"),
        blank=True,
        null=True
    )
    
    replied_by_member = models.ForeignKey(
        'users.Member',
        on_delete=models.SET_NULL,
        related_name='feedback_replies',
        verbose_name=_("回复人(Member)"),
        blank=True,
        null=True,
        help_text="一般不会用到，预留"
    )
    
    # ============ 回复内容 ============
    content = models.TextField(
        _("回复内容"),
        help_text="回复的详细内容"
    )
    
    reply_type = models.CharField(
        _("回复类型"),
        max_length=20,
        choices=REPLY_TYPE_CHOICES,
        default='official',
        help_text="官方回复会发送邮件，内部备注仅内部可见"
    )
    
    is_internal = models.BooleanField(
        _("内部备注"),
        default=False,
        help_text="True表示内部备注，不发送邮件"
    )
    
    # ============ 邮件发送状态 ============
    email_sent = models.BooleanField(
        _("邮件已发送"),
        default=False
    )
    
    email_sent_at = models.DateTimeField(
        _("邮件发送时间"),
        blank=True,
        null=True
    )
    
    email_error = models.TextField(
        _("邮件发送错误"),
        blank=True,
        null=True,
        help_text="记录邮件发送失败原因"
    )
    
    email_retry_count = models.PositiveIntegerField(
        _("邮件重试次数"),
        default=0
    )
    
    # ============ 其他 ============
    attachments = models.JSONField(
        _("附件"),
        default=list,
        blank=True,
        help_text="回复可以包含附件，存储文件路径列表"
    )
    
    class Meta:
        db_table = 'feedback_reply'
        verbose_name = _('反馈回复')
        verbose_name_plural = _('反馈回复')
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['feedback', 'created_at']),
            models.Index(fields=['feedback', 'is_internal']),
            models.Index(fields=['replied_by_user']),
            models.Index(fields=['email_sent']),
        ]
    
    def __str__(self):
        return f"回复 - {self.feedback.tracking_number}"
    
    def get_replier_name(self):
        """获取回复人名称"""
        if self.replied_by_user:
            return self.replied_by_user.username
        elif self.replied_by_member:
            return self.replied_by_member.username
        return '系统'
    
    def save(self, *args, **kwargs):
        """保存时触发邮件发送"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # 如果是新回复且是官方回复，触发邮件发送
        if is_new and not self.is_internal and self.feedback.can_reply_by_email():
            from feedbacks.tasks.email_tasks import send_feedback_reply_email
            send_feedback_reply_email.delay(self.id)
        
        # 更新反馈的回复计数和最后回复时间
        if not self.is_internal:
            from django.utils import timezone
            self.feedback.last_replied_at = timezone.now()
            if not self.feedback.first_replied_at:
                self.feedback.first_replied_at = timezone.now()
            self.feedback.update_replies_count()
```

**字段说明**:
- `is_internal`: 控制是否发送邮件
- `email_sent`: 邮件发送状态
- `email_retry_count`: 失败重试次数
- `attachments`: JSON存储附件路径

---

### 2.6 FeedbackStatusHistory（状态历史）⭐⭐⭐

**继承**: `BaseModel`

**说明**: 记录反馈的所有状态变更历史

```python
class FeedbackStatusHistory(BaseModel):
    """
    反馈状态历史模型
    
    记录反馈状态的所有变更，用于追踪和审计
    """
    
    feedback = models.ForeignKey(
        Feedback,
        on_delete=models.CASCADE,
        related_name='status_history',
        verbose_name=_("关联反馈")
    )
    
    # ============ 状态变更信息 ============
    old_status = models.CharField(
        _("原状态"),
        max_length=20,
        choices=Feedback.STATUS_CHOICES
    )
    
    new_status = models.CharField(
        _("新状态"),
        max_length=20,
        choices=Feedback.STATUS_CHOICES
    )
    
    # ============ 变更人信息 ============
    changed_by_user = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        related_name='status_changes',
        verbose_name=_("变更人"),
        blank=True,
        null=True
    )
    
    # ============ 变更原因 ============
    reason = models.TextField(
        _("变更原因"),
        blank=True,
        null=True,
        help_text="状态变更的原因或说明"
    )
    
    # ============ 邮件通知 ============
    email_sent = models.BooleanField(
        _("已发送邮件通知"),
        default=False
    )
    
    class Meta:
        db_table = 'feedback_status_history'
        verbose_name = _('状态历史')
        verbose_name_plural = _('状态历史')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['feedback', '-created_at']),
            models.Index(fields=['new_status', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.feedback.tracking_number}: {self.old_status} → {self.new_status}"
    
    @classmethod
    def create_history(cls, feedback, old_status, new_status, changed_by, reason=None, send_email=True):
        """创建状态历史记录"""
        history = cls.objects.create(
            feedback=feedback,
            old_status=old_status,
            new_status=new_status,
            changed_by_user=changed_by,
            reason=reason,
            tenant=feedback.tenant
        )
        
        # 如果需要发送邮件
        if send_email and feedback.email_notification_enabled and feedback.can_reply_by_email():
            from feedbacks.tasks.email_tasks import send_status_change_email
            send_status_change_email.delay(history.id)
        
        return history
```

**字段说明**:
- `old_status/new_status`: 记录状态变更
- `reason`: 变更原因说明
- `email_sent`: 是否已发送邮件通知

---

### 2.7 FeedbackAttachment（反馈附件）⭐⭐⭐

**继承**: `BaseModel`

**说明**: 存储反馈的附件信息

```python
class FeedbackAttachment(BaseModel):
    """
    反馈附件模型
    
    支持用户上传截图、日志等文件
    """
    
    # ============ 文件类型枚举 ============
    FILE_TYPE_CHOICES = [
        ('image', '图片'),
        ('log', '日志文件'),
        ('document', '文档'),
        ('archive', '压缩包'),
        ('other', '其他'),
    ]
    
    feedback = models.ForeignKey(
        Feedback,
        on_delete=models.CASCADE,
        related_name='attachments',
        verbose_name=_("关联反馈")
    )
    
    # ============ 文件信息 ============
    file = models.FileField(
        _("文件"),
        upload_to='feedbacks/attachments/%Y/%m/%d/',
        help_text="上传的附件文件"
    )
    
    original_filename = models.CharField(
        _("原始文件名"),
        max_length=255,
        help_text="用户上传时的文件名"
    )
    
    file_type = models.CharField(
        _("文件类型"),
        max_length=20,
        choices=FILE_TYPE_CHOICES,
        default='other'
    )
    
    file_size = models.PositiveIntegerField(
        _("文件大小"),
        help_text="单位: 字节"
    )
    
    mime_type = models.CharField(
        _("MIME类型"),
        max_length=100,
        blank=True,
        null=True
    )
    
    # ============ 上传人信息 ============
    uploaded_by_user = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        related_name='uploaded_attachments',
        verbose_name=_("上传人(User)"),
        blank=True,
        null=True
    )
    
    uploaded_by_member = models.ForeignKey(
        'users.Member',
        on_delete=models.SET_NULL,
        related_name='uploaded_attachments',
        verbose_name=_("上传人(Member)"),
        blank=True,
        null=True
    )
    
    class Meta:
        db_table = 'feedback_attachment'
        verbose_name = _('反馈附件')
        verbose_name_plural = _('反馈附件')
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['feedback']),
        ]
    
    def __str__(self):
        return f"{self.original_filename} - {self.feedback.tracking_number}"
    
    def get_file_url(self):
        """获取文件访问URL"""
        if self.file:
            return self.file.url
        return None
```

**字段说明**:
- `file`: 文件存储字段
- `original_filename`: 保留原始文件名
- `file_size`: 用于限制检查
- `mime_type`: 用于文件类型验证

---

### 2.8 FeedbackVote（反馈投票）⭐⭐⭐

**继承**: `BaseModel`

**说明**: 记录用户对反馈的投票

```python
class FeedbackVote(BaseModel):
    """
    反馈投票模型
    
    用户可以对反馈投票，表示关注或支持
    """
    
    feedback = models.ForeignKey(
        Feedback,
        on_delete=models.CASCADE,
        related_name='votes',
        verbose_name=_("关联反馈")
    )
    
    # ============ 投票人信息 ============
    # 只有注册用户可以投票
    voted_by_user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='feedback_votes',
        verbose_name=_("投票人(User)"),
        blank=True,
        null=True
    )
    
    voted_by_member = models.ForeignKey(
        'users.Member',
        on_delete=models.CASCADE,
        related_name='feedback_votes',
        verbose_name=_("投票人(Member)"),
        blank=True,
        null=True
    )
    
    class Meta:
        db_table = 'feedback_vote'
        verbose_name = _('反馈投票')
        verbose_name_plural = _('反馈投票')
        unique_together = [
            ['feedback', 'voted_by_user'],
            ['feedback', 'voted_by_member'],
        ]
        indexes = [
            models.Index(fields=['feedback']),
            models.Index(fields=['voted_by_user']),
            models.Index(fields=['voted_by_member']),
        ]
    
    def __str__(self):
        voter = self.voted_by_user or self.voted_by_member
        return f"{voter} 投票 - {self.feedback.tracking_number}"
    
    def save(self, *args, **kwargs):
        """保存时更新投票计数"""
        super().save(*args, **kwargs)
        self.feedback.update_votes_count()
    
    def delete(self, *args, **kwargs):
        """删除时更新投票计数"""
        super().delete(*args, **kwargs)
        self.feedback.update_votes_count()
```

**字段说明**:
- `unique_together`: 确保每个用户只能投票一次
- 保存和删除时自动更新反馈的投票计数

---

### 2.9 FeedbackEmailLog（邮件日志）⭐⭐⭐⭐

**不继承BaseModel**（不需要tenant、软删除等）

**说明**: 记录所有邮件发送历史，用于追踪和排错

```python
class FeedbackEmailLog(models.Model):
    """
    反馈邮件日志模型
    
    记录所有邮件发送历史，包括成功和失败
    """
    
    # ============ 邮件类型枚举 ============
    EMAIL_TYPE_CHOICES = [
        ('verification', '邮箱验证'),
        ('reply', '反馈回复'),
        ('status_change', '状态变更'),
        ('reminder', '提醒通知'),
    ]
    
    # ============ 邮件状态枚举 ============
    STATUS_CHOICES = [
        ('pending', '待发送'),
        ('sent', '已发送'),
        ('failed', '发送失败'),
        ('bounced', '邮件退回'),
    ]
    
    # ============ 关联信息 ============
    feedback = models.ForeignKey(
        Feedback,
        on_delete=models.CASCADE,
        related_name='email_logs',
        verbose_name=_("关联反馈")
    )
    
    reply = models.ForeignKey(
        FeedbackReply,
        on_delete=models.SET_NULL,
        related_name='email_logs',
        verbose_name=_("关联回复"),
        blank=True,
        null=True,
        help_text="如果是回复通知，关联到具体回复"
    )
    
    status_history = models.ForeignKey(
        FeedbackStatusHistory,
        on_delete=models.SET_NULL,
        related_name='email_logs',
        verbose_name=_("关联状态历史"),
        blank=True,
        null=True,
        help_text="如果是状态变更通知，关联到具体历史"
    )
    
    # ============ 邮件信息 ============
    email_type = models.CharField(
        _("邮件类型"),
        max_length=20,
        choices=EMAIL_TYPE_CHOICES
    )
    
    recipient_email = models.EmailField(
        _("收件人邮箱")
    )
    
    subject = models.CharField(
        _("邮件主题"),
        max_length=255
    )
    
    body = models.TextField(
        _("邮件正文"),
        help_text="HTML格式的邮件内容"
    )
    
    # ============ 发送状态 ============
    status = models.CharField(
        _("发送状态"),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    
    sent_at = models.DateTimeField(
        _("发送时间"),
        blank=True,
        null=True,
        auto_now_add=True
    )
    
    error_message = models.TextField(
        _("错误信息"),
        blank=True,
        null=True,
        help_text="发送失败时的错误信息"
    )
    
    retry_count = models.PositiveIntegerField(
        _("重试次数"),
        default=0
    )
    
    # ============ 其他 ============
    metadata = models.JSONField(
        _("元数据"),
        default=dict,
        blank=True,
        help_text="其他相关信息"
    )
    
    class Meta:
        db_table = 'feedback_email_log'
        verbose_name = _('邮件日志')
        verbose_name_plural = _('邮件日志')
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['feedback', '-sent_at']),
            models.Index(fields=['recipient_email', '-sent_at']),
            models.Index(fields=['status', 'sent_at']),
            models.Index(fields=['email_type', 'sent_at']),
        ]
    
    def __str__(self):
        return f"{self.email_type} - {self.recipient_email} - {self.status}"
```

**字段说明**:
- `email_type`: 区分不同类型的邮件
- `status`: 追踪发送状态
- `retry_count`: 失败重试次数
- `body`: 完整保存邮件内容，便于排错

---

### 2.10 EmailTemplate（邮件模板）⭐⭐⭐

**继承**: `BaseModel`

**说明**: 可配置的邮件模板，每个租户可自定义

```python
class EmailTemplate(BaseModel):
    """
    邮件模板模型
    
    每个租户可以自定义邮件模板
    """
    
    # ============ 模板类型枚举 ============
    TEMPLATE_TYPE_CHOICES = [
        ('verification', '邮箱验证'),
        ('reply', '反馈回复'),
        ('status_change', '状态变更'),
        ('reminder', '提醒通知'),
    ]
    
    name = models.CharField(
        _("模板名称"),
        max_length=100,
        help_text="模板的显示名称"
    )
    
    template_type = models.CharField(
        _("模板类型"),
        max_length=20,
        choices=TEMPLATE_TYPE_CHOICES,
        db_index=True
    )
    
    # ============ 模板内容 ============
    subject_template = models.CharField(
        _("主题模板"),
        max_length=255,
        help_text="支持变量: {software_name}, {tracking_number}, {tenant_name}"
    )
    
    body_template = models.TextField(
        _("正文模板"),
        help_text="HTML格式，支持变量替换"
    )
    # 支持的变量：
    # {feedback_title} - 反馈标题
    # {feedback_id} - 反馈ID
    # {tracking_number} - 追踪编号
    # {reply_content} - 回复内容
    # {status_display} - 状态显示名
    # {software_name} - 软件名称
    # {software_version} - 软件版本
    # {tenant_name} - 租户名称
    # {submitter_name} - 提交人名称
    # {feedback_url} - 反馈详情URL
    # {unsubscribe_url} - 退订URL
    # {verification_url} - 验证URL
    
    # ============ 模板设置 ============
    is_active = models.BooleanField(
        _("是否启用"),
        default=True
    )
    
    is_default = models.BooleanField(
        _("是否默认模板"),
        default=False,
        help_text="系统默认模板，不能删除"
    )
    
    priority = models.PositiveIntegerField(
        _("优先级"),
        default=0,
        help_text="数字越大优先级越高"
    )
    
    class Meta:
        db_table = 'feedback_email_template'
        verbose_name = _('邮件模板')
        verbose_name_plural = _('邮件模板')
        ordering = ['-priority', 'name']
        indexes = [
            models.Index(fields=['tenant', 'template_type', 'is_active']),
        ]
        unique_together = [
            ['tenant', 'template_type', 'is_default'],
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"
    
    def render(self, context):
        """渲染模板"""
        subject = self.subject_template
        body = self.body_template
        
        for key, value in context.items():
            subject = subject.replace(f"{{{key}}}", str(value))
            body = body.replace(f"{{{key}}}", str(value))
        
        return subject, body
    
    @classmethod
    def get_template(cls, tenant, template_type):
        """获取指定类型的模板"""
        # 优先使用租户自定义模板
        template = cls.objects.filter(
            tenant=tenant,
            template_type=template_type,
            is_active=True
        ).order_by('-priority').first()
        
        if not template:
            # 使用默认模板
            template = cls.objects.filter(
                template_type=template_type,
                is_default=True,
                is_active=True
            ).first()
        
        return template
```

**字段说明**:
- `subject_template/body_template`: 支持变量替换
- `is_default`: 系统默认模板
- `priority`: 模板优先级
- `render()`: 渲染方法

---

## 3. 数据库索引策略

### 3.1 主要索引

```sql
-- Feedback表
CREATE INDEX idx_feedback_tracking ON feedback_feedback(tracking_number);
CREATE INDEX idx_feedback_software_status ON feedback_feedback(software_id, status);
CREATE INDEX idx_feedback_tenant_status ON feedback_feedback(tenant_id, status);
CREATE INDEX idx_feedback_status_priority ON feedback_feedback(status, priority);
CREATE INDEX idx_feedback_type_status ON feedback_feedback(feedback_type, status);
CREATE INDEX idx_feedback_email ON feedback_feedback(contact_email);
CREATE INDEX idx_feedback_created ON feedback_feedback(created_at);
CREATE INDEX idx_feedback_votes ON feedback_feedback(votes_count DESC);

-- FeedbackReply表
CREATE INDEX idx_reply_feedback_created ON feedback_reply(feedback_id, created_at);
CREATE INDEX idx_reply_feedback_internal ON feedback_reply(feedback_id, is_internal);
CREATE INDEX idx_reply_user ON feedback_reply(replied_by_user_id);

-- FeedbackStatusHistory表
CREATE INDEX idx_history_feedback_created ON feedback_status_history(feedback_id, created_at DESC);
CREATE INDEX idx_history_status_created ON feedback_status_history(new_status, created_at);

-- FeedbackEmailLog表
CREATE INDEX idx_email_log_feedback ON feedback_email_log(feedback_id, sent_at DESC);
CREATE INDEX idx_email_log_recipient ON feedback_email_log(recipient_email, sent_at DESC);
CREATE INDEX idx_email_log_status ON feedback_email_log(status, sent_at);
```

### 3.2 索引优化建议

1. **经常查询的字段**: status, feedback_type, tenant_id
2. **排序字段**: created_at, votes_count, priority
3. **联合索引**: (tenant_id, status), (software_id, status)
4. **覆盖索引**: 常见查询添加覆盖索引

---

## 4. 数据迁移计划

### 4.1 初始迁移

```python
# 0001_initial.py
operations = [
    # 创建Feedback表
    migrations.CreateModel(
        name='Feedback',
        fields=[...],
    ),
    # 创建FeedbackReply表
    migrations.CreateModel(
        name='FeedbackReply',
        fields=[...],
    ),
    # ... 其他表
]
```

### 4.2 默认数据迁移

```python
# 0002_default_email_templates.py
# 创建默认邮件模板
def create_default_templates(apps, schema_editor):
    EmailTemplate = apps.get_model('feedbacks', 'EmailTemplate')
    
    # 创建默认模板
    templates = [
        {
            'name': '默认邮箱验证模板',
            'template_type': 'verification',
            'subject_template': '[{software_name}] 请验证您的邮箱',
            'body_template': '...',
            'is_default': True,
        },
        # ... 其他模板
    ]
    
    for template_data in templates:
        EmailTemplate.objects.create(**template_data)
```

---

## 5. 性能优化

### 5.1 查询优化

```python
# 使用select_related减少查询
feedbacks = Feedback.objects.select_related(
    'software',
    'tenant',
    'submitted_by_user',
    'submitted_by_member'
).all()

# 使用prefetch_related优化关联查询
feedbacks = Feedback.objects.prefetch_related(
    'replies',
    'attachments',
    'votes'
).all()

# 使用annotate添加统计字段
from django.db.models import Count
feedbacks = Feedback.objects.annotate(
    replies_count=Count('replies')
)
```

### 5.2 缓存策略

```python
# 缓存热门反馈
from django.core.cache import cache

def get_hot_feedbacks(tenant_id):
    cache_key = f'hot_feedbacks_{tenant_id}'
    result = cache.get(cache_key)
    
    if not result:
        result = Feedback.objects.filter(
            tenant_id=tenant_id,
            status__in=['submitted', 'confirmed']
        ).order_by('-votes_count')[:10]
        cache.set(cache_key, result, 3600)  # 缓存1小时
    
    return result
```

---

## 6. 数据清理策略

### 6.1 自动清理规则

```python
# 定期清理任务 (Celery)
from django.utils import timezone
from datetime import timedelta

@periodic_task(run_every=timedelta(days=1))
def cleanup_feedback_data():
    """清理过期数据"""
    
    # 1. 清理未验证邮箱的匿名反馈（7天后）
    seven_days_ago = timezone.now() - timedelta(days=7)
    Feedback.objects.filter(
        email_verified=False,
        submitted_by_user__isnull=True,
        submitted_by_member__isnull=True,
        created_at__lt=seven_days_ago
    ).delete()
    
    # 2. 清理已删除反馈的附件（30天后）
    thirty_days_ago = timezone.now() - timedelta(days=30)
    FeedbackAttachment.objects.filter(
        feedback__is_deleted=True,
        created_at__lt=thirty_days_ago
    ).delete()
    
    # 3. 自动关闭已解决反馈（14天无回复）
    fourteen_days_ago = timezone.now() - timedelta(days=14)
    Feedback.objects.filter(
        status='resolved',
        last_replied_at__lt=fourteen_days_ago
    ).update(status='closed', closed_at=timezone.now())
```

---

## 7. 数据完整性约束

### 7.1 业务约束

```python
# 模型层面的验证
class Feedback(BaseModel):
    def clean(self):
        """数据验证"""
        from django.core.exceptions import ValidationError
        
        # 验证：三种提交者类型至少有一个
        if not (self.submitted_by_user or self.submitted_by_member or self.contact_email):
            raise ValidationError('必须指定提交人或联系邮箱')
        
        # 验证：匿名用户必须提供邮箱或姓名
        if not (self.submitted_by_user or self.submitted_by_member):
            if not self.contact_email and not self.anonymous_name:
                raise ValidationError('匿名用户必须提供邮箱或昵称')
        
        # 验证：软件产品必须属于同一租户
        if self.software and self.software.tenant_id != self.tenant_id:
            raise ValidationError('软件产品必须属于同一租户')
```

---

## 8. 总结

### 8.1 模型统计

| 模型 | 表名 | 字段数 | 索引数 | 外键数 |
|------|------|-------|-------|-------|
| **软件管理** | | | | |
| SoftwareCategory | feedback_software_category | ~8 | 2 | 1 |
| Software | feedback_software | ~20 | 4 | 2 |
| SoftwareVersion | feedback_software_version | ~10 | 3 | 1 |
| **反馈管理** | | | | |
| Feedback | feedback_feedback | ~33 | 8 | 4 |
| FeedbackReply | feedback_reply | ~15 | 4 | 3 |
| FeedbackStatusHistory | feedback_status_history | ~10 | 2 | 2 |
| FeedbackAttachment | feedback_attachment | ~10 | 1 | 3 |
| FeedbackVote | feedback_vote | ~6 | 3 | 3 |
| **邮件管理** | | | | |
| FeedbackEmailLog | feedback_email_log | ~12 | 4 | 3 |
| EmailTemplate | feedback_email_template | ~10 | 1 | 1 |

### 8.2 存储预估

假设：
- 每月1000个反馈
- 每个反馈平均2个回复
- 每个反馈平均1个附件(2MB)

年度存储需求：
- Feedback: 1000 × 12 × 2KB ≈ 24MB
- Reply: 2000 × 12 × 1KB ≈ 24MB
- Attachment: 1000 × 12 × 2MB ≈ 24GB
- EmailLog: 3000 × 12 × 1KB ≈ 36MB
- **合计**: 约 24.08GB/年

### 8.3 设计亮点

✅ **完全独立**: 不依赖任何外部系统，可独立部署
✅ **多租户隔离**: 所有核心表继承BaseModel
✅ **完整的软件管理**: 分类、版本、标签等功能齐全
✅ **灵活的提交者类型**: 支持User/Member/匿名
✅ **完整的邮件追踪**: 独立的邮件日志表
✅ **可扩展的模板系统**: 租户可自定义邮件模板
✅ **丰富的索引**: 优化查询性能
✅ **软删除支持**: 数据可恢复
✅ **JSON字段应用**: 灵活存储环境信息和元数据
✅ **权限明确**: 只有租户管理员可管理软件

---

**相关文档**: [03_API设计.md](./03_API设计.md)

