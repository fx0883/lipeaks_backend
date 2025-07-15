"""
RBAC应用配置
"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class RbacConfig(AppConfig):
    """RBAC权限系统应用配置"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'rbac'
    verbose_name = "RBAC权限系统"
    
    def ready(self):
        """应用准备就绪时执行的操作"""
        # 不再需要导入schemas模块
        pass
