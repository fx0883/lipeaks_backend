"""
User Feedback System Serializers

This module contains all serializers for the feedback management system,
providing data validation and transformation for API operations.
"""

from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import (
    Feedback, FeedbackReply, FeedbackStatusHistory,
    FeedbackAttachment, FeedbackVote,
    FeedbackEmailLog, EmailTemplate,
    FeedbackNotificationConfig, FeedbackNotificationRecipient
)
from applications.models import Application
from applications.serializers import ApplicationListSerializer
import mimetypes
import os

User = get_user_model()


# ===================== Application Management Serializers =====================
# Application相关序列化器已废弃，现在使用applications模块
# 请使用 applications.serializers 中的序列化器

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
            'id', 'filename', 'file_size', 'mime_type', 'uploaded_by', 'created_at'
        ]
        
    @extend_schema_field(serializers.CharField(allow_null=True))
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
            'id', 'feedback', 'user', 'email_sent', 'email_sent_at',
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


class FeedbackReplyCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating Feedback Replies (without feedback field)"""
    
    class Meta:
        model = FeedbackReply
        fields = [
            'content', 'is_internal_note'
        ]
        
    def validate_content(self, value):
        """Ensure content is not empty"""
        if not value or not value.strip():
            raise serializers.ValidationError(
                _("Reply content cannot be empty.")
            )
        return value


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
    application_name = serializers.CharField(source='application.name', read_only=True)
    submitter = serializers.SerializerMethodField(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    type_display = serializers.CharField(source='get_feedback_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = Feedback
        fields = [
            'id', 'title', 'description', 'feedback_type', 'type_display',
            'priority', 'priority_display', 'status', 'status_display',
            'application', 'application_name',
            'submitter', 'contact_email', 'vote_count', 'reply_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'vote_count', 'reply_count', 'created_at', 'updated_at'
        ]
        
    @extend_schema_field(serializers.DictField())
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
    contact_email = serializers.EmailField(
        required=False,
        allow_blank=True,
        help_text="Email for replies (required for anonymous users)"
    )
    
    class Meta:
        model = Feedback
        fields = [
            'title', 'description', 'feedback_type', 'priority',
            'application', 'contact_email', 'contact_name',
            'environment_info', 'attachments'
        ]
    
    def create(self, validated_data):
        """Create feedback with attachments"""
        attachments_data = validated_data.pop('attachments', [])
        
        # Set user if authenticated
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # ✅ 只有User类型才设置user字段，Member类型不设置
            # 通过表名判断用户类型
            user_table_name = request.user._meta.db_table
            if user_table_name == 'user':  # User模型
                validated_data['user'] = request.user
            # else: Member或其他类型，不设置user字段（保持None）
            
            # ✅ 对于已登录用户，如果没有提供contact_email，尝试从用户获取
            if not validated_data.get('contact_email'):
                user_email = getattr(request.user, 'email', None)
                if user_email and user_email.strip():  # 检查email不为空
                    validated_data['contact_email'] = user_email
                # 如果用户没有email，contact_email保持为None（已登录用户可选）
            
            # ✅ 如果没有提供contact_name，使用用户名
            if not validated_data.get('contact_name'):
                validated_data['contact_name'] = request.user.username
        
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
                uploaded_by=request.user if request.user.is_authenticated else None,
                tenant=feedback.tenant
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
    application = ApplicationListSerializer(read_only=True)
    user_info = serializers.SerializerMethodField(read_only=True)
    attachments = FeedbackAttachmentSerializer(many=True, read_only=True)
    replies = serializers.SerializerMethodField(read_only=True)
    status_history = FeedbackStatusHistorySerializer(many=True, read_only=True)
    user_vote = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Feedback
        fields = [
            'id', 'title', 'description', 'feedback_type', 'priority', 'status',
            'application', 'user', 'user_info',
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
        
    @extend_schema_field(serializers.DictField())
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
    
    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
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
    
    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_user_vote(self, obj):
        """Get current user's vote on this feedback"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # ✅ 只有User类型可以投票，Member类型返回None
            user_table_name = request.user._meta.db_table
            if user_table_name == 'user':
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


# ===================== Notification Configuration Serializers =====================

class FeedbackNotificationRecipientSerializer(serializers.ModelSerializer):
    """反馈通知接收者序列化器"""
    
    class Meta:
        model = FeedbackNotificationRecipient
        fields = [
            'id', 'email', 'name', 'is_active', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class FeedbackNotificationRecipientCreateSerializer(serializers.ModelSerializer):
    """创建反馈通知接收者序列化器"""
    
    class Meta:
        model = FeedbackNotificationRecipient
        fields = ['email', 'name', 'is_active']
    
    def validate_email(self, value):
        """验证邮箱格式并检查重复"""
        config = self.context.get('config')
        if config:
            if FeedbackNotificationRecipient.objects.filter(
                config=config, 
                email=value,
                is_deleted=False
            ).exists():
                raise serializers.ValidationError(_("该邮箱已在接收列表中"))
        return value


class FeedbackNotificationConfigSerializer(serializers.ModelSerializer):
    """反馈通知配置序列化器"""
    recipients = FeedbackNotificationRecipientSerializer(many=True, read_only=True)
    recipient_count = serializers.SerializerMethodField()
    active_recipient_count = serializers.SerializerMethodField()
    application_name = serializers.CharField(source='application.name', read_only=True)
    application_code = serializers.CharField(source='application.code', read_only=True)
    
    class Meta:
        model = FeedbackNotificationConfig
        fields = [
            'id', 'application', 'application_name', 'application_code',
            'is_enabled', 'recipients', 'recipient_count', 'active_recipient_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    @extend_schema_field(serializers.IntegerField())
    def get_recipient_count(self, obj):
        """获取接收者总数"""
        return obj.recipients.filter(is_deleted=False).count()
    
    @extend_schema_field(serializers.IntegerField())
    def get_active_recipient_count(self, obj):
        """获取活跃接收者数量"""
        return obj.get_active_recipients().count()


class FeedbackNotificationConfigCreateSerializer(serializers.ModelSerializer):
    """创建反馈通知配置序列化器"""
    
    class Meta:
        model = FeedbackNotificationConfig
        fields = ['application', 'is_enabled']
    
    def validate_application(self, value):
        """验证应用归属和唯一性"""
        request = self.context.get('request')
        if request and hasattr(request, 'tenant'):
            # 检查应用是否属于当前租户
            if value.tenant_id != request.tenant.id:
                raise serializers.ValidationError(_("应用不属于当前租户"))
            
            # 检查是否已存在配置
            if FeedbackNotificationConfig.objects.filter(
                application=value,
                is_deleted=False
            ).exists():
                raise serializers.ValidationError(_("该应用已有通知配置"))
        return value


class FeedbackNotificationConfigUpdateSerializer(serializers.ModelSerializer):
    """更新反馈通知配置序列化器"""
    
    class Meta:
        model = FeedbackNotificationConfig
        fields = ['is_enabled']


class NotificationTestSerializer(serializers.Serializer):
    """测试邮件发送序列化器"""
    email = serializers.EmailField(help_text="测试邮件接收地址")
