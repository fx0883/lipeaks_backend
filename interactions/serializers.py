"""
用户互动序列化器
"""
from rest_framework import serializers
from .models import ArticleFavorite
from cms.serializers import ArticleListSerializer


class ArticleFavoriteSerializer(serializers.ModelSerializer):
    """文章收藏序列化器"""
    
    article_detail = ArticleListSerializer(source='article', read_only=True)
    user_info = serializers.SerializerMethodField()
    
    class Meta:
        model = ArticleFavorite
        fields = [
            'id', 'user', 'article', 'article_detail',
            'user_info', 'tenant', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'tenant', 'created_at']
    
    def get_user_info(self, obj):
        """获取用户信息"""
        return {
            'id': obj.user.id,
            'username': obj.user.username
        }


class ArticleFavoriteCreateSerializer(serializers.ModelSerializer):
    """文章收藏创建序列化器"""
    
    class Meta:
        model = ArticleFavorite
        fields = ['article']
    
    def validate_article(self, value):
        """验证文章是否存在且可访问"""
        user = self.context['request'].user
        
        # 检查文章是否属于当前租户
        if value.tenant_id != user.tenant_id:
            raise serializers.ValidationError("您无法收藏其他租户的文章")
        
        # 检查是否已经收藏
        if ArticleFavorite.objects.filter(user=user, article=value).exists():
            raise serializers.ValidationError("您已经收藏过这篇文章")
        
        return value
