# 获取可申请产品列表 API

本文档详细说明获取可申请试用产品列表的API接口。

---

## API概述

### 基本信息

```
GET /api/v1/licenses/member/available-products/
```

**功能**：获取当前Member用户可以申请试用许可证的产品列表

**权限要求**：
- 需要JWT认证
- 必须是Member用户身份
- 用户和租户状态必须为活跃

**频率限制**：100次/小时

**内容类型**：`application/json`

---

## 请求说明

### 请求头

```http
Authorization: Bearer <access_token>
```

### 查询参数

无需查询参数，系统会自动根据当前用户返回可申请的产品。

### 请求示例

#### HTTP请求

```http
GET /api/v1/licenses/member/available-products/ HTTP/1.1
Host: localhost:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### cURL

```bash
curl -X GET "http://localhost:8000/api/v1/licenses/member/available-products/" \
  -H "Authorization: Bearer <your_token>"
```

#### JavaScript/Axios

```javascript
const response = await axios.get(
  'http://localhost:8000/api/v1/licenses/member/available-products/',
  {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`
    }
  }
);

console.log(response.data);
```

---

## 响应说明

### 成功响应

**状态码**：`200 OK`

**响应体**：

```json
{
  "success": true,
  "data": {
    "count": 3,
    "products": [
      {
        "id": 1,
        "name": "PDF压缩工具",
        "code": "pdf_compress",
        "description": "高效的PDF文件压缩工具，支持批量处理",
        "version": "1.2.0",
        "trial_plan": {
          "id": 10,
          "name": "试用版",
          "default_validity_days": 30,
          "default_max_activations": 1,
          "features": {
            "compression_level": "basic",
            "batch_processing": true,
            "max_file_size_mb": 10
          },
          "price": 0.0,
          "currency": "CNY"
        },
        "already_applied": false
      },
      {
        "id": 2,
        "name": "图片处理工具",
        "code": "image_editor",
        "description": "专业的图片编辑和处理工具",
        "version": "2.0.1",
        "trial_plan": {
          "id": 11,
          "name": "免费试用",
          "default_validity_days": 15,
          "default_max_activations": 2,
          "features": {
            "filters": ["basic", "blur", "sharpen"],
            "export_formats": ["jpg", "png"]
          },
          "price": 0.0,
          "currency": "CNY"
        },
        "already_applied": true
      },
      {
        "id": 3,
        "name": "视频转换工具",
        "code": "video_converter",
        "description": "快速视频格式转换工具",
        "version": "3.1.0",
        "trial_plan": {
          "id": 12,
          "name": "体验版",
          "default_validity_days": 7,
          "default_max_activations": 1,
          "features": {
            "output_formats": ["mp4", "avi"],
            "max_duration_minutes": 5
          },
          "price": 0.0,
          "currency": "CNY"
        },
        "already_applied": false
      }
    ]
  }
}
```

### 响应字段说明

#### 顶层字段

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 请求是否成功 |
| data | object | 响应数据对象 |

#### data对象

| 字段 | 类型 | 说明 |
|------|------|------|
| count | integer | 可申请产品总数 |
| products | array | 产品对象数组 |

#### Product对象

| 字段 | 类型 | 必有 | 说明 |
|------|------|------|------|
| id | integer | ✅ | 产品ID，申请时需要提供 |
| name | string | ✅ | 产品名称 |
| code | string | ✅ | 产品代码，用于标识 |
| description | string | ✅ | 产品描述 |
| version | string | ✅ | 产品版本号 |
| trial_plan | object\|null | ✅ | 试用方案信息，null表示无试用方案 |
| already_applied | boolean | ✅ | 是否已申请过该产品 |

#### TrialPlan对象

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 试用方案ID |
| name | string | 方案名称（如"试用版"、"免费试用"） |
| default_validity_days | integer | 默认有效期（天数） |
| default_max_activations | integer | 默认最大激活设备数 |
| features | object | 功能配置（JSON对象） |
| price | number | 价格（试用版为0.0） |
| currency | string | 货币单位（如"CNY"、"USD"） |

---

## 错误响应

### 401 未认证

```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 权限不足

```json
{
  "detail": "You do not have permission to perform this action."
}
```

**原因**：
- 用户不是Member身份（可能是管理员）
- 用户状态不是活跃
- 租户状态不是活跃

### 500 服务器内部错误

```json
{
  "success": false,
  "error": "获取产品列表失败，请稍后重试",
  "code": "FETCH_PRODUCTS_FAILED"
}
```

---

## 前端实现示例

### Vue 3 完整示例

```vue
<template>
  <div class="available-products">
    <el-page-header @back="goBack" title="返回">
      <template #content>
        <span class="page-title">试用产品列表</span>
      </template>
    </el-page-header>
    
    <!-- Loading状态 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="3" animated />
    </div>
    
    <!-- 产品列表 -->
    <div v-else class="products-grid">
      <el-empty v-if="products.length === 0" description="暂无可申请的试用产品" />
      
      <el-card
        v-for="product in products"
        :key="product.id"
        class="product-card"
        :class="{ 'applied': product.already_applied }"
      >
        <template #header>
          <div class="card-header">
            <span class="product-name">{{ product.name }}</span>
            <el-tag v-if="product.already_applied" type="success">
              已申请
            </el-tag>
          </div>
        </template>
        
        <!-- 产品信息 -->
        <div class="product-info">
          <p class="version">版本：{{ product.version }}</p>
          <p class="description">{{ product.description }}</p>
          
          <!-- 试用方案信息 -->
          <div v-if="product.trial_plan" class="trial-info">
            <el-divider />
            <h4>试用方案</h4>
            <ul>
              <li>
                <el-icon><Clock /></el-icon>
                有效期：{{ product.trial_plan.default_validity_days }} 天
              </li>
              <li>
                <el-icon><Monitor /></el-icon>
                可激活设备：{{ product.trial_plan.default_max_activations }} 个
              </li>
              <li v-if="product.trial_plan.features">
                <el-icon><Star /></el-icon>
                功能特性：
                <el-tag
                  v-for="(value, key) in product.trial_plan.features"
                  :key="key"
                  size="small"
                  style="margin-left: 5px;"
                >
                  {{ key }}: {{ value }}
                </el-tag>
              </li>
            </ul>
          </div>
        </div>
        
        <!-- 操作按钮 -->
        <template #footer>
          <el-button
            type="primary"
            :disabled="product.already_applied || !product.trial_plan"
            @click="handleApply(product)"
            style="width: 100%;"
          >
            {{ product.already_applied ? '已申请' : '申请试用' }}
          </el-button>
        </template>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage } from 'element-plus';
import { Clock, Monitor, Star } from '@element-plus/icons-vue';
import axios from 'axios';

const router = useRouter();

// 数据
const loading = ref(false);
const products = ref([]);

// 获取可申请产品列表
const fetchProducts = async () => {
  loading.value = true;
  try {
    const response = await axios.get('/api/v1/licenses/member/available-products/');
    
    if (response.data.success) {
      products.value = response.data.data.products;
      
      if (products.value.length === 0) {
        ElMessage.info('暂无可申请的试用产品');
      }
    }
  } catch (error) {
    console.error('获取产品列表失败:', error);
    
    if (error.response) {
      const { status, data } = error.response;
      
      if (status === 401) {
        ElMessage.error('登录已过期，请重新登录');
        router.push('/login');
      } else if (status === 403) {
        ElMessage.error('权限不足，此功能仅限Member用户使用');
      } else {
        ElMessage.error(data.error || '获取产品列表失败');
      }
    } else {
      ElMessage.error('网络连接失败，请检查网络设置');
    }
  } finally {
    loading.value = false;
  }
};

// 申请产品
const handleApply = (product) => {
  router.push({
    name: 'ApplyLicense',
    params: { productId: product.id },
    query: { productName: product.name }
  });
};

// 返回
const goBack = () => {
  router.back();
};

// 组件挂载时获取数据
onMounted(() => {
  fetchProducts();
});
</script>

<style scoped>
.available-products {
  padding: 20px;
}

.page-title {
  font-size: 18px;
  font-weight: 600;
}

.loading-container {
  padding: 40px 0;
}

.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
  margin-top: 20px;
}

