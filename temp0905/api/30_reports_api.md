# 报告API

## 概述

报告API提供许可证系统的统计分析和数据报告功能，支持许可证使用情况、激活趋势、收入分析等多维度报告。

**Base URL**: `/api/v1/licenses/reports/`  
**认证要求**: JWT Bearer Token  
**权限要求**: 超级管理员或租户管理员  

## API端点详解

### 1. 获取许可证报告列表

#### 请求
```http
GET /api/v1/licenses/reports/
Authorization: Bearer {access_token}
```

#### 查询参数
| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `report_type` | string | 否 | 报告类型 | `report_type=license_usage` |
| `date_from` | date | 否 | 开始日期 | `date_from=2024-01-01` |
| `date_to` | date | 否 | 结束日期 | `date_to=2024-01-31` |
| `tenant` | integer | 否 | 按租户过滤 | `tenant=1` |
| `product` | integer | 否 | 按产品过滤 | `product=1` |

#### 响应示例
```json
{
    "success": true,
    "data": {
        "reports": [
            {
                "id": 1,
                "report_type": "license_usage",
                "title": "许可证使用情况报告",
                "date_range": {
                    "from": "2024-01-01",
                    "to": "2024-01-31"
                },
                "generated_at": "2024-02-01T09:00:00Z",
                "file_url": "/reports/license_usage_202401.pdf"
            }
        ]
    }
}
```

### 2. 生成报告

#### 请求
```http
POST /api/v1/licenses/reports/generate/
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "report_type": "license_usage",
    "date_from": "2024-01-01",
    "date_to": "2024-01-31",
    "filters": {
        "tenant_id": 1,
        "product_ids": [1, 2, 3]
    },
    "format": "pdf"
}
```

#### 报告类型选项
- `license_usage` - 许可证使用情况
- `activation_trend` - 激活趋势分析  
- `revenue_analysis` - 收入分析
- `customer_analysis` - 客户分析
- `security_audit` - 安全审计报告

#### 响应示例
```json
{
    "success": true,
    "data": {
        "report_id": 15,
        "status": "generating",
        "estimated_completion": "2024-02-01T09:05:00Z",
        "download_url": null
    },
    "message": "报告生成中，请稍后查看"
}
```

### 3. 获取仪表板数据

#### 请求
```http
GET /api/v1/licenses/reports/dashboard/
Authorization: Bearer {access_token}
```

#### 查询参数
| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `period` | string | 否 | 统计周期 | `period=last_30_days` |
| `metrics` | string | 否 | 指标类型 | `metrics=licenses,activations,revenue` |

#### 响应示例
```json
{
    "success": true,
    "data": {
        "period": "last_30_days",
        "overview": {
            "total_licenses": 1250,
            "active_licenses": 980,
            "total_activations": 2150,
            "total_revenue": "125000.00",
            "new_customers": 45
        },
        "trends": {
            "license_growth": [
                {"date": "2024-01-01", "count": 1200},
                {"date": "2024-01-02", "count": 1205},
                {"date": "2024-01-03", "count": 1210}
            ],
            "activation_trend": [
                {"date": "2024-01-01", "count": 25},
                {"date": "2024-01-02", "count": 30},
                {"date": "2024-01-03", "count": 28}
            ]
        },
        "breakdown": {
            "by_product": [
                {
                    "product_name": "MyApplication Pro",
                    "license_count": 450,
                    "revenue": "45000.00"
                },
                {
                    "product_name": "MyApplication Basic",
                    "license_count": 800,
                    "revenue": "32000.00"
                }
            ],
            "by_plan_type": {
                "trial": 120,
                "basic": 400,
                "professional": 520,
                "enterprise": 210
            },
            "by_tenant": [
                {
                    "tenant_name": "示例公司",
                    "license_count": 200,
                    "revenue": "20000.00"
                }
            ]
        },
        "alerts": [
            {
                "type": "high_usage",
                "message": "租户配额使用率超过85%",
                "count": 3
            },
            {
                "type": "expiring_soon",
                "message": "30天内到期的许可证",
                "count": 25
            }
        ]
    }
}
```

### 4. 获取详细统计

#### 许可证统计
```http
GET /api/v1/licenses/reports/dashboard/license_stats/
Authorization: Bearer {access_token}
```

#### 响应示例
```json
{
    "success": true,
    "data": {
        "total_licenses": 1250,
        "by_status": {
            "active": 980,
            "suspended": 50,
            "expired": 180,
            "revoked": 40
        },
        "by_plan_type": {
            "trial": 120,
            "basic": 400,
            "professional": 520,
            "enterprise": 210
        },
        "expiring_soon": {
            "next_7_days": 8,
            "next_30_days": 25,
            "next_90_days": 78
        },
        "utilization": {
            "high_usage": 45,
            "medium_usage": 234,
            "low_usage": 701
        }
    }
}
```

