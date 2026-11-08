"""
每日连续签到与成长激励服务
支持应用级专属签到与租户全局签到，提供原子性并发防重与等级联动
"""
import logging
from datetime import date, timedelta
from typing import Optional, Dict, Any

from django.db import transaction
from django.utils import timezone

from common.exceptions import PointsException
from points.models import (
    CheckinConfig,
    UserCheckinStreak,
    UserCheckinRecord,
    TenantUserProfile,
    AppUserPointsAccount,
    TenantUserPoints
)

logger = logging.getLogger(__name__)


class CheckinService:
    """
    签到业务引擎服务
    """

    @classmethod
    def get_or_create_config(cls, tenant, application=None) -> CheckinConfig:
        """
        获取或初始化签到规则配置
        """
        config, created = CheckinConfig.objects.get_or_create(
            tenant=tenant,
            application=application,
            defaults={
                'name': f"{application.name if application else '全局'}每日签到",
                'cycle_days': 7,
                'cycle_mode': 'repeat',
                'reward_ladder': CheckinConfig.get_default_ladder(),
                'allow_recheckin': False,
                'recheckin_cost': 50,
                'is_active': True,
            }
        )
        return config

    @classmethod
    def get_checkin_status(
        cls,
        member,
        tenant,
        application=None,
        today: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        查询用户当前的签到状态与日历数据
        """
        today = today or timezone.localdate()
        yesterday = today - timedelta(days=1)

        config = cls.get_or_create_config(tenant, application)

        streak = UserCheckinStreak.objects.filter(
            tenant=tenant,
            application=application,
            member=member
        ).first()

        current_streak = streak.current_streak if streak else 0
        max_streak = streak.max_streak if streak else 0
        total_days = streak.total_days if streak else 0
        last_checkin_date = streak.last_checkin_date if streak else None

        has_checked_in_today = (last_checkin_date == today)

        # 预测下一打卡属于第几天
        if has_checked_in_today:
            active_streak_day = current_streak
            next_day_streak = current_streak + 1
        elif last_checkin_date == yesterday:
            active_streak_day = current_streak + 1
            next_day_streak = current_streak + 2
        else:
            # 断签或首次签到，从第 1 天重新开始
            active_streak_day = 1
            next_day_streak = 2

        today_points = config.get_points_for_day(active_streak_day)
        tomorrow_points = config.get_points_for_day(next_day_streak)

        # 生成周期日历状态
        cycle = max(config.cycle_days, 1)
        # 当前在周期中的位置 (1 ~ cycle)
        cycle_position = ((active_streak_day - 1) % cycle) + 1 if config.cycle_mode == 'repeat' else min(active_streak_day, cycle)

        calendar = []
        ladder = config.reward_ladder if config.reward_ladder else config.get_default_ladder()
        ladder_map = {item.get('day'): item.get('points', 0) for item in ladder if isinstance(item, dict)}

        for d in range(1, cycle + 1):
            day_points = ladder_map.get(d, config.get_points_for_day(d))
            if has_checked_in_today:
                if d <= cycle_position:
                    day_status = 'checked'
                else:
                    day_status = 'upcoming'
            else:
                if d < cycle_position:
                    day_status = 'checked'
                elif d == cycle_position:
                    day_status = 'current'
                else:
                    day_status = 'upcoming'

            calendar.append({
                'day': d,
                'points': day_points,
                'status': day_status,
                'is_today': (d == cycle_position),
                'label': f"第{d}天"
            })

        # 统计近 14 天漏签日期（供补签使用）
        missed_dates = []
        if config.allow_recheckin:
            checked_dates_set = set(
                UserCheckinRecord.objects.filter(
                    tenant=tenant,
                    application=application,
                    member=member,
                    checkin_date__gte=today - timedelta(days=14),
                    checkin_date__lt=today
                ).values_list('checkin_date', flat=True)
            )
            for i in range(1, 15):
                past_date = today - timedelta(days=i)
                if past_date not in checked_dates_set:
                    missed_dates.append({
                        'date': past_date.isoformat(),
                        'cost': config.recheckin_cost
                    })

        return {
            'has_checked_in_today': has_checked_in_today,
            'current_streak': current_streak,
            'max_streak': max_streak,
            'total_days': total_days,
            'last_checkin_date': last_checkin_date.isoformat() if last_checkin_date else None,
            'today_reward': today_points,
            'tomorrow_reward': tomorrow_points,
            'cycle_days': config.cycle_days,
            'cycle_mode': config.cycle_mode,
            'is_active': config.is_active,
            'allow_recheckin': config.allow_recheckin,
            'recheckin_cost': config.recheckin_cost,
            'missed_dates': missed_dates,
            'calendar': calendar
        }

    @classmethod
    @transaction.atomic
    def execute_checkin(
        cls,
        member,
        tenant,
        application=None,
        today: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        执行每日签到打卡（支持加锁防并发与等级提升检查）
        """
        today = today or timezone.localdate()
        yesterday = today - timedelta(days=1)

        config = cls.get_or_create_config(tenant, application)
        if not config.is_active:
            raise PointsException(
                error_code="CHECKIN_DISABLED",
                detail="该应用暂未开启每日签到功能"
            )

        # 1. 显式行锁锁定用户连续打卡统计，杜绝并发竞争
        streak, _ = UserCheckinStreak.objects.select_for_update().get_or_create(
            tenant=tenant,
            application=application,
            member=member,
            defaults={
                'current_streak': 0,
                'max_streak': 0,
                'total_days': 0,
                'last_checkin_date': None
            }
        )

        # 2. 防重检查
        if streak.last_checkin_date == today:
            raise PointsException(
                error_code="ALREADY_CHECKED_IN",
                detail="今日已完成签到，请明天再来"
            )

        # 3. 计算连续天数（断签判定）
        if streak.last_checkin_date == yesterday:
            new_streak = streak.current_streak + 1
        else:
            new_streak = 1

        # 4. 依据阶梯规则计算奖励积分
        reward_points = config.get_points_for_day(new_streak)

        level_upgraded = False
        current_level_name = None
        new_balance = 0

        # 5. 积分入账分流：应用专属账户 vs 租户全局档案
        if application:
            profile, _ = TenantUserProfile.objects.get_or_create(
                tenant=tenant,
                member=member,
                defaults={'is_points_enabled': True}
            )
            account, _ = AppUserPointsAccount.objects.select_for_update().get_or_create(
                tenant=tenant,
                application=application,
                member=member,
                defaults={
                    'tenant_user_profile': profile,
                    'is_enabled': True,
                    'available_points': 0,
                    'total_points': 0
                }
            )
            if not account.is_enabled:
                raise PointsException(
                    error_code="POINTS_DISABLED",
                    detail="用户在该应用的积分账户已被停用"
                )

            balance_before = account.available_points
            account.available_points += reward_points
            account.total_points += reward_points
            account.points_earned_total += reward_points
            account.last_points_update = timezone.now()
            account.save(update_fields=[
                'available_points',
                'total_points',
                'points_earned_total',
                'last_points_update'
            ])

            # 触发应用等级升级检验
            level_upgraded = account.check_level_upgrade()
            account.refresh_from_db()
            current_level_name = account.current_level.level_name if account.current_level else None
            new_balance = account.available_points

            # 写入通用积分明细账
            TenantUserPoints.objects.create(
                tenant=tenant,
                member=member,
                tenant_user_profile=profile,
                application=application,
                app_account=account,
                point_type='earn',
                category='checkin',
                source_type='api',
                points=reward_points,
                balance_before=balance_before,
                balance_after=new_balance,
                operation_reason=f"应用【{application.name}】连续签到第{new_streak}天奖励",
                status='active'
            )
        else:
            profile, _ = TenantUserProfile.objects.select_for_update().get_or_create(
                tenant=tenant,
                member=member,
                defaults={'is_points_enabled': True}
            )
            if not profile.is_points_enabled:
                raise PointsException(
                    error_code="POINTS_DISABLED",
                    detail="租户积分账户已被停用"
                )

            balance_before = profile.available_points
            profile.available_points += reward_points
            profile.total_points += reward_points
            profile.points_earned_total += reward_points
            profile.last_points_update = timezone.now()
            profile.save(update_fields=[
                'available_points',
                'total_points',
                'points_earned_total',
                'last_points_update'
            ])

            new_balance = profile.available_points
            current_level_name = profile.current_level.level_name if profile.current_level else None

            TenantUserPoints.objects.create(
                tenant=tenant,
                member=member,
                tenant_user_profile=profile,
                point_type='earn',
                category='checkin',
                source_type='api',
                points=reward_points,
                balance_before=balance_before,
                balance_after=new_balance,
                operation_reason=f"平台连续签到第{new_streak}天奖励",
                status='active'
            )

        # 6. 更新连续打卡统计状态
        streak.current_streak = new_streak
        streak.max_streak = max(streak.max_streak, new_streak)
        streak.total_days += 1
        streak.last_checkin_date = today
        streak.save(update_fields=[
            'current_streak',
            'max_streak',
            'total_days',
            'last_checkin_date',
            'updated_at'
        ])

        # 7. 写入每日打卡明细留痕
        UserCheckinRecord.objects.create(
            tenant=tenant,
            application=application,
            member=member,
            checkin_date=today,
            streak_day=new_streak,
            reward_points=reward_points,
            is_recheckin=False
        )

        logger.info(
            f"成员 {member.username} 完成【{application.name if application else '全局'}】签到: "
            f"第{new_streak}天, 获{reward_points}积分, 最新余额={new_balance}"
        )

        return {
            'success': True,
            'points_earned': reward_points,
            'current_streak': new_streak,
            'total_days': streak.total_days,
            'new_balance': new_balance,
            'level_upgraded': level_upgraded,
            'current_level': current_level_name,
            'checkin_date': today.isoformat()
        }

    @classmethod
    @transaction.atomic
    def execute_recheckin(
        cls,
        member,
        tenant,
        target_date: date,
        application=None
    ) -> Dict[str, Any]:
        """
        执行补签打卡操作
        """
        if isinstance(target_date, str):
            from datetime import datetime
            target_date = datetime.strptime(target_date, "%Y-%m-%d").date()

        today = timezone.localdate()

        if target_date >= today:
            raise PointsException(
                error_code="INVALID_RECHECKIN_DATE",
                detail="只能补签过去的日期，今日及未来日期不可补签"
            )

        if (today - target_date).days > 30:
            raise PointsException(
                error_code="RECHECKIN_EXPIRED",
                detail="超出补签有效期，仅支持补签近30天内的漏签记录"
            )

        config = cls.get_or_create_config(tenant, application)
        if not config.is_active:
            raise PointsException(
                error_code="CHECKIN_DISABLED",
                detail="该应用暂未开启每日签到功能"
            )
        if not config.allow_recheckin:
            raise PointsException(
                error_code="RECHECKIN_DISABLED",
                detail="该应用未开启补签功能"
            )

        # 1. 行级排他锁锁定用户打卡状态
        streak, _ = UserCheckinStreak.objects.select_for_update().get_or_create(
            tenant=tenant,
            application=application,
            member=member,
            defaults={
                'current_streak': 0,
                'max_streak': 0,
                'total_days': 0,
                'last_checkin_date': None
            }
        )

        # 2. 检查该日期是否已经签到或补签
        if UserCheckinRecord.objects.filter(
            tenant=tenant,
            application=application,
            member=member,
            checkin_date=target_date
        ).exists():
            raise PointsException(
                error_code="ALREADY_CHECKED_IN",
                detail=f"{target_date.isoformat()} 已经完成过签到或补签，无需重复补签"
            )

        # 3. 补签消耗积分扣除
        cost = max(config.recheckin_cost, 0)
        level_upgraded = False
        current_level_name = None
        new_balance = 0

        if application:
            profile, _ = TenantUserProfile.objects.get_or_create(
                tenant=tenant,
                member=member,
                defaults={'is_points_enabled': True}
            )
            account, _ = AppUserPointsAccount.objects.select_for_update().get_or_create(
                tenant=tenant,
                application=application,
                member=member,
                defaults={
                    'tenant_user_profile': profile,
                    'is_enabled': True,
                    'available_points': 0,
                    'total_points': 0
                }
            )
            if not account.is_enabled:
                raise PointsException(
                    error_code="POINTS_DISABLED",
                    detail="用户在该应用的积分账户已被停用"
                )

            if cost > 0:
                if account.available_points < cost:
                    raise PointsException(
                        error_code="INSUFFICIENT_POINTS",
                        detail=f"积分不足，补签需要消耗 {cost} 积分，当前可用积分仅为 {account.available_points}"
                    )
                # 扣除补签消耗积分
                balance_before_deduct = account.available_points
                account.available_points -= cost
                account.points_spent_total += cost
                account.last_points_update = timezone.now()
                account.save(update_fields=['available_points', 'points_spent_total', 'last_points_update'])

                TenantUserPoints.objects.create(
                    tenant=tenant,
                    member=member,
                    tenant_user_profile=profile,
                    application=application,
                    app_account=account,
                    point_type='spend',
                    category='checkin',
                    subcategory='recheckin_cost',
                    source_type='api',
                    points=-cost,
                    balance_before=balance_before_deduct,
                    balance_after=account.available_points,
                    operation_reason=f"应用【{application.name}】补签扣除积分（补签日期：{target_date}）",
                    status='active'
                )

            # 4. 计算补签日期归属的连续阶梯序号
            prior_streak = 0
            check_day = target_date - timedelta(days=1)
            while UserCheckinRecord.objects.filter(
                tenant=tenant, application=application, member=member, checkin_date=check_day
            ).exists():
                prior_streak += 1
                check_day -= timedelta(days=1)
            target_streak_day = prior_streak + 1

            reward_points = config.get_points_for_day(target_streak_day)

            # 5. 发放补签日奖励积分
            balance_before_reward = account.available_points
            account.available_points += reward_points
            account.total_points += reward_points
            account.points_earned_total += reward_points
            account.last_points_update = timezone.now()
            account.save(update_fields=['available_points', 'total_points', 'points_earned_total', 'last_points_update'])

            level_upgraded = account.check_level_upgrade()
            account.refresh_from_db()
            current_level_name = account.current_level.level_name if account.current_level else None
            new_balance = account.available_points

            TenantUserPoints.objects.create(
                tenant=tenant,
                member=member,
                tenant_user_profile=profile,
                application=application,
                app_account=account,
                point_type='earn',
                category='checkin',
                subcategory='recheckin_reward',
                source_type='api',
                points=reward_points,
                balance_before=balance_before_reward,
                balance_after=new_balance,
                operation_reason=f"应用【{application.name}】补签【{target_date}】第{target_streak_day}天奖励",
                status='active'
            )
        else:
            profile, _ = TenantUserProfile.objects.select_for_update().get_or_create(
                tenant=tenant,
                member=member,
                defaults={'is_points_enabled': True}
            )
            if not profile.is_points_enabled:
                raise PointsException(
                    error_code="POINTS_DISABLED",
                    detail="租户积分账户已被停用"
                )

            if cost > 0:
                if profile.available_points < cost:
                    raise PointsException(
                        error_code="INSUFFICIENT_POINTS",
                        detail=f"积分不足，补签需要消耗 {cost} 积分，当前可用积分仅为 {profile.available_points}"
                    )
                balance_before_deduct = profile.available_points
                profile.available_points -= cost
                profile.points_spent_total += cost
                profile.last_points_update = timezone.now()
                profile.save(update_fields=['available_points', 'points_spent_total', 'last_points_update'])

                TenantUserPoints.objects.create(
                    tenant=tenant,
                    member=member,
                    tenant_user_profile=profile,
                    point_type='spend',
                    category='checkin',
                    subcategory='recheckin_cost',
                    source_type='api',
                    points=-cost,
                    balance_before=balance_before_deduct,
                    balance_after=profile.available_points,
                    operation_reason=f"平台补签扣除积分（补签日期：{target_date}）",
                    status='active'
                )

            prior_streak = 0
            check_day = target_date - timedelta(days=1)
            while UserCheckinRecord.objects.filter(
                tenant=tenant, application=None, member=member, checkin_date=check_day
            ).exists():
                prior_streak += 1
                check_day -= timedelta(days=1)
            target_streak_day = prior_streak + 1

            reward_points = config.get_points_for_day(target_streak_day)

            balance_before_reward = profile.available_points
            profile.available_points += reward_points
            profile.total_points += reward_points
            profile.points_earned_total += reward_points
            profile.last_points_update = timezone.now()
            profile.save(update_fields=['available_points', 'total_points', 'points_earned_total', 'last_points_update'])

            new_balance = profile.available_points
            current_level_name = profile.current_level.level_name if profile.current_level else None

            TenantUserPoints.objects.create(
                tenant=tenant,
                member=member,
                tenant_user_profile=profile,
                point_type='earn',
                category='checkin',
                subcategory='recheckin_reward',
                source_type='api',
                points=reward_points,
                balance_before=balance_before_reward,
                balance_after=new_balance,
                operation_reason=f"平台补签【{target_date}】第{target_streak_day}天奖励",
                status='active'
            )

        # 6. 写入补签记录
        UserCheckinRecord.objects.create(
            tenant=tenant,
            application=application,
            member=member,
            checkin_date=target_date,
            streak_day=target_streak_day,
            reward_points=reward_points,
            is_recheckin=True,
            extra_data={'cost_points': cost}
        )

        # 7. 重新推导与修正 UserCheckinStreak 连续打卡状态
        streak.total_days += 1

        has_today = UserCheckinRecord.objects.filter(
            tenant=tenant, application=application, member=member, checkin_date=today
        ).exists()
        anchor = today if has_today else today - timedelta(days=1)

        cur_streak = 0
        while UserCheckinRecord.objects.filter(
            tenant=tenant, application=application, member=member, checkin_date=anchor
        ).exists():
            cur_streak += 1
            anchor -= timedelta(days=1)

        streak.current_streak = cur_streak
        streak.max_streak = max(streak.max_streak, cur_streak)

        latest_record = UserCheckinRecord.objects.filter(
            tenant=tenant, application=application, member=member
        ).order_by('-checkin_date').first()
        if latest_record:
            streak.last_checkin_date = latest_record.checkin_date

        streak.save(update_fields=[
            'current_streak',
            'max_streak',
            'total_days',
            'last_checkin_date',
            'updated_at'
        ])

        logger.info(
            f"成员 {member.username} 成功补签【{application.name if application else '全局'}】"
            f"日期 {target_date}: 消耗{cost}分, 获得{reward_points}分, 连签更新为{cur_streak}天"
        )

        return {
            'success': True,
            'target_date': target_date.isoformat(),
            'cost_points': cost,
            'points_earned': reward_points,
            'net_points_change': reward_points - cost,
            'current_streak': cur_streak,
            'total_days': streak.total_days,
            'new_balance': new_balance,
            'level_upgraded': level_upgraded,
            'current_level': current_level_name
        }
