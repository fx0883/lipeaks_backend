# 系统健康状态图表

## 图表清单

1. **系统错误日志统计**：按严重程度分类的错误日志数量趋势
2. **API性能监控**：系统整体API响应时间的变化趋势
3. **数据库性能指标**：数据库查询性能、连接数等关键指标

## 数据源分析

这些图表的数据主要来源于以下几个方面：

1. **系统错误日志**：
   - Django日志系统记录的错误日志
   - 需要实现日志解析和分析功能

2. **API性能数据**：
   - `common.APILog`模型中的响应时间数据
   - 响应时间异常的API调用记录

3. **数据库性能数据**：
   - 需要实现数据库性能监控功能
   - 可以使用Django数据库连接钩子或第三方监控工具

## API设计

### 1. 系统错误日志统计 API

#### 请求

```
GET /api/v1/admin/charts/error-logs-stats/?period={daily|weekly|monthly}&start_date={YYYY-MM-DD}&end_date={YYYY-MM-DD}
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
    "chart_type": "stacked_bar",
    "title": "系统错误日志统计",
    "description": "按严重程度分类的错误日志数量趋势",
    "labels": ["2023-01-01", "2023-01-02", "2023-01-03", ...],
    "datasets": [
      {
        "label": "严重错误",
        "data": [2, 1, 0, ...],
        "color": "#F44336"
      },
      {
        "label": "警告",
        "data": [8, 5, 7, ...],
        "color": "#FF9800"
      },
      {
        "label": "一般错误",
        "data": [15, 12, 10, ...],
        "color": "#2196F3"
      }
    ],
    "summary": {
      "total_errors": 150,
      "critical_errors": 20,
      "warnings": 50,
      "general_errors": 80,
      "trend": "decreasing"
    }
  }
}
```

### 2. API性能监控 API

#### 请求

```
GET /api/v1/admin/charts/api-performance/?period={hourly|daily|weekly|monthly}&start_date={YYYY-MM-DD}&end_date={YYYY-MM-DD}
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
    "title": "API性能监控",
    "description": "系统整体API响应时间的变化趋势",
    "labels": ["2023-01-01", "2023-01-02", "2023-01-03", ...],
    "datasets": [
      {
        "label": "平均响应时间(ms)",
        "data": [120, 135, 110, ...],
        "color": "#3F51B5"
      },
      {
        "label": "95%响应时间(ms)",
        "data": [250, 280, 230, ...],
        "color": "#E91E63"
      },
      {
        "label": "最大响应时间(ms)",
        "data": [450, 520, 410, ...],
        "color": "#FF5722"
      }
    ],
    "summary": {
      "overall_average": 125,
      "overall_95_percentile": 260,
      "overall_maximum": 520,
      "trend": "stable"
    }
  }
}
```

### 3. 数据库性能指标 API

#### 请求

```
GET /api/v1/admin/charts/database-performance/?period={hourly|daily|weekly}&start_date={YYYY-MM-DD}&end_date={YYYY-MM-DD}
```

#### 参数说明

- `period`：统计周期，可选值为hourly（小时）、daily（日）、weekly（周）
- `start_date`：开始日期，格式为YYYY-MM-DD
- `end_date`：结束日期，格式为YYYY-MM-DD

#### 响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "chart_type": "multi_line",
    "title": "数据库性能指标",
    "description": "数据库查询性能、连接数等关键指标",
    "labels": ["2023-01-01", "2023-01-02", "2023-01-03", ...],
    "datasets": [
      {
        "label": "平均查询时间(ms)",
        "data": [25, 28, 22, ...],
        "color": "#673AB7",
        "yAxisID": "time"
      },
      {
        "label": "活跃连接数",
        "data": [12, 15, 10, ...],
        "color": "#009688",
        "yAxisID": "connections"
      },
      {
        "label": "查询缓存命中率(%)",
        "data": [75, 72, 78, ...],
        "color": "#8BC34A",
        "yAxisID": "percentage"
      }
    ],
    "summary": {
      "average_query_time": 25,
      "average_connections": 12,
      "average_cache_hit_rate": 75,
      "slow_queries_percentage": 3.2
    }
  }
}
```

## 实现步骤

### 1. 创建图表数据视图

1. 在`common`应用中的`charts`子目录下创建`system_health_charts.py`文件
2. 实现系统健康状态相关的图表数据API视图
3. 在`urls.py`文件中配置API路由

### 2. 数据查询与处理

#### 系统错误日志统计

1. 实现日志文件解析功能，从Django日志文件中提取错误信息
2. 按照严重程度（严重错误、警告、一般错误）分类统计
3. 按照指定的时间周期（日/周/月）分组计算错误数量

```python
# 伪代码示例
import re
import os
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from django.conf import settings

