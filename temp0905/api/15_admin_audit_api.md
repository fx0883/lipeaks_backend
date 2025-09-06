# 安全审计日志API

## 概述

安全审计日志API提供系统安全事件的查看和分析功能，用于监控系统安全状态和异常行为追踪。

**Base URL**: `/api/v1/licenses/admin/audit-logs/`  
**认证要求**: JWT Bearer Token  
**权限要求**: 超级管理员或租户管理员  
**访问权限**: 只读

## 数据模型

### SecurityAuditLog 字段详解

| 字段名 | 类型 | 必填 | 说明 | 生成方式 |
|--------|------|------|------|----------|
| `id` | integer | 只读 | 日志记录唯一标识符 | 数据库自动生成 |
| `tenant` | integer | 可空 | 关联租户ID | 租户级事件时设置 |
| `event_type` | string(50) | 是 | 事件类型 | 系统自动设置 |
| `severity` | string(20) | 是 | 严重程度 | 根据事件类型设置 |
| `description` | text | 是 | 事件描述 | 自动生成 |
| `user_id` | integer | 可空 | 操作用户ID | 有用户操作时设置 |
| `ip_address` | string(45) | 可空 | 操作IP地址 | 请求时获取 |
| `user_agent` | string(500) | 可空 | 用户代理信息 | 请求头获取 |
| `license_id` | integer | 可空 | 关联许可证ID | 许可证相关事件时设置 |
| `machine_fingerprint` | string(64) | 可空 | 机器指纹 | 设备相关事件时设置 |
| `metadata` | JSON | 可空 | 附加元数据 | 事件详细信息 |
| `timestamp` | datetime | 只读 | 事件时间戳 | 事件发生时自动设置 |
| `created_at` | datetime | 只读 | 创建时间 | 自动设置 |

### 枚举值说明

#### event_type可选值:
**认证相关**:
- `LOGIN_SUCCESS` - 登录成功
- `LOGIN_FAILED` - 登录失败
- `LOGOUT` - 用户登出
- `TOKEN_EXPIRED` - Token过期
- `UNAUTHORIZED_ACCESS` - 未授权访问

**许可证相关**:
- `LICENSE_CREATED` - 许可证创建
- `LICENSE_ACTIVATED` - 许可证激活
- `LICENSE_SUSPENDED` - 许可证挂起
- `LICENSE_REVOKED` - 许可证撤销
- `LICENSE_EXPIRED` - 许可证过期

**设备相关**:
- `MACHINE_BOUND` - 设备绑定
- `MACHINE_UNBOUND` - 设备解绑
- `MACHINE_BLOCKED` - 设备被阻止
- `SUSPICIOUS_ACTIVITY` - 可疑活动

**系统相关**:
- `KEYPAIR_REGENERATED` - 密钥对重新生成
- `CONFIGURATION_CHANGED` - 配置变更
- `DATA_EXPORT` - 数据导出
- `BULK_OPERATION` - 批量操作

#### severity可选值:
- `low` - 低：信息性事件
- `medium` - 中：需要关注的事件
- `high` - 高：重要安全事件
- `critical` - 严重：需要立即处理的事件

## API端点详解

### 1. 获取审计日志列表

#### 请求
```http
GET /api/v1/licenses/admin/audit-logs/
Authorization: Bearer {access_token}
```

#### 查询参数
| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `page` | integer | 否 | 页码 | `page=2` |
| `page_size` | integer | 否 | 每页条数 | `page_size=20` |
| `search` | string | 否 | 搜索描述、IP地址 | `search=192.168.1` |
| `event_type` | string | 否 | 按事件类型过滤 | `event_type=LOGIN_FAILED` |
| `severity` | string | 否 | 按严重程度过滤 | `severity=high` |
| `user_id` | integer | 否 | 按用户过滤 | `user_id=1` |
| `license_id` | integer | 否 | 按许可证过滤 | `license_id=1` |
| `ip_address` | string | 否 | 按IP地址过滤 | `ip_address=192.168.1.100` |
| `timestamp_after` | datetime | 否 | 时间晚于 | `timestamp_after=2024-01-01T00:00:00Z` |
| `timestamp_before` | datetime | 否 | 时间早于 | `timestamp_before=2024-12-31T23:59:59Z` |
| `ordering` | string | 否 | 排序字段 | `ordering=-timestamp` |

