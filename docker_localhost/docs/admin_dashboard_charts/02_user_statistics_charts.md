# 用户统计分析图表

## 图表清单

1. **用户总量与增长趋势**：系统内所有用户数量的时间序列图
2. **用户角色分布**：超级管理员、租户管理员、普通用户的比例饼图
3. **活跃用户统计**：按日/周/月统计的活跃用户数量折线图
4. **用户登录情况**：登录频次热力图，展示不同时间段的登录活跃度

## 数据源分析

这些图表的数据主要来源于以下模型：

1. `users.User`模型：包含用户基本信息、角色标识和创建时间
2. `common.APILog`模型：包含用户登录和API调用记录

关键字段包括：

- `User.date_joined`：用户创建时间
- `User.is_admin`：是否管理员
- `User.is_super_admin`：是否超级管理员
- `User.is_member`：是否普通成员
- `APILog.user`：关联的用户
- `APILog.created_at`：API调用时间
- `APILog.request_path`：请求路径（用于识别登录请求）

## API设计

### 1. 用户总量与增长趋势 API

#### 请求

```
GET /api/v1/admin/charts/user-growth-trend/?period={daily|weekly|monthly|quarterly|yearly}&start_date={YYYY-MM-DD}&end_date={YYYY-MM-DD}
```

#### 参数说明

- `period`：统计周期，可选值为daily（日）、weekly（周）、monthly（月）、quarterly（季度）、yearly（年）
- `start_date`：开始日期，格式为YYYY-MM-DD
- `end_date`：结束日期，格式为YYYY-MM-DD

#### 响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "chart_type": "line",
    "title": "用户总量与增长趋势",
    "description": "系统内所有用户数量的时间序列图",
    "labels": ["2023-01", "2023-02", "2023-03", ...],
    "datasets": [
      {
        "label": "用户总数",
        "data": [100, 150, 220, ...],
        "color": "#3366cc"
      },
      {
        "label": "新增用户数",
        "data": [100, 50, 70, ...],
        "color": "#dc3912"
      }
    ],
    "summary": {
      "total_users": 220,
      "growth_rate": 120,
      "average_monthly_growth": 40
    }
  }
}
```

### 2. 用户角色分布 API

#### 请求

```
GET /api/v1/admin/charts/user-role-distribution/
```

#### 响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "chart_type": "pie",
    "title": "用户角色分布",
    "description": "超级管理员、租户管理员、普通用户的比例",
    "labels": ["超级管理员", "租户管理员", "普通用户"],
    "datasets": [
      {
        "data": [5, 25, 70],
        "colors": ["#9C27B0", "#2196F3", "#4CAF50"]
      }
    ],
    "summary": {
      "total_users": 100,
      "super_admin_percentage": 5,
      "tenant_admin_percentage": 25,
      "regular_user_percentage": 70
    }
  }
}
```

### 3. 活跃用户统计 API

#### 请求

```
GET /api/v1/admin/charts/active-users/?period={daily|weekly|monthly}&start_date={YYYY-MM-DD}&end_date={YYYY-MM-DD}
```

#### 参数说明

- `period`：统计周期，可选值为daily（日）、weekly（周）、monthly（月）
- `start_date`：开始日期，格式为YYYY-MM-DD
- `end_date`：结束日期，格式为YYYY-MM-DD

