# 软件产品 API 使用文档

## 📋 概述

软件产品API用于管理具体的软件产品信息（如：CRM系统、ERP系统等）。

**基础URL**: `/api/v1/feedbacks/software/`  
**权限要求**: 查看（所有人）、管理（仅租户管理员）  
**API数量**: 8个

---

## API 列表

| 序号 | 功能 | HTTP方法 | URL |
|------|------|---------|-----|
| 1 | 获取软件列表 | GET | `/software/` |
| 2 | 创建软件 | POST | `/software/` |
| 3 | 获取软件详情 | GET | `/software/{id}/` |
| 4 | 完整更新软件 | PUT | `/software/{id}/` |
| 5 | 部分更新软件 | PATCH | `/software/{id}/` |
| 6 | 删除软件 | DELETE | `/software/{id}/` |
| 7 | 获取软件版本列表 | GET | `/software/{id}/versions/` |
| 8 | 为软件添加版本 | POST | `/software/{id}/versions/` |

---

## 1. 获取软件产品列表

### 接口信息

- **URL**: `GET /api/v1/feedbacks/software/`
- **权限**: 任何已认证用户
- **用途**: 获取所有软件产品，支持多条件筛选

### 请求参数

| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|--------|------|------|------|--------|
| category | Integer | 否 | 按分类ID筛选 | `1` |
| status | String | 否 | 按状态筛选 | `released` |
| is_active | Boolean | 否 | 筛选激活状态 | `true` |
| search | String | 否 | 搜索名称和代码 | `CRM` |
| ordering | String | 否 | 排序 | `name`, `-created_at` |

### 状态值说明

| 值 | 说明 | 适用场景 |
|---|------|---------|
| development | 开发中 | 内部测试阶段 |
| testing | 测试中 | Beta测试 |
| released | 已发布 | 正式上线 |
| maintenance | 维护中 | 仅修复bug |
| deprecated | 已弃用 | 不再维护 |

### 响应格式

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": [
    {
      "id": 1,
      "name": "CRM系统",
      "code": "crm_system",
      "description": "客户关系管理系统",
      "category": 1,
      "category_name": "Web应用",
      "logo": "http://example.com/media/logo.png",
      "current_version": "v2.1.0",
      "status": "released",
      "is_active": true,
      "total_feedbacks": 42,
      "open_feedbacks": 5,
      "version_count": 10,
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-15T00:00:00Z"
    }
  ]
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 软件ID |
| name | String | 软件名称 |
| code | String | 软件代码（唯一） |
| description | String | 软件描述 |
| category | Integer | 分类ID |
| category_name | String | 分类名称（只读） |
| logo | String | Logo图片URL |
| current_version | String | 当前版本号 |
| status | String | 开发状态 |
| is_active | Boolean | 是否激活 |
| total_feedbacks | Integer | 总反馈数（统计） |
| open_feedbacks | Integer | 未解决反馈数（统计） |
| version_count | Integer | 版本数量（统计） |

### 使用示例

```javascript
// 获取特定分类下的已发布软件
const getSoftwareList = async (categoryId) => {
  try {
    const response = await axios.get('/api/v1/feedbacks/software/', {
      params: {
        category: categoryId,
        status: 'released',
        is_active: true,
        ordering: 'name'
      }
    })
    
    if (response.data.success) {
      return response.data.data
    }
  } catch (error) {
    ElMessage.error('获取软件列表失败')
    return []
  }
}

// Vue组件中使用
const softwareList = ref([])

onMounted(async () => {
  softwareList.value = await getSoftwareList(1)
})
```

---

## 2. 创建软件产品

### 接口信息

- **URL**: `POST /api/v1/feedbacks/software/`
- **权限**: 仅租户管理员
- **用途**: 创建新的软件产品

### 请求参数

| 参数名 | 类型 | 必填 | 说明 | 约束 |
|--------|------|------|------|------|
| name | String | ✅ | 软件名称 | 最多200字符 |
| code | String | ✅ | 软件代码 | 最多100字符，租户内唯一 |
| description | String | ❌ | 软件描述 | 无限制 |
| category_id | Integer | ✅ | 所属分类ID | 必须是有效的分类 |
| website | String | ❌ | 官方网站 | URL格式 |
| owner | String | ❌ | 负责人 | 最多100字符 |
| team | String | ❌ | 团队名称 | 最多200字符 |
| contact_email | String | ❌ | 联系邮箱 | 邮箱格式 |
| tags | Array | ❌ | 标签数组 | JSON数组 |
| status | String | ❌ | 开发状态 | 默认development |
| is_active | Boolean | ❌ | 是否激活 | 默认true |

### 请求示例

