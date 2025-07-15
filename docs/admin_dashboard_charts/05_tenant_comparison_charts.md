# 租户对比分析图表

## 图表清单

1. **租户活跃度排名**：基于API调用量、用户活跃度等指标的租户排名
2. **租户增长速度对比**：各租户用户增长速度的对比图
3. **租户资源利用率对比**：各租户资源配额使用率的雷达图

## 数据源分析

这些图表的数据主要来源于以下模型：

1. `tenants.Tenant`模型：租户基本信息
2. `tenants.TenantQuota`模型：租户资源配额和使用情况
3. `users.User`模型：用户信息，包括创建时间和租户关联
4. `common.APILog`模型：API调用记录，包括租户关联

## API设计

### 1. 租户活跃度排名 API

#### 请求

```
GET /api/v1/admin/charts/tenant-activity-ranking/?period={daily|weekly|monthly}&start_date={YYYY-MM-DD}&end_date={YYYY-MM-DD}&top={number}
```

#### 参数说明

- `period`：统计周期，可选值为daily（日）、weekly（周）、monthly（月）
- `start_date`：开始日期，格式为YYYY-MM-DD
- `end_date`：结束日期，格式为YYYY-MM-DD
- `top`：返回排名前N的租户，默认为10

#### 响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "chart_type": "bar",
    "title": "租户活跃度排名",
    "description": "基于API调用量、用户活跃度等指标的租户排名",
    "labels": ["租户A", "租户B", "租户C", ...],
    "datasets": [
      {
        "label": "API调用量",
        "data": [5600, 4200, 3800, ...],
        "color": "#2196F3"
      },
      {
        "label": "活跃用户数",
        "data": [120, 95, 85, ...],
        "color": "#4CAF50"
      },
      {
        "label": "活跃度得分",
        "data": [85, 78, 72, ...],
        "color": "#FF9800"
      }
    ],
    "summary": {
      "most_active_tenant": "租户A",
      "most_active_tenant_score": 85,
      "average_activity_score": 65
    }
  }
}
```

### 2. 租户增长速度对比 API

#### 请求

```
GET /api/v1/admin/charts/tenant-growth-comparison/?period={monthly|quarterly|yearly}&start_date={YYYY-MM-DD}&end_date={YYYY-MM-DD}&top={number}
```

#### 参数说明

- `period`：统计周期，可选值为monthly（月）、quarterly（季度）、yearly（年）
- `start_date`：开始日期，格式为YYYY-MM-DD
- `end_date`：结束日期，格式为YYYY-MM-DD
- `top`：返回增长最快的前N个租户，默认为10

#### 响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "chart_type": "line",
    "title": "租户增长速度对比",
    "description": "各租户用户增长速度的对比图",
    "labels": ["2023-01", "2023-02", "2023-03", ...],
    "datasets": [
      {
        "label": "租户A",
        "data": [100, 120, 150, ...],
        "color": "#3F51B5"
      },
      {
        "label": "租户B",
        "data": [80, 90, 105, ...],
        "color": "#E91E63"
      },
      {
        "label": "租户C",
        "data": [50, 70, 100, ...],
        "color": "#009688"
      }
    ],
    "summary": {
      "fastest_growing_tenant": "租户C",
      "fastest_growth_rate": 100,
      "average_growth_rate": 45
    }
  }
}
```

### 3. 租户资源利用率对比 API

#### 请求

```
GET /api/v1/admin/charts/tenant-resource-usage/?top={number}
```

#### 参数说明

- `top`：返回资源利用率最高的前N个租户，默认为10

#### 响应

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "chart_type": "radar",
    "title": "租户资源利用率对比",
    "description": "各租户资源配额使用率的雷达图",
    "labels": ["用户数", "管理员数", "存储空间", "产品数"],
    "datasets": [
      {
        "label": "租户A",
        "data": [85, 60, 75, 40],
        "color": "#3F51B5"
      },
      {
        "label": "租户B",
        "data": [70, 80, 65, 90],
        "color": "#E91E63"
      },
      {
        "label": "租户C",
        "data": [60, 50, 95, 70],
        "color": "#009688"
      }
    ],
    "summary": {
      "highest_resource_usage_tenant": "租户C",
      "highest_resource_type": "存储空间",
      "highest_usage_percentage": 95,
      "average_usage_percentage": 68.75
    }
  }
}
```

## 实现步骤

### 1. 创建图表数据视图

1. 在`common`应用中的`charts`子目录下创建`tenant_comparison_charts.py`文件
2. 实现租户对比分析相关的图表数据API视图
3. 在`urls.py`文件中配置API路由

### 2. 数据查询与处理

#### 租户活跃度排名

1. 计算每个租户在指定时间段内的API调用量
2. 计算每个租户在指定时间段内的活跃用户数
3. 结合API调用量和活跃用户数计算活跃度得分
4. 按活跃度得分降序排序

```python
# 伪代码示例
from django.db.models import Count, F, Sum, Q
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
from common.models import APILog
from tenants.models import Tenant
from users.models import User

