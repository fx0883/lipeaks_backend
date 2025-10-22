"""
User Feedback System App Configuration
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FeedbacksConfig(AppConfig):
    """Configuration for the Feedbacks application"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'feedbacks'
    verbose_name = _('User Feedback System')
    
    def ready(self):
        """
        Application initialization
        Import signal handlers when Django starts
        """
        # Import signal handlers if any
        # from . import signals
        pass