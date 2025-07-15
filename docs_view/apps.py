from django.apps import AppConfig


class DocsViewConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'docs_view'
    verbose_name = 'Markdown文档查看器'
