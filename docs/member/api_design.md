# API设计

## API端点调整方案

在将用户系统拆分为User和Member两个模型后，需要对API端点进行相应的调整，以支持两种不同类型的用户进行管理。

## API端点概览

### 认证相关API

| 端点 | 方法 | 描述 | 权限 |
|-----|-----|-----|-----|
| `/api/auth/login/` | POST | 用户登录（支持两种用户类型） | 匿名 |
| `/api/auth/refresh/` | POST | 刷新访问令牌 | 匿名 |
| `/api/auth/logout/` | POST | 用户登出 | 认证用户 |
| `/api/auth/password/change/` | POST | 修改密码 | 认证用户 |
| `/api/auth/password/reset/` | POST | 请求密码重置 | 匿名 |
| `/api/auth/password/reset/confirm/` | POST | 确认密码重置 | 匿名 |

### 用户管理API

| 端点 | 方法 | 描述 | 权限 |
|-----|-----|-----|-----|
| `/api/users/` | GET | 获取用户列表 | 超级管理员/租户管理员 |
| `/api/users/` | POST | 创建新用户 | 超级管理员/租户管理员 |
| `/api/users/:id/` | GET | 获取用户详情 | 超级管理员/租户管理员/自己 |
| `/api/users/:id/` | PUT | 更新用户信息 | 超级管理员/租户管理员/自己 |
| `/api/users/:id/` | DELETE | 删除用户 | 超级管理员/租户管理员 |
| `/api/users/me/` | GET | 获取当前用户信息 | 认证用户 |

### 成员管理API

| 端点 | 方法 | 描述 | 权限 |
|-----|-----|-----|-----|
| `/api/members/` | GET | 获取成员列表 | 超级管理员/租户管理员 |
| `/api/members/` | POST | 创建新成员 | 超级管理员/租户管理员 |
| `/api/members/:id/` | GET | 获取成员详情 | 超级管理员/租户管理员/自己 |
| `/api/members/:id/` | PUT | 更新成员信息 | 超级管理员/租户管理员/自己 |
| `/api/members/:id/` | DELETE | 删除成员 | 超级管理员/租户管理员 |
| `/api/members/:id/sub-accounts/` | GET | 获取子账号列表 | 超级管理员/租户管理员/父账号 |
| `/api/members/:id/sub-accounts/` | POST | 创建子账号 | 超级管理员/租户管理员/父账号 |

## API详细设计

### 认证API

#### 登录API

```python
# POST /api/auth/login/
class LoginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        # 见认证系统设计文档
        pass
```

#### 刷新令牌API

```python
# POST /api/auth/refresh/
class RefreshTokenView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        # 见认证系统设计文档
        pass
```

#### 登出API

```python
# POST /api/auth/logout/
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # 可选：将当前令牌加入黑名单
        return Response(status=status.HTTP_204_NO_CONTENT)
```

#### 修改密码API

```python
# POST /api/auth/password/change/
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        
        if not old_password or not new_password:
            return Response(
                {'error': '旧密码和新密码不能为空'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = request.user
        
        if not user.check_password(old_password):
            return Response(
                {'error': '旧密码不正确'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.save()
        
        return Response({'message': '密码修改成功'})
```

### 用户管理API

#### 用户序列化器

```python
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'nick_name', 'phone', 'avatar',
            'first_name', 'last_name', 'is_active', 'is_super_admin',
            'tenant', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = super().create(validated_data)
        
        if password:
            user.set_password(password)
            user.save()
        
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        
        if password:
            user.set_password(password)
            user.save()
        
        return user
```

#### 用户视图集

```python
class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsSuperAdminOrTenantAdmin]
    
    def get_queryset(self):
        user = self.request.user
        
        # 超级管理员可以查看所有用户
        if isinstance(user, User) and user.is_super_admin:
            return User.objects.filter(is_deleted=False)
        
        # 租户管理员只能查看自己租户的用户
        if isinstance(user, User) and user.tenant:
            return User.objects.filter(tenant=user.tenant, is_deleted=False)
        
        # 其他情况只能查看自己
        return User.objects.filter(pk=user.pk)
    
    def perform_create(self, serializer):
        user = self.request.user
        
        # 如果是租户管理员，自动设置租户
        if isinstance(user, User) and user.tenant and not user.is_super_admin:
            serializer.save(tenant=user.tenant)
        else:
            serializer.save()
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # 软删除而不是物理删除
        instance.soft_delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
```

