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

def format_period_key(dt, period):
    """
    统一将截断聚合的 datetime 或 date 对象格式化为周期字符串
    """
    if dt is None:
        return ""
    if period == 'daily':
        return dt.strftime('%Y-%m-%d')
    elif period == 'weekly':
        iso_year, iso_week, _ = dt.isocalendar()
        return f"{iso_year}-W{iso_week:02d}"
    elif period == 'monthly':
        return dt.strftime('%Y-%m')
    elif period == 'quarterly':
        quarter = (dt.month - 1) // 3 + 1
        return f"{dt.year}-Q{quarter}"
    elif period == 'yearly':
        return str(dt.year)
    return dt.strftime('%Y-%m-%d')

def generate_period_labels(start_date, end_date, period='monthly'):
    """
    生成指定时间段内所有连续周期的有序标签列表（用于补齐缺失数据）
    """
    if start_date > end_date:
        return []
    
    labels = []
    if period == 'daily':
        curr = start_date
        while curr <= end_date:
            labels.append(curr.strftime('%Y-%m-%d'))
            curr += timedelta(days=1)
    elif period == 'weekly':
        curr = start_date
        while curr <= end_date:
            iso_year, iso_week, _ = curr.isocalendar()
            key = f"{iso_year}-W{iso_week:02d}"
            if key not in labels:
                labels.append(key)
            curr += timedelta(days=1)
    elif period == 'monthly':
        curr = start_date.replace(day=1)
        while curr <= end_date:
            labels.append(curr.strftime('%Y-%m'))
            if curr.month == 12:
                curr = curr.replace(year=curr.year + 1, month=1)
            else:
                curr = curr.replace(month=curr.month + 1)
    elif period == 'quarterly':
        curr = start_date.replace(day=1, month=((start_date.month - 1) // 3) * 3 + 1)
        while curr <= end_date:
            q = (curr.month - 1) // 3 + 1
            labels.append(f"{curr.year}-Q{q}")
            if curr.month > 9:
                curr = curr.replace(year=curr.year + 1, month=1)
            else:
                curr = curr.replace(month=curr.month + 3)
    elif period == 'yearly':
        for y in range(start_date.year, end_date.year + 1):
            labels.append(str(y))
    else:
        curr = start_date
        while curr <= end_date:
            labels.append(curr.strftime('%Y-%m-%d'))
            curr += timedelta(days=1)
    return labels


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
        trunc_func = get_date_trunc_func(period)
        
        # 1. 查询时间区间内的新增用户，按周期下推数据库分组统计
        user_increments_qs = (
            User.objects
            .filter(date_joined__range=(start_datetime, end_datetime), is_deleted=False)
            .annotate(period_dt=trunc_func('date_joined'))
            .values('period_dt')
            .annotate(cnt=Count('id'))
            .order_by('period_dt')
        )
        increments_map = {
            format_period_key(r['period_dt'], period): r['cnt']
            for r in user_increments_qs if r['period_dt']
        }
        
        # 2. 查询起始时间之前的存量用户总数（仅 1 次 COUNT 查询）
        total_before_start = User.objects.filter(
            date_joined__lt=start_datetime,
            is_deleted=False
        ).count()
        
        # 3. 生成完整连续周期列表并补全 0 值
        dates = generate_period_labels(start_date, end_date, period)
        if not dates:
            dates = sorted(increments_map.keys())
        
        new_counts = []
        cumulative_counts = []
        running_total = total_before_start
        
        for date in dates:
            cnt = increments_map.get(date, 0)
            new_counts.append(cnt)
            running_total += cnt
            cumulative_counts.append(running_total)
        
        # 4. 计算汇总数据
        total_users = User.objects.filter(is_deleted=False).count()
        growth_rate = 0
        if len(cumulative_counts) >= 2 and cumulative_counts[0] > 0:
            growth_rate = ((cumulative_counts[-1] - cumulative_counts[0]) / cumulative_counts[0]) * 100
        
        avg_growth = 0
        if len(new_counts) > 0:
            avg_growth = sum(new_counts) / len(new_counts)
        
        # 5. 构建响应数据
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
        trunc_func = get_date_trunc_func(period)
        
        # 1. 活跃用户数聚合：下推数据库 Count('user', distinct=True)
        active_users_qs = (
            APILog.objects
            .filter(created_at__range=(start_datetime, end_datetime), user__isnull=False)
            .annotate(period_dt=trunc_func('created_at'))
            .values('period_dt')
            .annotate(active_count=Count('user', distinct=True))
            .order_by('period_dt')
        )
        active_counts_map = {
            format_period_key(r['period_dt'], period): r['active_count']
            for r in active_users_qs if r['period_dt']
        }
        
        # 2. 存量用户基准数（仅 1 次 COUNT 查询）
        base_total_users = User.objects.filter(
            date_joined__lt=start_datetime,
            is_deleted=False
        ).count()
        
        # 3. 区间内新增用户分组统计（仅 1 次聚合查询）
        user_increments_qs = (
            User.objects
            .filter(date_joined__range=(start_datetime, end_datetime), is_deleted=False)
            .annotate(period_dt=trunc_func('date_joined'))
            .values('period_dt')
            .annotate(cnt=Count('id'))
            .order_by('period_dt')
        )
        increments_map = {
            format_period_key(r['period_dt'], period): r['cnt']
            for r in user_increments_qs if r['period_dt']
        }
        
        # 4. 生成完整连续周期列表并补全 0 值
        dates = generate_period_labels(start_date, end_date, period)
        if not dates:
            dates = sorted(set(list(active_counts_map.keys()) + list(increments_map.keys())))
        
        active_counts = []
        active_rates = []
        running_total_users = base_total_users
        
        # 5. 内存 O(1) 累加计算累计用户与活跃率，彻底消除 365 次数据库 COUNT
        for date_key in dates:
            active_count = active_counts_map.get(date_key, 0)
            active_counts.append(active_count)
            
            running_total_users += increments_map.get(date_key, 0)
            rate = (active_count / running_total_users * 100) if running_total_users > 0 else 0
            active_rates.append(round(rate, 1))
        
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