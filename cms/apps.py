from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CmsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'cms'
    verbose_name = _('内容管理系统')
    
    def ready(self):
        """
        应用准备就绪时的回调函数
        """
        # 导入信号处理器
        try:
            import cms.signals
        except ImportError:
            pass