#### 响应示例
```json
{
    "success": true,
    "data": {
        "count": 1567,
        "next": "https://api.example.com/api/v1/licenses/admin/audit-logs/?page=3",
        "previous": "https://api.example.com/api/v1/licenses/admin/audit-logs/?page=1",
        "results": [
            {
                "id": 1,
                "tenant": {
                    "id": 2,
                    "name": "示例公司"
                },
                "event_type": "LICENSE_ACTIVATED",
                "severity": "medium",
                "description": "许可证 MYAPP-PRO-XXXX-XXXX-XXXX-XXXX 在设备 DESKTOP-ABC123 上激活成功",
                "user_id": null,
                "ip_address": "192.168.1.100",
                "user_agent": "MyApplication/2.1.0 (Windows NT 10.0)",
                "license_id": 1,
                "machine_fingerprint": "a1b2c3d4e5f6789012345678901234567890abcd",
                "metadata": {
                    "activation_code": "ACT-12345678901234567890123456789012",
                    "machine_name": "DESKTOP-ABC123",
                    "activation_type": "online"
                },
                "timestamp": "2024-01-16T09:15:00Z",
                "created_at": "2024-01-16T09:15:00Z"
            }
        ]
    }
}
```

### 2. 获取审计日志详情

#### 请求
```http
GET /api/v1/licenses/admin/audit-logs/{id}/
Authorization: Bearer {access_token}
```

#### 响应示例
```json
{
    "success": true,
    "data": {
        "id": 1,
        "tenant": {
            "id": 2,
            "name": "示例公司"
        },
        "event_type": "LICENSE_ACTIVATED",
        "severity": "medium",
        "description": "许可证 MYAPP-PRO-XXXX-XXXX-XXXX-XXXX 在设备 DESKTOP-ABC123 上激活成功",
        "user": null,
        "ip_address": "192.168.1.100",
        "user_agent": "MyApplication/2.1.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "license": {
            "id": 1,
            "license_key": "MYAPP-PRO-XXXX-XXXX-XXXX-XXXX",
            "customer_name": "张三",
            "status": "active"
        },
        "machine_fingerprint": "a1b2c3d4e5f6789012345678901234567890abcd",
        "metadata": {
            "activation_code": "ACT-12345678901234567890123456789012",
            "machine_name": "DESKTOP-ABC123",
            "activation_type": "online",
            "request_headers": {
                "content-type": "application/json",
                "x-forwarded-for": "192.168.1.100"
            },
            "response_time_ms": 156
        },
        "geolocation": {
            "country": "中国",
            "city": "北京",
            "region": "北京市"
        },
        "timestamp": "2024-01-16T09:15:00Z",
        "created_at": "2024-01-16T09:15:00Z"
    }
}
```

### 3. 审计日志统计分析

#### 获取统计概览
```http
GET /api/v1/licenses/admin/audit-logs/statistics/
Authorization: Bearer {access_token}
```

#### 查询参数
| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `period` | string | 否 | 统计周期 | `period=last_30_days` |
| `group_by` | string | 否 | 分组字段 | `group_by=event_type` |

#### 响应示例
```json
{
    "success": true,
    "data": {
        "period": "last_30_days",
        "total_events": 2456,
        "by_severity": {
            "low": 1234,
            "medium": 890,
            "high": 287,
            "critical": 45
        },
        "by_event_type": {
            "LICENSE_ACTIVATED": 567,
            "LOGIN_SUCCESS": 234,
            "LOGIN_FAILED": 89,
            "LICENSE_CREATED": 156,
            "SUSPICIOUS_ACTIVITY": 23
        },
        "top_ips": [
            {
                "ip_address": "192.168.1.100",
                "event_count": 45,
                "risk_score": 2.1
            },
            {
                "ip_address": "10.0.0.50",
                "event_count": 38,
                "risk_score": 1.8
            }
        ],
        "security_alerts": {
            "critical_events_last_24h": 2,
            "failed_login_attempts": 15,
            "suspicious_activations": 5,
            "blocked_ips": 3
        }
    }
}
```