def parse_log_file(log_file_path, start_date, end_date):
    """解析日志文件，提取错误信息"""
    # 定义错误级别的正则表达式模式
    error_patterns = {
        'critical': re.compile(r'\[CRITICAL\]|\[FATAL\]'),
        'warning': re.compile(r'\[WARNING\]'),
        'error': re.compile(r'\[ERROR\]')
    }
    
    # 日期格式
    date_pattern = re.compile(r'(\d{4}-\d{2}-\d{2})')
    
    # 存储结果的数据结构
    results = defaultdict(lambda: {'critical': 0, 'warning': 0, 'error': 0})
    
    # 读取日志文件
    try:
        with open(log_file_path, 'r') as file:
            for line in file:
                # 提取日期
                date_match = date_pattern.search(line)
                if not date_match:
                    continue
                    
                log_date_str = date_match.group(1)
                log_date = datetime.strptime(log_date_str, '%Y-%m-%d').date()
                
                # 检查日期是否在指定范围内
                if log_date < start_date or log_date > end_date:
                    continue
                
                # 检查错误级别
                for level, pattern in error_patterns.items():
                    if pattern.search(line):
                        results[log_date_str][level] += 1
                        break
        
        return results
    except Exception as e:
        logging.error(f"解析日志文件时出错: {str(e)}")
        return {}

def get_error_logs_stats(start_date, end_date, period='daily'):
    """获取错误日志统计数据"""
    # 获取日志文件路径
    log_file_path = os.path.join(settings.BASE_DIR, 'logs', 'django.log')
    
    # 解析日志文件
    log_data = parse_log_file(log_file_path, start_date, end_date)
    
    # 根据周期聚合数据
    if period == 'weekly' or period == 'monthly':
        aggregated_data = aggregate_by_period(log_data, period, start_date, end_date)
    else:
        aggregated_data = log_data
    
    # 格式化结果
    labels = sorted(aggregated_data.keys())
    datasets = {
        'critical': [],
        'warning': [],
        'error': []
    }
    
    for date in labels:
        for level in ['critical', 'warning', 'error']:
            datasets[level].append(aggregated_data[date][level])
    
    # 计算总计
    total_critical = sum(datasets['critical'])
    total_warning = sum(datasets['warning'])
    total_error = sum(datasets['error'])
    total_all = total_critical + total_warning + total_error
    
    result = {
        'labels': labels,
        'datasets': [
            {
                'label': '严重错误',
                'data': datasets['critical'],
                'color': '#F44336'
            },
            {
                'label': '警告',
                'data': datasets['warning'],
                'color': '#FF9800'
            },
            {
                'label': '一般错误',
                'data': datasets['error'],
                'color': '#2196F3'
            }
        ],
        'summary': {
            'total_errors': total_all,
            'critical_errors': total_critical,
            'warnings': total_warning,
            'general_errors': total_error,
            'trend': determine_trend(datasets['critical'] + datasets['warning'] + datasets['error'])
        }
    }
    
    return result

def aggregate_by_period(log_data, period, start_date, end_date):
    """按周或月聚合日志数据"""
    # 实现周或月的聚合逻辑
    # ...
    
