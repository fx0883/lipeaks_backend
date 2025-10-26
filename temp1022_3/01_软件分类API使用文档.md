# 软件分类 API 使用文档

## 📋 概述

软件分类API用于管理软件的分类信息（如：Web应用、移动应用、API服务等）。

**基础URL**: `/api/v1/feedbacks/software-categories/`  
**权限要求**: 查看（所有人）、管理（仅租户管理员）  
**API数量**: 6个

---

## API 列表

| 序号 | 功能 | HTTP方法 | URL |
|------|------|---------|-----|
| 1 | 获取分类列表 | GET | `/software-categories/` |
| 2 | 创建分类 | POST | `/software-categories/` |
| 3 | 获取分类详情 | GET | `/software-categories/{id}/` |
| 4 | 完整更新分类 | PUT | `/software-categories/{id}/` |
| 5 | 部分更新分类 | PATCH | `/software-categories/{id}/` |
| 6 | 删除分类 | DELETE | `/software-categories/{id}/` |

---

## 1. 获取软件分类列表

### 接口信息

- **URL**: `GET /api/v1/feedbacks/software-categories/`
- **权限**: 任何已认证用户
- **用途**: 获取所有软件分类，用于下拉选择器、分类导航等

### 请求参数

| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|--------|------|------|------|--------|
| is_active | Boolean | 否 | 筛选激活状态 | `true` |
| search | String | 否 | 搜索分类名称和描述 | `web` |
| ordering | String | 否 | 排序字段 | `sort_order`, `name` |

### 响应格式

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": [
    {
      "id": 1,
      "name": "Web应用",
      "code": "web",
      "description": "基于Web的应用程序",
      "icon": "web",
      "sort_order": 1,
      "is_active": true,
      "software_count": 5,
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z"
    },
    {
      "id": 2,
      "name": "移动应用",
      "code": "mobile",
      "description": "手机端应用程序",
      "icon": "smartphone",
      "sort_order": 2,
      "is_active": true,
      "software_count": 3,
      "created_at": "2025-01-02T00:00:00Z",
      "updated_at": "2025-01-02T00:00:00Z"
    }
  ]
}
```

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 分类ID（唯一标识） |
| name | String | 分类名称 |
| code | String | 分类代码（唯一，用于程序识别） |
| description | String | 分类描述 |
| icon | String | 图标名称（Element Plus图标） |
| sort_order | Integer | 排序顺序（数字越小越靠前） |
| is_active | Boolean | 是否激活 |
| software_count | Integer | 该分类下的软件数量 |
| created_at | DateTime | 创建时间（UTC） |
| updated_at | DateTime | 最后更新时间（UTC） |

### 使用示例

**Vue 3 + Axios**:

```javascript
// 获取所有激活的分类
const getCategories = async () => {
  try {
    const response = await axios.get('/api/v1/feedbacks/software-categories/', {
      params: {
        is_active: true,
        ordering: 'sort_order'
      }
    })
    
    if (response.data.success) {
      const categories = response.data.data
      console.log(`获取到 ${categories.length} 个分类`)
      return categories
    }
  } catch (error) {
    console.error('获取分类失败:', error)
  }
}
```

**在下拉选择器中使用**:

```vue
<template>
  <el-select v-model="selectedCategory" placeholder="选择软件分类">
    <el-option
      v-for="category in categories"
      :key="category.id"
      :label="category.name"
      :value="category.id"
    >
      <span>{{ category.name }}</span>
      <span style="color: #8492a6; font-size: 13px">
        ({{ category.software_count }}个软件)
      </span>
    </el-option>
  </el-select>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const categories = ref([])
const selectedCategory = ref(null)

