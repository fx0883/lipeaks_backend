# API 4: 查看许可证的设备列表

## 📌 API 概述

获取指定许可证下所有已绑定设备的详细信息，包括设备状态、硬件信息、最后活跃时间等。用于管理许可证的设备激活情况。

---

## 🔗 请求信息

- **HTTP Method**: `GET`
- **URL**: `/api/v1/licenses/member/my-licenses/{license_id}/devices/`
- **完整URL**: `https://backend.espressox.online/api/v1/licenses/member/my-licenses/{license_id}/devices/`
- **认证**: 必需（JWT Bearer Token）
- **权限要求**: Member 用户，且必须拥有该许可证
- **频率限制**: 无特殊限制

---

## 📥 请求参数

### URL 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `license_id` | Integer | **是** | 许可证ID（从 API 3 获取） |

### 请求头

```http
Authorization: Bearer <your_jwt_token>
Content-Type: application/json
Accept: application/json
```

### 示例 URL

```
GET /api/v1/licenses/member/my-licenses/12345/devices/
```

---

## 📤 响应格式

### ✅ 成功响应 (200 OK)

```json
{
  "success": true,
  "data": {
    "license_info": {
      "id": 12345,
      "product_name": "PDF压缩工具专业版",
      "plan_name": "14天试用版",
      "max_activations": 3,
      "current_activations": 2,
      "available_slots": 1,
      "expires_at": "2024-02-15T10:30:00Z"
    },
    "statistics": {
      "total": 3,
      "active": 2,
      "inactive": 1,
      "blocked": 0
    },
    "devices": [
      {
        "id": 456,
        "machine_id": "MACHINE-ABC123-XYZ",
        "machine_fingerprint": "a1b2c3d4e5f6...",
        "os_name": "Windows 11",
        "os_info": {
          "os_name": "Windows",
          "os_version": "11",
          "os_build": "22000.1",
          "architecture": "x64"
        },
        "hardware_summary": {
          "cpu": "Intel Core i7-10700K",
          "ram": "16GB",
          "disk": "512GB SSD",
          "gpu": "NVIDIA GeForce RTX 3060"
        },
        "last_ip_address": "192.168.1.100",
        "status": "active",
        "status_display": "活跃",
        "first_seen_at": "2024-01-15T10:30:00Z",
        "last_seen_at": "2024-01-20T14:25:30Z",
        "days_since_last_seen": 0
      },
      {
        "id": 457,
        "machine_id": "MACHINE-DEF456-UVW",
        "machine_fingerprint": "b2c3d4e5f6g7...",
        "os_name": "macOS 14.0",
        "os_info": {
          "os_name": "macOS",
          "os_version": "14.0",
          "os_build": "23A344",
          "architecture": "arm64"
        },
        "hardware_summary": {
          "cpu": "Apple M2 Pro",
          "ram": "32GB",
          "disk": "1TB SSD"
        },
        "last_ip_address": "192.168.1.105",
        "status": "active",
        "status_display": "活跃",
        "first_seen_at": "2024-01-18T09:15:00Z",
        "last_seen_at": "2024-01-20T11:40:20Z",
        "days_since_last_seen": 0
      },
      {
        "id": 458,
        "machine_id": "MACHINE-GHI789-RST",
        "machine_fingerprint": "c3d4e5f6g7h8...",
        "os_name": "Windows 10",
        "os_info": {
          "os_name": "Windows",
          "os_version": "10",
          "os_build": "19045.2006",
          "architecture": "x64"
        },
        "hardware_summary": {
          "cpu": "AMD Ryzen 5 5600X",
          "ram": "16GB",
          "disk": "256GB SSD"
        },
        "last_ip_address": "192.168.1.110",
        "status": "inactive",
        "status_display": "非活跃",
        "first_seen_at": "2024-01-12T15:00:00Z",
        "last_seen_at": "2024-01-14T18:30:00Z",
        "days_since_last_seen": 6
      }
    ],
    "permissions": {
      "can_unbind": true
    }
  }
}
```

### 📋 响应字段说明

