from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncQuarter, TruncYear
from django.core.cache import cache
from django.db.models import Count, Q
from users.models import User
from common.models import APILog
from collections import defaultdict

def get_date_trunc_func(period):
    """
    根据周期返回对应的时间截断函数
    
    Args:
        period: 时间周期 (daily/weekly/monthly/quarterly/yearly)
        
    Returns:
        对应的Django时间截断函数
    """
    trunc_funcs = {
        'daily': TruncDay,
        'weekly': TruncWeek,
        'monthly': TruncMonth,
        'quarterly': TruncQuarter,
        'yearly': TruncYear
    }
    return trunc_funcs.get(period, TruncMonth)

def generate_date_range(start_date, end_date, period='monthly'):
    """
    生成指定时间段的日期范围
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        period: 时间周期
        
    Returns:
        日期范围列表
    """
    if period == 'daily':
        delta = timedelta(days=1)
        date_format = '%Y-%m-%d'
    elif period == 'weekly':
        delta = timedelta(weeks=1)
        date_format = '%Y-%m-%d'
    elif period == 'monthly':
        # 按月生成日期
        result = []
        current = start_date.replace(day=1)
        while current <= end_date:
            result.append(current.strftime('%Y-%m'))
            # 移动到下一个月
            if current.month == 12:
                current = current.replace(year=current.year+1, month=1)
            else:
                current = current.replace(month=current.month+1)
        return result
    elif period == 'quarterly':
        # 按季度生成日期
        result = []
        current = start_date.replace(day=1, month=((start_date.month-1)//3)*3 + 1)
        while current <= end_date:
            quarter = (current.month-1)//3 + 1
            result.append(f"{current.year}-Q{quarter}")
            # 移动到下一个季度
            if current.month > 9:
                current = current.replace(year=current.year+1, month=1)
            else:
                current = current.replace(month=current.month+3)
        return result
    elif period == 'yearly':
        # 按年生成日期
        result = []
        for year in range(start_date.year, end_date.year + 1):
            result.append(str(year))
        return result
    
    # 对于日期和周期，使用时间增量
    result = []
    current = start_date
    while current <= end_date:
        result.append(current.strftime(date_format))
        current += delta
    
    return result

def get_cache_key(prefix, **params):
    """
    根据参数生成缓存键
    
    Args:
        prefix: 缓存键前缀
        **params: 缓存参数
        
    Returns:
        缓存键字符串
    """
    param_str = '_'.join(f"{k}={v}" for k, v in sorted(params.items()))
    return f"{prefix}_{param_str}"

def format_chart_response(chart_type, title, description, labels, datasets, summary=None):
    """
    格式化图表响应数据
    
    Args:
        chart_type: 图表类型 (line/bar/pie)
        title: 图表标题
        description: 图表描述
        labels: X轴标签
        datasets: 数据集
        summary: 汇总信息
        
    Returns:
        格式化的响应字典
    """
    return {
        "chart_type": chart_type,
        "title": title,
        "description": description,
        "labels": labels,
        "datasets": datasets,
        "summary": summary or {}
    }

def empty_chart_response(title, message="暂无数据", chart_type="line"):
    """
    创建空图表响应
    
    Args:
        title: 图表标题
        message: 显示的消息
        chart_type: 图表类型，默认为line
        
    Returns:
        空的图表响应
    """
    return format_chart_response(
        chart_type=chart_type,
        title=title,
        description=message,
        labels=[],
        datasets=[],
        summary={"message": message}
    )

def get_user_growth_trend(start_date, end_date, period='monthly'):
    """
    获取用户总量与增长趋势数据
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        period: 统计周期，可选值为daily、weekly、monthly、quarterly、yearly
        
    Returns:
        包含图表数据的字典
    """
    # 生成缓存键
    cache_key = get_cache_key(
        'user_growth_trend', 
        period=period,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat()
    )
    
    # 尝试从缓存获取数据
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    # 查询数据
    try:
        # 转换日期为datetime对象并添加时区信息
        start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
        end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
        
        # 使用Python手动按时间段统计，而不是依赖数据库函数
        all_users = (
            User.objects
            .filter(date_joined__range=(start_datetime, end_datetime), is_deleted=False)
            .order_by('date_joined')
        )
        
        # 手动按周期分组
        period_counts = defaultdict(int)
        for user in all_users:
            if period == 'daily':
                period_key = user.date_joined.strftime('%Y-%m-%d')
            elif period == 'weekly':
                # 使用ISO周格式，例如：2025-W16
                period_key = f"{user.date_joined.isocalendar()[0]}-W{user.date_joined.isocalendar()[1]:02d}"
            elif period == 'monthly':
                period_key = user.date_joined.strftime('%Y-%m')
            elif period == 'quarterly':
                quarter = (user.date_joined.month - 1) // 3 + 1
                period_key = f"{user.date_joined.year}-Q{quarter}"
            else:  # yearly
                period_key = str(user.date_joined.year)
            
            period_counts[period_key] += 1
        
        # 按时间排序
        dates = sorted(period_counts.keys())
        new_counts = [period_counts[date] for date in dates]
        
        # 计算累计值
        total_before_start = User.objects.filter(
            date_joined__lt=start_datetime,
            is_deleted=False
        ).count()
        
        cumulative_counts = []
        running_total = total_before_start
        
        for date in dates:
            running_total += period_counts[date]
            cumulative_counts.append(running_total)
        
        # 计算汇总数据
        total_users = User.objects.filter(is_deleted=False).count()
        growth_rate = 0
        if len(cumulative_counts) >= 2 and cumulative_counts[0] > 0:
            growth_rate = ((cumulative_counts[-1] - cumulative_counts[0]) / cumulative_counts[0]) * 100
        
        avg_growth = 0
        if len(new_counts) > 0:
            avg_growth = sum(new_counts) / len(new_counts)
        
        # 构建响应数据
        result = format_chart_response(
            chart_type="line",
            title="用户总量与增长趋势",
            description="系统内所有用户数量的时间序列图",
            labels=dates,
            datasets=[
                {
                    "label": "用户总数",
                    "data": cumulative_counts,
                    "color": "#3366cc"
                },
                {
                    "label": "新增用户数",
                    "data": new_counts,
                    "color": "#dc3912"
                }
            ],
            summary={
                "total_users": total_users,
                "growth_rate": round(growth_rate, 1),
                "average_monthly_growth": round(avg_growth, 1)
            }
        )
        
        # 如果没有数据，返回空图表
        if not dates:
            result = empty_chart_response("用户总量与增长趋势", "该时间段内无用户数据", "line")
        
        # 缓存数据
        cache.set(cache_key, result, 3600)
        
        return result
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"获取用户增长趋势数据出错: {str(e)}")
        return empty_chart_response("用户总量与增长趋势", f"获取数据出错: {str(e)}", "line")

def get_user_role_distribution():
    """
    获取用户角色分布数据
    
    Returns:
        包含图表数据的字典
    """
    # 生成缓存键
    cache_key = 'user_role_distribution'
    
    # 尝试从缓存获取数据
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    # 查询数据
    try:
        # 查询各角色用户数量
        total_users = User.objects.filter(is_deleted=False).count()
        super_admins = User.objects.filter(is_super_admin=True, is_deleted=False).count()
        tenant_admins = User.objects.filter(is_admin=True, is_super_admin=False, is_deleted=False).count()
        regular_users = User.objects.filter(is_admin=False, is_super_admin=False, is_deleted=False).count()
        
        # 计算百分比
        super_admin_percentage = (super_admins / total_users) * 100 if total_users > 0 else 0
        tenant_admin_percentage = (tenant_admins / total_users) * 100 if total_users > 0 else 0
        regular_user_percentage = (regular_users / total_users) * 100 if total_users > 0 else 0
        
        # 构建响应数据
        result = format_chart_response(
            chart_type="pie",
            title="用户角色分布",
            description="超级管理员、租户管理员、普通用户的比例",
            labels=["超级管理员", "租户管理员", "普通用户"],
            datasets=[
                {
                    "data": [super_admins, tenant_admins, regular_users],
                    "colors": ["#9C27B0", "#2196F3", "#4CAF50"]
                }
            ],
            summary={
                "total_users": total_users,
                "super_admin_percentage": round(super_admin_percentage, 1),
                "tenant_admin_percentage": round(tenant_admin_percentage, 1),
                "regular_user_percentage": round(regular_user_percentage, 1)
            }
        )
        
        # 如果没有数据，返回空图表
        if total_users == 0:
            result = empty_chart_response("用户角色分布", "暂无用户数据", "pie")
        
        # 缓存数据
        cache.set(cache_key, result, 1800)  # 30分钟缓存
        
        return result
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"获取用户角色分布数据出错: {str(e)}")
        return empty_chart_response("用户角色分布", f"获取数据出错: {str(e)}", "pie")

