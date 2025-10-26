# 软件版本 API 使用文档

## 📋 概述

软件版本API用于管理软件的不同版本信息。

**基础URL**: `/api/v1/feedbacks/software-versions/`  
**权限要求**: 查看（所有人）、管理（仅租户管理员）  
**API数量**: 6个

---

## API 列表

| 序号 | 功能 | HTTP方法 | URL |
|------|------|---------|-----|
| 1 | 创建软件版本 | POST | `/software/{software_id}/versions/` |
| 2 | 获取所有版本列表 | GET | `/software-versions/` |
| 3 | 获取版本详情 | GET | `/software-versions/{id}/` |
| 4 | 完整更新版本 | PUT | `/software-versions/{id}/` |
| 5 | 部分更新版本 | PATCH | `/software-versions/{id}/` |
| 6 | 删除版本 | DELETE | `/software-versions/{id}/` |

**注意**: 创建版本使用嵌套路由 `/software/{software_id}/versions/`

---

## 1. 创建软件版本

### 接口信息

- **URL**: `POST /api/v1/feedbacks/software/{software_id}/versions/`
- **权限**: 仅租户管理员
- **用途**: 为指定软件添加新版本

### URL参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| software_id | Integer | ✅ | 软件ID（在URL路径中） |

### 请求参数

| 参数名 | 类型 | 必填 | 说明 | 约束 |
|--------|------|------|------|------|
| version | String | ✅ | 版本号 | 如 v2.1.0，最多50字符 |
| version_code | Integer | ✅ | 版本代码 | 用于比较大小，必须递增 |
| release_date | Date | ❌ | 发布日期 | YYYY-MM-DD格式，空值传null或不传 |
| release_notes | String | ❌ | 发布说明 | 支持Markdown格式，空值传null或不传 |
| is_stable | Boolean | ❌ | 是否稳定版 | 默认true |
| is_active | Boolean | ❌ | 是否激活 | 默认true |
| download_url | String | ❌ | 下载链接 | URL格式，空值传null或不传 |

**⚠️ 重要提示**:
- **不需要传`software`字段**，系统会自动从URL的`{software_id}`获取
- 可选字段如果为空，请传`null`或不传该字段，**不要传空字符串`""`**

### 请求示例

**完整示例（包含所有字段）**:

```json
{
  "version": "v2.2.0",
  "version_code": 220,
  "release_date": "2025-01-15",
  "release_notes": "## 新功能\n- 添加暗黑模式支持\n- 界面性能优化\n\n## Bug修复\n- 修复登录异常问题\n- 修复数据导出错误",
  "is_stable": true,
  "is_active": true,
  "download_url": "https://example.com/download/v2.2.0.zip"
}
```

**最小示例（只包含必填字段）**:

```json
{
  "version": "v2.2.0",
  "version_code": 220
}
```

**注意**:
- ✅ 不需要传`software`字段
- ✅ 可选字段为空时，不传或传`null`
- ❌ 不要传空字符串`""`

### 成功响应

**状态码**: 201 Created

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 11,
    "software": 1,
    "software_name": "CRM系统",
    "software_code": "crm_system",
    "version": "v2.2.0",
    "version_code": 220,
    "release_date": "2025-01-15",
    "release_notes": "## 新功能\n- 添加暗黑模式支持\n...",
    "is_stable": true,
    "is_active": true,
    "download_url": "https://example.com/download/v2.2.0.zip",
    "created_at": "2025-01-15T10:00:00Z",
    "updated_at": "2025-01-15T10:00:00Z"
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

**软件不存在（404）**:
```json
{
  "success": false,
  "code": 4004,
  "message": "Software not found.",
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
    "version": ["此字段不能为空"],
    "version_code": ["此字段不能为空"]
  }
}
```

### 使用示例

