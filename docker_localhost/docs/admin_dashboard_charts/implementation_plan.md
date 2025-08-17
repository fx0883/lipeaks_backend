# 租户图表API实现文档

## 一、创建charts应用

### 1. 创建应用

```bash
python manage.py startapp charts
```

### 2. 注册应用

在`settings.py`的`INSTALLED_APPS`中添加:

```python
'charts.apps.ChartsConfig',
```

## 二、应用结构

```
charts/
├── __init__.py
├── apps.py          # 应用配置
├── views.py         # API视图
├── urls.py          # URL路由
├── utils.py         # 工具函数
├── permissions.py   # 权限类
├── schema.py        # API文档模式
└── tests.py         # 测试
```

## 三、实现租户图表API

### 1. 定义权限类 (charts/permissions.py)

```python
from rest_framework import permissions
import logging

logger = logging.getLogger(__name__)

class IsSuperAdminOnly(permissions.BasePermission):
    """
    仅允许超级管理员访问的权限类
    """
    def has_permission(self, request, view):
        is_super_admin = bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.is_super_admin
        )
        
        if not is_super_admin:
            logger.warning(
                f"用户 {request.user.username if request.user.is_authenticated else 'Anonymous'} "
                f"尝试访问仅限超级管理员的图表API {request.path}"
            )
        
        return is_super_admin
```

### 2. 实现工具函数 (charts/utils.py)

```python
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth, TruncQuarter, TruncYear
from django.core.cache import cache

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
    # 实现日期范围生成逻辑
    # ...

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
```

### 3. 定义API模式 (charts/schema.py)

```python
from drf_spectacular.utils import OpenApiResponse, OpenApiExample

# 租户趋势图响应模式
tenant_trend_responses = {
    200: OpenApiResponse(
        description="租户趋势数据获取成功",
        examples=[
            OpenApiExample(
                name="租户趋势示例",
                value={
                    "code": 200,
                    "message": "success",
                    "data": {
                        "chart_type": "line",
                        "title": "租户数量趋势",
                        "description": "系统内租户总数随时间的变化趋势",
                        "labels": ["2023-01", "2023-02", "2023-03"],
                        "datasets": [
                            {
                                "label": "租户总数",
                                "data": [10, 15, 22],
                                "color": "#3366cc"
                            }
                        ],
                        "summary": {
                            "total": 22,
                            "growth_rate": 15.5,
                            "average_monthly_growth": 8.2
                        }
                    }
                }
            )
        ]
    ),
    403: OpenApiResponse(description="权限不足"),
    500: OpenApiResponse(description="服务器错误")
}

# 租户状态分布响应模式
tenant_status_distribution_responses = {
    # 类似的定义...
}

# 租户创建速率响应模式
tenant_creation_rate_responses = {
    # 类似的定义...
}
```

### 4. 实现API视图 (charts/views.py)

```python
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter

from django.db.models import Count
from django.core.cache import cache
from datetime import timedelta

from tenants.models import Tenant
from .permissions import IsSuperAdminOnly
from .utils import (
    get_date_trunc_func, get_cache_key, format_chart_response
)
from .schema import (
    tenant_trend_responses, tenant_status_distribution_responses, 
    tenant_creation_rate_responses
)

class BaseChartView(APIView):
    """
    图表API的基类
    """
    permission_classes = [IsAuthenticated, IsSuperAdminOnly]
    
    def get_cached_data(self, cache_key, ttl=3600):
        """获取缓存数据或设置缓存"""
        data = cache.get(cache_key)
        return data
        
    def set_cached_data(self, cache_key, data, ttl=3600):
        """设置缓存数据"""
        cache.set(cache_key, data, ttl)
        
    def format_response(self, data):
        """格式化API响应"""
        return Response({
            "code": 200,
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
        
        # 尝试从缓存获取数据
        cache_key = get_cache_key(
            'tenant_trend', 
            period=period,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat()
        )
        
        cached_data = self.get_cached_data(cache_key)
        if cached_data:
            return self.format_response(cached_data)
        
        # 查询数据
        try:
            # 获取时间截断函数
            trunc_func = get_date_trunc_func(period)
            
            # 按时间段查询租户创建数量
            tenant_counts = (
                Tenant.objects
                .filter(created_at__date__range=(start_date, end_date))
                .annotate(period=trunc_func('created_at'))
                .values('period')
                .annotate(count=Count('id'))
                .order_by('period')
            )
            
            # 处理数据，计算累计值
            dates = []
            counts = []
            cumulative = 0
            
            for item in tenant_counts:
                period_date = item['period'].date() if hasattr(item['period'], 'date') else item['period']
                period_str = period_date.strftime('%Y-%m-%d') if period == 'daily' else (
                    period_date.strftime('%Y-%m-%d') if period == 'weekly' else (
                        period_date.strftime('%Y-%m') if period == 'monthly' else (
                            f"{period_date.year}-Q{(period_date.month-1)//3+1}" if period == 'quarterly' else 
                            str(period_date.year)
                        )
                    )
                )
                
                cumulative += item['count']
                dates.append(period_str)
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
            
            # 缓存数据
            self.set_cached_data(cache_key, result)
            
            return self.format_response(result)
            
        except Exception as e:
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
        # 实现逻辑...
        pass


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
        # 实现逻辑...
        pass
```

### 5. 配置URL (charts/urls.py)

```python
from django.urls import path
from . import views

app_name = 'charts'

urlpatterns = [
    path('tenant-trend/', views.TenantTrendChartView.as_view(), name='tenant-trend'),
    path('tenant-status-distribution/', views.TenantStatusDistributionView.as_view(), name='tenant-status-distribution'),
    path('tenant-creation-rate/', views.TenantCreationRateView.as_view(), name='tenant-creation-rate'),
]
```

### 6. 将应用URL包含到主URL配置 (core/urls.py)

在`core/urls.py`的`api/v1/`路径下添加:

```python
# 图表数据API
path('admin/charts/', include('charts.urls', namespace='charts')),
```

## 四、单元测试

在`charts/tests.py`中实现测试用例，确保：

1. 权限控制测试：非超级管理员无法访问API
2. 功能测试：API返回正确格式的数据
3. 边界条件测试：处理异常参数和边界情况

## 五、部署和验证

1. 运行迁移命令（如果有模型）
2. 重启应用服务器
3. 使用超级管理员访问图表API验证功能
4. 查看API文档 (`/api/v1/docs/`) 确认API已正确记录

## 六、性能优化考虑

1. **查询优化**：对`created_at`字段建立索引
2. **缓存策略**：根据数据变更频率调整缓存过期时间
3. **异步加载**：考虑将耗时查询放入异步任务
4. **分页限制**：对大数据集实施分页或限制记录数
5. **定期预热**：设置定时任务提前计算和缓存常用图表数据 