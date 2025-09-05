"""
用户权限检查工具模块
统一处理 User 和 Member 模型的权限判断，避免属性访问错误
"""

def is_super_admin(user):
    """
    检查用户是否为超级管理员
    
    Args:
        user: User 或 Member 实例
        
    Returns:
        bool: 是否为超级管理员
    """
    # Member 永远不是超级管理员
    if hasattr(user, '_meta') and user._meta.model_name == 'member':
        return False
    
    # User 检查 is_super_admin 属性
    return getattr(user, 'is_super_admin', False)


def is_admin(user):
    """
    检查用户是否为管理员（包括超级管理员和租户管理员）
    
    Args:
        user: User 或 Member 实例
        
    Returns:
        bool: 是否为管理员
    """
    # Member 永远不是管理员
    if hasattr(user, '_meta') and user._meta.model_name == 'member':
        return False
    
    # User 检查 is_admin 属性
    return getattr(user, 'is_admin', False)


def is_tenant_admin(user):
    """
    检查用户是否为租户管理员（非超级管理员的管理员）
    
    Args:
        user: User 或 Member 实例
        
    Returns:
        bool: 是否为租户管理员
    """
    return is_admin(user) and not is_super_admin(user)


def is_member(user):
    """
    检查用户是否为普通成员
    
    Args:
        user: User 或 Member 实例
        
    Returns:
        bool: 是否为普通成员
    """
    return hasattr(user, '_meta') and user._meta.model_name == 'member'


def can_create_content(user):
    """
    检查用户是否可以创建内容
    Member 只有只读权限，不能创建内容
    
    Args:
        user: User 或 Member 实例
        
    Returns:
        bool: 是否可以创建内容
    """
    return is_admin(user)


def can_edit_content(user, content_author=None):
    """
    检查用户是否可以编辑内容
    
    Args:
        user: User 或 Member 实例
        content_author: 内容作者，用于判断是否为作者本人
        
    Returns:
        bool: 是否可以编辑内容
    """
    if is_member(user):
        return False
    
    if is_super_admin(user):
        return True
    
    if is_admin(user):
        return True
    
    # 如果提供了作者信息，检查是否为作者本人
    if content_author and hasattr(user, 'id'):
        return user.id == getattr(content_author, 'id', content_author)
    
    return False


def can_delete_content(user, content_author=None):
    """
    检查用户是否可以删除内容
    
    Args:
        user: User 或 Member 实例
        content_author: 内容作者，用于判断是否为作者本人
        
    Returns:
        bool: 是否可以删除内容
    """
    if is_member(user):
        return False
    
    if is_super_admin(user):
        return True
    
    if is_admin(user):
        return True
    
    # 如果提供了作者信息，检查是否为作者本人
    if content_author and hasattr(user, 'id'):
        return user.id == getattr(content_author, 'id', content_author)
    
    return False


def can_moderate_comments(user, article_author=None):
    """
    检查用户是否可以审核评论
    
    Args:
        user: User 或 Member 实例
        article_author: 文章作者，文章作者可以审核自己文章下的评论
        
    Returns:
        bool: 是否可以审核评论
    """
    if is_member(user):
        return False
    
    if is_super_admin(user) or is_admin(user):
        return True
    
    # 文章作者可以审核自己文章下的评论
    if article_author and hasattr(user, 'id'):
        return user.id == getattr(article_author, 'id', article_author)
    
    return False


def get_user_display_role(user):
    """
    获取用户角色显示名称
    
    Args:
        user: User 或 Member 实例
        
    Returns:
        str: 角色显示名称
    """
    if is_super_admin(user):
        return "超级管理员"
    elif is_admin(user):
        return "租户管理员"
    elif is_member(user):
        if hasattr(user, 'is_sub_account') and user.is_sub_account:
            return "子账号"
        return "普通成员"
    else:
        return "未知角色"


def get_user_type(user):
    """
    获取用户类型
    
    Args:
        user: User 或 Member 实例
        
    Returns:
        str: 'user' 或 'member'
    """
    if hasattr(user, '_meta'):
        return user._meta.model_name
    return 'unknown'


def filter_queryset_by_user_permissions(queryset, user, tenant_field='tenant'):
    """
    根据用户权限过滤查询集
    
    Args:
        queryset: Django QuerySet
        user: User 或 Member 实例
        tenant_field: 租户字段名，默认为 'tenant'
        
    Returns:
        QuerySet: 过滤后的查询集
    """
    if not user.is_authenticated:
        return queryset.none()
    
    if is_super_admin(user):
        # 超级管理员可以看到所有数据
        return queryset
    
    # 其他用户只能看到自己租户的数据
    if hasattr(user, 'tenant') and user.tenant:
        filter_dict = {tenant_field: user.tenant}
        return queryset.filter(**filter_dict)
    
    return queryset.none()
