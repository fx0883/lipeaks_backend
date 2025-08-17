# API调用分析图表

## 图表清单

1. **API调用量趋势图**：系统API总调用量随时间变化的折线图
2. **API错误率监控**：不同API端点的错误率对比
3. **最常用API排行**：调用次数最多的API端点柱状图
4. **API响应时间分析**：各主要API的平均响应时间对比

## 数据源分析

这些图表的数据主要来源于`common.APILog`模型，该模型记录了系统中所有的API调用信息，包含以下关键字段：

- `request_path`：API请求路径
- `request_method`：请求方法（GET、POST等）
- `status_code`：HTTP状态码
- `response_time`：响应时间（毫秒）
- `status_type`：状态类型（success、error）
- `created_at`：API调用时间
- `user`：关联的用户
- `tenant`：关联的租户

## API设计

### 1. API调用量趋势图 API

#### 请求

```
GET /api/v1/admin/charts/api-call-trend/?period={hourly|daily|weekly|monthly}&start_date={YYYY-MM-DD}&end_date={YYYY-MM-DD}
```

#### 参数说明

- `period`：统计周期，可选值为hourly（小时）、daily（日）、weekly（周）、monthly（月）
- `start_date`：开始日期，格式为YYYY-MM-DD
- `end_date`：结束日期，格式为YYYY-MM-DD

#### 响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "chart_type": "line",
    "title": "API调用量趋势",
    "description": "系统API总调用量随时间变化的趋势",
    "labels": ["2023-01-01", "2023-01-02", "2023-01-03", ...],
    "datasets": [
      {
        "label": "总调用量",
        "data": [1250, 1340, 1120, ...],
        "color": "#3366cc"
      },
      {
        "label": "成功调用",
        "data": [1200, 1290, 1080, ...],
        "color": "#4CAF50"
      },
      {
        "label": "失败调用",
        "data": [50, 50, 40, ...],
        "color": "#F44336"
      }
    ],
    "summary": {
      "total_calls": 45000,
      "success_calls": 43200,
      "error_calls": 1800,
      "average_daily_calls": 1500,
      "error_rate": 4.0
    }
  }
}
```

### 2. API错误率监控 API

#### 请求

```
GET /api/v1/admin/charts/api-error-rate/?start_date={YYYY-MM-DD}&end_date={YYYY-MM-DD}&top={number}
```

#### 参数说明

- `start_date`：开始日期，格式为YYYY-MM-DD
- `end_date`：结束日期，格式为YYYY-MM-DD
- `top`：返回错误率最高的前N个API端点，默认为10

#### 响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "chart_type": "bar",
    "title": "API错误率监控",
    "description": "不同API端点的错误率对比",
    "labels": ["/api/v1/users/import/", "/api/v1/tenants/validate/", ...],
    "datasets": [
      {
        "label": "错误率(%)",
        "data": [12.5, 8.3, 6.7, ...],
        "color": "#FF5722"
      }
    ],
    "summary": {
      "average_error_rate": 4.2,
      "highest_error_rate": 12.5,
      "highest_error_endpoint": "/api/v1/users/import/"
    }
  }
}
```

### 3. 最常用API排行 API

#### 请求

```
GET /api/v1/admin/charts/most-used-apis/?start_date={YYYY-MM-DD}&end_date={YYYY-MM-DD}&top={number}
```

#### 参数说明

- `start_date`：开始日期，格式为YYYY-MM-DD
- `end_date`：结束日期，格式为YYYY-MM-DD
- `top`：返回调用量最高的前N个API端点，默认为10

