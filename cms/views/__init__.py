"""
CMS系统视图模块

将大型views.py拆分为模块化结构，通过__init__.py保持向后兼容性
"""

# 从base_views导入所有ViewSet，保持向后兼容
from .base_views import (
    ArticleViewSet,
    CategoryViewSet,
    TagViewSet,
    TagGroupViewSet,
    CommentViewSet,
)

# 导出所有公共ViewSet
__all__ = [
    'ArticleViewSet',
    'CategoryViewSet',
    'TagViewSet',
    'TagGroupViewSet',
    'CommentViewSet',
]
