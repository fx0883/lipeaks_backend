# API 5: 解绑设备

## 📌 API 概述

Member 用户解绑自己许可证下的指定设备，释放激活配额。适用于更换设备、清理不使用的设备绑定等场景。

---

## 🔗 请求信息

- **HTTP Method**: `POST`
- **URL**: `/api/v1/licenses/member/unbind-device/`
- **完整URL**: `https://backend.espressox.online/api/v1/licenses/member/unbind-device/`
- **认证**: 必需（JWT Bearer Token）
- **权限要求**: Member 用户，且必须拥有该许可证
- **频率限制**: 通用 Member API 限制（每小时 60 次）

---

## 📥 请求参数

### Request Body (JSON)

```json
{
  "license_id": 12345,
  "machine_binding_id": 456,
  "reason": "更换新电脑"
}
```

### 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `license_id` | Integer | **是** | 许可证ID（从 API 3 获取） |
| `machine_binding_id` | Integer | **是** | 设备绑定ID（从 API 4 获取） |
| `reason` | String | 否 | 解绑原因，最多500字符，默认"用户主动解绑" |

### 请求头

```http
Authorization: Bearer <your_jwt_token>
Content-Type: application/json
Accept: application/json
```

---

## 📤 响应格式

### ✅ 成功响应 (200 OK)

```json
{
  "success": true,
  "message": "设备解绑成功",
  "data": {
    "license_id": 12345,
    "machine_binding_id": 456,
    "machine_id": "MACHINE-ABC123-XYZ",
    "unbound_at": "2024-01-20T15:30:00Z",
    "reason": "更换新电脑",
    "remaining_activations": 1,
    "max_activations": 3,
    "available_slots": 2
  }
}
```

### 📋 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | Boolean | 操作是否成功（true） |
| `message` | String | 成功消息 |
| `license_id` | Integer | 许可证ID |
| `machine_binding_id` | Integer | 设备绑定ID |
| `machine_id` | String | 机器标识符 |
| `unbound_at` | String (ISO 8601) | 解绑时间 |
| `reason` | String | 解绑原因 |
| `remaining_activations` | Integer | 解绑后剩余的活跃设备数 |
| `max_activations` | Integer | 最大允许激活设备数 |
| `available_slots` | Integer | 解绑后可用的激活配额 |

---

## ❌ 错误响应

### 400 Bad Request - 业务错误

#### 1. 许可证不存在或无权访问

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

#### 2. 设备不存在或不属于该许可证

```json
{
  "success": false,
  "error": "设备不存在或不属于该许可证",
  "code": "DEVICE_NOT_FOUND"
}
```

**原因**:
- 设备绑定ID不存在
- 设备不属于指定的许可证
- 数据不匹配

---

#### 3. 设备不是活跃状态

```json
{
  "success": false,
  "error": "设备当前状态为非活跃，无法解绑",
  "code": "DEVICE_NOT_ACTIVE"
}
```

**原因**:
- 设备已经被解绑（状态为 `inactive`）
- 设备被阻止（状态为 `blocked`）
- 只能解绑状态为 `active` 的设备

---

#### 4. 参数验证错误

```json
{
  "success": false,
  "errors": {
    "license_id": ["This field is required."],
    "machine_binding_id": ["Ensure this value is greater than or equal to 1."],
    "reason": ["Ensure this field has no more than 500 characters."]
  }
}
```

**原因**: 请求参数格式或内容不符合要求。

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

### 429 Too Many Requests

```json
{
  "detail": "Request was throttled. Expected available in 3600 seconds."
}
```

**原因**: API 调用频率超限。

---

### 500 Internal Server Error

```json
{
  "success": false,
  "error": "设备解绑失败，请稍后重试",
  "code": "UNBIND_FAILED"
}
```

---

## 💻 前端集成代码

### JavaScript + Axios

```javascript
import axios from 'axios';

/**
 * 解绑设备
 * @param {number} licenseId - 许可证ID
 * @param {number} machineBindingId - 设备绑定ID
 * @param {string} reason - 解绑原因（可选）
 * @returns {Promise<object>} 解绑结果
 */
async function unbindDevice(licenseId, machineBindingId, reason = '') {
  try {
    const response = await axios.post(
      '/api/v1/licenses/member/unbind-device/',
      {
        license_id: licenseId,
        machine_binding_id: machineBindingId,
        reason: reason || '用户主动解绑'
      },
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`,
          'Content-Type': 'application/json'
        }
      }
    );

    if (response.data.success) {
      const result = response.data.data;
      console.log('✅ 设备解绑成功');
      console.log(`机器ID: ${result.machine_id}`);
      console.log(`剩余激活数: ${result.remaining_activations}/${result.max_activations}`);
      console.log(`可用配额: ${result.available_slots}`);
      return result;
    }
  } catch (error) {
    handleUnbindError(error);
    throw error;
  }
}