def get_tenant_activity_ranking(start_date, end_date, period='monthly', top=10):
    # 根据period选择合适的时间截断函数
    trunc_func = {
        'daily': TruncDay,
        'weekly': TruncWeek,
        'monthly': TruncMonth
    }.get(period, TruncMonth)
    
    # 计算每个租户的API调用量
    tenant_api_calls = APILog.objects.filter(
        created_at__range=[start_date, end_date],
        tenant__isnull=False  # 确保有关联租户
    ).values('tenant').annotate(
        api_calls=Count('id')
    )
    
    # 计算每个租户的活跃用户数
    tenant_active_users = APILog.objects.filter(
        created_at__range=[start_date, end_date],
        tenant__isnull=False,  # 确保有关联租户
        user__isnull=False  # 确保有关联用户
    ).values('tenant').annotate(
        active_users=Count('user', distinct=True)
    )
    
    # 获取所有租户
    tenants = Tenant.objects.filter(
        status='active',
        is_deleted=False
    )
    
    # 合并数据
    tenant_activity = []
    for tenant in tenants:
        # 获取该租户的API调用量
        api_calls = next((item['api_calls'] for item in tenant_api_calls if item['tenant'] == tenant.id), 0)
        
        # 获取该租户的活跃用户数
        active_users = next((item['active_users'] for item in tenant_active_users if item['tenant'] == tenant.id), 0)
        
        # 获取该租户的总用户数
        total_users = User.objects.filter(tenant=tenant, is_deleted=False).count()
        
        # 计算活跃度得分 (可以根据实际需求调整计算方法)
        # 这里使用一个简单的加权平均: 60% API调用量 + 40% 用户活跃率
        if total_users > 0:
            user_activity_rate = (active_users / total_users) * 100
        else:
            user_activity_rate = 0
        
        activity_score = (api_calls * 0.6) + (user_activity_rate * 0.4)
        
        tenant_activity.append({
            'tenant_id': tenant.id,
            'tenant_name': tenant.name,
            'api_calls': api_calls,
            'active_users': active_users,
            'total_users': total_users,
            'activity_score': activity_score
        })
    
    # 按活跃度得分降序排序
    sorted_tenants = sorted(tenant_activity, key=lambda x: x['activity_score'], reverse=True)[:top]
    
    # 计算平均活跃度得分
    average_score = sum(item['activity_score'] for item in tenant_activity) / len(tenant_activity) if tenant_activity else 0
    
    # 格式化结果
    labels = [item['tenant_name'] for item in sorted_tenants]
    api_calls_data = [item['api_calls'] for item in sorted_tenants]
    active_users_data = [item['active_users'] for item in sorted_tenants]
    activity_scores = [round(item['activity_score'], 2) for item in sorted_tenants]
    
    result = {
        'labels': labels,
        'datasets': [
            {
                'label': 'API调用量',
                'data': api_calls_data,
                'color': '#2196F3'
            },
            {
                'label': '活跃用户数',
                'data': active_users_data,
                'color': '#4CAF50'
            },
            {
                'label': '活跃度得分',
                'data': activity_scores,
                'color': '#FF9800'
            }
        ],
        'summary': {
            'most_active_tenant': sorted_tenants[0]['tenant_name'] if sorted_tenants else None,
            'most_active_tenant_score': sorted_tenants[0]['activity_score'] if sorted_tenants else 0,
            'average_activity_score': round(average_score, 2)
        }
    }
    
    return result
```

#### 租户增长速度对比

1. 按照指定的时间周期（月/季/年）分组，计算每个租户在每个时间段内的新增用户数
2. 计算每个租户的用户增长率
3. 按增长率降序排序，选择增长最快的租户

```python
# 伪代码示例
from django.db.models import Count
from django.db.models.functions import TruncMonth, TruncQuarter, TruncYear
from users.models import User
from tenants.models import Tenant

