"""
菜单管理系统模型定义
"""
import logging
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings

logger = logging.getLogger(__name__)

class Menu(models.Model):
    """
    菜单模型，定义系统的导航菜单项，适配前端路由配置
    """
    # 基本路由配置
    name = models.CharField(_("路由名称"), max_length=100, unique=True)  # 对应前端 name
    code = models.CharField(_("唯一标识符"), max_length=100, unique=True)  # 保留原有字段，用于后端标识
    path = models.CharField(_("路由路径"), max_length=200)  # 对应前端 path
    component = models.CharField(_("前端组件路径"), max_length=200, null=True, blank=True)  # 对应前端 component
    redirect = models.CharField(_("重定向路径"), max_length=200, null=True, blank=True)  # 对应前端 redirect
    
    # Meta 相关字段
    title = models.CharField(_("菜单标题"), max_length=100)  # 对应前端 meta.title
    icon = models.CharField(_("图标名称"), max_length=100, null=True, blank=True)  # 对应前端 meta.icon
    extra_icon = models.CharField(_("额外图标"), max_length=100, null=True, blank=True)  # 对应前端 meta.extraIcon
    rank = models.IntegerField(_("菜单排序"), default=0)  # 对应前端 meta.rank
    show_link = models.BooleanField(_("是否在菜单中显示"), default=True)  # 对应前端 meta.showLink
    show_parent = models.BooleanField(_("是否显示父级菜单"), default=True)  # 对应前端 meta.showParent
    roles = models.JSONField(_("页面级别权限设置"), default=list, null=True, blank=True)  # 对应前端 meta.roles
    auths = models.JSONField(_("按钮级别权限设置"), default=list, null=True, blank=True)  # 对应前端 meta.auths
    keep_alive = models.BooleanField(_("是否缓存路由页面"), default=False)  # 对应前端 meta.keepAlive
    frame_src = models.CharField(_("iframe链接地址"), max_length=255, null=True, blank=True)  # 对应前端 meta.frameSrc
    frame_loading = models.BooleanField(_("iframe是否开启首次加载动画"), default=True)  # 对应前端 meta.frameLoading
    hidden_tag = models.BooleanField(_("禁止添加到标签页"), default=False)  # 对应前端 meta.hiddenTag
    dynamic_level = models.IntegerField(_("标签页最大数量"), null=True, blank=True)  # 对应前端 meta.dynamicLevel
    active_path = models.CharField(_("激活菜单的路径"), max_length=200, null=True, blank=True)  # 对应前端 meta.activePath
    
    # Transition 相关字段
    transition_name = models.CharField(_("页面动画名称"), max_length=100, null=True, blank=True)  # 对应前端 meta.transition.name
    enter_transition = models.CharField(_("进场动画"), max_length=100, null=True, blank=True)  # 对应前端 meta.transition.enterTransition
    leave_transition = models.CharField(_("离场动画"), max_length=100, null=True, blank=True)  # 对应前端 meta.transition.leaveTransition
    
    # 层级关系
    parent = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='children',
        verbose_name=_("父菜单")
    )
    
    # 状态字段
    is_active = models.BooleanField(_("是否启用"), default=True)
    remarks = models.TextField(_("备注说明"), null=True, blank=True)
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    class Meta:
        verbose_name = _('菜单')
        verbose_name_plural = _('菜单')
        db_table = 'menu'
        ordering = ['rank', 'id']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """
        重写保存方法，检查是否存在循环引用
        """
        if self.pk and self.parent:
            # 检查是否存在循环引用
            if self._check_circular_reference(self.parent_id, self.pk):
                logger.error(f"检测到循环引用: 菜单 {self.title} 不能将 {self.parent.title} 设为父菜单")
                raise ValueError(f"检测到循环引用: 菜单 '{self.title}' 不能将 '{self.parent.title}' 设为父菜单")
        
        is_new = self.pk is None
        action = "创建" if is_new else "更新"
        logger.info(f"{action}菜单: {self.title}")
        
        super().save(*args, **kwargs)

    def _check_circular_reference(self, parent_id, menu_id):
        """
        检查是否存在循环引用
        
        Args:
            parent_id: 父菜单ID
            menu_id: 当前菜单ID
            
        Returns:
            布尔值，指示是否存在循环引用
        """
        if parent_id == menu_id:
            return True
        
        parent = Menu.objects.filter(id=parent_id).first()
        if parent and parent.parent_id:
            return self._check_circular_reference(parent.parent_id, menu_id)
        
        return False

    def get_descendants(self, include_self=False):
        """
        获取当前菜单的所有后代菜单
        
        Args:
            include_self: 是否包含自身
            
        Returns:
            菜单列表
        """
        descendants = []
        if include_self:
            descendants.append(self)
            
        children = Menu.objects.filter(parent_id=self.id)
        for child in children:
            descendants.extend(child.get_descendants(include_self=True))
            
        return descendants
    
    def activate(self):
        """
        激活菜单
        """
        self.is_active = True
        self.save(update_fields=['is_active', 'updated_at'])
    
    def deactivate(self):
        """
        停用菜单
        """
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])


class UserMenu(models.Model):
    """
    用户菜单关联模型，定义用户与菜单的多对多关系
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='user_menus',
        verbose_name=_("用户")
    )
    menu = models.ForeignKey(
        Menu, 
        on_delete=models.CASCADE, 
        related_name='user_menus',
        verbose_name=_("菜单")
    )
    is_active = models.BooleanField(_("是否启用"), default=True)
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)

    class Meta:
        verbose_name = _('用户菜单')
        verbose_name_plural = _('用户菜单')
        db_table = 'user_menu'
        # 确保同一个用户不会重复分配相同的菜单
        unique_together = ('user', 'menu')
        ordering = ['user', 'menu__rank']

    def __str__(self):
        return f"{self.user.username} - {self.menu.title}"
    
    def save(self, *args, **kwargs):
        """
        重写保存方法，添加日志
        """
        is_new = self.pk is None
        action = "分配" if is_new else "更新"
        logger.info(f"{action}用户菜单: {self.user.username} - {self.menu.title}")
        
        super().save(*args, **kwargs)
    
    def activate(self):
        """
        激活用户菜单关联
        """
        self.is_active = True
        self.save(update_fields=['is_active', 'updated_at'])
        logger.info(f"激活用户菜单: {self.user.username} - {self.menu.title}")
    
    def deactivate(self):
        """
        停用用户菜单关联
        """
        self.is_active = False
        self.save(update_fields=['is_active', 'updated_at'])
        logger.info(f"停用用户菜单: {self.user.username} - {self.menu.title}")
