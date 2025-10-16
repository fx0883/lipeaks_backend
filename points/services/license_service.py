"""
租户感知许可证分配服务

集成多租户权限检查的许可证分配管理
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from licenses.models import License, LicenseAssignment
from ..models import TenantUserProfile
from .permission_service import TenantAwarePermissionService, PermissionValidator
from .points_engine import PointsEngine

logger = logging.getLogger(__name__)


class TenantAwareLicenseAssignmentService:
    """
    租户感知许可证分配服务
    
    提供集成多租户权限检查和积分奖励的许可证分配管理功能
    """
    
    def __init__(self):
        self.logger = logger
        self.permission_service = TenantAwarePermissionService()
        self.permission_validator = PermissionValidator(self.permission_service)
        self.points_engine = PointsEngine()
    
    @transaction.atomic
    def assign_license_to_member(
        self,
        member: Any,
        license: License,
        assignment_type: str = 'direct',
        reason: str = "",
        operator: Optional[Any] = None,
        auto_activate: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        分配许可证给成员
        
        Args:
            member: Member对象
            license: License对象
            assignment_type: 分配类型
            reason: 分配原因
            operator: 操作员
            auto_activate: 是否自动激活
            **kwargs: 其他配置参数
            
        Returns:
            Dict: 分配结果
        """
        # 1. 验证租户一致性
        if member.tenant_id != license.tenant_id:
            raise ValidationError("Member and license must belong to the same tenant")
        
        # 2. 权限验证
        permission_check = self.permission_validator.validate_license_assignment(
            member=member,
            tenant=member.tenant,
            license_count=1
        )
        
        if not permission_check['is_valid']:
            return {
                'success': False,
                'error': 'permission_denied',
                'message': permission_check['message'],
                'details': permission_check
            }
        
        # 3. 许可证状态检查
        license_validation = self._validate_license_for_assignment(license)
        if not license_validation['is_valid']:
            return {
                'success': False,
                'error': 'license_invalid',
                'message': license_validation['message'],
                'details': license_validation
            }
        
        # 4. 获取用户的有效权限配置
        user_permissions = self.permission_service.calculate_user_permissions(
            member=member,
            tenant=member.tenant
        )
        
        # 5. 应用权限增强
        assignment_config = self._apply_permission_enhancements(
            base_config=kwargs,
            user_permissions=user_permissions
        )
        
        try:
            # 6. 创建许可证分配
            assignment = LicenseAssignment.create_assignment(
                member=member,
                license=license,
                assignment_type=assignment_type,
                reason=reason,
                operator=operator,
                **assignment_config
            )
            
            # 7. 自动激活（如果需要）
            if auto_activate and assignment.can_activate:
                assignment.activate()
            
            # 8. 奖励积分
            self._award_license_points(member, license, 'activation')
            
            # 9. 记录分配日志
            self.logger.info(
                f"许可证分配成功: {member.username}@{member.tenant.name} "
                f"分配许可证 {license.license_key[-8:]}*** ({assignment_type})"
            )
            
            return {
                'success': True,
                'assignment': assignment,
                'assignment_id': assignment.id,
                'effective_permissions': assignment.get_effective_permissions(),
                'metadata': {
                    'user_level': user_permissions['_metadata']['user_level'],
                    'active_tags': user_permissions['_metadata']['active_tags'],
                    'points_awarded': True
                }
            }
            
        except Exception as e:
            self.logger.error(f"许可证分配失败: {e}")
            return {
                'success': False,
                'error': 'assignment_failed',
                'message': str(e)
            }
    
    @transaction.atomic
    def batch_assign_licenses(
        self,
        assignments: List[Dict[str, Any]],
        operator: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        批量分配许可证
        
        Args:
            assignments: 分配配置列表，每个包含 member, license, 等配置
            operator: 操作员
            
        Returns:
            Dict: 批量分配结果
        """
        results = {
            'total_requested': len(assignments),
            'successful': 0,
            'failed': 0,
            'assignment_ids': [],
            'errors': [],
            'summary': {}
        }
        
        for i, assignment_config in enumerate(assignments):
            try:
                member = assignment_config['member']
                license = assignment_config['license']
                
                # 执行单个分配
                result = self.assign_license_to_member(
                    member=member,
                    license=license,
                    assignment_type=assignment_config.get('assignment_type', 'batch'),
                    reason=assignment_config.get('reason', f"批量分配 #{i+1}"),
                    operator=operator,
                    auto_activate=assignment_config.get('auto_activate', True),
                    **assignment_config.get('config', {})
                )
                
                if result['success']:
                    results['successful'] += 1
                    results['assignment_ids'].append(result['assignment_id'])
                else:
                    results['failed'] += 1
                    results['errors'].append({
                        'index': i,
                        'member_username': member.username,
                        'license_key': license.license_key[-8:] + '***',
                        'error': result['error'],
                        'message': result['message']
                    })
                    
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'index': i,
                    'error': 'unexpected_error',
                    'message': str(e)
                })
        
        # 统计摘要
        results['summary'] = {
            'success_rate': (results['successful'] / results['total_requested']) * 100,
            'points_awarded_count': results['successful'],  # 成功分配的都会获得积分
        }
        
        self.logger.info(
            f"批量许可证分配完成: 成功 {results['successful']} 个，"
            f"失败 {results['failed']} 个，成功率 {results['summary']['success_rate']:.1f}%"
        )
        
        return results
    
    @transaction.atomic
    def revoke_license_assignment(
        self,
        assignment: LicenseAssignment,
        reason: str = "",
        operator: Optional[Any] = None,
        refund_points: bool = False
    ) -> Dict[str, Any]:
        """
        撤销许可证分配
        
        Args:
            assignment: 许可证分配对象
            reason: 撤销原因
            operator: 操作员
            refund_points: 是否退还积分
            
        Returns:
            Dict: 撤销结果
        """
        try:
            # 权限检查
            if not self.permission_validator.validate_api_access(
                assignment.member, assignment.tenant
            ):
                return {
                    'success': False,
                    'error': 'permission_denied',
                    'message': '没有撤销许可证的权限'
                }
            
            # 执行撤销
            assignment.revoke(reason=reason, operator=operator)
            
            # 退还积分（如果需要）
            points_refunded = 0
            if refund_points:
                points_refunded = self._refund_license_points(
                    assignment.member, assignment.license
                )
            
            self.logger.info(
                f"许可证分配撤销: {assignment.member.username}@{assignment.tenant.name} "
                f"撤销许可证 {assignment.license.license_key[-8:]}*** - {reason}"
            )
            
            return {
                'success': True,
                'assignment_id': assignment.id,
                'points_refunded': points_refunded,
                'revoked_at': assignment.revoked_at
            }
            
        except Exception as e:
            self.logger.error(f"许可证分配撤销失败: {e}")
            return {
                'success': False,
                'error': 'revoke_failed',
                'message': str(e)
            }
    
    def get_member_license_summary(
        self,
        member: Any,
        include_inactive: bool = False
    ) -> Dict[str, Any]:
        """
        获取成员的许可证分配摘要
        
        Args:
            member: Member对象
            include_inactive: 是否包含非活跃分配
            
        Returns:
            Dict: 许可证分配摘要
        """
        # 查询分配记录
        assignments = LicenseAssignment.objects.filter(
            member=member,
            tenant=member.tenant
        ).select_related('license', 'license__product', 'license__plan')
        
        if not include_inactive:
            assignments = assignments.filter(status='active')
        
        # 获取用户权限
        user_permissions = self.permission_service.calculate_user_permissions(
            member=member,
            tenant=member.tenant
        )
        
        # 统计信息
        total_assignments = assignments.count()
        active_assignments = assignments.filter(status='active').count()
        max_licenses = user_permissions['license']['max_licenses']
        available_slots = max_licenses - active_assignments
        
        # 按产品分组
        product_summary = {}
        for assignment in assignments:
            product_name = assignment.license.product.name
            if product_name not in product_summary:
                product_summary[product_name] = {
                    'count': 0,
                    'active_count': 0,
                    'assignments': []
                }
            
            product_summary[product_name]['count'] += 1
            if assignment.status == 'active':
                product_summary[product_name]['active_count'] += 1
            
            product_summary[product_name]['assignments'].append({
                'assignment_id': assignment.id,
                'license_key': assignment.license.license_key[-8:] + '***',
                'plan_name': assignment.license.plan.name,
                'status': assignment.status,
                'assigned_at': assignment.assigned_at,
                'expires_at': assignment.expires_at,
                'last_used_at': assignment.last_used_at,
                'usage_count': assignment.usage_count,
                'effective_permissions': assignment.get_effective_permissions()
            })
        
        return {
            'member_info': {
                'username': member.username,
                'tenant_name': member.tenant.name,
                'user_level': user_permissions['_metadata']['user_level'],
                'active_tags': user_permissions['_metadata']['active_tags']
            },
            'quota_info': {
                'max_licenses': max_licenses,
                'active_assignments': active_assignments,
                'available_slots': available_slots,
                'utilization_rate': (active_assignments / max_licenses) * 100 if max_licenses > 0 else 0
            },
            'assignment_summary': {
                'total_assignments': total_assignments,
                'active_assignments': active_assignments,
                'product_breakdown': product_summary
            },
            'permissions': user_permissions
        }
    
    def get_license_assignment_analytics(
        self,
        tenant: Any,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> Dict[str, Any]:
        """
        获取许可证分配分析数据
        
        Args:
            tenant: 租户对象
            date_range: 日期范围 (start, end)
            
        Returns:
            Dict: 分析数据
        """
        queryset = LicenseAssignment.objects.filter(tenant=tenant)
        
        if date_range:
            start_date, end_date = date_range
            queryset = queryset.filter(assigned_at__range=(start_date, end_date))
        
        # 基础统计
        total_assignments = queryset.count()
        active_assignments = queryset.filter(status='active').count()
        revoked_assignments = queryset.filter(status='revoked').count()
        
        # 按分配类型统计
        assignment_types = {}
        for assignment in queryset.values('assignment_type').distinct():
            type_name = assignment['assignment_type']
            type_count = queryset.filter(assignment_type=type_name).count()
            assignment_types[type_name] = type_count
        
        # 按产品统计
        product_stats = {}
        assignments_with_product = queryset.select_related('license__product')
        for assignment in assignments_with_product:
            product_name = assignment.license.product.name
            if product_name not in product_stats:
                product_stats[product_name] = {
                    'total': 0,
                    'active': 0,
                    'revoked': 0
                }
            
            product_stats[product_name]['total'] += 1
            if assignment.status == 'active':
                product_stats[product_name]['active'] += 1
            elif assignment.status == 'revoked':
                product_stats[product_name]['revoked'] += 1
        
        # 使用率统计
        usage_stats = queryset.filter(status='active').aggregate(
            avg_usage=models.Avg('usage_count'),
            total_usage=models.Sum('usage_count')
        )
        
        return {
            'overview': {
                'total_assignments': total_assignments,
                'active_assignments': active_assignments,
                'revoked_assignments': revoked_assignments,
                'activation_rate': (active_assignments / total_assignments) * 100 if total_assignments > 0 else 0
            },
            'assignment_types': assignment_types,
            'product_breakdown': product_stats,
            'usage_statistics': {
                'average_usage_per_license': usage_stats['avg_usage'] or 0,
                'total_usage_count': usage_stats['total_usage'] or 0
            },
            'date_range': {
                'start': date_range[0].isoformat() if date_range else None,
                'end': date_range[1].isoformat() if date_range else None
            }
        }
    
    def _validate_license_for_assignment(self, license: License) -> Dict[str, Any]:
        """验证许可证是否可以分配"""
        now = timezone.now()
        
        # 检查许可证状态
        if license.status not in ['generated', 'activated']:
            return {
                'is_valid': False,
                'message': f"许可证状态不允许分配: {license.get_status_display()}"
            }
        
        # 检查过期时间
        if license.expires_at and now > license.expires_at:
            return {
                'is_valid': False,
                'message': "License has expired"
            }
        
        # 检查激活配额
        if license.current_activations >= license.max_activations:
            return {
                'is_valid': False,
                'message': f"许可证激活配额已满 ({license.current_activations}/{license.max_activations})"
            }
        
        return {
            'is_valid': True,
            'message': "许可证验证通过"
        }
    
    def _apply_permission_enhancements(
        self,
        base_config: Dict[str, Any],
        user_permissions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """应用权限增强配置"""
        enhanced_config = base_config.copy()
        
        # 应用许可证相关权限
        license_permissions = user_permissions.get('license', {})
        
        # 最大设备数增强
        if 'max_devices_per_user' not in enhanced_config:
            enhanced_config['max_devices_per_user'] = license_permissions.get(
                'max_devices_per_license', 1
            )
        
        # 权限能力增强
        enhanced_config.update({
            'can_share': license_permissions.get('can_share_license', False),
            'can_backup': license_permissions.get('can_backup_license', False),
            'can_export': license_permissions.get('can_export_license', False),
        })
        
        return enhanced_config
    
    def _award_license_points(
        self,
        member: Any,
        license: License,
        action: str
    ) -> Optional[int]:
        """奖励许可证相关积分"""
        try:
            # 获取用户档案
            tenant_user_profile = TenantUserProfile.objects.filter(
                member=member,
                tenant=member.tenant
            ).first()
            
            if not tenant_user_profile:
                return None
            
            # 计算许可证价值（简化处理）
            license_value = None
            if hasattr(license, 'plan') and hasattr(license.plan, 'price'):
                license_value = getattr(license.plan, 'price', None)
            
            # 奖励积分
            points_record = self.points_engine.award_license_points(
                tenant_user_profile=tenant_user_profile,
                action=action,
                license_key=license.license_key,
                license_value=license_value
            )
            
            return points_record.points
            
        except Exception as e:
            self.logger.error(f"许可证积分奖励失败: {e}")
            return None
    
    def _refund_license_points(
        self,
        member: Any,
        license: License
    ) -> int:
        """退还许可证积分"""
        try:
            # 获取用户档案
            tenant_user_profile = TenantUserProfile.objects.filter(
                member=member,
                tenant=member.tenant
            ).first()
            
            if not tenant_user_profile:
                return 0
            
            # 查找相关的积分记录
            from ..models import TenantUserPoints
            
            license_points = TenantUserPoints.objects.filter(
                tenant_user_profile=tenant_user_profile,
                category='license',
                source_description__icontains=license.license_key,
                point_type='earn',
                status='active'
            ).first()
            
            if license_points:
                # 退还积分（创建负数记录）
                refund_record = self.points_engine.consume_points(
                    tenant_user_profile=tenant_user_profile,
                    points=license_points.points,
                    category='license',
                    subcategory='refund',
                    reason=f"撤销许可证退还积分 - {license.license_key}",
                    source_type='system'
                )
                
                return license_points.points
            
            return 0
            
        except Exception as e:
            self.logger.error(f"许可证积分退还失败: {e}")
            return 0


class LicenseQuotaManager:
    """
    许可证配额管理器
    
    提供租户许可证配额的动态管理
    """
    
    def __init__(self, permission_service: TenantAwarePermissionService):
        self.permission_service = permission_service
        self.logger = logger
    
    def calculate_dynamic_quota(
        self,
        member: Any,
        tenant: Any,
        base_quota: int = 1
    ) -> Dict[str, Any]:
        """
        计算动态许可证配额
        
        Args:
            member: Member对象
            tenant: Tenant对象
            base_quota: 基础配额
            
        Returns:
            Dict: 配额计算结果
        """
        # 获取用户权限
        user_permissions = self.permission_service.calculate_user_permissions(
            member=member,
            tenant=tenant
        )
        
        # 基础配额
        final_quota = base_quota
        
        # 等级增强
        level_multiplier = 1.0
        if user_permissions['_metadata']['user_level']['order'] > 0:
            # 根据等级提供配额倍数
            level_order = user_permissions['_metadata']['user_level']['order']
            level_multiplier = 1 + (level_order * 0.5)  # 每级增加50%
        
        # VIP标签增强
        vip_multiplier = 1.0
        for tag in user_permissions['_metadata']['active_tags']:
            if tag['type'] == 'vip' and tag['is_active']:
                vip_multiplier += 0.5  # VIP增加50%
            elif tag['type'] == 'enterprise' and tag['is_active']:
                vip_multiplier += 1.0  # 企业用户增加100%
        
        # 计算最终配额
        final_quota = int(base_quota * level_multiplier * vip_multiplier)
        
        return {
            'base_quota': base_quota,
            'level_multiplier': level_multiplier,
            'vip_multiplier': vip_multiplier,
            'final_quota': final_quota,
            'enhancement_details': {
                'level_bonus': int(base_quota * (level_multiplier - 1)),
                'vip_bonus': int(base_quota * level_multiplier * (vip_multiplier - 1))
            }
        }
