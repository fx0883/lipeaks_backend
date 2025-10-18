# Member 许可证删除 API 文档

## API 概述

**接口名称**: 删除我的许可证  
**接口路径**: `/api/v1/licenses/member/my-licenses/{license_id}/`  
**请求方法**: `DELETE`  
**认证方式**: JWT Bearer Token  
**权限要求**: Member 用户身份

## 功能说明

此 API 允许 Member 用户删除自己的许可证分配。删除操作将：

1. ✅ 删除许可证分配记录（标记为已撤销）
2. ✅ 删除所有关联的设备绑定
3. ✅ 更新许可证的激活数量
4. ✅ 记录审计日志
5. ⚠️ **删除操作不可逆**

## 业务规则

### ✅ 允许删除的许可证状态
- `active` - 有效
- `pending` - 待激活
- `suspended` - 已挂起

### ❌ 不允许删除的许可证状态
- `revoked` - 已撤销
- `expired` - 已过期

### 权限限制
- 只能删除自己被分配的许可证
- 受租户隔离保护
- 受频率限制保护（每小时最多 100 次请求）

---

## 请求参数

### 1. 路径参数（Path Parameters）

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| `license_id` | integer | 是 | 许可证分配 ID（从 `my-licenses` 接口返回的 `id` 字段） |

### 2. 查询参数（Query Parameters）

| 参数名 | 类型 | 必填 | 说明 | 默认值 |
|--------|------|------|------|--------|
| `reason` | string | 否 | 删除原因 | "用户主动删除" |

### 3. 请求头（Headers）

| 参数名 | 类型 | 必填 | 说明 | 示例 |
|--------|------|------|------|------|
| `Authorization` | string | 是 | JWT 认证令牌 | `Bearer eyJhbGciOiJIUzI1NiIs...` |
| `Content-Type` | string | 否 | 内容类型 | `application/json` |
| `X-Tenant-ID` | integer | 是 | 租户 ID | `1` |

---

## 响应数据

### 成功响应（200 OK）

```json
{
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
        "success": true,
        "message": "许可证删除成功",
        "data": {
            "assignment_id": 7,
            "license_info": {
                "id": 7,
                "license_id": 31,
                "license_key": "A83B5...9E98D",
                "product_name": "Lipeaks",
                "plan_name": "123",
                "assigned_at": "2025-10-18T02:07:56.364667Z",
                "status_before_delete": "active"
            },
            "deleted_devices_count": 2,
            "deleted_at": "2025-10-18T04:30:00.123456Z",
            "reason": "用户主动删除"
        }
    }
}
```

#### 响应字段说明

| 字段路径 | 类型 | 说明 |
|---------|------|------|
| `success` | boolean | 操作是否成功 |
| `code` | integer | 业务状态码（2000 表示成功） |
| `message` | string | 操作结果消息 |
| `data.success` | boolean | 内部操作是否成功 |
| `data.message` | string | 详细消息 |
| `data.data.assignment_id` | integer | 许可证分配 ID |
| `data.data.license_info` | object | 许可证信息 |
| `data.data.license_info.id` | integer | 分配记录 ID |
| `data.data.license_info.license_id` | integer | 许可证 ID |
| `data.data.license_info.license_key` | string | 许可证密钥（部分显示） |
| `data.data.license_info.product_name` | string | 产品名称 |
| `data.data.license_info.plan_name` | string | 方案名称 |
| `data.data.license_info.assigned_at` | string | 分配时间（ISO 8601 格式） |
| `data.data.license_info.status_before_delete` | string | 删除前的状态 |
| `data.data.deleted_devices_count` | integer | 删除的设备数量 |
| `data.data.deleted_at` | string | 删除时间（ISO 8601 格式） |
| `data.data.reason` | string | 删除原因 |

---

### 错误响应

#### 1. 许可证不存在（400 Bad Request）

```json
{
    "success": false,
    "code": "LICENSE_NOT_FOUND",
    "message": "请求参数错误",
    "data": {
        "success": false,
        "error": "许可证不存在或您无权访问",
        "code": "LICENSE_NOT_FOUND"
    }
}
```

#### 2. 许可证已撤销（400 Bad Request）

```json
{
    "success": false,
    "code": "LICENSE_ALREADY_REVOKED",
    "message": "请求参数错误",
    "data": {
        "success": false,
        "error": "许可证已撤销，无法删除",
        "code": "LICENSE_ALREADY_REVOKED"
    }
}
```

#### 3. 未认证（401 Unauthorized）

```json
{
    "detail": "Authentication credentials were not provided."
}
```

#### 4. 权限不足（403 Forbidden）

```json
{
    "detail": "You do not have permission to perform this action."
}
```