```json
{
  "name": "ERP系统",
  "code": "erp_system",
  "description": "企业资源计划系统，帮助企业管理资源",
  "category_id": 1,
  "website": "https://erp.example.com",
  "owner": "张三",
  "team": "ERP开发团队",
  "contact_email": "support@erp.example.com",
  "tags": ["企业级", "SaaS", "云服务"],
  "status": "released",
  "is_active": true
}
```

### 成功响应

**状态码**: 201 Created

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 2,
    "name": "ERP系统",
    "code": "erp_system",
    "description": "企业资源计划系统，帮助企业管理资源",
    "category": 1,
    "category_detail": {
      "id": 1,
      "name": "Web应用",
      "code": "web"
    },
    "logo": null,
    "website": "https://erp.example.com",
    "current_version": null,
    "owner": "张三",
    "team": "ERP开发团队",
    "contact_email": "support@erp.example.com",
    "tags": ["企业级", "SaaS", "云服务"],
    "metadata": {},
    "status": "released",
    "is_active": true,
    "total_feedbacks": 0,
    "open_feedbacks": 0,
    "versions": [],
    "created_at": "2025-10-23T10:00:00Z",
    "updated_at": "2025-10-23T10:00:00Z"
  }
}
```

### 使用示例

```javascript
const createSoftware = async (softwareData) => {
  try {
    const response = await axios.post(
      '/api/v1/feedbacks/software/',
      softwareData
    )
    
    if (response.data.success) {
      ElMessage.success('软件创建成功')
      return response.data.data
    }
  } catch (error) {
    if (error.response?.status === 400) {
      // 验证错误
      const errors = error.response.data.data
      Object.keys(errors).forEach(field => {
        ElMessage.error(`${field}: ${errors[field][0]}`)
      })
    } else if (error.response?.status === 403) {
      ElMessage.error('权限不足，只有管理员可以创建软件')
    }
  }
}
```

---

## 3. 获取软件详情

### 接口信息

- **URL**: `GET /api/v1/feedbacks/software/{id}/`
- **权限**: 任何已认证用户
- **用途**: 获取软件的完整信息，包括所有版本列表

### 响应格式

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 1,
    "name": "CRM系统",
    "code": "crm_system",
    "description": "客户关系管理系统",
    "category": {
      "id": 1,
      "name": "Web应用",
      "code": "web"
    },
    "logo": "http://example.com/media/logo.png",
    "website": "https://crm.example.com",
    "current_version": "v2.1.0",
    "owner": "张三",
    "team": "CRM团队",
    "contact_email": "support@crm.example.com",
    "tags": ["企业", "SaaS"],
    "status": "released",
    "is_active": true,
    "total_feedbacks": 42,
    "open_feedbacks": 5,
    "versions": [
      {
        "id": 10,
        "version": "v2.1.0",
        "version_code": 210,
        "release_date": "2025-01-01",
        "is_stable": true,
        "is_active": true
      },
      {
        "id": 9,
        "version": "v2.0.0",
        "version_code": 200,
        "release_date": "2024-12-01",
        "is_stable": true,
        "is_active": true
      }
    ],
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-15T00:00:00Z"
  }
}
```

---

## 4-5. 更新软件产品

### 接口信息

- **PATCH**: `PATCH /api/v1/feedbacks/software/{id}/` （推荐）
- **PUT**: `PUT /api/v1/feedbacks/software/{id}/`
- **权限**: 仅租户管理员

### 请求参数（PATCH - 部分更新）

**只需提供要修改的字段**:

```json
{
  "name": "新名称",
  "description": "新描述",
  "status": "maintenance"
}
```

### 使用示例

```javascript
// 更新软件状态
const updateSoftwareStatus = async (softwareId, newStatus) => {
  try {
    const response = await axios.patch(
      `/api/v1/feedbacks/software/${softwareId}/`,
      { status: newStatus }
    )
    
    if (response.data.success) {
      ElMessage.success('状态更新成功')
      return response.data.data
    }
  } catch (error) {
    ElMessage.error('更新失败')
  }
}

// 调用
await updateSoftwareStatus(1, 'maintenance')
```

---

## 6. 删除软件产品

### 接口信息

- **URL**: `DELETE /api/v1/feedbacks/software/{id}/`
- **权限**: 仅租户管理员
- **行为**: 软删除（数据保留）

### 响应

**成功**: 204 No Content（无响应体）

---

## 7. 获取软件的版本列表

### 接口信息

- **URL**: `GET /api/v1/feedbacks/software/{id}/versions/`
- **权限**: 任何已认证用户
- **用途**: 获取指定软件的所有版本

### URL参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | Integer | ✅ | 软件ID |

