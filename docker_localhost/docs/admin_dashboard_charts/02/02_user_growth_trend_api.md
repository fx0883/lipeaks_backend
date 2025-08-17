# 用户总量与增长趋势 API

## 功能描述

此API提供系统内所有用户数量的时间序列数据，包括用户总数和新增用户数的变化趋势。支持按日/周/月/季度/年进行统计，可用于生成折线图或柱状图。

## 请求

### 请求URL

```
GET /api/v1/charts/user-growth-trend/
```

### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| period | string | 否 | monthly | 统计周期，可选值为daily（日）、weekly（周）、monthly（月）、quarterly（季度）、yearly（年） |
| start_date | string | 否 | **当前日期往前一年** | 开始日期，格式为YYYY-MM-DD |
| end_date | string | 否 | **当前日期** | 结束日期，格式为YYYY-MM-DD |

### 请求示例

```
GET /api/v1/charts/user-growth-trend/?period=monthly&start_date=2023-01-01&end_date=2023-12-31
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
| data.summary | object | 汇总数据 |
| data.summary.total_users | integer | 用户总数 |
| data.summary.growth_rate | number | 增长率（百分比） |
| data.summary.average_monthly_growth | number | 平均月增长量 |

### 响应示例

```json
{
  "code": 2000,
  "message": "success",
  "data": {
    "chart_type": "line",
    "title": "用户总量与增长趋势",
    "description": "按月统计的系统内所有用户数量",
    "labels": ["2023-01", "2023-02", "2023-03", "2023-04", "2023-05", "2023-06"],
    "datasets": [
      {
        "label": "用户总数",
        "data": [100, 150, 220, 280, 350, 430],
        "color": "#3366cc"
      },
      {
        "label": "新增用户数",
        "data": [100, 50, 70, 60, 70, 80],
        "color": "#dc3912"
      }
    ],
    "summary": {
      "total_users": 430,
      "growth_rate": 330.0,
      "average_monthly_growth": 66.0
    }
  }
}
```

## 前端展示建议

### 图表类型

推荐使用双Y轴折线图或组合图表（折线图+柱状图）：
- 左侧Y轴：用户总数（折线图）
- 右侧Y轴：新增用户数（柱状图或折线图）

### 交互功能

1. **周期选择器**：提供下拉菜单，让用户选择统计周期（日/周/月/季度/年）
2. **日期范围选择器**：提供日期选择控件，让用户自定义查询时间范围
3. **图例切换**：允许用户点击图例切换显示/隐藏某个数据系列

### 汇总信息展示

在图表下方或旁边展示汇总信息：
- 用户总数：430
- 增长率：330.0%
- 平均月增长：66.0

## 注意事项

1. 当选择较长时间范围时（如按日查询一年数据），返回的数据点可能较多，需要考虑前端图表的性能和可读性
2. 增长率计算方式为：(当前用户总数 - 初始用户数) / 初始用户数 * 100%
3. 平均增长量计算方式为：总增长量 / 时间段数量 