```javascript
// 为软件添加新版本
const addSoftwareVersion = async (softwareId, versionData) => {
  try {
    const response = await axios.post(
      `/api/v1/feedbacks/software/${softwareId}/versions/`,
      versionData
    )
    
    if (response.data.success) {
      ElMessage.success('版本添加成功')
      return response.data.data
    }
  } catch (error) {
    if (error.response?.status === 403) {
      ElMessage.error('权限不足，只有管理员可以添加版本')
    } else if (error.response?.status === 404) {
      ElMessage.error('软件不存在')
    } else if (error.response?.status === 400) {
      // 显示验证错误
      const errors = error.response.data.data
      Object.keys(errors).forEach(field => {
        ElMessage.error(`${field}: ${errors[field][0]}`)
      })
    }
  }
}

// 调用示例1：完整参数
await addSoftwareVersion(1, {
  version: 'v2.2.0',
  version_code: 220,
  release_date: '2025-01-15',
  release_notes: '## 新功能\n- 添加暗黑模式\n- 性能优化',
  is_stable: true,
  is_active: true,
  download_url: 'https://example.com/download/v2.2.0.zip'
})

// 调用示例2：最小参数（推荐）
await addSoftwareVersion(1, {
  version: 'v2.2.0',
  version_code: 220
  // 可选字段不传，系统会使用默认值
})
```

### Vue组件示例

```vue
<template>
  <el-dialog v-model="showDialog" title="添加新版本" width="600px">
    <el-form :model="versionForm" label-width="100px">
      <el-form-item label="版本号" required>
        <el-input v-model="versionForm.version" placeholder="如：v2.2.0" />
        <span class="help-text">格式：v主版本.次版本.修订版本</span>
      </el-form-item>
      
      <el-form-item label="版本代码" required>
        <el-input-number v-model="versionForm.version_code" :min="1" />
        <span class="help-text">自动计算或手动输入（建议递增）</span>
      </el-form-item>
      
      <el-form-item label="发布日期">
        <el-date-picker
          v-model="versionForm.release_date"
          type="date"
          placeholder="选择日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
        />
      </el-form-item>
      
      <el-form-item label="发布说明">
        <el-input
          type="textarea"
          v-model="versionForm.release_notes"
          :rows="6"
          placeholder="## 新功能\n- 功能1\n\n## Bug修复\n- 修复1"
        />
        <span class="help-text">支持Markdown格式</span>
      </el-form-item>
      
      <el-form-item label="稳定版本">
        <el-switch v-model="versionForm.is_stable" />
        <span class="help-text">是否推荐用户使用</span>
      </el-form-item>
      
      <el-form-item label="启用状态">
        <el-switch v-model="versionForm.is_active" />
      </el-form-item>
      
      <el-form-item label="下载链接">
        <el-input v-model="versionForm.download_url" placeholder="https://..." />
      </el-form-item>
    </el-form>
    
    <template #footer>
      <el-button @click="showDialog = false">取消</el-button>
      <el-button type="primary" @click="handleSave">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const props = defineProps({
  softwareId: Number
})

const showDialog = ref(false)
const versionForm = reactive({
  version: '',
  version_code: 0,
  release_date: '',
  release_notes: '',
  is_stable: true,
  is_active: true,
  download_url: ''
})

// 自动计算version_code
watch(() => versionForm.version, (newVersion) => {
  if (newVersion && newVersion.startsWith('v')) {
    const parts = newVersion.replace('v', '').split('.').map(Number)
    if (parts.length >= 2) {
      versionForm.version_code = 
        (parts[0] || 0) * 100 + 
        (parts[1] || 0) * 10 + 
        (parts[2] || 0)
    }
  }
})

const handleSave = async () => {
  try {
    // 准备数据：清理空字符串
    const data = { ...versionForm }
    
    // 将空字符串转为null或删除字段
    if (data.release_date === '') delete data.release_date
    if (data.release_notes === '') delete data.release_notes
    if (data.download_url === '') delete data.download_url
    
    const response = await axios.post(
      `/api/v1/feedbacks/software/${props.softwareId}/versions/`,
      data
    )
    
    if (response.data.success) {
      ElMessage.success('版本添加成功')
      showDialog.value = false
      // 触发刷新
      emit('success')
    }
  } catch (error) {
    if (error.response?.status === 400) {
      const errors = error.response.data.data
      Object.keys(errors).forEach(field => {
        ElMessage.error(`${field}: ${errors[field][0]}`)
      })
    } else {
      ElMessage.error('添加失败')
    }
  }
}
</script>
```

