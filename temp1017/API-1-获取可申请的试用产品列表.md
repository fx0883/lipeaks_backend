# API 1: 获取可申请的试用产品列表

## 📌 API 概述

获取当前用户可以申请试用许可证的软件产品列表，仅返回有活跃试用方案的产品。

---

## 🔗 请求信息

- **HTTP Method**: `GET`
- **URL**: `/api/v1/licenses/member/available-products/`
- **完整URL**: `https://backend.espressox.online/api/v1/licenses/member/available-products/`
- **认证**: 必需（JWT Bearer Token）
- **权限要求**: Member 用户
- **频率限制**: 无特殊限制

---

## 📥 请求参数

### 无需任何参数

此 API 不需要任何查询参数或请求体，只需要在请求头中携带有效的 JWT Token。

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
  "data": [
    {
      "id": 1,
      "name": "PDF压缩工具专业版",
      "code": "PDF_COMPRESS_PRO",
      "description": "高效的PDF文件压缩工具，支持批量处理和多种压缩模式",
      "version": "2.0.0",
      "max_activations": 3,
      "offline_days": 7,
      "status": "active",
      "trial_plans": [
        {
          "id": 10,
          "name": "14天试用版",
          "code": "TRIAL_14D",
          "plan_type": "trial",
          "default_max_activations": 2,
          "default_validity_days": 14,
          "features": {
            "max_file_size": "100MB",
            "batch_processing": true,
            "watermark": false,
            "compression_modes": ["standard", "high", "extreme"]
          },
          "status": "active"
        },
        {
          "id": 11,
          "name": "30天试用版",
          "code": "TRIAL_30D",
          "plan_type": "trial",
          "default_max_activations": 3,
          "default_validity_days": 30,
          "features": {
            "max_file_size": "100MB",
            "batch_processing": true,
            "watermark": false,
            "compression_modes": ["standard", "high", "extreme"]
          },
          "status": "active"
        }
      ]
    },
    {
      "id": 2,
      "name": "图片批量处理工具",
      "code": "IMAGE_BATCH_TOOL",
      "description": "支持批量图片压缩、格式转换、水印添加等功能",
      "version": "1.5.0",
      "max_activations": 5,
      "offline_days": 30,
      "status": "active",
      "trial_plans": [
        {
          "id": 20,
          "name": "7天试用版",
          "code": "TRIAL_7D",
          "plan_type": "trial",
          "default_max_activations": 1,
          "default_validity_days": 7,
          "features": {
            "max_images": 100,
            "formats": ["jpg", "png", "webp", "bmp"],
            "batch_size": 50
          },
          "status": "active"
        }
      ]
    }
  ]
}
```

### 📋 响应字段说明

#### 顶层字段
| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | Boolean | 请求是否成功 |
| `data` | Array | 产品数组 |

#### Product (产品) 对象

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer | 产品ID（用于申请许可证） |
| `name` | String | 产品名称 |
| `code` | String | 产品代码（唯一标识符） |
| `description` | String | 产品描述 |
| `version` | String | 当前产品版本号 |
| `max_activations` | Integer | 默认最大激活设备数 |
| `offline_days` | Integer | 离线验证允许天数 |
| `status` | String | 产品状态（`active`=活跃） |
| `trial_plans` | Array | 该产品的试用方案列表 |

#### TrialPlan (试用方案) 对象

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | Integer | 试用方案ID（用于申请许可证） |
| `name` | String | 方案名称 |
| `code` | String | 方案代码 |
| `plan_type` | String | 方案类型（`trial`=试用版） |
| `default_max_activations` | Integer | 该方案允许的最大激活设备数 |
| `default_validity_days` | Integer | 试用有效天数 |
| `features` | Object | 功能特性（JSON对象，各产品不同） |
| `status` | String | 方案状态（`active`=活跃） |

---

## ❌ 错误响应

### 401 Unauthorized - 未认证

```json
{
  "detail": "Authentication credentials were not provided."
}
```

**原因**: 
- 未提供 JWT Token
- Token 格式不正确
- Token 已过期

**处理方式**:
```javascript
// 跳转到登录页面
window.location.href = '/login';
```

### 403 Forbidden - 权限不足

```json
{
  "detail": "You do not have permission to perform this action."
}
```

**原因**:
- 用户不是 Member 类型
- 用户账户被禁用
- 租户账户被禁用

**处理方式**:
```javascript
alert('您没有权限访问此功能');
```

### 500 Internal Server Error

```json
{
  "success": false,
  "error": "服务器内部错误",
  "code": "INTERNAL_ERROR"
}
```

**原因**: 服务器内部错误

**处理方式**:
```javascript
alert('服务暂时不可用，请稍后重试');
```

---

## 💻 前端集成代码

### JavaScript + Axios

```javascript
import axios from 'axios';

