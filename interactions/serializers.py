"""
用户互动序列化器
"""
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from .models import ArticleFavorite, MemberLike, MemberFollow, ArticleLike
from cms.serializers import ArticleListSerializer
from users.models import Member
from common.utils.image_url import add_domain_to_image_url


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
    
    @extend_schema_field(serializers.DictField())
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


class MemberLikeSerializer(serializers.ModelSerializer):
    """用户点赞序列化器"""
    
    from_member_info = serializers.SerializerMethodField()
    to_member_info = serializers.SerializerMethodField()
    
    class Meta:
        model = MemberLike
        fields = [
            'id', 'from_member', 'to_member', 'from_member_info',
            'to_member_info', 'tenant', 'created_at'
        ]
        read_only_fields = ['id', 'from_member', 'tenant', 'created_at']
    
    @extend_schema_field(serializers.DictField())
    def get_from_member_info(self, obj):
        """获取点赞发起者信息"""
        request = self.context.get('request')
        avatar_url = add_domain_to_image_url(request, obj.from_member.avatar) if obj.from_member.avatar and request else (obj.from_member.avatar or '')
        return {
            'id': obj.from_member.id,
            'username': obj.from_member.username,
            'nick_name': obj.from_member.nick_name,
            'avatar': avatar_url
        }
    
    @extend_schema_field(serializers.DictField())
    def get_to_member_info(self, obj):
        """获取被点赞用户信息"""
        request = self.context.get('request')
        avatar_url = add_domain_to_image_url(request, obj.to_member.avatar) if obj.to_member.avatar and request else (obj.to_member.avatar or '')
        return {
            'id': obj.to_member.id,
            'username': obj.to_member.username,
            'nick_name': obj.to_member.nick_name,
            'avatar': avatar_url
        }


class MemberLikeCreateSerializer(serializers.ModelSerializer):
    """用户点赞创建序列化器"""
    
    class Meta:
        model = MemberLike
        fields = ['to_member']
    
    def validate_to_member(self, value):
        """验证被点赞用户是否存在且可访问"""
        request = self.context.get('request')
        from_member = request.user
        
        # 检查用户类型
        if not isinstance(from_member, Member):
            raise serializers.ValidationError("只有Member用户可以点赞")
        
        # 检查是否点赞自己
        if value.id == from_member.id:
            raise serializers.ValidationError("不能点赞自己")
        
        # 检查被点赞用户是否属于当前租户
        if value.tenant_id != from_member.tenant_id:
            raise serializers.ValidationError("您无法点赞其他租户的用户")
        
        # 检查是否已经点赞
        if MemberLike.objects.filter(from_member=from_member, to_member=value).exists():
            raise serializers.ValidationError("您已经点赞过该用户")
        
        return value


class MemberFollowSerializer(serializers.ModelSerializer):
    """用户关注序列化器"""
    
    follower_info = serializers.SerializerMethodField()
    following_info = serializers.SerializerMethodField()
    is_mutual = serializers.SerializerMethodField()
    
    class Meta:
        model = MemberFollow
        fields = [
            'id', 'follower', 'following', 'follower_info',
            'following_info', 'is_mutual', 'tenant', 'created_at'
        ]
        read_only_fields = ['id', 'follower', 'tenant', 'created_at']
    
    @extend_schema_field(serializers.DictField())
    def get_follower_info(self, obj):
        """获取关注者信息"""
        request = self.context.get('request')
        avatar_url = add_domain_to_image_url(request, obj.follower.avatar) if obj.follower.avatar and request else (obj.follower.avatar or '')
        return {
            'id': obj.follower.id,
            'username': obj.follower.username,
            'nick_name': obj.follower.nick_name,
            'avatar': avatar_url
        }
    
    @extend_schema_field(serializers.DictField())
    def get_following_info(self, obj):
        """获取被关注者信息"""
        request = self.context.get('request')
        avatar_url = add_domain_to_image_url(request, obj.following.avatar) if obj.following.avatar and request else (obj.following.avatar or '')
        return {
            'id': obj.following.id,
            'username': obj.following.username,
            'nick_name': obj.following.nick_name,
            'avatar': avatar_url
        }
    
    @extend_schema_field(serializers.BooleanField())
    def get_is_mutual(self, obj):
        """检查是否互相关注"""
        return obj.is_mutual()


class MemberFollowCreateSerializer(serializers.ModelSerializer):
    """用户关注创建序列化器"""
    
    class Meta:
        model = MemberFollow
        fields = ['following']
    
    def validate_following(self, value):
        """验证被关注用户是否存在且可访问"""
        request = self.context.get('request')
        follower = request.user
        
        # 检查用户类型
        if not isinstance(follower, Member):
            raise serializers.ValidationError("只有Member用户可以关注")
        
        # 检查是否关注自己
        if value.id == follower.id:
            raise serializers.ValidationError("不能关注自己")
        
        # 检查被关注用户是否属于当前租户
        if value.tenant_id != follower.tenant_id:
            raise serializers.ValidationError("您无法关注其他租户的用户")
        
        # 检查是否已经关注
        if MemberFollow.objects.filter(follower=follower, following=value).exists():
            raise serializers.ValidationError("您已经关注过该用户")
        
        return value


class ArticleLikeSerializer(serializers.ModelSerializer):
    """文章点赞序列化器"""
    
    article_detail = ArticleListSerializer(source='article', read_only=True)
    from_member_info = serializers.SerializerMethodField()
    
    class Meta:
        model = ArticleLike
        fields = [
            'id', 'from_member', 'article', 'article_detail',
            'from_member_info', 'tenant', 'created_at',
            'ip_address', 'user_agent'
        ]
        read_only_fields = ['id', 'from_member', 'tenant', 'created_at', 'ip_address', 'user_agent']
    
    @extend_schema_field(serializers.DictField())
    def get_from_member_info(self, obj):
        """获取点赞发起者信息"""
        request = self.context.get('request')
        avatar_url = add_domain_to_image_url(request, obj.from_member.avatar) if obj.from_member.avatar and request else (obj.from_member.avatar or '')
        return {
            'id': obj.from_member.id,
            'username': obj.from_member.username,
            'nick_name': obj.from_member.nick_name,
            'avatar': avatar_url
        }


class ArticleLikeCreateSerializer(serializers.ModelSerializer):
    """文章点赞创建序列化器"""
    
    class Meta:
        model = ArticleLike
        fields = ['article']
    
    def validate_article(self, value):
        """验证文章是否存在且可访问"""
        request = self.context.get('request')
        from_member = request.user
        
        # 检查用户类型
        if not isinstance(from_member, Member):
            raise serializers.ValidationError("只有Member用户可以点赞文章")
        
        # 检查文章是否属于当前租户
        if value.tenant_id != from_member.tenant_id:
            raise serializers.ValidationError("您无法点赞其他租户的文章")
        
        # 检查是否已经点赞
        if ArticleLike.objects.filter(from_member=from_member, article=value).exists():
            raise serializers.ValidationError("您已经点赞过这篇文章")
        
        return value
