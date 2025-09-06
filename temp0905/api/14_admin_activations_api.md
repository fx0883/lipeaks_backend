# 激活记录管理API

## 概述

激活记录管理API提供许可证激活历史的查看和分析功能，用于追踪激活过程和监控异常行为。

**Base URL**: `/api/v1/licenses/admin/activations/`  
**认证要求**: JWT Bearer Token  
**权限要求**: 超级管理员或租户管理员  
**访问权限**: 只读

## 数据模型

### LicenseActivation 字段详解

| 字段名 | 类型 | 必填 | 说明 | 生成方式 |
|--------|------|------|------|----------|
| `id` | integer | 只读 | 激活记录唯一标识符 | 数据库自动生成 |
| `license` | integer | 只读 | 关联的许可证ID | 激活时自动设置 |
| `activation_code` | string(32) | 只读 | 激活码 | 激活成功时生成 |
| `machine_fingerprint` | string(64) | 只读 | 机器硬件指纹 | 客户端提供 |
| `machine_name` | string(100) | 只读 | 机器名称 | 客户端提供 |
| `ip_address` | string(45) | 只读 | 激活IP地址 | 请求时获取 |
| `user_agent` | string(500) | 只读 | 用户代理信息 | 请求头获取 |
| `activated_at` | datetime | 只读 | 激活时间 | 激活成功时设置 |
| `success` | boolean | 只读 | 是否激活成功 | 根据激活结果设置 |
| `error_message` | string(500) | 只读 | 错误信息 | 激活失败时记录 |
| `activation_type` | string(20) | 只读 | 激活类型 | 自动识别 |
| `created_at` | datetime | 只读 | 创建时间 | 自动设置 |

### 枚举值说明

#### activation_type可选值:
- `online` - 在线激活：通过网络API激活
- `offline` - 离线激活：通过激活文件激活
- `automatic` - 自动激活：系统自动续期

## API端点详解

### 1. 获取激活记录列表

#### 请求
```http
GET /api/v1/licenses/admin/activations/
Authorization: Bearer {access_token}
```

#### 查询参数
| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `page` | integer | 否 | 页码 | `page=2` |
| `page_size` | integer | 否 | 每页条数 | `page_size=20` |
| `search` | string | 否 | 搜索机器名称、IP地址 | `search=192.168.1` |
| `license` | integer | 否 | 按许可证过滤 | `license=1` |
| `success` | boolean | 否 | 按成功状态过滤 | `success=true` |
| `activation_type` | string | 否 | 按激活类型过滤 | `activation_type=online` |
| `activated_after` | datetime | 否 | 激活时间晚于 | `activated_after=2024-01-01T00:00:00Z` |
| `activated_before` | datetime | 否 | 激活时间早于 | `activated_before=2024-12-31T23:59:59Z` |
| `ip_address` | string | 否 | 按IP地址过滤 | `ip_address=192.168.1.100` |
| `ordering` | string | 否 | 排序字段 | `ordering=-activated_at` |

#### 响应示例
```json
{
    "success": true,
    "data": {
        "count": 234,
        "next": "https://api.example.com/api/v1/licenses/admin/activations/?page=3",
        "previous": "https://api.example.com/api/v1/licenses/admin/activations/?page=1",
        "results": [
            {
                "id": 1,
                "license": {
                    "id": 1,
                    "license_key": "MYAPP-PRO-XXXX-XXXX-XXXX-XXXX",
                    "customer_name": "张三",
                    "customer_email": "zhangsan@example.com"
                },
                "activation_code": "ACT-12345678901234567890123456789012",
                "machine_fingerprint": "a1b2c3d4e5f6789012345678901234567890abcd",
                "machine_name": "DESKTOP-ABC123",
                "ip_address": "192.168.1.100",
                "user_agent": "MyApplication/2.1.0 (Windows NT 10.0)",
                "activated_at": "2024-01-16T09:15:00Z",
                "success": true,
                "error_message": null,
                "activation_type": "online",
                "created_at": "2024-01-16T09:15:00Z"
            }
        ]
    }
}
```

### 2. 获取激活记录详情

#### 请求
```http
GET /api/v1/licenses/admin/activations/{id}/
Authorization: Bearer {access_token}
```

#### 响应示例
```json
{
    "success": true,
    "data": {
        "id": 1,
        "license": {
            "id": 1,
            "license_key": "MYAPP-PRO-XXXX-XXXX-XXXX-XXXX",
            "customer_name": "张三",
            "customer_email": "zhangsan@example.com",
            "status": "active",
            "license_plan": {
                "name": "专业版年度订阅",
                "software_product": {
                    "name": "MyApplication Pro",
                    "version": "2.1.0"
                }
            }
        },
        "activation_code": "ACT-12345678901234567890123456789012",
        "machine_fingerprint": "a1b2c3d4e5f6789012345678901234567890abcd",
        "machine_name": "DESKTOP-ABC123",
        "ip_address": "192.168.1.100",
        "user_agent": "MyApplication/2.1.0 (Windows NT 10.0; Win64; x64)",
        "activated_at": "2024-01-16T09:15:00Z",
        "success": true,
        "error_message": null,
        "activation_type": "online",
        "geolocation": {
            "country": "中国",
            "city": "北京",
            "region": "北京市"
        },
        "machine_binding": {
            "id": 1,
            "status": "active",
            "last_seen_at": "2024-01-25T14:30:00Z"
        }
    }
}
```