.product-card {
  transition: all 0.3s;
}

.product-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.product-card.applied {
  background-color: #f5f7fa;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.product-name {
  font-size: 16px;
  font-weight: 600;
}

.product-info .version {
  color: #909399;
  font-size: 12px;
  margin: 0 0 10px 0;
}

.product-info .description {
  margin: 0 0 15px 0;
  line-height: 1.6;
}

.trial-info h4 {
  margin: 10px 0;
  font-size: 14px;
  color: #606266;
}

.trial-info ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.trial-info li {
  display: flex;
  align-items: center;
  margin: 8px 0;
  font-size: 14px;
  color: #606266;
}

.trial-info li .el-icon {
  margin-right: 8px;
  color: #409EFF;
}
</style>
```

### React 示例 (使用 Ant Design)

```jsx
import React, { useState, useEffect } from 'react';
import { Card, Tag, Button, Empty, Spin, message, Row, Col, Divider } from 'antd';
import { ClockCircleOutlined, LaptopOutlined, StarOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const { Meta } = Card;

const AvailableProducts = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [products, setProducts] = useState([]);

  // 获取产品列表
  const fetchProducts = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/v1/licenses/member/available-products/');
      
      if (response.data.success) {
        setProducts(response.data.data.products);
        
        if (response.data.data.products.length === 0) {
          message.info('暂无可申请的试用产品');
        }
      }
    } catch (error) {
      console.error('获取产品列表失败:', error);
      
      if (error.response) {
        const { status, data } = error.response;
        
        if (status === 401) {
          message.error('登录已过期，请重新登录');
          navigate('/login');
        } else if (status === 403) {
          message.error('权限不足');
        } else {
          message.error(data.error || '获取产品列表失败');
        }
      } else {
        message.error('网络连接失败');
      }
    } finally {
      setLoading(false);
    }
  };

  // 申请产品
  const handleApply = (product) => {
    navigate(`/member/apply-license/${product.id}`, {
      state: { productName: product.name }
    });
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px 0' }}>
        <Spin size="large" tip="加载中..." />
      </div>
    );
  }

  return (
    <div style={{ padding: '20px' }}>
      <h2>试用产品列表</h2>
      
      {products.length === 0 ? (
        <Empty description="暂无可申请的试用产品" />
      ) : (
        <Row gutter={[16, 16]}>
          {products.map(product => (
            <Col xs={24} sm={12} md={8} key={product.id}>
              <Card
                title={
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span>{product.name}</span>
                    {product.already_applied && (
                      <Tag color="success">已申请</Tag>
                    )}
                  </div>
                }
                extra={<Tag>{product.version}</Tag>}
                actions={[
                  <Button
                    type="primary"
                    disabled={product.already_applied || !product.trial_plan}
                    onClick={() => handleApply(product)}
                    block
                  >
                    {product.already_applied ? '已申请' : '申请试用'}
                  </Button>
                ]}
              >
                <p>{product.description}</p>
                
                {product.trial_plan && (
                  <>
                    <Divider />
                    <div>
                      <h4>试用方案</h4>
                      <p>
                        <ClockCircleOutlined /> 
                        有效期：{product.trial_plan.default_validity_days} 天
                      </p>
                      <p>
                        <LaptopOutlined /> 
                        可激活设备：{product.trial_plan.default_max_activations} 个
                      </p>
                      {product.trial_plan.features && (
                        <p>
                          <StarOutlined /> 
                          功能：
                          {Object.entries(product.trial_plan.features).map(([key, value]) => (
                            <Tag key={key} size="small" style={{ marginLeft: 4 }}>
                              {key}: {JSON.stringify(value)}
                            </Tag>
                          ))}
                        </p>
                      )}
                    </div>
                  </>
                )}
              </Card>
            </Col>
          ))}
        </Row>
      )}
    </div>
  );
};

