# 许可证更新 API 前端集成文档

## 📋 API 概述

**接口地址**: `PUT /api/v1/licenses/admin/licenses/{id}/`  
**功能描述**: 更新指定ID的许可证信息  
**认证方式**: JWT Token认证  
**权限要求**: 超级管理员或租户管理员  
**请求方法**: PUT (完全更新) / PATCH (部分更新)

## 🔐 权限说明

- **超级管理员**: 可以更新所有租户的许可证
- **租户管理员**: 只能更新自己租户下的许可证  
- **普通用户**: 无权限访问此接口

## 📝 请求参数

### URL参数

| 参数 | 类型 | 必需 | 说明 |
|-----|------|------|------|
| `id` | integer | 是 | 许可证ID |

### Header参数

| 参数名 | 类型 | 必需 | 说明 | 示例 |
|-------|------|------|------|------|
| `Authorization` | string | 是 | JWT认证Token | `Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` |
| `Content-Type` | string | 是 | 请求内容类型 | `application/json` |
| `X-Tenant-ID` | string | 可选 | 租户ID，用于多租户环境 | `1` |

### 请求体参数（JSON格式）

#### 可更新字段

| 字段名 | 类型 | 必需 | 说明 | 示例 |
|-------|------|------|------|------|
| `product` | integer | 否 | 产品ID | `1` |
| `plan` | integer | 否 | 许可方案ID | `2` |
| `tenant` | integer | 否 | 租户ID | `1` |
| `customer_name` | string | 否 | 客户姓名 | `"张三"` |
| `customer_email` | string | 否 | 客户邮箱 | `"zhangsan@example.com"` |
| `max_activations` | integer | 否 | 最大激活数量 | `5` |
| `expires_at` | string | 否 | 过期时间 (ISO8601格式) | `"2024-12-31T23:59:59Z"` |
| `status` | string | 否 | 许可证状态 | `"activated"` |
| `notes` | string | 否 | 备注信息 | `"企业版客户许可证"` |
| `metadata` | object | 否 | 元数据（JSON对象） | `{"region": "asia", "priority": "high"}` |

#### 只读字段（不可更新）

| 字段名 | 说明 |
|-------|------|
| `id` | 许可证唯一标识 |
| `license_key` | 许可证密钥 |
| `issued_at` | 签发时间 |
| `current_activations` | 当前激活数量 |
| `last_verified_at` | 最后验证时间 |

#### 状态枚举值

| 状态值 | 中文含义 |
|--------|----------|
| `generated` | 已生成 |
| `activated` | 已激活 |
| `suspended` | 已挂起 |
| `revoked` | 已撤销 |
| `expired` | 已过期 |

## 📤 响应格式

### 成功响应 (200 OK)

```json
{
    "id": 123,
    "product": 1,
    "product_name": "专业图像处理软件",
    "plan": 2,
    "plan_name": "企业版方案",
    "tenant": 1,
    "tenant_name": "科技有限公司",
    "license_key": "ABC12-DEF34-GHI56-JKL78-MNO90",
    "customer_name": "张三",
    "customer_email": "zhangsan@example.com",
    "max_activations": 10,
    "current_activations": 3,
    "issued_at": "2024-01-15T08:30:00Z",
    "expires_at": "2024-12-31T23:59:59Z",
    "last_verified_at": "2024-09-30T14:25:30Z",
    "status": "activated",
    "machine_bindings_count": 3,
    "days_until_expiry": 92,
    "notes": "企业版客户许可证，支持高级功能",
    "metadata": {
        "region": "asia",
        "priority": "high",
        "customer_tier": "enterprise"
    }
}
```

### 错误响应

#### 400 Bad Request - 参数错误
```json
{
    "success": false,
    "code": 4000,
    "message": "请求参数错误",
    "data": {
        "customer_email": [
            "请输入有效的电子邮箱地址。"
        ],
        "max_activations": [
            "请输入大于0的整数。"
        ]
    }
}
```