/**
 * 获取可申请的试用产品列表
 * @returns {Promise<Array>} 产品数组
 */
async function getAvailableProducts() {
  try {
    const response = await axios.get(
      'https://backend.espressox.online/api/v1/licenses/member/available-products/',
      {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`,
          'Content-Type': 'application/json'
        }
      }
    );

    if (response.data.success) {
      const products = response.data.data;
      console.log(`获取到 ${products.length} 个可用产品`);
      return products;
    } else {
      throw new Error('获取产品列表失败');
    }
  } catch (error) {
    // 错误处理
    if (error.response) {
      const status = error.response.status;
      
      if (status === 401) {
        // Token 无效，跳转登录
        console.error('认证失败，请重新登录');
        localStorage.removeItem('jwt_token');
        window.location.href = '/login';
      } else if (status === 403) {
        console.error('权限不足');
        alert('您没有权限访问此功能');
      } else {
        console.error('请求失败:', error.response.data);
      }
    } else {
      console.error('网络错误:', error.message);
    }
    throw error;
  }
}

// 使用示例
getAvailableProducts()
  .then(products => {
    console.log('产品列表:', products);
    // 渲染产品列表
    renderProducts(products);
  })
  .catch(error => {
    console.error('获取产品失败:', error);
  });
```

### React Hook 实现

```javascript
import { useState, useEffect } from 'react';
import axios from 'axios';

/**
 * 获取可用产品列表的自定义 Hook
 */
function useAvailableProducts() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await axios.get(
          '/api/v1/licenses/member/available-products/',
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`
            }
          }
        );

        if (response.data.success) {
          setProducts(response.data.data);
        }
      } catch (err) {
        const errorMessage = err.response?.data?.detail || '获取产品列表失败';
        setError(errorMessage);
        
        // 401 错误处理
        if (err.response?.status === 401) {
          localStorage.removeItem('jwt_token');
          window.location.href = '/login';
        }
      } finally {
        setLoading(false);
      }
    };

    fetchProducts();
  }, []); // 空依赖数组，仅在组件挂载时执行一次

  return { products, loading, error };
}