#### 当前用户API

```python
class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # 根据用户类型选择序列化器
        if isinstance(user, User):
            serializer = UserSerializer(user)
        elif isinstance(user, Member):
            serializer = MemberSerializer(user)
        else:
            return Response(
                {'error': '未知的用户类型'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        data = serializer.data
        data['user_type'] = 'user' if isinstance(user, User) else 'member'
        data['role'] = user.display_role
        
        return Response(data)
```

### 成员管理API

#### 成员序列化器

```python
class MemberSerializer(serializers.ModelSerializer):
    parent_username = serializers.CharField(source='parent.username', read_only=True)
    
    class Meta:
        model = Member
        fields = [
            'id', 'username', 'email', 'nick_name', 'phone', 'avatar',
            'first_name', 'last_name', 'is_active', 'parent', 'parent_username',
            'tenant', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        member = super().create(validated_data)
        
        if password:
            member.set_password(password)
            member.save()
        
        return member
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        member = super().update(instance, validated_data)
        
        if password:
            member.set_password(password)
            member.save()
        
        return member
```

#### 成员视图集

```python
class MemberViewSet(viewsets.ModelViewSet):
    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticated, IsSuperAdminOrTenantAdminOrSelf]
    
    def get_queryset(self):
        user = self.request.user
        
        # 超级管理员可以查看所有成员
        if isinstance(user, User) and user.is_super_admin:
            return Member.objects.filter(is_deleted=False)
        
        # 租户管理员只能查看自己租户的成员
        if isinstance(user, User) and user.tenant:
            return Member.objects.filter(tenant=user.tenant, is_deleted=False)
        
        # 普通成员只能查看自己和自己的子账号
        if isinstance(user, Member):
            return Member.objects.filter(
                Q(pk=user.pk) | Q(parent=user),
                is_deleted=False
            )
        
        # 其他情况只能查看自己
        return Member.objects.filter(pk=user.pk, is_deleted=False)
    
    def perform_create(self, serializer):
        user = self.request.user
        
        # 如果是租户管理员，自动设置租户
        if isinstance(user, User) and user.tenant and not user.is_super_admin:
            serializer.save(tenant=user.tenant)
        # 如果是普通成员创建子账号
        elif isinstance(user, Member) and not user.parent:
            serializer.save(tenant=user.tenant, parent=user)
        else:
            serializer.save()
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # 软删除而不是物理删除
        instance.soft_delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT)
```

#### 子账号API

```python
class SubAccountViewSet(viewsets.ModelViewSet):
    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticated, IsParentOrAdmin]
    
    def get_queryset(self):
        parent_id = self.kwargs.get('parent_id')
        user = self.request.user
        
        # 验证父账号存在
        try:
            parent = Member.objects.get(pk=parent_id, is_deleted=False)
        except Member.DoesNotExist:
            return Member.objects.none()
        
        # 超级管理员可以查看所有子账号
        if isinstance(user, User) and user.is_super_admin:
            return Member.objects.filter(parent=parent, is_deleted=False)
        
        # 租户管理员只能查看自己租户的子账号
        if isinstance(user, User) and user.tenant:
            return Member.objects.filter(
                parent=parent, 
                tenant=user.tenant, 
                is_deleted=False
            )
        
        # 父账号只能查看自己的子账号
        if isinstance(user, Member) and user.pk == parent.pk:
            return Member.objects.filter(parent=user, is_deleted=False)
        
        # 其他情况不允许访问
        return Member.objects.none()
    
    def perform_create(self, serializer):
        parent_id = self.kwargs.get('parent_id')
        
        try:
            parent = Member.objects.get(pk=parent_id, is_deleted=False)
        except Member.DoesNotExist:
            raise NotFound('父账号不存在')
        
        # 设置父账号和租户
        serializer.save(parent=parent, tenant=parent.tenant, is_active=False)
```

