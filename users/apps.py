from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'
    
    def ready(self):
        """
        应用就绪时注册信号处理器
        """
        import users.signals  # noqa: F401
