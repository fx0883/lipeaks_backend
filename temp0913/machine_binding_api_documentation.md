# 机器绑定管理 API 文档

## 概述

机器绑定管理API提供对软件许可证机器绑定的查看和管理功能。机器绑定记录表示特定许可证与客户端机器之间的关联关系，包含机器硬件信息、使用状态等详细数据。

## 基础信息

- **基础URL**: `/api/v1/licenses/admin/machine-bindings/`
- **认证方式**: JWT Token认证
- **权限要求**: 超级管理员或租户管理员权限
- **数据格式**: JSON
- **响应编码**: UTF-8

## 数据模型

### MachineBinding 机器绑定模型

```python
class MachineBinding(BaseModel):
    """机器绑定模型"""
    
    STATUS_CHOICES = [
        ('active', '活跃'),
        ('inactive', '非活跃'), 
        ('blocked', '已阻止')
    ]
    
    # 关联字段
    license = ForeignKey(License)  # 关联许可证
    
    # 机器标识
    machine_id = CharField(max_length=100)  # 机器ID
    machine_fingerprint = CharField(max_length=64)  # 机器指纹
    
    # 硬件信息
    encrypted_hardware_info = TextField()  # 加密硬件信息
    hardware_summary = JSONField()  # 硬件摘要
    os_info = JSONField()  # 操作系统信息
    
    # 网络信息
    last_ip_address = GenericIPAddressField()  # 最后IP地址
    last_location = JSONField()  # 最后位置信息
    
    # 状态管理
    status = CharField(max_length=20)  # 绑定状态
    first_seen_at = DateTimeField()  # 首次绑定时间
    last_seen_at = DateTimeField()  # 最后活跃时间
```

---

## API 接口详情

## 1. 获取机器绑定列表

### 基本信息
- **HTTP方法**: GET
- **URL**: `/api/v1/licenses/admin/machine-bindings/`
- **API名称**: `api_v1_licenses_admin_machine_bindings_list`
- **描述**: 获取机器绑定的分页列表，支持搜索和过滤

### 请求参数

#### Query Parameters (查询参数)

| 参数名称 | 类型 | 必需 | 默认值 | 描述 | 示例 |
|---------|------|------|--------|------|------|
| `page` | integer | 否 | 1 | 页码，从1开始 | `page=1` |
| `page_size` | integer | 否 | 20 | 每页记录数，最大100 | `page_size=50` |
| `license` | integer | 否 | - | 按许可证ID过滤 | `license=123` |
| `status` | string | 否 | - | 按状态过滤：active, inactive, blocked | `status=active` |
| `search` | string | 否 | - | 按机器ID搜索 | `search=DESKTOP-ABC123` |
| `ordering` | string | 否 | -last_seen_at | 排序字段：first_seen_at, last_seen_at, -first_seen_at, -last_seen_at | `ordering=-first_seen_at` |

#### Headers (请求头)

| 参数名称 | 类型 | 必需 | 描述 | 示例 |
|---------|------|------|------|------|
| `Authorization` | string | 是 | JWT认证令牌 | `Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...` |
| `Content-Type` | string | 否 | 内容类型 | `application/json` |
| `X-Tenant-ID` | integer | 否 | 租户ID（多租户环境） | `1` |

### 响应数据

#### 成功响应 (200 OK)

```json
{
    "count": 156,
    "next": "http://localhost:8000/api/v1/licenses/admin/machine-bindings/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "license": 123,
            "license_key_preview": "ABC12...XYZ89",
            "machine_id": "DESKTOP-ABC123",
            "hardware_summary": {
                "cpu": "Intel Core i7-9700K",
                "memory": "16 GB",
                "disk": "512 GB SSD",
                "motherboard": "ASUS ROG STRIX Z390-E"
            },
            "os_info": {
                "name": "Windows 11 Professional",
                "version": "21H2",
                "build": "22000.194",
                "architecture": "x64"
            },
            "last_ip_address": "192.168.1.100",
            "status": "active",
            "first_seen_at": "2023-10-01T08:30:00Z",
            "last_seen_at": "2023-10-15T14:25:30Z",
            "days_since_last_seen": 2
        },
        {
            "id": 2,
            "license": 124,
            "license_key_preview": "DEF45...ABC67",
            "machine_id": "LAPTOP-XYZ789",
            "hardware_summary": {
                "cpu": "AMD Ryzen 7 5800H",
                "memory": "32 GB",
                "disk": "1 TB NVMe SSD",
                "motherboard": "ASUS TUF Gaming A15"
            },
            "os_info": {
                "name": "Ubuntu Linux",
                "version": "22.04 LTS",
                "kernel": "5.15.0-48-generic",
                "architecture": "x86_64"
            },
            "last_ip_address": "10.0.0.25",
            "status": "inactive",
            "first_seen_at": "2023-09-15T10:45:00Z",
            "last_seen_at": "2023-10-10T09:15:20Z",
            "days_since_last_seen": 7
        }
    ]
}
```

