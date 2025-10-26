# Software Management API 前端使用文档

## 📚 文档概述

本文档集提供Software Management（软件管理）相关API的详细使用说明，包括完整的输入参数、输出格式和使用示例。

**适用项目**: Vue 3  
**文档数量**: 5个  
**API总数**: 20个

---

## 📖 文档列表

### API使用文档

| 文档 | API数量 | 主要内容 |
|------|---------|---------|
| [01_软件分类API使用文档.md](01_软件分类API使用文档.md) | 6个 | 分类的增删改查 |
| [02_软件产品API使用文档.md](02_软件产品API使用文档.md) | 8个 | 软件产品管理、版本添加 |
| [03_软件版本API使用文档.md](03_软件版本API使用文档.md) | 6个 | 版本的创建、查询、更新、删除 |

### 辅助文档

| 文档 | 主要内容 |
|------|---------|
| [常见问题与解决方案.md](常见问题与解决方案.md) | 错误排查、最佳实践、前端工具函数 |
| [序列化器改进说明.md](序列化器改进说明.md) | 外键信息自动关联、性能优化说明 |

---

## 🚀 快速开始

### API基础信息

**基础URL**: `http://your-domain.com/api/v1/feedbacks`

**认证方式**: JWT Bearer Token

**请求头配置**:
```
Authorization: Bearer {your_token}
Content-Type: application/json
```

### 数据流程

```
软件分类 (Category)
    ↓ 一对多
软件产品 (Software)
    ↓ 一对多
软件版本 (Version)
    ↓ 一对多
用户反馈 (Feedback)
```

---

## 📊 API 概览

### 软件分类 (6个API)

```bash
GET    /software-categories/              # 获取分类列表
POST   /software-categories/              # 创建分类
GET    /software-categories/{id}/         # 获取详情
PUT    /software-categories/{id}/         # 完整更新
PATCH  /software-categories/{id}/         # 部分更新
DELETE /software-categories/{id}/         # 删除
```

### 软件产品 (8个API)

```bash
GET    /software/                         # 获取软件列表
POST   /software/                         # 创建软件
GET    /software/{id}/                    # 获取详情
PUT    /software/{id}/                    # 完整更新
PATCH  /software/{id}/                    # 部分更新
DELETE /software/{id}/                    # 删除
GET    /software/{id}/versions/           # 获取软件的版本列表
POST   /software/{id}/versions/           # 为软件添加版本
```

### 软件版本 (6个API)

```bash
POST   /software/{id}/versions/           # 创建版本（嵌套路由）
GET    /software-versions/                # 获取所有版本
GET    /software-versions/{id}/           # 获取版本详情
PUT    /software-versions/{id}/           # 完整更新
PATCH  /software-versions/{id}/           # 部分更新
DELETE /software-versions/{id}/           # 删除
```

---

## 🔐 权限说明

| 操作 | 超级管理员 | 租户管理员 | 普通用户 |
|------|-----------|-----------|---------|
| 查看分类/软件/版本 | ✅ | ✅ | ✅ |
| 创建分类/软件/版本 | ❌ | ✅ | ❌ |
| 修改分类/软件/版本 | ❌ | ✅ | ❌ |
| 删除分类/软件/版本 | ❌ | ✅ | ❌ |

**注意**: 超级管理员**不能**管理软件，这是业务设计

---

## 🎨 统一响应格式

### 成功响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": { ... }  // 或 [...] 数组
}
```

### 错误响应

```json
{
  "success": false,
  "code": 4003,  // 错误码
  "message": "错误信息",
  "data": null  // 或验证错误详情
}
```

### 状态码说明

| HTTP状态码 | code | 说明 |
|-----------|------|------|
| 200 | 2000 | 操作成功 |
| 201 | 2000 | 创建成功 |
| 204 | 2000 | 删除成功（无响应体） |
| 400 | 4000 | 请求参数错误 |
| 401 | 4001 | 未认证 |
| 403 | 4003 | 权限不足 |
| 404 | 4004 | 资源不存在 |
| 500 | 5000 | 服务器错误 |

---

## 💡 使用建议

### 1. 级联选择器设计

**推荐流程**:
1. 用户选择分类 → 加载该分类下的软件列表
2. 用户选择软件 → 加载该软件的版本列表
3. 用户选择版本（可选）
4. 提交表单时携带软件ID和版本ID

### 2. 缓存策略

**建议缓存**:
- 分类列表（变化少，缓存5-10分钟）
- 软件列表（按分类缓存）

**实时获取**:
- 版本列表（可能频繁更新）
- 软件详情（包含统计信息）

### 3. 错误处理

```javascript
// 统一的错误处理
try {
  const response = await axios.get('/api/v1/feedbacks/software/')
  if (response.data.success) {
    // 成功处理
    return response.data.data
  }
} catch (error) {
  // 根据HTTP状态码处理
  switch (error.response?.status) {
    case 401:
      ElMessage.error('请先登录')
      // 跳转到登录页
      break
    case 403:
      ElMessage.error('权限不足')
      break
    case 404:
      ElMessage.error('资源不存在')
      break
    default:
      ElMessage.error('操作失败，请重试')
  }
}
```

---

## 🔧 Axios配置建议

### 创建API客户端

```javascript
// api/feedback.js
import axios from 'axios'
import { ElMessage } from 'element-plus'

const feedbackClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1/feedbacks',
  timeout: 10000
})

// 请求拦截器 - 自动添加Token
feedbackClient.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error)
)

// 响应拦截器 - 统一错误处理
feedbackClient.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 401) {
      ElMessage.error('登录已过期，请重新登录')
      // 跳转到登录页
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default feedbackClient
```

---

## 📋 常见问题

### Q1: 如何获取软件选择器的数据？

**答**: 分两步加载

```javascript
// 1. 先获取分类
const categories = await axios.get('/software-categories/')

// 2. 用户选择分类后，获取该分类的软件
const software = await axios.get('/software/', {
  params: { category: selectedCategoryId }
})
```

### Q2: 创建软件时category_id是什么？

**答**: 分类的ID

```javascript
{
  "category_id": 1  // 对应某个分类的id字段
}
```

### Q3: version_code怎么生成？

**答**: 建议规则

```javascript
// 版本号 v2.1.0
const versionCode = 2 * 100 + 1 * 10 + 0 = 210

// 辅助函数
function versionToCode(version) {
  // 去掉v前缀，分割
  const parts = version.replace('v', '').split('.').map(Number)
  return parts[0] * 100 + parts[1] * 10 + (parts[2] || 0)
}

// 使用
versionToCode('v2.1.0')  // 210
versionToCode('v3.0.5')  // 305
```

### Q4: 删除操作是真删除吗？

**答**: 不是，是软删除

- 数据仍保留在数据库（`is_deleted=true`）
- 不影响已有的关联数据
- 可以通过数据库恢复

---

## 🎯 完整业务流程示例

### 反馈提交页面的软件选择

```vue
<template>
  <el-form :model="feedbackForm">
    <!-- 1. 选择分类 -->
    <el-form-item label="软件分类">
      <el-select v-model="feedbackForm.category" @change="onCategoryChange">
        <el-option
          v-for="cat in categories"
          :key="cat.id"
          :label="cat.name"
          :value="cat.id"
        />
      </el-select>
    </el-form-item>

    <!-- 2. 选择软件 -->
    <el-form-item label="软件产品" v-if="softwareList.length > 0">
      <el-select v-model="feedbackForm.software" @change="onSoftwareChange">
        <el-option
          v-for="soft in softwareList"
          :key="soft.id"
          :label="soft.name"
          :value="soft.id"
        >
          <span>{{ soft.name }}</span>
          <span style="color: #8492a6; font-size: 13px">
            ({{ soft.current_version || '无版本' }})
          </span>
        </el-option>
      </el-select>
    </el-form-item>

    <!-- 3. 选择版本（可选） -->
    <el-form-item label="软件版本" v-if="versions.length > 0">
      <el-select v-model="feedbackForm.software_version">
        <el-option
          v-for="ver in versions"
          :key="ver.id"
          :label="ver.version"
          :value="ver.id"
        />
      </el-select>
    </el-form-item>
  </el-form>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'

const categories = ref([])
const softwareList = ref([])
const versions = ref([])
const feedbackForm = reactive({
  category: null,
  software: null,
  software_version: null
})

// 加载分类
onMounted(async () => {
  const response = await axios.get('/api/v1/feedbacks/software-categories/')
  if (response.data.success) {
    categories.value = response.data.data
  }
})

// 分类变化，加载软件
const onCategoryChange = async (categoryId) => {
  feedbackForm.software = null
  feedbackForm.software_version = null
  softwareList.value = []
  versions.value = []
  
  const response = await axios.get('/api/v1/feedbacks/software/', {
    params: { category: categoryId, is_active: true }
  })
  if (response.data.success) {
    softwareList.value = response.data.data
  }
}

// 软件变化，加载版本
const onSoftwareChange = async (softwareId) => {
  feedbackForm.software_version = null
  versions.value = []
  
  const response = await axios.get(`/api/v1/feedbacks/software/${softwareId}/versions/`)
  if (response.data.success) {
    versions.value = response.data.data
  }
}
</script>
```

---

## ✅ 验证清单

使用这些API前，请确认：

- [ ] 已配置Axios客户端
- [ ] 已添加Token到请求头
- [ ] 已了解权限要求
- [ ] 已理解响应格式
- [ ] 已阅读对应的API文档

---

## 📞 技术支持

**在线文档**: `http://your-domain.com/api/v1/docs/`

**遇到问题时**:
1. 检查请求参数是否完整
2. 确认Token是否有效
3. 查看响应的`code`和`message`字段
4. 参考文档中的使用示例

---

**文档版本**: 1.0.0  
**最后更新**: 2025-10-23  
**适用系统**: Feedback System v1.0