#### 401 Unauthorized - 认证失败
```json
{
    "success": false,
    "code": 4001,
    "message": "认证失败",
    "data": {
        "detail": "身份认证信息无效或已过期"
    }
}
```

#### 403 Forbidden - 权限不足
```json
{
    "success": false,
    "code": 4003,
    "message": "权限不足",
    "data": {
        "detail": "您没有权限执行此操作"
    }
}
```

#### 404 Not Found - 许可证不存在
```json
{
    "success": false,
    "code": 4004,
    "message": "资源不存在",
    "data": {
        "detail": "指定的许可证不存在或已被删除"
    }
}
```

#### 500 Internal Server Error - 服务器错误
```json
{
    "success": false,
    "code": 5000,
    "message": "服务器内部错误",
    "data": {
        "error": "数据库连接异常"
    }
}
```

## 💻 前端集成示例

### JavaScript (Axios)

#### 完整更新 (PUT)
```javascript
// 完整更新许可证
async function updateLicense(licenseId, licenseData, token) {
    try {
        const response = await axios.put(
            `/api/v1/licenses/admin/licenses/${licenseId}/`,
            licenseData,
            {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                    'X-Tenant-ID': '1' // 可选，多租户环境
                }
            }
        );
        
        console.log('许可证更新成功:', response.data);
        return response.data;
        
    } catch (error) {
        console.error('许可证更新失败:', error.response?.data || error.message);
        
        // 处理不同类型的错误
        if (error.response?.status === 400) {
            // 参数验证错误
            const errors = error.response.data.data;
            Object.keys(errors).forEach(field => {
                console.error(`字段 ${field}:`, errors[field].join(', '));
            });
        } else if (error.response?.status === 401) {
            // 认证失败，重定向到登录页
            window.location.href = '/login';
        } else if (error.response?.status === 403) {
            // 权限不足
            alert('权限不足，无法执行此操作');
        } else if (error.response?.status === 404) {
            // 资源不存在
            alert('许可证不存在或已被删除');
        }
        
        throw error;
    }
}

// 使用示例
const licenseId = 123;
const updateData = {
    customer_name: "李四",
    customer_email: "lisi@example.com", 
    max_activations: 15,
    expires_at: "2024-12-31T23:59:59Z",
    status: "activated",
    notes: "已升级到企业版",
    metadata: {
        region: "asia",
        priority: "high",
        upgrade_date: "2024-09-30"
    }
};

updateLicense(licenseId, updateData, userToken)
    .then(result => {
        console.log('更新成功，新的许可证信息:', result);
        // 更新界面显示
        updateLicenseDisplay(result);
    })
    .catch(error => {
        console.error('更新失败:', error);
    });
```

#### 部分更新 (PATCH)
```javascript
// 部分更新许可证（只更新指定字段）
async function partialUpdateLicense(licenseId, partialData, token) {
    try {
        const response = await axios.patch(
            `/api/v1/licenses/admin/licenses/${licenseId}/`,
            partialData,
            {
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            }
        );
        
        return response.data;
        
    } catch (error) {
        console.error('部分更新失败:', error.response?.data || error.message);
        throw error;
    }
}

// 部分更新示例：仅更新过期时间和备注
const partialUpdate = {
    expires_at: "2025-06-30T23:59:59Z",
    notes: "延长6个月有效期"
};

partialUpdateLicense(123, partialUpdate, userToken)
    .then(result => {
        console.log('部分更新成功:', result);
    });
```

### TypeScript 接口定义

