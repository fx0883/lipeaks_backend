# API 3: 查看我的许可证

## 📌 API 概述

获取当前用户拥有的所有许可证列表，包括许可证状态、激活情况、过期时间等详细信息。

---

## 🔗 请求信息

- **HTTP Method**: `GET`
- **URL**: `/api/v1/licenses/member/my-licenses/`
- **完整URL**: `https://backend.espressox.online/api/v1/licenses/member/my-licenses/`
- **认证**: 必需（JWT Bearer Token）
- **权限要求**: Member 用户
- **频率限制**: 无特殊限制

---

## 📥 请求参数

### 无需任何参数

此 API 不需要任何查询参数或请求体。

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
  "data": {
    "count": 3,
    "active_count": 2,
    "trial_count": 2,
    "expiring_soon_count": 1,
    "licenses": [
      {
        "id": 12345,
        "assignment_id": 67890,
        "product_name": "PDF压缩工具专业版",
        "product_id": 1,
        "plan_name": "14天试用版",
        "plan_type": "trial",
        "license_key": "ABCDE-12345-FGHIJ-67890-KLMNO",
        "max_activations": 2,
        "current_activations": 1,
        "available_activations": 1,
        "status": "active",
        "assignment_status": "active",
        "issued_at": "2024-01-15T10:30:00Z",
        "expires_at": "2024-01-29T10:30:00Z",
        "days_until_expiry": 5,
        "is_expired": false,
        "is_expiring_soon": true,
        "can_activate": true,
        "can_deactivate": true,
        "assignment_reason": "试用版申请",
        "created_at": "2024-01-15T10:30:00Z"
      },
      {
        "id": 12346,
        "assignment_id": 67891,
        "product_name": "图片批量处理工具",
        "product_id": 2,
        "plan_name": "30天试用版",
        "plan_type": "trial",
        "license_key": "PQRST-67890-UVWXY-12345-ZABCD",
        "max_activations": 3,
        "current_activations": 0,
        "available_activations": 3,
        "status": "active",
        "assignment_status": "active",
        "issued_at": "2024-01-10T14:20:00Z",
        "expires_at": "2024-02-09T14:20:00Z",
        "days_until_expiry": 20,
        "is_expired": false,
        "is_expiring_soon": false,
        "can_activate": true,
        "can_deactivate": true,
        "assignment_reason": "试用版申请",
        "created_at": "2024-01-10T14:20:00Z"
      },
      {
        "id": 12347,
        "assignment_id": 67892,
        "product_name": "PDF压缩工具专业版",
        "product_id": 1,
        "plan_name": "专业版",
        "plan_type": "paid",
        "license_key": "GHIJK-54321-LMNOP-98765-QRSTU",
        "max_activations": 5,
        "current_activations": 3,
        "available_activations": 2,
        "status": "active",
        "assignment_status": "expired",
        "issued_at": "2023-12-01T09:00:00Z",
        "expires_at": "2024-01-01T09:00:00Z",
        "days_until_expiry": -19,
        "is_expired": true,
        "is_expiring_soon": false,
        "can_activate": false,
        "can_deactivate": false,
        "assignment_reason": "购买专业版",
        "created_at": "2023-12-01T09:00:00Z"
      }
    ]
  }
}
```

### 📋 响应字段说明

#### 统计信息字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `count` | Integer | 许可证总数 |
| `active_count` | Integer | 有效许可证数量（状态为 active） |
| `trial_count` | Integer | 试用版许可证数量 |
| `expiring_soon_count` | Integer | 即将过期的许可证数量（7天内） |

#### 许可证对象字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer | 许可证ID |
| `assignment_id` | Integer | 分配记录ID |
| `product_name` | String | 产品名称 |
| `product_id` | Integer | 产品ID |
| `plan_name` | String | 方案名称 |
| `plan_type` | String | 方案类型（`trial`=试用版, `paid`=付费版） |
| `license_key` | String | 许可证密钥 |
| `max_activations` | Integer | 最大可激活设备数 |
| `current_activations` | Integer | 当前已激活设备数 |
| `available_activations` | Integer | 剩余可激活设备数 |
| `status` | String | 许可证状态（`active`=活跃, `expired`=已过期, `blocked`=已阻止） |
| `assignment_status` | String | 分配状态（`active`=活跃, `expired`=已过期, `revoked`=已撤销） |
| `issued_at` | String (ISO 8601) | 许可证签发时间 |
| `expires_at` | String (ISO 8601) | 许可证过期时间 |
| `days_until_expiry` | Integer | 距离过期天数（负数表示已过期） |
| `is_expired` | Boolean | 是否已过期 |
| `is_expiring_soon` | Boolean | 是否即将过期（7天内） |
| `can_activate` | Boolean | 是否可以激活新设备 |
| `can_deactivate` | Boolean | 是否可以解绑设备 |
| `assignment_reason` | String | 分配原因 |
| `created_at` | String (ISO 8601) | 分配创建时间 |

---

## ❌ 错误响应

### 401 Unauthorized

```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden

```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 500 Internal Server Error

```json
{
  "success": false,
  "error": "获取许可证列表失败，请稍后重试",
  "code": "FETCH_LICENSES_FAILED"
}
```

---

## 💻 前端集成代码

### JavaScript + Axios

```javascript
import axios from 'axios';

/**
 * 获取我的许可证列表
 * @returns {Promise<object>} 许可证列表和统计信息
 */
async function getMyLicenses() {
  try {
    const response = await axios.get(
      '/api/v1/licenses/member/my-licenses/',
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`
        }
      }
    );

    if (response.data.success) {
      const data = response.data.data;
      console.log(`共有 ${data.count} 个许可证，其中 ${data.active_count} 个有效`);
      return data;
    }
  } catch (error) {
    if (error.response?.status === 401) {
      localStorage.removeItem('jwt_token');
      window.location.href = '/login';
    } else {
      console.error('获取许可证列表失败:', error);
      throw error;
    }
  }
}

// 使用示例
getMyLicenses().then(data => {
  console.log('许可证统计:', {
    总数: data.count,
    有效: data.active_count,
    试用版: data.trial_count,
    即将过期: data.expiring_soon_count
  });
  
  // 遍历许可证
  data.licenses.forEach(license => {
    console.log(`${license.product_name} - ${license.plan_name}`);
    console.log(`  状态: ${license.status}`);
    console.log(`  激活: ${license.current_activations}/${license.max_activations}`);
    console.log(`  过期: ${license.days_until_expiry} 天后`);
  });
});
```

### React Hook

```javascript
import { useState, useEffect } from 'react';
import axios from 'axios';

function useMyLicenses() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchLicenses = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await axios.get(
        '/api/v1/licenses/member/my-licenses/',
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
      setError(err.response?.data?.error || '获取许可证失败');
      
      if (err.response?.status === 401) {
        localStorage.removeItem('jwt_token');
        window.location.href = '/login';
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLicenses();
  }, []);

  return { 
    licenses: data?.licenses || [], 
    statistics: {
      count: data?.count || 0,
      activeCount: data?.active_count || 0,
      trialCount: data?.trial_count || 0,
      expiringSoonCount: data?.expiring_soon_count || 0
    },
    loading, 
    error,
    refresh: fetchLicenses 
  };
}

// 许可证列表组件
function MyLicensesPage() {
  const { licenses, statistics, loading, error, refresh } = useMyLicenses();
  const [copiedId, setCopiedId] = useState(null);

  const copyLicenseKey = (licenseId, licenseKey) => {
    navigator.clipboard.writeText(licenseKey).then(() => {
      setCopiedId(licenseId);
      setTimeout(() => setCopiedId(null), 2000);
    });
  };

  const getLicenseStatusBadge = (license) => {
    if (license.is_expired) {
      return <span className="badge badge-error">已过期</span>;
    }
    if (license.is_expiring_soon) {
      return <span className="badge badge-warning">即将过期</span>;
    }
    if (license.status === 'active') {
      return <span className="badge badge-success">活跃</span>;
    }
    return <span className="badge badge-gray">{license.status}</span>;
  };

  if (loading) {
    return <div className="loading-container">
      <div className="spinner"></div>
      <p>加载中...</p>
    </div>;
  }

  if (error) {
    return <div className="error-container">
      <p>❌ {error}</p>
      <button onClick={refresh}>重试</button>
    </div>;
  }

  return (
    <div className="my-licenses-page">
      {/* 统计卡片 */}
      <div className="statistics-cards">
        <div className="stat-card">
          <div className="stat-value">{statistics.count}</div>
          <div className="stat-label">总许可证</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{statistics.activeCount}</div>
          <div className="stat-label">有效</div>
        </div>
        <div className="stat-card">
          <div className="stat-value">{statistics.trialCount}</div>
          <div className="stat-label">试用版</div>
        </div>
        <div className="stat-card">
          <div className="stat-value warn">{statistics.expiringSoonCount}</div>
          <div className="stat-label">即将过期</div>
        </div>
      </div>

      {/* 许可证列表 */}
      <div className="licenses-list">
        <div className="list-header">
          <h2>我的许可证</h2>
          <button onClick={refresh} className="btn-refresh">
            🔄 刷新
          </button>
        </div>

        {licenses.length === 0 ? (
          <div className="empty-state">
            <p>您还没有任何许可证</p>
            <button onClick={() => window.location.href = '/products'}>
              申请试用许可证
            </button>
          </div>
        ) : (
          licenses.map(license => (
            <div key={license.id} className="license-card">
              <div className="license-header">
                <div className="product-info">
                  <h3>{license.product_name}</h3>
                  <span className="plan-badge">{license.plan_name}</span>
                </div>
                {getLicenseStatusBadge(license)}
              </div>

              <div className="license-details">
                <div className="detail-row">
                  <label>许可证密钥:</label>
                  <div className="license-key-group">
                    <code className="license-key">{license.license_key}</code>
                    <button 
                      onClick={() => copyLicenseKey(license.id, license.license_key)}
                      className="btn-copy"
                    >
                      {copiedId === license.id ? '✓ 已复制' : '📋 复制'}
                    </button>
                  </div>
                </div>

                <div className="detail-row">
                  <label>设备激活:</label>
                  <span>
                    {license.current_activations} / {license.max_activations} 台设备
                    {license.available_activations > 0 && (
                      <span className="text-success">
                        {' '}(还可激活 {license.available_activations} 台)
                      </span>
                    )}
                  </span>
                </div>

                <div className="detail-row">
                  <label>签发时间:</label>
                  <span>{new Date(license.issued_at).toLocaleString('zh-CN')}</span>
                </div>

                <div className="detail-row">
                  <label>过期时间:</label>
                  <span className={license.is_expired ? 'text-error' : license.is_expiring_soon ? 'text-warning' : ''}>
                    {new Date(license.expires_at).toLocaleString('zh-CN')}
                    {!license.is_expired && (
                      <span className="days-left">
                        {' '}({license.days_until_expiry} 天后过期)
                      </span>
                    )}
                    {license.is_expired && (
                      <span className="expired-text"> (已过期)</span>
                    )}
                  </span>
                </div>
              </div>

              <div className="license-actions">
                {license.can_activate && license.current_activations > 0 && (
                  <button 
                    onClick={() => window.location.href = `/licenses/${license.id}/devices`}
                    className="btn btn-secondary"
                  >
                    📱 管理设备 ({license.current_activations})
                  </button>
                )}
                
                {!license.can_activate && (
                  <button className="btn btn-disabled" disabled>
                    无法激活新设备
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
```

### 过滤和排序功能

```javascript
function MyLicensesWithFilter() {
  const { licenses, loading, error } = useMyLicenses();
  const [filter, setFilter] = useState('all'); // all, active, expired, expiring
  const [sortBy, setSortBy] = useState('created_at'); // created_at, expires_at, product_name

  // 过滤许可证
  const filteredLicenses = licenses.filter(license => {
    switch (filter) {
      case 'active':
        return license.status === 'active' && !license.is_expired;
      case 'expired':
        return license.is_expired;
      case 'expiring':
        return license.is_expiring_soon && !license.is_expired;
      default:
        return true;
    }
  });

  // 排序许可证
  const sortedLicenses = [...filteredLicenses].sort((a, b) => {
    switch (sortBy) {
      case 'expires_at':
        return new Date(a.expires_at) - new Date(b.expires_at);
      case 'product_name':
        return a.product_name.localeCompare(b.product_name);
      case 'created_at':
      default:
        return new Date(b.created_at) - new Date(a.created_at);
    }
  });

  return (
    <div>
      {/* 过滤和排序控件 */}
      <div className="filter-controls">
        <div className="filter-buttons">
          <button 
            className={filter === 'all' ? 'active' : ''}
            onClick={() => setFilter('all')}
          >
            全部 ({licenses.length})
          </button>
          <button 
            className={filter === 'active' ? 'active' : ''}
            onClick={() => setFilter('active')}
          >
            有效 ({licenses.filter(l => l.status === 'active' && !l.is_expired).length})
          </button>
          <button 
            className={filter === 'expiring' ? 'active' : ''}
            onClick={() => setFilter('expiring')}
          >
            即将过期 ({licenses.filter(l => l.is_expiring_soon && !l.is_expired).length})
          </button>
          <button 
            className={filter === 'expired' ? 'active' : ''}
            onClick={() => setFilter('expired')}
          >
            已过期 ({licenses.filter(l => l.is_expired).length})
          </button>
        </div>

        <select 
          value={sortBy} 
          onChange={(e) => setSortBy(e.target.value)}
          className="sort-select"
        >
          <option value="created_at">按创建时间</option>
          <option value="expires_at">按过期时间</option>
          <option value="product_name">按产品名称</option>
        </select>
      </div>

      {/* 许可证列表 */}
      <div className="licenses-list">
        {sortedLicenses.map(license => (
          <LicenseCard key={license.id} license={license} />
        ))}
      </div>
    </div>
  );
}
```

### cURL 示例

```bash
curl -X GET "https://backend.espressox.online/api/v1/licenses/member/my-licenses/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Accept: application/json"
```

---

## 🎨 UI/UX 建议

### 1. **统计概览**
在页面顶部显示统计卡片：
- 总许可证数
- 有效许可证数
- 试用版许可证数
- 即将过期数量（用醒目颜色提示）

### 2. **许可证卡片**
每个许可证显示为一张卡片，包含：
- 产品名称和方案名称
- 状态徽章（活跃/过期/即将过期）
- 许可证密钥（可复制）
- 设备激活情况
- 过期时间（醒目显示剩余天数）
- 操作按钮（管理设备）

### 3. **状态标识**
- 🟢 活跃：绿色徽章
- 🟡 即将过期：黄色徽章，剩余天数<7
- 🔴 已过期：红色徽章
- ⚫ 已阻止：灰色徽章

### 4. **交互功能**
- 许可证密钥一键复制
- 点击卡片展开更多详情
- 筛选器：全部/有效/即将过期/已过期
- 排序：按创建时间/过期时间/产品名称

### 5. **空状态**
如果没有许可证，显示友好的空状态页面：
- 提示文字："您还没有任何许可证"
- 引导按钮："申请试用许可证"

---

## 📝 注意事项

### 1. **数据刷新**
- 建议缓存 1-2 分钟
- 提供手动刷新按钮
- 从设备管理页返回时自动刷新

### 2. **过期提醒**
- 许可证即将过期（7天内）显示警告
- 建议在页面顶部显示过期提醒横幅
- 可发送邮件提醒（后端处理）

### 3. **激活配额**
- 清晰显示已用/总计设备数
- 如果配额用完，提示用户解绑设备
- 提供快速跳转到设备管理页的链接

### 4. **许可证类型**
- `plan_type`: `trial` 为试用版，`paid` 为付费版
- 可根据类型显示不同的图标或颜色

### 5. **性能优化**
- 如果许可证很多，考虑分页或虚拟滚动
- 懒加载许可证详情
- 使用 React.memo 优化组件渲染

---

## 🔄 业务流程

```
用户访问"我的许可证"页面
    ↓
前端调用 API 获取许可证列表
    ↓
后端验证用户身份
    ↓
查询用户的 LicenseAssignment 记录
    ↓
返回许可证列表和统计信息
    ↓
前端渲染许可证卡片
    ↓
用户可以:
  ├─ 复制许可证密钥
  ├─ 查看设备激活情况
  ├─ 点击"管理设备"查看详情（API 4）
  └─ 解绑不用的设备（API 5）
```

---

[返回文档导航](./README.md) | [上一个API](./API-2-申请试用许可证.md) | [下一个API](./API-4-查看许可证的设备列表.md)