#### 激活统计
```http
GET /api/v1/licenses/reports/dashboard/activation_stats/
Authorization: Bearer {access_token}
```

#### 响应示例
```json
{
    "success": true,
    "data": {
        "total_activations": 2150,
        "successful_activations": 2080,
        "failed_activations": 70,
        "success_rate": 96.74,
        "by_period": {
            "today": 12,
            "yesterday": 18,
            "last_7_days": 156,
            "last_30_days": 650
        },
        "by_type": {
            "online": 1950,
            "offline": 120,
            "automatic": 80
        },
        "top_failure_reasons": [
            {
                "reason": "许可证已过期",
                "count": 25
            },
            {
                "reason": "超过最大激活次数",
                "count": 20
            }
        ]
    }
}
```

#### 收入统计
```http
GET /api/v1/licenses/reports/dashboard/revenue_stats/
Authorization: Bearer {access_token}
```

#### 响应示例
```json
{
    "success": true,
    "data": {
        "total_revenue": "125000.00",
        "currency": "CNY",
        "by_period": {
            "this_month": "15000.00",
            "last_month": "18000.00",
            "this_quarter": "45000.00",
            "this_year": "125000.00"
        },
        "by_product": [
            {
                "product_name": "MyApplication Pro",
                "revenue": "75000.00",
                "percentage": 60.0
            },
            {
                "product_name": "MyApplication Basic",
                "revenue": "50000.00",
                "percentage": 40.0
            }
        ],
        "by_plan_type": {
            "trial": "0.00",
            "basic": "20000.00",
            "professional": "65000.00",
            "enterprise": "40000.00"
        },
        "growth_rate": {
            "month_over_month": 8.5,
            "year_over_year": 25.3
        }
    }
}
```

## 使用示例

### Python示例
```python
class ReportManager:
    def __init__(self, api_client):
        self.api = api_client
    
    def get_dashboard_overview(self, period='last_30_days'):
        return self.api.api_call(f'/reports/dashboard/?period={period}')
    
    def generate_monthly_report(self, year, month, report_type='license_usage'):
        from datetime import date
        
        date_from = date(year, month, 1)
        
        # 计算月末日期
        if month == 12:
            date_to = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            date_to = date(year, month + 1, 1) - timedelta(days=1)
        
        data = {
            'report_type': report_type,
            'date_from': date_from.isoformat(),
            'date_to': date_to.isoformat(),
            'format': 'pdf'
        }
        
        return self.api.api_call('/reports/generate/', method='POST', json=data)
    
    def get_license_health_summary(self):
        dashboard = self.get_dashboard_overview()
        license_stats = self.api.api_call('/reports/dashboard/license_stats/')
        
        total = license_stats['data']['total_licenses']
        active = license_stats['data']['by_status']['active']
        expiring_soon = license_stats['data']['expiring_soon']['next_30_days']
        
        health_score = (active / total * 100) if total > 0 else 0
        
        return {
            'total_licenses': total,
            'active_licenses': active,
            'health_score': round(health_score, 2),
            'expiring_soon': expiring_soon,
            'status': 'healthy' if health_score > 80 else 'warning' if health_score > 60 else 'critical'
        }
    
    def create_executive_summary(self):
        # 获取各种统计数据
        overview = self.get_dashboard_overview()['data']
        license_stats = self.api.api_call('/reports/dashboard/license_stats/')['data']
        activation_stats = self.api.api_call('/reports/dashboard/activation_stats/')['data']
        revenue_stats = self.api.api_call('/reports/dashboard/revenue_stats/')['data']
        
        return {
            'executive_summary': {
                'period': overview['period'],
                'key_metrics': {
                    'total_licenses': overview['overview']['total_licenses'],
                    'activation_success_rate': f"{activation_stats['success_rate']:.1f}%",
                    'total_revenue': revenue_stats['total_revenue'],
                    'revenue_growth': f"{revenue_stats['growth_rate']['month_over_month']:.1f}%"
                },
                'highlights': [
                    f"本期新增客户 {overview['overview']['new_customers']} 个",
                    f"许可证激活成功率达到 {activation_stats['success_rate']:.1f}%",
                    f"收入环比增长 {revenue_stats['growth_rate']['month_over_month']:.1f}%"
                ],
                'concerns': [
                    f"{license_stats['expiring_soon']['next_30_days']} 个许可证将在30天内过期",
                    f"{len(overview['alerts'])} 个系统告警需要关注"
                ]
            }
        }

# 使用示例
report_manager = ReportManager(api_client)

# 获取仪表板数据
dashboard = report_manager.get_dashboard_overview()
print(f"总许可证数: {dashboard['data']['overview']['total_licenses']}")

# 生成月度报告
monthly_report = report_manager.generate_monthly_report(2024, 1, 'license_usage')
print(f"报告生成状态: {monthly_report['data']['status']}")

# 获取许可证健康度摘要
health = report_manager.get_license_health_summary()
print(f"许可证健康度: {health['health_score']}% ({health['status']})")

# 创建高管摘要
executive_summary = report_manager.create_executive_summary()
print("执行摘要:", json.dumps(executive_summary, indent=2, ensure_ascii=False))
```

