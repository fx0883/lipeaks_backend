"""
用户视图包
"""
# 从auth_views.py导入身份验证相关视图
from .auth_views import (
    LoginView,
    TokenRefreshView,
    TokenVerifyView,
    RegisterView
)

# 从user_views.py导入用户相关视图
from .user_views import (
    UserRoleUpdateView
)

# 从admin_user_views.py导入管理员用户相关视图
from .admin_user_views import (
    CurrentAdminUserView,
    AdminUserListCreateView,
    AdminUserRetrieveUpdateDeleteView,
    GrantSuperAdminView,
    RevokeSuperAdminView,
    AdminPasswordUpdateView,
    SuperAdminCreateView,
    AdminUserAvatarUploadView,
    AdminUserSpecificAvatarUploadView
)

# 从member_views.py导入Member端视图（Member自用）
from .member_views import (
    CurrentMemberView,
    MemberPasswordUpdateView,
    SubAccountListCreateView,
    SubAccountDetailView,
    MemberAvatarUploadView,
)

# 从member_admin_views.py导入管理员端Member管理视图
from .member_admin_views import (
    AdminMemberListCreateView,
    AdminMemberRetrieveUpdateDeleteView,
    AdminSubAccountListView,
    AdminSubAccountDetailView,
    AdminMemberAvatarUploadView,
) 