---

## 2. 获取所有版本列表

### 接口信息

- **URL**: `GET /api/v1/feedbacks/software-versions/`
- **权限**: 任何已认证用户
- **用途**: 获取所有软件版本（跨软件），支持筛选

### 请求参数

| 参数名 | 类型 | 必填 | 说明 | 示例值 |
|--------|------|------|------|--------|
| software | Integer | 否 | 按软件ID筛选 | `1` |
| is_stable | Boolean | 否 | 筛选稳定版本 | `true` |
| is_active | Boolean | 否 | 筛选激活状态 | `true` |
| ordering | String | 否 | 排序 | `-version_code` |

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
      "software_name": "CRM系统",
      "software_code": "crm_system",
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

### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 版本ID |
| software | Integer | 软件ID（外键） |
| **software_name** | String | **软件名称**（只读，自动关联） |
| **software_code** | String | **软件代码**（只读，自动关联） |
| version | String | 版本号 |
| version_code | Integer | 版本代码（用于比较） |
| release_date | Date/null | 发布日期 |
| release_notes | String/null | 发布说明 |
| is_stable | Boolean | 是否稳定版 |
| is_active | Boolean | 是否激活 |
| download_url | String/null | 下载链接 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 最后更新时间 |

**✨ 改进**: 
- 现在自动包含`software_name`和`software_code`
- 前端无需再次查询软件信息
- 方便直接在列表中显示软件名称

### 使用示例

```javascript
// 获取某个软件的所有稳定版本
const getStableVersions = async (softwareId) => {
  const response = await axios.get('/api/v1/feedbacks/software-versions/', {
    params: {
      software: softwareId,
      is_stable: true,
      ordering: '-version_code'  // 最新版本在前
    }
  })
  
  if (response.data.success) {
    return response.data.data
  }
}
```

---

## 2. 获取版本详情

### 接口信息

- **URL**: `GET /api/v1/feedbacks/software-versions/{id}/`
- **权限**: 任何已认证用户

### 响应格式

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 10,
    "software": 1,
    "software_name": "CRM系统",
    "software_code": "crm_system",
    "version": "v2.1.0",
    "version_code": 210,
    "release_date": "2025-01-01",
    "release_notes": "## 新功能\n- 添加暗黑模式\n\n## Bug修复\n- 修复登录问题",
    "is_stable": true,
    "is_active": true,
    "download_url": "https://example.com/download/v2.1.0",
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T00:00:00Z"
  }
}
```

---

## 4-5. 更新软件版本

### 接口信息

- **PATCH**: `PATCH /api/v1/feedbacks/software-versions/{id}/` （推荐）
- **PUT**: `PUT /api/v1/feedbacks/software-versions/{id}/`
- **权限**: 仅租户管理员
- **用途**: 修改现有版本信息

### URL参数

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | Integer | ✅ | 版本ID（在URL路径中） |

### 请求参数（PATCH - 部分更新）

**只需提供要修改的字段**:

| 参数名 | 类型 | 说明 |
|--------|------|------|
| version | String | 版本号 |
| version_code | Integer | 版本代码 |
| release_date | Date | 发布日期 |
| release_notes | String | 发布说明 |
| is_stable | Boolean | 是否稳定版 |
| is_active | Boolean | 是否激活 |
| download_url | String | 下载链接 |

### 请求示例

**示例1: 更新发布说明**

```json
{
  "release_notes": "## 更新内容\n- 修复已知问题\n- 性能优化\n\n## 注意事项\n- 建议先备份数据"
}
```

**示例2: 标记为不稳定版本**

```json
{
  "is_stable": false,
  "release_notes": "发现严重bug，暂不推荐使用此版本"
}
```

**示例3: 停用版本**

```json
{
  "is_active": false
}
```

### 成功响应

**状态码**: 200 OK

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 10,
    "software": 1,
    "software_name": "CRM系统",
    "software_code": "crm_system",
    "version": "v2.1.0",
    "version_code": 210,
    "release_date": "2025-01-01",
    "release_notes": "## 更新内容\n- 修复已知问题\n- 性能优化",
    "is_stable": true,
    "is_active": true,
    "download_url": "https://example.com/download/v2.1.0",
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-10-23T14:30:00Z"
  }
}
```

