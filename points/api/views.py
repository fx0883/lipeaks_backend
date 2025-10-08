# points/api/views.py
"""
多租户积分系统的API视图集
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import transaction, models
from django.shortcuts import get_object_or_404

from points.models import (
    TenantUserProfile, TenantUserPoints, UserLevel, 
    UserTypeTag, TenantUserTypeTag
)
from points.api.serializers import (
    TenantUserProfileSerializer, TenantUserPointsSerializer,
    UserLevelSerializer, UserTypeTagSerializer, TenantUserTypeTagSerializer,
    PointsOperationSerializer, VipTagGrantSerializer, VipTagRenewalSerializer,
    UserPointsSummarySerializer
)
from points.api.permissions import (
    TenantUserProfilePermission, PointsManagementPermission,
    VipManagementPermission, ReadOnlyOrAdminPermission,
    PointsOperationPermission, ensure_tenant_isolation, get_user_tenant
)
from points.services.points_engine import PointsEngineService
from points.services.permission_service import TenantAwarePermissionService
from points.services.vip_service import VipExpirationService


class UserLevelViewSet(viewsets.ReadOnlyModelViewSet):
    """
    用户等级视图集（只读）
    提供用户等级的查询功能
    """
    
    queryset = UserLevel.objects.filter(is_active=True).order_by('level_order')
    serializer_class = UserLevelSerializer
    permission_classes = [IsAuthenticated, ReadOnlyOrAdminPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'is_default']
    search_fields = ['level_name', 'level_code', 'level_description']
    ordering_fields = ['level_order', 'min_points', 'created_at']
    ordering = ['level_order']


class UserTypeTagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    用户标签视图集（只读）
    提供用户标签的查询功能
    """
    
    queryset = UserTypeTag.objects.filter(is_active=True).order_by('-tag_level', 'tag_name')
    serializer_class = UserTypeTagSerializer
    permission_classes = [IsAuthenticated, ReadOnlyOrAdminPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tag_type', 'is_active', 'is_assignable', 'requires_payment']
    search_fields = ['tag_name', 'tag_code', 'tag_description']
    ordering_fields = ['tag_level', 'tag_name', 'created_at']
    ordering = ['-tag_level', 'tag_name']


class TenantUserProfileViewSet(viewsets.ModelViewSet):
    """
    租户用户档案视图集
    提供用户档案的CRUD操作和积分管理功能
    """
    
    serializer_class = TenantUserProfileSerializer
    permission_classes = [IsAuthenticated, TenantUserProfilePermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tenant', 'current_level', 'is_points_enabled']
    search_fields = ['member__username', 'member__email']
    ordering_fields = ['total_points', 'created_at', 'last_points_update']
    ordering = ['-total_points']
    
    def get_queryset(self):
        """获取查询集，确保租户隔离"""
        queryset = TenantUserProfile.objects.select_related(
            'member', 'tenant', 'current_level'
        ).prefetch_related('user_tags__tag')
        
        return ensure_tenant_isolation(self.request, queryset)
    
    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        """获取用户积分摘要"""
        profile = self.get_object()
        summary = PointsEngineService.get_user_points_summary(
            profile.member, profile.tenant, days=30
        )
        serializer = UserPointsSummarySerializer(summary)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def earn_points(self, request, pk=None):
        """用户获得积分"""
        profile = self.get_object()
        serializer = PointsOperationSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    record = PointsEngineService.earn_points(
                        member=profile.member,
                        tenant=profile.tenant,
                        points_amount=serializer.validated_data['points_amount'],
                        category=serializer.validated_data['category'],
                        subcategory=serializer.validated_data.get('subcategory', ''),
                        reason=serializer.validated_data.get('reason', ''),
                        operator_id=request.user.id,
                        expires_at=serializer.validated_data.get('expires_at'),
                        source_type=serializer.validated_data.get('source_type', 'manual'),
                        source_id=serializer.validated_data.get('source_id')
                    )
                
                return Response({
                    'success': True,
                    'message': f'成功获得 {serializer.validated_data["points_amount"]} 积分',
                    'record_id': record.id,
                    'new_total_points': profile.total_points
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                return Response({
                    'success': False,
                    'message': f'积分操作失败: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def spend_points(self, request, pk=None):
        """用户消费积分"""
        profile = self.get_object()
        serializer = PointsOperationSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    record = PointsEngineService.spend_points(
                        member=profile.member,
                        tenant=profile.tenant,
                        points_amount=serializer.validated_data['points_amount'],
                        category=serializer.validated_data['category'],
                        subcategory=serializer.validated_data.get('subcategory', ''),
                        reason=serializer.validated_data.get('reason', ''),
                        operator_id=request.user.id,
                        source_type=serializer.validated_data.get('source_type', 'manual'),
                        source_id=serializer.validated_data.get('source_id')
                    )
                
                # 刷新档案数据
                profile.refresh_from_db()
                
                return Response({
                    'success': True,
                    'message': f'成功消费 {serializer.validated_data["points_amount"]} 积分',
                    'record_id': record.id,
                    'new_total_points': profile.total_points
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                return Response({
                    'success': False,
                    'message': f'积分操作失败: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def adjust_points(self, request, pk=None):
        """手动调整用户积分"""
        profile = self.get_object()
        serializer = PointsOperationSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    # 调整可以是正数或负数
                    points_amount = serializer.validated_data['points_amount']
                    if request.data.get('is_negative', False):
                        points_amount = -points_amount
                    
                    record = PointsEngineService.adjust_points(
                        member=profile.member,
                        tenant=profile.tenant,
                        points_amount=points_amount,
                        category=serializer.validated_data.get('category', 'manual'),
                        subcategory=serializer.validated_data.get('subcategory', ''),
                        reason=serializer.validated_data.get('reason', ''),
                        operator_id=request.user.id,
                        source_type=serializer.validated_data.get('source_type', 'manual'),
                        source_id=serializer.validated_data.get('source_id')
                    )
                
                # 刷新档案数据
                profile.refresh_from_db()
                
                return Response({
                    'success': True,
                    'message': f'成功调整积分 {points_amount}',
                    'record_id': record.id,
                    'new_total_points': profile.total_points
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                return Response({
                    'success': False,
                    'message': f'积分操作失败: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def permissions(self, request, pk=None):
        """获取用户的有效权限"""
        profile = self.get_object()
        permissions = TenantAwarePermissionService.get_effective_permissions(
            profile.member, profile.tenant
        )
        return Response(permissions)


class TenantUserPointsViewSet(viewsets.ReadOnlyModelViewSet):
    """
    租户用户积分记录视图集（只读）
    提供积分记录的查询功能
    """
    
    serializer_class = TenantUserPointsSerializer
    permission_classes = [IsAuthenticated, PointsManagementPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'tenant', 'point_type', 'category', 'status', 'is_manual',
        'source_type'
    ]
    search_fields = ['operation_reason', 'source_description']
    ordering_fields = ['created_at', 'points', 'expires_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """获取查询集，确保租户隔离"""
        queryset = TenantUserPoints.objects.select_related(
            'tenant_user_profile', 'member', 'tenant'
        )
        
        return ensure_tenant_isolation(self.request, queryset)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """获取积分记录统计摘要"""
        user_tenant = get_user_tenant(request.user)
        if not user_tenant:
            return Response({'error': '无法确定用户租户'}, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = self.get_queryset()
        
        # 按类型统计
        summary = {
            'total_records': queryset.count(),
            'by_type': {},
            'by_category': {},
            'by_status': {},
        }
        
        # 统计各种类型
        for point_type, _ in TenantUserPoints.POINT_TYPE_CHOICES:
            count = queryset.filter(point_type=point_type).count()
            summary['by_type'][point_type] = count
        
        # 统计各种分类
        for category, _ in TenantUserPoints.CATEGORY_CHOICES:
            count = queryset.filter(category=category).count()
            summary['by_category'][category] = count
        
        # 统计各种状态
        for status_val, _ in TenantUserPoints.STATUS_CHOICES:
            count = queryset.filter(status=status_val).count()
            summary['by_status'][status_val] = count
        
        return Response(summary)


class TenantUserTypeTagViewSet(viewsets.ModelViewSet):
    """
    租户用户标签关联视图集
    提供VIP标签的管理功能
    """
    
    serializer_class = TenantUserTypeTagSerializer
    permission_classes = [IsAuthenticated, VipManagementPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'tenant', 'tag', 'status', 'is_active', 'auto_renewal',
        'grant_method'
    ]
    search_fields = ['grant_reason', 'notes']
    ordering_fields = ['granted_at', 'expires_at', 'usage_count']
    ordering = ['-granted_at']
    
    def get_queryset(self):
        """获取查询集，确保租户隔离"""
        queryset = TenantUserTypeTag.objects.select_related(
            'tenant_user_profile', 'tag', 'member', 'tenant'
        )
        
        return ensure_tenant_isolation(self.request, queryset)
    
    @action(detail=False, methods=['post'])
    def grant_vip_tag(self, request):
        """授予VIP标签"""
        serializer = VipTagGrantSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                user_tenant = get_user_tenant(request.user)
                if not user_tenant:
                    return Response({'error': '无法确定用户租户'}, status=status.HTTP_400_BAD_REQUEST)
                
                # 获取目标用户和标签
                member_id = request.data.get('member_id')
                if not member_id:
                    return Response({'error': '缺少 member_id 参数'}, status=status.HTTP_400_BAD_REQUEST)
                
                from users.models import Member
                member = get_object_or_404(Member, id=member_id, tenant=user_tenant)
                tag = get_object_or_404(UserTypeTag, id=serializer.validated_data['tag_id'])
                
                with transaction.atomic():
                    tag_assignment = VipExpirationService.grant_vip_tag(
                        member=member,
                        tenant=user_tenant,
                        tag=tag,
                        duration_days=serializer.validated_data.get('duration_days'),
                        grant_method=serializer.validated_data.get('grant_method', 'manual'),
                        reason=serializer.validated_data.get('reason', ''),
                        operator_id=request.user.id,
                        payment_info=serializer.validated_data.get('payment_info')
                    )
                
                return Response({
                    'success': True,
                    'message': f'成功授予 {tag.tag_name} 标签',
                    'tag_assignment_id': tag_assignment.id,
                    'expires_at': tag_assignment.expires_at
                }, status=status.HTTP_201_CREATED)
                
            except Exception as e:
                return Response({
                    'success': False,
                    'message': f'授予VIP标签失败: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def renew(self, request, pk=None):
        """续期VIP标签"""
        tag_assignment = self.get_object()
        serializer = VipTagRenewalSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    updated_assignment = VipExpirationService.renew_vip_tag(
                        member=tag_assignment.member,
                        tenant=tag_assignment.tenant,
                        tag=tag_assignment.tag,
                        duration_days=serializer.validated_data['duration_days'],
                        renewal_method=serializer.validated_data.get('renewal_method', 'manual'),
                        reason=serializer.validated_data.get('reason', ''),
                        operator_id=request.user.id,
                        payment_info=serializer.validated_data.get('payment_info')
                    )
                
                return Response({
                    'success': True,
                    'message': f'成功续期 {tag_assignment.tag.tag_name} 标签 {serializer.validated_data["duration_days"]} 天',
                    'new_expires_at': updated_assignment.expires_at,
                    'renewal_count': updated_assignment.renewal_count
                }, status=status.HTTP_200_OK)
                
            except Exception as e:
                return Response({
                    'success': False,
                    'message': f'续期VIP标签失败: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        """撤销VIP标签"""
        tag_assignment = self.get_object()
        reason = request.data.get('reason', '管理员撤销')
        
        try:
            with transaction.atomic():
                VipExpirationService.revoke_vip_tag(
                    member=tag_assignment.member,
                    tenant=tag_assignment.tenant,
                    tag=tag_assignment.tag,
                    reason=reason,
                    operator_id=request.user.id
                )
            
            return Response({
                'success': True,
                'message': f'成功撤销 {tag_assignment.tag.tag_name} 标签'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'撤销VIP标签失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """获取VIP标签详细状态"""
        tag_assignment = self.get_object()
        vip_status = tag_assignment.calculate_vip_status()
        
        return Response({
            'tag_assignment_id': tag_assignment.id,
            'tag_name': tag_assignment.tag.tag_name,
            'member': tag_assignment.member.username,
            'vip_status': vip_status,
            'usage_count': tag_assignment.usage_count,
            'renewal_count': tag_assignment.renewal_count,
            'auto_renewal': tag_assignment.auto_renewal,
        })
    
    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """获取即将过期的VIP标签"""
        days = int(request.query_params.get('days', 7))
        user_tenant = get_user_tenant(request.user)
        
        if not user_tenant:
            return Response({'error': '无法确定用户租户'}, status=status.HTTP_400_BAD_REQUEST)
        
        expiring_tags = TenantUserTypeTag.objects.filter(
            tenant=user_tenant,
            is_active=True,
            status='active',
            expires_at__lte=timezone.now() + timezone.timedelta(days=days),
            expires_at__gt=timezone.now()
        ).select_related('tag', 'member')
        
        serializer = TenantUserTypeTagSerializer(expiring_tags, many=True)
        return Response({
            'count': expiring_tags.count(),
            'days': days,
            'expiring_tags': serializer.data
        })


class PointsStatisticsViewSet(viewsets.ViewSet):
    """
    积分统计视图集
    提供各种积分统计数据
    """
    
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        """获取积分统计概览"""
        user_tenant = get_user_tenant(request.user)
        if not user_tenant:
            return Response({'error': '无法确定用户租户'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取租户下的基本统计
        profiles = TenantUserProfile.objects.filter(tenant=user_tenant)
        
        stats = {
            'total_users': profiles.count(),
            'active_users': profiles.filter(is_points_enabled=True).count(),
            'total_points_distributed': sum(p.total_points for p in profiles),
            'average_points_per_user': profiles.aggregate(
                avg_points=models.Avg('total_points')
            )['avg_points'] or 0,
        }
        
        # 按等级统计用户分布
        level_distribution = {}
        for level in UserLevel.objects.filter(is_active=True):
            count = profiles.filter(current_level=level).count()
            level_distribution[level.level_name] = count
        
        stats['level_distribution'] = level_distribution
        
        # VIP标签统计
        active_vip_tags = TenantUserTypeTag.objects.filter(
            tenant=user_tenant,
            is_active=True,
            status__in=['active', 'grace_period']
        )
        
        vip_stats = {}
        for tag_type, _ in UserTypeTag.TAG_TYPE_CHOICES:
            count = active_vip_tags.filter(tag__tag_type=tag_type).count()
            vip_stats[tag_type] = count
        
        stats['vip_distribution'] = vip_stats
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def points_trend(self, request):
        """获取积分趋势数据"""
        user_tenant = get_user_tenant(request.user)
        days = int(request.query_params.get('days', 30))
        
        if not user_tenant:
            return Response({'error': '无法确定用户租户'}, status=status.HTTP_400_BAD_REQUEST)
        
        from django.db.models import Sum, Count
        from django.utils import timezone
        import datetime
        
        # 获取指定天数内的积分变化趋势
        end_date = timezone.now()
        start_date = end_date - datetime.timedelta(days=days)
        
        points_records = TenantUserPoints.objects.filter(
            tenant=user_tenant,
            created_at__gte=start_date,
            created_at__lte=end_date
        )
        
        # 按天统计
        daily_stats = []
        for i in range(days):
            day = start_date + datetime.timedelta(days=i)
            day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + datetime.timedelta(days=1)
            
            day_records = points_records.filter(
                created_at__gte=day_start,
                created_at__lt=day_end
            )
            
            earned = day_records.filter(point_type='earn').aggregate(
                total=Sum('points')
            )['total'] or 0
            
            spent = abs(day_records.filter(point_type='spend').aggregate(
                total=Sum('points')
            )['total'] or 0)
            
            daily_stats.append({
                'date': day.date().isoformat(),
                'earned': earned,
                'spent': spent,
                'net': earned - spent,
                'record_count': day_records.count()
            })
        
        return Response({
            'period_days': days,
            'start_date': start_date.date().isoformat(),
            'end_date': end_date.date().isoformat(),
            'daily_stats': daily_stats
        })
