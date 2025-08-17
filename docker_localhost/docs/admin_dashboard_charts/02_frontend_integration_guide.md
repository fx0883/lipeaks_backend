# 租户图表API前端集成指南

本文档提供了将后端租户图表API集成到前端管理仪表盘的指导。这些API提供系统租户的统计数据，包括租户数量趋势、状态分布和创建速率。

## API概述

系统提供了三个专用于租户图表数据的API端点：

1. **租户数量趋势图**: `/api/v1/admin/charts/tenant-trend/`
2. **租户状态分布**: `/api/v1/admin/charts/tenant-status-distribution/`
3. **租户创建速率**: `/api/v1/admin/charts/tenant-creation-rate/`

所有API都需要JWT认证，且只有超级管理员有权限访问。

## 权限要求

- 用户必须已登录
- 用户必须具有超级管理员(is_super_admin=True)权限

## 集成步骤

### 1. 认证设置

确保API请求中包含有效的JWT令牌：

```javascript
// 使用axios示例
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  }
});
```

### 2. 获取租户数量趋势数据

```javascript
/**
 * 获取租户数量趋势数据
 * @param {string} period - 统计周期：'daily'|'weekly'|'monthly'|'quarterly'|'yearly'
 * @param {string} startDate - 开始日期，格式：YYYY-MM-DD
 * @param {string} endDate - 结束日期，格式：YYYY-MM-DD
 * @returns {Promise} 返回趋势数据
 */
async function fetchTenantTrendData(period = 'monthly', startDate = null, endDate = null) {
  try {
    let url = `/api/v1/admin/charts/tenant-trend/?period=${period}`;
    
    if (startDate) url += `&start_date=${startDate}`;
    if (endDate) url += `&end_date=${endDate}`;
    
    const response = await api.get(url);
    return response.data;
  } catch (error) {
    console.error('获取租户趋势数据失败:', error);
    throw error;
  }
}
```

### 3. 获取租户状态分布数据

```javascript
/**
 * 获取租户状态分布数据
 * @returns {Promise} 返回状态分布数据
 */
async function fetchTenantStatusDistribution() {
  try {
    const response = await api.get('/api/v1/admin/charts/tenant-status-distribution/');
    return response.data;
  } catch (error) {
    console.error('获取租户状态分布数据失败:', error);
    throw error;
  }
}
```

### 4. 获取租户创建速率数据

```javascript
/**
 * 获取租户创建速率数据
 * @param {string} period - 统计周期：'weekly'|'monthly'
 * @param {string} startDate - 开始日期，格式：YYYY-MM-DD
 * @param {string} endDate - 结束日期，格式：YYYY-MM-DD
 * @returns {Promise} 返回创建速率数据
 */
async function fetchTenantCreationRate(period = 'monthly', startDate = null, endDate = null) {
  try {
    let url = `/api/v1/admin/charts/tenant-creation-rate/?period=${period}`;
    
    if (startDate) url += `&start_date=${startDate}`;
    if (endDate) url += `&end_date=${endDate}`;
    
    const response = await api.get(url);
    return response.data;
  } catch (error) {
    console.error('获取租户创建速率数据失败:', error);
    throw error;
  }
}
```

## 数据可视化

### 使用Chart.js渲染图表

以下是使用Chart.js渲染这三种图表的示例代码：

#### 1. 租户数量趋势图 (折线图)

```javascript
import { Line } from 'vue-chartjs';

export default {
  extends: Line,
  data() {
    return {
      chartData: null,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true
          }
        }
      }
    };
  },
  async mounted() {
    const response = await fetchTenantTrendData();
    const data = response.data;
    
    this.chartData = {
      labels: data.labels,
      datasets: [{
        label: data.datasets[0].label,
        data: data.datasets[0].data,
        backgroundColor: 'rgba(51, 102, 204, 0.2)',
        borderColor: data.datasets[0].color || '#3366cc',
        borderWidth: 2,
        tension: 0.3
      }]
    };
    
    this.renderChart(this.chartData, this.options);
  }
};
```

#### 2. 租户状态分布图 (饼图)

```javascript
import { Pie } from 'vue-chartjs';

export default {
  extends: Pie,
  data() {
    return {
      chartData: null,
      options: {
        responsive: true,
        maintainAspectRatio: false
      }
    };
  },
  async mounted() {
    const response = await fetchTenantStatusDistribution();
    const data = response.data;
    
    this.chartData = {
      labels: data.labels,
      datasets: [{
        data: data.datasets[0].data,
        backgroundColor: data.datasets[0].colors || ['#36A2EB', '#FFCE56', '#FF6384']
      }]
    };
    
    this.renderChart(this.chartData, this.options);
  }
};
```