#### 字段说明

| 字段名称 | 类型 | 描述 |
|---------|------|------|
| `count` | integer | 符合条件的记录总数 |
| `next` | string/null | 下一页的URL，没有下一页时为null |
| `previous` | string/null | 上一页的URL，没有上一页时为null |
| `results` | array | 当前页的机器绑定记录列表 |
| `results[].id` | integer | 机器绑定记录的唯一标识ID |
| `results[].license` | integer | 关联的许可证ID |
| `results[].license_key_preview` | string | 许可证密钥预览，显示前5位和后5位 |
| `results[].machine_id` | string | 机器唯一标识符 |
| `results[].hardware_summary` | object | 硬件配置摘要信息 |
| `results[].hardware_summary.cpu` | string | CPU型号 |
| `results[].hardware_summary.memory` | string | 内存容量 |
| `results[].hardware_summary.disk` | string | 磁盘信息 |
| `results[].hardware_summary.motherboard` | string | 主板型号 |
| `results[].os_info` | object | 操作系统信息 |
| `results[].os_info.name` | string | 操作系统名称 |
| `results[].os_info.version` | string | 操作系统版本 |
| `results[].os_info.build` | string | 系统构建号（Windows） |
| `results[].os_info.kernel` | string | 内核版本（Linux） |
| `results[].os_info.architecture` | string | 系统架构 |
| `results[].last_ip_address` | string | 最后访问的IP地址 |
| `results[].status` | string | 绑定状态：active(活跃), inactive(非活跃), blocked(已阻止) |
| `results[].first_seen_at` | string | 首次绑定时间，ISO 8601格式 |
| `results[].last_seen_at` | string | 最后活跃时间，ISO 8601格式 |
| `results[].days_since_last_seen` | integer | 距离最后活跃的天数 |

#### 错误响应

**401 Unauthorized - 未授权**
```json
{
    "detail": "未提供认证凭据。"
}
```

**403 Forbidden - 权限不足**
```json
{
    "detail": "您没有执行该操作的权限。"
}
```

**400 Bad Request - 请求参数错误**
```json
{
    "status": ["选择一个有效的选项。abc 不在可用选项中。"],
    "page": ["确保该值大于或等于 1。"]
}
```

### 使用示例

#### cURL 示例
```bash
# 获取所有机器绑定
curl -X GET \
  "http://localhost:8000/api/v1/licenses/admin/machine-bindings/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"

# 获取特定许可证的活跃机器绑定
curl -X GET \
  "http://localhost:8000/api/v1/licenses/admin/machine-bindings/?license=123&status=active" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 搜索特定机器
curl -X GET \
  "http://localhost:8000/api/v1/licenses/admin/machine-bindings/?search=DESKTOP-ABC" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

#### Python 示例
```python
import requests

# 设置请求头
headers = {
    'Authorization': 'Bearer YOUR_JWT_TOKEN',
    'Content-Type': 'application/json'
}

# 获取机器绑定列表
response = requests.get(
    'http://localhost:8000/api/v1/licenses/admin/machine-bindings/',
    headers=headers,
    params={
        'status': 'active',
        'page_size': 50,
        'ordering': '-last_seen_at'
    }
)

if response.status_code == 200:
    data = response.json()
    print(f"总共 {data['count']} 条记录")
    for binding in data['results']:
        print(f"机器 {binding['machine_id']} - 状态: {binding['status']}")
else:
    print(f"请求失败: {response.status_code}")
```

#### JavaScript 示例
```javascript
// 使用 fetch API
const token = 'YOUR_JWT_TOKEN';

