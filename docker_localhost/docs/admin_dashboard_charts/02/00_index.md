# 用户统计图表API集成文档

## 文档目录

本文档集提供了用户统计图表API的详细集成指南，帮助前端开发人员将这些图表集成到Vue3管理员仪表盘中。

### 基础文档

1. [API概览](./01_api_overview.md) - 提供所有API的通用信息、认证要求、错误处理等基础内容

### API详细文档

2. [用户总量与增长趋势API](./02_user_growth_trend_api.md) - 获取系统内所有用户数量的时间序列数据，包括用户总数和新增用户数的变化趋势
3. [用户角色分布API](./03_user_role_distribution_api.md) - 获取系统内用户按角色分类的分布数据，包括超级管理员、租户管理员和普通用户的数量及比例
4. [活跃用户统计API](./04_active_users_api.md) - 获取按日/周/月统计的活跃用户数量和活跃率数据
5. [用户登录热力图API](./05_login_heatmap_api.md) - 获取用户登录情况的热力图数据，按星期几和小时统计登录次数

### 最佳实践

6. [集成最佳实践](./06_integration_best_practices.md) - 提供API调用、错误处理、缓存策略、性能优化等方面的建议

## 快速入门

### 1. 准备工作

确保您已经：

- 拥有超级管理员权限
- 获取了有效的JWT认证令牌
- 在您的Vue3项目中安装了适当的图表库（如ECharts、Chart.js等）

### 2. API调用基础

所有API都使用相同的基本调用模式：

```javascript
// 示例代码
async function fetchChartData(apiEndpoint, params = {}) {
  const response = await fetch(`/api/v1/charts/${apiEndpoint}`, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  return await response.json();
}
```

### 3. 常见问题

**Q: API返回空数据怎么办？**

A: 检查您的时间范围参数是否合理，尝试扩大时间范围或使用默认时间范围。

**Q: 如何处理大量数据点？**

A: 参考[集成最佳实践](./06_integration_best_practices.md)中的数据聚合建议。

**Q: 图表在移动设备上显示不正确怎么办？**

A: 确保您实现了响应式设计，参考最佳实践文档中的相关建议。

## 后续更新

本文档集将根据API的更新和前端需求的变化进行定期更新。如有问题或建议，请联系后端开发团队。 