"""
积分引擎服务

提供积分获取、消费、过期处理等核心功能
"""
import logging
from typing import Optional, Dict, List, Any
from decimal import Decimal
from datetime import datetime, timedelta

from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from ..models import (
    TenantUserProfile,
    TenantUserPoints,
    UserLevel,
    TenantUserTypeTag
)

logger = logging.getLogger(__name__)


class PointsEngine:
    """
    积分引擎核心服务
    
    负责处理积分的获取、消费、过期管理以及等级升级逻辑
    """
    
    # 积分来源配置
    POINTS_SOURCES = {
        'login': {'default_points': 10, 'max_daily': 50, 'description': '每日登录奖励'},
        'consecutive_login': {'base_points': 5, 'max_streak': 30, 'description': '连续登录奖励'},
        'license_activation': {'default_points': 100, 'description': '许可证激活奖励'},
        'license_renewal': {'default_points': 50, 'description': '许可证续期奖励'},
        'referral': {'default_points': 200, 'description': '推荐用户奖励'},
        'community': {'default_points': 20, 'description': '社区活动奖励'},
        'payment': {'rate': 0.01, 'description': '付费积分奖励（1%返点）'},
        'manual': {'description': '手动调整'},
    }
    
    # 积分消费配置  
    POINTS_CONSUMPTION = {
        'vip_upgrade': {'cost': 1000, 'description': 'VIP升级'},
        'license_discount': {'rate': 0.01, 'description': '许可证折扣（1分=1分钱）'},
        'feature_unlock': {'cost': 500, 'description': '功能解锁'},
        'priority_support': {'cost': 200, 'description': '优先技术支持'},
    }
    
    def __init__(self):
        self.logger = logger
    
    @transaction.atomic
    def award_points(
        self,
        tenant_user_profile: TenantUserProfile,
        points: int,
        category: str,
        subcategory: str = "",
        reason: str = "",
        source_type: str = "system",
        source_id: Optional[int] = None,
        expires_days: Optional[int] = None,
        operator_id: Optional[int] = None
    ) -> TenantUserPoints:
        """
        奖励积分
        
        Args:
            tenant_user_profile: 租户用户档案
            points: 奖励积分数量
            category: 业务分类
            subcategory: 子分类
            reason: 奖励原因
            source_type: 来源类型
            source_id: 来源记录ID
            expires_days: 过期天数（None表示永不过期）
            operator_id: 操作员ID
            
        Returns:
            TenantUserPoints: 积分记录
        """
        if points <= 0:
            raise ValueError("奖励积分必须大于0")
        
        if not tenant_user_profile.is_points_enabled:
            raise ValidationError("该用户未启用积分功能")
        
        # 应用积分倍数
        actual_points = int(points * tenant_user_profile.points_multiplier)
        
        # 检查每日限额（如果有配置）
        if category in self.POINTS_SOURCES:
            source_config = self.POINTS_SOURCES[category]
            if 'max_daily' in source_config:
                today_points = self._get_daily_points(tenant_user_profile, category)
                if today_points + actual_points > source_config['max_daily']:
                    raise ValidationError(f"今日{source_config['description']}积分已达上限")
        
        # 计算过期时间
        expires_at = None
        if expires_days:
            expires_at = timezone.now() + timedelta(days=expires_days)
        
        # 创建积分记录
        points_record = TenantUserPoints.create_points_record(
            tenant_user_profile=tenant_user_profile,
            point_type='earn',
            category=category,
            points=actual_points,
            subcategory=subcategory,
            operation_reason=reason,
            source_type=source_type,
            source_id=source_id,
            expires_at=expires_at,
            operator_id=operator_id,
            original_points=points
        )
        
        # 更新用户积分
        tenant_user_profile.add_points(actual_points, reason, source_type)
        
        # 检查等级升级
        self._check_level_upgrade(tenant_user_profile)
        
        self.logger.info(
            f"积分奖励成功: {tenant_user_profile.member.username}@{tenant_user_profile.tenant.name} "
            f"获得 {actual_points} 积分 (原始: {points}) - {reason}"
        )
        
        return points_record
    
    @transaction.atomic
    def consume_points(
        self,
        tenant_user_profile: TenantUserProfile,
        points: int,
        category: str,
        subcategory: str = "",
        reason: str = "",
        source_type: str = "system",
        source_id: Optional[int] = None,
        operator_id: Optional[int] = None
    ) -> TenantUserPoints:
        """
        消费积分
        
        Args:
            tenant_user_profile: 租户用户档案
            points: 消费积分数量
            category: 业务分类
            subcategory: 子分类
            reason: 消费原因
            source_type: 来源类型
            source_id: 来源记录ID
            operator_id: 操作员ID
            
        Returns:
            TenantUserPoints: 积分记录
        """
        if points <= 0:
            raise ValueError("消费积分必须大于0")
        
        if not tenant_user_profile.is_points_enabled:
            raise ValidationError("该用户未启用积分功能")
        
        if tenant_user_profile.available_points < points:
            raise ValidationError(
                f"积分余额不足，当前可用: {tenant_user_profile.available_points}，需要: {points}"
            )
        
        # 创建消费记录（负数）
        points_record = TenantUserPoints.create_points_record(
            tenant_user_profile=tenant_user_profile,
            point_type='spend',
            category=category,
            points=-points,
            subcategory=subcategory,
            operation_reason=reason,
            source_type=source_type,
            source_id=source_id,
            operator_id=operator_id
        )
        
        # 扣除用户积分
        tenant_user_profile.spend_points(points, reason)
        
        self.logger.info(
            f"积分消费成功: {tenant_user_profile.member.username}@{tenant_user_profile.tenant.name} "
            f"消费 {points} 积分 - {reason}"
        )
        
        return points_record
    
    def award_login_points(self, tenant_user_profile: TenantUserProfile) -> Optional[TenantUserPoints]:
        """
        奖励登录积分
        
        Args:
            tenant_user_profile: 租户用户档案
            
        Returns:
            TenantUserPoints: 积分记录，如果今日已获得则返回None
        """
        # 更新连续登录天数
        streak_days = tenant_user_profile.update_login_streak()
        
        # 检查今日是否已获得登录积分
        today_points = self._get_daily_points(tenant_user_profile, 'login')
        if today_points > 0:
            self.logger.info(f"用户 {tenant_user_profile.member.username} 今日已获得登录积分")
            return None
        
        # 基础登录积分
        base_points = self.POINTS_SOURCES['login']['default_points']
        
        # 连续登录奖励
        consecutive_bonus = 0
        if streak_days > 1:
            consecutive_config = self.POINTS_SOURCES['consecutive_login']
            max_streak = consecutive_config['max_streak']
            bonus_points = consecutive_config['base_points']
            
            # 连续登录奖励递增，但有上限
            consecutive_bonus = min(streak_days - 1, max_streak) * bonus_points
        
        total_points = base_points + consecutive_bonus
        
        # 奖励积分
        reason = f"每日登录奖励"
        if consecutive_bonus > 0:
            reason += f" + 连续登录{streak_days}天奖励"
        
        return self.award_points(
            tenant_user_profile=tenant_user_profile,
            points=total_points,
            category='login',
            subcategory='daily_login',
            reason=reason
        )
    
    def award_license_points(
        self,
        tenant_user_profile: TenantUserProfile,
        action: str,
        license_key: str,
        license_value: Optional[Decimal] = None
    ) -> TenantUserPoints:
        """
        奖励许可证相关积分
        
        Args:
            tenant_user_profile: 租户用户档案
            action: 动作类型（activation, renewal）
            license_key: 许可证密钥
            license_value: 许可证价值（用于计算比例奖励）
            
        Returns:
            TenantUserPoints: 积分记录
        """
        if action == 'activation':
            points = self.POINTS_SOURCES['license_activation']['default_points']
            reason = f"激活许可证 {license_key}"
            subcategory = 'activation'
        elif action == 'renewal':
            points = self.POINTS_SOURCES['license_renewal']['default_points']
            reason = f"续期许可证 {license_key}"
            subcategory = 'renewal'
        else:
            raise ValueError(f"不支持的许可证动作: {action}")
        
        # 如果有许可证价值，增加比例奖励
        if license_value:
            value_bonus = int(license_value * Decimal('0.001'))  # 0.1%返点
            points += value_bonus
            reason += f" (价值奖励: +{value_bonus})"
        
        return self.award_points(
            tenant_user_profile=tenant_user_profile,
            points=points,
            category='license',
            subcategory=subcategory,
            reason=reason,
            source_type='system'
        )
    
    def process_expired_points(self, tenant: Optional[Any] = None) -> Dict[str, int]:
        """
        处理过期积分
        
        Args:
            tenant: 租户对象，None表示处理所有租户
            
        Returns:
            Dict: 处理结果统计
        """
        from django.db.models import Q
        
        now = timezone.now()
        
        # 查询已过期但未处理的积分记录
        expired_queryset = TenantUserPoints.objects.filter(
            expires_at__lt=now,
            status='active',
            point_type='earn'
        )
        
        if tenant:
            expired_queryset = expired_queryset.filter(tenant=tenant)
        
        expired_records = list(expired_queryset.select_related('tenant_user_profile'))
        
        stats = {
            'processed_records': 0,
            'total_expired_points': 0,
            'affected_users': set()
        }
        
        with transaction.atomic():
            for record in expired_records:
                # 标记积分为过期
                record.expire_points(f"系统自动过期处理 - {now.strftime('%Y-%m-%d %H:%M')}")
                
                # 从用户可用积分中扣除
                profile = record.tenant_user_profile
                if profile.available_points >= record.points:
                    profile.available_points -= record.points
                    profile.points_expired_total += record.points
                    profile.save(update_fields=['available_points', 'points_expired_total'])
                
                stats['processed_records'] += 1
                stats['total_expired_points'] += record.points
                stats['affected_users'].add(record.member.id)
        
        stats['affected_users'] = len(stats['affected_users'])
        
        self.logger.info(
            f"积分过期处理完成: 处理 {stats['processed_records']} 条记录，"
            f"过期积分 {stats['total_expired_points']} 分，"
            f"影响用户 {stats['affected_users']} 人"
        )
        
        return stats
    
    def calculate_points_value(self, points: int, currency: str = 'CNY') -> Decimal:
        """
        计算积分价值
        
        Args:
            points: 积分数量
            currency: 货币类型
            
        Returns:
            Decimal: 积分价值
        """
        # 默认汇率配置（1积分 = 0.01元）
        exchange_rates = {
            'CNY': Decimal('0.01'),
            'USD': Decimal('0.0014'), 
            'EUR': Decimal('0.0013'),
        }
        
        rate = exchange_rates.get(currency, exchange_rates['CNY'])
        return Decimal(points) * rate
    
    def get_points_leaderboard(
        self,
        tenant: Any,
        period: str = 'month',
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        获取积分排行榜
        
        Args:
            tenant: 租户对象
            period: 统计周期（week, month, year, all）
            limit: 返回条数限制
            
        Returns:
            List[Dict]: 排行榜数据
        """
        from django.db.models import Sum, Count
        from datetime import timedelta
        
        # 计算时间范围
        now = timezone.now()
        if period == 'week':
            start_date = now - timedelta(days=7)
        elif period == 'month':
            start_date = now - timedelta(days=30)
        elif period == 'year':
            start_date = now - timedelta(days=365)
        else:  # all
            start_date = None
        
        # 查询用户积分统计
        queryset = TenantUserProfile.objects.filter(tenant=tenant, is_points_enabled=True)
        
        # 根据周期选择不同的排序方式
        if start_date:
            # 统计期间内获得的积分
            queryset = queryset.annotate(
                period_earned_points=Sum(
                    'points_records__points',
                    filter=models.Q(
                        points_records__point_type='earn',
                        points_records__created_at__gte=start_date
                    )
                ) or 0
            ).order_by('-period_earned_points')
        else:
            # 使用总积分排序
            queryset = queryset.order_by('-total_points')
        
        # 限制结果数量
        queryset = queryset[:limit].select_related('member', 'current_level')
        
        # 构建排行榜数据
        leaderboard = []
        for rank, profile in enumerate(queryset, 1):
            leaderboard.append({
                'rank': rank,
                'username': profile.member.username,
                'avatar': getattr(profile.member, 'avatar', ''),
                'total_points': profile.total_points,
                'current_level': {
                    'name': profile.current_level.level_name if profile.current_level else '无等级',
                    'color': profile.current_level.level_color if profile.current_level else '#999999'
                },
                'period_points': getattr(profile, 'period_earned_points', profile.total_points),
                'consecutive_login_days': profile.consecutive_login_days
            })
        
        return leaderboard
    
    def _get_daily_points(self, tenant_user_profile: TenantUserProfile, category: str) -> int:
        """获取当日指定分类的积分总数"""
        today = timezone.now().date()
        
        return TenantUserPoints.objects.filter(
            tenant_user_profile=tenant_user_profile,
            category=category,
            point_type='earn',
            created_at__date=today
        ).aggregate(total=models.Sum('points'))['total'] or 0
    
    def _check_level_upgrade(self, tenant_user_profile: TenantUserProfile) -> bool:
        """
        检查并处理等级升级
        
        Args:
            tenant_user_profile: 租户用户档案
            
        Returns:
            bool: 是否发生了等级升级
        """
        return tenant_user_profile.check_level_upgrade()
    
    @classmethod
    def get_points_statistics(
        cls,
        tenant_user_profile: TenantUserProfile,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        获取用户积分统计
        
        Args:
            tenant_user_profile: 租户用户档案
            days: 统计天数
            
        Returns:
            Dict: 积分统计数据
        """
        return TenantUserPoints.get_points_summary(tenant_user_profile, days)


class UserLevelService:
    """
    用户等级服务
    
    负责用户等级的计算和管理
    """
    
    def __init__(self):
        self.logger = logger
    
    def calculate_user_level(self, total_points: int) -> Optional[UserLevel]:
        """
        根据积分计算用户等级
        
        Args:
            total_points: 总积分
            
        Returns:
            UserLevel: 对应的用户等级，None表示无等级
        """
        # 查找匹配的等级（按序号降序，找到第一个满足条件的）
        levels = UserLevel.objects.filter(
            is_active=True,
            min_points__lte=total_points
        ).order_by('-level_order')
        
        for level in levels:
            if level.is_points_in_range(total_points):
                return level
        
        # 如果没找到匹配的等级，返回默认等级
        return UserLevel.objects.filter(is_default=True, is_active=True).first()
    
    def get_next_level(self, current_level: Optional[UserLevel]) -> Optional[UserLevel]:
        """
        获取下一个等级
        
        Args:
            current_level: 当前等级
            
        Returns:
            UserLevel: 下一个等级，None表示已是最高等级
        """
        if not current_level:
            # 如果当前无等级，返回最低等级
            return UserLevel.objects.filter(is_active=True).order_by('level_order').first()
        
        return UserLevel.objects.filter(
            is_active=True,
            level_order__gt=current_level.level_order
        ).order_by('level_order').first()
    
    def get_level_progress(
        self,
        tenant_user_profile: TenantUserProfile
    ) -> Dict[str, Any]:
        """
        获取等级进度信息
        
        Args:
            tenant_user_profile: 租户用户档案
            
        Returns:
            Dict: 等级进度信息
        """
        current_level = tenant_user_profile.current_level
        next_level = self.get_next_level(current_level)
        
        progress_info = {
            'current_level': {
                'name': current_level.level_name if current_level else '无等级',
                'color': current_level.level_color if current_level else '#999999',
                'min_points': current_level.min_points if current_level else 0,
                'max_points': current_level.max_points if current_level else None
            },
            'current_points': tenant_user_profile.total_points,
            'next_level': None,
            'points_to_next': None,
            'progress_percentage': 0
        }
        
        if next_level:
            points_needed = next_level.min_points - tenant_user_profile.total_points
            progress_info.update({
                'next_level': {
                    'name': next_level.level_name,
                    'color': next_level.level_color,
                    'min_points': next_level.min_points
                },
                'points_to_next': max(0, points_needed),
                'progress_percentage': min(100, 
                    (tenant_user_profile.total_points / next_level.min_points) * 100
                ) if next_level.min_points > 0 else 100
            })
        else:
            # 已是最高等级
            progress_info['progress_percentage'] = 100
        
        return progress_info


# 为保持API兼容性，创建服务类别名
PointsEngineService = PointsEngine
UserLevelService = UserLevelService