### 使用示例

```javascript
// 更新版本（推荐使用PATCH）
const updateVersion = async (versionId, updates) => {
  try {
    const response = await axios.patch(
      `/api/v1/feedbacks/software-versions/${versionId}/`,
      updates
    )
    
    if (response.data.success) {
      ElMessage.success('版本更新成功')
      return response.data.data
    }
  } catch (error) {
    if (error.response?.status === 403) {
      ElMessage.error('权限不足')
    } else if (error.response?.status === 404) {
      ElMessage.error('版本不存在')
    } else if (error.response?.status === 400) {
      const errors = error.response.data.data
      Object.keys(errors).forEach(field => {
        ElMessage.error(`${field}: ${errors[field][0]}`)
      })
    }
  }
}

// 场景1: 标记版本为不稳定
await updateVersion(10, {
  is_stable: false,
  release_notes: '发现严重bug，建议不要使用此版本'
})

// 场景2: 更新发布说明
await updateVersion(10, {
  release_notes: '## 更新内容\n- 修复已知问题\n- 性能优化'
})

// 场景3: 停用旧版本
await updateVersion(10, {
  is_active: false
})
```

### Vue组件示例

```vue
<template>
  <el-dialog v-model="showDialog" title="编辑版本" width="600px">
    <el-form :model="versionForm" label-width="100px">
      <el-form-item label="版本号" required>
        <el-input v-model="versionForm.version" disabled />
        <span class="help-text">版本号通常不建议修改</span>
      </el-form-item>
      
      <el-form-item label="发布日期">
        <el-date-picker
          v-model="versionForm.release_date"
          type="date"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
        />
      </el-form-item>
      
      <el-form-item label="发布说明">
        <el-input
          type="textarea"
          v-model="versionForm.release_notes"
          :rows="8"
          placeholder="Markdown格式"
        />
      </el-form-item>
      
      <el-form-item label="稳定版本">
        <el-switch v-model="versionForm.is_stable" />
        <span class="help-text">不稳定版本会有特殊标识</span>
      </el-form-item>
      
      <el-form-item label="启用状态">
        <el-switch v-model="versionForm.is_active" />
        <span class="help-text">停用后用户将看不到此版本</span>
      </el-form-item>
      
      <el-form-item label="下载链接">
        <el-input v-model="versionForm.download_url" />
      </el-form-item>
    </el-form>
    
    <template #footer>
      <el-button @click="showDialog = false">取消</el-button>
      <el-button type="primary" @click="handleUpdate">保存</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const props = defineProps({
  versionId: Number,
  versionData: Object
})

const emit = defineEmits(['success'])

const showDialog = ref(false)
const versionForm = reactive({
  version: '',
  release_date: '',
  release_notes: '',
  is_stable: true,
  is_active: true,
  download_url: ''
})

// 打开对话框时填充数据
const open = (data) => {
  Object.assign(versionForm, data)
  showDialog.value = true
}

const handleUpdate = async () => {
  try {
    const response = await axios.patch(
      `/api/v1/feedbacks/software-versions/${props.versionId}/`,
      versionForm
    )
    
    if (response.data.success) {
      ElMessage.success('版本更新成功')
      showDialog.value = false
      emit('success')
    }
  } catch (error) {
    if (error.response?.status === 400) {
      const errors = error.response.data.data
      Object.keys(errors).forEach(field => {
        ElMessage.error(`${field}: ${errors[field][0]}`)
      })
    } else {
      ElMessage.error('更新失败')
    }
  }
}

defineExpose({ open })
</script>
```

