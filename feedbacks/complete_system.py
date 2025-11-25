"""
Complete Feedback System Implementation

This file contains all remaining views and components for rapid deployment.
Split these into appropriate files in production.
"""

# ===================== Reply Views =====================

from rest_framework import viewsets, status, generics, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils.translation import gettext_lazy as _
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta
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
import json

# Import models
from .models import (
    Feedback, FeedbackReply, FeedbackVote, FeedbackAttachment,
    FeedbackEmailLog, EmailTemplate, FeedbackStatusHistory
)
# Import serializers
from .serializers import (
    FeedbackReplySerializer, FeedbackVoteSerializer,
    FeedbackAttachmentSerializer, EmailTemplateSerializer,
    FeedbackEmailLogSerializer
)
# Import permissions
from .permissions import (
    FeedbackReplyPermission, FeedbackVotePermission,
    EmailTemplatePermission, StatisticsViewPermission
)


# Reply Views
@extend_schema_view(
    list=extend_schema(
        tags=['Feedback System'],
        summary='List feedback replies',
        description='Get all replies for a specific feedback. Staff see all replies, others see only non-internal.',
        responses={
            200: OpenApiResponse(
                description='List of replies'
            ),
            404: OpenApiResponse(description='Feedback not found')
        }
    ),
    create=extend_schema(
        tags=['Feedback System'],
        summary='Add reply to feedback',
        description='Add a reply to feedback. Only administrators can reply.',
        responses={
            201: OpenApiResponse(description='Reply added successfully'),
            400: OpenApiResponse(description='Invalid input data'),
            403: OpenApiResponse(description='Permission denied'),
            404: OpenApiResponse(description='Feedback not found')
        }
    )
)
class FeedbackReplyViewSet(TenantModelViewSet):
    """
    ViewSet for feedback replies
    
    继承TenantModelViewSet自动处理租户过滤、设置和验证
    """
    serializer_class = FeedbackReplySerializer
    permission_classes = [FeedbackReplyPermission]
    
    def get_queryset(self):
        feedback_id = self.kwargs.get('feedback_pk')
        queryset = FeedbackReply.objects.filter(
            feedback_id=feedback_id
        )
        
        # Non-staff users don't see internal notes
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_internal_note=False)
        
        return queryset
    
    def perform_create(self, serializer):
        feedback_id = self.kwargs.get('feedback_pk')
        feedback = Feedback.objects.get(pk=feedback_id)
        
        # Use service to add reply (handles email)
        from .services import FeedbackService
        reply = FeedbackService.add_reply(
            feedback=feedback,
            content=serializer.validated_data['content'],
            user=self.request.user,
            is_internal_note=serializer.validated_data.get('is_internal_note', False)
        )
        
        # Update serializer instance
        serializer.instance = reply


# Vote Views
class FeedbackVoteView(APIView):
    """View for voting on feedback"""
    
    @extend_schema(
        tags=['Feedback System'],
        summary='Vote on feedback',
        description='Submit or update vote on feedback. Users can only have one vote per feedback.',
        request=inline_serializer(
            name='VoteRequest',
            fields={
                'vote_type': serializers.ChoiceField(
                    choices=[(1, 'Upvote'), (-1, 'Downvote')],
                    help_text='1 for upvote, -1 for downvote'
                )
            }
        ),
        responses={
            200: OpenApiResponse(description='Vote recorded'),
            400: OpenApiResponse(description='Invalid vote type'),
            401: OpenApiResponse(description='Authentication required'),
            404: OpenApiResponse(description='Feedback not found')
        }
    )
    def post(self, request, pk):
        """Submit or update vote"""
        try:
            feedback = Feedback.objects.get(pk=pk)
        except Feedback.DoesNotExist:
            return Response({'error': 'Feedback not found'}, status=404)
        
        vote_type = request.data.get('vote_type')
        if vote_type not in [1, -1]:
            return Response({'error': 'Invalid vote type'}, status=400)
        
        # 获取租户
        tenant = self._get_tenant_from_request(request)
        
        vote, created = FeedbackVote.objects.update_or_create(
            feedback=feedback,
            user=request.user,
            defaults={'vote_type': vote_type, 'tenant': tenant}
        )
        
        # 刷新获取最新的vote_count
        feedback.refresh_from_db()
        
        return Response({
            'message': 'Vote recorded',
            'vote_type': vote_type,
            'total_votes': feedback.vote_count
        })
    
    def _get_tenant_from_request(self, request):
        """从request中获取租户"""
        # 1. 尝试从request属性获取
        tenant = getattr(request, 'tenant', None)
        if tenant:
            return tenant
        
        # 2. 尝试从线程本地存储获取
        from common.utils.tenant_context import get_current_tenant
        tenant = get_current_tenant()
        if tenant:
            return tenant
        
        # 3. 尝试从用户关联的租户获取
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            tenant = getattr(user, 'tenant', None)
            if tenant:
                return tenant
        
        return None
    
    @extend_schema(
        tags=['Feedback System'],
        summary='Remove vote',
        description='Remove user vote from feedback.',
        responses={
            204: OpenApiResponse(description='Vote removed'),
            404: OpenApiResponse(description='Vote not found')
        }
    )
    def delete(self, request, pk):
        """Remove vote"""
        try:
            feedback = Feedback.objects.get(pk=pk)
            vote = FeedbackVote.objects.get(feedback=feedback, user=request.user)
            vote.delete()
            return Response(status=204)
        except (Feedback.DoesNotExist, FeedbackVote.DoesNotExist):
            return Response({'error': 'Vote not found'}, status=404)


