"""
User Feedback System Serializers

This module contains all serializers for the feedback management system,
providing data validation and transformation for API operations.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import (
    SoftwareCategory, Software, SoftwareVersion,
    Feedback, FeedbackReply, FeedbackStatusHistory,
    FeedbackAttachment, FeedbackVote,
    FeedbackEmailLog, EmailTemplate
)
import mimetypes
import os

User = get_user_model()


# ===================== Software Management Serializers =====================

class SoftwareCategorySerializer(serializers.ModelSerializer):
    """Serializer for Software Category"""
    software_count = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = SoftwareCategory
        fields = [
            'id', 'name', 'code', 'description', 'icon', 
            'sort_order', 'is_active', 'software_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'software_count']
        
    def get_software_count(self, obj):
        """Get count of active software in this category"""
        return obj.software_list.filter(is_active=True).count()
    
    def validate_code(self, value):
        """Ensure code is unique within tenant"""
        request = self.context.get('request')
        if request and hasattr(request, 'tenant'):
            queryset = SoftwareCategory.objects.filter(
                tenant=request.tenant,
                code=value
            )
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError(
                    _("Category with this code already exists in your tenant.")
                )
        return value


class SoftwareVersionSerializer(serializers.ModelSerializer):
    """Serializer for Software Version"""
    
    class Meta:
        model = SoftwareVersion
        fields = [
            'id', 'software', 'version', 'version_code', 'release_date',
            'release_notes', 'is_stable', 'is_active', 'download_url',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
        
    def validate(self, attrs):
        """Ensure version is unique for the software"""
        software = attrs.get('software')
        version = attrs.get('version')
        
        if software and version:
            queryset = SoftwareVersion.objects.filter(
                software=software,
                version=version
            )
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError({
                    'version': _("This version already exists for the software.")
                })
        
        return attrs


class SoftwareListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for Software listing"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    version_count = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Software
        fields = [
            'id', 'name', 'code', 'description', 'category', 'category_name',
            'logo', 'current_version', 'status', 'is_active',
            'total_feedbacks', 'open_feedbacks', 'version_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'total_feedbacks', 'open_feedbacks', 
            'version_count', 'created_at', 'updated_at'
        ]
        
    def get_version_count(self, obj):
        """Get count of versions for this software"""
        return obj.versions.count()


class SoftwareDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Software with nested data"""
    category = SoftwareCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=SoftwareCategory.objects.all(),
        source='category',
        write_only=True,
        required=False
    )
    versions = SoftwareVersionSerializer(many=True, read_only=True)
    latest_stable_version = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Software
        fields = [
            'id', 'name', 'code', 'description', 'category', 'category_id',
            'logo', 'website', 'current_version', 'owner', 'team',
            'contact_email', 'tags', 'metadata', 'status', 'is_active',
            'total_feedbacks', 'open_feedbacks', 'versions',
            'latest_stable_version', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'total_feedbacks', 'open_feedbacks',
            'created_at', 'updated_at'
        ]
        
    def get_latest_stable_version(self, obj):
        """Get latest stable version"""
        version = obj.versions.filter(
            is_stable=True,
            is_active=True
        ).order_by('-version_code').first()
        
        if version:
            return SoftwareVersionSerializer(version).data
        return None
    
    def validate_code(self, value):
        """Ensure code is unique within tenant"""
        request = self.context.get('request')
        if request and hasattr(request, 'tenant'):
            queryset = Software.objects.filter(
                tenant=request.tenant,
                code=value
            )
            if self.instance:
                queryset = queryset.exclude(pk=self.instance.pk)
            if queryset.exists():
                raise serializers.ValidationError(
                    _("Software with this code already exists in your tenant.")
                )
        return value


# ===================== Feedback Management Serializers =====================

class FeedbackAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for Feedback Attachments"""
    file_url = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = FeedbackAttachment
        fields = [
            'id', 'file', 'file_url', 'filename', 'file_size',
            'mime_type', 'uploaded_by', 'created_at'
        ]
        read_only_fields = [
            'id', 'file_size', 'mime_type', 'uploaded_by', 'created_at'
        ]
        
    def get_file_url(self, obj):
        """Get full URL for the file"""
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None
    
    def validate_file(self, value):
        """Validate file size and type"""
        # Max file size: 10MB
        max_size = 10 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError(
                _("File size cannot exceed 10MB.")
            )
        return value
    
    def create(self, validated_data):
        """Set file metadata on creation"""
        file = validated_data.get('file')
        if file:
            validated_data['filename'] = file.name
            validated_data['file_size'] = file.size
            validated_data['mime_type'] = mimetypes.guess_type(file.name)[0]
        
        # Set uploaded_by from request
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['uploaded_by'] = request.user
            
        return super().create(validated_data)


class FeedbackReplySerializer(serializers.ModelSerializer):
    """Serializer for Feedback Replies"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = FeedbackReply
        fields = [
            'id', 'feedback', 'user', 'user_name', 'user_email',
            'content', 'is_internal_note', 'email_sent', 'email_sent_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'email_sent', 'email_sent_at',
            'created_at', 'updated_at'
        ]
        
    def validate_content(self, value):
        """Ensure content is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError(
                _("Reply content cannot be empty.")
            )
        return value
    
    def create(self, validated_data):
        """Set user from request"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        return super().create(validated_data)