#### 响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "chart_type": "line",
    "title": "活跃用户统计",
    "description": "按日/周/月统计的活跃用户数量",
    "labels": ["2023-01-01", "2023-01-02", "2023-01-03", ...],
    "datasets": [
      {
        "label": "活跃用户数",
        "data": [45, 52, 49, ...],
        "color": "#FF9800"
      },
      {
        "label": "活跃率",
        "data": [45, 52, 49, ...],
        "color": "#E91E63",
        "yAxisID": "percentage"
      }
    ],
    "summary": {
      "average_active_users": 48,
      "highest_active_day": "2023-01-02",
      "highest_active_count": 52,
      "average_active_rate": 48
    }
  }
}
```

### 4. 用户登录情况 API

#### 请求

```
GET /api/v1/admin/charts/login-heatmap/?start_date={YYYY-MM-DD}&end_date={YYYY-MM-DD}
```

#### 参数说明

- `start_date`：开始日期，格式为YYYY-MM-DD
- `end_date`：结束日期，格式为YYYY-MM-DD

#### 响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "chart_type": "heatmap",
    "title": "用户登录热力图",
    "description": "不同时间段的登录活跃度",
    "x_labels": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"],
    "y_labels": ["0时", "1时", "2时", "...", "23时"],
    "dataset": [
      [0, 0, 5],  // [x, y, value] 表示周一0时有5次登录
      [0, 1, 3],
      [0, 2, 1],
      // ...更多数据点
    ],
    "summary": {
      "total_logins": 1250,
      "peak_hour": "周一 10时",
      "peak_hour_count": 45,
      "lowest_hour": "周日 3时",
      "lowest_hour_count": 0
    }
  }
}
```

## 实现步骤

### 1. 创建图表数据视图

1. 在`common`应用中的`charts`子目录下创建`user_charts.py`文件
2. 实现用户统计相关的图表数据API视图
3. 在`urls.py`文件中配置API路由

### 2. 数据查询与处理

#### 用户总量与增长趋势

1. 按照指定的时间周期（日/周/月/季/年）对用户创建时间进行分组
2. 计算每个时间段的新增用户数
3. 计算截至每个时间点的累计用户总数

```python
# 伪代码示例
from django.db.models import Count
from django.db.models.functions import TruncMonth
from users.models import User

def get_user_growth_trend(start_date, end_date, period='monthly'):
    # 根据period选择合适的时间截断函数
    trunc_func = {
        'daily': TruncDay,
        'weekly': TruncWeek,
        'monthly': TruncMonth,
        'quarterly': TruncQuarter,
        'yearly': TruncYear
    }.get(period, TruncMonth)
    
    # 查询每个时间段的新增用户数
    new_users_by_period = User.objects.filter(
        date_joined__range=[start_date, end_date],
        is_deleted=False
    ).annotate(
        period=trunc_func('date_joined')
    ).values('period').annotate(
        count=Count('id')
    ).order_by('period')
    
    # 计算累计用户数
    total_users = []
    running_total = User.objects.filter(date_joined__lt=start_date, is_deleted=False).count()
    
    for period_data in new_users_by_period:
        running_total += period_data['count']
        total_users.append({
            'period': period_data['period'],
            'total': running_total,
            'new': period_data['count']
        })
    
    return total_users
```

#### 用户角色分布

1. 使用Django ORM的聚合函数按角色分组计算用户数量
2. 计算各角色用户占比

```python
# 伪代码示例
from django.db.models import Count, Q
from users.models import User

def get_user_role_distribution():
    # 查询各角色用户数量
    total_users = User.objects.filter(is_deleted=False).count()
    super_admins = User.objects.filter(is_super_admin=True, is_deleted=False).count()
    tenant_admins = User.objects.filter(is_admin=True, is_super_admin=False, is_deleted=False).count()
    regular_users = User.objects.filter(is_admin=False, is_super_admin=False, is_deleted=False).count()
    
    # 计算百分比
    result = {
        'total': total_users,
        'roles': [
            {
                'name': '超级管理员',
                'count': super_admins,
                'percentage': (super_admins / total_users) * 100 if total_users > 0 else 0
            },
            {
                'name': '租户管理员',
                'count': tenant_admins,
                'percentage': (tenant_admins / total_users) * 100 if total_users > 0 else 0
            },
            {
                'name': '普通用户',
                'count': regular_users,
                'percentage': (regular_users / total_users) * 100 if total_users > 0 else 0
            }
        ]
    }
    
    return result
```

#### 活跃用户统计

