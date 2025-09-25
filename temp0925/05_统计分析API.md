# 统计分析API - 详细文档

## 📋 目录

- [统计分析概述](#统计分析概述)
- [积分统计API](#积分统计api)
- [趋势分析API](#趋势分析api)
- [用户行为分析](#用户行为分析)
- [业务指标监控](#业务指标监控)
- [数据可视化](#数据可视化)
- [使用示例](#使用示例)

---

## 📊 统计分析概述

### 统计分析系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    数据分析处理流程                         │
├─────────────────────────────────────────────────────────────┤
│ 数据收集 → 数据清洗 → 数据分析 → 指标计算 → 可视化 → 报告生成 │
│     ↓         ↓         ↓         ↓         ↓         ↓     │
│  实时数据   去重过滤   算法处理   KPI计算   图表生成  定期报告 │
│  批量导入   格式化     统计分析   趋势计算   仪表板    业务洞察│
└─────────────────────────────────────────────────────────────┘
```

### 分析维度

| 维度 | 描述 | 指标示例 |
|------|------|----------|
| **时间维度** | 按时间周期分析 | 日活、月活、增长率 |
| **用户维度** | 按用户群体分析 | 用户等级分布、活跃度 |
| **业务维度** | 按业务类型分析 | 积分流转、VIP转化 |
| **地域维度** | 按地理位置分析 | 区域分布、时区分析 |
| **设备维度** | 按设备类型分析 | 移动端、桌面端使用 |

### 数据刷新策略

| 数据类型 | 刷新频率 | 说明 |
|----------|----------|------|
| **实时数据** | 每分钟 | 当前在线用户、实时积分 |
| **小时数据** | 每小时 | 使用量统计、活跃度 |
| **日数据** | 每日凌晨 | 日活、积分流水 |
| **周/月数据** | 定期计算 | 趋势分析、同比环比 |

---

## 📈 积分统计API

### 获取积分统计概览

**端点**: `GET /api/v1/points/statistics/`

**描述**: 获取当前租户的积分系统统计概览

#### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `period` | string | 否 | `month` | 统计周期（day/week/month/year） |
| `start_date` | date | 否 | - | 开始日期 |
| `end_date` | date | 否 | - | 结束日期 |

#### 请求示例

```bash
curl -X GET \
  "http://localhost:8000/api/v1/points/statistics/?period=month" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

#### 响应示例

```json
{
  "period": "month",
  "period_start": "2025-09-01",
  "period_end": "2025-09-30",
  "last_updated": "2025-09-25T16:00:00Z",
  
  "user_statistics": {
    "total_users": 1250,
    "active_users": 980,
    "new_users_this_period": 85,
    "points_enabled_users": 950,
    "activation_rate": 0.76
  },
  
  "points_overview": {
    "total_points_distributed": 1500000,
    "total_points_spent": 450000,
    "net_points_in_circulation": 1050000,
    "average_points_per_user": 1200,
    "median_points_per_user": 800
  },
  
  "level_distribution": {
    "青铜会员": {
      "count": 500,
      "percentage": 40.0,
      "avg_points": 350
    },
    "白银会员": {
      "count": 400,
      "percentage": 32.0,
      "avg_points": 2500
    },
    "黄金会员": {
      "count": 250,
      "percentage": 20.0,
      "avg_points": 6500
    },
    "钻石会员": {
      "count": 80,
      "percentage": 6.4,
      "avg_points": 15000
    },
    "至尊会员": {
      "count": 20,
      "percentage": 1.6,
      "avg_points": 35000
    }
  },
  
  "vip_distribution": {
    "vip": {
      "total_active": 180,
      "percentage": 14.4,
      "revenue_contribution": 0.65
    },
    "privilege": {
      "total_active": 50,
      "percentage": 4.0,
      "revenue_contribution": 0.15
    },
    "temporary": {
      "total_active": 120,
      "percentage": 9.6,
      "revenue_contribution": 0.05
    }
  },
  
  "activity_metrics": {
    "daily_active_users": 650,
    "weekly_active_users": 850,
    "monthly_active_users": 980,
    "user_retention": {
      "day_1": 0.85,
      "day_7": 0.65,
      "day_30": 0.45
    },
    "session_statistics": {
      "avg_session_duration": "00:25:30",
      "avg_sessions_per_user": 8.5,
      "peak_hours": ["14:00", "20:00", "21:00"]
    }
  },
  
  "business_metrics": {
    "points_conversion_rate": 0.25,
    "vip_conversion_rate": 0.12,
    "average_revenue_per_user": 45.50,
    "customer_lifetime_value": 285.60
  },
  
  "growth_indicators": {
    "user_growth_rate": 0.07,
    "points_growth_rate": 0.15,
    "revenue_growth_rate": 0.22,
    "engagement_score": 8.5
  }
}
```

---

## 📊 趋势分析API

### 获取积分趋势数据

**端点**: `GET /api/v1/points/statistics/points_trend/`

**描述**: 获取积分流转的趋势分析数据

#### 请求参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `days` | integer | 否 | 30 | 分析天数（7-365） |
| `granularity` | string | 否 | `day` | 时间粒度（hour/day/week） |
| `metrics` | array | 否 | all | 指定指标类型 |

#### 指标类型

| 指标 | 代码 | 说明 |
|------|------|------|
| 积分获得 | `earned` | 用户获得的积分 |
| 积分消费 | `spent` | 用户消费的积分 |
| 积分过期 | `expired` | 过期失效的积分 |
| 净变化 | `net_change` | 积分净增减 |
| 活跃用户 | `active_users` | 积分活跃用户数 |

#### 请求示例

```bash
curl -X GET \
  "http://localhost:8000/api/v1/points/statistics/points_trend/?days=30&granularity=day" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### 响应示例

```json
{
  "period_days": 30,
  "granularity": "day",
  "start_date": "2025-08-26",
  "end_date": "2025-09-25",
  "last_updated": "2025-09-25T16:00:00Z",
  
  "summary_metrics": {
    "total_earned": 450000,
    "total_spent": 135000,
    "total_expired": 5000,
    "net_change": 310000,
    "avg_daily_earned": 15000,
    "avg_daily_spent": 4500,
    "peak_day": "2025-09-15",
    "peak_value": 25000
  },
  
  "daily_stats": [
    {
      "date": "2025-09-25",
      "earned": 18500,
      "spent": 5200,
      "expired": 150,
      "net": 13150,
      "active_users": 650,
      "transactions": 1250,
      "categories": {
        "login": 3500,
        "license": 8500,
        "referral": 2500,
        "vip_upgrade": -5200,
        "manual": 4000
      }
    },
    {
      "date": "2025-09-24",
      "earned": 16200,
      "spent": 4800,
      "expired": 200,
      "net": 11200,
      "active_users": 620,
      "transactions": 1180,
      "categories": {
        "login": 3200,
        "license": 7500,
        "referral": 2000,
        "vip_upgrade": -4800,
        "manual": 3500
      }
    }
  ],
  
  "trend_analysis": {
    "growth_rate": 0.08,
    "volatility": 0.15,
    "seasonality": {
      "weekdays_avg": 14500,
      "weekends_avg": 12000,
      "peak_hours": ["10:00", "14:00", "20:00"]
    },
    "predictions": {
      "next_7_days_forecast": 105000,
      "confidence_interval": [95000, 115000],
      "trend_direction": "increasing"
    }
  },
  
  "category_breakdown": {
    "login": {
      "total": 98000,
      "percentage": 21.8,
      "trend": "stable",
      "daily_avg": 3267
    },
    "license": {
      "total": 225000,
      "percentage": 50.0,
      "trend": "increasing",
      "daily_avg": 7500
    },
    "referral": {
      "total": 67500,
      "percentage": 15.0,
      "trend": "fluctuating",
      "daily_avg": 2250
    },
    "manual": {
      "total": 59500,
      "percentage": 13.2,
      "trend": "decreasing",
      "daily_avg": 1983
    }
  }
}
```

---

## 👥 用户行为分析

### 用户等级流转分析

**端点**: `GET /api/v1/points/statistics/level_transitions/`

**描述**: 分析用户等级变化和流转情况

#### 响应示例

```json
{
  "analysis_period": {
    "start_date": "2025-08-01",
    "end_date": "2025-09-25",
    "total_days": 55
  },
  
  "level_transition_matrix": {
    "青铜会员": {
      "retained": 450,
      "upgraded_to": {
        "白银会员": 45,
        "黄金会员": 3
      },
      "downgraded_to": {},
      "retention_rate": 0.90
    },
    "白银会员": {
      "retained": 350,
      "upgraded_to": {
        "黄金会员": 35,
        "钻石会员": 2
      },
      "downgraded_to": {
        "青铜会员": 13
      },
      "retention_rate": 0.875
    },
    "黄金会员": {
      "retained": 220,
      "upgraded_to": {
        "钻石会员": 18,
        "至尊会员": 1
      },
      "downgraded_to": {
        "白银会员": 11
      },
      "retention_rate": 0.88
    }
  },
  
  "upgrade_paths": [
    {
      "path": "青铜会员 → 白银会员",
      "count": 45,
      "avg_time_days": 28,
      "avg_points_needed": 1000,
      "success_rate": 0.09
    },
    {
      "path": "白银会员 → 黄金会员",
      "count": 35,
      "avg_time_days": 45,
      "avg_points_needed": 3000,
      "success_rate": 0.088
    }
  ],
  
  "user_journey_analysis": {
    "new_user_progression": {
      "stay_at_bronze_30_days": 0.75,
      "reach_silver_30_days": 0.20,
      "reach_gold_30_days": 0.04,
      "reach_diamond_30_days": 0.01
    },
    "churn_analysis": {
      "bronze_churn_rate": 0.25,
      "silver_churn_rate": 0.15,
      "gold_churn_rate": 0.08,
      "diamond_churn_rate": 0.05
    },
    "engagement_by_level": {
      "青铜会员": {
        "daily_login_rate": 0.35,
        "feature_usage_rate": 0.45,
        "support_ticket_rate": 0.08
      },
      "黄金会员": {
        "daily_login_rate": 0.75,
        "feature_usage_rate": 0.85,
        "support_ticket_rate": 0.15
      }
    }
  }
}
```

### VIP转化分析

**端点**: `GET /api/v1/points/statistics/vip_conversion/`

**描述**: 分析VIP转化漏斗和用户行为

#### 响应示例

```json
{
  "conversion_funnel": {
    "total_users": 1250,
    "viewed_vip_page": {
      "count": 625,
      "rate": 0.50
    },
    "started_purchase": {
      "count": 250,
      "rate": 0.40
    },
    "completed_payment": {
      "count": 180,
      "rate": 0.72
    },
    "activated_vip": {
      "count": 175,
      "rate": 0.97
    }
  },
  
  "vip_tier_preference": {
    "VIP_BRONZE": {
      "purchases": 50,
      "percentage": 28.6,
      "avg_duration_days": 30,
      "renewal_rate": 0.65
    },
    "VIP_SILVER": {
      "purchases": 80,
      "percentage": 45.7,
      "avg_duration_days": 60,
      "renewal_rate": 0.75
    },
    "VIP_GOLD": {
      "purchases": 45,
      "percentage": 25.7,
      "avg_duration_days": 90,
      "renewal_rate": 0.85
    }
  },
  
  "conversion_drivers": {
    "top_motivations": [
      {
        "reason": "优先技术支持",
        "impact_score": 8.5,
        "user_mentions": 125
      },
      {
        "reason": "独家功能访问",
        "impact_score": 8.2,
        "user_mentions": 98
      },
      {
        "reason": "折扣优惠",
        "impact_score": 7.8,
        "user_mentions": 156
      }
    ],
    "conversion_triggers": [
      {
        "trigger": "积分达到阈值",
        "conversion_rate": 0.35,
        "optimal_timing": "积分达到2000+"
      },
      {
        "trigger": "许可证即将到期",
        "conversion_rate": 0.28,
        "optimal_timing": "到期前7天"
      }
    ]
  },
  
  "churn_analysis": {
    "vip_churn_rate": 0.15,
    "churn_reasons": [
      {
        "reason": "价格因素",
        "percentage": 35.0
      },
      {
        "reason": "功能使用频率低",
        "percentage": 28.0
      },
      {
        "reason": "替代方案",
        "percentage": 20.0
      },
      {
        "reason": "其他",
        "percentage": 17.0
      }
    ],
    "retention_strategies": [
      {
        "strategy": "个性化折扣",
        "effectiveness": 0.45
      },
      {
        "strategy": "功能使用指导",
        "effectiveness": 0.38
      }
    ]
  }
}
```

---

## 🎯 业务指标监控

### 关键业务指标

**端点**: `GET /api/v1/points/statistics/kpi_dashboard/`

**描述**: 获取关键业务指标仪表板数据

#### 响应示例

```json
{
  "dashboard_metrics": {
    "revenue_metrics": {
      "total_revenue": 125000.00,
      "monthly_recurring_revenue": 45000.00,
      "average_revenue_per_user": 100.00,
      "revenue_growth_rate": 0.18,
      "revenue_per_vip_user": 250.00
    },
    
    "user_metrics": {
      "total_active_users": 980,
      "new_user_acquisition": 85,
      "user_acquisition_cost": 25.50,
      "customer_lifetime_value": 285.60,
      "net_promoter_score": 7.8
    },
    
    "engagement_metrics": {
      "daily_active_users": 650,
      "session_duration_avg": "00:25:30",
      "feature_adoption_rate": 0.68,
      "user_engagement_score": 8.2,
      "content_interaction_rate": 0.45
    },
    
    "operational_metrics": {
      "system_uptime": 0.998,
      "api_response_time_avg": 185,
      "error_rate": 0.002,
      "support_ticket_resolution_time": "4.5 hours",
      "customer_satisfaction_score": 8.7
    }
  },
  
  "performance_alerts": [
    {
      "metric": "api_response_time",
      "current_value": 250,
      "threshold": 200,
      "severity": "warning",
      "trend": "increasing"
    }
  ],
  
  "goal_tracking": {
    "monthly_revenue_goal": {
      "target": 50000.00,
      "current": 45000.00,
      "progress": 0.90,
      "days_remaining": 6
    },
    "user_acquisition_goal": {
      "target": 100,
      "current": 85,
      "progress": 0.85,
      "days_remaining": 6
    }
  }
}
```

### 许可证使用分析

**端点**: `GET /api/v1/licenses/admin/assignments/analytics/`

**描述**: 分析许可证使用情况和效率

#### 响应示例

```json
{
  "license_efficiency": {
    "total_licenses": 200,
    "assigned_licenses": 150,
    "active_licenses": 120,
    "utilization_rate": 0.60,
    "efficiency_score": 8.0
  },
  
  "usage_patterns": {
    "peak_usage_hours": {
      "weekday": ["09:00", "14:00", "16:00"],
      "weekend": ["10:00", "20:00"]
    },
    "seasonal_trends": {
      "q1_usage": 0.85,
      "q2_usage": 0.92,
      "q3_usage": 0.88,
      "q4_usage": 0.95
    },
    "geographic_distribution": {
      "asia_pacific": 0.45,
      "north_america": 0.35,
      "europe": 0.15,
      "others": 0.05
    }
  },
  
  "cost_optimization": {
    "license_cost_per_user": 150.00,
    "roi_analysis": {
      "productivity_gain": 0.25,
      "cost_savings": 25000.00,
      "payback_period_months": 8.5
    },
    "optimization_recommendations": [
      {
        "action": "回收未使用许可证",
        "potential_savings": 4500.00,
        "impact": "低风险"
      },
      {
        "action": "升级高频用户许可证",
        "potential_revenue": 8000.00,
        "impact": "中等收益"
      }
    ]
  }
}
```

---

## 📈 数据可视化

### 图表数据接口

**端点**: `GET /api/v1/points/statistics/chart_data/`

**描述**: 获取用于前端图表展示的格式化数据

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `chart_type` | string | 是 | 图表类型 |
| `period` | string | 否 | 时间周期 |
| `dimensions` | array | 否 | 数据维度 |

#### 图表类型

| 类型 | 代码 | 说明 |
|------|------|------|
| 线图 | `line` | 趋势分析 |
| 柱状图 | `bar` | 对比分析 |
| 饼图 | `pie` | 占比分析 |
| 散点图 | `scatter` | 相关性分析 |
| 热力图 | `heatmap` | 密度分析 |

#### 请求示例

```bash
curl -X GET \
  "http://localhost:8000/api/v1/points/statistics/chart_data/?chart_type=line&period=month" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### 响应示例（线图数据）

```json
{
  "chart_type": "line",
  "title": "积分趋势分析",
  "subtitle": "最近30天积分获得和消费趋势",
  "xAxis": {
    "type": "datetime",
    "categories": [
      "2025-08-26", "2025-08-27", "2025-08-28"
    ]
  },
  "yAxis": {
    "title": "积分数量",
    "unit": "分"
  },
  "series": [
    {
      "name": "积分获得",
      "type": "line",
      "color": "#4CAF50",
      "data": [
        {"x": "2025-08-26", "y": 15000},
        {"x": "2025-08-27", "y": 16500},
        {"x": "2025-08-28", "y": 14800}
      ]
    },
    {
      "name": "积分消费",
      "type": "line",
      "color": "#F44336",
      "data": [
        {"x": "2025-08-26", "y": 4500},
        {"x": "2025-08-27", "y": 5200},
        {"x": "2025-08-28", "y": 4800}
      ]
    }
  ],
  "annotations": [
    {
      "x": "2025-09-15",
      "y": 25000,
      "text": "活动推广高峰",
      "type": "point"
    }
  ]
}
```

#### 响应示例（饼图数据）

```json
{
  "chart_type": "pie",
  "title": "用户等级分布",
  "subtitle": "当前用户等级构成比例",
  "series": [
    {
      "name": "用户等级",
      "data": [
        {
          "name": "青铜会员",
          "y": 40.0,
          "color": "#CD7F32",
          "count": 500
        },
        {
          "name": "白银会员", 
          "y": 32.0,
          "color": "#C0C0C0",
          "count": 400
        },
        {
          "name": "黄金会员",
          "y": 20.0,
          "color": "#FFD700", 
          "count": 250
        },
        {
          "name": "钻石会员",
          "y": 6.4,
          "color": "#B9F2FF",
          "count": 80
        },
        {
          "name": "至尊会员",
          "y": 1.6,
          "color": "#E6E6FA",
          "count": 20
        }
      ]
    }
  ],
  "legend": {
    "enabled": true,
    "position": "right"
  }
}
```

---

## 💡 使用示例

### 完整的数据分析流程

#### 1. 获取概览数据

```bash
# 获取当月积分系统概览
curl -X GET \
  "http://localhost:8000/api/v1/points/statistics/?period=month" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### 2. 分析积分趋势

```bash
# 获取最近30天的积分趋势
curl -X GET \
  "http://localhost:8000/api/v1/points/statistics/points_trend/?days=30&granularity=day" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### 3. 用户行为分析

```bash
# 分析用户等级流转情况
curl -X GET \
  "http://localhost:8000/api/v1/points/statistics/level_transitions/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 分析VIP转化情况
curl -X GET \
  "http://localhost:8000/api/v1/points/statistics/vip_conversion/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### 4. 业务指标监控

```bash
# 获取KPI仪表板数据
curl -X GET \
  "http://localhost:8000/api/v1/points/statistics/kpi_dashboard/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 分析许可证使用效率
curl -X GET \
  "http://localhost:8000/api/v1/licenses/admin/assignments/analytics/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### 5. 数据可视化

```bash
# 获取线图数据
curl -X GET \
  "http://localhost:8000/api/v1/points/statistics/chart_data/?chart_type=line&period=month" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 获取饼图数据
curl -X GET \
  "http://localhost:8000/api/v1/points/statistics/chart_data/?chart_type=pie&dimensions=user_level" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 前端集成示例

#### React组件示例

```javascript
// 积分趋势图表组件
import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

const PointsTrendChart = () => {
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchTrendData();
  }, []);

  const fetchTrendData = async () => {
    try {
      const response = await fetch('/api/v1/points/statistics/points_trend/?days=30', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json'
        }
      });
      const data = await response.json();
      setChartData(data.daily_stats);
    } catch (error) {
      console.error('获取趋势数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>加载中...</div>;

  return (
    <div className="chart-container">
      <h3>积分趋势分析</h3>
      <LineChart width={800} height={400} data={chartData}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="earned" stroke="#4CAF50" name="获得积分" />
        <Line type="monotone" dataKey="spent" stroke="#F44336" name="消费积分" />
        <Line type="monotone" dataKey="net" stroke="#2196F3" name="净变化" />
      </LineChart>
    </div>
  );
};

export default PointsTrendChart;
```

#### Vue组件示例

```vue
<template>
  <div class="statistics-dashboard">
    <div class="kpi-cards">
      <div class="kpi-card" v-for="kpi in kpiData" :key="kpi.name">
        <h4>{{ kpi.name }}</h4>
        <div class="kpi-value">{{ kpi.value }}</div>
        <div class="kpi-change" :class="kpi.trend">
          {{ kpi.change }}
        </div>
      </div>
    </div>
    
    <div class="charts-grid">
      <div class="chart-item">
        <pie-chart :data="levelDistribution" title="用户等级分布" />
      </div>
      <div class="chart-item">
        <line-chart :data="pointsTrend" title="积分趋势" />
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue';
import PieChart from './components/PieChart.vue';
import LineChart from './components/LineChart.vue';

export default {
  name: 'StatisticsDashboard',
  components: {
    PieChart,
    LineChart
  },
  setup() {
    const kpiData = ref([]);
    const levelDistribution = ref([]);
    const pointsTrend = ref([]);

    const fetchDashboardData = async () => {
      try {
        // 获取KPI数据
        const kpiResponse = await fetch('/api/v1/points/statistics/kpi_dashboard/');
        const kpi = await kpiResponse.json();
        
        kpiData.value = [
          {
            name: '总收入',
            value: `¥${kpi.dashboard_metrics.revenue_metrics.total_revenue}`,
            change: '+18%',
            trend: 'positive'
          },
          {
            name: '活跃用户',
            value: kpi.dashboard_metrics.user_metrics.total_active_users,
            change: '+7%',
            trend: 'positive'
          },
          {
            name: '参与度评分',
            value: kpi.dashboard_metrics.engagement_metrics.user_engagement_score,
            change: '+0.3',
            trend: 'positive'
          }
        ];

        // 获取图表数据
        const chartResponse = await fetch('/api/v1/points/statistics/chart_data/?chart_type=pie');
        const chartData = await chartResponse.json();
        levelDistribution.value = chartData.series[0].data;

        const trendResponse = await fetch('/api/v1/points/statistics/points_trend/?days=7');
        const trendData = await trendResponse.json();
        pointsTrend.value = trendData.daily_stats;

      } catch (error) {
        console.error('获取仪表板数据失败:', error);
      }
    };

    onMounted(fetchDashboardData);

    return {
      kpiData,
      levelDistribution,
      pointsTrend
    };
  }
};
</script>
```

---

## 📊 数据导出

### 导出统计报告

**端点**: `GET /api/v1/points/statistics/export/`

**描述**: 导出详细的统计分析报告

#### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `format` | string | 否 | 导出格式（excel/csv/pdf） |
| `period` | string | 否 | 统计周期 |
| `sections` | array | 否 | 报告章节 |

#### 请求示例

```bash
curl -X GET \
  "http://localhost:8000/api/v1/points/statistics/export/?format=excel&period=month" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -o "points_statistics_report.xlsx"
```

---

## ⚠️ 性能优化

### 大数据量处理

1. **数据分页**: 大数据集使用分页避免超时
2. **缓存策略**: 热点数据使用Redis缓存
3. **异步处理**: 复杂统计使用后台任务
4. **索引优化**: 查询字段建立合适索引

### 实时数据处理

1. **增量更新**: 只处理变化的数据
2. **预聚合**: 预先计算常用指标
3. **数据压缩**: 历史数据适当压缩存储
4. **批量处理**: 批量处理减少数据库连接

---

下一步查看: [06_用户场景和用例.md](./06_用户场景和用例.md) 了解详细的业务场景和实际使用案例。
