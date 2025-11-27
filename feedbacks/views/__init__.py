"""
User Feedback System Views

This package contains all view modules for the feedback management system.
All views now use APIView pattern for better control and debugging.
All views support Tenant-ID header for multi-tenant filtering.
"""

# Import APIView versions (all feedback system now uses APIView instead of ViewSet)
from .feedback_api_views import (
    FeedbackListView,
    FeedbackDetailView,
    FeedbackChangeStatusView,
    FeedbackVerifyEmailView,
    FeedbackToggleNotificationsView,
)
from .feedback_reply_api_views import (
    FeedbackReplyListView,
    FeedbackReplyDetailView,
)
from .feedback_attachment_api_views import (
    FeedbackAttachmentListView,
    FeedbackAttachmentDetailView,
)
# Application/Software management has been moved to applications module
# from .application_api_views import (...)
from .email_api_views import (
    EmailTemplateListView,
    EmailTemplateDetailView,
    EmailLogListView,
    EmailLogDetailView,
)
from .notification_config_views import (
    FeedbackNotificationConfigViewSet,
)

__all__ = [
    # Feedback Management
    'FeedbackListView',
    'FeedbackDetailView',
    'FeedbackChangeStatusView',
    'FeedbackVerifyEmailView',
    'FeedbackToggleNotificationsView',
    # Feedback Reply
    'FeedbackReplyListView',
    'FeedbackReplyDetailView',
    # Feedback Attachment
    'FeedbackAttachmentListView',
    'FeedbackAttachmentDetailView',
    # Software Management moved to applications module
    # Email Management
    'EmailTemplateListView',
    'EmailTemplateDetailView',
    'EmailLogListView',
    'EmailLogDetailView',
    # Notification Configuration
    'FeedbackNotificationConfigViewSet',
]
