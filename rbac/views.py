"""
RBAC系统视图
"""
import logging
from django.db import transaction
from django.db.models import Q
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, permissions, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample

from .models import Permission, Role, RolePermission, UserRole
from .serializers import (
    PermissionSerializer, 
    RoleSerializer, 
    RoleDetailSerializer, 
    RolePermissionSerializer,
    UserRoleSerializer,
    UserRoleCreateSerializer,
    PermissionBatchCheckSerializer,
    PermissionCheckResponseSerializer,
    PermissionBatchCheckResponseSerializer,
    CacheRefreshResponseSerializer,
    TenantRoleCreateFromTemplateSerializer
)
from .permissions import (
    RBACPermissionRequired, 
    has_permission, 
    get_user_permissions, 
    invalidate_permissions_cache,
    RBAC_CACHE_TIMEOUT
)

logger = logging.getLogger(__name__)

@extend_schema_view(
    list=extend_schema(
        summary="获取权限列表",
        description="获取系统中所有权限，支持分页、搜索和按类别过滤",
        parameters=[
            OpenApiParameter(name='search', description='搜索关键词(针对name, code, description)', required=False, type=str),
            OpenApiParameter(name='category', description='按类别过滤', required=False, type=str),
            OpenApiParameter(name='is_system', description='是否系统权限(true/false)', required=False, type=bool),
        ],
        tags=["RBAC系统"]
    ),
    retrieve=extend_schema(
        summary="获取权限详情",
        description="获取单个权限的详细信息",
        tags=["RBAC系统"]
    ),
    create=extend_schema(
        summary="创建权限",
        description="创建新权限",
        tags=["RBAC系统"]
    ),
    update=extend_schema(
        summary="更新权限",
        description="更新现有权限",
        tags=["RBAC系统"]
    ),
    partial_update=extend_schema(
        summary="部分更新权限",
        description="部分更新现有权限",
        tags=["RBAC系统"]
    ),
    destroy=extend_schema(
        summary="删除权限",
        description="删除权限(系统权限不可删除)",
        tags=["RBAC系统"]
    )
)
class PermissionViewSet(viewsets.ModelViewSet):
    """
    权限管理API
    """
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAuthenticated, RBACPermissionRequired]
    rbac_permissions = {
        'list': 'permission:view',
        'retrieve': 'permission:view',
        'create': 'permission:create',
        'update': 'permission:edit',
        'partial_update': 'permission:edit',
        'destroy': 'permission:delete',
        'categories': 'permission:view',
        'check': None,  # 无需特定权限
        'batch_check': None,  # 无需特定权限
    }
    
    def get_queryset(self):
        """根据查询参数过滤权限"""
        queryset = Permission.objects.all()
        
        # 根据搜索关键词过滤
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(code__icontains=search) | 
                Q(description__icontains=search)
            )
        
        # 根据类别过滤
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        # 根据是否系统权限过滤
        is_system = self.request.query_params.get('is_system')
        if is_system is not None:
            is_system = is_system.lower() == 'true'
            queryset = queryset.filter(is_system=is_system)
        
        return queryset
    
    def perform_destroy(self, instance):
        """删除前检查是否为系统权限"""
        if instance.is_system:
            logger.warning(f"用户 {self.request.user.username} 尝试删除系统权限 {instance.code}")
            return Response(
                {"detail": "系统权限不允许删除"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 如果该权限被角色使用，则不允许删除
        if instance.roles.exists():
            logger.warning(f"用户 {self.request.user.username} 尝试删除已被角色使用的权限 {instance.code}")
            return Response(
                {"detail": "该权限已被角色使用，不能删除"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        logger.info(f"用户 {self.request.user.username} 删除权限 {instance.code}")
        instance.delete()
    
    @extend_schema(
        summary="获取权限类别",
        description="获取系统中所有权限类别",
        tags=["RBAC系统"]
    )
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """获取所有权限类别"""
        categories = Permission.objects.values_list('category', flat=True).distinct()
        return Response(list(categories))
    
    @extend_schema(
        summary="检查当前用户权限",
        description="检查当前用户是否拥有指定权限",
        parameters=[
            OpenApiParameter(name='code', description='权限代码', required=True, type=str),
        ],
        responses={200: PermissionCheckResponseSerializer},
        tags=["RBAC系统"]
    )
    @action(detail=False, methods=['get'])
    def check(self, request):
        """检查当前用户是否拥有指定权限"""
        code = request.query_params.get('code')
        if not code:
            return Response(
                {"detail": "必须提供权限代码参数'code'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        has_perm = has_permission(request.user, code)
        return Response({
            "has_permission": has_perm,
            "permission_code": code
        })
    
    @extend_schema(
        summary="批量检查权限",
        description="批量检查当前用户是否拥有多个权限",
        request=PermissionBatchCheckSerializer,
        responses={200: PermissionBatchCheckResponseSerializer},
        tags=["RBAC系统"]
    )
    @action(detail=False, methods=['post'])
    def batch_check(self, request):
        """批量检查当前用户是否拥有多个权限"""
        serializer = PermissionBatchCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        codes = serializer.validated_data['codes']
        user_permissions = get_user_permissions(request.user)
        
        result = {code: code in user_permissions for code in codes}
        
        return Response({"permissions": result})

@extend_schema_view(
    list=extend_schema(
        summary="获取角色列表",
        description="获取角色列表，根据当前用户租户上下文过滤",
        parameters=[
            OpenApiParameter(name='search', description='搜索关键词(针对name, code, description)', required=False, type=str),
            OpenApiParameter(name='tenant_id', description='按租户过滤(超管可用)', required=False, type=int),
            OpenApiParameter(name='is_system', description='是否系统角色(true/false)', required=False, type=bool),
        ],
        tags=["RBAC系统"]
    ),
    retrieve=extend_schema(
        summary="获取角色详情",
        description="获取角色详情，包括关联的权限",
        tags=["RBAC系统"]
    ),
    create=extend_schema(
        summary="创建角色",
        description="创建新角色",
        tags=["RBAC系统"]
    ),
    update=extend_schema(
        summary="更新角色",
        description="更新角色信息",
        tags=["RBAC系统"]
    ),
    partial_update=extend_schema(
        summary="部分更新角色",
        description="部分更新角色信息",
        tags=["RBAC系统"]
    ),
    destroy=extend_schema(
        summary="删除角色",
        description="删除角色(系统角色不可删除)",
        tags=["RBAC系统"]
    )
)
class RoleViewSet(viewsets.ModelViewSet):
    """
    角色管理API
    """
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated, RBACPermissionRequired]
    rbac_permissions = {
        'list': 'role:view',
        'retrieve': 'role:view',
        'create': 'role:create',
        'update': 'role:edit',
        'partial_update': 'role:edit',
        'destroy': 'role:delete',
        'permissions': 'role:view',
        'add_permissions': 'permission:assign',
        'remove_permission': 'permission:assign',
        'update_permissions': 'permission:assign',
    }
    
    def get_serializer_class(self):
        """根据操作选择序列化器"""
        if self.action == 'retrieve':
            return RoleDetailSerializer
        elif self.action in ['add_permissions', 'update_permissions']:
            return RolePermissionSerializer
        return self.serializer_class
    
    def get_queryset(self):
        """根据查询参数和用户租户过滤角色"""
        queryset = Role.objects.all()
        
        # 获取用户所在租户
        user = self.request.user
        user_tenant_id = getattr(user, 'tenant_id', None)
        
        # 如果用户不是超级管理员，只能看到自己租户的角色和系统角色
        if not getattr(user, 'is_super_admin', False):
            queryset = queryset.filter(
                Q(tenant_id=user_tenant_id) | Q(tenant__isnull=True)
            )
        
        # 根据搜索关键词过滤
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(code__icontains=search) | 
                Q(description__icontains=search)
            )
        
        # 根据租户过滤(仅超管可用)
        tenant_id = self.request.query_params.get('tenant_id')
        if tenant_id and getattr(user, 'is_super_admin', False):
            if tenant_id == 'null':
                queryset = queryset.filter(tenant__isnull=True)
            else:
                queryset = queryset.filter(tenant_id=tenant_id)
        
        # 根据是否系统角色过滤
        is_system = self.request.query_params.get('is_system')
        if is_system is not None:
            is_system = is_system.lower() == 'true'
            queryset = queryset.filter(is_system=is_system)
        
        return queryset
    
    def perform_create(self, serializer):
        """创建角色时设置租户"""
        user = self.request.user
        
        # 如果前端没有提供tenant_id或当前用户不是超级管理员，使用当前用户租户
        tenant_id = serializer.validated_data.get('tenant')
        if tenant_id is None and not getattr(user, 'is_super_admin', False):
            serializer.validated_data['tenant_id'] = getattr(user, 'tenant_id', None)
            
        logger.info(f"用户 {user.username} 创建角色 {serializer.validated_data['name']}")
        serializer.save()
    
    def perform_destroy(self, instance):
        """删除前检查是否为系统角色"""
        if instance.is_system:
            logger.warning(f"用户 {self.request.user.username} 尝试删除系统角色 {instance.name}")
            return Response(
                {"detail": "系统角色不允许删除"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # 如果该角色已被用户使用，则不允许删除
        if instance.user_roles.exists():
            logger.warning(f"用户 {self.request.user.username} 尝试删除已被用户使用的角色 {instance.name}")
            return Response(
                {"detail": "该角色已被用户使用，不能删除"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        logger.info(f"用户 {self.request.user.username} 删除角色 {instance.name}")
        instance.delete()

    @extend_schema(
        summary="获取角色权限",
        description="获取角色关联的所有权限",
        tags=["RBAC系统"]
    )
    @action(detail=True, methods=['get'])
    def permissions(self, request, pk=None):
        """获取角色关联的所有权限"""
        role = self.get_object()
        permissions = role.permissions.all()
        serializer = PermissionSerializer(permissions, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="分配权限到角色",
        description="分配一个或多个权限给角色",
        request=RolePermissionSerializer,
        tags=["RBAC系统"]
    )
    @action(detail=True, methods=['post'], url_path='permissions')
    def add_permissions(self, request, pk=None):
        """分配一个或多个权限给角色"""
        role = self.get_object()
        serializer = RolePermissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        permission_ids = serializer.validated_data['permission_ids']
        permissions = Permission.objects.filter(id__in=permission_ids)
        
        # 检查权限是否存在
        if len(permissions) != len(permission_ids):
            return Response(
                {"detail": "部分权限不存在"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # 添加权限到角色
        for permission in permissions:
            RolePermission.objects.get_or_create(role=role, permission=permission)
            
        # 刷新用户权限缓存
        self._refresh_users_permissions_cache(role)
        
        logger.info(f"用户 {request.user.username} 为角色 {role.name} 添加了权限: {', '.join([p.code for p in permissions])}")
        
        return Response({"detail": "权限已成功添加到角色"})
    
    @extend_schema(
        summary="从角色移除权限",
        description="从角色中移除指定权限",
        tags=["RBAC系统"]
    )
    @action(detail=True, methods=['delete'], url_path='permissions/(?P<permission_id>[^/.]+)')
    def remove_permission(self, request, pk=None, permission_id=None):
        """从角色中移除指定权限"""
        role = self.get_object()
        
        try:
            permission = Permission.objects.get(id=permission_id)
        except Permission.DoesNotExist:
            return Response(
                {"detail": "权限不存在"},
                status=status.HTTP_404_NOT_FOUND
            )
            
        try:
            role_permission = RolePermission.objects.get(role=role, permission=permission)
            role_permission.delete()
            
            # 刷新用户权限缓存
            self._refresh_users_permissions_cache(role)
            
            logger.info(f"用户 {request.user.username} 从角色 {role.name} 移除了权限: {permission.code}")
            
            return Response({"detail": "权限已成功从角色移除"})
        except RolePermission.DoesNotExist:
            return Response(
                {"detail": "该权限未分配给该角色"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @extend_schema(
        summary="批量更新角色权限",
        description="批量更新角色的全部权限(替换现有权限)",
        request=RolePermissionSerializer,
        tags=["RBAC系统"]
    )
    @action(detail=True, methods=['put'], url_path='permissions')
    def update_permissions(self, request, pk=None):
        """批量更新角色的全部权限"""
        role = self.get_object()
        serializer = RolePermissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        permission_ids = serializer.validated_data['permission_ids']
        permissions = Permission.objects.filter(id__in=permission_ids)
        
        # 检查权限是否存在
        if len(permissions) != len(permission_ids) and permission_ids:
            return Response(
                {"detail": "部分权限不存在"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        with transaction.atomic():
            # 清除现有权限
            RolePermission.objects.filter(role=role).delete()
            
            # 添加新权限
            for permission in permissions:
                RolePermission.objects.create(role=role, permission=permission)
                
        # 刷新用户权限缓存
        self._refresh_users_permissions_cache(role)
        
        logger.info(f"用户 {request.user.username} 更新了角色 {role.name} 的权限: {', '.join([p.code for p in permissions])}")
        
        return Response({"detail": "角色权限已成功更新"})
    
    def _refresh_users_permissions_cache(self, role):
        """刷新使用该角色的用户的权限缓存"""
        # 获取使用该角色的所有用户
        user_roles = role.user_roles.all()
        
        # 清除每个用户的权限缓存
        for user_role in user_roles:
            cache_key = f"rbac_user_permissions_{user_role.user_type}_{user_role.user_id}"
            cache.delete(cache_key)
            
        logger.info(f"已刷新角色 {role.name} 的 {user_roles.count()} 个用户的权限缓存")

@extend_schema_view(
    list=extend_schema(
        summary="获取用户角色列表",
        description="获取用户角色关联列表，支持按用户类型、角色等过滤",
        parameters=[
            OpenApiParameter(name='user_type', description='用户类型(user/member)', required=False, type=str),
            OpenApiParameter(name='user_id', description='用户ID', required=False, type=int),
            OpenApiParameter(name='role_id', description='角色ID', required=False, type=int),
            OpenApiParameter(name='is_active', description='是否激活', required=False, type=bool),
        ],
        tags=["RBAC系统"]
    ),
    retrieve=extend_schema(
        summary="获取用户角色详情",
        description="获取单个用户角色关联的详细信息",
        tags=["RBAC系统"]
    ),
    update=extend_schema(
        summary="更新用户角色",
        description="更新用户角色关联信息",
        tags=["RBAC系统"]
    ),
    partial_update=extend_schema(
        summary="部分更新用户角色",
        description="部分更新用户角色关联信息",
        tags=["RBAC系统"]
    ),
    destroy=extend_schema(
        summary="删除用户角色",
        description="删除用户角色关联",
        tags=["RBAC系统"]
    )
)
class UserRoleViewSet(viewsets.ModelViewSet):
    """
    用户角色关联管理API
    """
    queryset = UserRole.objects.all()
    serializer_class = UserRoleSerializer
    permission_classes = [permissions.IsAuthenticated, RBACPermissionRequired]
    rbac_permissions = {
        'list': 'role:view',
        'retrieve': 'role:view',
        'create': None,  # 通过专门的API创建
        'update': 'role:assign',
        'partial_update': 'role:assign',
        'destroy': 'role:assign'
    }
    http_method_names = ['get', 'put', 'patch', 'delete', 'head', 'options']  # 移除POST
    
    def get_queryset(self):
        """根据查询参数和用户租户过滤用户角色"""
        queryset = UserRole.objects.all()
        
        # 获取用户所在租户
        user = self.request.user
        user_tenant_id = getattr(user, 'tenant_id', None)
        
        # 如果用户不是超级管理员，只能看到自己租户的角色
        if not getattr(user, 'is_super_admin', False) and user_tenant_id:
            queryset = queryset.filter(
                Q(role__tenant_id=user_tenant_id) | Q(role__tenant__isnull=True)
            )
        
        # 根据用户类型过滤
        user_type = self.request.query_params.get('user_type')
        if user_type:
            queryset = queryset.filter(user_type=user_type)
        
        # 根据用户ID过滤
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # 根据角色ID过滤
        role_id = self.request.query_params.get('role_id')
        if role_id:
            queryset = queryset.filter(role_id=role_id)
        
        # 根据激活状态过滤
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
        
        return queryset
    
    def perform_update(self, serializer):
        """更新用户角色关联信息"""
        original_instance = self.get_object()
        instance = serializer.save()
        
        # 如果是修改了状态或有效期，可能需要刷新权限缓存
        changed_fields = set()
        for field in ['is_active', 'start_date', 'end_date']:
            original_value = getattr(original_instance, field)
            new_value = getattr(instance, field)
            if original_value != new_value:
                changed_fields.add(field)
        
        if changed_fields:
            cache_key = f"rbac_user_permissions_{instance.user_type}_{instance.user_id}"
            cache.delete(cache_key)
            logger.info(f"更新了用户角色 #{instance.id} 的 {','.join(changed_fields)} 字段，已刷新权限缓存")
    
    def perform_destroy(self, instance):
        """删除用户角色关联前记录日志"""
        logger.info(f"用户 {self.request.user.username} 删除 {instance.get_user_type_display()} ID:{instance.user_id} 的角色 {instance.role.name}")
        
        # 删除前先清除缓存
        cache_key = f"rbac_user_permissions_{instance.user_type}_{instance.user_id}"
        cache.delete(cache_key)
        
        instance.delete()

@extend_schema_view(
    list=extend_schema(
        summary="获取指定用户的角色",
        description="获取指定用户关联的所有角色",
        tags=["RBAC系统"]
    ),
    create=extend_schema(
        summary="为用户分配角色",
        description="为指定用户分配一个角色",
        request=UserRoleCreateSerializer,
        tags=["RBAC系统"]
    )
)
class UserRolesViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    获取特定用户的角色，或为特定用户分配角色
    """
    serializer_class = UserRoleSerializer
    permission_classes = [permissions.IsAuthenticated, RBACPermissionRequired]
    rbac_permissions = {
        'list': 'role:view',
        'create': 'role:assign',
        'destroy': 'role:assign',
        'update': 'role:assign'
    }
    
    def get_queryset(self):
        """获取指定用户所有角色"""
        user_type = self.kwargs.get('user_type')
        user_id = self.kwargs.get('user_id')
        
        if not user_type or not user_id:
            return UserRole.objects.none()
            
        return UserRole.objects.filter(user_type=user_type, user_id=user_id)
    
    def get_serializer_class(self):
        """根据操作选择序列化器"""
        if self.action == 'create':
            return UserRoleCreateSerializer
        return self.serializer_class
    
    def create(self, request, *args, **kwargs):
        """为用户分配角色"""
        user_type = kwargs.get('user_type')
        user_id = kwargs.get('user_id')
        
        if not user_type or not user_id:
            return Response(
                {"detail": "未提供用户类型或用户ID"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        role_id = data.get('role_id')
        
        # 检查是否已分配该角色
        if UserRole.objects.filter(user_type=user_type, user_id=user_id, role_id=role_id).exists():
            return Response(
                {"detail": "该用户已分配此角色"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 创建用户角色关联
        user_role = UserRole(
            user_type=user_type,
            user_id=user_id,
            role_id=role_id,
            is_active=data.get('is_active', True),
            start_date=data.get('start_date'),
            end_date=data.get('end_date')
        )
        user_role.save()
        
        # 清除用户权限缓存
        cache_key = f"rbac_user_permissions_{user_type}_{user_id}"
        cache.delete(cache_key)
        
        # 返回创建的对象
        result_serializer = UserRoleSerializer(user_role)
        return Response(result_serializer.data, status=status.HTTP_201_CREATED)

@extend_schema_view(
    retrieve=extend_schema(
        summary="获取用户角色关联",
        description="获取指定用户与指定角色的关联详情",
        tags=["RBAC系统"]
    ),
    update=extend_schema(
        summary="更新用户角色关联",
        description="更新用户角色关联的属性(如有效期、激活状态)",
        tags=["RBAC系统"]
    ),
    partial_update=extend_schema(
        summary="部分更新用户角色关联",
        description="部分更新用户角色关联的属性",
        tags=["RBAC系统"]
    ),
    destroy=extend_schema(
        summary="从用户移除角色",
        description="从用户中移除指定角色",
        tags=["RBAC系统"]
    )
)
class UserRoleDetailViewSet(mixins.RetrieveModelMixin, 
                           mixins.UpdateModelMixin, 
                           mixins.DestroyModelMixin, 
                           viewsets.GenericViewSet):
    """
    管理特定用户的特定角色
    """
    serializer_class = UserRoleSerializer
    permission_classes = [permissions.IsAuthenticated, RBACPermissionRequired]
    rbac_permissions = {
        'retrieve': 'role:view',
        'update': 'role:assign',
        'partial_update': 'role:assign',
        'destroy': 'role:assign'
    }
    
    def get_object(self):
        """获取用户角色对象"""
        user_type = self.kwargs.get('user_type')
        user_id = self.kwargs.get('user_id')
        role_id = self.kwargs.get('role_id')
        
        obj = get_object_or_404(
            UserRole, 
            user_type=user_type, 
            user_id=user_id, 
            role_id=role_id
        )
        self.check_object_permissions(self.request, obj)
        return obj
    
    def perform_update(self, serializer):
        """更新用户角色关联"""
        instance = serializer.save()
        
        # 刷新用户权限缓存
        cache_key = f"rbac_user_permissions_{instance.user_type}_{instance.user_id}"
        cache.delete(cache_key)
        
        logger.info(f"用户 {self.request.user.username} 更新了 {instance.get_user_type_display()} ID:{instance.user_id} 的角色 {instance.role.name}")
    
    def perform_destroy(self, instance):
        """删除用户角色关联"""
        user_type = instance.user_type
        user_id = instance.user_id
        role_name = instance.role.name
        
        # 删除前先清除缓存
        cache_key = f"rbac_user_permissions_{user_type}_{user_id}"
        cache.delete(cache_key)
        
        instance.delete()
        logger.info(f"用户 {self.request.user.username} 从 {instance.get_user_type_display()} ID:{user_id} 移除了角色 {role_name}")

@extend_schema_view(
    list=extend_schema(
        summary="获取用户权限",
        description="获取指定用户拥有的所有权限",
        tags=["RBAC系统"]
    )
)
class UserPermissionsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    获取用户权限API
    """
    serializer_class = PermissionSerializer
    permission_classes = [permissions.IsAuthenticated, RBACPermissionRequired]
    rbac_permissions = {
        'list': 'permission:view',
    }
    
    def get_queryset(self):
        """获取指定用户的所有权限"""
        user_type = self.kwargs.get('user_type')
        user_id = self.kwargs.get('user_id')
        
        if not user_type or not user_id:
            return Permission.objects.none()
            
        # 获取用户所有有效角色
        current_date = timezone.now().date()
        user_roles = UserRole.objects.filter(
            user_type=user_type,
            user_id=user_id,
            is_active=True
        ).filter(
            # 筛选有效期内的角色
            (
                # 开始日期和结束日期都为空，表示永久有效
                (Q(start_date__isnull=True) & Q(end_date__isnull=True)) |
                # 只有开始日期，表示从开始日期起永久有效
                (Q(start_date__lte=current_date) & Q(end_date__isnull=True)) |
                # 只有结束日期，表示直到结束日期止有效
                (Q(start_date__isnull=True) & Q(end_date__gte=current_date)) |
                # 开始日期和结束日期都有，表示在日期范围内有效
                (Q(start_date__lte=current_date) & Q(end_date__gte=current_date))
            )
        )
        
        # 获取所有角色的权限ID
        role_ids = user_roles.values_list('role_id', flat=True)
        
        # 查询这些角色拥有的所有权限
        permission_ids = RolePermission.objects.filter(
            role_id__in=role_ids
        ).values_list('permission_id', flat=True)
        
        return Permission.objects.filter(id__in=permission_ids)

@extend_schema_view(
    create=extend_schema(
        summary="刷新权限缓存",
        description="刷新所有权限缓存",
        responses={200: CacheRefreshResponseSerializer},
        tags=["RBAC系统"]
    )
)
class CacheRefreshViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    权限缓存刷新API
    """
    permission_classes = [permissions.IsAuthenticated, RBACPermissionRequired]
    rbac_permissions = {
        'create': 'permission:manage',
    }
    serializer_class = CacheRefreshResponseSerializer
    
    @extend_schema(
        summary="刷新所有权限缓存",
        description="刷新系统中所有用户的权限缓存",
        responses={200: CacheRefreshResponseSerializer},
        tags=["RBAC系统"]
    )
    def create(self, request, *args, **kwargs):
        """刷新所有权限缓存"""
        # 清除所有权限缓存
        cache_keys = cache.keys('user_permissions_*')
        if cache_keys:
            cache.delete_many(cache_keys)
        
        # 记录操作
        logger.info(f"用户 {request.user.username} 刷新了所有权限缓存")
        
        return Response({
            'success': True,
            'message': '所有权限缓存已刷新',
            'timestamp': timezone.now().isoformat()
        })

@extend_schema_view(
    create=extend_schema(
        summary="刷新指定用户权限缓存",
        description="刷新指定用户的权限缓存",
        responses={200: CacheRefreshResponseSerializer},
        tags=["RBAC系统"]
    )
)
class UserCacheRefreshViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    指定用户权限缓存刷新API
    """
    permission_classes = [permissions.IsAuthenticated, RBACPermissionRequired]
    rbac_permissions = {
        'create': 'permission:manage',
    }
    serializer_class = CacheRefreshResponseSerializer
    
    @extend_schema(
        summary="刷新指定用户权限缓存",
        description="刷新指定用户的权限缓存",
        responses={200: CacheRefreshResponseSerializer},
        tags=["RBAC系统"]
    )
    def create(self, request, *args, **kwargs):
        """刷新指定用户的权限缓存"""
        user_type = kwargs.get('user_type')
        user_id = kwargs.get('user_id')
        
        # 验证用户类型
        if user_type not in ['user', 'member']:
            return Response(
                {"detail": "无效的用户类型，必须是'user'或'member'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 获取用户
        from users.models import User, Member
        UserModel = User if user_type == 'user' else Member
        
        try:
            user = UserModel.objects.get(id=user_id)
        except UserModel.DoesNotExist:
            return Response(
                {"detail": f"{user_type.capitalize()} ID {user_id} 不存在"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 清除用户权限缓存
        invalidate_permissions_cache(user)
        
        # 记录操作
        logger.info(f"用户 {request.user.username} 刷新了 {user.username} 的权限缓存")
        
        return Response({
            'success': True,
            'message': f'用户 {user.username} 的权限缓存已刷新',
            'timestamp': timezone.now().isoformat()
        })

@extend_schema_view(
    list=extend_schema(
        summary="获取租户角色列表",
        description="获取指定租户的所有角色",
        tags=["RBAC系统"]
    ),
)
class TenantRolesViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    租户角色管理API
    """
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated, RBACPermissionRequired]
    rbac_permissions = {
        'list': 'role:view',
        'create_from_template': 'role:create',
    }
    
    def get_queryset(self):
        """获取指定租户的角色"""
        tenant_id = self.kwargs.get('tenant_id')
        return Role.objects.filter(tenant_id=tenant_id)
    
    @extend_schema(
        summary="从系统角色创建租户角色",
        description="从系统角色模板创建租户特定角色",
        request=TenantRoleCreateFromTemplateSerializer,
        responses={201: RoleSerializer},
        tags=["RBAC系统"]
    )
    @action(detail=False, methods=['post'], url_path='from-template')
    def create_from_template(self, request, tenant_id=None):
        """从系统角色模板创建租户角色"""
        serializer = TenantRoleCreateFromTemplateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        template_role_id = serializer.validated_data['template_role_id']
        
        try:
            template_role = Role.objects.get(id=template_role_id, is_system=True, tenant=None)
        except Role.DoesNotExist:
            return Response(
                {"detail": "系统角色模板不存在"},
                status=status.HTTP_404_NOT_FOUND
            )
            
        from tenants.models import Tenant
        try:
            tenant = Tenant.objects.get(id=tenant_id)
        except Tenant.DoesNotExist:
            return Response(
                {"detail": "租户不存在"},
                status=status.HTTP_404_NOT_FOUND
            )
            
        # 检查是否已存在同名角色
        if Role.objects.filter(name=template_role.name, tenant=tenant).exists():
            return Response(
                {"detail": f"租户已存在名为'{template_role.name}'的角色"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # 创建新角色
        with transaction.atomic():
            new_role = Role.objects.create(
                name=template_role.name,
                code=template_role.code,
                description=template_role.description,
                tenant=tenant,
                is_system=False,
                created_by=request.user
            )
            
            # 复制权限
            template_permissions = template_role.permissions.all()
            for permission in template_permissions:
                RolePermission.objects.create(
                    role=new_role,
                    permission=permission
                )
                
        logger.info(f"用户 {request.user.username} 基于模板 '{template_role.name}' 为租户 '{tenant.name}' 创建了角色 '{new_role.name}'")
        
        serializer = RoleSerializer(new_role)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
