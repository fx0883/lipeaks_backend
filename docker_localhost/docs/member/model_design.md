# 用户系统模型设计

## 模型结构设计

### BaseUserModel（抽象基类）

创建一个抽象基类，包含User和Member共有的字段和方法：

```
BaseUserModel (继承自AbstractUser)
├── 基本信息字段
│   ├── phone (手机号)
│   ├── email (邮箱)
│   ├── nick_name (昵称)
│   ├── avatar (头像)
│   └── status (状态：active/suspended/inactive)
├── 租户关联
│   └── tenant (关联到Tenant模型)
├── 状态标记
│   ├── is_deleted (软删除标记)
│   └── last_login_ip (最后登录IP)
└── 通用方法
    ├── soft_delete() (软删除方法)
    └── display_name (显示名称属性)
```

### User模型（管理员用户）

管理员用户模型，继承自BaseUserModel：

```
User (继承自BaseUserModel)
├── 角色标记
│   ├── is_admin (是否管理员，始终为True)
│   └── is_super_admin (是否超级管理员)
└── 特有方法
    ├── save() (重写保存方法，处理超级管理员逻辑)
    ├── is_tenant_admin (属性，判断是否为租户管理员)
    └── display_role (属性，显示用户角色)
```

### Member模型（普通成员）

普通成员模型，继承自BaseUserModel：

```
Member (继承自BaseUserModel)
├── 成员关系
│   └── parent (父账号，关联到自身)
└── 特有方法
    ├── save() (重写保存方法，处理子账号逻辑)
    ├── is_sub_account (属性，判断是否为子账号)
    └── display_role (属性，显示成员角色)
```

## 模型关系图

```
┌───────────────────────────────────────────────────┐
│                   BaseUserModel                   │
│                                                   │
│ + phone: CharField                                │
│ + email: EmailField                               │
│ + nick_name: CharField                            │
│ + avatar: CharField                               │
│ + status: CharField                               │
│ + tenant: ForeignKey(Tenant)                      │
│ + is_deleted: BooleanField                        │
│ + last_login_ip: CharField                        │
│                                                   │
│ + soft_delete()                                   │
│ + display_name                                    │
└───────────────────────────────────────────────────┘
                 ↑                 ↑
                 │                 │
    ┌────────────┘                 └────────────┐
    │                                           │
┌───────────────────────┐           ┌───────────────────────┐
│         User          │           │        Member         │
│                       │           │                       │
│ + is_admin: Boolean   │           │ + parent: ForeignKey  │
│ + is_super_admin: Bool│           │                       │
│                       │           │                       │
│ + save()              │           │ + save()              │
│ + is_tenant_admin     │           │ + is_sub_account      │
│ + display_role        │           │ + display_role        │
└───────────────────────┘           └───────────────────────┘
```

## 详细模型定义

### BaseUserModel

```python
class BaseUserModel(AbstractUser):
    """
    用户基础模型，包含所有用户类型共有的字段
    """
    # 租户关联字段
    tenant = models.ForeignKey(
        'tenants.Tenant', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name="%(class)ss",  # 动态关联名
        verbose_name=_("所属租户")
    )
    
    # 用户信息字段
    phone = models.CharField(_("手机号"), max_length=11, null=True, blank=True)
    email = models.EmailField(_("邮箱"))
    nick_name = models.CharField(_("昵称"), max_length=30, null=True, blank=True)
    avatar = models.CharField(_("头像"), max_length=200, default="", blank=True)
    is_deleted = models.BooleanField(_("是否删除"), default=False)
    
    # 状态字段
    status = models.CharField(
        _("状态"), 
        max_length=20, 
        choices=[
            ('active', '活跃'),
            ('suspended', '暂停'),
            ('inactive', '未激活'),
        ],
        default='active'
    )
    
    # 最后登录IP
    last_login_ip = models.CharField(_("最后登录IP"), max_length=50, null=True, blank=True)
    
    class Meta:
        abstract = True
        ordering = ['-date_joined']
    
    def soft_delete(self):
        """
        软删除用户
        """
        self.is_deleted = True
        self.status = 'inactive'
        self.is_active = False
        self.save(update_fields=['is_deleted', 'status', 'is_active'])
        return self
    
    @property
    def display_name(self):
        """
        获取用户显示名称
        """
        if self.nick_name:
            return self.nick_name
        elif self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        else:
            return self.username
```

### User模型

```python
class User(BaseUserModel):
    """
    管理员用户模型，包括超级管理员和租户管理员
    """
    # 用户角色字段
    is_admin = models.BooleanField(_("是否管理员"), default=True)
    is_super_admin = models.BooleanField(_("是否超级管理员"), default=False)
    
    class Meta:
        verbose_name = _('管理员用户')
        verbose_name_plural = _('管理员用户')
        db_table = 'user'
    
    def __str__(self):
        return f"{self.username} ({self.display_role})"
    
    def save(self, *args, **kwargs):
        """
        重写保存方法，处理超级管理员逻辑
        """
        is_new = self.pk is None
        
        # 如果是新用户且关联了租户，检查配额
        if is_new and self.tenant:
            try:
                # 确保配额存在
                quota = self.tenant.ensure_quota()
                # 检查配额
                if not quota.can_add_user(is_admin=True):
                    raise PermissionDenied("租户管理员配额已满，无法创建更多管理员")
            except Exception as e:
                # 出现错误时记录错误
                logger.error(f"检查租户 {self.tenant.name} 的配额时发生错误: {str(e)}")
        
        # 如果用户是超级管理员，清除租户关联
        if self.is_super_admin and self.tenant:
            self.tenant = None
        
        # 确保is_admin始终为True
        self.is_admin = True
        
        # 超级管理员同时设置Django内置权限
        if self.is_super_admin:
            self.is_staff = True
            self.is_superuser = True
        
        super().save(*args, **kwargs)
    
    @property
    def is_tenant_admin(self):
        """
        判断用户是否是租户管理员
        """
        return not self.is_super_admin
    
    @property
    def display_role(self):
        """
        获取用户角色显示名称
        """
        if self.is_super_admin:
            return "超级管理员"
        else:
            return "租户管理员"
```

