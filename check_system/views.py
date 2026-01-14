"""
打卡系统视图

租户隔离架构：
- TaskCategory/TaskTemplate: 租户管理员 CRUD，Member 只读
- Task/CheckRecord/CheckinCycle: Member CRUD 自己的数据
"""
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
import logging

from common.pagination import StandardResultsSetPagination
from common.authentication.api_auth import APIJWTAuthentication
from common.viewsets import TenantModelViewSet
from users.models import Member
from .models import TaskCategory, Task, CheckRecord, TaskTemplate, CheckinCycle
from .serializers import (
    TaskCategorySerializer, TaskSerializer, 
    CheckRecordSerializer, TaskTemplateSerializer, CheckinCycleSerializer
)

logger = logging.getLogger(__name__)


class IsTenantAdmin(permissions.BasePermission):
    """租户管理员权限"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff


class IsMemberUser(permissions.BasePermission):
    """Member用户权限"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and isinstance(request.user, Member)


class TenantAdminOrMemberReadOnly(permissions.BasePermission):
    """租户管理员可写，Member只读"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        # 安全方法（GET, HEAD, OPTIONS）
        if request.method in permissions.SAFE_METHODS:
            return True
        # 写操作需要租户管理员权限
        return request.user.is_staff


class IsTenantAdminOnly(permissions.BasePermission):
    """仅租户管理员权限"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_staff


@extend_schema_view(
    list=extend_schema(summary="获取打卡类型列表", tags=["打卡系统-类型管理"]),
    retrieve=extend_schema(summary="获取打卡类型详情", tags=["打卡系统-类型管理"]),
    create=extend_schema(summary="创建打卡类型（租户管理员）", tags=["打卡系统-类型管理"]),
    update=extend_schema(summary="更新打卡类型（租户管理员）", tags=["打卡系统-类型管理"]),
    destroy=extend_schema(summary="删除打卡类型（租户管理员）", tags=["打卡系统-类型管理"]),
)
class TaskCategoryViewSet(TenantModelViewSet):
    """
    打卡类型视图集
    
    - 租户管理员：CRUD
    - Member：只读（系统预设 + 租户内类型）
    """
    queryset = TaskCategory.objects.all()
    serializer_class = TaskCategorySerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_system']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'sort_order']
    ordering = ['sort_order', '-created_at']
    authentication_classes = [APIJWTAuthentication]
    permission_classes = [TenantAdminOrMemberReadOnly]
    
    def get_queryset(self):
        """获取查询集：系统预设 + 租户内类型"""
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.is_superuser:
            return queryset
        
        # 系统预设 + 当前租户的类型
        if hasattr(user, 'tenant') and user.tenant:
            return queryset.filter(Q(is_system=True) | Q(tenant=user.tenant))
        
        return queryset.filter(is_system=True)
    
    def perform_create(self, serializer):
        """创建时自动设置租户"""
        user = self.request.user
        tenant = user.tenant if hasattr(user, 'tenant') else None
        serializer.save(tenant=tenant)
        logger.info(f"租户管理员 {user.username} 创建类型")


