"""
Member 用户打卡系统视图

提供 Member 用户专用的打卡 API：
- MemberThemeViewSet - 主题只读
- MemberTaskViewSet - CRUD 自己的任务
- MemberCheckinViewSet - CRUD 自己的打卡
- MemberCycleViewSet - CRUD 自己的21天周期
"""
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets, permissions, status, filters, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
import logging

from common.viewsets import TenantModelViewSet
from common.pagination import StandardResultsSetPagination
from common.utils.user_permissions import is_member
from users.models import Member
from .models import TaskCategory, Task, CheckRecord, CheckinCycle
from .serializers import (
    TaskCategorySerializer, TaskSerializer,
    CheckRecordSerializer, CheckinCycleSerializer
)

logger = logging.getLogger(__name__)


class MemberPermission(permissions.BasePermission):
    """Member 用户权限"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and is_member(request.user)


@extend_schema_view(
    list=extend_schema(summary="[Member] 获取主题列表", tags=["打卡系统-Member"]),
    retrieve=extend_schema(summary="[Member] 获取主题详情", tags=["打卡系统-Member"]),
)
class MemberThemeViewSet(TenantModelViewSet):
    """
    Member 主题视图集（只读）
    
    Member 可以查看系统预设主题和租户内主题
    """
    queryset = TaskCategory.objects.all()
    serializer_class = TaskCategorySerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [MemberPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_system', 'form_type']
    search_fields = ['name', 'description']
    http_method_names = ['get', 'head', 'options']  # 只读
    
    def get_queryset(self):
        """获取系统预设 + 租户内主题"""
        queryset = super().get_queryset()
        user = self.request.user
        
        if hasattr(user, 'tenant') and user.tenant:
            return queryset.filter(Q(is_system=True) | Q(tenant=user.tenant))
        
        return queryset.filter(is_system=True)


@extend_schema_view(
    list=extend_schema(summary="[Member] 获取我的任务列表", tags=["打卡系统-Member"]),
    retrieve=extend_schema(summary="[Member] 获取任务详情", tags=["打卡系统-Member"]),
    create=extend_schema(summary="[Member] 创建任务", tags=["打卡系统-Member"]),
    update=extend_schema(summary="[Member] 更新任务", tags=["打卡系统-Member"]),
    destroy=extend_schema(summary="[Member] 删除任务", tags=["打卡系统-Member"]),
)
class MemberTaskViewSet(TenantModelViewSet):
    """
    Member 任务视图集
    
    Member 只能操作自己的任务
    """
    queryset = Task.objects.all().select_related('member', 'category')
    serializer_class = TaskSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [MemberPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'status']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'start_date']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """只返回当前 Member 的任务"""
        queryset = super().get_queryset()
        user = self.request.user
        
        if is_member(user):
            return queryset.filter(member=user)
        
        return queryset.none()
    
    def perform_create(self, serializer):
        """创建时自动设置 member"""
        user = self.request.user
        tenant = user.tenant if hasattr(user, 'tenant') else None
        serializer.save(member=user, tenant=tenant)
        logger.info(f"Member {user.username} 创建任务")
    
    def perform_update(self, serializer):
        """更新时验证所有权"""
        instance = self.get_object()
        if instance.member_id != self.request.user.id:
            raise serializers.ValidationError(_("你只能编辑自己的任务"))
        serializer.save()
    
    def perform_destroy(self, instance):
        """删除时验证所有权（软删除）"""
        if instance.member_id != self.request.user.id:
            raise serializers.ValidationError(_("你只能删除自己的任务"))
        instance.soft_delete()


@extend_schema_view(
    list=extend_schema(summary="[Member] 获取我的打卡记录", tags=["打卡系统-Member"]),
    retrieve=extend_schema(summary="[Member] 获取打卡详情", tags=["打卡系统-Member"]),
    create=extend_schema(summary="[Member] 打卡", tags=["打卡系统-Member"]),
    update=extend_schema(summary="[Member] 更新打卡记录", tags=["打卡系统-Member"]),
    destroy=extend_schema(summary="[Member] 删除打卡记录", tags=["打卡系统-Member"]),
)
class MemberCheckinViewSet(TenantModelViewSet):
    """
    Member 打卡记录视图集
    
    Member 只能操作自己的打卡记录
    """
    queryset = CheckRecord.objects.all().select_related('member', 'task', 'theme')
    serializer_class = CheckRecordSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [MemberPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['task', 'theme', 'check_date', 'delayed']
    ordering_fields = ['check_date', 'check_time', 'created_at']
    ordering = ['-check_date', '-check_time']
    
    def get_queryset(self):
        """只返回当前 Member 的打卡记录"""
        queryset = super().get_queryset()
        user = self.request.user
        
        if is_member(user):
            return queryset.filter(member=user)
        
        return queryset.none()
    
    def perform_create(self, serializer):
        """创建时自动设置 member"""
        user = self.request.user
        tenant = user.tenant if hasattr(user, 'tenant') else None
        
        # 验证重复打卡
        task = serializer.validated_data.get('task')
        theme = serializer.validated_data.get('theme')
        check_date = serializer.validated_data.get('check_date')
        
        if task and CheckRecord.objects.filter(member=user, task=task, check_date=check_date).exists():
            raise serializers.ValidationError(_("您今天已经为该任务打过卡了"))
        
        if theme and CheckRecord.objects.filter(member=user, theme=theme, check_date=check_date).exists():
            raise serializers.ValidationError(_("您今天已经为该主题打过卡了"))
        
        serializer.save(member=user, tenant=tenant)
        
        target = task.name if task else (theme.name if theme else "未知")
        logger.info(f"Member {user.username} 打卡: {target}")
    
    def perform_update(self, serializer):
        """更新时验证所有权"""
        instance = self.get_object()
        if instance.member_id != self.request.user.id:
            raise serializers.ValidationError(_("你只能编辑自己的打卡记录"))
        serializer.save()
    
    def perform_destroy(self, instance):
        """删除时验证所有权（软删除）"""
        if instance.member_id != self.request.user.id:
            raise serializers.ValidationError(_("你只能删除自己的打卡记录"))
        instance.soft_delete()
    
    @extend_schema(summary="[Member] 今日打卡状态", tags=["打卡系统-Member"])
    @action(detail=False, methods=['get'])
    def today(self, request):
        """获取今日打卡状态"""
        from datetime import date
        
        today = date.today()
        records = self.get_queryset().filter(check_date=today)
        
        return Response({
            'date': today.isoformat(),
            'total': records.count(),
            'records': CheckRecordSerializer(records, many=True, context={'request': request}).data
        })


@extend_schema_view(
    list=extend_schema(summary="[Member] 获取我的21天周期", tags=["打卡系统-Member"]),
    retrieve=extend_schema(summary="[Member] 获取周期详情", tags=["打卡系统-Member"]),
    create=extend_schema(summary="[Member] 创建新周期", tags=["打卡系统-Member"]),
)
class MemberCycleViewSet(TenantModelViewSet):
    """
    Member 21天周期视图集
    
    Member 只能操作自己的周期
    """
    queryset = CheckinCycle.objects.all().select_related('member')
    serializer_class = CheckinCycleSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [MemberPermission]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['is_active']
    ordering_fields = ['created_at', 'start_date']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """只返回当前 Member 的周期"""
        queryset = super().get_queryset()
        user = self.request.user
        
        if is_member(user):
            return queryset.filter(member=user)
        
        return queryset.none()
    
    def perform_create(self, serializer):
        """创建时自动设置 member"""
        user = self.request.user
        tenant = user.tenant if hasattr(user, 'tenant') else None
        serializer.save(member=user, tenant=tenant)
        logger.info(f"Member {user.username} 创建21天周期")
    
    @extend_schema(summary="[Member] 获取当前活跃周期", tags=["打卡系统-Member"])
    @action(detail=False, methods=['get'])
    def current(self, request):
        """获取当前活跃的周期"""
        cycle = self.get_queryset().filter(is_active=True).first()
        if cycle:
            serializer = self.get_serializer(cycle)
            return Response(serializer.data)
        return Response({'detail': '没有活跃的周期'}, status=status.HTTP_404_NOT_FOUND)
    
    @extend_schema(summary="[Member] 获取周期统计", tags=["打卡系统-Member"])
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """获取周期统计数据"""
        cycle = self.get_object()
        
        # 验证所有权
        if cycle.member_id != request.user.id:
            return Response({'detail': '无权查看'}, status=status.HTTP_403_FORBIDDEN)
        
        # 获取该周期内的打卡记录
        records = CheckRecord.objects.filter(
            member=cycle.member,
            check_date__gte=cycle.start_date,
            check_date__lte=cycle.end_date
        )
        
        return Response({
            'cycle_id': cycle.id,
            'current_day': cycle.get_current_day(),
            'progress': cycle.get_progress(),
            'total_checkins': records.count(),
            'unique_days': records.values('check_date').distinct().count(),
            'themes_completed': records.values('theme').distinct().count(),
            'selected_themes_count': len(cycle.selected_themes) if cycle.selected_themes else 0
        })