### JavaScript示例
```javascript
class ReportDashboard {
    constructor(apiClient) {
        this.api = apiClient;
    }
    
    async loadDashboardData(period = 'last_30_days') {
        const [overview, licenseStats, activationStats, revenueStats] = await Promise.all([
            this.api.apiCall(`/reports/dashboard/?period=${period}`),
            this.api.apiCall('/reports/dashboard/license_stats/'),
            this.api.apiCall('/reports/dashboard/activation_stats/'),
            this.api.apiCall('/reports/dashboard/revenue_stats/')
        ]);
        
        return {
            overview: overview.data,
            licenses: licenseStats.data,
            activations: activationStats.data,
            revenue: revenueStats.data
        };
    }
    
    async generateRealtimeMetrics() {
        const data = await this.loadDashboardData('today');
        
        return {
            realtime: {
                activeUsers: data.activations.by_period.today,
                systemHealth: this.calculateSystemHealth(data),
                alerts: data.overview.alerts.length,
                revenue: data.revenue.by_period.this_month
            }
        };
    }
    
    calculateSystemHealth(data) {
        const licenseHealth = (data.licenses.by_status.active / data.licenses.total_licenses) * 100;
        const activationHealth = data.activations.success_rate;
        
        return Math.round((licenseHealth + activationHealth) / 2);
    }
    
    async createChartData() {
        const data = await this.loadDashboardData('last_30_days');
        
        return {
            licenseTrend: {
                labels: data.overview.trends.license_growth.map(item => item.date),
                data: data.overview.trends.license_growth.map(item => item.count)
            },
            activationTrend: {
                labels: data.overview.trends.activation_trend.map(item => item.date),
                data: data.overview.trends.activation_trend.map(item => item.count)
            },
            productBreakdown: {
                labels: data.overview.breakdown.by_product.map(item => item.product_name),
                data: data.overview.breakdown.by_product.map(item => item.license_count)
            },
            planTypeDistribution: data.overview.breakdown.by_plan_type
        };
    }
    
    async generateAutomatedAlert() {
        const data = await this.loadDashboardData();
        const alerts = [];
        
        // 检查许可证到期告警
        if (data.licenses.expiring_soon.next_30_days > 20) {
            alerts.push({
                type: 'warning',
                title: '许可证即将到期',
                message: `${data.licenses.expiring_soon.next_30_days} 个许可证将在30天内到期`
            });
        }
        
        // 检查激活成功率
        if (data.activations.success_rate < 95) {
            alerts.push({
                type: 'error',
                title: '激活成功率下降',
                message: `当前激活成功率为 ${data.activations.success_rate.toFixed(1)}%`
            });
        }
        
        // 检查收入增长
        if (data.revenue.growth_rate.month_over_month < 0) {
            alerts.push({
                type: 'warning',
                title: '收入下降',
                message: `月度收入环比下降 ${Math.abs(data.revenue.growth_rate.month_over_month).toFixed(1)}%`
            });
        }
        
        return alerts;
    }
}

// 使用示例
const dashboard = new ReportDashboard(apiClient);

// 加载仪表板
async function initializeDashboard() {
    const data = await dashboard.loadDashboardData();
    
    // 更新UI组件
    updateOverviewCards(data.overview);
    updateLicenseCharts(data.licenses);
    updateActivationStats(data.activations);
    updateRevenueCharts(data.revenue);
    
    // 检查告警
    const alerts = await dashboard.generateAutomatedAlert();
    displayAlerts(alerts);
}

// 实时数据更新
setInterval(async () => {
    const metrics = await dashboard.generateRealtimeMetrics();
    updateRealtimeMetrics(metrics.realtime);
}, 60000); // 每分钟更新一次

// 图表数据
const chartData = await dashboard.createChartData();
initializeCharts(chartData);
```

## 常见问题

### Q: 报告生成需要多长时间？
A: 取决于数据量和报告复杂度，通常1-5分钟。大型报告可能需要更长时间。

### Q: 支持哪些报告格式？
A: 支持PDF、Excel、CSV格式。PDF适合阅读，Excel适合进一步分析。

### Q: 如何定制报告内容？
A: 通过filters参数可以过滤数据范围，支持按租户、产品、时间等维度定制。

### Q: 报告数据的准确性如何保证？
A: 报告基于实时数据库数据生成，确保数据一致性和准确性。

## 相关API文档
- [许可证管理API](./12_admin_licenses_api.md) - 了解许可证数据结构  
- [激活记录API](./14_admin_activations_api.md) - 了解激活数据来源
- [安全审计日志API](./15_admin_audit_api.md) - 了解安全报告数据