#### 3. 租户创建速率图 (柱状图)

```javascript
import { Bar } from 'vue-chartjs';

export default {
  extends: Bar,
  data() {
    return {
      chartData: null,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true
          }
        }
      }
    };
  },
  async mounted() {
    const response = await fetchTenantCreationRate();
    const data = response.data;
    
    this.chartData = {
      labels: data.labels,
      datasets: [{
        label: data.datasets[0].label,
        data: data.datasets[0].data,
        backgroundColor: data.datasets[0].color || '#4BC0C0'
      }]
    };
    
    this.renderChart(this.chartData, this.options);
  }
};
```

## 仪表盘布局建议

以下是租户统计仪表盘的布局建议：

```html
<template>
  <div class="tenant-dashboard">
    <h1>租户统计仪表盘</h1>
    
    <!-- 日期范围选择器 -->
    <div class="date-filter">
      <date-range-picker @change="handleDateRangeChange" />
      <period-selector @change="handlePeriodChange" />
    </div>
    
    <!-- 租户数量汇总卡片 -->
    <div class="summary-card">
      <div class="stat-item">
        <h3>租户总数</h3>
        <div class="stat-value">{{ summary.total }}</div>
      </div>
      <div class="stat-item">
        <h3>增长率</h3>
        <div class="stat-value">{{ summary.growthRate }}%</div>
      </div>
      <div class="stat-item">
        <h3>平均增长</h3>
        <div class="stat-value">{{ summary.avgGrowth }} / {{ period }}</div>
      </div>
    </div>
    
    <!-- 图表区域 -->
    <div class="charts-container">
      <div class="chart-wrapper">
        <h2>租户数量趋势</h2>
        <tenant-trend-chart :period="period" :startDate="startDate" :endDate="endDate" />
      </div>
      
      <div class="chart-wrapper">
        <h2>租户状态分布</h2>
        <tenant-status-chart />
      </div>
      
      <div class="chart-wrapper">
        <h2>租户创建速率</h2>
        <tenant-creation-chart :period="period" :startDate="startDate" :endDate="endDate" />
      </div>
    </div>
  </div>
</template>
```

## 时间参数说明

### 默认时间范围

- **租户数量趋势图**: 默认显示最近一年(365天)的数据，默认周期为"monthly"
- **租户状态分布**: 显示当前时间点的状态分布，不需要时间参数
- **租户创建速率**: 默认显示最近六个月(180天)的数据，默认周期为"monthly"

### 自定义时间范围

通过添加查询参数可以自定义数据时间范围：

```javascript
// 查询最近一周的每日数据
fetchTenantTrendData('daily', '2025-06-06', '2025-06-13');

// 查询最近三个月的每周新增租户
fetchTenantCreationRate('weekly', '2025-03-13', '2025-06-13');
```

## 刷新策略

建议实施以下数据刷新策略：

1. 页面加载时获取数据
2. 提供手动刷新按钮
3. 实现定时刷新（例如每30分钟）
4. 日期范围或周期变更时重新获取数据

## 错误处理

API可能返回以下错误：

- **401 Unauthorized**: 用户未登录或登录已过期
- **403 Forbidden**: 用户无权访问（非超级管理员）
- **500 Internal Server Error**: 服务器处理错误

建议实现以下错误处理逻辑：

```javascript
try {
  const response = await fetchTenantTrendData();
  // 处理成功响应
} catch (error) {
  if (error.response) {
    switch (error.response.status) {
      case 401:
        // 重定向到登录页面或刷新令牌
        break;
      case 403:
        // 显示权限不足提示
        break;
      case 500:
        // 显示服务器错误提示
        break;
      default:
        // 显示通用错误提示
    }
  } else {
    // 网络错误或请求被取消
  }
}
```

## 最佳实践

1. **实现数据缓存**: 在前端实现缓存机制，避免频繁请求相同数据
2. **加载状态**: 显示加载指示器，提升用户体验
3. **数据导出**: 提供数据导出为CSV或Excel的功能
4. **响应式设计**: 确保图表在不同屏幕尺寸上正确显示
5. **主题支持**: 支持浅色/深色模式下的图表样式

## 浏览器兼容性

以上代码示例兼容现代浏览器，包括：

- Chrome 60+
- Firefox 60+
- Safari 12+
- Edge 79+

对于旧版浏览器，需要添加适当的polyfill。 