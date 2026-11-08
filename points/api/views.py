# points/api/views.py
"""
多租户积分系统的API视图集
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from django.utils import timezone
from django.db import transaction, models
from django.shortcuts import get_object_or_404
from common.viewsets import TenantModelViewSet

from points.models import (
    TenantUserProfile, TenantUserPoints, UserLevel, 
    UserTypeTag, TenantUserTypeTag, ApplicationUserLevel,
    AppUserPointsAccount, CheckinConfig, UserCheckinStreak,
    UserCheckinRecord
)
from points.api.serializers import (
    TenantUserProfileSerializer, TenantUserPointsSerializer,
    UserLevelSerializer, UserTypeTagSerializer, TenantUserTypeTagSerializer,
    PointsOperationSerializer, VipTagGrantSerializer, VipTagRenewalSerializer,
    UserPointsSummarySerializer, ApplicationUserLevelSerializer,
    AppUserPointsAccountSerializer, AppPointsAdjustSerializer,
    CheckinConfigSerializer, UserCheckinRecordSerializer,
    UserCheckinStreakSerializer, CheckinExecuteSerializer,
    CheckinRecheckinSerializer
)
from common.exceptions import PointsException
from points.services.checkin_service import CheckinService
from points.api.permissions import (
    TenantUserProfilePermission, PointsManagementPermission,
    VipManagementPermission, ReadOnlyOrAdminPermission,
    PointsOperationPermission, get_user_tenant, ensure_tenant_isolation
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


class TenantUserProfileViewSet(TenantModelViewSet):
    """
    租户用户档案视图集
    提供用户档案的CRUD操作和积分管理功能
    
    继承TenantModelViewSet自动处理租户过滤、设置和验证
    """
    queryset = TenantUserProfile.objects.select_related(
        'member', 'tenant', 'current_level'
    ).prefetch_related('user_tags__tag')
    serializer_class = TenantUserProfileSerializer
    permission_classes = [IsAuthenticated, TenantUserProfilePermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tenant', 'current_level', 'is_points_enabled']
    search_fields = ['member__username', 'member__email']
    ordering_fields = ['total_points', 'created_at', 'last_points_update']
    ordering = ['-total_points']
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """获取当前登录成员自身的平台积分画像与等级"""
        user = request.user
        from users.models import Member
        if not isinstance(user, Member):
            return Response({'error': '仅成员可直接获取自身积分档案'}, status=status.HTTP_400_BAD_REQUEST)
        tenant = getattr(request, 'tenant', None) or get_user_tenant(user)
        profile, _ = TenantUserProfile.objects.get_or_create(
            tenant=tenant,
            member=user,
            defaults={'is_points_enabled': True}
        )
        serializer = self.get_serializer(profile)
        return Response(serializer.data)

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
        # Swagger文档生成时返回空queryset
        if getattr(self, 'swagger_fake_view', False):
            return TenantUserPoints.objects.none()
        
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


class TenantUserTypeTagViewSet(TenantModelViewSet):
    """
    租户用户标签关联视图集
    提供VIP标签的管理功能
    
    继承TenantModelViewSet自动处理租户过滤、设置和验证
    """
    queryset = TenantUserTypeTag.objects.select_related(
        'tenant_user_profile', 'tag', 'member', 'tenant'
    )
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
    serializer_class = None  # ViewSet返回动态数据，使用extend_schema定义响应
    
    @extend_schema(
        tags=['Points System'],
        summary='Get points statistics overview',
        responses={200: {
            'type': 'object',
            'properties': {
                'total_users': {'type': 'integer'},
                'active_users': {'type': 'integer'},
                'total_points_distributed': {'type': 'number'},
                'average_points_per_user': {'type': 'number'},
                'level_distribution': {'type': 'object'},
                'vip_distribution': {'type': 'object'},
            }
        }}
    )
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


class ApplicationUserLevelViewSet(TenantModelViewSet):
    """
    应用专属积分等级视图集
    提供应用层级积分阶梯的完整CRUD和预置图标/图标上传服务
    """
    queryset = ApplicationUserLevel.objects.select_related('tenant', 'application')
    serializer_class = ApplicationUserLevelSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['application', 'is_active', 'is_default']
    search_fields = ['level_name', 'level_code', 'level_description']
    ordering_fields = ['level_order', 'min_points', 'created_at']
    ordering = ['level_order']

    @action(detail=False, methods=['get'])
    def preset_icons(self, request):
        """获取系统预置的等级徽章图标"""
        import os
        from django.conf import settings
        images_dir = os.path.join(settings.MEDIA_ROOT, 'application', 'images')
        preset_names = {
            'level_bronze.png': '青铜勋章',
            'level_silver.png': '白银勋章',
            'level_gold.png': '黄金勋章',
            'level_platinum.png': '铂金勋章',
            'level_diamond.png': '钻石勋章',
            'level_crown.png': '王者皇冠',
        }
        order_map = {
            'level_bronze.png': 1,
            'level_silver.png': 2,
            'level_gold.png': 3,
            'level_platinum.png': 4,
            'level_diamond.png': 5,
            'level_crown.png': 6,
        }
        icons = []
        if os.path.exists(images_dir):
            for filename in os.listdir(images_dir):
                if filename.endswith(('.png', '.jpg', '.jpeg', '.svg', '.webp')) and not filename.startswith('.'):
                    icons.append({
                        'filename': filename,
                        'name': preset_names.get(filename, filename),
                        'relative_path': f"application/images/{filename}",
                        'url': request.build_absolute_uri(f"/media/application/images/{filename}")
                    })
        icons.sort(key=lambda x: order_map.get(x['filename'], 99))
        return Response(icons)

    @action(detail=False, methods=['post'])
    def upload_icon(self, request):
        """上传自定义等级图标"""
        import os, uuid
        from django.conf import settings
        from django.core.files.storage import default_storage
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': '未提供文件'}, status=status.HTTP_400_BAD_REQUEST)
        
        ext = os.path.splitext(file_obj.name)[1].lower()
        if ext not in ['.png', '.jpg', '.jpeg', '.svg', '.webp']:
            return Response({'error': '仅支持 png, jpg, jpeg, svg, webp 格式图片'}, status=status.HTTP_400_BAD_REQUEST)
        
        filename = f"custom_{uuid.uuid4().hex[:10]}{ext}"
        rel_path = f"application/images/uploads/{filename}"
        saved_path = default_storage.save(rel_path, file_obj)
        url = request.build_absolute_uri(f"/media/{saved_path}")
        return Response({'success': True, 'path': saved_path, 'url': url})


class AppUserPointsAccountViewSet(TenantModelViewSet):
    """
    应用用户积分账户视图集
    提供各应用下独立积分账户的查询、调账与流水追踪
    """
    queryset = AppUserPointsAccount.objects.select_related(
        'tenant', 'application', 'member', 'current_level', 'tenant_user_profile'
    )
    serializer_class = AppUserPointsAccountSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['application', 'member', 'is_enabled', 'current_level']
    search_fields = ['member__username', 'member__email', 'application__name']
    ordering_fields = ['total_points', 'available_points', 'created_at', 'last_points_update']
    ordering = ['-total_points']

    def get_queryset(self):
        qs = super().get_queryset()
        user = getattr(self.request, 'user', None)
        if user and user.is_authenticated:
            from users.models import Member
            if isinstance(user, Member):
                qs = qs.filter(member=user)
        return qs

    @action(detail=False, methods=['get'])
    def me(self, request):
        """当前成员获取自身应用积分账户（支持传 ?application_id= 获取指定应用账户）"""
        user = request.user
        from users.models import Member
        if not isinstance(user, Member):
            return Response({'error': '仅成员可直接获取自身应用积分账户'}, status=status.HTTP_400_BAD_REQUEST)
        app_id = request.query_params.get('application_id')
        tenant = getattr(request, 'tenant', None) or get_user_tenant(user)

        if app_id:
            from applications.models import Application
            app = get_object_or_404(Application, id=app_id, tenant=tenant)
            profile, _ = TenantUserProfile.objects.get_or_create(
                tenant=tenant, member=user, defaults={'is_points_enabled': True}
            )
            account, _ = AppUserPointsAccount.objects.get_or_create(
                tenant=tenant,
                application=app,
                member=user,
                defaults={
                    'tenant_user_profile': profile,
                    'is_enabled': True,
                    'available_points': 0,
                    'total_points': 0
                }
            )
            serializer = self.get_serializer(account)
            return Response(serializer.data)
        else:
            accounts = AppUserPointsAccount.objects.filter(tenant=tenant, member=user)
            serializer = self.get_serializer(accounts, many=True)
            return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_records(self, request):
        """当前成员获取自身应用积分变动明细台账流水"""
        user = request.user
        from users.models import Member
        if not isinstance(user, Member):
            return Response({'error': '仅成员可直接获取自身积分明细流水'}, status=status.HTTP_400_BAD_REQUEST)
        app_id = request.query_params.get('application_id')
        tenant = getattr(request, 'tenant', None) or get_user_tenant(user)
        qs = TenantUserPoints.objects.filter(tenant=tenant, member=user)
        if app_id:
            qs = qs.filter(application_id=app_id)
        qs = qs.order_by('-created_at')

        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = TenantUserPointsSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = TenantUserPointsSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def adjust(self, request, pk=None):
        """管理员对特定应用积分账户进行调账"""
        account = self.get_object()
        serializer = AppPointsAdjustSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        points = serializer.validated_data['points']
        reason = serializer.validated_data.get('reason', '管理员调账')
        category = serializer.validated_data.get('category', 'manual')

        if points == 0:
            return Response({'error': '调账积分不能为0'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # 锁定子账户行
            acct = AppUserPointsAccount.objects.select_for_update().get(id=account.id)
            if points < 0 and acct.available_points < abs(points):
                return Response({
                    'error': f'可用积分不足，当前可用: {acct.available_points}，需要扣减: {abs(points)}'
                }, status=status.HTTP_400_BAD_REQUEST)

            balance_before = acct.available_points
            balance_after = balance_before + points

            if points > 0:
                acct.total_points += points
                acct.available_points += points
                acct.points_earned_total += points
            else:
                acct.available_points += points  # points is negative
                acct.points_spent_total += abs(points)

            acct.last_points_update = timezone.now()
            acct.save()

            # 检查等级变动
            acct.check_level_upgrade()

            # 记录台账流水
            record = TenantUserPoints.objects.create(
                tenant_user_profile=acct.tenant_user_profile,
                tenant=acct.tenant,
                member=acct.member,
                application=acct.application,
                app_account=acct,
                point_type='adjust' if category == 'manual' else ('earn' if points > 0 else 'spend'),
                category=category,
                points=points,
                balance_before=balance_before,
                balance_after=balance_after,
                operation_reason=reason,
                operator_id=request.user.id,
                source_type='manual'
            )

        return Response({
            'success': True,
            'message': f'成功调账 {points} 积分',
            'available_points': acct.available_points,
            'total_points': acct.total_points,
            'current_level_name': acct.current_level.level_name if acct.current_level else '无等级',
            'account': AppUserPointsAccountSerializer(acct, context={'request': request}).data
        })

    @action(detail=True, methods=['get'])
    def records(self, request, pk=None):
        """获取该应用账户的流水明细"""
        account = self.get_object()
        records = TenantUserPoints.objects.filter(
            app_account=account
        ).order_by('-created_at')

        page = self.paginate_queryset(records)
        if page is not None:
            serializer = TenantUserPointsSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = TenantUserPointsSerializer(records, many=True, context={'request': request})
        return Response(serializer.data)


class CheckinConfigViewSet(TenantModelViewSet):
    """
    签到规则配置视图集
    提供签到规则的CRUD及默认阶梯查询
    """
    queryset = CheckinConfig.objects.select_related('tenant', 'application')
    serializer_class = CheckinConfigSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['application', 'is_active', 'cycle_mode']
    search_fields = ['name', 'application__name']
    ordering_fields = ['created_at', 'updated_at', 'cycle_days']
    ordering = ['-created_at']

    @action(detail=False, methods=['get'])
    def default_ladder(self, request):
        """获取系统默认的7天递增阶梯配置"""
        return Response(CheckinConfig.get_default_ladder())


class UserCheckinStreakViewSet(TenantModelViewSet):
    """
    用户连续签到统计视图集（管理后台专用）
    提供按租户与应用筛选的用户连续签到统计列表与详情
    """
    queryset = UserCheckinStreak.objects.select_related('tenant', 'application', 'member')
    serializer_class = UserCheckinStreakSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['application']
    search_fields = ['member__username', 'member__email', 'application__name']
    ordering_fields = ['current_streak', 'max_streak', 'total_days', 'last_checkin_date', 'created_at']
    ordering = ['-last_checkin_date', '-current_streak']


class UserCheckinRecordViewSet(TenantModelViewSet):
    """
    用户签到流水明细视图集（管理后台专用）
    提供按租户与应用筛选的实际打卡流水与补签记录
    """
    queryset = UserCheckinRecord.objects.select_related('tenant', 'application', 'member')
    serializer_class = UserCheckinRecordSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['application', 'is_recheckin', 'checkin_date']
    search_fields = ['member__username', 'member__email', 'application__name']
    ordering_fields = ['checkin_date', 'streak_day', 'reward_points', 'created_at']
    ordering = ['-checkin_date', '-created_at']


class MemberCheckinViewSet(viewsets.ViewSet):
    """
    用户/成员每日签到操作接口
    """
    permission_classes = [IsAuthenticated]

    def _get_tenant(self, request):
        return getattr(request, 'tenant', None) or get_user_tenant(request.user)

    def _resolve_application(self, request):
        app_id = None
        if hasattr(request, 'query_params') and request.query_params.get('application_id'):
            app_id = request.query_params.get('application_id')
        elif hasattr(request, 'data') and hasattr(request.data, 'get'):
            app_id = request.data.get('application_id')

        if not app_id:
            return None
        from applications.models import Application
        from rest_framework.exceptions import ValidationError
        tenant = self._get_tenant(request)
        try:
            if tenant:
                return Application.objects.get(id=int(app_id), tenant=tenant)
            return Application.objects.get(id=int(app_id))
        except (Application.DoesNotExist, ValueError):
            raise ValidationError({'application_id': f'ID 为 {app_id} 的应用不存在或无权访问'})

    @action(detail=False, methods=['get'])
    def status(self, request):
        """查询签到状态与打卡日历"""
        app = self._resolve_application(request)
        tenant = self._get_tenant(request)
        status_data = CheckinService.get_checkin_status(
            member=request.user,
            tenant=tenant,
            application=app
        )
        return Response(status_data)

    @action(detail=False, methods=['post'])
    def execute(self, request):
        """执行每日打卡签到"""
        app = self._resolve_application(request)
        tenant = self._get_tenant(request)
        try:
            result = CheckinService.execute_checkin(
                member=request.user,
                tenant=tenant,
                application=app
            )
            return Response(result)
        except PointsException as e:
            return Response({
                'success': False,
                'error_code': e.error_code,
                'message': e.detail
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def recheckin(self, request):
        """执行补签打卡"""
        serializer = CheckinRecheckinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        app = self._resolve_application(request)
        tenant = self._get_tenant(request)
        target_date = serializer.validated_data['target_date']
        try:
            result = CheckinService.execute_recheckin(
                member=request.user,
                tenant=tenant,
                target_date=target_date,
                application=app
            )
            return Response(result)
        except PointsException as e:
            return Response({
                'success': False,
                'error_code': e.error_code,
                'message': e.detail
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def records(self, request):
        """查询用户签到历史明细"""
        app = self._resolve_application(request)
        tenant = self._get_tenant(request)
        qs = UserCheckinRecord.objects.filter(
            member=request.user
        )
        if tenant:
            qs = qs.filter(tenant=tenant)
        if app:
            qs = qs.filter(application=app)
        qs = qs.order_by('-checkin_date', '-created_at')

        from rest_framework.pagination import PageNumberPagination
        paginator = PageNumberPagination()
        page = paginator.paginate_queryset(qs, request)
        if page is not None:
            serializer = UserCheckinRecordSerializer(page, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)

        serializer = UserCheckinRecordSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data)



