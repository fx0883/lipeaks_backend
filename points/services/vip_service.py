"""
VIP期限管理服务

提供VIP标签的过期管理、宽限期处理、自动续期等功能
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Q

from ..models import (
    TenantUserProfile,
    TenantUserTypeTag,
    UserTypeTag
)

logger = logging.getLogger(__name__)


class VipExpirationService:
    """
    VIP期限管理服务
    
    负责处理VIP标签的生命周期管理，包括：
    1. 过期检查和处理
    2. 宽限期管理
    3. 自动续期
    4. 过期提醒
    5. VIP状态计算
    """
    
    # VIP期限管理配置
    VIP_CONFIG = {
        'default_grace_period_days': 7,  # 默认宽限期
        'renewal_reminder_days': [30, 7, 3, 1],  # 续期提醒时间点
        'auto_renewal_retry_days': 3,  # 自动续期重试天数
        'cleanup_expired_days': 90,  # 清理过期记录的天数
    }
    
    def __init__(self):
        self.logger = logger
    
    def check_vip_expiration(self, tenant: Optional[Any] = None) -> Dict[str, Any]:
        """
        检查VIP过期状态
        
        Args:
            tenant: 租户对象，None表示检查所有租户
            
        Returns:
            Dict: 检查结果统计
        """
        now = timezone.now()
        
        # 查询需要检查的VIP标签
        queryset = TenantUserTypeTag.objects.filter(
            is_active=True,
            expires_at__isnull=False
        ).select_related('tag', 'tenant_user_profile', 'member', 'tenant')
        
        if tenant:
            queryset = queryset.filter(tenant=tenant)
        
        stats = {
            'total_checked': 0,
            'expired_count': 0,
            'grace_period_count': 0,
            'reminder_sent_count': 0,
            'auto_renewed_count': 0,
            'failed_renewals': 0,
        }
        
        for vip_tag in queryset:
            stats['total_checked'] += 1
            
            # 计算VIP状态
            vip_status = vip_tag.calculate_vip_status()
            
            if vip_status['status'] == 'expired':
                # 完全过期，需要处理
                self._handle_expired_vip(vip_tag)
                stats['expired_count'] += 1
                
            elif vip_status['status'] == 'grace_period':
                # 在宽限期内
                stats['grace_period_count'] += 1
                
                # 检查是否需要自动续期
                if vip_tag.auto_renewal:
                    if self._attempt_auto_renewal(vip_tag):
                        stats['auto_renewed_count'] += 1
                    else:
                        stats['failed_renewals'] += 1
                        
            elif vip_status['status'] == 'active':
                # 检查是否需要发送续期提醒
                days_remaining = vip_status.get('days_remaining', 0)
                if self._should_send_reminder(vip_tag, days_remaining):
                    self._send_renewal_reminder(vip_tag, days_remaining)
                    stats['reminder_sent_count'] += 1
                
                # 检查自动续期
                if vip_tag.auto_renewal and days_remaining <= 7:
                    if self._attempt_auto_renewal(vip_tag):
                        stats['auto_renewed_count'] += 1
                    else:
                        stats['failed_renewals'] += 1
        
        self.logger.info(
            f"VIP过期检查完成: 检查 {stats['total_checked']} 个VIP，"
            f"过期 {stats['expired_count']} 个，"
            f"宽限期 {stats['grace_period_count']} 个，"
            f"自动续期 {stats['auto_renewed_count']} 个"
        )
        
        return stats
    
    @transaction.atomic
    def extend_vip_period(
        self,
        vip_tag: TenantUserTypeTag,
        extend_days: int,
        reason: str = "",
        operator_id: Optional[int] = None,
        payment_id: Optional[int] = None
    ) -> bool:
        """
        延长VIP期限
        
        Args:
            vip_tag: VIP标签关联对象
            extend_days: 延长天数
            reason: 延长原因
            operator_id: 操作员ID
            payment_id: 关联的支付记录ID
            
        Returns:
            bool: 是否延长成功
        """
        if extend_days <= 0:
            raise ValueError("Extension days must be greater than 0")
        
        try:
            # 延长期限
            vip_tag.extend_period(extend_days, reason)
            
            # 更新支付信息
            if payment_id:
                vip_tag.payment_id = payment_id
                vip_tag.save(update_fields=['payment_id'])
            
            # 记录操作日志
            self.logger.info(
                f"VIP期限延长: {vip_tag.member.username}@{vip_tag.tenant.name} "
                f"{vip_tag.tag.tag_name} 延长 {extend_days} 天 - {reason}"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"VIP期限延长失败: {e}")
            return False
    
    @transaction.atomic
    def grant_vip_tag(
        self,
        tenant_user_profile: TenantUserProfile,
        tag: UserTypeTag,
        duration_days: Optional[int] = None,
        grant_method: str = 'manual',
        reason: str = "",
        operator_id: Optional[int] = None,
        payment_info: Optional[Dict[str, Any]] = None
    ) -> TenantUserTypeTag:
        """
        授予VIP标签
        
        Args:
            tenant_user_profile: 租户用户档案
            tag: 用户标签
            duration_days: 有效期天数，None使用标签默认期限
            grant_method: 授予方式
            reason: 授予原因
            operator_id: 操作员ID
            payment_info: 支付信息
            
        Returns:
            TenantUserTypeTag: 创建的VIP标签关联
        """
        # 确定有效期
        if duration_days is None:
            duration_days = tag.default_duration_days
        
        expires_at = None
        if duration_days:
            expires_at = timezone.now() + timedelta(days=duration_days)
        
        # 检查是否已存在同类型标签
        existing_tag = TenantUserTypeTag.objects.filter(
            tenant_user_profile=tenant_user_profile,
            tag=tag,
            is_active=True
        ).first()
        
        if existing_tag:
            # 如果已存在，延长期限
            if duration_days:
                self.extend_vip_period(
                    existing_tag,
                    duration_days,
                    f"重新授予 - {reason}",
                    operator_id
                )
            return existing_tag
        
        # 创建新的VIP标签关联
        vip_tag = TenantUserTypeTag.objects.create(
            tenant_user_profile=tenant_user_profile,
            tag=tag,
            tenant=tenant_user_profile.tenant,
            member=tenant_user_profile.member,
            grant_method=grant_method,
            grant_reason=reason,
            granted_by_id=operator_id,
            expires_at=expires_at,
            original_duration_days=duration_days,
            grace_period_days=self.VIP_CONFIG['default_grace_period_days'],
            **self._extract_payment_info(payment_info or {})
        )
        
        self.logger.info(
            f"VIP标签授予: {tenant_user_profile.member.username}@{tenant_user_profile.tenant.name} "
            f"获得 {tag.tag_name} 标签，有效期 {duration_days} 天"
        )
        
        return vip_tag
    
    def setup_auto_renewal(
        self,
        vip_tag: TenantUserTypeTag,
        payment_method_id: str,
        renewal_duration_days: Optional[int] = None
    ) -> bool:
        """
        设置自动续期
        
        Args:
            vip_tag: VIP标签关联对象
            payment_method_id: 支付方式ID
            renewal_duration_days: 续期期限天数
            
        Returns:
            bool: 设置是否成功
        """
        try:
            vip_tag.setup_auto_renewal(payment_method_id)
            
            # 存储续期配置
            if not vip_tag.metadata:
                vip_tag.metadata = {}
            
            vip_tag.metadata.update({
                'auto_renewal_duration_days': renewal_duration_days or vip_tag.original_duration_days,
                'auto_renewal_setup_at': timezone.now().isoformat()
            })
            vip_tag.save(update_fields=['metadata'])
            
            return True
            
        except Exception as e:
            self.logger.error(f"自动续期设置失败: {e}")
            return False
    
    def cancel_auto_renewal(self, vip_tag: TenantUserTypeTag) -> bool:
        """
        取消自动续期
        
        Args:
            vip_tag: VIP标签关联对象
            
        Returns:
            bool: 取消是否成功
        """
        try:
            vip_tag.cancel_auto_renewal()
            return True
        except Exception as e:
            self.logger.error(f"取消自动续期失败: {e}")
            return False
    
    def get_vip_statistics(
        self,
        tenant: Any,
        include_expired: bool = False
    ) -> Dict[str, Any]:
        """
        获取VIP统计信息
        
        Args:
            tenant: 租户对象
            include_expired: 是否包含已过期的VIP
            
        Returns:
            Dict: VIP统计数据
        """
        queryset = TenantUserTypeTag.objects.filter(tenant=tenant)
        
        if not include_expired:
            queryset = queryset.filter(is_active=True)
        
        queryset = queryset.select_related('tag', 'member')
        
        # 按标签类型统计
        tag_stats = {}
        status_stats = {
            'active': 0,
            'grace_period': 0,
            'expired': 0,
            'permanent': 0
        }
        
        auto_renewal_count = 0
        total_revenue = Decimal('0.00')
        
        for vip_tag in queryset:
            # 标签类型统计
            tag_name = vip_tag.tag.tag_name
            if tag_name not in tag_stats:
                tag_stats[tag_name] = {'count': 0, 'revenue': Decimal('0.00')}
            
            tag_stats[tag_name]['count'] += 1
            
            # 收入统计
            if vip_tag.payment_amount:
                tag_stats[tag_name]['revenue'] += vip_tag.payment_amount
                total_revenue += vip_tag.payment_amount
            
            # 状态统计
            if include_expired or vip_tag.is_active:
                vip_status = vip_tag.calculate_vip_status()
                status = vip_status['status']
                if status in status_stats:
                    status_stats[status] += 1
            
            # 自动续期统计
            if vip_tag.auto_renewal:
                auto_renewal_count += 1
        
        return {
            'tag_statistics': tag_stats,
            'status_distribution': status_stats,
            'auto_renewal_count': auto_renewal_count,
            'total_vips': sum(status_stats.values()),
            'total_revenue': total_revenue,
            'average_revenue_per_vip': (
                total_revenue / sum(tag_stats[tag]['count'] for tag in tag_stats)
                if tag_stats else Decimal('0.00')
            )
        }
    
    def get_expiring_vips(
        self,
        tenant: Any,
        days_ahead: int = 30
    ) -> List[Dict[str, Any]]:
        """
        获取即将过期的VIP列表
        
        Args:
            tenant: 租户对象
            days_ahead: 提前天数
            
        Returns:
            List: 即将过期的VIP信息
        """
        cutoff_date = timezone.now() + timedelta(days=days_ahead)
        
        expiring_vips = TenantUserTypeTag.objects.filter(
            tenant=tenant,
            is_active=True,
            expires_at__isnull=False,
            expires_at__lte=cutoff_date
        ).select_related('tag', 'member').order_by('expires_at')
        
        results = []
        for vip_tag in expiring_vips:
            vip_status = vip_tag.calculate_vip_status()
            
            results.append({
                'member_username': vip_tag.member.username,
                'tag_name': vip_tag.tag.tag_name,
                'tag_color': vip_tag.tag.tag_color,
                'expires_at': vip_tag.expires_at,
                'days_remaining': vip_status.get('days_remaining', 0),
                'status': vip_status['status'],
                'auto_renewal': vip_tag.auto_renewal,
                'grace_period_days': vip_tag.grace_period_days,
                'payment_amount': vip_tag.payment_amount,
                'usage_count': vip_tag.usage_count,
                'last_used_at': vip_tag.last_used_at
            })
        
        return results
    
    def _handle_expired_vip(self, vip_tag: TenantUserTypeTag):
        """处理已过期的VIP"""
        # 标记为过期状态
        vip_tag.status = 'expired'
        vip_tag.is_active = False
        vip_tag.save(update_fields=['status', 'is_active'])
        
        self.logger.info(
            f"VIP已过期: {vip_tag.member.username}@{vip_tag.tenant.name} "
            f"{vip_tag.tag.tag_name}"
        )
    
    def _attempt_auto_renewal(self, vip_tag: TenantUserTypeTag) -> bool:
        """
        尝试自动续期
        
        Args:
            vip_tag: VIP标签关联对象
            
        Returns:
            bool: 续期是否成功
        """
        if not vip_tag.auto_renewal:
            return False
        
        try:
            # 获取续期配置
            metadata = vip_tag.metadata or {}
            renewal_days = metadata.get(
                'auto_renewal_duration_days',
                vip_tag.original_duration_days or vip_tag.tag.default_duration_days
            )
            
            if not renewal_days:
                self.logger.warning(f"VIP自动续期失败：无法确定续期天数 - {vip_tag}")
                return False
            
            # 这里应该调用支付服务进行扣费
            # 简化处理，假设支付成功
            payment_successful = self._process_auto_renewal_payment(vip_tag)
            
            if payment_successful:
                # 延长期限
                self.extend_vip_period(
                    vip_tag,
                    renewal_days,
                    "自动续期",
                    operator_id=None,
                    payment_id=None  # 这里应该是实际的支付记录ID
                )
                
                # 更新续期次数
                vip_tag.renewal_count += 1
                vip_tag.save(update_fields=['renewal_count'])
                
                return True
            else:
                self.logger.warning(f"VIP自动续期支付失败 - {vip_tag}")
                return False
                
        except Exception as e:
            self.logger.error(f"VIP自动续期异常: {e}")
            return False
    
    def _process_auto_renewal_payment(self, vip_tag: TenantUserTypeTag) -> bool:
        """
        处理自动续期支付
        
        Args:
            vip_tag: VIP标签关联对象
            
        Returns:
            bool: 支付是否成功
        """
        # 这里应该集成实际的支付系统
        # 简化处理，假设支付成功
        
        # 模拟支付处理时间
        import time
        time.sleep(0.1)
        
        # 检查支付方式是否有效
        metadata = vip_tag.metadata or {}
        payment_method_id = metadata.get('auto_renewal_payment_method')
        
        if not payment_method_id:
            return False
        
        # 这里应该调用支付API
        # payment_result = PaymentService.charge(payment_method_id, amount)
        
        # 简化：90%成功率
        import random
        return random.random() > 0.1
    
    def _should_send_reminder(self, vip_tag: TenantUserTypeTag, days_remaining: int) -> bool:
        """
        检查是否应该发送续期提醒
        
        Args:
            vip_tag: VIP标签关联对象
            days_remaining: 剩余天数
            
        Returns:
            bool: 是否应该发送提醒
        """
        # 检查是否在提醒时间点
        if days_remaining not in self.VIP_CONFIG['renewal_reminder_days']:
            return False
        
        # 检查是否已发送过提醒
        if vip_tag.renewal_reminder_sent:
            # 重置提醒状态（每个时间点都可以提醒一次）
            last_reminder = vip_tag.reminder_sent_at
            if last_reminder:
                days_since_reminder = (timezone.now() - last_reminder).days
                if days_since_reminder < 1:  # 一天内不重复提醒
                    return False
        
        return True
    
    def _send_renewal_reminder(self, vip_tag: TenantUserTypeTag, days_remaining: int):
        """
        发送续期提醒
        
        Args:
            vip_tag: VIP标签关联对象
            days_remaining: 剩余天数
        """
        # 这里应该集成消息发送系统
        # 简化处理，只记录日志
        
        reminder_message = (
            f"VIP续期提醒: {vip_tag.member.username} 的 {vip_tag.tag.tag_name} "
            f"将在 {days_remaining} 天后过期"
        )
        
        self.logger.info(reminder_message)
        
        # 更新提醒状态
        vip_tag.reminder_sent_at = timezone.now()
        vip_tag.renewal_reminder_sent = True
        vip_tag.save(update_fields=['reminder_sent_at', 'renewal_reminder_sent'])
        
        # 这里可以发送邮件、短信、站内消息等
        # EmailService.send_vip_renewal_reminder(vip_tag, days_remaining)
        # SMSService.send_renewal_reminder(vip_tag, days_remaining)
    
    def _extract_payment_info(self, payment_info: Dict[str, Any]) -> Dict[str, Any]:
        """提取支付信息"""
        return {
            'payment_id': payment_info.get('payment_id'),
            'payment_amount': payment_info.get('amount'),
            'payment_currency': payment_info.get('currency', 'CNY')
        }


class VipBatchOperations:
    """
    VIP批量操作服务
    
    提供批量VIP管理功能
    """
    
    def __init__(self, vip_service: VipExpirationService):
        self.vip_service = vip_service
        self.logger = logger
    
    @transaction.atomic
    def batch_grant_vip(
        self,
        tenant: Any,
        member_ids: List[int],
        tag: UserTypeTag,
        duration_days: int,
        reason: str = "",
        operator_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        批量授予VIP
        
        Args:
            tenant: 租户对象
            member_ids: 成员ID列表
            tag: VIP标签
            duration_days: 有效期天数
            reason: 授予原因
            operator_id: 操作员ID
            
        Returns:
            Dict: 批量操作结果
        """
        from ..models import TenantUserProfile
        
        results = {
            'total_requested': len(member_ids),
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        for member_id in member_ids:
            try:
                # 获取用户档案
                profile = TenantUserProfile.objects.get(
                    member_id=member_id,
                    tenant=tenant
                )
                
                # 授予VIP
                self.vip_service.grant_vip_tag(
                    tenant_user_profile=profile,
                    tag=tag,
                    duration_days=duration_days,
                    grant_method='batch',
                    reason=f"批量操作 - {reason}",
                    operator_id=operator_id
                )
                
                results['successful'] += 1
                
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'member_id': member_id,
                    'error': str(e)
                })
        
        self.logger.info(
            f"批量VIP授予完成: 成功 {results['successful']} 个，"
            f"失败 {results['failed']} 个"
        )
        
        return results
    
    @transaction.atomic
    def batch_extend_vip(
        self,
        tenant: Any,
        tag: UserTypeTag,
        extend_days: int,
        reason: str = "",
        operator_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        批量延长VIP期限
        
        Args:
            tenant: 租户对象
            tag: VIP标签
            extend_days: 延长天数
            reason: 延长原因
            operator_id: 操作员ID
            
        Returns:
            Dict: 批量操作结果
        """
        vip_tags = TenantUserTypeTag.objects.filter(
            tenant=tenant,
            tag=tag,
            is_active=True
        )
        
        results = {
            'total_found': vip_tags.count(),
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        for vip_tag in vip_tags:
            try:
                self.vip_service.extend_vip_period(
                    vip_tag=vip_tag,
                    extend_days=extend_days,
                    reason=f"批量延期 - {reason}",
                    operator_id=operator_id
                )
                
                results['successful'] += 1
                
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'member_username': vip_tag.member.username,
                    'error': str(e)
                })
        
        self.logger.info(
            f"批量VIP延期完成: 成功 {results['successful']} 个，"
            f"失败 {results['failed']} 个"
        )
        
        return results