/**
 * 错误处理函数
 */
function handleUnbindError(error) {
  if (!error.response) {
    console.error('网络错误:', error.message);
    alert('网络连接失败，请检查网络后重试');
    return;
  }

  const status = error.response.status;
  const data = error.response.data;

  switch (status) {
    case 400:
      // 业务错误
      switch (data.code) {
        case 'LICENSE_NOT_FOUND':
          alert('许可证不存在或您无权访问');
          break;
        case 'DEVICE_NOT_FOUND':
          alert('设备不存在或不属于该许可证');
          break;
        case 'DEVICE_NOT_ACTIVE':
          alert('该设备已经被解绑，无需重复操作');
          break;
        default:
          alert(data.error || '解绑失败，请检查输入');
      }
      break;

    case 401:
      console.error('认证失败');
      localStorage.removeItem('jwt_token');
      window.location.href = '/login';
      break;

    case 403:
      alert('您没有权限执行此操作');
      break;

    case 429:
      alert('操作过于频繁，请稍后再试');
      break;

    case 500:
      alert('服务器错误，请稍后重试');
      break;

    default:
      console.error('未知错误:', error);
      alert('解绑失败，请稍后重试');
  }
}

// 使用示例
unbindDevice(12345, 456, '更换新电脑')
  .then(result => {
    console.log('解绑成功:', result);
    // 显示成功消息
    alert(`设备已成功解绑！\n剩余可用激活配额: ${result.available_slots} 个`);
    // 刷新设备列表
    window.location.reload();
  })
  .catch(err => {
    console.error('解绑失败:', err);
  });
```

### React 组件 - 解绑确认对话框

```javascript
import { useState } from 'react';
import axios from 'axios';