```typescript
// 许可证数据类型定义
interface License {
    id: number;
    product: number;
    product_name: string;
    plan: number;
    plan_name: string;
    tenant: number;
    tenant_name: string;
    license_key: string;
    customer_name: string;
    customer_email: string;
    max_activations: number;
    current_activations: number;
    issued_at: string;
    expires_at: string;
    last_verified_at: string | null;
    status: 'generated' | 'activated' | 'suspended' | 'revoked' | 'expired';
    machine_bindings_count: number;
    days_until_expiry: number;
    notes: string;
    metadata: Record<string, any>;
}

// 许可证更新参数类型
interface LicenseUpdateData {
    product?: number;
    plan?: number;
    tenant?: number;
    customer_name?: string;
    customer_email?: string;
    max_activations?: number;
    expires_at?: string;
    status?: 'generated' | 'activated' | 'suspended' | 'revoked' | 'expired';
    notes?: string;
    metadata?: Record<string, any>;
}

// API响应类型
interface ApiResponse<T> {
    success: boolean;
    code: number;
    message: string;
    data: T;
}

// 许可证更新函数
async function updateLicense(
    licenseId: number, 
    licenseData: LicenseUpdateData, 
    token: string
): Promise<License> {
    const response = await axios.put<License>(
        `/api/v1/licenses/admin/licenses/${licenseId}/`,
        licenseData,
        {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        }
    );
    
    return response.data;
}
```

### React Hook 示例

```tsx
import { useState } from 'react';
import { License, LicenseUpdateData } from './types';

// 自定义Hook：许可证更新
function useLicenseUpdate() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    
    const updateLicense = async (
        licenseId: number, 
        data: LicenseUpdateData, 
        token: string
    ): Promise<License | null> => {
        setLoading(true);
        setError(null);
        
        try {
            const response = await axios.put<License>(
                `/api/v1/licenses/admin/licenses/${licenseId}/`,
                data,
                {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    }
                }
            );
            
            setLoading(false);
            return response.data;
            
        } catch (err: any) {
            setLoading(false);
            
            if (err.response?.status === 400) {
                setError('请求参数错误，请检查输入数据');
            } else if (err.response?.status === 401) {
                setError('认证失败，请重新登录');
            } else if (err.response?.status === 403) {
                setError('权限不足，无法执行此操作');
            } else if (err.response?.status === 404) {
                setError('许可证不存在或已被删除');
            } else {
                setError('更新失败，请稍后重试');
            }
            
            return null;
        }
    };
    
    return { updateLicense, loading, error };
}

// React组件使用示例
function LicenseUpdateForm({ licenseId, currentLicense, onUpdateSuccess }) {
    const { updateLicense, loading, error } = useLicenseUpdate();
    const [formData, setFormData] = useState({
        customer_name: currentLicense.customer_name,
        customer_email: currentLicense.customer_email,
        max_activations: currentLicense.max_activations,
        expires_at: currentLicense.expires_at,
        status: currentLicense.status,
        notes: currentLicense.notes
    });
    
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        
        const token = localStorage.getItem('authToken');
        if (!token) {
            alert('请先登录');
            return;
        }
        
        const result = await updateLicense(licenseId, formData, token);
        if (result) {
            onUpdateSuccess(result);
            alert('许可证更新成功！');
        }
    };
    
    return (
        <form onSubmit={handleSubmit}>
            {error && <div className="error">{error}</div>}
            
            <div>
                <label>客户姓名:</label>
                <input
                    type="text"
                    value={formData.customer_name}
                    onChange={(e) => setFormData({
                        ...formData, 
                        customer_name: e.target.value
                    })}
                />
            </div>
            
            <div>
                <label>客户邮箱:</label>
                <input
                    type="email"
                    value={formData.customer_email}
                    onChange={(e) => setFormData({
                        ...formData, 
                        customer_email: e.target.value
                    })}
                />
            </div>
            
            <div>
                <label>最大激活数:</label>
                <input
                    type="number"
                    min="1"
                    value={formData.max_activations}
                    onChange={(e) => setFormData({
                        ...formData, 
                        max_activations: parseInt(e.target.value)
                    })}
                />
            </div>
            
            <div>
                <label>过期时间:</label>
                <input
                    type="datetime-local"
                    value={formData.expires_at.slice(0, 19)}
                    onChange={(e) => setFormData({
                        ...formData, 
                        expires_at: e.target.value + 'Z'
                    })}
                />
            </div>
            
            <div>
                <label>状态:</label>
                <select
                    value={formData.status}
                    onChange={(e) => setFormData({
                        ...formData, 
                        status: e.target.value as any
                    })}
                >
                    <option value="generated">已生成</option>
                    <option value="activated">已激活</option>
                    <option value="suspended">已挂起</option>
                    <option value="revoked">已撤销</option>
                    <option value="expired">已过期</option>
                </select>
            </div>
            
            <div>
                <label>备注:</label>
                <textarea
                    value={formData.notes}
                    onChange={(e) => setFormData({
                        ...formData, 
                        notes: e.target.value
                    })}
                />
            </div>
            
            <button type="submit" disabled={loading}>
                {loading ? '更新中...' : '更新许可证'}
            </button>
        </form>
    );
}
```