### 4. 安全事件检测

#### 获取安全告警
```http
GET /api/v1/licenses/admin/audit-logs/security_alerts/
Authorization: Bearer {access_token}
```

#### 查询参数
| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `severity` | string | 否 | 最低严重程度 | `severity=high` |
| `time_range` | string | 否 | 时间范围 | `time_range=last_24_hours` |
| `alert_type` | string | 否 | 告警类型 | `alert_type=brute_force` |

#### alert_type可选值:
- `brute_force` - 暴力攻击
- `suspicious_location` - 可疑地理位置
- `rapid_activations` - 快速激活
- `unauthorized_access` - 未授权访问
- `data_breach_attempt` - 数据泄露尝试

#### 响应示例
```json
{
    "success": true,
    "data": {
        "alerts": [
            {
                "id": "alert_001",
                "type": "brute_force",
                "severity": "high",
                "title": "暴力破解攻击检测",
                "description": "IP地址 192.168.1.200 在10分钟内尝试登录失败20次",
                "affected_resources": {
                    "ip_addresses": ["192.168.1.200"],
                    "user_accounts": ["admin@company.com"],
                    "event_count": 20
                },
                "first_detected": "2024-01-25T10:00:00Z",
                "last_updated": "2024-01-25T10:10:00Z",
                "status": "active",
                "recommended_actions": [
                    "阻止IP地址 192.168.1.200",
                    "重置受影响用户密码",
                    "启用账户锁定机制"
                ]
            },
            {
                "id": "alert_002",
                "type": "suspicious_location",
                "severity": "medium",
                "title": "异常地理位置访问",
                "description": "用户 admin@company.com 从未知地理位置登录",
                "affected_resources": {
                    "users": ["admin@company.com"],
                    "locations": ["俄罗斯, 莫斯科"],
                    "ip_addresses": ["203.0.113.50"]
                },
                "first_detected": "2024-01-25T09:30:00Z",
                "status": "investigating"
            }
        ],
        "summary": {
            "total_alerts": 2,
            "active_alerts": 1,
            "resolved_alerts": 0,
            "by_severity": {
                "critical": 0,
                "high": 1,
                "medium": 1,
                "low": 0
            }
        }
    }
}
```

### 5. 日志导出

#### 导出审计日志
```http
GET /api/v1/licenses/admin/audit-logs/export/
Authorization: Bearer {access_token}
```

#### 查询参数
| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `format` | string | 否 | 导出格式 | `format=csv` |
| `date_from` | date | 否 | 开始日期 | `date_from=2024-01-01` |
| `date_to` | date | 否 | 结束日期 | `date_to=2024-01-31` |
| `event_types` | string | 否 | 事件类型列表 | `event_types=LOGIN_FAILED,SUSPICIOUS_ACTIVITY` |

#### format可选值:
- `csv` - CSV格式
- `json` - JSON格式
- `excel` - Excel格式

## 使用示例

