"""
应用管理序列化器
"""
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import Application


class ApplicationListSerializer(serializers.ModelSerializer):
    """应用列表序列化器（简化）"""
    
    class Meta:
        model = Application
        fields = [
            'id', 'name', 'code', 'description', 'logo',
            'current_version', 'status', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ApplicationDetailSerializer(serializers.ModelSerializer):
    """应用详情序列化器（完整）"""
    license_count = serializers.SerializerMethodField()
    feedback_count = serializers.SerializerMethodField()
    article_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Application
        fields = [
            'id', 'name', 'code', 'description', 'logo', 'website',
            'contact_email', 'current_version', 'owner', 'team',
            'status', 'is_active', 'tags', 'metadata',
            'license_count', 'feedback_count', 'article_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    @extend_schema_field(serializers.IntegerField)
    def get_license_count(self, obj):
        return obj.get_license_count()
    
    @extend_schema_field(serializers.IntegerField)
    def get_feedback_count(self, obj):
        return obj.get_feedback_count()
    
    @extend_schema_field(serializers.IntegerField)
    def get_article_count(self, obj):
        return obj.get_article_count()


class ApplicationCreateSerializer(serializers.ModelSerializer):
    """应用创建序列化器"""
    
    class Meta:
        model = Application
        fields = [
            'name', 'code', 'description', 'logo', 'website',
            'contact_email', 'current_version', 'owner', 'team',
            'status', 'is_active', 'tags', 'metadata'
        ]
    
    def validate_code(self, value):
        """验证应用代码唯一性（租户内）"""
        request = self.context.get('request')
        if request and hasattr(request, 'tenant'):
            if Application.objects.filter(
                tenant=request.tenant,
                code=value
            ).exists():
                raise serializers.ValidationError(
                    f"应用代码 '{value}' 在当前租户下已存在"
                )
        return value


class ApplicationStatisticsSerializer(serializers.Serializer):
    """应用统计信息序列化器"""
    licenses = serializers.DictField()
    feedbacks = serializers.DictField()
    articles = serializers.DictField()