// 在组件中使用
function ProductListPage() {
  const { products, loading, error } = useAvailableProducts();

  if (loading) {
    return <div className="loading">加载中...</div>;
  }

  if (error) {
    return <div className="error">错误: {error}</div>;
  }

  if (products.length === 0) {
    return <div className="empty">暂无可申请的试用产品</div>;
  }

  return (
    <div className="product-list">
      <h2>可申请的试用产品</h2>
      {products.map(product => (
        <div key={product.id} className="product-card">
          <h3>{product.name}</h3>
          <p>{product.description}</p>
          <p>版本: {product.version}</p>
          
          <div className="trial-plans">
            <h4>试用方案:</h4>
            {product.trial_plans.map(plan => (
              <div key={plan.id} className="plan-item">
                <span>{plan.name}</span>
                <span>{plan.default_validity_days} 天试用</span>
                <span>最多 {plan.default_max_activations} 台设备</span>
                <button onClick={() => applyTrial(product.id, plan.id)}>
                  申请试用
                </button>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
```

### Vue 3 Composition API

```javascript
import { ref, onMounted } from 'vue';
import axios from 'axios';

export function useAvailableProducts() {
  const products = ref([]);
  const loading = ref(true);
  const error = ref(null);

  const fetchProducts = async () => {
    try {
      loading.value = true;
      error.value = null;

      const response = await axios.get(
        '/api/v1/licenses/member/available-products/',
        {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`
          }
        }
      );

      if (response.data.success) {
        products.value = response.data.data;
      }
    } catch (err) {
      error.value = err.response?.data?.detail || '获取产品列表失败';
      
      if (err.response?.status === 401) {
        localStorage.removeItem('jwt_token');
        window.location.href = '/login';
      }
    } finally {
      loading.value = false;
    }
  };

  onMounted(() => {
    fetchProducts();
  });

  return {
    products,
    loading,
    error,
    refetch: fetchProducts
  };
}
```

### 使用 SWR (推荐)

```javascript
import useSWR from 'swr';
import axios from 'axios';

const fetcher = async (url) => {
  const response = await axios.get(url, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('jwt_token')}`
    }
  });
  return response.data.data; // 直接返回 products 数组
};

function useAvailableProducts() {
  const { data, error, isLoading, mutate } = useSWR(
    '/api/v1/licenses/member/available-products/',
    fetcher,
    {
      revalidateOnFocus: false, // 窗口聚焦时不重新请求
      revalidateOnReconnect: true, // 网络重连时重新请求
      dedupingInterval: 60000, // 60秒内相同请求去重
    }
  );

  return {
    products: data || [],
    loading: isLoading,
    error,
    refresh: mutate // 手动刷新数据
  };
}
```

### cURL 命令示例

```bash
curl -X GET "https://backend.espressox.online/api/v1/licenses/member/available-products/" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMjMsInVzZXJuYW1lIjoidGVzdHVzZXIifQ..." \
  -H "Content-Type: application/json" \
  -H "Accept: application/json"
```

---

## 🎨 UI/UX 建议

### 产品卡片布局

```jsx
<div className="product-card">
  {/* 产品信息 */}
  <div className="product-header">
    <h3>{product.name}</h3>
    <span className="version">v{product.version}</span>
  </div>
  
  <p className="description">{product.description}</p>
  
  {/* 试用方案 */}
  <div className="trial-plans">
    {product.trial_plans.map(plan => (
      <div key={plan.id} className="plan-option">
        <div className="plan-info">
          <strong>{plan.name}</strong>
          <span className="duration">{plan.default_validity_days} 天</span>
          <span className="devices">
            最多 {plan.default_max_activations} 台设备
          </span>
        </div>
        
        {/* 功能特性 */}
        {plan.features && (
          <ul className="features">
            {Object.entries(plan.features).map(([key, value]) => (
              <li key={key}>
                {formatFeature(key, value)}
              </li>
            ))}
          </ul>
        )}
        
        <button 
          className="btn-apply"
          onClick={() => handleApply(product.id, plan.id)}
        >
          申请试用
        </button>
      </div>
    ))}
  </div>
</div>
```

### 空状态显示

```jsx
{products.length === 0 && (
  <div className="empty-state">
    <img src="/images/empty-products.svg" alt="暂无产品" />
    <h3>暂无可申请的试用产品</h3>
    <p>请联系管理员添加产品</p>
  </div>
)}
```

---

## 📝 注意事项

### 1. **产品过滤**
- API 只返回当前用户所属租户的产品
- 只显示状态为 `active` 的产品
- 只包含有活跃试用方案的产品

### 2. **试用方案选择**
- 一个产品可能有多个试用方案（如7天、14天、30天）
- 不同方案的激活设备数和功能可能不同
- 让用户选择最适合的方案

### 3. **数据缓存**
- 建议缓存 5-10 分钟，减少服务器压力
- 使用 SWR、React Query 等工具管理缓存
- 提供手动刷新按钮

### 4. **错误处理**
- 401: 清除 Token，跳转登录页
- 403: 显示权限不足提示
- 500: 显示服务错误，提供重试按钮
- 网络错误: 显示网络异常提示

### 5. **加载状态**
- 首次加载显示 skeleton 或 loading 动画
- 刷新时显示轻量级 loading 提示
- 避免页面闪烁

### 6. **功能特性展示**
- `features` 字段是动态的 JSON 对象
- 不同产品的 features 结构可能不同
- 需要灵活处理和渲染

---

## 🔄 完整业务流程

```
1. 用户登录系统
   ↓
2. 访问产品列表页面
   ↓
3. 前端调用 API 获取可用产品
   ↓
4. 后端验证用户身份和权限
   ↓
5. 返回该租户下的活跃产品
   ↓
6. 前端渲染产品卡片
   ↓
7. 用户浏览产品和试用方案
   ↓
8. 用户点击"申请试用"
   ↓
9. 进入下一步：申请试用许可证（API 2）
```

---

## 🚀 性能优化建议

### 1. 数据缓存
```javascript
// 使用 SWR 自动缓存和重新验证
const { data: products } = useSWR(
  '/api/v1/licenses/member/available-products/',
  fetcher,
  {
    dedupingInterval: 300000, // 5分钟内去重
    focusThrottleInterval: 300000 // 5分钟内窗口聚焦不重新请求
  }
);
```

### 2. 图片懒加载
```jsx
<img 
  src={product.icon} 
  loading="lazy"
  alt={product.name}
/>
```

### 3. 虚拟滚动
如果产品数量很多（>50个），考虑使用虚拟滚动：
```javascript
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={600}
  itemCount={products.length}
  itemSize={200}
>
  {({ index, style }) => (
    <div style={style}>
      <ProductCard product={products[index]} />
    </div>
  )}
</FixedSizeList>
```

---

[返回文档导航](./README.md)