### Python示例
```python
class AuditLogManager:
    def __init__(self, api_client):
        self.api = api_client
    
    def get_security_events(self, severity='high', hours=24):
        from datetime import datetime, timedelta
        since_time = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        return self.api.api_call(
            f'/admin/audit-logs/?severity={severity}&timestamp_after={since_time}Z'
        )
    
    def monitor_failed_logins(self, threshold=5, minutes=10):
        from datetime import datetime, timedelta
        since_time = (datetime.now() - timedelta(minutes=minutes)).isoformat()
        
        failed_logins = self.api.api_call(
            f'/admin/audit-logs/?event_type=LOGIN_FAILED&timestamp_after={since_time}Z'
        )
        
        # 按IP地址分组统计
        ip_counts = {}
        for event in failed_logins['data']['results']:
            ip = event['ip_address']
            if ip:
                ip_counts[ip] = ip_counts.get(ip, 0) + 1
        
        # 找出超过阈值的IP
        suspicious_ips = [ip for ip, count in ip_counts.items() if count >= threshold]
        
        return {
            'total_failed_attempts': failed_logins['data']['count'],
            'suspicious_ips': suspicious_ips,
            'ip_statistics': ip_counts
        }
    
    def get_user_activity_summary(self, user_id, days=30):
        from datetime import datetime, timedelta
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        events = self.api.api_call(
            f'/admin/audit-logs/?user_id={user_id}&timestamp_after={since_date}Z'
        )
        
        if not events['data']['results']:
            return {"message": "无活动记录"}
        
        event_types = {}
        ip_addresses = set()
        
        for event in events['data']['results']:
            event_type = event['event_type']
            event_types[event_type] = event_types.get(event_type, 0) + 1
            
            if event['ip_address']:
                ip_addresses.add(event['ip_address'])
        
        return {
            'total_events': events['data']['count'],
            'event_breakdown': event_types,
            'unique_ip_addresses': len(ip_addresses),
            'ip_list': list(ip_addresses),
            'last_activity': events['data']['results'][0]['timestamp']
        }
    
    def generate_security_report(self, days=7):
        from datetime import datetime, timedelta
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # 获取统计数据
        stats = self.api.api_call('/admin/audit-logs/statistics/?period=last_7_days')
        
        # 获取安全告警
        alerts = self.api.api_call('/admin/audit-logs/security_alerts/?time_range=last_7_days')
        
        # 获取高风险事件
        high_risk_events = self.api.api_call(
            f'/admin/audit-logs/?severity=high&timestamp_after={since_date}Z'
        )
        
        return {
            'report_period': f'最近{days}天',
            'generated_at': datetime.now().isoformat(),
            'statistics': stats['data'],
            'security_alerts': alerts['data'],
            'high_risk_events_count': high_risk_events['data']['count'],
            'recommendations': self._generate_recommendations(stats['data'], alerts['data'])
        }
    
    def _generate_recommendations(self, stats, alerts):
        recommendations = []
        
        # 基于统计数据的建议
        if stats['security_alerts']['failed_login_attempts'] > 50:
            recommendations.append("考虑启用账户锁定机制")
        
        if stats['security_alerts']['suspicious_activations'] > 10:
            recommendations.append("加强许可证激活监控")
        
        # 基于告警的建议
        critical_alerts = alerts['summary']['by_severity'].get('critical', 0)
        if critical_alerts > 0:
            recommendations.append("立即处理严重安全告警")
        
        if not recommendations:
            recommendations.append("当前安全状况良好，建议保持现有安全策略")
        
        return recommendations

# 使用示例
audit_manager = AuditLogManager(api_client)

# 监控登录失败
login_monitor = audit_manager.monitor_failed_logins(threshold=3, minutes=15)
if login_monitor['suspicious_ips']:
    print(f"发现可疑IP: {login_monitor['suspicious_ips']}")

# 生成安全报告
security_report = audit_manager.generate_security_report(days=7)
print("安全报告:")
print(f"总事件数: {security_report['statistics']['total_events']}")
print(f"安全建议: {security_report['recommendations']}")

# 获取特定用户的活动摘要
user_activity = audit_manager.get_user_activity_summary(user_id=1, days=30)
print(f"用户活动: {user_activity}")
```

