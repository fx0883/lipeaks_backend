"""
RBAC权限系统模型
"""
import logging
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

logger = logging.getLogger(__name__)

class Permission(models.Model):
    """
    权限模型，代表系统中的一个具体操作权限
    """
    code = models.CharField(_("权限代码"), max_length=100, unique=True, help_text="如：user:create")
    name = models.CharField(_("权限名称"), max_length=100, help_text="如：创建用户")
    description = models.TextField(_("权限描述"), blank=True, null=True)
    category = models.CharField(_("权限分类"), max_length=50, help_text="如：用户管理、内容管理等")
    is_system = models.BooleanField(_("是否系统权限"), default=False, help_text="系统权限不允许删除")
    
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    class Meta:
        verbose_name = _('权限')
        verbose_name_plural = _('权限')
        db_table = 'rbac_permission'
        ordering = ['category', 'code']
        
    def __str__(self):
        return f"{self.name} ({self.code})"
        
    def save(self, *args, **kwargs):
        """
        重写保存方法，添加日志记录
        """
        is_new = self.pk is None
        if is_new:
            logger.info(f"创建新权限: {self.code}")
        else:
            logger.info(f"更新权限: {self.code}")
            
        super().save(*args, **kwargs)


class Role(models.Model):
    """
    角色模型，代表一组权限的集合
    """
    name = models.CharField(_("角色名称"), max_length=100)
    code = models.CharField(_("角色代码"), max_length=50, help_text="用于API和代码中引用")
    description = models.TextField(_("角色描述"), blank=True, null=True)
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='roles',
        verbose_name=_("所属租户"),
        help_text=_("为空表示系统角色，所有租户可见")
    )
    is_system = models.BooleanField(_("是否系统角色"), default=False, help_text="系统角色不允许删除")
    
    # 通过中间表关联权限
    permissions = models.ManyToManyField(
        Permission,
        through='RolePermission',
        related_name='roles',
        verbose_name=_("权限")
    )
    
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    class Meta:
        verbose_name = _('角色')
        verbose_name_plural = _('角色')
        db_table = 'rbac_role'
        ordering = ['-created_at']
        # 角色名称在同一租户内唯一
        unique_together = [['name', 'tenant']]
        
    def __str__(self):
        tenant_name = self.tenant.name if self.tenant else "系统"
        return f"{self.name} ({tenant_name})"
    
    def save(self, *args, **kwargs):
        """
        重写保存方法，添加日志记录
        """
        is_new = self.pk is None
        if is_new:
            tenant_name = self.tenant.name if self.tenant else "系统"
            logger.info(f"创建新角色: {self.name} (租户: {tenant_name})")
        else:
            logger.info(f"更新角色: {self.name}")
            
        # 如果没有设置code，使用name的小写版本作为默认code
        if not self.code and self.name:
            self.code = self.name.lower().replace(' ', '_')
            
        super().save(*args, **kwargs)


class RolePermission(models.Model):
    """
    角色权限关联模型
    """
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='role_permissions',
        verbose_name=_("角色")
    )
    permission = models.ForeignKey(
        Permission,
        on_delete=models.CASCADE,
        related_name='role_permissions',
        verbose_name=_("权限")
    )
    
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)

    class Meta:
        verbose_name = _('角色权限')
        verbose_name_plural = _('角色权限')
        db_table = 'rbac_role_permission'
        # 确保一个角色不会重复分配同一权限
        unique_together = [['role', 'permission']]
        
    def __str__(self):
        return f"{self.role.name} - {self.permission.name}"


class UserRole(models.Model):
    """
    用户角色关联模型，支持两种用户类型：User和Member
    """
    USER_TYPE_CHOICES = (
        ('user', '管理员'),
        ('member', '普通成员'),
    )
    
    user_type = models.CharField(_("用户类型"), max_length=10, choices=USER_TYPE_CHOICES)
    user_id = models.IntegerField(_("用户ID"))
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='user_roles',
        verbose_name=_("角色")
    )
    is_active = models.BooleanField(_("是否激活"), default=True, help_text="可临时禁用角色")
    start_date = models.DateField(_("生效开始日期"), null=True, blank=True)
    end_date = models.DateField(_("生效结束日期"), null=True, blank=True)
    
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    class Meta:
        verbose_name = _('用户角色')
        verbose_name_plural = _('用户角色')
        db_table = 'rbac_user_role'
        # 确保一个用户不会重复分配同一角色
        unique_together = [['user_type', 'user_id', 'role']]
        
    def __str__(self):
        return f"{self.get_user_type_display()} ID:{self.user_id} - {self.role.name}"
    
    def save(self, *args, **kwargs):
        """
        重写保存方法，添加日志记录
        """
        is_new = self.pk is None
        if is_new:
            logger.info(f"为 {self.get_user_type_display()} ID:{self.user_id} 分配角色: {self.role.name}")
        else:
            logger.info(f"更新 {self.get_user_type_display()} ID:{self.user_id} 的角色 {self.role.name}")
            
        super().save(*args, **kwargs)
    
    @property
    def user(self):
        """
        获取关联的用户对象
        """
        if self.user_type == 'user':
            from users.models import User
            try:
                return User.objects.get(pk=self.user_id)
            except User.DoesNotExist:
                return None
        elif self.user_type == 'member':
            from users.models import Member
            try:
                return Member.objects.get(pk=self.user_id)
            except Member.DoesNotExist:
                return None
        return None
