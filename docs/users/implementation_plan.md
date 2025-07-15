# 用户系统API改进实施计划

## 概述

为了更好地适应用户系统中User(管理员)和Member(普通用户)的分离设计，需要对API架构进行重构。本文档详细说明了改进API的具体步骤和实施方案。

## 实施阶段

### 阶段一：新建视图和序列化器（2周）

#### 1. 创建Member专用视图

**新文件：** `users/views/member_views.py`

```python
"""
普通用户(Member)相关视图
"""
import logging
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse, OpenApiExample

from common.permissions import IsAdmin, IsSuperAdmin
from users.models import Member
from users.serializers import (
    MemberSerializer, 
    MemberCreateSerializer,
    SubAccountSerializer
)
from common.schema import api_schema, common_search_parameter, user_status_parameter, common_pagination_parameters

logger = logging.getLogger(__name__)

# 以下视图类似于现有的user_views.py中的视图，但专门针对Member模型
class MemberListCreateView(generics.ListCreateAPIView):
    """
    普通用户列表和创建视图
    """
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    serializer_class = MemberSerializer
    pagination_class = PageNumberPagination
    
    # 实现方法与现有UserListCreateView类似，但针对Member模型
    ...

class MemberRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    """
    普通用户详情、更新和删除视图
    """
    serializer_class = MemberSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    # 实现方法与现有UserRetrieveUpdateDeleteView类似，但针对Member模型
    ...

class CurrentMemberView(APIView):
    """
    获取和更新当前登录普通用户信息
    """
    permission_classes = [permissions.IsAuthenticated]
    
    # 实现方法与现有CurrentUserView类似，但确保用户是Member类型
    ...

# 子账号相关视图，从现有视图迁移并优化
class SubAccountCreateView(generics.CreateAPIView):
    """
    创建子账号视图
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SubAccountSerializer
    
    # 实现方法与现有SubAccountCreateView类似，但优化
    ...

# 添加会员头像上传视图
class MemberAvatarUploadView(APIView):
    """
    普通用户头像上传视图
    """
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    # 实现方法与现有UserAvatarUploadView类似，但确保用户是Member类型
    ...

# 添加管理员为会员上传头像的视图
class MemberSpecificAvatarUploadView(APIView):
    """
    管理员为普通用户上传头像视图
    """
    permission_classes = [permissions.IsAuthenticated, IsAdmin]
    parser_classes = [MultiPartParser, FormParser]
    
    # 实现方法与现有UserSpecificAvatarUploadView类似，但针对Member模型
    ...
```

#### 2. 重构现有用户视图

**修改文件：** `users/views/user_views.py` → 重命名为 `users/views/admin_user_views.py`

主要修改：
- 从视图中移除所有Member相关的处理
- 调整查询和过滤逻辑，只处理User模型
- 更新API文档

#### 3. 创建Member专用序列化器

**新文件或修改现有文件：** `users/serializers.py`

添加以下序列化器：

```python
class MemberSerializer(serializers.ModelSerializer):
    """
    普通用户序列化器
    """
    tenant_name = serializers.SerializerMethodField()
    is_sub_account = serializers.SerializerMethodField()
    parent_username = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = Member
        fields = [
            'id', 'username', 'email', 'phone', 'nick_name', 'first_name', 
            'last_name', 'is_active', 'avatar', 'tenant', 'tenant_name', 
            'is_sub_account', 'parent', 'parent_username', 'date_joined'
        ]
        read_only_fields = ['id', 'date_joined', 'tenant_name', 'is_sub_account', 'parent_username']
    
    # 实现各种get_方法
    ...

class MemberCreateSerializer(serializers.ModelSerializer):
    """
    普通用户创建序列化器
    """
    password_confirm = serializers.CharField(write_only=True)
    tenant_id = serializers.PrimaryKeyRelatedField(
        queryset=Tenant.objects.all(),
        required=False,
        source='tenant',
        write_only=True
    )
    
    class Meta:
        model = Member
        fields = [
            'id', 'username', 'email', 'phone', 'nick_name', 'first_name',
            'last_name', 'password', 'password_confirm', 'tenant_id',
            'avatar'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'id': {'read_only': True}
        }
    
    # 实现validate和create方法
    ...
```

#### 4. 优化认证视图

**修改文件：** `users/views/auth_views.py`