### 3. 激活统计分析

#### 获取激活统计
```http
GET /api/v1/licenses/admin/activations/statistics/
Authorization: Bearer {access_token}
```

#### 查询参数
| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `period` | string | 否 | 统计周期 | `period=last_30_days` |
| `group_by` | string | 否 | 分组字段 | `group_by=date` |
| `license` | integer | 否 | 按许可证过滤 | `license=1` |

#### period可选值:
- `today` - 今天
- `yesterday` - 昨天
- `last_7_days` - 最近7天
- `last_30_days` - 最近30天
- `this_month` - 本月
- `last_month` - 上月

#### group_by可选值:
- `date` - 按日期分组
- `hour` - 按小时分组
- `license` - 按许可证分组
- `ip_address` - 按IP地址分组

#### 响应示例
```json
{
    "success": true,
    "data": {
        "period": "last_30_days",
        "total_activations": 156,
        "successful_activations": 145,
        "failed_activations": 11,
        "success_rate": 92.95,
        "unique_licenses": 89,
        "unique_machines": 134,
        "unique_ips": 67,
        "by_date": [
            {
                "date": "2024-01-25",
                "total": 8,
                "success": 7,
                "failed": 1
            },
            {
                "date": "2024-01-24",
                "total": 12,
                "success": 11,
                "failed": 1
            }
        ],
        "by_type": {
            "online": 142,
            "offline": 3,
            "automatic": 11
        },
        "failure_reasons": [
            {
                "reason": "许可证已过期",
                "count": 5
            },
            {
                "reason": "超过最大激活次数",
                "count": 3
            }
        ]
    }
}
```

### 4. 异常激活检测

#### 获取异常激活记录
```http
GET /api/v1/licenses/admin/activations/anomalies/
Authorization: Bearer {access_token}
```

#### 查询参数
| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `anomaly_type` | string | 否 | 异常类型 | `anomaly_type=suspicious_ip` |
| `severity` | string | 否 | 严重程度 | `severity=high` |
| `time_range` | string | 否 | 时间范围 | `time_range=last_24_hours` |

#### anomaly_type可选值:
- `suspicious_ip` - 可疑IP地址
- `rapid_activations` - 快速连续激活
- `geolocation_jump` - 地理位置跳跃
- `device_change` - 设备频繁更换

#### 响应示例
```json
{
    "success": true,
    "data": {
        "anomalies": [
            {
                "type": "rapid_activations",
                "severity": "high",
                "description": "同一许可证在5分钟内激活3次",
                "license_id": 1,
                "license_key": "MYAPP-PRO-XXXX-XXXX-XXXX-XXXX",
                "activation_ids": [15, 16, 17],
                "detected_at": "2024-01-25T10:30:00Z",
                "details": {
                    "activation_count": 3,
                    "time_span_minutes": 5,
                    "different_machines": 3
                }
            },
            {
                "type": "suspicious_ip",
                "severity": "medium",
                "description": "来自高风险地区的激活",
                "license_id": 2,
                "ip_address": "203.0.113.1",
                "activation_ids": [18],
                "detected_at": "2024-01-25T11:15:00Z",
                "details": {
                    "country": "未知",
                    "risk_score": 8.5
                }
            }
        ],
        "summary": {
            "total_anomalies": 2,
            "by_severity": {
                "high": 1,
                "medium": 1,
                "low": 0
            },
            "by_type": {
                "rapid_activations": 1,
                "suspicious_ip": 1
            }
        }
    }
}
```

## 使用示例

