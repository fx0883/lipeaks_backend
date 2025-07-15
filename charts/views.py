from django.shortcuts import render
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter

from django.db.models import Count, Q
from django.core.cache import cache
from datetime import datetime, timedelta
from collections import defaultdict

from tenants.models import Tenant
from .permissions import IsSuperAdminOnly
from .utils import (
    get_date_trunc_func, get_cache_key, format_chart_response, empty_chart_response,
    get_user_growth_trend, get_user_role_distribution, get_active_users, get_login_heatmap
)
from .schema import (
    tenant_trend_responses, tenant_status_distribution_responses, 
    tenant_creation_rate_responses, user_growth_trend_responses,
    user_role_distribution_responses, active_users_responses,
    login_heatmap_responses, period_param, date_params
)

import logging
logger = logging.getLogger(__name__)

class BaseChartView(APIView):
    """
    图表API的基类
    """
    permission_classes = [IsAuthenticated, IsSuperAdminOnly]
    
    def get_cached_data(self, cache_key, ttl=3600):
        """获取缓存数据"""
        return cache.get(cache_key)
        
    def set_cached_data(self, cache_key, data, ttl=3600):
        """设置缓存数据"""
        cache.set(cache_key, data, ttl)
        
    def format_response(self, data):
        """格式化API响应"""
        return Response({
            "code": 2000,
            "message": "success",
            "data": data
        })