def determine_trend(data_series):
    """确定数据趋势（增加、减少或稳定）"""
    if len(data_series) < 2:
        return "stable"
    
    first_half = sum(data_series[:len(data_series)//2])
    second_half = sum(data_series[len(data_series)//2:])
    
    if second_half > first_half * 1.1:
        return "increasing"
    elif second_half < first_half * 0.9:
        return "decreasing"
    else:
        return "stable"
```

#### API性能监控

1. 使用`common.APILog`模型数据，按照指定的时间周期分组
2. 计算每个时间段的平均响应时间、95%分位响应时间和最大响应时间

```python
# 伪代码示例
from django.db.models import Avg, Max, Count, F
from django.db.models.functions import TruncHour, TruncDay, TruncWeek, TruncMonth
from common.models import APILog
import numpy as np

def get_api_performance(start_date, end_date, period='daily'):
    # 根据period选择合适的时间截断函数
    trunc_func = {
        'hourly': TruncHour,
        'daily': TruncDay,
        'weekly': TruncWeek,
        'monthly': TruncMonth
    }.get(period, TruncDay)
    
    # 查询每个时间段的平均响应时间
    avg_response_times = APILog.objects.filter(
        created_at__range=[start_date, end_date]
    ).annotate(
        period=trunc_func('created_at')
    ).values('period').annotate(
        avg_time=Avg('response_time'),
        max_time=Max('response_time'),
        count=Count('id')
    ).order_by('period')
    
    # 计算95%分位响应时间
    percentile_data = {}
    for period_data in avg_response_times:
        period_key = period_data['period'].strftime('%Y-%m-%d')
        # 为每个时间段查询所有响应时间
        response_times = list(APILog.objects.filter(
            created_at__range=[period_data['period'], period_data['period'] + timedelta(days=1)]
        ).values_list('response_time', flat=True))
        
        if response_times:
            percentile_95 = np.percentile(response_times, 95)
        else:
            percentile_95 = 0
        
        percentile_data[period_key] = percentile_95
    
    # 格式化结果
    labels = [item['period'].strftime('%Y-%m-%d') for item in avg_response_times]
    avg_times = [item['avg_time'] for item in avg_response_times]
    max_times = [item['max_time'] for item in avg_response_times]
    percentile_95_times = [percentile_data[label] for label in labels]
    
    # 计算总体指标
    overall_avg = sum(avg_times) / len(avg_times) if avg_times else 0
    overall_max = max(max_times) if max_times else 0
    overall_95 = sum(percentile_95_times) / len(percentile_95_times) if percentile_95_times else 0
    
    result = {
        'labels': labels,
        'datasets': [
            {
                'label': '平均响应时间(ms)',
                'data': avg_times,
                'color': '#3F51B5'
            },
            {
                'label': '95%响应时间(ms)',
                'data': percentile_95_times,
                'color': '#E91E63'
            },
            {
                'label': '最大响应时间(ms)',
                'data': max_times,
                'color': '#FF5722'
            }
        ],
        'summary': {
            'overall_average': overall_avg,
            'overall_95_percentile': overall_95,
            'overall_maximum': overall_max,
            'trend': determine_trend(avg_times)
        }
    }
    
    return result
```

#### 数据库性能指标

1. 实现数据库性能监控功能，收集查询时间、连接数和缓存命中率等指标
2. 可以使用Django数据库连接钩子或第三方监控工具

```python
# 伪代码示例
from django.db import connection
from django.conf import settings
import time
import pymysql
import redis

class DatabasePerformanceMonitor:
    """数据库性能监控类"""
    
    def __init__(self):
        self.db_settings = settings.DATABASES['default']
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB
        )
    
    def get_connection_stats(self):
        """获取数据库连接统计信息"""
        try:
            # 连接到MySQL
            conn = pymysql.connect(
                host=self.db_settings['HOST'],
                user=self.db_settings['USER'],
                password=self.db_settings['PASSWORD'],
                db=self.db_settings['NAME'],
                port=int(self.db_settings['PORT'])
            )
            
            cursor = conn.cursor()
            
            # 查询活跃连接数
            cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
            threads_connected = int(cursor.fetchone()[1])
            
            # 查询最大连接数
            cursor.execute("SHOW VARIABLES LIKE 'max_connections'")
            max_connections = int(cursor.fetchone()[1])
            
            # 查询缓存命中率
            cursor.execute("SHOW STATUS LIKE 'Qcache_hits'")
            qcache_hits = int(cursor.fetchone()[1])
            
            cursor.execute("SHOW STATUS LIKE 'Com_select'")
            com_select = int(cursor.fetchone()[1])
            
            # 计算缓存命中率
            cache_hit_rate = (qcache_hits / (qcache_hits + com_select)) * 100 if (qcache_hits + com_select) > 0 else 0
            
            # 查询慢查询数量
            cursor.execute("SHOW GLOBAL STATUS LIKE 'Slow_queries'")
            slow_queries = int(cursor.fetchone()[1])
            
            cursor.close()
            conn.close()
            
            return {
                'active_connections': threads_connected,
                'max_connections': max_connections,
                'connection_usage': (threads_connected / max_connections) * 100,
                'cache_hit_rate': cache_hit_rate,
                'slow_queries': slow_queries
            }
        except Exception as e:
            logging.error(f"获取数据库连接统计信息时出错: {str(e)}")
            return {
                'active_connections': 0,
                'max_connections': 0,
                'connection_usage': 0,
                'cache_hit_rate': 0,
                'slow_queries': 0
            }
    
    def get_query_performance(self):
        """获取查询性能指标"""
        try:
            # 使用Django连接执行测试查询
            start_time = time.time()
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            end_time = time.time()
            
            query_time = (end_time - start_time) * 1000  # 转换为毫秒
            
            return {
                'query_time': query_time
            }
        except Exception as e:
            logging.error(f"获取查询性能指标时出错: {str(e)}")
            return {
                'query_time': 0
            }
    
    def get_performance_metrics(self):
        """获取所有性能指标"""
        connection_stats = self.get_connection_stats()
        query_performance = self.get_query_performance()
        
        return {
            **connection_stats,
            **query_performance
        }

def get_database_performance(start_date, end_date, period='hourly'):
    """获取数据库性能指标历史数据"""
    # 从Redis中获取历史性能数据
    # 假设我们已经设置了一个定时任务，每小时收集一次性能数据并存储在Redis中
    
    # 实现从Redis获取历史数据的逻辑
    # ...
    
    # 如果没有历史数据，则获取当前性能指标
    monitor = DatabasePerformanceMonitor()
    current_metrics = monitor.get_performance_metrics()
    
    # 格式化结果
    # ...
    
    return result
```

### 3. API权限控制

确保只有超级管理员可以访问这些图表数据API：

```python
# 伪代码示例
from rest_framework.permissions import IsAuthenticated
from common.permissions import IsSuperAdmin

class SystemHealthView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    # ...
```

### 4. 数据缓存策略

对于计算密集型的图表数据，实施缓存策略：

```python
# 伪代码示例
from django.core.cache import cache

def get_error_logs_stats(start_date, end_date, period='daily'):
    # 生成缓存键
    cache_key = f"error_logs_stats_{period}_{start_date}_{end_date}"
    
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

### 5. 定时任务收集性能数据

使用Celery实现定时任务，定期收集系统健康状态数据：

```python
# 伪代码示例
from celery import shared_task
from datetime import datetime
import redis
import json

@shared_task
def collect_system_health_data():
    """定时收集系统健康状态数据"""
    # 收集数据库性能指标
    monitor = DatabasePerformanceMonitor()
    db_metrics = monitor.get_performance_metrics()
    
    # 收集API性能指标
    api_metrics = collect_api_performance_metrics()
    
    # 收集错误日志统计
    error_logs = collect_error_logs_stats()
    
    # 组合所有指标
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'database': db_metrics,
        'api': api_metrics,
        'error_logs': error_logs
    }
    
    # 存储到Redis
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB
    )
    
    # 使用时间戳作为键
    key = f"system_health:{datetime.now().strftime('%Y-%m-%d:%H')}"
    redis_client.set(key, json.dumps(metrics))
    
    # 设置过期时间（例如保留7天）
    redis_client.expire(key, 7 * 24 * 60 * 60)
    
    return True
```

### 6. 前端实现

1. 在超级管理员仪表盘页面中添加系统健康状态相关图表
2. 使用Chart.js或ECharts库渲染折线图和堆叠柱状图
3. 实现时间范围选择器和周期选择器
4. 为关键指标添加阈值告警功能

## 注意事项

1. **性能考虑**：
   - 日志解析是CPU密集型操作，应该异步执行或使用缓存
   - 数据库性能监控应该尽量减少对生产系统的影响

2. **安全考虑**：
   - 确保系统健康状态数据只对超级管理员可见
   - 日志解析过程中需要注意敏感信息的处理

3. **可扩展性**：
   - 设计灵活的数据收集和存储机制，便于添加新的健康指标
   - 考虑使用专业的监控工具（如Prometheus、Grafana）进行更全面的系统监控

4. **告警机制**：
   - 实现关键指标的告警阈值设置功能
   - 当指标超过阈值时，通过邮件、短信等方式通知管理员

5. **历史数据管理**：
   - 实现历史数据的归档和清理策略
   - 考虑使用时序数据库存储长期的性能指标数据 