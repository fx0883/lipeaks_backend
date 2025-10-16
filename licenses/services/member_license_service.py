"""
Member用户许可证申请服务模块
提供试用许可证申请、配额管理、通知等业务功能
"""

import logging
from datetime import timedelta
from typing import Dict, Any, Optional, List, Tuple
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from django.conf import settings

from common.exceptions import (
    LicenseException,
    LicenseQuotaExceededException,
    UserInactiveException,
    TenantInactiveException,
)
from licenses.models import (
    SoftwareProduct, LicensePlan, License, LicenseAssignment,
    TenantLicenseQuota, SecurityAuditLog
)
from licenses.services.license_service import LicenseGenerationService, LicenseManagementService
from users.models import Member

logger = logging.getLogger('licenses.member')


class MemberLicenseApplicationService:
    """Member用户许可证申请服务"""
    
    def __init__(self):
        self.license_generation_service = LicenseGenerationService()
        self.license_management_service = LicenseManagementService()
    
    @transaction.atomic
    def apply_trial_license(
        self,
        member: Member,
        product_id: int,
        plan_id: int = None,
        reason: str = "试用版申请",
        user_info: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        申请试用许可证
        
        Args:
            member: Member用户实例
            product_id: 产品ID
            plan_id: 方案ID（可选）。如果指定，使用指定方案；否则自动选择有效期最长的方案
            reason: 申请原因
            user_info: 用户补充信息
            
        Returns:
            Dict[str, Any]: 申请结果
        """
        try:
            logger.info(f"开始处理Member {member.username} 的试用许可证申请，产品ID: {product_id}, 方案ID: {plan_id}")
            
            # 1. 验证产品和方案
            product, trial_plan = self._validate_product_and_plan(product_id, plan_id)
            
            # 2. 检查申请资格
            self._check_application_eligibility(member, product)
            
            # 3. 检查配额限制
            self._check_quota_limits(member, product)
            
            # 4. 获取统一的时间基准（避免时间差异导致验证失败）
            base_time = timezone.now()
            
            # 5. 生成许可证
            license_obj = self._create_trial_license(
                product, trial_plan, member, user_info, base_time
            )
            
            # 6. 创建分配关系
            assignment = self._create_license_assignment(
                member, license_obj, reason, base_time
            )
            
            # 6. 发送通知
            self._send_application_notification(member, assignment)
            
            # 7. 记录审计日志
            self._log_application_activity(member, assignment)
            
            logger.info(f"试用许可证申请成功: Member {member.username}, 许可证 {license_obj.id}")
            
            return {
                'success': True,
                'message': '试用许可证申请成功',
                'data': {
                    'license_id': license_obj.id,
                    'assignment_id': assignment.id,
                    'license_key': license_obj.license_key,
                    'expires_at': assignment.expires_at.isoformat() if assignment.expires_at else None,
                    'product_name': product.name,
                    'plan_name': trial_plan.name,
                    'max_activations': license_obj.max_activations
                }
            }
            
        except ValueError as e:
            logger.warning(f"试用许可证申请失败 - 业务规则错误: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'code': 'APPLICATION_FAILED'
            }
        except Exception as e:
            logger.error(f"试用许可证申请异常: {str(e)}")
            return {
                'success': False,
                'error': '系统内部错误，请稍后重试',
                'code': 'INTERNAL_ERROR'
            }
    
    def get_available_products(self, member: Member) -> List[SoftwareProduct]:
        """
        获取可申请的试用产品列表
        
        Args:
            member: Member用户实例
            
        Returns:
            List[SoftwareProduct]: 可申请的产品列表
        """
        try:
            from django.db.models import Exists, OuterRef
            
            # 使用子查询确保产品有活跃的试用方案
            # 这样可以避免JOIN导致的误判问题
            has_active_trial_plan = LicensePlan.objects.filter(
                product=OuterRef('pk'),
                plan_type='trial',
                status='active'
            )
            
            # 获取有活跃试用方案的产品
            available_products = SoftwareProduct.objects.filter(
                status='active',
                is_deleted=False
            ).filter(
                Exists(has_active_trial_plan)  # 确保产品有活跃的试用方案
            )
            
            # 过滤租户产品（如果有租户限制）
            if member.tenant:
                available_products = available_products.filter(
                    tenant=member.tenant
                )
            
            logger.info(f"为Member {member.username} 找到 {available_products.count()} 个可申请产品")
            return list(available_products)
            
        except Exception as e:
            logger.error(f"获取可申请产品列表失败: {str(e)}")
            return []
    
    def get_member_licenses(self, member: Member) -> Dict[str, Any]:
        """
        获取Member用户的许可证列表及统计信息
        
        Args:
            member: Member用户实例
            
        Returns:
            Dict[str, Any]: 许可证列表和统计信息
        """
        try:
            # 获取用户的所有许可证分配
            assignments = LicenseAssignment.objects.filter(
                member=member
            ).select_related(
                'license', 'license__product', 'license__plan'
            ).order_by('-created_at')
            
            # 统计信息
            total_count = assignments.count()
            active_count = assignments.filter(status='active').count()
            trial_count = assignments.filter(
                license__plan__plan_type='trial'
            ).count()
            
            # 计算即将过期的许可证（7天内）
            seven_days_later = timezone.now() + timedelta(days=7)
            expiring_soon_count = assignments.filter(
                status='active',
                expires_at__lte=seven_days_later,
                expires_at__gte=timezone.now()
            ).count()
            
            logger.info(f"Member {member.username} 拥有 {total_count} 个许可证，其中 {active_count} 个有效")
            
            return {
                'count': total_count,
                'active_count': active_count,
                'trial_count': trial_count,
                'expiring_soon_count': expiring_soon_count,
                'licenses': list(assignments)
            }
            
        except Exception as e:
            logger.error(f"获取Member许可证列表失败: {str(e)}")
            return {
                'count': 0,
                'active_count': 0,
                'trial_count': 0,
                'expiring_soon_count': 0,
                'licenses': []
            }
    
    def _validate_product_and_plan(self, product_id: int, plan_id: int = None) -> Tuple[SoftwareProduct, LicensePlan]:
        """
        验证产品和试用方案
        
        Args:
            product_id: 产品ID
            plan_id: 方案ID（可选）
            
        Returns:
            Tuple[SoftwareProduct, LicensePlan]: 产品和试用方案
        """
        try:
            product = SoftwareProduct.objects.get(
                id=product_id,
                status='active',
                is_deleted=False
            )
        except SoftwareProduct.DoesNotExist:
            raise LicenseException(
                error_code='PRODUCT_NOT_FOUND',
                detail=f'产品ID {product_id} 不存在或不可用',
                product_id=product_id
            )
        
        # 如果指定了plan_id，使用指定的方案
        if plan_id:
            try:
                trial_plan = product.license_plans.get(
                    id=plan_id,
                    plan_type='trial',
                    status='active'
                )
            except LicensePlan.DoesNotExist:
                raise LicenseException(
                    error_code='TRIAL_PLAN_NOT_FOUND',
                    detail=f'试用方案ID {plan_id} 不存在或不可用',
                    plan_id=plan_id,
                    product_id=product_id
                )
        else:
            # 未指定plan_id，自动选择有效期最长的方案
            trial_plan = product.license_plans.filter(
                plan_type='trial',
                status='active'
            ).order_by(
                '-default_validity_days',
                '-default_max_activations'
            ).first()
            
            if not trial_plan:
                raise LicenseException(
                    error_code='NO_TRIAL_PLAN_AVAILABLE',
                    detail=f'产品 {product.name} 没有可用的试用方案',
                    product_id=product_id,
                    product_name=product.name
                )
        
        return product, trial_plan
    
    def _check_application_eligibility(self, member: Member, product: SoftwareProduct):
        """
        检查申请资格
        
        Args:
            member: Member用户实例
            product: 产品实例
        """
        # 检查重复申请（排除已删除的许可证）
        existing = LicenseAssignment.objects.filter(
            member=member,
            license__product=product,
            license__is_deleted=False,  # 排除已删除的许可证
            status__in=['active', 'pending']
        ).exists()
        
        if existing:
            raise LicenseException(
                error_code='LICENSE_ALREADY_ASSIGNED',
                detail='您已经拥有该产品的有效许可证',
                member_id=member.id,
                product_id=product.id
            )
        
        # 检查用户状态
        if not member.is_active:
            raise UserInactiveException(
                detail=f'用户 {member.username} 账户已被禁用，无法申请许可证',
                user_id=member.id,
                username=member.username
            )
        
        if getattr(member, 'status', 'active') != 'active':
            raise UserInactiveException(
                detail=f'用户状态异常（{member.status}），无法申请许可证',
                user_id=member.id,
                status=getattr(member, 'status', 'unknown')
            )
        
        # 检查租户状态
        if not member.tenant or not member.tenant.is_active:
            raise TenantInactiveException(
                detail='租户账户已被禁用，无法申请许可证',
                tenant_id=member.tenant.id if member.tenant else None,
                member_id=member.id
            )
        
        # 检查用户是否被禁止申请许可证
        if hasattr(member, 'license_application_banned') and member.license_application_banned:
            raise LicenseException(
                error_code='LICENSE_APPLICATION_BANNED',
                detail='您的账户已被禁止申请许可证',
                member_id=member.id,
                banned=True
            )
    
    def _check_quota_limits(self, member: Member, product: SoftwareProduct):
        """
        检查配额限制
        
        Args:
            member: Member用户实例
            product: 产品实例
        """
        # 检查租户配额
        tenant_quota = TenantLicenseQuota.objects.filter(
            tenant=member.tenant,
            product=product,
            is_active=True
        ).first()
        
        if tenant_quota:
            if tenant_quota.current_licenses >= tenant_quota.max_licenses:
                raise LicenseQuotaExceededException(
                    detail=f'租户许可证配额已满，current配额: {tenant_quota.max_licenses}',
                    tenant_id=member.tenant.id,
                    current_count=tenant_quota.current_licenses,
                    max_count=tenant_quota.max_licenses,
                    quota_type='tenant'
                )
        
        # 检查用户个人配额（试用许可证限制）
        from licenses.config import TRIAL_LICENSE_QUOTAS
        
        # 从配置文件获取默认配额
        default_quota = TRIAL_LICENSE_QUOTAS.get('default', 1)
        max_trial_licenses = getattr(member, 'max_trial_licenses', default_quota)
        
        user_trial_count = LicenseAssignment.objects.filter(
            member=member,
            license__plan__plan_type='trial',
            status='active'
        ).count()
        
        if user_trial_count >= max_trial_licenses:
            raise LicenseQuotaExceededException(
                detail=f'Your trial license quota has been reached（{max_trial_licenses}个）',
                member_id=member.id,
                current_count=user_trial_count,
                max_count=max_trial_licenses,
                quota_type='user_trial'
            )
        
        # 检查申请频率（从配置文件获取限制）
        from licenses.config import APPLICATION_RATE_LIMITS
        
        business_limit = APPLICATION_RATE_LIMITS.get('business_limit', 3)
        cooldown_hours = APPLICATION_RATE_LIMITS.get('cooldown_hours', 24)
        
        recent_applications = LicenseAssignment.objects.filter(
            member=member,
            created_at__gte=timezone.now() - timedelta(hours=cooldown_hours)
        ).count()
        
        if recent_applications >= business_limit:
            raise LicenseException(
                error_code='APPLICATION_RATE_LIMIT_EXCEEDED',
                detail=f'{cooldown_hours}hours. Too many applications, please try again later（Current limit: {business_limit}次）',
                member_id=member.id,
                cooldown_hours=cooldown_hours,
                business_limit=business_limit,
                recent_applications_count=recent_applications_count
            )
    
    def _create_trial_license(
        self, 
        product: SoftwareProduct, 
        plan: LicensePlan, 
        member: Member, 
        user_info: Dict[str, Any] = None,
        base_time: timezone.datetime = None
    ) -> License:
        """
        创建试用许可证
        
        Args:
            product: 产品实例
            plan: 方案实例
            member: Member用户实例
            user_info: 用户补充信息
            
        Returns:
            License: 创建的许可证实例
        """
        customer_info = {
            'name': member.username,
            'email': member.email,
            'company': user_info.get('company', '') if user_info else '',
            'phone': user_info.get('phone', '') if user_info else '',
            'job_title': user_info.get('job_title', '') if user_info else '',
            'intended_use': user_info.get('intended_use', '') if user_info else ''
        }
        
        # 计算许可证过期时间（使用统一的时间基准）
        if base_time is None:
            base_time = timezone.now()
        
        license_expires_at = base_time + timedelta(days=plan.default_validity_days)
        
        # 使用现有的许可证管理服务创建许可证
        license_obj = self.license_management_service.create_license(
            product_id=product.id,
            plan_id=plan.id,
            tenant_id=member.tenant.id,
            customer_info=customer_info,
            expires_at=license_expires_at,  # 明确传递过期时间
            max_activations=plan.default_max_activations
        )
        
        return license_obj
    
    def _create_license_assignment(
        self, 
        member: Member, 
        license_obj: License, 
        reason: str,
        base_time: timezone.datetime = None
    ) -> LicenseAssignment:
        """
        创建许可证分配
        
        Args:
            member: Member用户实例
            license_obj: 许可证实例
            reason: 分配原因
            
        Returns:
            LicenseAssignment: 创建的分配实例
        """
        # 试用版默认有效期从方案配置读取（使用统一的时间基准）
        if base_time is None:
            base_time = timezone.now()
        
        # 确保分配过期时间不超过许可证过期时间
        license_expires_at = license_obj.expires_at
        assignment_expires_at = base_time + timedelta(days=license_obj.plan.default_validity_days)
        
        # 如果许可证有过期时间，分配时间不能超过许可证时间
        if license_expires_at and assignment_expires_at > license_expires_at:
            expires_at = license_expires_at
        else:
            expires_at = assignment_expires_at
        
        assignment = LicenseAssignment.objects.create(
            member=member,
            license=license_obj,
            tenant=member.tenant,
            assignment_type='direct',
            assignment_reason=reason,
            status='active',
            expires_at=expires_at,
            can_activate=True,
            max_devices_per_user=license_obj.max_activations
        )
        
        return assignment
    
    def _send_application_notification(self, member: Member, assignment: LicenseAssignment):
        """
        发送申请成功通知
        
        Args:
            member: Member用户实例
            assignment: 许可证分配实例
        """
        try:
            # 这里可以集成邮件、短信、站内消息等通知方式
            # 目前仅记录日志
            logger.info(
                f"应发送许可证申请成功通知: "
                f"用户 {member.username}, "
                f"产品 {assignment.license.product.name}, "
                f"许可证密钥 {assignment.license.license_key[:10]}..."
            )
            
            # TODO: 集成通知系统
            # NotificationService.send_trial_license_granted(member, assignment)
            
        except Exception as e:
            logger.error(f"发送申请通知失败: {str(e)}")
    
    def _log_application_activity(self, member: Member, assignment: LicenseAssignment):
        """
        记录申请活动审计日志
        
        Args:
            member: Member用户实例
            assignment: 许可证分配实例
        """
        try:
            SecurityAuditLog.objects.create(
                event_type='license_generated',
                severity='LOW',
                tenant_id=member.tenant.id,
                ip_address=None,  # 这里可以从request中获取
                user_agent='',
                details={
                    'event': 'trial_license_application',
                    'member_id': member.id,
                    'member_username': member.username,
                    'license_id': assignment.license.id,
                    'product': assignment.license.product.code,
                    'plan_type': assignment.license.plan.plan_type,
                    'assignment_id': assignment.id,
                    'reason': assignment.assignment_reason,
                    'expires_at': assignment.expires_at.isoformat() if assignment.expires_at else None
                }
            )
            
        except Exception as e:
            logger.error(f"记录审计日志失败: {str(e)}")


class MemberLicenseStatisticsService:
    """Member许可证统计服务"""
    
    @staticmethod
    def get_application_statistics(tenant_id: int = None, days: int = 30) -> Dict[str, Any]:
        """
        获取申请统计数据
        
        Args:
            tenant_id: 租户ID（可选）
            days: 统计天数
            
        Returns:
            Dict[str, Any]: 统计数据
        """
        try:
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days)
            
            queryset = LicenseAssignment.objects.filter(
                created_at__gte=start_date,
                license__plan__plan_type='trial'
            )
            
            if tenant_id:
                queryset = queryset.filter(tenant_id=tenant_id)
            
            total_applications = queryset.count()
            active_licenses = queryset.filter(status='active').count()
            
            # 按产品分组统计
            product_stats = {}
            for assignment in queryset.select_related('license__product'):
                product_name = assignment.license.product.name
                if product_name not in product_stats:
                    product_stats[product_name] = {
                        'applications': 0,
                        'active': 0
                    }
                product_stats[product_name]['applications'] += 1
                if assignment.status == 'active':
                    product_stats[product_name]['active'] += 1
            
            return {
                'period_days': days,
                'total_applications': total_applications,
                'active_licenses': active_licenses,
                'activation_rate': (active_licenses / total_applications * 100) if total_applications > 0 else 0,
                'product_statistics': product_stats
            }
            
        except Exception as e:
            logger.error(f"获取申请统计失败: {str(e)}")
            return {
                'period_days': days,
                'total_applications': 0,
                'active_licenses': 0,
                'activation_rate': 0,
                'product_statistics': {}
            }
