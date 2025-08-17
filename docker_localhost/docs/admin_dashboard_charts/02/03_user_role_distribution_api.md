# 用户角色分布 API

## 功能描述

此API提供系统内用户按角色分类的分布数据，包括超级管理员、租户管理员和普通用户的数量及比例。适用于生成饼图或环形图，帮助管理员了解系统内不同角色用户的分布情况。

## 请求

### 请求URL

```
GET /api/v1/charts/user-role-distribution/
```

### 请求参数

此API不需要任何请求参数，直接获取当前系统内的用户角色分布情况。

### 请求示例

```
GET /api/v1/charts/user-role-distribution/
```

## 响应

### 响应参数

| 参数 | 类型 | 说明 |
|------|------|------|
| code | integer | 响应码，2000表示成功 |
| message | string | 响应消息 |
| data | object | 响应数据 |
| data.chart_type | string | 图表类型，固定为"pie" |
| data.title | string | 图表标题 |
| data.description | string | 图表描述 |
| data.labels | array | 角色名称数组 |
| data.datasets | array | 数据集数组 |
| data.datasets[].data | array | 各角色用户数量数组 |
| data.datasets[].colors | array | 各角色对应的颜色数组（十六进制颜色代码） |
| data.summary | object | 汇总数据 |
| data.summary.total_users | integer | 用户总数 |
| data.summary.super_admin_percentage | number | 超级管理员占比（百分比） |
| data.summary.tenant_admin_percentage | number | 租户管理员占比（百分比） |
| data.summary.regular_user_percentage | number | 普通用户占比（百分比） |

### 响应示例

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

## 前端展示建议

### 图表类型

推荐使用以下图表类型：
- 饼图：展示各角色用户数量的比例关系
- 环形图：与饼图类似，但中间可以显示总用户数
- 条形图：当需要更精确地比较各角色用户数量时

### 交互功能

1. **图例交互**：点击图例可以隐藏/显示对应的数据系列
2. **悬停提示**：鼠标悬停在图表区域显示详细信息（角色名称、用户数量、百分比）
3. **点击下钻**：可选功能，点击某个角色扇区可以查看该角色用户的更多详细信息

### 汇总信息展示

在图表旁边展示汇总信息：
- 总用户数：100
- 超级管理员：5人（5.0%）
- 租户管理员：25人（25.0%）
- 普通用户：70人（70.0%）

## 注意事项

1. 此API不需要时间参数，始终返回当前系统状态
2. 角色分类是互斥的，每个用户只属于一个角色类别
3. 百分比数值已经计算好，可以直接使用，无需前端再次计算
4. 建议使用API提供的颜色方案，以保持整个系统的视觉一致性 