### 响应格式

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": [
    {
      "id": 10,
      "software": 1,
      "version": "v2.1.0",
      "version_code": 210,
      "release_date": "2025-01-01",
      "release_notes": "新功能和bug修复",
      "is_stable": true,
      "is_active": true,
      "download_url": "https://example.com/download/v2.1.0",
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    }
  ]
}
```

---

## 8. 为软件添加版本

### 接口信息

- **URL**: `POST /api/v1/feedbacks/software/{id}/versions/`
- **权限**: 仅租户管理员
- **用途**: 为指定软件添加新版本

### 请求参数

| 参数名 | 类型 | 必填 | 说明 | 约束 |
|--------|------|------|------|------|
| version | String | ✅ | 版本号 | 如 v2.1.0 |
| version_code | Integer | ✅ | 版本代码 | 用于比较大小 |
| release_date | Date | ❌ | 发布日期 | YYYY-MM-DD格式 |
| release_notes | String | ❌ | 发布说明 | Markdown格式 |
| is_stable | Boolean | ❌ | 是否稳定版 | 默认true |
| is_active | Boolean | ❌ | 是否激活 | 默认true |
| download_url | String | ❌ | 下载链接 | URL格式 |

### 请求示例

```json
{
  "version": "v2.2.0",
  "version_code": 220,
  "release_date": "2025-01-15",
  "release_notes": "## 新功能\n- 添加暗黑模式\n- 性能优化\n\n## Bug修复\n- 修复登录问题",
  "is_stable": true,
  "is_active": true,
  "download_url": "https://example.com/download/v2.2.0"
}
```

### 成功响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 11,
    "software": 1,
    "version": "v2.2.0",
    "version_code": 220,
    "release_date": "2025-01-15",
    "release_notes": "## 新功能\n- 添加暗黑模式\n...",
    "is_stable": true,
    "is_active": true,
    "download_url": "https://example.com/download/v2.2.0",
    "created_at": "2025-01-15T10:00:00Z",
    "updated_at": "2025-01-15T10:00:00Z"
  }
}
```

---

## 完整的软件管理流程示例

```vue
<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const categories = ref([])
const softwareList = ref([])
const selectedCategory = ref(null)

// 1. 加载分类列表
onMounted(async () => {
  const response = await axios.get('/api/v1/feedbacks/software-categories/')
  if (response.data.success) {
    categories.value = response.data.data
  }
})

// 2. 根据分类加载软件列表
watch(selectedCategory, async (categoryId) => {
  if (!categoryId) return
  
  const response = await axios.get('/api/v1/feedbacks/software/', {
    params: { category: categoryId, is_active: true }
  })
  
  if (response.data.success) {
    softwareList.value = response.data.data
  }
})

// 3. 创建新软件
const createSoftware = async () => {
  const newSoftware = {
    name: 'ERP系统',
    code: 'erp_system',
    description: '企业资源计划系统',
    category_id: selectedCategory.value,
    status: 'released',
    is_active: true
  }
  
  const response = await axios.post('/api/v1/feedbacks/software/', newSoftware)
  if (response.data.success) {
    ElMessage.success('软件创建成功')
    // 刷新列表
    // ...
  }
}

// 4. 更新软件
const updateSoftware = async (id, updates) => {
  const response = await axios.patch(`/api/v1/feedbacks/software/${id}/`, updates)
  if (response.data.success) {
    ElMessage.success('更新成功')
  }
}

// 5. 为软件添加版本
const addVersion = async (softwareId) => {
  const newVersion = {
    version: 'v2.2.0',
    version_code: 220,
    release_date: '2025-01-15',
    is_stable: true,
    is_active: true
  }
  
  const response = await axios.post(
    `/api/v1/feedbacks/software/${softwareId}/versions/`,
    newVersion
  )
  
  if (response.data.success) {
    ElMessage.success('版本添加成功')
  }
}
</script>
```

---

## 注意事项

### 1. 软件代码唯一性
- `code`字段在租户内必须唯一
- 建议格式：`product_name`（小写+下划线）

### 2. 分类关联
- 创建软件时必须指定`category_id`
- 分类ID必须是有效且属于当前租户的

### 3. 版本管理
- 添加版本后会自动更新软件的`current_version`
- `version_code`建议规则：主版本*100 + 次版本*10 + 修订版本
  - v2.1.0 → 210
  - v3.0.5 → 305

### 4. Logo上传
- Logo需要单独上传（使用文件上传接口）
- 返回URL后更新到logo字段

### 5. 统计字段
- `total_feedbacks`、`open_feedbacks`、`version_count`是系统自动计算的
- 创建时自动设为0
- 后续会根据实际数据更新

---

**下一步**: [03_软件版本API使用文档.md](03_软件版本API使用文档.md)