### JavaScript示例
```javascript
class SecurityMonitor {
    constructor(apiClient) {
        this.api = apiClient;
    }
    
    async getRealTimeAlerts() {
        const alerts = await this.api.apiCall('/admin/audit-logs/security_alerts/?time_range=last_1_hour');
        return alerts.data.alerts.filter(alert => alert.status === 'active');
    }
    
    async detectAnomalousActivity() {
        const now = new Date();
        const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);
        
        const events = await this.api.apiCall(
            `/admin/audit-logs/?timestamp_after=${oneHourAgo.toISOString()}&severity=high`
        );
        
        // 分析事件模式
        const eventsByType = {};
        const eventsByIP = {};
        
        events.data.results.forEach(event => {
            // 按类型统计
            eventsByType[event.event_type] = (eventsByType[event.event_type] || 0) + 1;
            
            // 按IP统计
            if (event.ip_address) {
                eventsByIP[event.ip_address] = (eventsByIP[event.ip_address] || 0) + 1;
            }
        });
        
        return {
            total_high_risk_events: events.data.count,
            events_by_type: eventsByType,
            events_by_ip: eventsByIP,
            anomalies: this.identifyAnomalies(eventsByType, eventsByIP)
        };
    }
    
    identifyAnomalies(eventsByType, eventsByIP) {
        const anomalies = [];
        
        // 检测异常事件类型频率
        Object.entries(eventsByType).forEach(([type, count]) => {
            if (count > 10) {  // 阈值可配置
                anomalies.push({
                    type: 'high_frequency_event',
                    details: `事件类型 ${type} 在1小时内发生了 ${count} 次`
                });
            }
        });
        
        // 检测异常IP活动
        Object.entries(eventsByIP).forEach(([ip, count]) => {
            if (count > 5) {  // 阈值可配置
                anomalies.push({
                    type: 'suspicious_ip_activity',
                    details: `IP地址 ${ip} 在1小时内产生了 ${count} 个高风险事件`
                });
            }
        });
        
        return anomalies;
    }
    
    async createDashboard() {
        const [stats, alerts, recentEvents] = await Promise.all([
            this.api.apiCall('/admin/audit-logs/statistics/?period=last_24_hours'),
            this.api.apiCall('/admin/audit-logs/security_alerts/?time_range=last_24_hours'),
            this.api.apiCall('/admin/audit-logs/?page_size=10&ordering=-timestamp')
        ]);
        
        return {
            timestamp: new Date().toISOString(),
            statistics: stats.data,
            active_alerts: alerts.data.alerts.filter(a => a.status === 'active'),
            recent_events: recentEvents.data.results.slice(0, 5),
            security_score: this.calculateSecurityScore(stats.data, alerts.data)
        };
    }
    
    calculateSecurityScore(stats, alerts) {
        let score = 100;
        
        // 根据告警数量扣分
        const criticalAlerts = alerts.summary.by_severity.critical || 0;
        const highAlerts = alerts.summary.by_severity.high || 0;
        
        score -= criticalAlerts * 20;
        score -= highAlerts * 10;
        
        // 根据安全事件扣分
        if (stats.security_alerts.failed_login_attempts > 20) {
            score -= 15;
        }
        
        if (stats.security_alerts.suspicious_activations > 5) {
            score -= 10;
        }
        
        return Math.max(0, score);
    }
}

// 使用示例
const monitor = new SecurityMonitor(apiClient);

// 实时监控
async function startMonitoring() {
    setInterval(async () => {
        const alerts = await monitor.getRealTimeAlerts();
        if (alerts.length > 0) {
            console.warn(`🚨 检测到 ${alerts.length} 个活跃安全告警`);
            alerts.forEach(alert => {
                console.warn(`- ${alert.title}: ${alert.description}`);
            });
        }
        
        const anomalies = await monitor.detectAnomalousActivity();
        if (anomalies.anomalies.length > 0) {
            console.warn(`⚠️  检测到 ${anomalies.anomalies.length} 个异常模式`);
        }
    }, 60000); // 每分钟检查一次
}

// 创建安全仪表板
const dashboard = await monitor.createDashboard();
console.log(`安全评分: ${dashboard.security_score}/100`);
```

## 常见问题

### Q: 审计日志会保存多长时间？
A: 默认保存90天，超级管理员可以配置保留策略。重要安全事件可能会保存更长时间。

### Q: 如何设置自动安全告警？
A: 可以：
- 定期调用安全告警API
- 设置Webhook通知
- 集成第三方监控系统
- 使用邮件或短信通知

### Q: 哪些操作会记录审计日志？
A: 所有涉及安全的操作都会记录，包括：
- 用户认证和授权
- 许可证管理操作
- 配置变更
- 数据导出
- 异常访问尝试

### Q: 如何分析安全趋势？
A: 建议：
- 定期生成统计报告
- 关注事件类型变化趋势
- 监控地理位置异常
- 跟踪失败率指标

## 相关API文档
- [认证和权限详解](./02_authentication.md) - 了解认证相关的审计事件
- [许可证管理API](./12_admin_licenses_api.md) - 了解许可证操作的审计记录
- [激活记录API](./14_admin_activations_api.md) - 了解激活相关的审计事件