# Statistics Views
class FeedbackStatisticsView(APIView):
    """View for feedback statistics"""
    permission_classes = [StatisticsViewPermission]
    
    @extend_schema(
        tags=['Feedback System'],
        summary='Get feedback statistics',
        description='Get comprehensive statistics about feedback. Only administrators can access.',
        parameters=[
            OpenApiParameter(
                name='software',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by software ID'
            ),
            OpenApiParameter(
                name='date_from',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='Start date for statistics'
            ),
            OpenApiParameter(
                name='date_to',
                type=OpenApiTypes.DATE,
                location=OpenApiParameter.QUERY,
                description='End date for statistics'
            ),
        ],
        responses={
            200: OpenApiResponse(
                description='Statistics data',
                examples=[
                    OpenApiExample(
                        'Statistics Response',
                        value={
                            'total_feedbacks': 150,
                            'open_feedbacks': 25,
                            'resolved_feedbacks': 100,
                            'avg_resolution_time': '3 days, 4:30:00',
                            'feedbacks_by_type': {
                                'bug': 60,
                                'feature': 40,
                                'improvement': 30,
                                'question': 15,
                                'other': 5
                            },
                            'feedbacks_by_status': {
                                'submitted': 10,
                                'reviewing': 5,
                                'confirmed': 10,
                                'in_progress': 15,
                                'resolved': 100,
                                'closed': 5,
                                'rejected': 3,
                                'duplicate': 2
                            },
                            'feedbacks_by_priority': {
                                'critical': 10,
                                'high': 30,
                                'medium': 80,
                                'low': 30
                            },
                            'top_voted_feedbacks': [],
                            'recent_feedbacks': [],
                            'daily_trend': []
                        }
                    )
                ]
            ),
            403: OpenApiResponse(description='Permission denied')
        }
    )
    def get(self, request):
        """Get statistics"""
        # Permission is checked by permission_classes
        
        # Get parameters (compatible with both DRF Request and Django Request)
        query_params = getattr(request, 'query_params', request.GET)
        software_id = query_params.get('software')
        date_from = query_params.get('date_from')
        date_to = query_params.get('date_to')
        
        # Base queryset
        queryset = Feedback.objects.all()
        
        if hasattr(request, 'tenant'):
            queryset = queryset.filter(tenant=request.tenant)
        
        if software_id:
            queryset = queryset.filter(software_id=software_id)
        
        if date_from:
            queryset = queryset.filter(created_at__gte=date_from)
        
        if date_to:
            queryset = queryset.filter(created_at__lte=date_to)
        
        # Calculate statistics
        stats = {
            'total_feedbacks': queryset.count(),
            'open_feedbacks': queryset.filter(
                status__in=['submitted', 'reviewing', 'confirmed', 'in_progress']
            ).count(),
            'resolved_feedbacks': queryset.filter(status='resolved').count(),
            'avg_resolution_time': self._calculate_avg_resolution_time(queryset),
            'feedbacks_by_type': self._count_by_field(queryset, 'feedback_type'),
            'feedbacks_by_status': self._count_by_field(queryset, 'status'),
            'feedbacks_by_priority': self._count_by_field(queryset, 'priority'),
            'top_voted_feedbacks': self._get_top_voted(queryset, request),
            'recent_feedbacks': self._get_recent(queryset, request),
            'daily_trend': self._get_daily_trend(queryset)
        }
        
        return Response(stats)
    
    def _calculate_avg_resolution_time(self, queryset):
        resolved = queryset.filter(
            status='resolved',
            resolved_at__isnull=False
        )
        if not resolved.exists():
            return None
        
        total_time = timedelta()
        count = 0
        for feedback in resolved:
            total_time += (feedback.resolved_at - feedback.created_at)
            count += 1
        
        if count > 0:
            avg_time = total_time / count
            return str(avg_time)
        return None
    
    def _count_by_field(self, queryset, field):
        from django.db.models import Count
        return dict(
            queryset.values(field).annotate(count=Count('id')).values_list(field, 'count')
        )
    
    def _get_top_voted(self, queryset, request, limit=10):
        top = queryset.order_by('-vote_count')[:limit]
        from .serializers import FeedbackListSerializer
        return FeedbackListSerializer(top, many=True, context={'request': request}).data
    
    def _get_recent(self, queryset, request, limit=10):
        recent = queryset.order_by('-created_at')[:limit]
        from .serializers import FeedbackListSerializer
        return FeedbackListSerializer(recent, many=True, context={'request': request}).data
    
    def _get_daily_trend(self, queryset, days=30):
        from django.db.models.functions import TruncDate
        from django.db.models import Count
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        trend = queryset.filter(
            created_at__date__gte=start_date
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        return list(trend)


# Attachment Views
@extend_schema_view(
    create=extend_schema(
        tags=['Feedback System'],
        summary='Upload attachment',
        description='Upload a file attachment for feedback.',
        request={'multipart/form-data': {'type': 'object', 'properties': {'file': {'type': 'string', 'format': 'binary'}}}},
        responses={
            201: OpenApiResponse(description='Attachment uploaded'),
            400: OpenApiResponse(description='Invalid file'),
            413: OpenApiResponse(description='File too large'),
            415: OpenApiResponse(description='Unsupported file type')
        }
    ),
    list=extend_schema(
        tags=['Feedback System'],
        summary='List attachments',
        description='Get all attachments for a feedback.',
        responses={
            200: OpenApiResponse(description='List of attachments')
        }
    ),
    destroy=extend_schema(
        tags=['Feedback System'],
        summary='Delete attachment',
        description='Delete an attachment.',
        responses={
            204: OpenApiResponse(description='Attachment deleted'),
            403: OpenApiResponse(description='Permission denied'),
            404: OpenApiResponse(description='Attachment not found')
        }
    )
)
class FeedbackAttachmentViewSet(TenantModelViewSet):
    """
    ViewSet for feedback attachments
    
    继承TenantModelViewSet自动处理租户过滤、设置和验证
    """
    serializer_class = FeedbackAttachmentSerializer
    parser_classes = (MultiPartParser, FormParser)
    
    def get_queryset(self):
        # 先获取租户过滤的queryset
        queryset = super().get_queryset()
        
        # 然后按feedback_id过滤
        feedback_id = self.kwargs.get('feedback_pk')
        return queryset.filter(
            feedback_id=feedback_id
        )


# Email Template Views
@extend_schema_view(
    list=extend_schema(
        tags=['Feedback System'],
        summary='List email templates',
        description='Get all email templates for the tenant.',
        responses={
            200: OpenApiResponse(description='List of email templates')
        }
    ),
    create=extend_schema(
        tags=['Feedback System'],
        summary='Create email template',
        description='Create a new email template. Only tenant administrators can perform this action.',
        responses={
            201: OpenApiResponse(description='Template created'),
            400: OpenApiResponse(description='Invalid input'),
            403: OpenApiResponse(description='Permission denied')
        }
    ),
    update=extend_schema(
        tags=['Feedback System'],
        summary='Update email template',
        description='Update an email template. Only tenant administrators can perform this action.',
        responses={
            200: OpenApiResponse(description='Template updated'),
            403: OpenApiResponse(description='Permission denied'),
            404: OpenApiResponse(description='Template not found')
        }
    ),
    destroy=extend_schema(
        tags=['Feedback System'],
        summary='Delete email template',
        description='Delete an email template. Only tenant administrators can perform this action.',
        responses={
            204: OpenApiResponse(description='Template deleted'),
            403: OpenApiResponse(description='Permission denied'),
            404: OpenApiResponse(description='Template not found')
        }
    )
)
class EmailTemplateViewSet(TenantModelViewSet):
    """
    ViewSet for email templates
    
    继承TenantModelViewSet自动处理租户过滤、设置和验证
    """
    queryset = EmailTemplate.objects.all()
    serializer_class = EmailTemplateSerializer
    permission_classes = [EmailTemplatePermission]
    
    def get_queryset(self):
        # TenantModelViewSet已经处理租户过滤
        queryset = super().get_queryset()
        return queryset


# Email Log Views
@extend_schema_view(
    list=extend_schema(
        tags=['Feedback System'],
        summary='List email logs',
        description='Get email sending history.',
        parameters=[
            OpenApiParameter(
                name='feedback',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                description='Filter by feedback ID'
            ),
            OpenApiParameter(
                name='status',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by email status',
                enum=['pending', 'sending', 'sent', 'failed', 'bounced']
            ),
            OpenApiParameter(
                name='email_type',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='Filter by email type',
                enum=['reply', 'status_change', 'verification', 'summary']
            ),
        ],
        responses={
            200: OpenApiResponse(description='List of email logs')
        }
    )
)
class EmailLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for email logs (read-only)"""
    queryset = FeedbackEmailLog.objects.all()
    serializer_class = FeedbackEmailLogSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        if hasattr(self.request, 'tenant'):
            queryset = queryset.filter(tenant=self.request.tenant)
        
        # Filter by parameters
        feedback_id = self.request.query_params.get('feedback')
        if feedback_id:
            queryset = queryset.filter(feedback_id=feedback_id)
        
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        email_type = self.request.query_params.get('email_type')
        if email_type:
            queryset = queryset.filter(email_type=email_type)
        
        return queryset.order_by('-created_at')
