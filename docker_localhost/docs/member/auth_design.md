# 认证系统设计

## 认证系统调整方案

在将用户系统拆分为User和Member两个模型后，需要对认证系统进行相应的调整，以支持两种不同类型的用户进行认证。

## 认证流程

### 现有认证流程

当前系统使用JWT（JSON Web Token）进行认证，基本流程如下：

1. 用户提供用户名/密码进行登录
2. 系统验证凭据并生成访问令牌（access token）和刷新令牌（refresh token）
3. 客户端在后续请求中使用访问令牌进行身份验证
4. 访问令牌过期后，客户端使用刷新令牌获取新的访问令牌

### 调整后的认证流程

调整后的认证流程需要支持两种用户模型，主要流程如下：

1. 用户提供用户名/密码进行登录
2. 系统首先在User模型中查找用户，如果找到则验证密码
3. 如果在User模型中未找到用户，则在Member模型中查找并验证密码
4. 根据用户类型（User或Member）生成包含用户类型信息的令牌
5. 在验证令牌时，根据令牌中的用户类型信息，从对应的模型中获取用户实例

## 认证后端设计

### 自定义认证后端

创建一个自定义认证后端，支持两种用户模型的认证：

```python
class MultiModelAuthBackend(BaseBackend):
    """
    支持User和Member两种模型的认证后端
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        验证用户凭据
        """
        # 尝试在User模型中查找用户
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            pass
        
        # 尝试在Member模型中查找用户
        try:
            member = Member.objects.get(username=username)
            if member.check_password(password):
                return member
        except Member.DoesNotExist:
            pass
        
        # 认证失败
        return None
    
    def get_user(self, user_id):
        """
        根据ID获取用户
        """
        # 尝试从User模型获取
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            pass
        
        # 尝试从Member模型获取
        try:
            return Member.objects.get(pk=user_id)
        except Member.DoesNotExist:
            return None
```

### JWT令牌定制

修改JWT令牌生成和验证逻辑，以支持两种用户模型：

```python
def get_token_for_user(user):
    """
    为用户生成JWT令牌
    """
    # 确定用户类型
    if isinstance(user, User):
        user_type = 'user'
    elif isinstance(user, Member):
        user_type = 'member'
    else:
        raise ValueError("不支持的用户类型")
    
    # 创建令牌负载
    payload = {
        'user_id': user.id,
        'username': user.username,
        'user_type': user_type,
        'exp': datetime.datetime.utcnow() + settings.JWT_EXPIRATION_DELTA,
    }
    
    # 如果用户关联了租户，添加租户信息
    if user.tenant:
        payload['tenant_id'] = user.tenant.id
    
    # 生成令牌
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm='HS256')
    
    return token
```

### 用户获取中间件

创建一个中间件，用于从JWT令牌中获取当前用户：

```python
class JWTAuthMiddleware:
    """
    从JWT令牌中获取当前用户的中间件
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # 获取请求头中的Authorization
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if auth_header.startswith('Bearer '):
            # 提取令牌
            token = auth_header[7:]
            
            try:
                # 解码令牌
                payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=['HS256'])
                
                # 根据用户类型获取用户实例
                user_type = payload.get('user_type')
                user_id = payload.get('user_id')
                
                if user_type == 'user':
                    request.user = User.objects.get(pk=user_id)
                elif user_type == 'member':
                    request.user = Member.objects.get(pk=user_id)
                else:
                    # 无效的用户类型
                    request.user = AnonymousUser()
            except (jwt.DecodeError, jwt.ExpiredSignatureError, User.DoesNotExist, Member.DoesNotExist):
                # 令牌无效或用户不存在
                request.user = AnonymousUser()
        else:
            # 没有令牌
            request.user = AnonymousUser()
        
        return self.get_response(request)
```

## 登录视图设计

### 登录视图

创建一个统一的登录视图，支持两种用户模型：

```python
class LoginView(APIView):
    """
    用户登录视图
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {'error': '用户名和密码不能为空'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 使用自定义认证后端进行认证
        user = authenticate(request, username=username, password=password)
        
        if user is None:
            return Response(
                {'error': '用户名或密码错误'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # 检查用户是否被删除或禁用
        if user.is_deleted:
            return Response(
                {'error': '该用户已被删除'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if not user.is_active:
            return Response(
                {'error': '该用户已被禁用'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 检查用户类型
        if isinstance(user, Member) and user.is_sub_account:
            return Response(
                {'error': '子账号不允许登录'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 生成令牌
        access_token = get_token_for_user(user)
        refresh_token = get_refresh_token_for_user(user)
        
        # 更新最后登录信息
        user.last_login = timezone.now()
        user.last_login_ip = get_client_ip(request)
        user.save(update_fields=['last_login', 'last_login_ip'])
        
        # 返回令牌和用户信息
        return Response({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'nick_name': user.nick_name,
                'avatar': user.avatar,
                'user_type': 'user' if isinstance(user, User) else 'member',
                'role': user.display_role,
                'tenant': user.tenant.name if user.tenant else None,
            }
        })
```