class TenantTrendChartView(BaseChartView):
    """租户数量趋势图API"""
    
    @extend_schema(
        summary="获取租户数量趋势图数据",
        description="显示系统内租户总数随时间的变化趋势，可按日/周/月/季度/年统计。仅超级管理员可访问。",
        parameters=[
            OpenApiParameter(
                name='period',
                description='统计周期',
                required=False,
                type=str,
                enum=['daily', 'weekly', 'monthly', 'quarterly', 'yearly'],
                default='monthly'
            ),
            OpenApiParameter(
                name='start_date',
                description='开始日期 (YYYY-MM-DD)',
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name='end_date',
                description='结束日期 (YYYY-MM-DD)',
                required=False,
                type=str,
            )
        ],
        responses=tenant_trend_responses,
        tags=["仪表盘图表"]
    )
    def get(self, request):
        # 获取请求参数
        period = request.query_params.get('period', 'monthly')
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        
        # 设置默认日期范围
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=365)  # 默认最近一年
        
        # 解析日期参数
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
                
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # 记录查询参数
        logger.info(f"租户趋势图查询参数: period={period}, start_date={start_date}, end_date={end_date}")
        
        # 尝试从缓存获取数据
        cache_key = get_cache_key(
            'tenant_trend', 
            period=period,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
        
        cached_data = self.get_cached_data(cache_key)
        if cached_data:
            logger.debug(f"从缓存获取租户趋势图数据: {cache_key}")
            return self.format_response(cached_data)
        
        # 查询数据
        try:
            # 转换日期为datetime对象并添加时区信息
            start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
            end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
            
            # 使用Python手动按时间段统计，而不是依赖数据库函数
            all_tenants = (
                Tenant.objects
                .filter(created_at__range=(start_datetime, end_datetime))
                .order_by('created_at')
            )
            
            logger.debug(f"查询到 {all_tenants.count()} 条租户数据")
            
            # 手动按周期分组
            period_counts = defaultdict(int)
            for tenant in all_tenants:
                if period == 'daily':
                    period_key = tenant.created_at.strftime('%Y-%m-%d')
                elif period == 'weekly':
                    # 使用ISO周格式，例如：2025-W16
                    period_key = f"{tenant.created_at.isocalendar()[0]}-W{tenant.created_at.isocalendar()[1]:02d}"
                elif period == 'monthly':
                    period_key = tenant.created_at.strftime('%Y-%m')
                elif period == 'quarterly':
                    quarter = (tenant.created_at.month - 1) // 3 + 1
                    period_key = f"{tenant.created_at.year}-Q{quarter}"
                else:  # yearly
                    period_key = str(tenant.created_at.year)
                
                period_counts[period_key] += 1
            
            # 按时间排序并计算累计值
            dates = sorted(period_counts.keys())
            counts = []
            cumulative = 0
            
            for date in dates:
                cumulative += period_counts[date]
                counts.append(cumulative)
            
            # 计算汇总数据
            total = Tenant.objects.count()
            growth_rate = 0
            if len(counts) >= 2 and counts[0] > 0:
                growth_rate = ((counts[-1] - counts[0]) / counts[0]) * 100
            
            avg_growth = 0
            if len(counts) > 1:
                avg_growth = (counts[-1] - counts[0]) / len(counts)
            
            # 构建响应数据
            result = format_chart_response(
                chart_type="line",
                title="租户数量趋势",
                description="系统内租户总数随时间的变化趋势",
                labels=dates,
                datasets=[{
                    "label": "租户总数",
                    "data": counts,
                    "color": "#3366cc"
                }],
                summary={
                    "total": total,
                    "growth_rate": round(growth_rate, 1),
                    "average_period_growth": round(avg_growth, 1)
                }
            )
            
            # 如果没有数据，返回空图表
            if not dates:
                logger.debug(f"租户趋势图无数据: period={period}, start_date={start_date}, end_date={end_date}")
                result = empty_chart_response("租户数量趋势", "该时间段内无租户数据", "line")
            
            # 缓存数据
            self.set_cached_data(cache_key, result)
            logger.debug(f"租户趋势图数据已缓存: {cache_key}")
            
            return self.format_response(result)
            
        except Exception as e:
            logger.error(f"获取租户趋势数据失败: {str(e)}", exc_info=True)
            return Response({
                "code": 500,
                "message": f"获取租户趋势数据失败: {str(e)}",
                "data": None
            }, status=500)


class TenantStatusDistributionView(BaseChartView):
    """租户状态分布饼图API"""
    
    @extend_schema(
        summary="获取租户状态分布数据",
        description="显示活跃/暂停/已删除租户的比例。仅超级管理员可访问。",
        responses=tenant_status_distribution_responses,
        tags=["仪表盘图表"]
    )
    def get(self, request):
        # 尝试从缓存获取数据
        cache_key = get_cache_key('tenant_status_distribution')
        cached_data = self.get_cached_data(cache_key)
        if cached_data:
            logger.debug(f"从缓存获取租户状态分布数据: {cache_key}")
            return self.format_response(cached_data)
        
        try:
            # 查询各状态租户数量
            status_counts = []
            labels = []
            colors = []
            
            # 活跃租户
            active_count = Tenant.objects.filter(status='active').count()
            if active_count > 0:
                status_counts.append(active_count)
                labels.append('活跃')
                colors.append('#36A2EB')  # 蓝色
            
            # 暂停租户
            suspended_count = Tenant.objects.filter(status='suspended').count()
            if suspended_count > 0:
                status_counts.append(suspended_count)
                labels.append('暂停')
                colors.append('#FFCE56')  # 黄色
            
            # 已删除租户
            deleted_count = Tenant.objects.filter(Q(status='deleted') | Q(is_deleted=True)).count()
            if deleted_count > 0:
                status_counts.append(deleted_count)
                labels.append('已删除')
                colors.append('#FF6384')  # 红色
                
            total_count = sum(status_counts)
            
            # 计算百分比
            percentages = {}
            if total_count > 0:
                percentages = {
                    'active_percentage': round((active_count / total_count) * 100, 1) if active_count else 0,
                    'suspended_percentage': round((suspended_count / total_count) * 100, 1) if suspended_count else 0,
                    'deleted_percentage': round((deleted_count / total_count) * 100, 1) if deleted_count else 0
                }
            
            # 构建响应数据
            result = format_chart_response(
                chart_type="pie",
                title="租户状态分布",
                description="不同状态的租户占比",
                labels=labels,
                datasets=[{
                    "label": "租户数量",
                    "data": status_counts,
                    "colors": colors
                }],
                summary={
                    "total": total_count,
                    **percentages
                }
            )
            
            # 缓存数据 (较短的过期时间，因为状态可能会变化)
            self.set_cached_data(cache_key, result, ttl=1800)  # 30分钟
            logger.debug(f"租户状态分布数据已缓存: {cache_key}")
            
            return self.format_response(result)
            
        except Exception as e:
            logger.error(f"获取租户状态分布数据失败: {str(e)}", exc_info=True)
            return Response({
                "code": 500,
                "message": f"获取租户状态分布数据失败: {str(e)}",
                "data": None
            }, status=500)


class TenantCreationRateView(BaseChartView):
    """租户创建速率API"""
    
    @extend_schema(
        summary="获取租户创建速率数据",
        description="显示每月/每周新增租户数量。仅超级管理员可访问。",
        parameters=[
            OpenApiParameter(
                name='period',
                description='统计周期',
                required=False,
                type=str,
                enum=['weekly', 'monthly'],
                default='monthly'
            ),
            OpenApiParameter(
                name='start_date',
                description='开始日期 (YYYY-MM-DD)',
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name='end_date',
                description='结束日期 (YYYY-MM-DD)',
                required=False,
                type=str,
            )
        ],
        responses=tenant_creation_rate_responses,
        tags=["仪表盘图表"]
    )
    def get(self, request):
        # 获取请求参数
        period = request.query_params.get('period', 'monthly')
        if period not in ['weekly', 'monthly']:
            period = 'monthly'
            
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        
        # 设置默认日期范围
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=180)  # 默认最近6个月
        
        # 解析日期参数
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
                
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # 记录查询参数
        logger.info(f"租户创建速率查询参数: period={period}, start_date={start_date}, end_date={end_date}")
        
        # 尝试从缓存获取数据
        cache_key = get_cache_key(
            'tenant_creation_rate', 
            period=period,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
        
        cached_data = self.get_cached_data(cache_key)
        if cached_data:
            logger.debug(f"从缓存获取租户创建速率数据: {cache_key}")
            return self.format_response(cached_data)
        
        try:
            # 转换日期为datetime对象并添加时区信息
            start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
            end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
            
            # 使用Python手动按时间段统计，而不是依赖数据库函数
            all_tenants = (
                Tenant.objects
                .filter(created_at__range=(start_datetime, end_datetime))
                .order_by('created_at')
            )
            
            logger.debug(f"查询到 {all_tenants.count()} 条租户数据")
            
            # 手动按周期分组
            period_counts = defaultdict(int)
            for tenant in all_tenants:
                if period == 'weekly':
                    # 使用ISO周格式，例如：2025-W16
                    period_key = f"{tenant.created_at.isocalendar()[0]}-W{tenant.created_at.isocalendar()[1]:02d}"
                else:  # monthly
                    period_key = tenant.created_at.strftime('%Y-%m')
                
                period_counts[period_key] += 1
            
            # 按时间排序
            periods = sorted(period_counts.keys())
            counts = [period_counts[period_key] for period_key in periods]
            
            # 没有数据时返回空图表
            if not counts:
                empty_result = empty_chart_response("租户创建速率", "所选时间范围内没有新增租户", chart_type="bar")
                return self.format_response(empty_result)
            
            # 计算汇总数据
            total_new = sum(counts)
            avg_monthly = round(total_new / len(counts), 1) if counts else 0
            max_monthly = max(counts) if counts else 0
            
            # 判断趋势
            growth_trend = "持平"
            if len(counts) >= 2:
                # 计算后半段和前半段平均值
                half_point = len(counts) // 2
                first_half_avg = sum(counts[:half_point]) / half_point if half_point else 0
                second_half_avg = sum(counts[half_point:]) / (len(counts) - half_point) if len(counts) > half_point else 0
                
                if second_half_avg > first_half_avg * 1.1:  # 增长超过10%
                    growth_trend = "上升"
                elif second_half_avg < first_half_avg * 0.9:  # 下降超过10%
                    growth_trend = "下降"
            
            # 构建响应数据
            result = format_chart_response(
                chart_type="bar",
                title="租户创建速率",
                description=f"{'每周' if period=='weekly' else '每月'}新增租户数量",
                labels=periods,
                datasets=[{
                    "label": "新增租户",
                    "data": counts,
                    "color": "#4BC0C0"
                }],
                summary={
                    "total_new": total_new,
                    f"avg_{period}": avg_monthly,
                    f"max_{period}": max_monthly,
                    "growth_trend": growth_trend
                }
            )
            
            # 缓存数据
            self.set_cached_data(cache_key, result)
            logger.debug(f"租户创建速率数据已缓存: {cache_key}")
            
            return self.format_response(result)
            
        except Exception as e:
            logger.error(f"获取租户创建速率数据失败: {str(e)}", exc_info=True)
            return Response({
                "code": 500,
                "message": f"获取租户创建速率数据失败: {str(e)}",
                "data": None
            }, status=500)


class UserGrowthTrendView(BaseChartView):
    """用户总量与增长趋势图API"""
    
    @extend_schema(
        summary="获取用户总量与增长趋势图数据",
        description="显示系统内所有用户数量的时间序列图，可按日/周/月/季度/年统计。仅超级管理员可访问。",
        parameters=[period_param] + date_params,
        responses=user_growth_trend_responses,
        tags=["用户统计图表"]
    )
    def get(self, request):
        # 获取请求参数
        period = request.query_params.get('period', 'monthly')
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        
        # 设置默认日期范围
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=365)  # 默认最近一年
        
        # 解析日期参数
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
                
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # 记录查询参数
        logger.info(f"用户增长趋势图查询参数: period={period}, start_date={start_date}, end_date={end_date}")
        
        # 获取数据
        data = get_user_growth_trend(start_date, end_date, period)
        
        return self.format_response(data)