### Member模型

```python
class Member(BaseUserModel):
    """
    普通成员模型，包括普通用户和子账号
    """
    # 父账号关联，用于子账号功能
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="sub_accounts",
        verbose_name=_("父账号")
    )
    
    class Meta:
        verbose_name = _('普通成员')
        verbose_name_plural = _('普通成员')
        db_table = 'member'
    
    def __str__(self):
        if self.parent:
            return f"{self.username} (子账号)"
        return f"{self.username}"
    
    def save(self, *args, **kwargs):
        """
        重写保存方法，处理子账号逻辑和配额检查
        """
        is_new = self.pk is None
        
        # 如果是新用户且关联了租户，检查配额
        if is_new and self.tenant:
            try:
                # 确保配额存在
                quota = self.tenant.ensure_quota()
                # 检查配额
                if not quota.can_add_user(is_admin=False):
                    raise PermissionDenied("租户成员配额已满，无法创建更多成员")
            except Exception as e:
                # 出现错误时记录错误
                logger.error(f"检查租户 {self.tenant.name} 的配额时发生错误: {str(e)}")
        
        # 子账号不允许登录
        if self.parent:
            self.is_active = False
        
        super().save(*args, **kwargs)
    
    @property
    def is_sub_account(self):
        """
        判断是否为子账号
        """
        return self.parent is not None
    
    @property
    def display_role(self):
        """
        获取成员角色显示名称
        """
        if self.is_sub_account:
            return "子账号"
        else:
            return "普通成员"
```

## 数据库表设计

### user表（管理员用户）

| 字段名 | 类型 | 说明 | 约束 |
|-------|------|------|------|
| id | BigAutoField | 主键 | PK |
| username | CharField | 用户名 | unique |
| password | CharField | 密码 | - |
| email | EmailField | 邮箱 | - |
| phone | CharField | 手机号 | null=True |
| nick_name | CharField | 昵称 | null=True |
| avatar | CharField | 头像 | blank=True |
| first_name | CharField | 名 | blank=True |
| last_name | CharField | 姓 | blank=True |
| is_active | BooleanField | 是否激活 | default=True |
| is_staff | BooleanField | 是否可登录管理后台 | default=False |
| is_superuser | BooleanField | 是否超级用户 | default=False |
| is_admin | BooleanField | 是否管理员 | default=True |
| is_super_admin | BooleanField | 是否超级管理员 | default=False |
| is_deleted | BooleanField | 是否删除 | default=False |
| status | CharField | 状态 | default='active' |
| tenant_id | ForeignKey | 关联租户ID | null=True |
| last_login | DateTimeField | 最后登录时间 | null=True |
| last_login_ip | CharField | 最后登录IP | null=True |
| date_joined | DateTimeField | 注册时间 | auto_now_add=True |

### member表（普通成员）

| 字段名 | 类型 | 说明 | 约束 |
|-------|------|------|------|
| id | BigAutoField | 主键 | PK |
| username | CharField | 用户名 | unique |
| password | CharField | 密码 | - |
| email | EmailField | 邮箱 | - |
| phone | CharField | 手机号 | null=True |
| nick_name | CharField | 昵称 | null=True |
| avatar | CharField | 头像 | blank=True |
| first_name | CharField | 名 | blank=True |
| last_name | CharField | 姓 | blank=True |
| is_active | BooleanField | 是否激活 | default=True |
| is_superuser | BooleanField | 是否超级用户 | default=False |
| is_deleted | BooleanField | 是否删除 | default=False |
| status | CharField | 状态 | default='active' |
| tenant_id | ForeignKey | 关联租户ID | null=True |
| parent_id | ForeignKey | 父账号ID | null=True |
| last_login | DateTimeField | 最后登录时间 | null=True |
| last_login_ip | CharField | 最后登录IP | null=True |
| date_joined | DateTimeField | 注册时间 | auto_now_add=True |

## 注意事项

1. **AUTH_USER_MODEL设置**：需要修改Django设置中的`AUTH_USER_MODEL`，指向新的User模型
2. **动态关联名**：使用`%(class)ss`作为关联名，避免子类继承时的冲突
3. **数据库索引**：为常用查询字段添加索引，如`tenant_id`、`parent_id`、`username`等
4. **模型管理器**：需要为User和Member模型分别实现自定义管理器，处理查询逻辑
5. **权限控制**：需要调整权限检查机制，以适应两种用户模型 