---

## 6. 删除软件版本

### 接口信息

- **URL**: `DELETE /api/v1/feedbacks/software-versions/{id}/`
- **权限**: 仅租户管理员
- **行为**: 软删除

---

## 版本号规范建议

### 推荐格式

**版本号**: `v主版本.次版本.修订版本`  
**示例**: `v2.1.0`, `v3.0.5`

### version_code 计算规则

```
version_code = 主版本 × 100 + 次版本 × 10 + 修订版本

示例:
v2.1.0 → 2×100 + 1×10 + 0 = 210
v3.0.5 → 3×100 + 0×10 + 5 = 305
v10.5.2 → 10×100 + 5×10 + 2 = 1052
```

**作用**: 用于版本大小比较和排序

---

## 完整示例：版本选择器

```vue
<template>
  <div class="version-selector">
    <el-select v-model="selectedVersion" placeholder="选择版本">
      <el-option
        v-for="version in versions"
        :key="version.id"
        :label="version.version"
        :value="version.id"
      >
        <span>{{ version.version }}</span>
        <span v-if="!version.is_stable" style="color: red; margin-left: 10px">
          (不稳定)
        </span>
        <span style="color: #8492a6; font-size: 13px; margin-left: 10px">
          {{ version.release_date }}
        </span>
      </el-option>
    </el-select>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import axios from 'axios'

const props = defineProps({
  softwareId: {
    type: Number,
    required: true
  }
})

const versions = ref([])
const selectedVersion = ref(null)

// 监听软件ID变化，加载对应版本
watch(() => props.softwareId, async (softwareId) => {
  if (!softwareId) return
  
  try {
    const response = await axios.get('/api/v1/feedbacks/software-versions/', {
      params: {
        software: softwareId,
        is_active: true,
        ordering: '-version_code'
      }
    })
    
    if (response.data.success) {
      versions.value = response.data.data
      // 默认选择最新版本
      if (versions.value.length > 0) {
        selectedVersion.value = versions.value[0].id
      }
    }
  } catch (error) {
    console.error('获取版本列表失败:', error)
  }
}, { immediate: true })
</script>
```

---

## 注意事项

### 1. 版本号格式
- 建议使用语义化版本号：`vMAJOR.MINOR.PATCH`
- 如：`v2.1.0`, `v3.0.1`

### 2. 版本代码
- `version_code`用于版本比较
- 必须是递增的数字
- 不要修改已发布版本的version_code

### 3. 稳定性标记
- `is_stable=true`: 稳定版本，推荐用户使用
- `is_stable=false`: 测试版本，可能有问题

### 4. 版本激活
- `is_active=true`: 可用版本
- `is_active=false`: 已停用（如发现严重bug）

### 5. 空值处理（重要⚠️）

**创建版本时**:
- ✅ 可选字段不传，或传`null`
- ❌ 不要传空字符串`""`

**错误示例**:
```json
{
  "version": "v2.2.0",
  "version_code": 220,
  "release_date": "",        // ❌ 会报错
  "release_notes": "",       // ❌ 会报错  
  "download_url": ""         // ❌ 会报错
}
```

**正确示例**:
```json
{
  "version": "v2.2.0",
  "version_code": 220
  // 可选字段直接不传
}
```

或:
```json
{
  "version": "v2.2.0",
  "version_code": 220,
  "release_date": null,      // ✅ 正确
  "release_notes": null,     // ✅ 正确
  "download_url": null       // ✅ 正确
}
```

**前端处理建议**:
```javascript
// 提交前清理空字符串
const cleanData = (data) => {
  const cleaned = { ...data }
  Object.keys(cleaned).forEach(key => {
    if (cleaned[key] === '') {
      delete cleaned[key]  // 删除空字符串字段
    }
  })
  return cleaned
}

// 使用
await axios.post('/api/v1/feedbacks/software/1/versions/', cleanData(formData))
```

---

**下一步**: [README.md](README.md)

