# 活跃用户统计 API

## 功能描述

此API提供按日/周/月统计的活跃用户数量和活跃率数据。活跃用户定义为在指定时间段内至少有一次API调用的用户。此API适用于生成折线图，帮助管理员了解系统用户活跃度的变化趋势。

## 请求

### 请求URL

```
GET /api/v1/charts/active-users/
```

### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| period | string | 否 | daily | 统计周期，可选值为daily（日）、weekly（周）、monthly（月） |
| start_date | string | 否 | **根据周期动态设置：<br>- daily: 最近30天<br>- weekly: 最近90天<br>- monthly: 最近一年** | 开始日期，格式为YYYY-MM-DD |
| end_date | string | 否 | **当前日期** | 结束日期，格式为YYYY-MM-DD |

### 请求示例

```
GET /api/v1/charts/active-users/?period=weekly&start_date=2023-01-01&end_date=2023-03-31
```

## 响应

### 响应参数

| 参数 | 类型 | 说明 |
|------|------|------|
| code | integer | 响应码，2000表示成功 |
| message | string | 响应消息 |
| data | object | 响应数据 |
| data.chart_type | string | 图表类型，固定为"line" |
| data.title | string | 图表标题 |
| data.description | string | 图表描述 |
| data.labels | array | X轴标签数组，表示时间点 |
| data.datasets | array | 数据集数组 |
| data.datasets[].label | string | 数据集名称 |
| data.datasets[].data | array | 数据集数值数组 |
| data.datasets[].color | string | 数据集颜色（十六进制颜色代码） |
| data.datasets[].yAxisID | string | Y轴ID，用于双Y轴图表（可选） |
| data.summary | object | 汇总数据 |
| data.summary.average_active_users | number | 平均活跃用户数 |
| data.summary.highest_active_day | string | 活跃用户数最高的日期 |
| data.summary.highest_active_count | integer | 最高活跃用户数 |
| data.summary.average_active_rate | number | 平均活跃率（百分比） |

### 响应示例

```json
{
  "code": 2000,
  "message": "success",
  "data": {
    "chart_type": "line",
    "title": "活跃用户统计",
    "description": "按周统计的活跃用户数量",
    "labels": ["2023-W01", "2023-W02", "2023-W03", "2023-W04", "2023-W05", "2023-W06"],
    "datasets": [
      {
        "label": "活跃用户数",
        "data": [45, 52, 49, 60, 55, 58],
        "color": "#FF9800"
      },
      {
        "label": "活跃率",
        "data": [45.0, 52.0, 49.0, 60.0, 55.0, 58.0],
        "color": "#E91E63",
        "yAxisID": "percentage"
      }
    ],
    "summary": {
      "average_active_users": 53.2,
      "highest_active_day": "2023-W04",
      "highest_active_count": 60,
      "average_active_rate": 53.2
    }
  }
}
```

## 前端展示建议

### 图表类型

推荐使用双Y轴折线图：
- 左侧Y轴：活跃用户数（主要指标）
- 右侧Y轴：活跃率（百分比，辅助指标）

### 交互功能

1. **周期选择器**：提供下拉菜单，让用户选择统计周期（日/周/月）
2. **日期范围选择器**：提供日期选择控件，让用户自定义查询时间范围
3. **图例切换**：允许用户点击图例切换显示/隐藏某个数据系列
4. **数据点悬停**：鼠标悬停在数据点上显示详细信息

### 汇总信息展示

在图表下方或旁边展示汇总信息：
- 平均活跃用户数：53.2
- 最高活跃日期：2023-W04
- 最高活跃用户数：60
- 平均活跃率：53.2%

## 注意事项

1. 活跃用户的定义为：在指定时间段内至少有一次API调用的用户
2. 活跃率的计算方式为：活跃用户数 / 该时间段内已注册的总用户数 * 100%
3. 根据选择的周期不同，返回的日期格式也不同：
   - daily: YYYY-MM-DD（如2023-01-01）
   - weekly: YYYY-WXX（如2023-W01表示2023年第1周）
   - monthly: YYYY-MM（如2023-01表示2023年1月）
4. 当查询的时间范围内没有数据时，API会返回空的数据集和相应的提示信息 