#### license_info (许可证信息)

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer | 许可证ID |
| `product_name` | String | 产品名称 |
| `plan_name` | String | 方案名称 |
| `max_activations` | Integer | 最大允许激活设备数 |
| `current_activations` | Integer | 当前活跃设备数 |
| `available_slots` | Integer | 剩余可用激活配额 |
| `expires_at` | String (ISO 8601) | 许可证过期时间 |

#### statistics (统计信息)

| 字段 | 类型 | 说明 |
|------|------|------|
| `total` | Integer | 总设备数（包括已解绑） |
| `active` | Integer | 活跃设备数 |
| `inactive` | Integer | 非活跃设备数（已解绑） |
| `blocked` | Integer | 被阻止的设备数 |

#### device (设备对象)

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer | 设备绑定ID（用于解绑操作） |
| `machine_id` | String | 机器唯一标识符 |
| `machine_fingerprint` | String | 机器指纹哈希值 |
| `os_name` | String | 操作系统名称和版本（格式化） |
| `os_info` | Object | 详细操作系统信息 |
| `os_info.os_name` | String | 操作系统名称 |
| `os_info.os_version` | String | 操作系统版本 |
| `os_info.os_build` | String | 系统构建号 |
| `os_info.architecture` | String | 系统架构（x64/arm64等） |
| `hardware_summary` | Object | 硬件摘要信息 |
| `hardware_summary.cpu` | String | CPU型号 |
| `hardware_summary.ram` | String | 内存大小 |
| `hardware_summary.disk` | String | 硬盘信息 |
| `hardware_summary.gpu` | String | 显卡信息（可选） |
| `last_ip_address` | String | 最后连接IP地址 |
| `status` | String | 设备状态（`active`/`inactive`/`blocked`） |
| `status_display` | String | 状态显示名称（中文） |
| `first_seen_at` | String (ISO 8601) | 首次绑定时间 |
| `last_seen_at` | String (ISO 8601) | 最后活跃时间 |
| `days_since_last_seen` | Integer | 距离最后活跃天数 |

#### permissions (权限信息)

| 字段 | 类型 | 说明 |
|------|------|------|
| `can_unbind` | Boolean | 当前用户是否可以解绑设备 |

---

## ❌ 错误响应

### 400 Bad Request - 许可证不存在或无权访问

```json
{
  "success": false,
  "error": "许可证不存在或您无权访问",
  "code": "LICENSE_NOT_FOUND"
}
```

**原因**:
- 许可证ID不存在
- 许可证不属于当前用户
- 许可证已被删除

---

### 401 Unauthorized

```json
{
  "detail": "Authentication credentials were not provided."
}
```

---

### 403 Forbidden

```json
{
  "detail": "You do not have permission to perform this action."
}
```

---

### 500 Internal Server Error

```json
{
  "success": false,
  "error": "获取设备列表失败，请稍后重试",
  "code": "FETCH_DEVICES_FAILED"
}
```

---

## 💻 前端集成代码

### JavaScript + Axios

```javascript
import axios from 'axios';

/**
 * 获取许可证的设备列表
 * @param {number} licenseId - 许可证ID
 * @returns {Promise<object>} 设备列表和统计信息
 */
async function getLicenseDevices(licenseId) {
  try {
    const response = await axios.get(
      `/api/v1/licenses/member/my-licenses/${licenseId}/devices/`,
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`
        }
      }
    );

    if (response.data.success) {
      const data = response.data.data;
      console.log(`许可证 ${licenseId} 共有 ${data.statistics.total} 台设备`);
      console.log(`活跃设备: ${data.statistics.active} 台`);
      console.log(`可用配额: ${data.license_info.available_slots} 个`);
      return data;
    }
  } catch (error) {
    if (error.response?.status === 400) {
      alert('许可证不存在或您无权访问');
    } else if (error.response?.status === 401) {
      localStorage.removeItem('jwt_token');
      window.location.href = '/login';
    } else {
      console.error('获取设备列表失败:', error);
    }
    throw error;
  }
}

// 使用示例
getLicenseDevices(12345).then(data => {
  // 渲染设备列表
  renderDeviceList(data.devices);
  
  // 显示统计信息
  console.log('许可证信息:', data.license_info);
  console.log('设备统计:', data.statistics);
});
```

### React 完整组件

```javascript
import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';