1. 使用APILog模型数据，按照指定的时间周期（日/周/月）分组
2. 计算每个时间段内有API调用记录的唯一用户数量
3. 计算活跃率（活跃用户数/总用户数）

```python
# 伪代码示例
from django.db.models import Count
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
from common.models import APILog
from users.models import User

def get_active_users(start_date, end_date, period='daily'):
    # 根据period选择合适的时间截断函数
    trunc_func = {
        'daily': TruncDay,
        'weekly': TruncWeek,
        'monthly': TruncMonth
    }.get(period, TruncDay)
    
    # 查询每个时间段的活跃用户数
    active_users = APILog.objects.filter(
        created_at__range=[start_date, end_date],
        user__isnull=False  # 确保有关联用户
    ).annotate(
        period=trunc_func('created_at')
    ).values('period').annotate(
        active_count=Count('user', distinct=True)
    ).order_by('period')
    
    # 计算每个时间段的活跃率
    result = []
    for period_data in active_users:
        # 获取该时间段之前注册的总用户数
        total_users = User.objects.filter(
            date_joined__lte=period_data['period'],
            is_deleted=False
        ).count()
        
        active_rate = (period_data['active_count'] / total_users) * 100 if total_users > 0 else 0
        
        result.append({
            'period': period_data['period'],
            'active_users': period_data['active_count'],
            'total_users': total_users,
            'active_rate': active_rate
        })
    
    return result
```

#### 用户登录情况热力图

1. 从APILog中筛选登录相关的记录
2. 按照星期几和小时分组，计算每个时间段的登录次数

```python
# 伪代码示例
from django.db.models import Count
from django.db.models.functions import ExtractHour, ExtractWeekDay
from common.models import APILog

def get_login_heatmap(start_date, end_date):
    # 筛选登录相关的API调用记录
    login_logs = APILog.objects.filter(
        created_at__range=[start_date, end_date],
        request_path='/api/v1/auth/login/',  # 登录API路径
        status_code=200  # 成功的登录请求
    )
    
    # 按星期几和小时分组统计
    heatmap_data = login_logs.annotate(
        weekday=ExtractWeekDay('created_at'),  # 1-7表示周一到周日
        hour=ExtractHour('created_at')  # 0-23表示小时
    ).values('weekday', 'hour').annotate(
        count=Count('id')
    ).order_by('weekday', 'hour')
    
    # 转换为热力图所需的格式
    result = []
    for item in heatmap_data:
        result.append([
            item['weekday'] - 1,  # 转换为0-6表示周一到周日
            item['hour'],
            item['count']
        ])
    
    return result
```

### 3. API权限控制

确保只有超级管理员可以访问这些图表数据API：

```python
# 伪代码示例
from rest_framework.permissions import IsAuthenticated
from common.permissions import IsSuperAdmin

class UserStatisticsView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    # ...
```

### 4. 数据缓存策略

对于计算密集型的图表数据，实施缓存策略：

```python
# 伪代码示例
from django.core.cache import cache

def get_user_growth_trend(start_date, end_date, period='monthly'):
    # 生成缓存键
    cache_key = f"user_growth_{period}_{start_date}_{end_date}"
    
    # 尝试从缓存获取数据
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    # 计算数据
    # ...
    
    # 缓存数据（设置1小时过期）
    cache.set(cache_key, result, 3600)
    
    return result
```

### 5. 前端实现

1. 在超级管理员仪表盘页面中添加用户统计分析相关图表
2. 使用Chart.js或ECharts库渲染折线图、饼图和热力图
3. 实现时间范围选择器和周期选择器

## 注意事项

1. 对于活跃用户统计，需要明确定义"活跃"的标准，如"在指定时间段内至少有一次API调用"
2. 登录热力图可能需要根据服务器时区和用户所在时区进行调整
3. 考虑添加用户增长预测功能，基于历史数据预测未来用户增长趋势
4. 对于大型系统，可能需要使用异步任务处理计算密集型的统计任务
5. 考虑添加用户留存率分析，帮助评估系统的用户粘性 