主要修改：
- 优化登录逻辑，明确区分User和Member模型
- 在JWT令牌中添加用户类型标识
- 确保令牌刷新和验证功能兼容两种用户类型

### 阶段二：创建新的URL配置（1周）

#### 1. 创建Member专用URL配置

**新文件：** `users/urls/member_urls.py`

```python
"""
普通用户相关的URL路由
"""
from django.urls import path
from users.views import member_views

app_name = 'members'

urlpatterns = [
    # 当前普通用户信息
    path('me/', member_views.CurrentMemberView.as_view(), name='current-member'),
    
    # 普通用户列表和创建
    path('', member_views.MemberListCreateView.as_view(), name='member-list-create'),
    
    # 普通用户详情、更新和删除
    path('<int:pk>/', member_views.MemberRetrieveUpdateDeleteView.as_view(), name='member-detail'),
    
    # 上传头像
    path('me/upload-avatar/', member_views.MemberAvatarUploadView.as_view(), name='upload-avatar'),
    
    # 管理员为指定普通用户上传头像
    path('<int:pk>/upload-avatar/', member_views.MemberSpecificAvatarUploadView.as_view(), name='upload-member-avatar'),
    
    # 子账号管理
    path('sub-account/create/', member_views.SubAccountCreateView.as_view(), name='create-sub-account'),
]
```

#### 2. 更新管理员用户URL配置

**修改文件：** `users/urls/user_urls.py` → 重命名为 `users/urls/admin_urls.py`

修改URL模式以反映专注于管理员的功能。

#### 3. 更新主URL配置

**修改文件：** `users/urls/__init__.py`

```python
"""
用户相关URL路由包
"""
from django.urls import path, include

app_name = 'users'

urlpatterns = [
    # 认证相关URL - 保持不变
    path('auth/', include('users.urls.auth_urls', namespace='auth')),
    
    # 管理员用户相关URL
    path('admin-users/', include('users.urls.admin_urls', namespace='admin')),
    
    # 普通用户相关URL
    path('members/', include('users.urls.member_urls', namespace='members')),
    
    # 兼容性：保留旧路径一段时间，但标记为弃用
    path('users/', include('users.urls.compat_urls', namespace='compat')),
]
```

**新文件：** `users/urls/compat_urls.py`

创建兼容性URL配置，保留旧的路径但添加弃用警告。

### 阶段三：更新权限和认证机制（1周）

#### 1. 创建专用权限类

**新文件或修改现有文件：** `common/permissions.py`

```python
from rest_framework import permissions
from users.models import User, Member

class IsMember(permissions.BasePermission):
    """
    只允许Member模型的实例访问
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and isinstance(request.user, Member)

class IsAdminUser(permissions.BasePermission):
    """
    只允许User模型的实例访问
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and isinstance(request.user, User)
```

#### 2. 更新JWT认证处理

**修改文件：** `common/authentication/jwt_auth.py`

优化JWT认证机制，确保能正确处理两种用户类型。

### 阶段四：测试和文档（2周）

#### 1. 编写测试用例

为所有新创建和修改的API端点编写全面的测试用例。

#### 2. 更新API文档

**新文件：** `docs/users/admin_api.md` 和 `docs/users/member_api.md`

创建分离的API文档，明确区分管理员API和普通用户API。

#### 3. 创建迁移指南

**新文件：** `docs/users/migration_guide.md`

为前端开发人员提供从旧API迁移到新API的详细指南。

## 实施时间表

总计预计需要6周时间完成所有工作：

1. **阶段一**（2周）：新建视图和序列化器
2. **阶段二**（1周）：创建新的URL配置
3. **阶段三**（1周）：更新权限和认证机制
4. **阶段四**（2周）：测试和文档

## 风险和缓解措施

### 潜在风险

1. **前端兼容性问题**：前端可能依赖于当前的API结构
2. **认证流程中断**：修改认证机制可能导致用户无法登录
3. **性能影响**：API改动可能影响系统性能

### 缓解措施

1. **保留兼容性路径**：维持旧API路径一段时间
2. **分阶段部署**：先部署不影响现有功能的部分
3. **全面测试**：部署前进行全面测试
4. **回滚计划**：准备详细的回滚方案
5. **监控系统**：部署后密切监控系统性能和错误

## 结论

通过这一系列改进，用户系统API将更加清晰、高效，并且更符合REST API的设计原则。分离管理员和普通用户的API不仅提高了代码的可维护性，也增强了系统的安全性。 