onMounted(async () => {
  const response = await axios.get('/api/v1/feedbacks/software-categories/', {
    params: { is_active: true }
  })
  if (response.data.success) {
    categories.value = response.data.data
  }
})
</script>
```

---

## 2. 创建软件分类

### 接口信息

- **URL**: `POST /api/v1/feedbacks/software-categories/`
- **权限**: 仅租户管理员
- **用途**: 创建新的软件分类

### 请求参数

| 参数名 | 类型 | 必填 | 说明 | 约束 |
|--------|------|------|------|------|
| name | String | ✅ | 分类名称 | 最多100字符 |
| code | String | ✅ | 分类代码（唯一） | 最多50字符，建议英文小写+下划线 |
| description | String | ❌ | 分类描述 | 无限制 |
| icon | String | ❌ | 图标名称 | Element Plus图标名称 |
| sort_order | Integer | ❌ | 排序顺序 | 默认0 |
| is_active | Boolean | ❌ | 是否激活 | 默认true |

### 请求示例

```json
{
  "name": "API服务",
  "code": "api_service",
  "description": "后端API服务类软件",
  "icon": "ep:link",
  "sort_order": 3,
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
    "id": 3,
    "name": "API服务",
    "code": "api_service",
    "description": "后端API服务类软件",
    "icon": "ep:link",
    "sort_order": 3,
    "is_active": true,
    "software_count": 0,
    "created_at": "2025-10-23T10:00:00Z",
    "updated_at": "2025-10-23T10:00:00Z"
  }
}
```

### 错误响应

**权限不足（403）**:
```json
{
  "success": false,
  "code": 4003,
  "message": "Permission denied.",
  "data": null
}
```

**验证失败（400）**:
```json
{
  "success": false,
  "code": 4000,
  "message": "验证失败",
  "data": {
    "name": ["此字段不能为空"],
    "code": ["分类代码已存在"]
  }
}
```

### 使用示例

```javascript
// 创建分类
const createCategory = async (categoryData) => {
  try {
    const response = await axios.post(
      '/api/v1/feedbacks/software-categories/',
      categoryData
    )
    
    if (response.data.success) {
      ElMessage.success('分类创建成功')
      return response.data.data
    }
  } catch (error) {
    if (error.response?.status === 403) {
      ElMessage.error('权限不足，只有管理员可以创建分类')
    } else if (error.response?.status === 400) {
      // 显示验证错误
      const errors = error.response.data.data
      Object.keys(errors).forEach(field => {
        ElMessage.error(`${field}: ${errors[field][0]}`)
      })
    }
  }
}

// 调用
await createCategory({
  name: 'API服务',
  code: 'api_service',
  description: '后端API服务类软件',
  icon: 'ep:link',
  sort_order: 3,
  is_active: true
})
```

---

## 3. 获取分类详情

### 接口信息

- **URL**: `GET /api/v1/feedbacks/software-categories/{id}/`
- **权限**: 任何已认证用户
- **用途**: 获取单个分类的详细信息

### URL参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | Integer | ✅ | 分类ID |

### 响应格式

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 1,
    "name": "Web应用",
    "code": "web",
    "description": "基于Web的应用程序",
    "icon": "web",
    "sort_order": 1,
    "is_active": true,
    "software_count": 5,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
  }
}
```

### 错误响应

**未找到（404）**:
```json
{
  "success": false,
  "code": 4004,
  "message": "Category not found.",
  "data": null
}
```

---

## 4-5. 更新软件分类

### 接口信息

- **URL**: `PUT /api/v1/feedbacks/software-categories/{id}/` （完整更新）
- **URL**: `PATCH /api/v1/feedbacks/software-categories/{id}/` （部分更新）
- **权限**: 仅租户管理员
- **用途**: 修改现有分类信息

### PUT vs PATCH

| 方法 | 说明 | 使用场景 |
|------|------|---------|
| **PATCH** | 部分更新，只需提供要修改的字段 | 推荐使用，更灵活 |
| **PUT** | 完整更新，需要提供所有字段 | 替换整个对象时使用 |

### 请求参数（PATCH）

**只需要提供要修改的字段**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| name | String | 分类名称 |
| code | String | 分类代码 |
| description | String | 分类描述 |
| icon | String | 图标名称 |
| sort_order | Integer | 排序顺序 |
| is_active | Boolean | 是否激活 |

### 请求示例（PATCH）

```json
{
  "name": "Web应用程序",
  "description": "更新后的描述"
}
```

### 成功响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 1,
    "name": "Web应用程序",
    "code": "web",
    "description": "更新后的描述",
    "icon": "web",
    "sort_order": 1,
    "is_active": true,
    "software_count": 5,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-10-23T14:30:00Z"
  }
}
```

### 使用示例

```javascript
// 部分更新分类（推荐）
const updateCategory = async (categoryId, updates) => {
  try {
    const response = await axios.patch(
      `/api/v1/feedbacks/software-categories/${categoryId}/`,
      updates
    )
    
    if (response.data.success) {
      ElMessage.success('分类更新成功')
      return response.data.data
    }
  } catch (error) {
    if (error.response?.status === 403) {
      ElMessage.error('权限不足，只有管理员可以修改分类')
    } else if (error.response?.status === 404) {
      ElMessage.error('分类不存在')
    }
  }
}