class FeedbackStatusHistorySerializer(serializers.ModelSerializer):
    """Serializer for Feedback Status History"""
    changed_by_name = serializers.CharField(source='changed_by.username', read_only=True)
    from_status_display = serializers.CharField(source='get_from_status_display', read_only=True)
    to_status_display = serializers.CharField(source='get_to_status_display', read_only=True)
    
    class Meta:
        model = FeedbackStatusHistory
        fields = [
            'id', 'feedback', 'from_status', 'to_status',
            'from_status_display', 'to_status_display',
            'changed_by', 'changed_by_name', 'reason',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class FeedbackVoteSerializer(serializers.ModelSerializer):
    """Serializer for Feedback Votes"""
    user_name = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = FeedbackVote
        fields = [
            'id', 'feedback', 'user', 'user_name', 'vote_type',
            'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']
        
    def create(self, validated_data):
        """Set user from request"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        return super().create(validated_data)


class FeedbackListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for Feedback listing"""
    software_name = serializers.CharField(source='software.name', read_only=True)
    version_number = serializers.CharField(source='software_version.version', read_only=True)
    submitter = serializers.SerializerMethodField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type_display = serializers.CharField(source='get_feedback_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = Feedback
        fields = [
            'id', 'title', 'description', 'feedback_type', 'type_display',
            'priority', 'priority_display', 'status', 'status_display',
            'software', 'software_name', 'software_version', 'version_number',
            'submitter', 'contact_email', 'vote_count', 'reply_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'vote_count', 'reply_count', 'created_at', 'updated_at'
        ]
        
    def get_submitter(self, obj):
        """Get submitter information"""
        if obj.user:
            return {
                'id': obj.user.id,
                'username': obj.user.username,
                'email': obj.user.email
            }
        return {
            'name': obj.contact_name,
            'email': obj.contact_email
        }


class FeedbackCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Feedback"""
    attachments = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        write_only=True
    )
    
    class Meta:
        model = Feedback
        fields = [
            'title', 'description', 'feedback_type', 'priority',
            'software', 'software_version', 'contact_email', 'contact_name',
            'environment_info', 'attachments'
        ]
        
    def validate(self, attrs):
        """Validate feedback data"""
        # Check if user is authenticated or email is provided
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            if not attrs.get('contact_email'):
                raise serializers.ValidationError({
                    'contact_email': _("Email is required for anonymous feedback.")
                })
        
        # Validate software version belongs to software
        software = attrs.get('software')
        version = attrs.get('software_version')
        if version and version.software != software:
            raise serializers.ValidationError({
                'software_version': _("Version does not belong to selected software.")
            })
        
        return attrs
    
    def create(self, validated_data):
        """Create feedback with attachments"""
        attachments_data = validated_data.pop('attachments', [])
        
        # Set user if authenticated
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
            if not validated_data.get('contact_email'):
                validated_data['contact_email'] = request.user.email
        
        # Set IP and user agent
        if request:
            validated_data['ip_address'] = self.get_client_ip(request)
            validated_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
        
        # Create feedback
        feedback = super().create(validated_data)
        
        # Create attachments
        for file in attachments_data:
            FeedbackAttachment.objects.create(
                feedback=feedback,
                file=file,
                filename=file.name,
                file_size=file.size,
                mime_type=mimetypes.guess_type(file.name)[0],
                uploaded_by=request.user if request.user.is_authenticated else None
            )
        
        return feedback
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class FeedbackDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for Feedback with nested data"""
    software = SoftwareListSerializer(read_only=True)
    software_version = SoftwareVersionSerializer(read_only=True)
    user_info = serializers.SerializerMethodField(read_only=True)
    attachments = FeedbackAttachmentSerializer(many=True, read_only=True)
    replies = serializers.SerializerMethodField(read_only=True)
    status_history = FeedbackStatusHistorySerializer(many=True, read_only=True)
    user_vote = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Feedback
        fields = [
            'id', 'title', 'description', 'feedback_type', 'priority', 'status',
            'software', 'software_version', 'user', 'user_info',
            'contact_email', 'contact_name', 'email_verified',
            'email_notification_enabled', 'environment_info',
            'ip_address', 'user_agent', 'assigned_to', 'resolved_at',
            'resolution_notes', 'view_count', 'vote_count', 'reply_count',
            'attachments', 'replies', 'status_history', 'user_vote',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'email_verified', 'view_count', 'vote_count',
            'reply_count', 'created_at', 'updated_at'
        ]
        
    def get_user_info(self, obj):
        """Get submitter information"""
        if obj.user:
            return {
                'id': obj.user.id,
                'username': obj.user.username,
                'email': obj.user.email,
                'is_registered': True
            }
        return {
            'name': obj.contact_name,
            'email': obj.contact_email,
            'is_registered': False
        }
    
    def get_replies(self, obj):
        """Get non-internal replies"""
        request = self.context.get('request')
        if request and request.user.is_staff:
            # Staff can see all replies
            replies = obj.replies.all()
        else:
            # Others can only see non-internal replies
            replies = obj.replies.filter(is_internal_note=False)
        
        return FeedbackReplySerializer(replies, many=True, context=self.context).data
    
    def get_user_vote(self, obj):
        """Get current user's vote on this feedback"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            vote = obj.votes.filter(user=request.user).first()
            if vote:
                return vote.vote_type
        return None


class FeedbackUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating Feedback"""
    
    class Meta:
        model = Feedback
        fields = [
            'title', 'description', 'priority', 'status',
            'assigned_to', 'resolution_notes', 'email_notification_enabled'
        ]
        
    def validate_status(self, value):
        """Validate status transition"""
        if self.instance:
            current_status = self.instance.status
            
            # Define valid status transitions
            valid_transitions = {
                'submitted': ['reviewing', 'rejected', 'duplicate'],
                'reviewing': ['confirmed', 'rejected', 'duplicate'],
                'confirmed': ['in_progress', 'rejected', 'duplicate'],
                'in_progress': ['resolved', 'rejected'],
                'resolved': ['closed', 'in_progress'],
                'closed': ['submitted'],  # Can reopen
                'rejected': ['submitted'],  # Can reopen
                'duplicate': ['submitted'],  # Can reopen
            }
            
            if value not in valid_transitions.get(current_status, []):
                raise serializers.ValidationError(
                    _(f"Cannot change status from {current_status} to {value}.")
                )
        
        return value


# ===================== Email Management Serializers =====================

class FeedbackEmailLogSerializer(serializers.ModelSerializer):
    """Serializer for Email Logs"""
    email_type_display = serializers.CharField(source='get_email_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = FeedbackEmailLog
        fields = [
            'id', 'feedback', 'email_type', 'email_type_display',
            'recipient', 'subject', 'content', 'status', 'status_display',
            'sent_at', 'error_message', 'retry_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at'
        ]


class EmailTemplateSerializer(serializers.ModelSerializer):
    """Serializer for Email Templates"""
    template_type_display = serializers.CharField(source='get_template_type_display', read_only=True)
    
    class Meta:
        model = EmailTemplate
        fields = [
            'id', 'name', 'template_type', 'template_type_display',
            'subject', 'body_html', 'body_text', 'is_active',
            'variables', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at'
        ]
        
    def validate(self, attrs):
        """Ensure unique template per type and tenant"""
        name = attrs.get('name')
        template_type = attrs.get('template_type')
        
        if name and template_type:
            request = self.context.get('request')
            if request and hasattr(request, 'tenant'):
                queryset = EmailTemplate.objects.filter(
                    tenant=request.tenant,
                    template_type=template_type,
                    name=name
                )
                if self.instance:
                    queryset = queryset.exclude(pk=self.instance.pk)
                if queryset.exists():
                    raise serializers.ValidationError({
                        'name': _("Template with this name already exists for this type.")
                    })
        
        return attrs


# ===================== Statistics Serializers =====================

class FeedbackStatisticsSerializer(serializers.Serializer):
    """Serializer for Feedback Statistics"""
    total_feedbacks = serializers.IntegerField()
    open_feedbacks = serializers.IntegerField()
    resolved_feedbacks = serializers.IntegerField()
    avg_resolution_time = serializers.DurationField()
    
    feedbacks_by_type = serializers.DictField()
    feedbacks_by_status = serializers.DictField()
    feedbacks_by_priority = serializers.DictField()
    
    top_voted_feedbacks = FeedbackListSerializer(many=True)
    recent_feedbacks = FeedbackListSerializer(many=True)
    
    daily_trend = serializers.ListField(
        child=serializers.DictField()
    )
