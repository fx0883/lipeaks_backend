from django.apps import AppConfig


class PointsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'points'
    verbose_name = '多租户积分系统'
    
    def ready(self):
        """应用启动时执行的初始化操作"""
        # 导入信号处理器
        try:
            import points.signals
        except ImportError:
            pass