#### 响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "chart_type": "bar",
    "title": "最常用API排行",
    "description": "调用次数最多的API端点",
    "labels": ["/api/v1/auth/login/", "/api/v1/users/profile/", ...],
    "datasets": [
      {
        "label": "调用次数",
        "data": [5600, 4200, 3800, ...],
        "color": "#2196F3"
      }
    ],
    "summary": {
      "total_calls": 45000,
      "top_api_calls_percentage": 65.3
    }
  }
}
```

### 4. API响应时间分析 API

#### 请求

```
GET /api/v1/admin/charts/api-response-time/?start_date={YYYY-MM-DD}&end_date={YYYY-MM-DD}&top={number}
```

#### 参数说明

- `start_date`：开始日期，格式为YYYY-MM-DD
- `end_date`：结束日期，格式为YYYY-MM-DD
- `top`：返回响应时间最长的前N个API端点，默认为10

#### 响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "chart_type": "bar",
    "title": "API响应时间分析",
    "description": "各主要API的平均响应时间对比",
    "labels": ["/api/v1/tenants/report/", "/api/v1/cms/articles/search/", ...],
    "datasets": [
      {
        "label": "平均响应时间(ms)",
        "data": [320, 280, 240, ...],
        "color": "#9C27B0"
      }
    ],
    "summary": {
      "overall_average_response_time": 120,
      "slowest_api": "/api/v1/tenants/report/",
      "slowest_api_response_time": 320
    }
  }
}
```

## 实现步骤

### 1. 创建图表数据视图

1. 在`common`应用中的`charts`子目录下创建`api_charts.py`文件
2. 实现API调用分析相关的图表数据API视图
3. 在`urls.py`文件中配置API路由

### 2. 数据查询与处理

#### API调用量趋势图

1. 按照指定的时间周期（小时/日/周/月）对API调用时间进行分组
2. 计算每个时间段的总调用量、成功调用量和失败调用量

```python
# 伪代码示例
from django.db.models import Count, Q
from django.db.models.functions import TruncHour, TruncDay, TruncWeek, TruncMonth
from common.models import APILog

def get_api_call_trend(start_date, end_date, period='daily'):
    # 根据period选择合适的时间截断函数
    trunc_func = {
        'hourly': TruncHour,
        'daily': TruncDay,
        'weekly': TruncWeek,
        'monthly': TruncMonth
    }.get(period, TruncDay)
    
    # 查询每个时间段的API调用量
    api_calls = APILog.objects.filter(
        created_at__range=[start_date, end_date]
    ).annotate(
        period=trunc_func('created_at')
    ).values('period').annotate(
        total=Count('id'),
        success=Count('id', filter=Q(status_type='success')),
        error=Count('id', filter=Q(status_type='error'))
    ).order_by('period')
    
    # 计算总计和平均值
    total_calls = sum(item['total'] for item in api_calls)
    success_calls = sum(item['success'] for item in api_calls)
    error_calls = sum(item['error'] for item in api_calls)
    period_count = len(api_calls)
    average_calls = total_calls / period_count if period_count > 0 else 0
    error_rate = (error_calls / total_calls) * 100 if total_calls > 0 else 0
    
    result = {
        'data': list(api_calls),
        'summary': {
            'total_calls': total_calls,
            'success_calls': success_calls,
            'error_calls': error_calls,
            'average_daily_calls': average_calls,
            'error_rate': error_rate
        }
    }
    
    return result
```

#### API错误率监控

1. 按API端点分组，计算每个端点的总调用量和错误调用量
2. 计算每个端点的错误率，并按错误率降序排序

```python
# 伪代码示例
from django.db.models import Count, F, ExpressionWrapper, FloatField, Q
from common.models import APILog

def get_api_error_rate(start_date, end_date, top=10):
    # 查询每个API端点的调用量和错误量
    api_stats = APILog.objects.filter(
        created_at__range=[start_date, end_date]
    ).values('request_path').annotate(
        total_calls=Count('id'),
        error_calls=Count('id', filter=Q(status_type='error'))
    )
    
    # 计算错误率并排序
    for item in api_stats:
        item['error_rate'] = (item['error_calls'] / item['total_calls']) * 100 if item['total_calls'] > 0 else 0
    
    # 按错误率降序排序并限制返回数量
    sorted_apis = sorted(api_stats, key=lambda x: x['error_rate'], reverse=True)[:top]
    
    # 计算平均错误率
    total_calls = sum(item['total_calls'] for item in api_stats)
    total_errors = sum(item['error_calls'] for item in api_stats)
    average_error_rate = (total_errors / total_calls) * 100 if total_calls > 0 else 0
    
    result = {
        'data': sorted_apis,
        'summary': {
            'average_error_rate': average_error_rate,
            'highest_error_rate': sorted_apis[0]['error_rate'] if sorted_apis else 0,
            'highest_error_endpoint': sorted_apis[0]['request_path'] if sorted_apis else None
        }
    }
    
    return result
```