async function getMachineBindings(status = null, pageSize = 20) {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    params.append('page_size', pageSize);
    
    try {
        const response = await fetch(
            `http://localhost:8000/api/v1/licenses/admin/machine-bindings/?${params}`,
            {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            }
        );
        
        if (response.ok) {
            const data = await response.json();
            console.log('机器绑定列表:', data.results);
            return data;
        } else {
            console.error('请求失败:', response.status);
        }
    } catch (error) {
        console.error('网络错误:', error);
    }
}

// 调用示例
getMachineBindings('active', 50);
```

---

## 2. 获取机器绑定详情

### 基本信息
- **HTTP方法**: GET
- **URL**: `/api/v1/licenses/admin/machine-bindings/{id}/`
- **API名称**: `api_v1_licenses_admin_machine_bindings_retrieve`
- **描述**: 根据ID获取指定机器绑定的详细信息

### 请求参数

#### Path Parameters (路径参数)

| 参数名称 | 类型 | 必需 | 描述 | 示例 |
|---------|------|------|------|------|
| `id` | integer | 是 | 机器绑定记录的唯一标识ID | `123` |

#### Headers (请求头)

| 参数名称 | 类型 | 必需 | 描述 | 示例 |
|---------|------|------|------|------|
| `Authorization` | string | 是 | JWT认证令牌 | `Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...` |
| `Content-Type` | string | 否 | 内容类型 | `application/json` |
| `X-Tenant-ID` | integer | 否 | 租户ID（多租户环境） | `1` |

### 响应数据

#### 成功响应 (200 OK)

```json
{
    "id": 1,
    "license": 123,
    "license_key_preview": "ABC12...XYZ89",
    "machine_id": "DESKTOP-ABC123",
    "hardware_summary": {
        "cpu": "Intel Core i7-9700K",
        "memory": "16 GB",
        "disk": "512 GB SSD",
        "motherboard": "ASUS ROG STRIX Z390-E",
        "graphics": "NVIDIA GeForce RTX 3080",
        "bios": "American Megatrends Inc. 3203",
        "network_adapters": [
            "Intel Ethernet Connection I219-V",
            "Intel Wi-Fi 6 AX200"
        ]
    },
    "os_info": {
        "name": "Windows 11 Professional",
        "version": "21H2",
        "build": "22000.194",
        "architecture": "x64",
        "install_date": "2023-08-15T00:00:00Z",
        "last_boot_time": "2023-10-15T08:00:00Z",
        "timezone": "UTC+08:00",
        "language": "zh-CN",
        "domain": "WORKGROUP"
    },
    "last_ip_address": "192.168.1.100",
    "status": "active",
    "first_seen_at": "2023-10-01T08:30:00Z",
    "last_seen_at": "2023-10-15T14:25:30Z",
    "days_since_last_seen": 2
}
```

#### 字段说明

除了列表接口的基础字段外，详情接口还包含以下扩展信息：

| 字段名称 | 类型 | 描述 |
|---------|------|------|
| `hardware_summary.graphics` | string | 显卡型号 |
| `hardware_summary.bios` | string | BIOS信息 |
| `hardware_summary.network_adapters` | array | 网络适配器列表 |
| `os_info.install_date` | string | 操作系统安装日期 |
| `os_info.last_boot_time` | string | 最后启动时间 |
| `os_info.timezone` | string | 系统时区 |
| `os_info.language` | string | 系统语言 |
| `os_info.domain` | string | 域信息 |

#### 错误响应

**404 Not Found - 记录不存在**
```json
{
    "detail": "未找到。"
}
```

**401 Unauthorized - 未授权**
```json
{
    "detail": "未提供认证凭据。"
}
```

**403 Forbidden - 权限不足**
```json
{
    "detail": "您没有执行该操作的权限。"
}
```

### 使用示例

#### cURL 示例
```bash
# 获取ID为123的机器绑定详情
curl -X GET \
  "http://localhost:8000/api/v1/licenses/admin/machine-bindings/123/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