def get_tenant_growth_comparison(start_date, end_date, period='monthly', top=10):
    # 根据period选择合适的时间截断函数
    trunc_func = {
        'monthly': TruncMonth,
        'quarterly': TruncQuarter,
        'yearly': TruncYear
    }.get(period, TruncMonth)
    
    # 获取活跃租户
    active_tenants = Tenant.objects.filter(
        status='active',
        is_deleted=False
    )
    
    # 计算每个租户在每个时间段的新增用户数
    tenant_growth_data = {}
    for tenant in active_tenants:
        # 查询该租户在每个时间段的新增用户数
        new_users_by_period = User.objects.filter(
            tenant=tenant,
            date_joined__range=[start_date, end_date],
            is_deleted=False
        ).annotate(
            period=trunc_func('date_joined')
        ).values('period').annotate(
            count=Count('id')
        ).order_by('period')
        
        # 如果有数据，添加到结果中
        if new_users_by_period:
            tenant_growth_data[tenant.name] = {
                'tenant_id': tenant.id,
                'periods': [item['period'].strftime('%Y-%m') for item in new_users_by_period],
                'new_users': [item['count'] for item in new_users_by_period],
                'total_new_users': sum(item['count'] for item in new_users_by_period)
            }
    
    # 计算每个租户的增长率
    for tenant_name, data in tenant_growth_data.items():
        if len(data['new_users']) >= 2:
            # 计算增长率: (最后一期 - 第一期) / 第一期 * 100%
            first_period = data['new_users'][0]
            last_period = data['new_users'][-1]
            if first_period > 0:
                growth_rate = ((last_period - first_period) / first_period) * 100
            else:
                growth_rate = float('inf') if last_period > 0 else 0
        else:
            growth_rate = 0
        
        tenant_growth_data[tenant_name]['growth_rate'] = growth_rate
    
    # 按增长率降序排序
    sorted_tenants = sorted(
        tenant_growth_data.items(),
        key=lambda x: x[1]['growth_rate'],
        reverse=True
    )[:top]
    
    # 获取所有时间段的并集
    all_periods = set()
    for _, data in sorted_tenants:
        all_periods.update(data['periods'])
    all_periods = sorted(all_periods)
    
    # 格式化结果
    datasets = []
    for tenant_name, data in sorted_tenants:
        # 为每个租户创建一个完整的时间序列，缺失的时间段填充0
        tenant_data = []
        for period in all_periods:
            if period in data['periods']:
                idx = data['periods'].index(period)
                tenant_data.append(data['new_users'][idx])
            else:
                tenant_data.append(0)
        
        datasets.append({
            'label': tenant_name,
            'data': tenant_data,
            'color': get_color_for_tenant(tenant_name)  # 为每个租户分配一个颜色
        })
    
    # 计算平均增长率
    growth_rates = [data['growth_rate'] for _, data in sorted_tenants]
    average_growth_rate = sum(growth_rates) / len(growth_rates) if growth_rates else 0
    
    # 找出增长最快的租户
    fastest_tenant = sorted_tenants[0][0] if sorted_tenants else None
    fastest_growth_rate = sorted_tenants[0][1]['growth_rate'] if sorted_tenants else 0
    
    result = {
        'labels': all_periods,
        'datasets': datasets,
        'summary': {
            'fastest_growing_tenant': fastest_tenant,
            'fastest_growth_rate': round(fastest_growth_rate, 2),
            'average_growth_rate': round(average_growth_rate, 2)
        }
    }
    
    return result

def get_color_for_tenant(tenant_name):
    """为租户分配一个固定的颜色"""
    # 这里可以实现一个简单的哈希函数，根据租户名称生成一个颜色
    # 或者使用预定义的颜色列表
    colors = ['#3F51B5', '#E91E63', '#009688', '#FF5722', '#607D8B', 
              '#FFC107', '#2196F3', '#4CAF50', '#9C27B0', '#795548']
    
    # 使用租户名称的哈希值选择颜色
    index = hash(tenant_name) % len(colors)
    return colors[index]
```

#### 租户资源利用率对比

1. 计算每个租户的资源配额使用率（用户数、管理员数、存储空间、产品数）
2. 按照总体资源利用率降序排序
3. 为每个租户生成资源利用率雷达图数据

```python
# 伪代码示例
from django.db.models import Count, F, ExpressionWrapper, FloatField
from tenants.models import Tenant, TenantQuota
from users.models import User

