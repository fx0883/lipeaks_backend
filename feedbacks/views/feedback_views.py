"""
Feedback Management Views

This module contains views for managing user feedback submissions.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, Count, Avg
from django.utils import timezone
from common.viewsets import TenantModelViewSet
from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiExample,
    OpenApiResponse,
    inline_serializer
)
from drf_spectacular.types import OpenApiTypes
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework import serializers as drf_serializers

from ..models import Feedback, FeedbackStatusHistory
from ..serializers import (
    FeedbackListSerializer,
    FeedbackDetailSerializer,
    FeedbackCreateSerializer,
    FeedbackUpdateSerializer,
)
from ..permissions import (
    FeedbackViewPermission,
    FeedbackCreatePermission,
    FeedbackUpdatePermission,
    FeedbackDeletePermission,
    FeedbackStatusChangePermission
)


@extend_schema_view(
    list=extend_schema(
        tags=['Feedback System'],
        summary='List feedback',
        description='Get a list of feedback. Permissions: Super admins see all tenant feedback, '
                   'tenant admins see all tenant feedback, regular users see only their own.',
        parameters=[
            OpenApiParameter(
                name='software',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by software ID'
            ),
            OpenApiParameter(
                name='feedback_type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by feedback type',
                enum=['bug', 'feature', 'improvement', 'question', 'other']
            ),
            OpenApiParameter(
                name='status',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by status',
                enum=['submitted', 'reviewing', 'confirmed', 'in_progress', 
                      'resolved', 'closed', 'rejected', 'duplicate']
            ),
            OpenApiParameter(
                name='priority',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by priority',
                enum=['critical', 'high', 'medium', 'low']
            ),
            OpenApiParameter(
                name='user',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by user ID (admin only)'
            ),
            OpenApiParameter(
                name='email_verified',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                description='Filter by email verification status'
            ),
            OpenApiParameter(
                name='search',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Search in title, description, and contact email'
            ),
            OpenApiParameter(
                name='ordering',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Order by field (prefix with - for descending)',
                enum=['created_at', '-created_at', 'vote_count', '-vote_count', 
                      'reply_count', '-reply_count', 'priority', '-priority']
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=FeedbackListSerializer(many=True),
                description='List of feedback',
                examples=[
                    OpenApiExample(
                        'Success Response',
                        value=[
                            {
                                'id': 1,
                                'title': 'Application crashes on startup',
                                'description': 'The app crashes when trying to start...',
                                'feedback_type': 'bug',
                                'type_display': 'Bug Report',
                                'priority': 'high',
                                'priority_display': 'High',
                                'status': 'reviewing',
                                'status_display': 'Reviewing',
                                'software': 1,
                                'software_name': 'CRM System',
                                'submitter': {
                                    'id': 1,
                                    'username': 'johndoe',
                                    'email': 'john@example.com'
                                },
                                'contact_email': 'john@example.com',
                                'vote_count': 5,
                                'reply_count': 2,
                                'created_at': '2025-01-01T00:00:00Z',
                                'updated_at': '2025-01-01T00:00:00Z'
                            }
                        ]
                    )
                ]
            ),
            401: OpenApiResponse(description='Authentication required')
        }
    ),
    create=extend_schema(
        tags=['Feedback System'],
        summary='Submit feedback',
        description='Submit new feedback. Anyone can submit feedback, including anonymous users. '
                   'Anonymous users must provide an email address.',
        request=FeedbackCreateSerializer,
        responses={
            201: OpenApiResponse(
                response=FeedbackDetailSerializer,
                description='Feedback submitted successfully'
            ),
            400: OpenApiResponse(description='Invalid input data')
        },
        examples=[
            OpenApiExample(
                'Submit Feedback Request',
                value={
                    'title': 'Feature request: Dark mode',
                    'description': 'It would be great to have a dark mode option...',
                    'feedback_type': 'feature',
                    'priority': 'medium',
                    'software': 1,
                    'contact_email': 'user@example.com',
                    'contact_name': 'John Doe',
                    'environment_info': {
                        'os': 'Windows 10',
                        'browser': 'Chrome 96',
                        'screen_resolution': '1920x1080'
                    }
                },
                request_only=True
            )
        ]
    ),
    retrieve=extend_schema(
        tags=['Feedback System'],
        summary='Get feedback details',
        description='Retrieve detailed information about specific feedback. '
                   'Permissions vary based on user role.',
        responses={
            200: OpenApiResponse(
                response=FeedbackDetailSerializer,
                description='Feedback details'
            ),
            403: OpenApiResponse(description='Permission denied'),
            404: OpenApiResponse(description='Feedback not found')
        }
    ),
    update=extend_schema(
        tags=['Feedback System'],
        summary='Update feedback',
        description='Update feedback. Admins can update any feedback, users can update '
                   'their own if not replied to.',
        request=FeedbackUpdateSerializer,
        responses={
            200: FeedbackDetailSerializer,
            400: OpenApiResponse(description='Invalid input data'),
            403: OpenApiResponse(description='Permission denied'),
            404: OpenApiResponse(description='Feedback not found')
        }
    ),
    partial_update=extend_schema(
        tags=['Feedback System'],
        summary='Partially update feedback',
        description='Update specific fields of feedback.',
        request=FeedbackUpdateSerializer,
        responses={
            200: FeedbackDetailSerializer,
            400: OpenApiResponse(description='Invalid input data'),
            403: OpenApiResponse(description='Permission denied'),
            404: OpenApiResponse(description='Feedback not found')
        }
    ),
    destroy=extend_schema(
        tags=['Feedback System'],
        summary='Delete feedback',
        description='Soft delete feedback. Admins can delete any feedback, users can delete '
                   'their own if not replied to.',
        responses={
            204: OpenApiResponse(description='Feedback deleted successfully'),
            403: OpenApiResponse(description='Permission denied'),
            404: OpenApiResponse(description='Feedback not found')
        }
    )
)
class FeedbackViewSet(TenantModelViewSet):
    """
    ViewSet for managing feedback
    
    继承TenantModelViewSet自动处理租户过滤、设置和验证
    """
    queryset = Feedback.objects.filter(is_deleted=False)
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = [
        'software', 'application', 'feedback_type', 
        'status', 'priority', 'email_verified'
    ]
    search_fields = ['title', 'description', 'contact_email', 'contact_name']
    ordering_fields = ['created_at', 'vote_count', 'reply_count', 'priority']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'list':
            return FeedbackListSerializer
        elif self.action == 'create':
            return FeedbackCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return FeedbackUpdateSerializer
        return FeedbackDetailSerializer
    
    def get_permissions(self):
        """Get permissions based on action"""
        if self.action == 'create':
            permission_classes = [FeedbackCreatePermission]
        elif self.action in ['list', 'retrieve']:
            permission_classes = [FeedbackViewPermission]
        elif self.action in ['update', 'partial_update']:
            permission_classes = [FeedbackUpdatePermission]
        elif self.action == 'destroy':
            permission_classes = [FeedbackDeletePermission]
        elif self.action == 'change_status':
            permission_classes = [FeedbackStatusChangePermission]
        else:
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """
        Filter queryset based on user permissions
        TenantModelViewSet已经处理租户过滤
        """
        queryset = super().get_queryset()  # 租户过滤已处理
        user = self.request.user
        
        if not user.is_authenticated:
            return queryset.none()
        
        # Additional filtering based on user role
        if not user.is_superuser and not getattr(user, 'is_tenant_admin', False):
            # Regular users can only see their own feedback
            queryset = queryset.filter(user=user)
        
        # Allow filtering by user ID for admins
        if self.action == 'list' and (user.is_superuser or getattr(user, 'is_tenant_admin', False)):
            user_id = self.request.query_params.get('user')
            if user_id:
                queryset = queryset.filter(user_id=user_id)
        
        return queryset
    
    def perform_create(self, serializer):
        """
        Set tenant when creating feedback
        TenantModelViewSet自动设置租户
        """
        # TenantModelViewSet会自动设置tenant
        super().perform_create(serializer)
    
    def retrieve(self, request, *args, **kwargs):
        """Increment view count when retrieving feedback"""
        instance = self.get_object()
        instance.view_count += 1
        instance.save(update_fields=['view_count'])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @extend_schema(
        tags=['Feedback System'],
        summary='Change feedback status',
        description='Change the status of feedback. Only administrators can perform this action. '
                   'A status history record will be created.',
        request=inline_serializer(
            name='ChangeStatusRequest',
            fields={
                'status': drf_serializers.ChoiceField(
                    choices=Feedback.STATUS_CHOICES,
                    help_text='New status'
                ),
                'reason': drf_serializers.CharField(
                    required=False,
                    help_text='Reason for status change'
                )
            }
        ),
        responses={
            200: OpenApiResponse(
                response=FeedbackDetailSerializer,
                description='Status changed successfully'
            ),
            400: OpenApiResponse(description='Invalid status transition'),
            403: OpenApiResponse(description='Permission denied'),
            404: OpenApiResponse(description='Feedback not found')
        },
        examples=[
            OpenApiExample(
                'Change Status Request',
                value={
                    'status': 'in_progress',
                    'reason': 'Assigned to development team'
                },
                request_only=True
            )
        ]
    )
    @action(detail=True, methods=['patch'], url_path='status')
    def change_status(self, request, pk=None):
        """Change feedback status with history tracking"""
        feedback = self.get_object()
        new_status = request.data.get('status')
        reason = request.data.get('reason', '')
        
        if not new_status:
            return Response(
                {'error': _('Status is required')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate status transition
        valid_transitions = {
            'submitted': ['reviewing', 'rejected', 'duplicate'],
            'reviewing': ['confirmed', 'rejected', 'duplicate'],
            'confirmed': ['in_progress', 'rejected', 'duplicate'],
            'in_progress': ['resolved', 'rejected'],
            'resolved': ['closed', 'in_progress'],
            'closed': ['submitted'],
            'rejected': ['submitted'],
            'duplicate': ['submitted'],
        }
        
        if new_status not in valid_transitions.get(feedback.status, []):
            return Response(
                {'error': _(f'Cannot change status from {feedback.status} to {new_status}')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Use service to change status (handles history and email)
        from ..services import FeedbackService
        FeedbackService.change_status(
            feedback=feedback,
            new_status=new_status,
            changed_by=request.user,
            reason=reason
        )
        
        serializer = FeedbackDetailSerializer(feedback, context={'request': request})
        return Response(serializer.data)
    
    @extend_schema(
        tags=['Feedback System'],
        summary='Verify email',
        description='Verify email address for anonymous feedback submission.',
        request=inline_serializer(
            name='VerifyEmailRequest',
            fields={
                'token': drf_serializers.CharField(
                    help_text='Email verification token'
                )
            }
        ),
        responses={
            200: OpenApiResponse(
                description='Email verified successfully'
            ),
            400: OpenApiResponse(description='Invalid or expired token'),
            404: OpenApiResponse(description='Feedback not found')
        }
    )
    @action(detail=True, methods=['post'], url_path='verify-email', permission_classes=[AllowAny])
    def verify_email(self, request, pk=None):
        """Verify email for anonymous feedback"""
        feedback = self.get_object()
        token = request.data.get('token')
        
        if not token:
            return Response(
                {'error': _('Token is required')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if feedback.email_verified:
            return Response(
                {'message': _('Email already verified')},
                status=status.HTTP_200_OK
            )
        
        if feedback.email_verification_token != token:
            return Response(
                {'error': _('Invalid verification token')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check token expiry (24 hours)
        if feedback.email_verification_sent_at:
            expiry_time = feedback.email_verification_sent_at + timezone.timedelta(hours=24)
            if timezone.now() > expiry_time:
                return Response(
                    {'error': _('Verification token has expired')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Mark as verified
        feedback.email_verified = True
        feedback.email_verification_token = None
        feedback.save(update_fields=['email_verified', 'email_verification_token'])
        
        return Response({'message': _('Email verified successfully')})
    
    @extend_schema(
        tags=['Feedback System'],
        summary='Toggle email notifications',
        description='Enable or disable email notifications for feedback updates.',
        request=inline_serializer(
            name='ToggleNotificationRequest',
            fields={
                'enabled': drf_serializers.BooleanField(
                    help_text='Enable or disable notifications'
                )
            }
        ),
        responses={
            200: OpenApiResponse(
                description='Notification settings updated'
            ),
            403: OpenApiResponse(description='Permission denied'),
            404: OpenApiResponse(description='Feedback not found')
        }
    )
    @action(detail=True, methods=['patch'], url_path='notifications')
    def toggle_notifications(self, request, pk=None):
        """Toggle email notifications for feedback"""
        feedback = self.get_object()
        
        # Only the submitter can change notification settings
        if feedback.user != request.user and feedback.contact_email != request.user.email:
            return Response(
                {'error': _('You can only change notification settings for your own feedback')},
                status=status.HTTP_403_FORBIDDEN
            )
        
        enabled = request.data.get('enabled')
        if enabled is None:
            return Response(
                {'error': _('Enabled field is required')},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        feedback.email_notification_enabled = enabled
        feedback.save(update_fields=['email_notification_enabled'])
        
        return Response({
            'message': _('Notification settings updated'),
            'email_notification_enabled': feedback.email_notification_enabled
        })