### Python示例
```python
class ActivationManager:
    def __init__(self, api_client):
        self.api = api_client
    
    def get_activations(self, **filters):
        params = '&'.join(f'{k}={v}' for k, v in filters.items())
        endpoint = f'/admin/activations/?{params}' if params else '/admin/activations/'
        return self.api.api_call(endpoint)
    
    def get_failed_activations(self, days=7):
        from datetime import datetime, timedelta
        since_date = (datetime.now() - timedelta(days=days)).isoformat()
        return self.get_activations(
            success=False,
            activated_after=since_date
        )
    
    def get_activation_stats(self, period='last_30_days'):
        return self.api.api_call(f'/admin/activations/statistics/?period={period}')
    
    def detect_anomalies(self, time_range='last_24_hours'):
        return self.api.api_call(f'/admin/activations/anomalies/?time_range={time_range}')
    
    def analyze_license_activations(self, license_id):
        activations = self.get_activations(license=license_id, ordering='-activated_at')
        
        if not activations['data']['results']:
            return {"message": "无激活记录"}
        
        results = activations['data']['results']
        unique_machines = set(a['machine_fingerprint'] for a in results)
        unique_ips = set(a['ip_address'] for a in results)
        success_count = sum(1 for a in results if a['success'])
        
        return {
            "total_activations": len(results),
            "successful_activations": success_count,
            "success_rate": success_count / len(results) * 100,
            "unique_machines": len(unique_machines),
            "unique_ips": len(unique_ips),
            "last_activation": results[0]['activated_at'],
            "activation_pattern": self._analyze_pattern(results)
        }
    
    def _analyze_pattern(self, activations):
        # 分析激活模式
        if len(activations) < 2:
            return "数据不足"
        
        time_intervals = []
        for i in range(1, len(activations)):
            current = datetime.fromisoformat(activations[i-1]['activated_at'].replace('Z', '+00:00'))
            previous = datetime.fromisoformat(activations[i]['activated_at'].replace('Z', '+00:00'))
            interval = (current - previous).total_seconds() / 60  # 分钟
            time_intervals.append(interval)
        
        avg_interval = sum(time_intervals) / len(time_intervals)
        
        if avg_interval < 5:
            return "频繁激活"
        elif avg_interval < 60:
            return "快速激活"
        elif avg_interval < 1440:  # 24小时
            return "正常激活"
        else:
            return "偶发激活"

# 使用示例
activation_manager = ActivationManager(api_client)

# 获取最近失败的激活
failed_activations = activation_manager.get_failed_activations(days=7)
print(f"最近7天失败激活次数: {failed_activations['data']['count']}")

# 获取激活统计
stats = activation_manager.get_activation_stats('last_30_days')
print(f"30天激活成功率: {stats['data']['success_rate']:.2f}%")

# 检测异常激活
anomalies = activation_manager.detect_anomalies()
print(f"发现 {anomalies['data']['summary']['total_anomalies']} 个异常")

# 分析特定许可证的激活模式
analysis = activation_manager.analyze_license_activations(1)
print(f"许可证激活分析: {analysis}")
```

### JavaScript示例
```javascript
class ActivationAnalyzer {
    constructor(apiClient) {
        this.api = apiClient;
    }
    
    async getDailyActivationTrend(days = 30) {
        const stats = await this.api.apiCall(
            `/admin/activations/statistics/?period=last_${days}_days&group_by=date`
        );
        
        return stats.data.by_date.map(day => ({
            date: day.date,
            total: day.total,
            successRate: (day.success / day.total * 100).toFixed(2)
        }));
    }
    
    async getTopFailureReasons(limit = 5) {
        const stats = await this.api.apiCall('/admin/activations/statistics/');
        return stats.data.failure_reasons.slice(0, limit);
    }
    
    async monitorSuspiciousActivity() {
        const anomalies = await this.api.apiCall('/admin/activations/anomalies/');
        
        const highSeverityAnomalies = anomalies.data.anomalies.filter(
            a => a.severity === 'high'
        );
        
        if (highSeverityAnomalies.length > 0) {
            console.warn(`发现 ${highSeverityAnomalies.length} 个高风险异常激活`);
            return highSeverityAnomalies;
        }
        
        return [];
    }
}

// 使用示例
const analyzer = new ActivationAnalyzer(apiClient);

// 获取激活趋势
const trend = await analyzer.getDailyActivationTrend(30);
console.log('激活趋势:', trend);

// 监控可疑活动
const suspicious = await analyzer.monitorSuspiciousActivity();
if (suspicious.length > 0) {
    // 发送警告通知
    suspicious.forEach(anomaly => {
        console.warn(`异常类型: ${anomaly.type}, 许可证: ${anomaly.license_key}`);
    });
}
```

## 常见问题

### Q: 为什么激活记录中有重复的机器指纹？
A: 同一设备可能因为网络问题或软件重启导致多次激活尝试，这是正常现象。

### Q: 如何识别许可证滥用？
A: 关注以下指标：
- 短时间内多次激活
- 来自不同地理位置的激活
- 超过预期的设备数量
- 异常的激活时间模式

### Q: 激活失败的常见原因有哪些？
A: 主要原因包括：
- 许可证已过期
- 超过最大激活次数
- 许可证被挂起或撤销
- 网络连接问题
- 客户端版本不兼容

### Q: 如何设置激活异常告警？
A: 可以：
- 定期调用异常检测API
- 设置阈值监控激活失败率
- 监控特定IP地址的激活模式
- 集成外部监控系统

## 相关API文档
- [许可证管理API](./12_admin_licenses_api.md) - 查看激活记录关联的许可证
- [机器绑定管理API](./13_admin_machines_api.md) - 查看激活产生的设备绑定
- [安全审计日志API](./15_admin_audit_api.md) - 查看激活相关的安全事件