#### 最常用API排行

1. 按API端点分组，计算每个端点的调用次数
2. 按调用次数降序排序，获取调用量最高的API端点

```python
# 伪代码示例
from django.db.models import Count
from common.models import APILog

def get_most_used_apis(start_date, end_date, top=10):
    # 查询每个API端点的调用量
    api_usage = APILog.objects.filter(
        created_at__range=[start_date, end_date]
    ).values('request_path').annotate(
        call_count=Count('id')
    ).order_by('-call_count')[:top]
    
    # 计算总调用量
    total_calls = APILog.objects.filter(
        created_at__range=[start_date, end_date]
    ).count()
    
    # 计算前N个API的调用量占总调用量的百分比
    top_apis_calls = sum(item['call_count'] for item in api_usage)
    top_apis_percentage = (top_apis_calls / total_calls) * 100 if total_calls > 0 else 0
    
    result = {
        'data': list(api_usage),
        'summary': {
            'total_calls': total_calls,
            'top_api_calls_percentage': top_apis_percentage
        }
    }
    
    return result
```

#### API响应时间分析

1. 按API端点分组，计算每个端点的平均响应时间
2. 按平均响应时间降序排序，获取响应时间最长的API端点

```python
# 伪代码示例
from django.db.models import Avg, Count
from common.models import APILog

def get_api_response_time(start_date, end_date, top=10):
    # 查询每个API端点的平均响应时间
    api_response_times = APILog.objects.filter(
        created_at__range=[start_date, end_date]
    ).values('request_path').annotate(
        avg_response_time=Avg('response_time'),
        call_count=Count('id')
    ).filter(
        call_count__gte=10  # 只考虑调用量达到一定阈值的API
    ).order_by('-avg_response_time')[:top]
    
    # 计算所有API的平均响应时间
    overall_avg_response_time = APILog.objects.filter(
        created_at__range=[start_date, end_date]
    ).aggregate(avg_time=Avg('response_time'))['avg_time'] or 0
    
    result = {
        'data': list(api_response_times),
        'summary': {
            'overall_average_response_time': overall_avg_response_time,
            'slowest_api': api_response_times[0]['request_path'] if api_response_times else None,
            'slowest_api_response_time': api_response_times[0]['avg_response_time'] if api_response_times else 0
        }
    }
    
    return result
```

### 3. API权限控制

确保只有超级管理员可以访问这些图表数据API：

```python
# 伪代码示例
from rest_framework.permissions import IsAuthenticated
from common.permissions import IsSuperAdmin

class APIAnalysisView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    # ...
```

### 4. 数据缓存策略

对于计算密集型的图表数据，实施缓存策略：

```python
# 伪代码示例
from django.core.cache import cache

def get_api_call_trend(start_date, end_date, period='daily'):
    # 生成缓存键
    cache_key = f"api_call_trend_{period}_{start_date}_{end_date}"
    
    # 尝试从缓存获取数据
    cached_data = cache.get(cache_key)
    if cached_data:
        return cached_data
    
    # 计算数据
    # ...
    
    # 缓存数据（设置30分钟过期）
    cache.set(cache_key, result, 1800)
    
    return result
```

### 5. 前端实现

1. 在超级管理员仪表盘页面中添加API调用分析相关图表
2. 使用Chart.js或ECharts库渲染折线图和柱状图
3. 实现时间范围选择器和周期选择器

## 注意事项

1. 对于大型系统，APILog表可能会非常大，需要考虑以下优化措施：
   - 定期归档历史日志数据
   - 为APILog表创建适当的索引（如created_at、request_path、status_type）
   - 考虑使用数据库分区技术按时间分区
   
2. 对于实时监控需求，可以考虑以下方案：
   - 实现WebSocket实时推送API调用统计数据
   - 为关键API设置性能阈值告警
   
3. 数据可视化增强：
   - 为错误率较高的API添加视觉告警（如红色标记）
   - 提供API调用详情钻取功能，点击图表可查看具体API调用记录
   - 添加异常检测算法，自动识别异常的API调用模式
   
4. 安全考虑：
   - 确保API日志中不包含敏感信息
   - 对于包含敏感操作的API，考虑添加额外的审计日志记录 