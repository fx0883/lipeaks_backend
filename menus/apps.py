from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MenusConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'menus'
    verbose_name = _('菜单管理')
    
    def ready(self):
        """
        应用就绪时执行的操作
        """
        try:
            # 导入信号模块以确保信号被注册
            import menus.signals  # noqa
        except ImportError:
            pass