function LicenseDevicesPage() {
  const { licenseId } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDevices();
  }, [licenseId]);

  const fetchDevices = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await axios.get(
        `/api/v1/licenses/member/my-licenses/${licenseId}/devices/`,
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`
          }
        }
      );

      if (response.data.success) {
        setData(response.data.data);
      }
    } catch (err) {
      const errorData = err.response?.data;
      setError(errorData?.error || '获取设备列表失败');
      
      if (err.response?.status === 401) {
        window.location.href = '/login';
      }
    } finally {
      setLoading(false);
    }
  };

  const getDeviceIcon = (osName) => {
    if (osName.includes('Windows')) return '🖥️';
    if (osName.includes('macOS')) return '🍎';
    if (osName.includes('Linux')) return '🐧';
    return '💻';
  };

  const getStatusBadge = (status) => {
    const badges = {
      active: <span className="badge badge-success">活跃</span>,
      inactive: <span className="badge badge-gray">非活跃</span>,
      blocked: <span className="badge badge-error">已阻止</span>
    };
    return badges[status] || <span className="badge">{status}</span>;
  };

  const handleUnbindDevice = (deviceId, machineName) => {
    if (confirm(`确定要解绑设备 "${machineName}" 吗？`)) {
      // 跳转到解绑确认页或直接调用解绑 API（API 5）
      unbindDevice(licenseId, deviceId);
    }
  };

  if (loading) {
    return <div className="loading">加载中...</div>;
  }

  if (error) {
    return (
      <div className="error-page">
        <p>❌ {error}</p>
        <button onClick={() => window.history.back()}>返回</button>
      </div>
    );
  }

  const { license_info, statistics, devices, permissions } = data;

  return (
    <div className="license-devices-page">
      {/* 许可证信息卡片 */}
      <div className="license-info-card">
        <h2>{license_info.product_name}</h2>
        <p className="plan-name">{license_info.plan_name}</p>
        
        <div className="activation-progress">
          <div className="progress-info">
            <span>设备激活</span>
            <span className="progress-numbers">
              {license_info.current_activations} / {license_info.max_activations}
            </span>
          </div>
          <div className="progress-bar">
            <div 
              className="progress-fill"
              style={{ 
                width: `${(license_info.current_activations / license_info.max_activations) * 100}%` 
              }}
            ></div>
          </div>
          <div className="available-slots">
            {license_info.available_slots > 0 ? (
              <span className="text-success">
                还可激活 {license_info.available_slots} 台设备
              </span>
            ) : (
              <span className="text-error">激活配额已用完</span>
            )}
          </div>
        </div>

        <div className="expiry-info">
          <span>过期时间:</span>
          <span>{new Date(license_info.expires_at).toLocaleString('zh-CN')}</span>
        </div>
      </div>

      {/* 统计卡片 */}
      <div className="statistics-row">
        <div className="stat-item">
          <div className="stat-value">{statistics.total}</div>
          <div className="stat-label">总设备数</div>
        </div>
        <div className="stat-item">
          <div className="stat-value text-success">{statistics.active}</div>
          <div className="stat-label">活跃</div>
        </div>
        <div className="stat-item">
          <div className="stat-value text-gray">{statistics.inactive}</div>
          <div className="stat-label">非活跃</div>
        </div>
        <div className="stat-item">
          <div className="stat-value text-error">{statistics.blocked}</div>
          <div className="stat-label">已阻止</div>
        </div>
      </div>

      {/* 设备列表 */}
      <div className="devices-section">
        <div className="section-header">
          <h3>设备列表</h3>
          <button onClick={fetchDevices} className="btn-refresh">
            🔄 刷新
          </button>
        </div>

        {devices.length === 0 ? (
          <div className="empty-state">
            <p>此许可证尚未激活任何设备</p>
            <p className="hint">请在软件中使用许可证密钥进行激活</p>
          </div>
        ) : (
          <div className="devices-list">
            {devices.map(device => (
              <div key={device.id} className={`device-card ${device.status}`}>
                <div className="device-header">
                  <div className="device-title">
                    <span className="device-icon">{getDeviceIcon(device.os_name)}</span>
                    <div>
                      <h4>{device.machine_id}</h4>
                      <span className="os-name">{device.os_name}</span>
                    </div>
                  </div>
                  {getStatusBadge(device.status)}
                </div>

                <div className="device-details">
                  <div className="detail-grid">
                    <div className="detail-item">
                      <label>💻 CPU</label>
                      <span>{device.hardware_summary?.cpu || 'N/A'}</span>
                    </div>
                    <div className="detail-item">
                      <label>🎯 内存</label>
                      <span>{device.hardware_summary?.ram || 'N/A'}</span>
                    </div>
                    <div className="detail-item">
                      <label>💾 硬盘</label>
                      <span>{device.hardware_summary?.disk || 'N/A'}</span>
                    </div>
                    {device.hardware_summary?.gpu && (
                      <div className="detail-item">
                        <label>🎮 显卡</label>
                        <span>{device.hardware_summary.gpu}</span>
                      </div>
                    )}
                    <div className="detail-item">
                      <label>🌐 IP地址</label>
                      <span>{device.last_ip_address}</span>
                    </div>
                    <div className="detail-item">
                      <label>🕐 首次激活</label>
                      <span>{new Date(device.first_seen_at).toLocaleDateString('zh-CN')}</span>
                    </div>
                    <div className="detail-item">
                      <label>🕑 最后活跃</label>
                      <span>
                        {new Date(device.last_seen_at).toLocaleString('zh-CN')}
                        {device.days_since_last_seen > 0 && (
                          <span className="days-ago">
                            {' '}({device.days_since_last_seen} 天前)
                          </span>
                        )}
                      </span>
                    </div>
                  </div>
                </div>

                {/* 设备操作 */}
                {device.status === 'active' && permissions.can_unbind && (
                  <div className="device-actions">
                    <button 
                      onClick={() => handleUnbindDevice(device.id, device.machine_id)}
                      className="btn btn-danger btn-sm"
                    >
                      🗑️ 解绑此设备
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
```

### cURL 示例

```bash
curl -X GET "https://backend.espressox.online/api/v1/licenses/member/my-licenses/12345/devices/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Accept: application/json"
```

---

## 🎨 UI/UX 建议

### 1. **许可证信息展示**
- 显示产品名称和方案名称
- 可视化激活进度条
- 突出显示可用配额

### 2. **设备卡片设计**
- 根据操作系统显示对应图标
- 状态用颜色区分（绿色=活跃，灰色=非活跃）
- 显示硬件摘要信息
- 最后活跃时间用相对时间（如"2小时前"）

### 3. **操作按钮**
- 活跃设备显示"解绑"按钮
- 非活跃设备隐藏或禁用按钮
- 解绑前显示确认对话框

### 4. **空状态**
- 如果没有设备，提示用户激活
- 提供激活指南链接

### 5. **过滤和搜索**
- 按状态筛选（全部/活跃/非活跃）
- 按设备名称搜索
- 按最后活跃时间排序

---

## 📝 注意事项

### 1. **权限验证**
- 只能查看自己拥有的许可证设备
- 后端自动验证 LicenseAssignment 归属

### 2. **设备状态**
- `active`: 当前正在使用的设备
- `inactive`: 已解绑的设备（保留历史记录）
- `blocked`: 被管理员阻止的设备

### 3. **硬件信息**
- 硬件信息由客户端软件上报
- 不同产品上报的字段可能不同
- 前端需灵活处理缺失字段

### 4. **数据刷新**
- 建议实时刷新，不缓存
- 解绑设备后自动刷新列表
- 提供手动刷新按钮

### 5. **解绑操作**
- 只能解绑 `active` 状态的设备
- 解绑前显示确认对话框
- 解绑成功后跳转到 API 5

---

## 🔄 业务流程

```
用户在"我的许可证"页面点击"管理设备"
    ↓
跳转到设备列表页，传递 license_id
    ↓
前端调用 API 4 获取设备列表
    ↓
后端验证许可证归属
    ↓
查询该许可证的所有 MachineBinding
    ↓
返回设备列表和统计信息
    ↓
前端渲染设备卡片
    ↓
用户可以:
  ├─ 查看设备硬件信息
  ├─ 查看最后活跃时间
  └─ 点击"解绑"按钮解绑设备（API 5）
```

---

[返回文档导航](./README.md) | [上一个API](./API-3-查看我的许可证.md) | [下一个API](./API-5-解绑设备.md)