#### Python 示例
```python
import requests

def get_machine_binding_detail(binding_id, token):
    """获取机器绑定详情"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    url = f'http://localhost:8000/api/v1/licenses/admin/machine-bindings/{binding_id}/'
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            binding = response.json()
            print(f"机器ID: {binding['machine_id']}")
            print(f"状态: {binding['status']}")
            print(f"CPU: {binding['hardware_summary'].get('cpu', 'N/A')}")
            print(f"操作系统: {binding['os_info'].get('name', 'N/A')}")
            print(f"最后活跃: {binding['last_seen_at']}")
            return binding
        elif response.status_code == 404:
            print(f"机器绑定记录 {binding_id} 不存在")
        else:
            print(f"请求失败: {response.status_code}")
            print(response.json())
    except requests.exceptions.RequestException as e:
        print(f"网络错误: {e}")
    
    return None

# 使用示例
binding_detail = get_machine_binding_detail(123, 'YOUR_JWT_TOKEN')
```

#### JavaScript 示例
```javascript
async function getMachineBindingDetail(bindingId, token) {
    try {
        const response = await fetch(
            `http://localhost:8000/api/v1/licenses/admin/machine-bindings/${bindingId}/`,
            {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                }
            }
        );
        
        if (response.ok) {
            const binding = await response.json();
            console.log('机器绑定详情:', binding);
            
            // 显示关键信息
            console.log(`机器ID: ${binding.machine_id}`);
            console.log(`状态: ${binding.status}`);
            console.log(`CPU: ${binding.hardware_summary?.cpu || 'N/A'}`);
            console.log(`操作系统: ${binding.os_info?.name || 'N/A'}`);
            
            return binding;
        } else if (response.status === 404) {
            console.error('机器绑定记录不存在');
        } else {
            console.error('请求失败:', response.status);
            const error = await response.json();
            console.error('错误详情:', error);
        }
    } catch (error) {
        console.error('网络错误:', error);
    }
    
    return null;
}

// 使用示例
getMachineBindingDetail(123, 'YOUR_JWT_TOKEN');
```

---

## 3. 阻止机器绑定

### 基本信息
- **HTTP方法**: POST
- **URL**: `/api/v1/licenses/admin/machine-bindings/{id}/block/`
- **API名称**: `api_v1_licenses_admin_machine_bindings_block_create`
- **描述**: 阻止指定的机器绑定并记录原因，被阻止的机器将无法继续使用该许可证

### 请求参数

#### Path Parameters (路径参数)

| 参数名称 | 类型 | 必需 | 描述 | 示例 |
|---------|------|------|------|------|
| `id` | integer | 是 | 要阻止的机器绑定记录ID | `123` |

#### Headers (请求头)

| 参数名称 | 类型 | 必需 | 描述 | 示例 |
|---------|------|------|------|------|
| `Authorization` | string | 是 | JWT认证令牌 | `Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...` |
| `Content-Type` | string | 是 | 内容类型 | `application/json` |
| `X-Tenant-ID` | integer | 否 | 租户ID（多租户环境） | `1` |

#### Request Body (请求体)

| 字段名称 | 类型 | 必需 | 描述 | 示例 |
|---------|------|------|------|------|
| `reason` | string | 否 | 阻止原因，默认为"管理员阻止" | `发现可疑活动，暂时阻止访问` |

### 请求示例

```json
{
    "reason": "发现可疑活动，违反许可证使用条款"
}
```

### 响应数据

#### 成功响应 (200 OK)

```json
{
    "success": true,
    "message": "机器绑定已阻止"
}
```

#### 字段说明

| 字段名称 | 类型 | 描述 |
|---------|------|------|
| `success` | boolean | 操作是否成功 |
| `message` | string | 操作结果消息 |

#### 错误响应

**404 Not Found - 记录不存在**
```json
{
    "detail": "未找到。"
}
```

**400 Bad Request - 请求参数错误**
```json
{
    "reason": ["该字段不能超过500个字符。"]
}
```

**401 Unauthorized - 未授权**
```json
{
    "detail": "未提供认证凭据。"
}
```

**403 Forbidden - 权限不足**
```json
{
    "detail": "您没有执行该操作的权限。"
}
```

**500 Internal Server Error - 服务器内部错误**
```json
{
    "success": false,
    "error": "数据库连接失败"
}
```

### 业务逻辑

1. **状态更改**: 将机器绑定的状态从 `active` 或 `inactive` 更改为 `blocked`
2. **安全日志**: 自动记录安全审计日志，包含操作用户、操作时间、机器信息和阻止原因
3. **影响范围**: 被阻止的机器将无法通过该许可证继续激活或验证，现有激活会失效
4. **权限检查**: 只有超级管理员或对应租户的管理员可以执行此操作
5. **审计追踪**: 所有阻止操作都会记录在安全审计日志中，便于后续审查

### 使用示例

#### cURL 示例
```bash
# 阻止ID为123的机器绑定
curl -X POST \
  "http://localhost:8000/api/v1/licenses/admin/machine-bindings/123/block/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "发现可疑活动，暂时阻止访问"
  }'

