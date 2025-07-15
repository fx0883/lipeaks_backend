# 超级管理员仪表盘图表实现方案

## 概述

本文档提供了为多租户用户管理系统开发超级管理员仪表盘图表的实现方案。这些图表旨在帮助超级管理员全面了解系统运行状况、租户使用情况和关键性能指标。

## 图表分类

本方案涵盖以下几类图表：

1. [租户概览统计](./01_tenant_overview_charts.md)
2. [用户统计分析](./02_user_statistics_charts.md)
3. [API调用分析](./03_api_analysis_charts.md)
4. [系统健康状态](./04_system_health_charts.md)
5. [租户对比分析](./05_tenant_comparison_charts.md)
6. [安全监控](./06_security_monitoring_charts.md)

## 技术架构

### 后端技术栈

- Django REST Framework：提供图表数据API
- Django ORM：数据查询和聚合
- Pandas：数据处理和分析
- 数据缓存：使用Redis缓存计算密集型图表数据

### 前端技术栈

- Chart.js/ECharts：图表渲染
- Vue.js/React：前端框架
- Axios：API调用

## 实现思路

1. **数据源确定**：明确每个图表所需的原始数据来源
2. **API设计**：设计统一的图表数据API接口
3. **数据处理**：实现数据查询、聚合和转换逻辑
4. **缓存策略**：对计算密集型图表数据实施缓存策略
5. **前端实现**：使用适当的图表库渲染可视化图表
6. **权限控制**：确保只有超级管理员可以访问这些图表

## 通用API设计

所有图表数据API将遵循统一的请求和响应格式：

### 请求格式

```
GET /api/v1/admin/charts/{chart_type}/?period={period}&start_date={start_date}&end_date={end_date}&...
```

### 响应格式

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "chart_type": "xxx",
    "title": "xxx",
    "description": "xxx",
    "labels": [...],
    "datasets": [
      {
        "label": "xxx",
        "data": [...],
        "color": "xxx"
      }
    ],
    "summary": {
      "total": xxx,
      "average": xxx,
      "change_rate": xxx
    }
  }
}
```

## 后续文档

请参阅各个子文档，了解每类图表的详细实现方案：

1. [租户概览统计](./01_tenant_overview_charts.md)
2. [用户统计分析](./02_user_statistics_charts.md)
3. [API调用分析](./03_api_analysis_charts.md)
4. [系统健康状态](./04_system_health_charts.md)
5. [租户对比分析](./05_tenant_comparison_charts.md)
6. [安全监控](./06_security_monitoring_charts.md)

## 会话总结

### 本次会话的主要目标
完成超级管理员仪表盘图表实现方案的安全监控图表文档，添加实现步骤和注意事项部分。

### 已完成的具体任务
- 为安全监控图表文档(06_security_monitoring_charts.md)添加了详细的实现步骤
- 添加了三个主要图表的实现代码：异常登录尝试、权限变更审计和敏感操作日志
- 为每个图表提供了数据查询与处理、API实现和前端实现的代码示例
- 添加了全面的注意事项，包括数据安全与隐私、性能优化、告警机制和可扩展性

### 采用的技术方案及决策理由
- 使用Django ORM进行数据查询和聚合：充分利用现有技术栈，提高查询效率
- 采用React-Leaflet实现地理位置热图：提供直观的异常登录地理分布可视化
- 使用Chart.js实现各类统计图表：轻量级且功能强大的图表库，易于集成
- 实现数据缓存策略：减轻服务器负担，提高图表加载速度
- 设计告警机制：及时发现并响应安全威胁

### 使用的主要技术栈
- 后端：Django REST Framework、Django ORM、缓存机制
- 前端：React、Chart.js、React-Leaflet
- 数据处理：Pandas、Django ORM聚合函数
- 安全机制：权限控制、数据脱敏、HTTPS传输

### 变更的文件清单
- docs/admin_dashboard_charts/06_security_monitoring_charts.md：添加了实现步骤和注意事项部分
- docs/admin_dashboard_charts/README.md：更新了会话总结 