## 🚨 重要注意事项

### 1. 数据一致性验证
- **产品与方案一致性**: 如果同时更新`product`和`plan`字段，确保方案属于指定的产品
- **租户一致性**: 确保产品、方案、许可证都属于同一租户
- **激活数量限制**: `max_activations`不能小于`current_activations`

### 2. 业务规则限制
- **状态转换规则**: 某些状态转换可能被系统限制（如从`revoked`无法直接变为`activated`）
- **过期时间限制**: 新的过期时间不能早于当前时间
- **租户权限**: 租户管理员只能更新本租户的许可证

### 3. 安全考虑
- **Token有效性**: 定期检查和刷新JWT Token
- **敏感信息**: 客户信息更新时要验证邮箱格式等
- **操作日志**: 所有更新操作都会记录到安全审计日志

### 4. 性能优化
- **部分更新**: 优先使用PATCH方法进行部分更新，减少数据传输
- **批量操作**: 如需更新多个许可证，考虑使用批量更新接口
- **缓存策略**: 更新成功后及时更新前端缓存

### 5. 错误处理最佳实践
```javascript
// 完整的错误处理示例
function handleUpdateError(error) {
    const { response } = error;
    
    switch (response?.status) {
        case 400:
            // 参数验证错误 - 显示具体字段错误
            const fieldErrors = response.data.data;
            return {
                type: 'validation',
                message: '请检查输入数据',
                details: fieldErrors
            };
            
        case 401:
            // 认证失败 - 清除本地token并跳转登录
            localStorage.removeItem('authToken');
            window.location.href = '/login';
            return { type: 'auth', message: '请重新登录' };
            
        case 403:
            // 权限不足 - 显示权限错误
            return { 
                type: 'permission', 
                message: '权限不足，请联系管理员' 
            };
            
        case 404:
            // 资源不存在 - 刷新页面或返回列表
            return { 
                type: 'notfound', 
                message: '许可证不存在，可能已被删除' 
            };
            
        case 500:
            // 服务器错误 - 显示通用错误信息
            return { 
                type: 'server', 
                message: '系统暂时不可用，请稍后重试' 
            };
            
        default:
            return { 
                type: 'unknown', 
                message: '操作失败，请检查网络连接' 
            };
    }
}
```

## 🔗 相关API接口

- **获取许可证详情**: `GET /api/v1/licenses/admin/licenses/{id}/`
- **获取许可证列表**: `GET /api/v1/licenses/admin/licenses/`
- **创建许可证**: `POST /api/v1/licenses/admin/licenses/`
- **删除许可证**: `DELETE /api/v1/licenses/admin/licenses/{id}/`
- **撤销许可证**: `POST /api/v1/licenses/admin/licenses/{id}/revoke/`
- **延长许可证**: `POST /api/v1/licenses/admin/licenses/{id}/extend/`
- **下载许可证**: `GET /api/v1/licenses/admin/licenses/{id}/download/`

---

*文档版本: v1.0*  
*更新时间: 2024-09-30*  
*维护者: 开发团队*