# 使用默认原因阻止
curl -X POST \
  "http://localhost:8000/api/v1/licenses/admin/machine-bindings/123/block/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

#### Python 示例
```python
import requests
import json

def block_machine_binding(binding_id, reason=None, token=None):
    """阻止机器绑定"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # 构建请求数据
    data = {}
    if reason:
        data['reason'] = reason
    
    url = f'http://localhost:8000/api/v1/licenses/admin/machine-bindings/{binding_id}/block/'
    
    try:
        response = requests.post(
            url, 
            headers=headers, 
            data=json.dumps(data)
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"机器绑定 {binding_id} 已成功阻止")
                print(f"消息: {result.get('message')}")
                return True
            else:
                print(f"阻止失败: {result.get('error')}")
        elif response.status_code == 404:
            print(f"机器绑定记录 {binding_id} 不存在")
        elif response.status_code == 403:
            print("权限不足，无法执行此操作")
        else:
            print(f"请求失败: {response.status_code}")
            print(response.json())
    except requests.exceptions.RequestException as e:
        print(f"网络错误: {e}")
    
    return False

# 使用示例
success = block_machine_binding(
    binding_id=123,
    reason="发现未授权使用，立即阻止",
    token='YOUR_JWT_TOKEN'
)

if success:
    print("阻止操作成功完成")
```

#### JavaScript 示例
```javascript
async function blockMachineBinding(bindingId, reason = null, token) {
    const requestData = {};
    if (reason) {
        requestData.reason = reason;
    }
    
    try {
        const response = await fetch(
            `http://localhost:8000/api/v1/licenses/admin/machine-bindings/${bindingId}/block/`,
            {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            }
        );
        
        const result = await response.json();
        
        if (response.ok) {
            if (result.success) {
                console.log(`机器绑定 ${bindingId} 已成功阻止`);
                console.log(`消息: ${result.message}`);
                
                // 显示成功通知
                alert('机器绑定已成功阻止');
                
                return true;
            } else {
                console.error('阻止失败:', result.error);
                alert(`阻止失败: ${result.error}`);
            }
        } else if (response.status === 404) {
            console.error('机器绑定记录不存在');
            alert('机器绑定记录不存在');
        } else if (response.status === 403) {
            console.error('权限不足');
            alert('权限不足，无法执行此操作');
        } else {
            console.error('请求失败:', response.status, result);
            alert(`请求失败: ${response.status}`);
        }
    } catch (error) {
        console.error('网络错误:', error);
        alert('网络错误，请检查网络连接');
    }
    
    return false;
}

// 使用示例
async function handleBlockMachine() {
    const bindingId = 123;
    const reason = prompt('请输入阻止原因（可选）:');
    const token = 'YOUR_JWT_TOKEN';
    
    const success = await blockMachineBinding(bindingId, reason, token);
    
    if (success) {
        // 刷新页面或更新UI
        location.reload();
    }
}

