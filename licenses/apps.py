from django.apps import AppConfig


class LicensesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'licenses'
    
    def ready(self):
        """应用启动时注册信号处理器"""
        import licenses.signals