# Licenses API 概览

## 系统架构

Licenses API是一个基于多租户架构的许可证管理系统，提供完整的软件许可证生命周期管理功能。

### 核心概念

#### 1. 软件产品 (SoftwareProduct)
- **定义**：需要许可证保护的软件产品
- **用途**：作为许可证的基础单位，每个产品有独立的RSA密钥对
- **特点**：支持版本管理、激活限制、离线使用配置

#### 2. 许可证方案 (LicensePlan)  
- **定义**：软件产品的不同许可证套餐方案
- **用途**：定义许可证的功能、价格、机器数限制等
- **类型**：试用版、基础版、专业版、企业版、定制版

#### 3. 许可证 (License)
- **定义**：分发给客户的具体许可证实例
- **用途**：控制软件的使用权限和时间限制
- **状态**：已生成、已激活、已挂起、已撤销、已过期

#### 4. 机器绑定 (MachineBinding)
- **定义**：许可证与具体硬件设备的绑定关系
- **用途**：防止许可证在未授权设备上使用
- **验证**：基于硬件指纹和机器唯一标识

#### 5. 激活记录 (LicenseActivation)
- **定义**：许可证激活操作的历史记录
- **用途**：追踪激活过程、监控异常行为
- **类型**：在线激活、离线激活

### API分类

#### 管理API (`/api/v1/licenses/admin/`)
**用途**：供管理员使用的后台管理接口
**认证**：需要JWT Token，要求管理员权限
**权限**：
- 超级管理员：访问所有租户数据
- 租户管理员：仅访问本租户数据

**包含功能**：
- 软件产品管理 (`products/`)
- 许可证方案管理 (`plans/`)
- 许可证管理 (`licenses/`)
- 机器绑定管理 (`machine-bindings/`)
- 激活记录查看 (`activations/`)
- 安全审计日志 (`audit-logs/`)
- 租户配额管理 (`quotas/`)

#### 客户端API (`/api/v1/licenses/`)
**用途**：供客户端软件调用的公开接口
**认证**：通过许可证密钥验证，部分接口无需认证
**权限**：基于许可证有效性验证

**包含功能**：
- 许可证激活 (`activate/`)
- 激活状态验证 (`verify/`)
- 心跳检测 (`heartbeat/`)
- 许可证信息查询 (`info/`)
- 服务状态查询 (`status/`)

#### 报告API (`/api/v1/licenses/reports/`)
**用途**：提供统计分析和报告功能
**认证**：需要JWT Token，要求管理员权限
**权限**：基于租户隔离

**包含功能**：
- 许可证报告生成 (`/`, `generate/`)
- 仪表板统计数据 (`dashboard/`)

## 基础配置

### Base URL
```
生产环境: https://your-domain.com/api/v1/licenses/
开发环境: http://localhost:8000/api/v1/licenses/
```

### HTTP方法约定
- `GET` - 查询数据
- `POST` - 创建数据或执行操作
- `PUT` - 完整更新数据
- `PATCH` - 部分更新数据
- `DELETE` - 删除数据（通常为软删除）

### 内容类型
```
Content-Type: application/json
Accept: application/json
```

## 响应格式规范

### 成功响应
```json
{
    "success": true,
    "data": {
        // 响应数据
    },
    "message": "操作成功",
    "timestamp": "2024-01-15T10:30:00Z"
}
```

### 错误响应
```json
{
    "success": false,
    "error": "错误描述",
    "code": "ERROR_CODE",
    "details": {
        // 详细错误信息
    },
    "timestamp": "2024-01-15T10:30:00Z"
}
```

### 分页响应
```json
{
    "success": true,
    "data": {
        "count": 100,
        "next": "https://api.example.com/api/v1/licenses/admin/products/?page=3",
        "previous": "https://api.example.com/api/v1/licenses/admin/products/?page=1",
        "results": [
            // 数据列表
        ]
    }
}
```

## HTTP状态码

### 成功状态码
- `200 OK` - 请求成功
- `201 Created` - 创建成功
- `204 No Content` - 删除成功，无返回内容

### 客户端错误
- `400 Bad Request` - 请求参数错误
- `401 Unauthorized` - 未认证或认证失败
- `403 Forbidden` - 权限不足
- `404 Not Found` - 资源不存在
- `422 Unprocessable Entity` - 数据验证失败
- `429 Too Many Requests` - 请求频率限制

### 服务器错误
- `500 Internal Server Error` - 服务器内部错误
- `502 Bad Gateway` - 网关错误
- `503 Service Unavailable` - 服务不可用

## 数据字段类型说明

### 基础字段类型
- `string` - 字符串
- `integer` - 整数
- `float` - 浮点数
- `boolean` - 布尔值
- `datetime` - 日期时间 (ISO 8601格式)
- `date` - 日期 (YYYY-MM-DD格式)
- `object` - JSON对象
- `array` - 数组

### 自定义字段类型
- `license_key` - 许可证密钥（格式化字符串）
- `machine_fingerprint` - 机器指纹（64位哈希）
- `activation_code` - 激活码（唯一标识符）
- `encrypted_data` - 加密数据（Base64编码）

### 通用字段说明

#### BaseModel字段（所有模型继承）
- `id` - 主键ID (integer, 自动生成)
- `created_at` - 创建时间 (datetime, 自动设置)
- `updated_at` - 更新时间 (datetime, 自动更新)
- `is_deleted` - 软删除标记 (boolean, 默认false)

#### 状态字段约定
多数模型包含status字段，常见状态值：
- `active` - 活跃/启用
- `inactive` - 非活跃/禁用
- `pending` - 待处理
- `suspended` - 挂起
- `revoked` - 已撤销
- `expired` - 已过期

## 安全机制

### 数据加密
- **传输加密**：所有API通信使用HTTPS/TLS
- **存储加密**：敏感数据（客户信息、硬件信息）AES加密存储
- **密钥管理**：RSA密钥对用于许可证签名验证

### 访问控制
- **认证**：JWT Bearer Token
- **授权**：基于角色的权限控制(RBAC)
- **数据隔离**：严格的租户数据隔离

### 防护措施
- **频率限制**：API调用频率限制
- **异常检测**：可疑活动监控和告警
- **审计日志**：所有操作的详细记录

## 版本控制

### API版本
当前版本：`v1`
版本策略：URL路径版本控制 (`/api/v1/`)

### 向后兼容
- 字段增加：兼容
- 字段删除：新版本
- 字段类型变更：新版本
- 端点变更：新版本

## 错误处理最佳实践

### 常见错误场景
1. **认证失败** - 检查Token是否有效
2. **权限不足** - 确认用户角色和租户权限
3. **数据验证失败** - 检查请求参数格式和必填字段
4. **资源不存在** - 确认ID是否正确且资源未被删除
5. **频率限制** - 实现请求重试机制

### 错误码对照表
详见 [42_error_handling.md](./42_error_handling.md)

## 性能考虑

### 查询优化
- 使用分页限制大结果集
- 利用筛选参数减少数据量
- 合理使用缓存机制

### 并发控制
- 避免同时大量API调用
- 实现指数退避重试策略
- 使用批量操作接口

## 监控和日志

### 系统监控
- API响应时间监控
- 错误率统计
- 系统资源使用监控

### 业务监控
- 许可证激活成功率
- 异常行为检测
- 用户活跃度统计

## 下一步

查看具体的API文档：
- [认证和权限详解](./02_authentication.md)
- [管理API详细文档](./10_admin_products_api.md)
- [客户端API详细文档](./20_client_activation_api.md)
- [使用示例和最佳实践](./40_usage_examples.md)