class UserRoleDistributionView(BaseChartView):
    """用户角色分布图API"""
    
    @extend_schema(
        summary="获取用户角色分布数据",
        description="显示超级管理员、租户管理员、普通用户的比例。仅超级管理员可访问。",
        responses=user_role_distribution_responses,
        tags=["用户统计图表"]
    )
    def get(self, request):
        # 记录查询
        logger.info("请求用户角色分布数据")
        
        # 获取数据
        data = get_user_role_distribution()
        
        return self.format_response(data)


class ActiveUsersView(BaseChartView):
    """活跃用户统计API"""
    
    @extend_schema(
        summary="获取活跃用户统计数据",
        description="按日/周/月统计的活跃用户数量。仅超级管理员可访问。",
        parameters=[
            OpenApiParameter(
                name='period',
                description='统计周期',
                required=False,
                type=str,
                enum=['daily', 'weekly', 'monthly'],
                default='daily'
            )
        ] + date_params,
        responses=active_users_responses,
        tags=["用户统计图表"]
    )
    def get(self, request):
        # 获取请求参数
        period = request.query_params.get('period', 'daily')
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        
        # 设置默认日期范围
        end_date = timezone.now().date()
        
        # 根据周期设置默认开始日期
        if period == 'daily':
            start_date = end_date - timedelta(days=30)  # 最近30天
        elif period == 'weekly':
            start_date = end_date - timedelta(days=90)  # 最近13周
        else:  # monthly
            start_date = end_date - timedelta(days=365)  # 最近12个月
        
        # 解析日期参数
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
                
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # 记录查询参数
        logger.info(f"活跃用户统计图查询参数: period={period}, start_date={start_date}, end_date={end_date}")
        
        # 获取数据
        data = get_active_users(start_date, end_date, period)
        
        return self.format_response(data)


class LoginHeatmapView(BaseChartView):
    """用户登录热力图API"""
    
    @extend_schema(
        summary="获取用户登录热力图数据",
        description="显示不同时间段的登录活跃度。仅超级管理员可访问。",
        parameters=date_params,
        responses=login_heatmap_responses,
        tags=["用户统计图表"]
    )
    def get(self, request):
        # 获取请求参数
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')
        
        # 设置默认日期范围
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)  # 最近30天
        
        # 解析日期参数
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
                
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        # 记录查询参数
        logger.info(f"用户登录热力图查询参数: start_date={start_date}, end_date={end_date}")
        
        # 获取数据
        data = get_login_heatmap(start_date, end_date)
        
        return self.format_response(data)