def get_active_users(start_date, end_date, period='daily'):
    """
    获取活跃用户统计数据
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        period: 统计周期，可选值为daily、weekly、monthly
        
    Returns:
        包含图表数据的字典
    """
    # 生成缓存键
    cache_key = get_cache_key(
        'active_users', 
        period=period,
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat()
    )
    
    # 尝试从缓存获取数据
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    # 查询数据
    try:
        # 转换日期为datetime对象并添加时区信息
        start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
        end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
        
        # 不使用数据库时区功能，直接获取所有记录并在Python中处理
        api_logs = (
            APILog.objects
            .filter(created_at__range=(start_datetime, end_datetime), user__isnull=False)
            .select_related('user')
            .values('created_at', 'user')
            .order_by('created_at')
        )
        
        # 手动按周期分组
        period_user_sets = defaultdict(set)
        
        for log in api_logs:
            created_at = log['created_at']
            user_id = log['user']
            
            if period == 'daily':
                period_key = created_at.strftime('%Y-%m-%d')
            elif period == 'weekly':
                period_key = f"{created_at.isocalendar()[0]}-W{created_at.isocalendar()[1]:02d}"
            elif period == 'monthly':
                period_key = created_at.strftime('%Y-%m')
            else:
                period_key = created_at.strftime('%Y-%m-%d')
            
            period_user_sets[period_key].add(user_id)
        
        # 按时间排序
        dates = sorted(period_user_sets.keys())
        active_counts = [len(period_user_sets[date]) for date in dates]
        active_rates = []
        
        # 计算每个时间段的活跃率
        for date in dates:
            if period == 'daily':
                period_date = datetime.strptime(date, '%Y-%m-%d').date()
            elif period == 'weekly':
                year, week = date.split('-W')
                period_date = datetime.strptime(f"{year}-{week}-1", '%Y-%W-%w').date()
            elif period == 'monthly':
                period_date = datetime.strptime(date + '-01', '%Y-%m-%d').date()
            else:
                period_date = datetime.strptime(date, '%Y-%m-%d').date()
            
            # 获取该时间段之前注册的总用户数
            period_datetime = timezone.make_aware(datetime.combine(period_date, datetime.max.time()))
            total_users = User.objects.filter(
                date_joined__lte=period_datetime,
                is_deleted=False
            ).count()
            
            active_rate = (len(period_user_sets[date]) / total_users) * 100 if total_users > 0 else 0
            active_rates.append(round(active_rate, 1))
        
        # 计算汇总数据
        avg_active_users = round(sum(active_counts) / len(active_counts), 1) if active_counts else 0
        avg_active_rate = round(sum(active_rates) / len(active_rates), 1) if active_rates else 0
        
        highest_active_count = max(active_counts) if active_counts else 0
        highest_active_index = active_counts.index(highest_active_count) if highest_active_count > 0 else -1
        highest_active_day = dates[highest_active_index] if highest_active_index >= 0 else "无数据"
        
        # 构建响应数据
        result = format_chart_response(
            chart_type="line",
            title="活跃用户统计",
            description=f"按{period}统计的活跃用户数量",
            labels=dates,
            datasets=[
                {
                    "label": "活跃用户数",
                    "data": active_counts,
                    "color": "#FF9800"
                },
                {
                    "label": "活跃率",
                    "data": active_rates,
                    "color": "#E91E63",
                    "yAxisID": "percentage"
                }
            ],
            summary={
                "average_active_users": avg_active_users,
                "highest_active_day": highest_active_day,
                "highest_active_count": highest_active_count,
                "average_active_rate": avg_active_rate
            }
        )
        
        # 如果没有数据，返回空图表
        if not dates:
            result = empty_chart_response("活跃用户统计", "该时间段内无活跃用户数据", "line")
        
        # 缓存数据
        cache.set(cache_key, result, 3600)
        
        return result
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"获取活跃用户统计数据出错: {str(e)}")
        return empty_chart_response("活跃用户统计", f"获取数据出错: {str(e)}", "line")

