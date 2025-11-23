"""
User Feedback System URL Configuration - APIView Version

完全移除ViewSet和Router，使用纯APIView模式
提供更好的调试体验和完全的控制能力
所有API都支持 Tenant-ID header 进行租户过滤
"""

from django.urls import path

# Software Management has been moved to applications module
# See /api/v1/applications/ for application management APIs

# Import Email Management APIViews
from .views.email_api_views import (
    EmailTemplateListView,
    EmailTemplateDetailView,
    EmailLogListView,
    EmailLogDetailView,
)

# Import Feedback Management APIViews
from .views.feedback_api_views import (
    FeedbackListView,
    FeedbackDetailView,
    FeedbackChangeStatusView,
    FeedbackVerifyEmailView,
    FeedbackToggleNotificationsView,
)

# Import Feedback Reply APIViews
from .views.feedback_reply_api_views import (
    FeedbackReplyListView,
    FeedbackReplyDetailView,
)

# Import Feedback Attachment APIViews
from .views.feedback_attachment_api_views import (
    FeedbackAttachmentListView,
    FeedbackAttachmentDetailView,
)

# Import other APIViews (already using APIView pattern)
from .complete_system import (
    FeedbackVoteView,
    FeedbackStatisticsView,
)

# Health check views (already APIView)
from .views.health_views import SystemHealthView, RedisStatusView

# Import Feedback Submission Page Views
from .views.feedback_submit_views import (
    FeedbackSubmitPageView,
    FeedbackSubmitSuccessView,
)

app_name = 'feedbacks'

urlpatterns = [
    # Software Management APIs have been moved to /api/v1/applications/
    
    # ==================== Email Management APIs ====================
    path('email-templates/', EmailTemplateListView.as_view(), name='email-template-list'),
    path('email-templates/<int:pk>/', EmailTemplateDetailView.as_view(), name='email-template-detail'),
    
    path('email-logs/', EmailLogListView.as_view(), name='email-log-list'),
    path('email-logs/<int:pk>/', EmailLogDetailView.as_view(), name='email-log-detail'),
    
    # ==================== Feedback Management APIs ====================
    path('feedbacks/', FeedbackListView.as_view(), name='feedback-list'),
    path('feedbacks/<int:pk>/', FeedbackDetailView.as_view(), name='feedback-detail'),
    path('feedbacks/<int:pk>/status/', FeedbackChangeStatusView.as_view(), name='feedback-change-status'),
    path('feedbacks/<int:pk>/verify-email/', FeedbackVerifyEmailView.as_view(), name='feedback-verify-email'),
    path('feedbacks/<int:pk>/notifications/', FeedbackToggleNotificationsView.as_view(), name='feedback-toggle-notifications'),
    path('feedbacks/<int:pk>/vote/', FeedbackVoteView.as_view(), name='feedback-vote'),
    
    # ==================== Feedback Reply APIs ====================
    path('feedbacks/<int:feedback_pk>/replies/', FeedbackReplyListView.as_view(), name='feedback-replies-list'),
    path('feedbacks/<int:feedback_pk>/replies/<int:pk>/', FeedbackReplyDetailView.as_view(), name='feedback-replies-detail'),
    
    # ==================== Feedback Attachment APIs ====================
    path('feedbacks/<int:feedback_pk>/attachments/', FeedbackAttachmentListView.as_view(), name='feedback-attachments-list'),
    path('feedbacks/<int:feedback_pk>/attachments/<int:pk>/', FeedbackAttachmentDetailView.as_view(), name='feedback-attachments-detail'),
    
    # ==================== Other APIs ====================
    path('statistics/', FeedbackStatisticsView.as_view(), name='feedback-statistics'),
    path('health/', SystemHealthView.as_view(), name='system-health'),
    path('health/redis/', RedisStatusView.as_view(), name='redis-status'),
    
    # ==================== Feedback Submission Pages (Server-side) ====================
    path('submit/', FeedbackSubmitPageView.as_view(), name='feedback-submit'),
    path('submit/success/', FeedbackSubmitSuccessView.as_view(), name='feedback-submit-success'),
]

# API Documentation
# The URLs will be automatically documented by drf-spectacular
# Access the API documentation at:
# - /api/schema/ - OpenAPI schema
# - /api/schema/swagger-ui/ - Swagger UI
# - /api/schema/redoc/ - ReDoc UI
