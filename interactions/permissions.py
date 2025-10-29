"""
用户互动权限控制
"""
from rest_framework import permissions


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