// 调用示例
await updateCategory(1, {
  name: '新名称',
  description: '新描述'
})
```

---

## 6. 删除软件分类

### 接口信息

- **URL**: `DELETE /api/v1/feedbacks/software-categories/{id}/`
- **权限**: 仅租户管理员
- **用途**: 软删除分类（数据仍保留）

### URL参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | Integer | ✅ | 分类ID |

### 成功响应

**状态码**: 204 No Content  
**响应体**: 无

### 错误响应

**权限不足（403）**:
```json
{
  "success": false,
  "code": 4003,
  "message": "Permission denied.",
  "data": null
}
```

**未找到（404）**:
```json
{
  "success": false,
  "code": 4004,
  "message": "Category not found.",
  "data": null
}
```

### 使用示例

```javascript
const deleteCategory = async (categoryId) => {
  try {
    // 先确认
    await ElMessageBox.confirm(
      '确定要删除此分类吗？删除后该分类下的软件将无法使用此分类。',
      '警告',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 执行删除
    const response = await axios.delete(
      `/api/v1/feedbacks/software-categories/${categoryId}/`
    )
    
    ElMessage.success('分类已删除')
    return true
  } catch (error) {
    if (error === 'cancel') {
      // 用户取消
      return false
    }
    
    if (error.response?.status === 403) {
      ElMessage.error('权限不足')
    } else if (error.response?.status === 404) {
      ElMessage.error('分类不存在')
    }
    return false
  }
}
```

---

## 完整的Vue组件示例

### 分类管理页面

```vue
<template>
  <div class="category-management">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>软件分类管理</span>
          <el-button type="primary" @click="showCreateDialog = true">
            新增分类
          </el-button>
        </div>
      </template>

      <!-- 分类列表 -->
      <el-table :data="categories" style="width: 100%">
        <el-table-column prop="name" label="分类名称" width="150" />
        <el-table-column prop="code" label="分类代码" width="120" />
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="software_count" label="软件数量" width="100" />
        <el-table-column prop="sort_order" label="排序" width="80" />
        <el-table-column label="状态" width="80">
          <template #default="scope">
            <el-tag :type="scope.row.is_active ? 'success' : 'danger'">
              {{ scope.row.is_active ? '激活' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180">
          <template #default="scope">
            <el-button size="small" @click="handleEdit(scope.row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(scope.row.id)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog 
      v-model="showCreateDialog" 
      :title="editingCategory ? '编辑分类' : '新增分类'"
      width="500px"
    >
      <el-form :model="formData" label-width="100px">
        <el-form-item label="分类名称" required>
          <el-input v-model="formData.name" placeholder="如：Web应用" />
        </el-form-item>
        <el-form-item label="分类代码" required>
          <el-input v-model="formData.code" placeholder="如：web_app" />
        </el-form-item>
        <el-form-item label="分类描述">
          <el-input type="textarea" v-model="formData.description" />
        </el-form-item>
        <el-form-item label="图标">
          <el-input v-model="formData.icon" placeholder="如：ep:folder" />
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="formData.sort_order" :min="0" />
        </el-form-item>
        <el-form-item label="是否激活">
          <el-switch v-model="formData.is_active" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const categories = ref([])
const showCreateDialog = ref(false)
const editingCategory = ref(null)
const formData = reactive({
  name: '',
  code: '',
  description: '',
  icon: '',
  sort_order: 0,
  is_active: true
})

// 获取分类列表
const fetchCategories = async () => {
  try {
    const response = await axios.get('/api/v1/feedbacks/software-categories/')
    if (response.data.success) {
      categories.value = response.data.data
    }
  } catch (error) {
    ElMessage.error('获取分类列表失败')
  }
}

// 保存（创建或更新）
const handleSave = async () => {
  try {
    let response
    if (editingCategory.value) {
      // 更新
      response = await axios.patch(
        `/api/v1/feedbacks/software-categories/${editingCategory.value.id}/`,
        formData
      )
    } else {
      // 创建
      response = await axios.post(
        '/api/v1/feedbacks/software-categories/',
        formData
      )
    }
    
    if (response.data.success) {
      ElMessage.success(editingCategory.value ? '更新成功' : '创建成功')
      showCreateDialog.value = false
      fetchCategories()
    }
  } catch (error) {
    const errorData = error.response?.data?.data
    if (errorData && typeof errorData === 'object') {
      // 显示验证错误
      Object.keys(errorData).forEach(field => {
        ElMessage.error(`${field}: ${errorData[field][0]}`)
      })
    } else {
      ElMessage.error('操作失败')
    }
  }
}

// 编辑
const handleEdit = (category) => {
  editingCategory.value = category
  Object.keys(formData).forEach(key => {
    formData[key] = category[key]
  })
  showCreateDialog.value = true
}

// 删除
const handleDelete = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除此分类吗？', '警告', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    await axios.delete(`/api/v1/feedbacks/software-categories/${id}/`)
    ElMessage.success('删除成功')
    fetchCategories()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  fetchCategories()
})
</script>
```

---

## 注意事项

### 1. 分类代码唯一性
- `code`字段在租户内必须唯一
- 建议使用英文小写+下划线格式
- 示例：`web_app`, `mobile_app`, `api_service`

### 2. 删除限制
- 删除操作是软删除，数据仍保留在数据库
- 建议删除前检查该分类下是否有软件

### 3. 排序规则
- `sort_order`数值越小，排序越靠前
- 相同`sort_order`时按名称字母顺序排序

### 4. 权限说明
- 查看分类：所有已认证用户
- 创建/修改/删除：仅租户管理员

---

**下一步**: [02_软件产品API使用文档.md](02_软件产品API使用文档.md)

