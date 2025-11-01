"""
用户互动权限控制
"""
from rest_framework import permissions
from users.models import Member


class ArticleFavoritePermission(permissions.BasePermission):
    """
    文章收藏权限类
    
    - 任何认证用户可以收藏文章
    - 用户只能管理自己的收藏
    """
    
    def has_permission(self, request, view):
        """
        检查用户是否有权限访问收藏API
        """
        # 所有操作都需要认证
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        """
        检查用户是否有权限操作specific收藏记录
        """
        # 用户只能删除自己的收藏
        return obj.user == request.user


class MemberLikePermission(permissions.BasePermission):
    """
    用户点赞权限类
    
    - 只有Member用户可以点赞
    - 用户只能管理自己发起的点赞
    """
    
    def has_permission(self, request, view):
        """
        检查用户是否有权限访问点赞API
        """
        # 需要认证且是Member用户
        return (
            request.user and 
            request.user.is_authenticated and 
            isinstance(request.user, Member)
        )
    
    def has_object_permission(self, request, view, obj):
        """
        检查用户是否有权限操作specific点赞记录
        """
        # 用户只能删除自己发起的点赞
        return obj.from_member == request.user


class MemberFollowPermission(permissions.BasePermission):
    """
    用户关注权限类
    
    - 只有Member用户可以关注
    - 用户只能管理自己发起的关注
    """
    
    def has_permission(self, request, view):
        """
        检查用户是否有权限访问关注API
        """
        # 需要认证且是Member用户
        return (
            request.user and 
            request.user.is_authenticated and 
            isinstance(request.user, Member)
        )
    
    def has_object_permission(self, request, view, obj):
        """
        检查用户是否有权限操作specific关注记录
        """
        # 用户只能删除自己发起的关注
        return obj.follower == request.user