def get_login_heatmap(start_date, end_date):
    """
    获取用户登录情况热力图数据
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        
    Returns:
        包含热力图数据的字典
    """
    # 生成缓存键
    cache_key = get_cache_key(
        'login_heatmap',
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat()
    )
    
    # 尝试从缓存获取数据
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    # 查询数据
    try:
        # 转换日期为datetime对象并添加时区信息
        start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
        end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
        
        # 筛选登录相关的API调用记录
        login_logs = APILog.objects.filter(
            created_at__range=(start_datetime, end_datetime),
            request_path__contains='/auth/login/',  # 登录API路径
            status_code=200  # 成功的登录请求
        )
        
        # 按星期几和小时分组统计
        heatmap_data = []
        weekday_hour_counts = defaultdict(int)
        
        for log in login_logs:
            weekday = log.created_at.weekday()  # 0-6表示周一到周日
            hour = log.created_at.hour  # 0-23表示小时
            weekday_hour_counts[(weekday, hour)] += 1
        
        # 转换为热力图所需的格式
        for (weekday, hour), count in weekday_hour_counts.items():
            heatmap_data.append([weekday, hour, count])
        
        # 计算汇总数据
        total_logins = sum(count for _, _, count in heatmap_data)
        
        peak_count = 0
        peak_weekday = 0
        peak_hour = 0
        
        lowest_count = float('inf')
        lowest_weekday = 0
        lowest_hour = 0
        
        if heatmap_data:
            for weekday, hour, count in heatmap_data:
                if count > peak_count:
                    peak_count = count
                    peak_weekday = weekday
                    peak_hour = hour
                
                if count < lowest_count:
                    lowest_count = count
                    lowest_weekday = weekday
                    lowest_hour = hour
        
        # 如果没有找到最低值（没有数据），设置为0
        if lowest_count == float('inf'):
            lowest_count = 0
        
        # 星期几的显示名称
        weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        
        # 构建响应数据
        result = {
            "chart_type": "heatmap",
            "title": "用户登录热力图",
            "description": "不同时间段的登录活跃度",
            "x_labels": weekday_names,
            "y_labels": [f"{h}时" for h in range(24)],
            "dataset": heatmap_data,
            "summary": {
                "total_logins": total_logins,
                "peak_hour": f"{weekday_names[peak_weekday]} {peak_hour}时" if total_logins > 0 else "无数据",
                "peak_hour_count": peak_count,
                "lowest_hour": f"{weekday_names[lowest_weekday]} {lowest_hour}时" if total_logins > 0 else "无数据",
                "lowest_hour_count": lowest_count
            }
        }
        
        # 如果没有数据，返回空热力图
        if not heatmap_data:
            result = {
                "chart_type": "heatmap",
                "title": "用户登录热力图",
                "description": "暂无登录数据",
                "x_labels": weekday_names,
                "y_labels": [f"{h}时" for h in range(24)],
                "dataset": [],
                "summary": {
                    "message": "该时间段内无登录数据",
                    "total_logins": 0
                }
            }
        
        # 缓存数据
        cache.set(cache_key, result, 3600)
        
        return result
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"获取用户登录热力图数据出错: {str(e)}")
        return {
            "chart_type": "heatmap",
            "title": "用户登录热力图",
            "description": f"获取数据出错: {str(e)}",
            "x_labels": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"],
            "y_labels": [f"{h}时" for h in range(24)],
            "dataset": [],
            "summary": {
                "message": f"获取数据出错: {str(e)}",
                "total_logins": 0
            }
        } 