def get_tenant_resource_usage(top=10):
    # 获取活跃租户及其配额
    tenants_with_quotas = Tenant.objects.filter(
        status='active',
        is_deleted=False
    ).select_related('quota')
    
    # 计算每个租户的资源使用情况
    tenant_resource_usage = []
    for tenant in tenants_with_quotas:
        try:
            quota = tenant.quota
            
            # 计算用户数使用率
            total_users = User.objects.filter(tenant=tenant, is_deleted=False).count()
            user_usage = (total_users / quota.max_users) * 100 if quota.max_users > 0 else 0
            
            # 计算管理员数使用率
            admin_users = User.objects.filter(tenant=tenant, is_admin=True, is_deleted=False).count()
            admin_usage = (admin_users / quota.max_admins) * 100 if quota.max_admins > 0 else 0
            
            # 获取存储空间使用率
            storage_usage = (quota.current_storage_used_mb / quota.max_storage_mb) * 100 if quota.max_storage_mb > 0 else 0
            
            # 获取产品数使用率 (假设有产品模型)
            # 这里需要根据实际情况修改
            product_count = 0  # 需要替换为实际的产品数查询
            product_usage = (product_count / quota.max_products) * 100 if quota.max_products > 0 else 0
            
            # 计算总体资源利用率 (简单平均)
            overall_usage = (user_usage + admin_usage + storage_usage + product_usage) / 4
            
            tenant_resource_usage.append({
                'tenant_id': tenant.id,
                'tenant_name': tenant.name,
                'user_usage': round(user_usage, 2),
                'admin_usage': round(admin_usage, 2),
                'storage_usage': round(storage_usage, 2),
                'product_usage': round(product_usage, 2),
                'overall_usage': round(overall_usage, 2)
            })
            
        except TenantQuota.DoesNotExist:
            # 如果租户没有配额记录，跳过
            continue
    
    # 按总体资源利用率降序排序
    sorted_tenants = sorted(tenant_resource_usage, key=lambda x: x['overall_usage'], reverse=True)[:top]
    
    # 格式化结果
    datasets = []
    for tenant in sorted_tenants:
        datasets.append({
            'label': tenant['tenant_name'],
            'data': [
                tenant['user_usage'],
                tenant['admin_usage'],
                tenant['storage_usage'],
                tenant['product_usage']
            ],
            'color': get_color_for_tenant(tenant['tenant_name'])
        })
    
    # 找出资源使用率最高的租户和资源类型
    highest_tenant = None
    highest_resource = None
    highest_usage = 0
    
    for tenant in sorted_tenants:
        for resource, usage in [
            ('用户数', tenant['user_usage']),
            ('管理员数', tenant['admin_usage']),
            ('存储空间', tenant['storage_usage']),
            ('产品数', tenant['product_usage'])
        ]:
            if usage > highest_usage:
                highest_usage = usage
                highest_tenant = tenant['tenant_name']
                highest_resource = resource
    
    # 计算平均资源使用率
    all_usages = []
    for tenant in tenant_resource_usage:
        all_usages.extend([
            tenant['user_usage'],
            tenant['admin_usage'],
            tenant['storage_usage'],
            tenant['product_usage']
        ])
    average_usage = sum(all_usages) / len(all_usages) if all_usages else 0
    
    result = {
        'labels': ['用户数', '管理员数', '存储空间', '产品数'],
        'datasets': datasets,
        'summary': {
            'highest_resource_usage_tenant': highest_tenant,
            'highest_resource_type': highest_resource,
            'highest_usage_percentage': round(highest_usage, 2),
            'average_usage_percentage': round(average_usage, 2)
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

class TenantComparisonView(APIView):
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    # ...
```

### 4. 数据缓存策略

对于计算密集型的图表数据，实施缓存策略：

```python
# 伪代码示例
from django.core.cache import cache

def get_tenant_activity_ranking(start_date, end_date, period='monthly', top=10):
    # 生成缓存键
    cache_key = f"tenant_activity_{period}_{start_date}_{end_date}_{top}"
    
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

1. 在超级管理员仪表盘页面中添加租户对比分析相关图表
2. 使用Chart.js或ECharts库渲染柱状图、折线图和雷达图
3. 实现租户筛选功能，允许超级管理员选择要比较的租户
4. 实现时间范围选择器和周期选择器

## 注意事项

1. **数据量考虑**：
   - 对于大型系统，租户数量可能很多，需要实现分页或限制返回的租户数量
   - 考虑使用异步加载方式，避免一次性加载过多数据

2. **公平比较**：
   - 不同规模的租户可能不具有可比性，考虑添加按租户规模分组的功能
   - 提供相对指标（如人均API调用量）和绝对指标的切换

3. **隐私考虑**：
   - 确保不同租户之间的数据隔离，租户管理员不应看到其他租户的详细数据
   - 在展示租户对比数据时，可以考虑匿名化处理

4. **可视化增强**：
   - 为租户分配固定的颜色，便于在不同图表中识别相同租户
   - 提供图表导出功能，支持导出为图片或PDF格式
   - 实现图表交互功能，如点击某个租户可以查看该租户的详细数据 