### 令牌刷新视图

创建令牌刷新视图，支持两种用户模型：

```python
class RefreshTokenView(APIView):
    """
    刷新令牌视图
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        
        if not refresh_token:
            return Response(
                {'error': '刷新令牌不能为空'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 解码刷新令牌
            payload = jwt.decode(refresh_token, settings.JWT_REFRESH_SECRET_KEY, algorithms=['HS256'])
            
            # 获取用户信息
            user_type = payload.get('user_type')
            user_id = payload.get('user_id')
            
            # 根据用户类型获取用户实例
            if user_type == 'user':
                user = User.objects.get(pk=user_id)
            elif user_type == 'member':
                user = Member.objects.get(pk=user_id)
            else:
                return Response(
                    {'error': '无效的用户类型'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 检查用户状态
            if user.is_deleted or not user.is_active:
                return Response(
                    {'error': '用户已被删除或禁用'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # 生成新的访问令牌
            access_token = get_token_for_user(user)
            
            return Response({
                'access_token': access_token
            })
        except (jwt.DecodeError, jwt.ExpiredSignatureError):
            return Response(
                {'error': '无效或已过期的刷新令牌'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except (User.DoesNotExist, Member.DoesNotExist):
            return Response(
                {'error': '用户不存在'},
                status=status.HTTP_401_UNAUTHORIZED
            )
```

## 权限控制设计

### 自定义权限类

创建自定义权限类，支持两种用户模型：

```python
class IsSuperAdmin(BasePermission):
    """
    检查用户是否为超级管理员
    """
    def has_permission(self, request, view):
        return isinstance(request.user, User) and request.user.is_super_admin

class IsTenantAdmin(BasePermission):
    """
    检查用户是否为租户管理员
    """
    def has_permission(self, request, view):
        return isinstance(request.user, User) and request.user.is_tenant_admin

class IsMember(BasePermission):
    """
    检查用户是否为普通成员
    """
    def has_permission(self, request, view):
        return isinstance(request.user, Member) and not request.user.is_sub_account

class IsAuthenticated(BasePermission):
    """
    检查用户是否已认证（支持两种用户模型）
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and
            not getattr(request.user, 'is_deleted', False)
        )

class HasTenantAccess(BasePermission):
    """
    检查用户是否有权访问指定租户的资源
    """
    def has_permission(self, request, view):
        # 超级管理员可以访问所有租户的资源
        if isinstance(request.user, User) and request.user.is_super_admin:
            return True
        
        # 获取请求中的租户ID
        tenant_id = view.kwargs.get('tenant_id') or request.query_params.get('tenant_id')
        
        if not tenant_id:
            return True  # 如果请求中没有指定租户，则放行（由视图处理）
        
        # 检查用户是否属于该租户
        return request.user.tenant_id == int(tenant_id)
```

## 配置更新

### Django设置更新

更新Django设置以支持两种用户模型：

```python
# 设置主要用户模型为User
AUTH_USER_MODEL = 'users.User'

# 认证后端
AUTHENTICATION_BACKENDS = [
    'users.backends.MultiModelAuthBackend',
    'django.contrib.auth.backends.ModelBackend',
]

# 中间件
MIDDLEWARE = [
    # ... 其他中间件 ...
    'users.middleware.JWTAuthMiddleware',
]

# JWT设置
JWT_SECRET_KEY = env('JWT_SECRET_KEY', default=SECRET_KEY)
JWT_REFRESH_SECRET_KEY = env('JWT_REFRESH_SECRET_KEY', default=SECRET_KEY)
JWT_EXPIRATION_DELTA = datetime.timedelta(hours=1)
JWT_REFRESH_EXPIRATION_DELTA = datetime.timedelta(days=7)
```

## 注意事项

1. **会话管理**：需要考虑如何处理两种用户模型的会话管理
2. **权限粒度**：需要根据业务需求调整权限粒度，可能需要更细粒度的权限控制
3. **认证性能**：由于需要在两个模型中查找用户，可能会影响认证性能，需要考虑优化措施
4. **令牌安全**：确保JWT令牌的安全性，包括适当的过期时间和密钥管理
5. **兼容性**：确保与现有系统的兼容性，特别是与第三方集成的部分 