#### 5. 频率限制（429 Too Many Requests）

```json
{
    "detail": "Request was throttled. Expected available in 3600 seconds."
}
```

#### 6. 服务器错误（500 Internal Server Error）

```json
{
    "success": false,
    "code": "DELETE_LICENSE_FAILED",
    "message": "服务器内部错误",
    "data": {
        "success": false,
        "error": "许可证删除失败，请稍后重试",
        "code": "DELETE_LICENSE_FAILED"
    }
}
```

---

## 调用示例

### 示例 1: 基本调用（使用 cURL）

```bash
curl -X DELETE \
  'http://localhost:8000/api/v1/licenses/member/my-licenses/7/' \
  -H 'Accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJ1c2VybmFtZSI6ImZ4MDg4MyIsImV4cCI6MTc2MDg2ODEyMiwibW9kZWxfdHlwZSI6Im1lbWJlciIsImlzX2FkbWluIjpmYWxzZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlfQ.uFo2SnupLSjPMsqfhvmmmA7B1v0x6c-pdMgdU4yQmPI' \
  -H 'X-Tenant-ID: 1'
```

### 示例 2: 指定删除原因（使用 cURL）

```bash
curl -X DELETE \
  'http://localhost:8000/api/v1/licenses/member/my-licenses/7/?reason=不再需要该许可证' \
  -H 'Accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...' \
  -H 'X-Tenant-ID: 1'
```

### 示例 3: JavaScript (Fetch API)

```javascript
// 删除许可证
async function deleteLicense(licenseId, reason = '用户主动删除') {
    try {
        const token = localStorage.getItem('access_token');
        const tenantId = localStorage.getItem('tenant_id');
        
        const url = new URL(`http://localhost:8000/api/v1/licenses/member/my-licenses/${licenseId}/`);
        if (reason) {
            url.searchParams.append('reason', reason);
        }
        
        const response = await fetch(url, {
            method: 'DELETE',
            headers: {
                'Accept': 'application/json',
                'Authorization': `Bearer ${token}`,
                'X-Tenant-ID': tenantId
            }
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            console.log('删除成功:', data.data);
            return data.data;
        } else {
            console.error('删除失败:', data.data?.error || data.detail);
            throw new Error(data.data?.error || data.detail);
        }
    } catch (error) {
        console.error('请求失败:', error);
        throw error;
    }
}

// 使用示例
deleteLicense(7, '试用期结束')
    .then(result => {
        alert(`许可证删除成功！删除了 ${result.deleted_devices_count} 个设备`);
    })
    .catch(error => {
        alert(`删除失败: ${error.message}`);
    });
```

### 示例 4: JavaScript (Axios)

```javascript
import axios from 'axios';

// 创建 axios 实例
const api = axios.create({
    baseURL: 'http://localhost:8000/api/v1',
    headers: {
        'Content-Type': 'application/json'
    }
});

// 添加请求拦截器
api.interceptors.request.use(config => {
    const token = localStorage.getItem('access_token');
    const tenantId = localStorage.getItem('tenant_id');
    
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    if (tenantId) {
        config.headers['X-Tenant-ID'] = tenantId;
    }
    
    return config;
});

// 删除许可证函数
async function deleteLicense(licenseId, reason) {
    try {
        const response = await api.delete(
            `/licenses/member/my-licenses/${licenseId}/`,
            {
                params: { reason }
            }
        );
        
        if (response.data.success) {
            return response.data.data;
        } else {
            throw new Error(response.data.data?.error || '删除失败');
        }
    } catch (error) {
        if (error.response) {
            // 服务器返回错误
            const errorMsg = error.response.data?.data?.error || error.response.data?.detail || '删除失败';
            throw new Error(errorMsg);
        } else {
            // 网络错误
            throw new Error('网络错误，请检查连接');
        }
    }
}

// 使用示例
deleteLicense(7, '不再使用')
    .then(result => {
        console.log('删除成功:', result);
        alert(`许可证删除成功！\n删除了 ${result.deleted_devices_count} 个设备绑定`);
    })
    .catch(error => {
        console.error('删除失败:', error.message);
        alert(`删除失败: ${error.message}`);
    });
```

### 示例 5: React 组件示例

```jsx
import React, { useState } from 'react';
import axios from 'axios';

