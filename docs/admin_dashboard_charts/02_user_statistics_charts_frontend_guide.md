# 用户统计分析图表前端集成指南

本文档提供了用户统计分析图表API的详细集成指南，帮助前端开发人员将这些图表集成到管理员仪表盘中。

## API概览

用户统计分析图表API提供以下四个端点：

1. **用户总量与增长趋势**：系统内所有用户数量的时间序列图
2. **用户角色分布**：超级管理员、租户管理员、普通用户的比例饼图
3. **活跃用户统计**：按日/周/月统计的活跃用户数量折线图
4. **用户登录情况**：登录频次热力图，展示不同时间段的登录活跃度

所有API端点都需要超级管理员权限才能访问。

## 通用响应格式

所有图表API都使用统一的响应格式：

```json
{
  "code": 2000,
  "message": "success",
  "data": {
    "chart_type": "图表类型",
    "title": "图表标题",
    "description": "图表描述",
    // 其他图表特定数据...
    "summary": {
      // 汇总数据...
    }
  }
}
```

## 1. 用户总量与增长趋势 API

### 请求

```
GET /api/v1/charts/user-growth-trend/?period={daily|weekly|monthly|quarterly|yearly}&start_date={YYYY-MM-DD}&end_date={YYYY-MM-DD}
```

### 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| period | string | 否 | monthly | 统计周期，可选值为daily（日）、weekly（周）、monthly（月）、quarterly（季度）、yearly（年） |
| start_date | string | 否 | **当前日期往前一年** | 开始日期，格式为YYYY-MM-DD |
| end_date | string | 否 | **当前日期** | 结束日期，格式为YYYY-MM-DD |

### 响应

```json
{
  "code": 2000,
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
      "growth_rate": 120.0,
      "average_monthly_growth": 40.0
    }
  }
}
```

### 前端实现建议

- 使用双Y轴折线图，左侧Y轴显示用户总数，右侧Y轴显示新增用户数
- 在图表下方显示汇总数据，包括用户总数、增长率和平均月增长量
- 提供周期选择器和日期范围选择器

## 2. 用户角色分布 API

### 请求

```
GET /api/v1/charts/user-role-distribution/
```

### 响应

```json
{
  "code": 2000,
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
      "super_admin_percentage": 5.0,
      "tenant_admin_percentage": 25.0,
      "regular_user_percentage": 70.0
    }
  }
}
```

### 前端实现建议

- 使用饼图或环形图显示不同角色用户的比例
- 显示每个角色的具体数量和百分比
- 在图表旁边显示汇总数据

## 3. 活跃用户统计 API

### 请求

```
GET /api/v1/charts/active-users/?period={daily|weekly|monthly}&start_date={YYYY-MM-DD}&end_date={YYYY-MM-DD}
```

### 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| period | string | 否 | daily | 统计周期，可选值为daily（日）、weekly（周）、monthly（月） |
| start_date | string | 否 | **根据周期动态设置：<br>- daily: 最近30天<br>- weekly: 最近90天<br>- monthly: 最近一年** | 开始日期，格式为YYYY-MM-DD |
| end_date | string | 否 | **当前日期** | 结束日期，格式为YYYY-MM-DD |

### 响应

```json
{
  "code": 2000,
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
        "data": [45.0, 52.0, 49.0, ...],
        "color": "#E91E63",
        "yAxisID": "percentage"
      }
    ],
    "summary": {
      "average_active_users": 48.0,
      "highest_active_day": "2023-01-02",
      "highest_active_count": 52,
      "average_active_rate": 48.0
    }
  }
}
```

### 前端实现建议

- 使用双Y轴折线图，左侧Y轴显示活跃用户数，右侧Y轴显示活跃率（百分比）
- 提供周期选择器和日期范围选择器
- 在图表下方显示汇总数据，包括平均活跃用户数、最高活跃日及其用户数、平均活跃率

## 4. 用户登录情况 API

### 请求

```
GET /api/v1/charts/login-heatmap/?start_date={YYYY-MM-DD}&end_date={YYYY-MM-DD}
```

### 参数说明

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| start_date | string | 否 | **当前日期往前30天** | 开始日期，格式为YYYY-MM-DD |
| end_date | string | 否 | **当前日期** | 结束日期，格式为YYYY-MM-DD |

### 响应

```json
{
  "code": 2000,
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

### 前端实现建议

- 使用热力图展示不同时间段的登录活跃度
- X轴表示星期几（周一到周日），Y轴表示小时（0-23时）
- 使用颜色深浅表示登录次数的多少
- 提供日期范围选择器
- 在图表旁边显示汇总数据，包括总登录次数、高峰时段及其登录次数、低谷时段及其登录次数

## 错误处理

所有API在发生错误时会返回相应的HTTP状态码和错误信息：

- 401 Unauthorized：未认证或认证已过期
- 403 Forbidden：权限不足（非超级管理员）
- 500 Internal Server Error：服务器内部错误

错误响应格式：

```json
{
  "code": 403,
  "message": "您没有权限访问此资源",
  "data": null
}
```

## 前端集成示例

### 使用Chart.js集成用户总量与增长趋势图

```javascript
// 获取数据
async function fetchUserGrowthTrend(period = 'monthly', startDate, endDate) {
  const params = new URLSearchParams();
  if (period) params.append('period', period);
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);
  
  const response = await fetch(`/api/v1/charts/user-growth-trend/?${params}`);
  return await response.json();
}

// 渲染图表
function renderUserGrowthChart(chartData) {
  const ctx = document.getElementById('userGrowthChart').getContext('2d');
  
  new Chart(ctx, {
    type: 'line',
    data: {
      labels: chartData.labels,
      datasets: [
        {
          label: chartData.datasets[0].label,
          data: chartData.datasets[0].data,
          borderColor: chartData.datasets[0].color,
          backgroundColor: 'rgba(51, 102, 204, 0.1)',
          yAxisID: 'y-total',
        },
        {
          label: chartData.datasets[1].label,
          data: chartData.datasets[1].data,
          borderColor: chartData.datasets[1].color,
          backgroundColor: 'rgba(220, 57, 18, 0.1)',
          yAxisID: 'y-new',
        }
      ]
    },
    options: {
      responsive: true,
      scales: {
        'y-total': {
          type: 'linear',
          position: 'left',
          title: {
            display: true,
            text: '用户总数'
          }
        },
        'y-new': {
          type: 'linear',
          position: 'right',
          title: {
            display: true,
            text: '新增用户数'
          }
        }
      }
    }
  });
  
  // 显示汇总数据
  document.getElementById('totalUsers').textContent = chartData.summary.total_users;
  document.getElementById('growthRate').textContent = chartData.summary.growth_rate + '%';
  document.getElementById('avgMonthlyGrowth').textContent = chartData.summary.average_monthly_growth;
}

// 初始化
async function initUserGrowthChart() {
  try {
    const result = await fetchUserGrowthTrend();
    if (result.code === 2000) {
      renderUserGrowthChart(result.data);
    } else {
      console.error('获取用户增长趋势数据失败:', result.message);
    }
  } catch (error) {
    console.error('获取用户增长趋势数据出错:', error);
  }
}

// 调用初始化函数
initUserGrowthChart();
```

## 注意事项

1. 所有API都需要用户已认证并具有超级管理员权限
2. 图表数据会被缓存一段时间（通常为1小时），如需实时数据，可以添加时间戳参数强制刷新
3. 日期参数必须使用YYYY-MM-DD格式
4. 对于大量数据，请合理设置日期范围，避免请求超时
5. 建议在前端实现数据加载状态和错误处理 