@extend_schema_view(
    list=extend_schema(summary="获取打卡任务列表", tags=["打卡系统-任务管理"]),
    retrieve=extend_schema(summary="获取打卡任务详情", tags=["打卡系统-任务管理"]),
    create=extend_schema(summary="创建打卡任务", tags=["打卡系统-任务管理"]),
    update=extend_schema(summary="更新打卡任务", tags=["打卡系统-任务管理"]),
    destroy=extend_schema(summary="删除打卡任务", tags=["打卡系统-任务管理"]),
)
class TaskViewSet(TenantModelViewSet):
    """
    打卡任务视图集
    
    - Member：CRUD 自己的任务
    - 租户管理员：读取租户内所有任务
    """
    queryset = Task.objects.all().select_related('member', 'category')
    serializer_class = TaskSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'status']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'start_date']
    ordering = ['-created_at']
    authentication_classes = [APIJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """获取查询集"""
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.is_superuser:
            return queryset
        
        # 租户管理员：租户内所有任务
        if user.is_staff and hasattr(user, 'tenant') and user.tenant:
            return queryset.filter(tenant=user.tenant)
        
        # Member：只看自己的任务
        if isinstance(user, Member):
            return queryset.filter(member=user)
        
        return queryset.none()
    
    def perform_create(self, serializer):
        """创建时自动设置 member 和 tenant"""
        user = self.request.user
        if not isinstance(user, Member):
            raise permissions.PermissionDenied(_("只有Member用户可以创建任务"))
        
        tenant = user.tenant if hasattr(user, 'tenant') else None
        serializer.save(member=user, tenant=tenant)
        logger.info(f"成员 {user.username} 创建任务")


@extend_schema_view(
    list=extend_schema(summary="获取打卡记录列表", tags=["打卡系统-打卡记录"]),
    retrieve=extend_schema(summary="获取打卡记录详情", tags=["打卡系统-打卡记录"]),
    create=extend_schema(summary="创建打卡记录", tags=["打卡系统-打卡记录"]),
    update=extend_schema(summary="更新打卡记录", tags=["打卡系统-打卡记录"]),
    destroy=extend_schema(summary="删除打卡记录", tags=["打卡系统-打卡记录"]),
)
class CheckRecordViewSet(TenantModelViewSet):
    """
    打卡记录视图集
    
    - Member：CRUD 自己的打卡记录
    - 租户管理员：读取租户内所有记录
    """
    queryset = CheckRecord.objects.all().select_related('member', 'task', 'theme')
    serializer_class = CheckRecordSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['task', 'theme', 'check_date']
    ordering_fields = ['check_date', 'check_time', 'created_at']
    ordering = ['-check_date', '-check_time']
    authentication_classes = [APIJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """获取查询集"""
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.is_superuser:
            return queryset
        
        # 租户管理员：租户内所有记录
        if user.is_staff and hasattr(user, 'tenant') and user.tenant:
            return queryset.filter(tenant=user.tenant)
        
        # Member：只看自己的记录
        if isinstance(user, Member):
            return queryset.filter(member=user)
        
        return queryset.none()
    
    def perform_create(self, serializer):
        """创建时自动设置 member 和 tenant"""
        user = self.request.user
        if not isinstance(user, Member):
            raise permissions.PermissionDenied(_("只有Member用户可以打卡"))
        
        tenant = user.tenant if hasattr(user, 'tenant') else None
        serializer.save(member=user, tenant=tenant)
        
        target = serializer.validated_data.get('task') or serializer.validated_data.get('theme')
        target_name = target.name if target else "未知"
        logger.info(f"成员 {user.username} 打卡: {target_name}")


@extend_schema_view(
    list=extend_schema(summary="获取任务模板列表", tags=["打卡系统-模板管理"]),
    retrieve=extend_schema(summary="获取任务模板详情", tags=["打卡系统-模板管理"]),
    create=extend_schema(summary="创建任务模板（租户管理员）", tags=["打卡系统-模板管理"]),
    update=extend_schema(summary="更新任务模板（租户管理员）", tags=["打卡系统-模板管理"]),
    destroy=extend_schema(summary="删除任务模板（租户管理员）", tags=["打卡系统-模板管理"]),
)
class TaskTemplateViewSet(TenantModelViewSet):
    """
    任务模板视图集
    
    - 租户管理员：CRUD
    - Member：只读
    """
    queryset = TaskTemplate.objects.all().select_related('category')
    serializer_class = TaskTemplateSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_system', 'category']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    authentication_classes = [APIJWTAuthentication]
    permission_classes = [TenantAdminOrMemberReadOnly]
    
    def get_queryset(self):
        """获取查询集：系统预设 + 租户内模板"""
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.is_superuser:
            return queryset
        
        if hasattr(user, 'tenant') and user.tenant:
            return queryset.filter(Q(is_system=True) | Q(tenant=user.tenant))
        
        return queryset.filter(is_system=True)
    
    def perform_create(self, serializer):
        """创建时自动设置租户"""
        user = self.request.user
        tenant = user.tenant if hasattr(user, 'tenant') else None
        serializer.save(tenant=tenant)
        logger.info(f"租户管理员 {user.username} 创建模板")


@extend_schema_view(
    list=extend_schema(summary="获取打卡周期列表", tags=["打卡系统-21天周期"]),
    retrieve=extend_schema(summary="获取周期详情", tags=["打卡系统-21天周期"]),
    create=extend_schema(summary="创建新周期", tags=["打卡系统-21天周期"]),
)
class CheckinCycleViewSet(TenantModelViewSet):
    """
    21天打卡周期视图集
    
    - Member：CRUD 自己的周期
    - 租户管理员：读取租户内所有周期
    """
    queryset = CheckinCycle.objects.all().select_related('member')
    serializer_class = CheckinCycleSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['is_active']
    ordering_fields = ['created_at', 'start_date']
    ordering = ['-created_at']
    authentication_classes = [APIJWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """获取查询集"""
        queryset = super().get_queryset()
        user = self.request.user
        
        if user.is_superuser:
            return queryset
        
        # 租户管理员：租户内所有周期
        if user.is_staff and hasattr(user, 'tenant') and user.tenant:
            return queryset.filter(tenant=user.tenant)
        
        # Member：只看自己的周期
        if isinstance(user, Member):
            return queryset.filter(member=user)
        
        return queryset.none()
    
    def perform_create(self, serializer):
        """创建时自动设置 member 和 tenant"""
        user = self.request.user
        if not isinstance(user, Member):
            raise permissions.PermissionDenied(_("只有Member用户可以创建打卡周期"))
        
        tenant = user.tenant if hasattr(user, 'tenant') else None
        serializer.save(member=user, tenant=tenant)
        logger.info(f"成员 {user.username} 创建21天打卡周期")
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """获取当前活跃的周期"""
        cycle = self.get_queryset().filter(is_active=True).first()
        if cycle:
            serializer = self.get_serializer(cycle)
            return Response(serializer.data)
        return Response({'detail': '没有活跃的周期'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """获取周期统计数据"""
        cycle = self.get_object()
        
        # 获取该周期内的所有打卡记录
        records = CheckRecord.objects.filter(
            member=cycle.member,
            check_date__gte=cycle.start_date,
            check_date__lte=cycle.end_date
        )
        
        # 统计数据
        total_checkins = records.count()
        unique_days = records.values('check_date').distinct().count()
        themes_completed = records.values('theme').distinct().count()
        
        return Response({
            'cycle_id': cycle.id,
            'current_day': cycle.get_current_day(),
            'progress': cycle.get_progress(),
            'total_checkins': total_checkins,
            'unique_days': unique_days,
            'themes_completed': themes_completed,
            'selected_themes_count': len(cycle.selected_themes) if cycle.selected_themes else 0
        })
