"""
通知系统序列化器
"""
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import Notification, NotificationRecipient


# ==================== 管理端序列化器 ====================

class NotificationListSerializer(serializers.ModelSerializer):
    """通知列表序列化器"""
    scope_display = serializers.CharField(source='get_scope_display', read_only=True)
    type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    application_name = serializers.CharField(source='application.name', read_only=True, allow_null=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    recipient_count = serializers.SerializerMethodField()
    read_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'scope', 'scope_display',
            'application', 'application_name',
            'notification_type', 'type_display',
            'priority', 'priority_display',
            'status', 'status_display',
            'send_email', 'email_sent_at',
            'published_at',
            'created_by', 'created_by_name',
            'recipient_count', 'read_count',
            'created_at', 'updated_at'
        ]
    
    def get_recipient_count(self, obj):
        return obj.get_recipient_count()
    
    def get_read_count(self, obj):
        return obj.get_read_count()


class NotificationDetailSerializer(serializers.ModelSerializer):
    """通知详情序列化器"""
    scope_display = serializers.CharField(source='get_scope_display', read_only=True)
    type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    application_name = serializers.CharField(source='application.name', read_only=True, allow_null=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True, allow_null=True)
    recipient_count = serializers.SerializerMethodField()
    read_count = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'content',
            'scope', 'scope_display',
            'application', 'application_name',
            'notification_type', 'type_display',
            'priority', 'priority_display',
            'status', 'status_display',
            'send_email', 'email_sent_at',
            'published_at',
            'created_by', 'created_by_name',
            'recipient_count', 'read_count', 'unread_count',
            'tenant',
            'created_at', 'updated_at'
        ]
    
    def get_recipient_count(self, obj):
        return obj.get_recipient_count()
    
    def get_read_count(self, obj):
        return obj.get_read_count()
    
    def get_unread_count(self, obj):
        return obj.get_unread_count()


class NotificationCreateSerializer(serializers.ModelSerializer):
    """通知创建序列化器"""
    
    class Meta:
        model = Notification
        fields = [
            'title', 'content',
            'scope', 'application',
            'notification_type', 'priority',
            'send_email'
        ]
    
    def validate(self, attrs):
        """验证数据"""
        scope = attrs.get('scope', 'tenant')
        application = attrs.get('application')
        
        # scope=application 时，application 必填
        if scope == 'application' and not application:
            raise serializers.ValidationError({
                'application': _('当通知范围为"面向应用"时，必须选择一个应用')
            })
        
        # scope 不是 application 时，application 必须为空
        if scope != 'application' and application:
            raise serializers.ValidationError({
                'application': _('当通知范围不是"面向应用"时，不能选择应用')
            })
        
        return attrs
    
    def create(self, validated_data):
        """创建通知"""
        # 从 context 获取 request
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['created_by'] = request.user
        
        return super().create(validated_data)


class NotificationUpdateSerializer(serializers.ModelSerializer):
    """通知更新序列化器"""
    
    class Meta:
        model = Notification
        fields = [
            'title', 'content',
            'scope', 'application',
            'notification_type', 'priority',
            'send_email'
        ]
    
    def validate(self, attrs):
        """验证数据"""
        # 只有草稿状态可以编辑
        if self.instance and self.instance.status != 'draft':
            raise serializers.ValidationError(_('只有草稿状态的通知可以编辑'))
        
        scope = attrs.get('scope', self.instance.scope if self.instance else 'tenant')
        application = attrs.get('application', self.instance.application if self.instance else None)
        
        # scope=application 时，application 必填
        if scope == 'application' and not application:
            raise serializers.ValidationError({
                'application': _('当通知范围为"面向应用"时，必须选择一个应用')
            })
        
        # scope 不是 application 时，application 必须为空
        if scope != 'application' and application:
            attrs['application'] = None
        
        return attrs


class RecipientAddSerializer(serializers.Serializer):
    """添加接收者序列化器"""
    member_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        help_text="成员ID列表"
    )


class RecipientRemoveSerializer(serializers.Serializer):
    """移除接收者序列化器"""
    member_ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1,
        help_text="成员ID列表"
    )


class NotificationRecipientSerializer(serializers.ModelSerializer):
    """通知接收者序列化器"""
    member_username = serializers.CharField(source='member.username', read_only=True)
    member_email = serializers.CharField(source='member.email', read_only=True)
    
    class Meta:
        model = NotificationRecipient
        fields = [
            'id', 'member', 'member_username', 'member_email',
            'is_read', 'read_at', 'created_at'
        ]


class NotificationStatisticsSerializer(serializers.Serializer):
    """通知统计序列化器"""
    total_recipients = serializers.IntegerField()
    read_count = serializers.IntegerField()
    unread_count = serializers.IntegerField()
    read_rate = serializers.FloatField()


# ==================== 成员端序列化器 ====================

class MemberNotificationListSerializer(serializers.ModelSerializer):
    """成员端通知列表序列化器"""
    scope_display = serializers.CharField(source='notification.get_scope_display', read_only=True)
    type_display = serializers.CharField(source='notification.get_notification_type_display', read_only=True)
    priority_display = serializers.CharField(source='notification.get_priority_display', read_only=True)
    application_name = serializers.CharField(source='notification.application.name', read_only=True, allow_null=True)
    
    # 通知内容字段
    notification_id = serializers.IntegerField(source='notification.id', read_only=True)
    title = serializers.CharField(source='notification.title', read_only=True)
    notification_type = serializers.CharField(source='notification.notification_type', read_only=True)
    priority = serializers.CharField(source='notification.priority', read_only=True)
    scope = serializers.CharField(source='notification.scope', read_only=True)
    application = serializers.IntegerField(source='notification.application_id', read_only=True, allow_null=True)
    published_at = serializers.DateTimeField(source='notification.published_at', read_only=True)
    
    class Meta:
        model = NotificationRecipient
        fields = [
            'id', 'notification_id',
            'title', 'scope', 'scope_display',
            'application', 'application_name',
            'notification_type', 'type_display',
            'priority', 'priority_display',
            'published_at',
            'is_read', 'read_at',
            'created_at'
        ]


class MemberNotificationDetailSerializer(serializers.ModelSerializer):
    """成员端通知详情序列化器"""
    scope_display = serializers.CharField(source='notification.get_scope_display', read_only=True)
    type_display = serializers.CharField(source='notification.get_notification_type_display', read_only=True)
    priority_display = serializers.CharField(source='notification.get_priority_display', read_only=True)
    application_name = serializers.CharField(source='notification.application.name', read_only=True, allow_null=True)
    
    # 通知内容字段
    notification_id = serializers.IntegerField(source='notification.id', read_only=True)
    title = serializers.CharField(source='notification.title', read_only=True)
    content = serializers.CharField(source='notification.content', read_only=True)
    notification_type = serializers.CharField(source='notification.notification_type', read_only=True)
    priority = serializers.CharField(source='notification.priority', read_only=True)
    scope = serializers.CharField(source='notification.scope', read_only=True)
    application = serializers.IntegerField(source='notification.application_id', read_only=True, allow_null=True)
    published_at = serializers.DateTimeField(source='notification.published_at', read_only=True)
    
    class Meta:
        model = NotificationRecipient
        fields = [
            'id', 'notification_id',
            'title', 'content',
            'scope', 'scope_display',
            'application', 'application_name',
            'notification_type', 'type_display',
            'priority', 'priority_display',
            'published_at',
            'is_read', 'read_at',
            'created_at'
        ]


class UnreadCountSerializer(serializers.Serializer):
    """未读数量序列化器"""
    unread_count = serializers.IntegerField()
