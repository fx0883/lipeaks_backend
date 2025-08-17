# 租户概览统计图表

## 图表清单

1. **租户数量趋势图**：显示系统内租户总数随时间的变化趋势，可按月/季度统计
2. **租户状态分布饼图**：显示活跃/暂停/已删除租户的比例
3. **租户创建速率**：每月/每周新增租户数量柱状图

## 数据源分析

这些图表的数据主要来源于`tenants.Tenant`模型，该模型包含以下关键字段：

- `created_at`：租户创建时间
- `status`：租户状态（'active', 'suspended', 'deleted'）
- `is_deleted`：是否删除标志

## API设计

### 1. 租户数量趋势图 API

#### 请求

```
GET /api/v1/admin/charts/tenant-trend/?period={daily|weekly|monthly|quarterly|yearly}&start_date={YYYY-MM-DD}&end_date={YYYY-MM-DD}
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
    "title": "租户数量趋势",
    "description": "系统内租户总数随时间的变化趋势",
    "labels": ["2023-01", "2023-02", "2023-03", ...],
    "datasets": [
      {
        "label": "租户总数",
        "data": [10, 15, 22, ...],
        "color": "#3366cc"
      }
    ],
    "summary": {
      "total": 120,
      "growth_rate": 15.5,
      "average_monthly_growth": 8.2
    }
  }
}
```

### 2. 租户状态分布饼图 API

#### 请求

```
GET /api/v1/admin/charts/tenant-status-distribution/
```

#### 响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "chart_type": "pie",
    "title": "租户状态分布",
    "description": "活跃/暂停/已删除租户的比例",
    "labels": ["活跃", "暂停", "已删除"],
    "datasets": [
      {
        "data": [75, 15, 10],
        "colors": ["#4CAF50", "#FFC107", "#F44336"]
      }
    ],
    "summary": {
      "total": 100,
      "active_percentage": 75,
      "suspended_percentage": 15,
      "deleted_percentage": 10
    }
  }
}
```

### 3. 租户创建速率 API

#### 请求

```
GET /api/v1/admin/charts/tenant-creation-rate/?period={weekly|monthly}&start_date={YYYY-MM-DD}&end_date={YYYY-MM-DD}
```

#### 参数说明

- `period`：统计周期，可选值为weekly（周）、monthly（月）
- `start_date`：开始日期，格式为YYYY-MM-DD
- `end_date`：结束日期，格式为YYYY-MM-DD

#### 响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "chart_type": "bar",
    "title": "租户创建速率",
    "description": "每月新增租户数量",
    "labels": ["2023-01", "2023-02", "2023-03", ...],
    "datasets": [
      {
        "label": "新增租户数",
        "data": [5, 8, 12, ...],
        "color": "#2196F3"
      }
    ],
    "summary": {
      "total_new_tenants": 120,
      "average_monthly_new": 10,
      "highest_month": "2023-03",
      "highest_month_count": 12
    }
  }
}
```

## 实现步骤

### 1. 创建图表数据视图

1. 在`common`应用中创建新的`charts`子目录
2. 创建`views.py`文件，实现图表数据API视图
3. 创建`urls.py`文件，配置API路由

### 2. 数据查询与处理

#### 租户数量趋势图

1. 按照指定的时间周期（日/周/月/季/年）对数据进行分组
2. 使用Django ORM的聚合函数计算每个时间段的租户总数
3. 对于累计趋势，需要计算截至每个时间点的累计租户数

```python
# 伪代码示例
from django.db.models import Count
from django.db.models.functions import TruncMonth

def get_tenant_trend_data(start_date, end_date, period='monthly'):
    # 根据period选择合适的时间截断函数
    trunc_func = {
        'daily': TruncDay,
        'weekly': TruncWeek,
        'monthly': TruncMonth,
        'quarterly': TruncQuarter,
        'yearly': TruncYear
    }.get(period, TruncMonth)
    
    # 查询每个时间段的新增租户数
    new_tenants_by_period = Tenant.objects.filter(
        created_at__range=[start_date, end_date]
    ).annotate(
        period=trunc_func('created_at')
    ).values('period').annotate(
        count=Count('id')
    ).order_by('period')
    
    # 计算累计租户数
    # ...
    
    return result
```

#### 租户状态分布饼图

1. 使用Django ORM的聚合函数按状态分组计算租户数量
2. 计算各状态租户占比

```python
# 伪代码示例
from django.db.models import Count

def get_tenant_status_distribution():
    # 查询各状态租户数量
    status_counts = Tenant.objects.values('status').annotate(
        count=Count('id')
    )
    
    # 计算百分比
    total = sum(item['count'] for item in status_counts)
    for item in status_counts:
        item['percentage'] = (item['count'] / total) * 100 if total > 0 else 0
    
    return status_counts
```

#### 租户创建速率

1. 按照指定的时间周期（周/月）对数据进行分组
2. 计算每个时间段的新增租户数量

```python
# 伪代码示例
from django.db.models import Count
from django.db.models.functions import TruncMonth, TruncWeek

def get_tenant_creation_rate(start_date, end_date, period='monthly'):
    # 根据period选择合适的时间截断函数
    trunc_func = TruncMonth if period == 'monthly' else TruncWeek
    
    # 查询每个时间段的新增租户数
    new_tenants_by_period = Tenant.objects.filter(
        created_at__range=[start_date, end_date]
    ).annotate(
        period=trunc_func('created_at')
    ).values('period').annotate(
        count=Count('id')
    ).order_by('period')
    
    return new_tenants_by_period
```

### 3. API权限控制

确保只有超级管理员可以访问这些图表数据API：

```python
# 伪代码示例
from rest_framework.permissions import IsAuthenticated
from common.permissions import IsSuperAdmin

class TenantChartView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    # ...
```

### 4. 数据缓存策略

对于计算密集型的图表数据，实施缓存策略：

1. 使用Redis作为缓存后端
2. 为每个图表数据设置适当的缓存过期时间
3. 根据查询参数生成缓存键

```python
# 伪代码示例
from django.core.cache import cache

def get_tenant_trend_data(start_date, end_date, period='monthly'):
    # 生成缓存键
    cache_key = f"tenant_trend_{period}_{start_date}_{end_date}"
    
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

1. 在前端管理界面中创建超级管理员仪表盘页面
2. 使用Chart.js或ECharts库渲染图表
3. 使用Axios调用后端API获取图表数据
4. 实现时间范围选择器，允许超级管理员自定义查看时间范围

## 注意事项

1. 对于大型系统，可能需要优化查询性能，考虑使用数据库索引或物化视图
2. 定期清理缓存数据，避免缓存过期导致的数据不一致
3. 考虑添加数据导出功能，允许超级管理员导出图表数据为CSV或Excel格式
4. 实现图表数据的定期快照，用于历史比较分析 