export default AvailableProducts;
```

---

## 使用场景

### 1. 产品浏览页面

展示所有可申请的试用产品，用户可以浏览和选择：

```javascript
// 页面加载时获取产品列表
async function loadProducts() {
  const response = await axios.get('/api/v1/licenses/member/available-products/');
  return response.data.data.products;
}
```

### 2. 产品选择器

在申请流程中，让用户选择要申请的产品：

```vue
<el-select v-model="selectedProductId" placeholder="选择产品">
  <el-option
    v-for="product in availableProducts"
    :key="product.id"
    :label="product.name"
    :value="product.id"
    :disabled="product.already_applied"
  >
    <span>{{ product.name }}</span>
    <span style="float: right; color: #8492a6; font-size: 13px;">
      {{ product.trial_plan?.default_validity_days }}天试用
    </span>
  </el-option>
</el-select>
```

### 3. 产品详情展示

展开产品的详细信息和试用方案：

```javascript
function renderProductDetail(product) {
  return `
    <h3>${product.name} v${product.version}</h3>
    <p>${product.description}</p>
    
    ${product.trial_plan ? `
      <h4>试用方案</h4>
      <ul>
        <li>有效期：${product.trial_plan.default_validity_days}天</li>
        <li>可激活设备：${product.trial_plan.default_max_activations}个</li>
        <li>功能配置：${JSON.stringify(product.trial_plan.features, null, 2)}</li>
      </ul>
    ` : '<p>该产品暂无试用方案</p>'}
    
    ${!product.already_applied && product.trial_plan ? `
      <button onclick="applyProduct(${product.id})">立即申请</button>
    ` : '<button disabled>已申请</button>'}
  `;
}
```

---

## 前端开发建议

### 功能清单

- [x] 获取产品列表
- [x] 显示产品信息（名称、描述、版本）
- [x] 显示试用方案信息（有效期、激活数、功能）
- [x] 标记已申请状态
- [x] 禁用已申请产品的申请按钮
- [x] Loading状态
- [x] 空状态处理
- [x] 错误处理

### UI/UX建议

1. **卡片布局**：使用卡片展示产品，响应式网格布局
2. **视觉区分**：已申请的产品用不同颜色或样式区分
3. **信息突出**：试用天数和激活数用醒目方式展示
4. **引导操作**：明确的"申请试用"按钮

### 性能优化

```javascript
// 1. 缓存产品列表（5分钟）
const CACHE_KEY = 'available_products';
const CACHE_DURATION = 5 * 60 * 1000;

function getCachedProducts() {
  const cached = localStorage.getItem(CACHE_KEY);
  if (cached) {
    const { data, timestamp } = JSON.parse(cached);
    if (Date.now() - timestamp < CACHE_DURATION) {
      return data;
    }
  }
  return null;
}

function setCachedProducts(data) {
  localStorage.setItem(CACHE_KEY, JSON.stringify({
    data,
    timestamp: Date.now()
  }));
}

// 2. 使用时先检查缓存
async function getProducts() {
  const cached = getCachedProducts();
  if (cached) {
    return cached;
  }
  
  const response = await axios.get('/api/v1/licenses/member/available-products/');
  const products = response.data.data.products;
  setCachedProducts(products);
  
  return products;
}
```

---

## 下一步

继续阅读：

📙 **apply_license_api.md** - 申请试用许可证API