## 权限类设计

### 用户管理权限类

```python
class IsSuperAdminOrTenantAdmin(BasePermission):
    """
    检查用户是否为超级管理员或租户管理员
    """
    def has_permission(self, request, view):
        return (
            isinstance(request.user, User) and 
            (request.user.is_super_admin or request.user.is_tenant_admin)
        )
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # 超级管理员可以操作任何用户
        if isinstance(user, User) and user.is_super_admin:
            return True
        
        # 租户管理员只能操作自己租户的用户
        if isinstance(user, User) and user.tenant:
            return obj.tenant == user.tenant
        
        # 用户可以操作自己
        return user.pk == obj.pk

class IsSuperAdminOrTenantAdminOrSelf(BasePermission):
    """
    检查用户是否为超级管理员、租户管理员或自己
    """
    def has_permission(self, request, view):
        # 列表操作需要管理员权限
        if view.action in ['list', 'create']:
            return (
                isinstance(request.user, User) and 
                (request.user.is_super_admin or request.user.is_tenant_admin)
            )
        
        # 其他操作在has_object_permission中检查
        return True
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # 超级管理员可以操作任何成员
        if isinstance(user, User) and user.is_super_admin:
            return True
        
        # 租户管理员只能操作自己租户的成员
        if isinstance(user, User) and user.tenant:
            return obj.tenant == user.tenant
        
        # 用户可以操作自己
        return user.pk == obj.pk

class IsParentOrAdmin(BasePermission):
    """
    检查用户是否为父账号、超级管理员或租户管理员
    """
    def has_permission(self, request, view):
        user = request.user
        parent_id = view.kwargs.get('parent_id')
        
        # 超级管理员可以操作任何子账号
        if isinstance(user, User) and user.is_super_admin:
            return True
        
        # 租户管理员只能操作自己租户的子账号
        if isinstance(user, User) and user.tenant:
            try:
                parent = Member.objects.get(pk=parent_id)
                return parent.tenant == user.tenant
            except Member.DoesNotExist:
                return False
        
        # 父账号可以操作自己的子账号
        return isinstance(user, Member) and str(user.pk) == parent_id
    
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # 超级管理员可以操作任何子账号
        if isinstance(user, User) and user.is_super_admin:
            return True
        
        # 租户管理员只能操作自己租户的子账号
        if isinstance(user, User) and user.tenant:
            return obj.tenant == user.tenant
        
        # 父账号可以操作自己的子账号
        return isinstance(user, Member) and obj.parent == user
```

## URL配置

```python
# users/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'members', views.MemberViewSet, basename='member')
router.register(r'members/(?P<parent_id>\d+)/sub-accounts', views.SubAccountViewSet, basename='sub-account')

urlpatterns = [
    # 认证相关URL
    path('auth/login/', views.LoginView.as_view(), name='login'),
    path('auth/refresh/', views.RefreshTokenView.as_view(), name='refresh'),
    path('auth/logout/', views.LogoutView.as_view(), name='logout'),
    path('auth/password/change/', views.ChangePasswordView.as_view(), name='change-password'),
    path('auth/password/reset/', views.ResetPasswordView.as_view(), name='reset-password'),
    path('auth/password/reset/confirm/', views.ResetPasswordConfirmView.as_view(), name='reset-password-confirm'),
    
    # 当前用户URL
    path('users/me/', views.CurrentUserView.as_view(), name='current-user'),
    
    # 视图集URL
    path('', include(router.urls)),
]
```

## 注意事项

1. **API版本控制**：考虑为API添加版本控制，以便将来进行兼容性更改
2. **请求限制**：为API端点添加请求限制，防止滥用
3. **错误处理**：统一API的错误处理和响应格式
4. **文档生成**：使用Swagger或DRF的文档生成功能生成API文档
5. **测试覆盖**：确保为所有API端点编写测试用例
6. **权限粒度**：根据实际业务需求调整权限控制的粒度 