function LicenseDeleteButton({ licenseId, onSuccess, onError }) {
    const [loading, setLoading] = useState(false);
    const [showConfirm, setShowConfirm] = useState(false);
    
    const handleDelete = async () => {
        setLoading(true);
        
        try {
            const token = localStorage.getItem('access_token');
            const tenantId = localStorage.getItem('tenant_id');
            
            const response = await axios.delete(
                `http://localhost:8000/api/v1/licenses/member/my-licenses/${licenseId}/`,
                {
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'X-Tenant-ID': tenantId
                    },
                    params: {
                        reason: '用户主动删除'
                    }
                }
            );
            
            if (response.data.success) {
                onSuccess && onSuccess(response.data.data);
                setShowConfirm(false);
            } else {
                throw new Error(response.data.data?.error || '删除失败');
            }
        } catch (error) {
            const errorMsg = error.response?.data?.data?.error 
                || error.response?.data?.detail 
                || error.message 
                || '删除失败';
            onError && onError(errorMsg);
        } finally {
            setLoading(false);
        }
    };
    
    return (
        <>
            <button 
                onClick={() => setShowConfirm(true)}
                className="btn btn-danger"
                disabled={loading}
            >
                删除许可证
            </button>
            
            {showConfirm && (
                <div className="modal">
                    <div className="modal-content">
                        <h3>确认删除</h3>
                        <p>确定要删除此许可证吗？所有绑定的设备也会被删除，此操作不可逆！</p>
                        <div className="modal-actions">
                            <button 
                                onClick={handleDelete}
                                className="btn btn-danger"
                                disabled={loading}
                            >
                                {loading ? '删除中...' : '确认删除'}
                            </button>
                            <button 
                                onClick={() => setShowConfirm(false)}
                                className="btn btn-secondary"
                                disabled={loading}
                            >
                                取消
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}

export default LicenseDeleteButton;
```

---

## 完整工作流程

### 步骤 1: 获取许可证列表

首先调用 `GET /api/v1/licenses/member/my-licenses/` 获取许可证列表：

```bash
curl -X GET \
  'http://localhost:8000/api/v1/licenses/member/my-licenses/' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'X-Tenant-ID: 1'
```

响应示例：

```json
{
    "success": true,
    "data": {
        "count": 1,
        "licenses": [
            {
                "id": 7,  // ← 这个 ID 用于删除
                "product_name": "Lipeaks",
                "plan_name": "123",
                "status": "active",
                ...
            }
        ]
    }
}
```

### 步骤 2: 删除许可证

使用步骤 1 获取的 `id` 字段（这里是 7）调用删除接口：

```bash
curl -X DELETE \
  'http://localhost:8000/api/v1/licenses/member/my-licenses/7/' \
  -H 'Authorization: Bearer YOUR_TOKEN' \
  -H 'X-Tenant-ID: 1'
```

### 步骤 3: 验证删除结果

再次调用获取列表接口，确认许可证已被删除（状态变为 revoked）。

---

## 错误码参考

| 错误码 | HTTP 状态码 | 说明 | 解决方案 |
|--------|-------------|------|----------|
| `LICENSE_NOT_FOUND` | 400 | 许可证不存在或无权访问 | 检查 license_id 是否正确，确认是自己的许可证 |
| `LICENSE_ALREADY_REVOKED` | 400 | 许可证已被撤销或过期 | 该许可证无法删除，已处于终止状态 |
| `DELETE_LICENSE_FAILED` | 500 | 服务器内部错误 | 稍后重试或联系技术支持 |
| 未认证 | 401 | Token 无效或过期 | 重新登录获取新 Token |
| 权限不足 | 403 | 不是 Member 用户 | 使用 Member 账户登录 |
| 频率限制 | 429 | 请求过于频繁 | 等待一段时间后重试 |

---

## 注意事项

### ⚠️ 重要提醒

1. **不可逆操作**: 删除许可证后，所有设备绑定将被永久删除，无法恢复
2. **状态限制**: 只能删除 active、pending、suspended 状态的许可证
3. **权限限制**: 只能删除自己被分配的许可证，无法删除他人的许可证
4. **租户隔离**: 自动进行租户隔离验证，确保数据安全
5. **审计记录**: 所有删除操作都会记录审计日志

### 💡 最佳实践

1. **删除前确认**: 在删除前向用户显示确认对话框
2. **显示设备数**: 告知用户将删除多少个设备绑定
3. **记录原因**: 建议传入 `reason` 参数，便于后续追踪
4. **错误处理**: 妥善处理各种错误情况，提供友好的错误提示
5. **刷新列表**: 删除成功后刷新许可证列表

---

## 技术支持

如有问题，请联系技术支持团队或查看完整的 API 文档：

- **Swagger UI**: `http://localhost:8000/api/schema/swagger-ui/`
- **ReDoc**: `http://localhost:8000/api/schema/redoc/`
- **OpenAPI Schema**: `http://localhost:8000/api/schema/`

---

## 更新日志

| 版本 | 日期 | 说明 |
|------|------|------|
| 1.0.0 | 2025-10-18 | 初始版本发布 |
