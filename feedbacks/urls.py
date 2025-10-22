"""
User Feedback System URL Configuration

This module defines all URL patterns for the feedback management system.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    SoftwareCategoryViewSet,
    SoftwareViewSet,
    SoftwareVersionViewSet,
    FeedbackViewSet,
)

# Import views from complete_system.py temporarily
# In production, these should be in separate files
from .complete_system import (
    FeedbackReplyViewSet,
    FeedbackVoteView,
    FeedbackAttachmentViewSet,
    FeedbackStatisticsView,
    EmailTemplateViewSet,
    EmailLogViewSet
)

# Health check views
from .views.health_views import SystemHealthView, RedisStatusView

app_name = 'feedbacks'

# Main router
router = DefaultRouter()

# Software management routes
router.register(r'software-categories', SoftwareCategoryViewSet, basename='software-category')
router.register(r'software', SoftwareViewSet, basename='software')
router.register(r'software-versions', SoftwareVersionViewSet, basename='software-version')

# Feedback management routes
router.register(r'feedbacks', FeedbackViewSet, basename='feedback')

# Email management routes
router.register(r'email-templates', EmailTemplateViewSet, basename='email-template')
router.register(r'email-logs', EmailLogViewSet, basename='email-log')

urlpatterns = [
    # Include main router URLs
    path('', include(router.urls)),
    
    # Nested feedback-related routes
    path('feedbacks/<int:feedback_pk>/replies/', 
         FeedbackReplyViewSet.as_view({'get': 'list', 'post': 'create'}), 
         name='feedback-replies-list'),
    path('feedbacks/<int:feedback_pk>/replies/<int:pk>/', 
         FeedbackReplyViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), 
         name='feedback-replies-detail'),
    
    path('feedbacks/<int:feedback_pk>/attachments/', 
         FeedbackAttachmentViewSet.as_view({'get': 'list', 'post': 'create'}), 
         name='feedback-attachments-list'),
    path('feedbacks/<int:feedback_pk>/attachments/<int:pk>/', 
         FeedbackAttachmentViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'}), 
         name='feedback-attachments-detail'),
    
    # Individual action URLs
    path('feedbacks/<int:pk>/vote/', FeedbackVoteView.as_view(), name='feedback-vote'),
    path('statistics/', FeedbackStatisticsView.as_view(), name='feedback-statistics'),
    
    # System Health Check URLs
    path('health/', SystemHealthView.as_view(), name='system-health'),
    path('health/redis/', RedisStatusView.as_view(), name='redis-status'),
    
    # Convenience URLs for common operations
    path('feedbacks/<int:pk>/verify-email/', 
         FeedbackViewSet.as_view({'post': 'verify_email'}), 
         name='feedback-verify-email'),
    path('feedbacks/<int:pk>/status/', 
         FeedbackViewSet.as_view({'patch': 'change_status'}), 
         name='feedback-change-status'),
    path('feedbacks/<int:pk>/notifications/', 
         FeedbackViewSet.as_view({'patch': 'toggle_notifications'}), 
         name='feedback-toggle-notifications'),
]

# API Documentation
# The URLs will be automatically documented by drf-spectacular
# Access the API documentation at:
# - /api/schema/ - OpenAPI schema
# - /api/schema/swagger-ui/ - Swagger UI
# - /api/schema/redoc/ - ReDoc UI
