# licenses/views/assignment_views.py
"""
许可证分配管理API视图
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import transaction
from django.shortcuts import get_object_or_404

from licenses.models import LicenseAssignment, License
from licenses.serializers import (
    LicenseAssignmentSerializer, LicenseAssignmentCreateSerializer
)
from points.api.permissions import (
    LicenseAssignmentPermission, ensure_tenant_isolation, get_user_tenant
)
from points.services.license_service import TenantAwareLicenseAssignmentService


class LicenseAssignmentViewSet(viewsets.ModelViewSet):
    """
    许可证分配视图集
    提供许可证分配的CRUD操作和管理功能
    """
    
    permission_classes = [IsAuthenticated, LicenseAssignmentPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'tenant', 'license', 'member', 'assignment_type', 'status',
        'is_primary', 'can_activate', 'priority'
    ]
    search_fields = ['assignment_reason', 'revoke_reason']
    ordering_fields = ['assigned_at', 'expires_at', 'usage_count', 'last_used_at']
    ordering = ['-assigned_at']
    
    def get_queryset(self):
        """获取查询集，确保租户隔离"""
        queryset = LicenseAssignment.objects.select_related(
            'member', 'license', 'tenant', 'assigned_by', 'revoked_by'
        ).prefetch_related('license__product', 'license__plan')
        
        return ensure_tenant_isolation(self.request, queryset)
    
    def get_serializer_class(self):
        """根据动作返回不同的序列化器"""
        if self.action == 'create':
            return LicenseAssignmentCreateSerializer
        return LicenseAssignmentSerializer
    
    def perform_create(self, serializer):
        """创建许可证分配时的额外处理"""
        with transaction.atomic():
            # 使用服务层创建分配
            assignment = TenantAwareLicenseAssignmentService.assign_license_to_member(
                member=serializer.validated_data['member'],
                license=serializer.validated_data['license'],
                assignment_type=serializer.validated_data.get('assignment_type', 'direct'),
                reason=serializer.validated_data.get('assignment_reason', ''),
                operator=self.request.user,
                **{k: v for k, v in serializer.validated_data.items() 
                   if k not in ['member', 'license', 'assignment_type', 'assignment_reason']}
            )
            
            return assignment
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """激活许可证分配"""
        assignment = self.get_object()
        
        if assignment.status != 'active':
            return Response({
                'success': False,
                'message': '只能激活处于活跃状态的分配'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if assignment.activated_at:
            return Response({
                'success': False,
                'message': '该分配已经激活'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                success = assignment.activate()
                
                if success:
                    return Response({
                        'success': True,
                        'message': '许可证分配激活成功',
                        'activated_at': assignment.activated_at
                    })
                else:
                    return Response({
                        'success': False,
                        'message': '激活失败，可能是配额不足'
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
        except Exception as e:
            return Response({
                'success': False,
                'message': f'激活失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        """撤销许可证分配"""
        assignment = self.get_object()
        reason = request.data.get('reason', '管理员撤销')
        
        try:
            with transaction.atomic():
                TenantAwareLicenseAssignmentService.revoke_license_from_member(
                    assignment=assignment,
                    reason=reason,
                    operator=request.user
                )
                
                return Response({
                    'success': True,
                    'message': '许可证分配撤销成功',
                    'revoked_at': assignment.revoked_at
                })
                
        except Exception as e:
            return Response({
                'success': False,
                'message': f'撤销失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def record_usage(self, request, pk=None):
        """记录使用情况"""
        assignment = self.get_object()
        
        if assignment.status != 'active':
            return Response({
                'success': False,
                'message': '只能记录活跃分配的使用情况'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            assignment.record_usage()
            
            return Response({
                'success': True,
                'message': '使用情况记录成功',
                'usage_count': assignment.usage_count,
                'last_used_at': assignment.last_used_at,
                'last_heartbeat': assignment.last_heartbeat
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'message': f'记录使用情况失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def permissions(self, request, pk=None):
        """获取分配的有效权限"""
        assignment = self.get_object()
        permissions = assignment.get_effective_permissions()
        
        return Response({
            'assignment_id': assignment.id,
            'member': assignment.member.username,
            'license_key': assignment.license.license_key[-8:] if assignment.license.license_key else None,
            'effective_permissions': permissions
        })
    
    @action(detail=False, methods=['get'])
    def my_assignments(self, request):
        """获取current用户的所有许可证分配"""
        # 这个端点允许Member用户查看自己的分配
        if hasattr(request.user, 'license_assignments'):
            assignments = request.user.license_assignments.filter(
                status__in=['active', 'suspended']
            ).select_related('license', 'tenant')
        else:
            assignments = LicenseAssignment.objects.none()
        
        serializer = LicenseAssignmentSerializer(assignments, many=True)
        return Response({
            'count': assignments.count(),
            'assignments': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """获取即将过期的许可证分配"""
        days = int(request.query_params.get('days', 30))
        user_tenant = get_user_tenant(request.user)
        
        if not user_tenant:
            return Response({'error': '无法确定用户租户'}, status=status.HTTP_400_BAD_REQUEST)
        
        expiring_assignments = LicenseAssignment.objects.filter(
            tenant=user_tenant,
            status='active',
            expires_at__lte=timezone.now() + timezone.timedelta(days=days),
            expires_at__gt=timezone.now()
        ).select_related('member', 'license')
        
        serializer = LicenseAssignmentSerializer(expiring_assignments, many=True)
        return Response({
            'count': expiring_assignments.count(),
            'days': days,
            'expiring_assignments': serializer.data
        })
    
    @action(detail=False, methods=['post'])
    def batch_assign(self, request):
        """批量分配许可证"""
        from licenses.serializers import LicenseAssignmentBatchSerializer
        
        serializer = LicenseAssignmentBatchSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    assignments = []
                    license_obj = serializer.validated_data['license']
                    members = serializer.validated_data['members']
                    
                    for member in members:
                        assignment = TenantAwareLicenseAssignmentService.assign_license_to_member(
                            member=member,
                            license=license_obj,
                            assignment_type=serializer.validated_data.get('assignment_type', 'direct'),
                            reason=serializer.validated_data.get('assignment_reason', '批量分配'),
                            operator=request.user,
                            expires_at=serializer.validated_data.get('expires_at')
                        )
                        assignments.append(assignment)
                    
                    return Response({
                        'success': True,
                        'message': f'成功批量分配 {len(assignments)} 个许可证',
                        'assignment_ids': [a.id for a in assignments]
                    }, status=status.HTTP_201_CREATED)
                    
            except Exception as e:
                return Response({
                    'success': False,
                    'message': f'批量分配失败: {str(e)}'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def batch_revoke(self, request):
        """批量撤销许可证分配"""
        assignment_ids = request.data.get('assignment_ids', [])
        reason = request.data.get('reason', '批量撤销')
        
        if not assignment_ids:
            return Response({
                'success': False,
                'message': '请提供要撤销的分配ID列表'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        user_tenant = get_user_tenant(request.user)
        if not user_tenant:
            return Response({'error': '无法确定用户租户'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                assignments = LicenseAssignment.objects.filter(
                    id__in=assignment_ids,
                    tenant=user_tenant,
                    status='active'
                )
                
                if assignments.count() != len(assignment_ids):
                    return Response({
                        'success': False,
                        'message': '部分分配ID不存在或不属于current租户'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                revoked_count = 0
                for assignment in assignments:
                    TenantAwareLicenseAssignmentService.revoke_license_from_member(
                        assignment=assignment,
                        reason=reason,
                        operator=request.user
                    )
                    revoked_count += 1
                
                return Response({
                    'success': True,
                    'message': f'成功批量撤销 {revoked_count} 个许可证分配'
                })
                
        except Exception as e:
            return Response({
                'success': False,
                'message': f'批量撤销失败: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取许可证分配统计信息"""
        user_tenant = get_user_tenant(request.user)
        if not user_tenant:
            return Response({'error': '无法确定用户租户'}, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = self.get_queryset()
        
        # 基本统计
        total_assignments = queryset.count()
        active_assignments = queryset.filter(status='active').count()
        expired_assignments = queryset.filter(status='expired').count()
        revoked_assignments = queryset.filter(status='revoked').count()
        
        # 按分配类型统计
        assignment_type_stats = {}
        for assignment_type, _ in LicenseAssignment.ASSIGNMENT_TYPE_CHOICES:
            count = queryset.filter(assignment_type=assignment_type).count()
            assignment_type_stats[assignment_type] = count
        
        # 按优先级统计
        priority_stats = {}
        for priority, _ in LicenseAssignment.PRIORITY_CHOICES:
            count = queryset.filter(priority=priority).count()
            priority_stats[priority] = count
        
        # 使用情况统计
        usage_stats = {
            'total_usage_count': sum(a.usage_count for a in queryset),
            'active_in_last_30_days': queryset.filter(
                last_used_at__gte=timezone.now() - timezone.timedelta(days=30)
            ).count(),
            'never_used': queryset.filter(last_used_at__isnull=True).count(),
        }
        
        return Response({
            'total_assignments': total_assignments,
            'status_distribution': {
                'active': active_assignments,
                'expired': expired_assignments,
                'revoked': revoked_assignments,
            },
            'assignment_type_distribution': assignment_type_stats,
            'priority_distribution': priority_stats,
            'usage_statistics': usage_stats,
        })