// 添加确认对话框的版本
async function blockMachineBindingWithConfirm(bindingId, reason, token) {
    const confirmed = confirm(
        `确定要阻止机器绑定 ${bindingId} 吗？\n` +
        `原因: ${reason || '管理员阻止'}\n\n` +
        `此操作将立即生效，被阻止的机器将无法继续使用该许可证。`
    );
    
    if (confirmed) {
        return await blockMachineBinding(bindingId, reason, token);
    }
    
    return false;
}
```

---

## 安全考虑

### 1. 权限控制
- 所有API均需要有效的JWT认证令牌
- 只有超级管理员或租户管理员可以访问
- 租户管理员只能查看和管理自己租户的机器绑定

### 2. 数据保护
- 硬件信息采用加密存储
- 许可证密钥仅显示预览格式（前5位+...+后5位）
- 敏感操作会记录详细的审计日志

### 3. 操作审计
- 所有阻止操作都会记录在安全审计日志中
- 包含操作时间、操作用户、IP地址、操作原因等信息
- 便于后续的安全审查和合规检查

---

## 错误码对照表

| HTTP状态码 | 错误类型 | 描述 | 解决方案 |
|-----------|---------|------|---------|
| 200 | 成功 | 请求处理成功 | - |
| 400 | 请求错误 | 请求参数格式错误或缺少必需参数 | 检查请求参数格式和必需字段 |
| 401 | 未授权 | 缺少认证令牌或令牌无效 | 提供有效的JWT令牌 |
| 403 | 权限不足 | 用户权限不足以执行该操作 | 确认用户具有管理员权限 |
| 404 | 资源不存在 | 指定的机器绑定记录不存在 | 检查机器绑定ID是否正确 |
| 500 | 服务器错误 | 服务器内部错误 | 联系系统管理员 |

---

## 最佳实践

### 1. 分页处理
```python
# 推荐的分页参数设置
page_size = 50  # 建议每页50条记录，平衡性能和用户体验
ordering = '-last_seen_at'  # 按最后活跃时间倒序排列
```

### 2. 状态过滤
```python
# 常用的状态过滤组合
active_machines = {'status': 'active'}  # 活跃机器
problem_machines = {'status__in': ['inactive', 'blocked']}  # 问题机器
```

### 3. 搜索优化
```python
# 使用机器ID前缀进行模糊搜索
search_params = {'search': 'DESKTOP-'}  # 查找所有台式机
```

### 4. 阻止操作
```python
# 阻止前建议先查看详情确认
def safe_block_machine(binding_id, reason, token):
    # 1. 先获取详情确认机器信息
    detail = get_machine_binding_detail(binding_id, token)
    if detail:
        # 2. 确认后执行阻止操作
        return block_machine_binding(binding_id, reason, token)
    return False
```

### 5. 错误处理
```python
# 推荐的错误处理模式
try:
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # 抛出HTTP错误
    return response.json()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 404:
        print("记录不存在")
    elif e.response.status_code == 403:
        print("权限不足")
    else:
        print(f"HTTP错误: {e.response.status_code}")
except requests.exceptions.RequestException as e:
    print(f"网络错误: {e}")
```

---

## 附录

### A. 硬件信息字段说明

`hardware_summary` 对象可能包含的字段：

| 字段名称 | 描述 | 示例 |
|---------|------|------|
| `cpu` | CPU型号 | "Intel Core i7-9700K" |
| `memory` | 内存容量 | "16 GB" |
| `disk` | 磁盘信息 | "512 GB SSD" |
| `motherboard` | 主板型号 | "ASUS ROG STRIX Z390-E" |
| `graphics` | 显卡型号 | "NVIDIA GeForce RTX 3080" |
| `bios` | BIOS信息 | "American Megatrends Inc. 3203" |
| `network_adapters` | 网络适配器 | ["Intel Ethernet Connection I219-V"] |

### B. 操作系统信息字段说明

`os_info` 对象可能包含的字段：

| 字段名称 | 描述 | 示例 |
|---------|------|------|
| `name` | 操作系统名称 | "Windows 11 Professional" |
| `version` | 版本号 | "21H2" |
| `build` | 构建号（Windows） | "22000.194" |
| `kernel` | 内核版本（Linux） | "5.15.0-48-generic" |
| `architecture` | 系统架构 | "x64" |
| `install_date` | 安装日期 | "2023-08-15T00:00:00Z" |
| `last_boot_time` | 最后启动时间 | "2023-10-15T08:00:00Z" |
| `timezone` | 时区 | "UTC+08:00" |
| `language` | 系统语言 | "zh-CN" |
| `domain` | 域信息 | "WORKGROUP" |

### C. 状态说明

| 状态值 | 中文名称 | 描述 |
|-------|---------|------|
| `active` | 活跃 | 机器正常使用中，定期发送心跳 |
| `inactive` | 非活跃 | 机器长时间未发送心跳，可能已离线 |
| `blocked` | 已阻止 | 机器被管理员手动阻止，无法使用许可证 |

---

## 联系支持

如果您在使用API过程中遇到问题，请联系技术支持：

- **邮箱**: support@example.com
- **文档更新日期**: 2023-10-17
- **API版本**: v1.0
- **文档版本**: 1.0.0