function UnbindDeviceDialog({ device, licenseId, onSuccess, onCancel }) {
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleUnbind = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(
        '/api/v1/licenses/member/unbind-device/',
        {
          license_id: licenseId,
          machine_binding_id: device.id,
          reason: reason || '用户主动解绑'
        },
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`
          }
        }
      );

      if (response.data.success) {
        // 调用成功回调
        onSuccess(response.data.data);
      }
    } catch (err) {
      const errorData = err.response?.data;
      
      if (errorData?.code) {
        const errorMessages = {
          'LICENSE_NOT_FOUND': '许可证不存在或您无权访问',
          'DEVICE_NOT_FOUND': '设备不存在',
          'DEVICE_NOT_ACTIVE': '设备已经被解绑'
        };
        setError(errorMessages[errorData.code] || errorData.error);
      } else if (err.response?.status === 401) {
        window.location.href = '/login';
      } else {
        setError('解绑失败，请稍后重试');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="dialog-overlay">
      <div className="dialog-content">
        <div className="dialog-header">
          <h3>⚠️ 确认解绑设备</h3>
        </div>

        <div className="dialog-body">
          <div className="warning-message">
            <p>您确定要解绑以下设备吗？</p>
          </div>

          <div className="device-info-box">
            <div className="info-row">
              <label>设备ID:</label>
              <span>{device.machine_id}</span>
            </div>
            <div className="info-row">
              <label>操作系统:</label>
              <span>{device.os_name}</span>
            </div>
            <div className="info-row">
              <label>最后活跃:</label>
              <span>{new Date(device.last_seen_at).toLocaleString('zh-CN')}</span>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="reason">解绑原因 (可选)</label>
            <textarea
              id="reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="请输入解绑原因..."
              rows={3}
              maxLength={500}
            />
            <div className="char-count">{reason.length} / 500</div>
          </div>

          <div className="info-message">
            <p>💡 解绑后，该设备将无法继续使用许可证，需要重新激活。</p>
          </div>

          {error && (
            <div className="alert alert-error">
              ❌ {error}
            </div>
          )}
        </div>

        <div className="dialog-footer">
          <button 
            onClick={onCancel}
            className="btn btn-secondary"
            disabled={loading}
          >
            取消
          </button>
          <button 
            onClick={handleUnbind}
            className="btn btn-danger"
            disabled={loading}
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                解绑中...
              </>
            ) : (
              '确认解绑'
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

// 成功消息组件
function UnbindSuccessMessage({ result, onClose }) {
  return (
    <div className="success-dialog">
      <div className="success-icon">✅</div>
      <h3>设备解绑成功</h3>
      
      <div className="result-info">
        <p>设备 <strong>{result.machine_id}</strong> 已成功解绑</p>
        <div className="quota-info">
          <p>剩余激活设备: <strong>{result.remaining_activations}</strong></p>
          <p>可用激活配额: <strong className="text-success">{result.available_slots}</strong></p>
        </div>
      </div>

      <button onClick={onClose} className="btn btn-primary">
        确定
      </button>
    </div>
  );
}

// 在设备列表中使用
function DeviceList({ licenseId, devices, onDevicesChange }) {
  const [showUnbindDialog, setShowUnbindDialog] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [showSuccess, setShowSuccess] = useState(false);
  const [unbindResult, setUnbindResult] = useState(null);

  const handleUnbindClick = (device) => {
    setSelectedDevice(device);
    setShowUnbindDialog(true);
  };

  const handleUnbindSuccess = (result) => {
    setUnbindResult(result);
    setShowUnbindDialog(false);
    setShowSuccess(true);
    
    // 刷新设备列表
    onDevicesChange();
  };

  const handleSuccessClose = () => {
    setShowSuccess(false);
    setUnbindResult(null);
  };

  return (
    <div>
      {/* 设备列表 */}
      {devices.map(device => (
        <div key={device.id} className="device-card">
          {/* 设备信息 */}
          <h4>{device.machine_id}</h4>
          <p>{device.os_name}</p>
          
          {/* 解绑按钮 */}
          {device.status === 'active' && (
            <button 
              onClick={() => handleUnbindClick(device)}
              className="btn btn-danger btn-sm"
            >
              🗑️ 解绑设备
            </button>
          )}
        </div>
      ))}

      {/* 解绑确认对话框 */}
      {showUnbindDialog && selectedDevice && (
        <UnbindDeviceDialog
          device={selectedDevice}
          licenseId={licenseId}
          onSuccess={handleUnbindSuccess}
          onCancel={() => setShowUnbindDialog(false)}
        />
      )}

      {/* 成功消息 */}
      {showSuccess && unbindResult && (
        <UnbindSuccessMessage
          result={unbindResult}
          onClose={handleSuccessClose}
        />
      )}
    </div>
  );
}
```

### 快速解绑（一键操作）

```javascript
/**
 * 快速解绑设备（带确认）
 * @param {number} licenseId - 许可证ID
 * @param {number} machineBindingId - 设备绑定ID
 * @param {string} machineName - 设备名称（用于显示）
 */
async function quickUnbind(licenseId, machineBindingId, machineName) {
  // 确认对话框
  const confirmed = confirm(
    `确定要解绑设备 "${machineName}" 吗？\n\n` +
    `解绑后该设备将无法继续使用许可证。`
  );

  if (!confirmed) {
    return;
  }

  try {
    const result = await unbindDevice(licenseId, machineBindingId);
    
    // 显示成功消息
    alert(
      `设备解绑成功！\n\n` +
      `剩余激活数: ${result.remaining_activations}/${result.max_activations}\n` +
      `可用配额: ${result.available_slots} 个`
    );
    
    // 刷新页面
    window.location.reload();
    
    return result;
  } catch (error) {
    // 错误已在 unbindDevice 中处理
    console.error('解绑失败:', error);
  }
}

// 在按钮中使用
<button onClick={() => quickUnbind(12345, 456, 'MACHINE-ABC123')}>
  解绑设备
</button>
```

### cURL 示例

```bash
curl -X POST "https://backend.espressox.online/api/v1/licenses/member/unbind-device/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "license_id": 12345,
    "machine_binding_id": 456,
    "reason": "更换新电脑"
  }'
```

---

## 🎨 UI/UX 建议

### 1. **确认对话框**
- 显示设备详细信息
- 提供解绑原因输入框（可选）
- 警告提示解绑后的影响
- "取消"和"确认解绑"按钮

### 2. **加载状态**
- 解绑按钮显示 loading 动画
- 防止重复提交
- 禁用其他操作

### 3. **成功反馈**
- 显示成功消息和图标
- 显示剩余激活配额
- 自动刷新设备列表
- 提供"返回"或"关闭"按钮

### 4. **错误处理**
- 在对话框内显示错误消息
- 不同错误提供不同的提示
- 提供重试选项

### 5. **批量解绑（高级功能）**
- 允许选择多个设备
- 批量解绑确认
- 显示批量操作进度

---

## 📝 注意事项

### 1. **权限验证**
- 只能解绑自己拥有的许可证设备
- 后端自动验证 LicenseAssignment 归属
- 租户隔离自动校验

### 2. **设备状态限制**
- 只能解绑状态为 `active` 的设备
- `inactive` 状态表示已解绑，无需重复操作
- `blocked` 状态的设备无法解绑

### 3. **解绑后的变化**
- 设备状态从 `active` 变为 `inactive`
- License.current_activations 减 1
- 可用激活配额增加 1
- 设备记录保留用于审计

### 4. **不可逆操作**
- 解绑后无法直接恢复
- 需要重新激活才能使用
- 建议在确认对话框中明确提示

### 5. **审计日志**
- 所有解绑操作记录到 SecurityAuditLog
- 包含用户ID、IP地址、解绑原因等
- 用于安全审计和故障排查

### 6. **频率限制**
- 受 Member API 通用限制（每小时60次）
- 短时间内大量解绑可能触发安全警告
- 建议合理使用

---

## 🔄 完整业务流程

```
用户在设备列表页面点击"解绑设备"
    ↓
显示确认对话框
  ├─ 显示设备信息
  ├─ 输入解绑原因（可选）
  └─ 警告提示
    ↓
用户确认解绑
    ↓
前端调用 API 5 解绑设备
    ↓
后端验证：
  ├─ 认证和权限
  ├─ 许可证归属
  ├─ 设备归属
  ├─ 设备状态（必须是 active）
  └─ 操作权限
    ↓
执行解绑操作：
  ├─ 更新 MachineBinding.status = 'inactive'
  ├─ 更新 License.current_activations -= 1
  └─ 记录 SecurityAuditLog
    ↓
返回解绑结果
    ↓
前端显示成功消息
    ↓
刷新设备列表
    ↓
用户可以激活新设备
```

---

## 🚀 高级功能建议

### 1. **批量解绑**

```javascript
async function batchUnbindDevices(licenseId, deviceIds, reason = '') {
  const results = [];
  const errors = [];

  for (const deviceId of deviceIds) {
    try {
      const result = await unbindDevice(licenseId, deviceId, reason);
      results.push(result);
    } catch (error) {
      errors.push({ deviceId, error });
    }
  }

  return { 
    success: results,
    failed: errors,
    total: deviceIds.length,
    successCount: results.length,
    failedCount: errors.length
  };
}
```

### 2. **解绑历史记录**

在前端维护解绑历史：
```javascript
const unbindHistory = {
  timestamp: new Date().toISOString(),
  licenseId: 12345,
  deviceId: 456,
  machineName: 'MACHINE-ABC123',
  reason: '更换新电脑'
};

// 保存到 localStorage
const history = JSON.parse(localStorage.getItem('unbind_history') || '[]');
history.unshift(unbindHistory);
localStorage.setItem('unbind_history', JSON.stringify(history.slice(0, 10)));
```

### 3. **撤销解绑（如果需要）**

如果业务需要支持撤销解绑，需要后端提供额外的 API 将设备状态从 `inactive` 改回 `active`。

---

## 📊 测试建议

### 功能测试
- ✅ 正常解绑活跃设备
- ✅ 解绑后激活配额正确更新
- ✅ 重复解绑同一设备（应失败）
- ✅ 解绑不属于自己的设备（应失败）
- ✅ 解绑不存在的设备（应失败）
- ✅ 未认证状态解绑（应失败）

### 错误处理测试
- ✅ 网络错误提示
- ✅ 401 错误跳转登录
- ✅ 400 错误显示友好提示
- ✅ 429 频率限制提示

### UI/UX 测试
- ✅ 确认对话框正确显示
- ✅ 加载状态正常
- ✅ 成功消息显示
- ✅ 设备列表自动刷新

---

[返回文档导航](./README.md) | [上一个API](./API-4-查看许可证的设备列表.md)
