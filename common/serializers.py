"""
Common应用的序列化器
"""
from rest_framework import serializers
from common.models import APILog
from users.serializers import UserMinimalSerializer

class APILogSerializer(serializers.ModelSerializer):
    """
    API日志列表序列化器
    """
    user = UserMinimalSerializer(read_only=True)
    tenant_name = serializers.SerializerMethodField()
    
    class Meta:
        model = APILog
        fields = [
            'id', 'user', 'tenant_name', 'request_method', 'request_path',
            'status_code', 'response_time', 'status_type', 'created_at'
        ]
    
    def get_tenant_name(self, obj) -> str:
        """获取租户名称"""
        if obj.tenant:
            return obj.tenant.name
        return None


class APILogDetailSerializer(serializers.ModelSerializer):
    """
    API日志详情序列化器
    """
    user = UserMinimalSerializer(read_only=True)
    tenant_name = serializers.SerializerMethodField()
    
    class Meta:
        model = APILog
        fields = [
            'id', 'user', 'tenant_name', 'ip_address', 'request_method', 
            'request_path', 'query_params', 'request_body', 'status_code', 
            'response_time', 'status_type', 'error_message', 'user_agent',
            'created_at'
        ]
    
    def get_tenant_name(self, obj) -> str:
        """获取租户名称"""
        if obj.tenant:
            return obj.tenant.name
        return None