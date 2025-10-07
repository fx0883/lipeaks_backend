# 子账号管理 API

本文档详细说明子账号（Sub-Account）管理的API接口。

---

## 目录

- [子账号说明](#子账号说明)
- [1. 获取子账号列表](#1-获取子账号列表)
- [2. 创建子账号](#2-创建子账号)
- [3. 获取子账号详情](#3-获取子账号详情)
- [4. 更新子账号](#4-更新子账号)
- [5. 删除子账号](#5-删除子账号)
- [使用示例](#使用示例)
- [前端实现参考](#前端实现参考)

---

## 子账号说明

### 什么是子账号？

子账号是关联到父账号（主账号）的从属账号，具有以下特点：

- 🔗 **关联关系**：每个子账号必须有一个父账号
- 🚫 **不能登录**：子账号的`is_active`强制为`false`，不能登录系统
- 📊 **数据关联**：用于关联业务数据（如订单、记录等）
- 🔐 **权限继承**：子账号的权限由父账号控制

### 使用场景

1. **家庭成员账号**：一个主账号可以创建多个家庭成员子账号
2. **部门账号**：公司账号下可以创建不同部门的子账号
3. **设备账号**：一个用户可以为不同设备创建子账号
4. **数据分类**：通过子账号对数据进行分类管理

### 权限说明

| 角色 | 权限 |
|------|------|
| **超级管理员** | 查看所有子账号 |
| **租户管理员** | 查看本租户的子账号 |
| **Member** | 只能管理自己的子账号 |
| **子账号** | 不能创建或管理子账号 |

---

## 1. 获取子账号列表

子账号API分为管理员端和Member端两个版本。

### 1.1 管理员端：获取所有子账号列表

管理员查看系统中的子账号列表（所有或本租户）。

#### 基本信息

```
GET /api/v1/admin/members/sub-accounts/
```

**权限要求**：
- 超级管理员：查看所有子账号
- 租户管理员：查看本租户的子账号

**内容类型**：`application/json`

#### 请求头

```http
Authorization: Bearer <access_token>
```

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | integer | 否 | 1 | 页码 |
| page_size | integer | 否 | 20 | 每页数量，最大100 |

#### 请求示例

```http
GET /api/v1/admin/members/sub-accounts/?page=1&page_size=20
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

```bash
curl -X GET "http://localhost:8000/api/v1/admin/members/sub-accounts/" \
  -H "Authorization: Bearer <your_token>"
```

---

### 1.2 Member端：获取自己的子账号列表

Member查看自己创建的子账号列表。

#### 基本信息

```
GET /api/v1/members/sub-accounts/
```

**权限要求**：
- Member：只能查看自己的子账号
- 子账号：无权访问

**内容类型**：`application/json`

#### 请求头

```http
Authorization: Bearer <access_token>
```

#### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | integer | 否 | 1 | 页码 |
| page_size | integer | 否 | 20 | 每页数量，最大100 |

#### 请求示例

```http
GET /api/v1/members/sub-accounts/?page=1&page_size=20
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

```bash
curl -X GET "http://localhost:8000/api/v1/members/sub-accounts/" \
  -H "Authorization: Bearer <your_token>"
```

### 成功响应

**状态码**：`200 OK`

**响应体**：

```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "count": 3,
    "next": null,
    "previous": null,
    "results": [
      {
        "id": 20,
        "username": "john_son",
        "email": "son@example.com",
        "phone": "13900001111",
        "nick_name": "儿子账号",
        "avatar": "",
        "wechat_id": null,
        "tenant": 1,
        "tenant_name": "测试租户",
        "parent": 10,
        "parent_username": "john_doe",
        "is_sub_account": true,
        "status": "active",
        "is_active": false,
        "is_deleted": false,
        "date_joined": "2025-01-05T14:20:00Z",
        "last_login": null,
        "last_login_ip": null
      },
      {
        "id": 21,
        "username": "john_daughter",
        "email": "daughter@example.com",
        "phone": "13900002222",
        "nick_name": "女儿账号",
        "avatar": "",
        "wechat_id": null,
        "tenant": 1,
        "tenant_name": "测试租户",
        "parent": 10,
        "parent_username": "john_doe",
        "is_sub_account": true,
        "status": "active",
        "is_active": false,
        "is_deleted": false,
        "date_joined": "2025-01-06T10:30:00Z",
        "last_login": null,
        "last_login_ip": null
      }
    ]
  }
}
```

### 注意事项

- 子账号的`is_active`始终为`false`，不能登录
- 子账号的`parent`字段指向父账号ID
- 子账号的`is_sub_account`字段为`true`

---

## 2. 创建子账号

为当前用户创建子账号。

### 基本信息

```
POST /api/v1/members/sub-accounts/
```

**权限要求**：
- 超级管理员：可以创建
- 租户管理员：可以创建
- Member：可以为自己创建子账号
- 子账号：不能创建子账号

**内容类型**：`application/json`

### 请求头

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

### 请求参数

#### 必填字段

| 字段 | 类型 | 说明 | 验证规则 |
|------|------|------|---------|
| username | string | 用户名 | 1-150字符，系统唯一 |
| email | string | 邮箱地址 | 有效的邮箱格式 |
| password | string | 密码 | 至少8位，包含大小写字母和数字（子账号不能登录，但仍需设置） |
| confirm_password | string | 确认密码 | 必须与password一致 |

#### 可选字段

| 字段 | 类型 | 说明 |
|------|------|------|
| phone | string | 手机号 |
| nick_name | string | 昵称 |
| wechat_id | string | 微信号 |

### 请求体示例

#### 示例1：创建基本子账号

```json
{
  "username": "john_son",
  "email": "son@example.com",
  "password": "Password@123",
  "confirm_password": "Password@123",
  "nick_name": "儿子账号"
}
```

#### 示例2：创建完整信息子账号

```json
{
  "username": "john_daughter",
  "email": "daughter@example.com",
  "password": "SecurePass@123",
  "confirm_password": "SecurePass@123",
  "phone": "13900002222",
  "nick_name": "女儿账号",
  "wechat_id": "wxid_daughter"
}
```

### cURL示例

```bash
curl -X POST "http://localhost:8000/api/v1/members/sub-accounts/" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_son",
    "email": "son@example.com",
    "password": "Password@123",
    "confirm_password": "Password@123",
    "nick_name": "儿子账号"
  }'
```

### 成功响应

**状态码**：`201 Created`

**响应体**：

```json
{
  "success": true,
  "code": 2001,
  "message": "创建成功",
  "data": {
    "id": 20,
    "username": "john_son",
    "email": "son@example.com",
    "phone": null,
    "nick_name": "儿子账号",
    "avatar": "",
    "wechat_id": null,
    "tenant": 1,
    "tenant_name": "测试租户",
    "parent": 10,
    "parent_username": "john_doe",
    "is_sub_account": true,
    "status": "active",
    "is_active": false,
    "is_deleted": false,
    "date_joined": "2025-10-06T10:30:00Z",
    "last_login": null,
    "last_login_ip": null
  }
}
```

### 重要说明

1. **自动关联父账号**：子账号会自动关联到当前登录用户作为父账号
2. **自动设置租户**：子账号的租户自动设置为父账号的租户
3. **禁用登录**：子账号的`is_active`自动设置为`false`，不能登录
4. **用户名唯一性**：子账号的用户名在整个系统中必须唯一

### 错误响应

#### 400 参数验证错误

```json
{
  "success": false,
  "errors": {
    "username": ["该用户名已被使用"],
    "email": ["请输入有效的邮箱地址"]
  }
}
```

#### 403 子账号尝试创建子账号

```json
{
  "detail": "子账号不能创建子账号"
}
```

---

## 3. 获取子账号详情

### 3.1 管理员端：获取子账号详情

```
GET /api/v1/admin/members/sub-accounts/{id}/
```

**权限要求**：
- 超级管理员：可查看任何子账号
- 租户管理员：可查看本租户的子账号

---

### 3.2 Member端：获取自己子账号详情

```
GET /api/v1/members/sub-accounts/{id}/
```

**权限要求**：
- Member：只能查看自己的子账号

### 请求头

```http
Authorization: Bearer <access_token>
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | integer | 是 | 子账号ID |

### 请求示例

```http
GET /api/v1/members/sub-accounts/20/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 成功响应

**状态码**：`200 OK`

**响应体**：返回完整的子账号对象（格式同列表接口中的单个对象）

---

## 4. 更新子账号

### 4.1 管理员端：更新子账号

```
PUT /api/v1/admin/members/sub-accounts/{id}/
PATCH /api/v1/admin/members/sub-accounts/{id}/
```

**权限要求**：
- 超级管理员：可更新任何子账号
- 租户管理员：可更新本租户的子账号

---

### 4.2 Member端：更新自己的子账号

```
PUT /api/v1/members/sub-accounts/{id}/
PATCH /api/v1/members/sub-accounts/{id}/
```

**权限要求**：
- Member：只能更新自己的子账号

### 请求头

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | integer | 是 | 子账号ID |

### 可更新字段

| 字段 | 类型 | 说明 |
|------|------|------|
| email | string | 邮箱地址 |
| phone | string | 手机号 |
| nick_name | string | 昵称 |
| wechat_id | string | 微信号 |
| status | string | 状态 |

### 请求体示例

#### 使用PATCH部分更新

```json
{
  "nick_name": "新昵称",
  "phone": "13900003333"
}
```

### cURL示例

```bash
curl -X PATCH "http://localhost:8000/api/v1/members/sub-accounts/20/" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "nick_name": "新昵称"
  }'
```

### 成功响应

**状态码**：`200 OK`

**响应体**：返回更新后的完整子账号对象

### 注意事项

- 不能修改子账号的`parent`（父账号关系）
- 不能修改子账号的`is_active`（始终为false）
- 不能修改子账号的`username`

---

## 5. 删除子账号

### 5.1 管理员端：删除子账号

```
DELETE /api/v1/admin/members/sub-accounts/{id}/
```

**权限要求**：
- 超级管理员：可删除任何子账号
- 租户管理员：可删除本租户的子账号

---

### 5.2 Member端：删除自己的子账号

```
DELETE /api/v1/members/sub-accounts/{id}/
```

**权限要求**：
- Member：只能删除自己的子账号

### 请求头

```http
Authorization: Bearer <access_token>
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | integer | 是 | 子账号ID |

### 请求示例

```http
DELETE /api/v1/members/sub-accounts/20/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

```bash
curl -X DELETE "http://localhost:8000/api/v1/members/sub-accounts/20/" \
  -H "Authorization: Bearer <your_token>"
```

### 成功响应

**状态码**：`204 No Content`

**响应体**：无内容

---

## 使用示例

### JavaScript/Axios示例

```javascript
import axios from 'axios';

const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  }
});

// 添加请求拦截器
apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 管理员端子账号API封装
const adminSubAccountAPI = {
  // 获取所有子账号列表（管理员）
  async getList(params = {}) {
    const response = await apiClient.get('/api/v1/admin/members/sub-accounts/', { params });
    return response.data.data;
  },
  
  // 获取子账号详情（管理员）
  async getDetail(id) {
    const response = await apiClient.get(`/api/v1/admin/members/sub-accounts/${id}/`);
    return response.data;
  },
  
  // 更新子账号（管理员）
  async update(id, data) {
    const response = await apiClient.patch(`/api/v1/admin/members/sub-accounts/${id}/`, data);
    return response.data;
  },
  
  // 删除子账号（管理员）
  async delete(id) {
    await apiClient.delete(`/api/v1/admin/members/sub-accounts/${id}/`);
    return true;
  }
};

// Member端子账号API封装（Member自己使用）
const memberSubAccountAPI = {
  // 获取自己的子账号列表
  async getMyList(params = {}) {
    const response = await apiClient.get('/api/v1/members/sub-accounts/', { params });
    return response.data.data;
  },
  
  // 创建自己的子账号
  async create(data) {
    const response = await apiClient.post('/api/v1/members/sub-accounts/', data);
    return response.data.data;
  },
  
  // 获取自己子账号详情
  async getDetail(id) {
    const response = await apiClient.get(`/api/v1/members/sub-accounts/${id}/`);
    return response.data;
  },
  
  // 更新自己的子账号
  async update(id, data) {
    const response = await apiClient.patch(`/api/v1/members/sub-accounts/${id}/`, data);
    return response.data;
  },
  
  // 删除自己的子账号
  async delete(id) {
    await apiClient.delete(`/api/v1/members/sub-accounts/${id}/`);
    return true;
  }
};

// 使用示例
async function manageSubAccounts() {
  try {
    // 1. 获取子账号列表
    const listData = await subAccountAPI.getList({ page: 1, page_size: 20 });
    console.log('子账号列表:', listData.results);
    console.log('总数:', listData.count);
    
    // 2. 创建新子账号
    const newSubAccount = await subAccountAPI.create({
      username: 'new_subaccount',
      email: 'sub@example.com',
      password: 'Password@123',
      confirm_password: 'Password@123',
      nick_name: '新子账号'
    });
    console.log('创建成功:', newSubAccount);
    
    // 3. 更新子账号
    const updated = await subAccountAPI.update(newSubAccount.id, {
      nick_name: '更新后的昵称'
    });
    console.log('更新成功:', updated);
    
    // 4. 删除子账号
    await subAccountAPI.delete(newSubAccount.id);
    console.log('删除成功');
    
  } catch (error) {
    console.error('操作失败:', error);
  }
}
```

### Vue 3 组合式API示例

```vue
<template>
  <div class="sub-account-manager">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>子账号管理</span>
          <el-button type="primary" @click="showCreateDialog">
            创建子账号
          </el-button>
        </div>
      </template>
      
      <!-- 子账号列表 -->
      <el-table :data="subAccountList" :loading="loading" border>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="email" label="邮箱" />
        <el-table-column prop="nick_name" label="昵称" />
        <el-table-column prop="phone" label="手机号" />
        <el-table-column prop="parent_username" label="父账号" />
        <el-table-column label="状态" width="100">
          <template #default>
            <el-tag type="info">子账号</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200">
          <template #default="{ row }">
            <el-button size="small" @click="editSubAccount(row)">
              编辑
            </el-button>
            <el-button size="small" type="danger" @click="deleteSubAccount(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        layout="total, prev, pager, next"
        @current-change="fetchSubAccounts"
      />
    </el-card>
    
    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
    >
      <el-form :model="formData" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="用户名" prop="username" v-if="!editMode">
          <el-input v-model="formData.username" />
        </el-form-item>
        
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="formData.email" type="email" />
        </el-form-item>
        
        <el-form-item label="密码" prop="password" v-if="!editMode">
          <el-input v-model="formData.password" type="password" show-password />
          <span class="hint">注意：子账号不能登录，但仍需设置密码</span>
        </el-form-item>
        
        <el-form-item label="确认密码" prop="confirm_password" v-if="!editMode">
          <el-input v-model="formData.confirm_password" type="password" show-password />
        </el-form-item>
        
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="formData.phone" />
        </el-form-item>
        
        <el-form-item label="昵称" prop="nick_name">
          <el-input v-model="formData.nick_name" />
        </el-form-item>
        
        <el-form-item label="微信号" prop="wechat_id">
          <el-input v-model="formData.wechat_id" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import axios from 'axios';

// 数据
const subAccountList = ref([]);
const loading = ref(false);
const currentPage = ref(1);
const pageSize = ref(20);
const total = ref(0);

// 对话框
const dialogVisible = ref(false);
const dialogTitle = ref('创建子账号');
const editMode = ref(false);
const currentEditId = ref(null);
const submitting = ref(false);
const formRef = ref(null);

// 表单数据
const formData = ref({
  username: '',
  email: '',
  password: '',
  confirm_password: '',
  phone: '',
  nick_name: '',
  wechat_id: ''
});

// 表单验证规则
const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码至少8位', trigger: 'blur' }
  ],
  confirm_password: [
    { required: true, message: '请确认密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== formData.value.password) {
          callback(new Error('两次密码不一致'));
        } else {
          callback();
        }
      },
      trigger: 'blur'
    }
  ]
};

// 获取子账号列表
const fetchSubAccounts = async () => {
  loading.value = true;
  try {
    const response = await axios.get('/api/v1/members/sub-accounts/', {
      params: {
        page: currentPage.value,
        page_size: pageSize.value
      }
    });
    
    const data = response.data.data;
    subAccountList.value = data.results;
    total.value = data.count;
  } catch (error) {
    ElMessage.error('获取子账号列表失败');
  } finally {
    loading.value = false;
  }
};

// 显示创建对话框
const showCreateDialog = () => {
  editMode.value = false;
  dialogTitle.value = '创建子账号';
  formData.value = {
    username: '',
    email: '',
    password: '',
    confirm_password: '',
    phone: '',
    nick_name: '',
    wechat_id: ''
  };
  dialogVisible.value = true;
};

// 编辑子账号
const editSubAccount = (subAccount) => {
  editMode.value = true;
  dialogTitle.value = '编辑子账号';
  currentEditId.value = subAccount.id;
  formData.value = {
    email: subAccount.email,
    phone: subAccount.phone || '',
    nick_name: subAccount.nick_name || '',
    wechat_id: subAccount.wechat_id || ''
  };
  dialogVisible.value = true;
};

// 提交表单
const submitForm = async () => {
  try {
    await formRef.value.validate();
    submitting.value = true;
    
    if (editMode.value) {
      // 更新
      await axios.patch(
        `/api/v1/members/sub-accounts/${currentEditId.value}/`,
        formData.value
      );
      ElMessage.success('更新成功');
    } else {
      // 创建
      await axios.post('/api/v1/members/sub-accounts/', formData.value);
      ElMessage.success('创建成功');
    }
    
    dialogVisible.value = false;
    fetchSubAccounts();
    
  } catch (error) {
    if (error.response && error.response.data.errors) {
      const errors = error.response.data.errors;
      for (const [field, messages] of Object.entries(errors)) {
        ElMessage.error(`${field}: ${messages.join(', ')}`);
      }
    } else {
      ElMessage.error(editMode.value ? '更新失败' : '创建失败');
    }
  } finally {
    submitting.value = false;
  }
};

// 删除子账号
const deleteSubAccount = async (subAccount) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除子账号 "${subAccount.username}" 吗？`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );
    
    await axios.delete(`/api/v1/members/sub-accounts/${subAccount.id}/`);
    ElMessage.success('删除成功');
    fetchSubAccounts();
    
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败');
    }
  }
};

onMounted(() => {
  fetchSubAccounts();
});
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.hint {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
```

---

## 前端实现参考

### 子账号管理页面功能清单

- [x] 子账号列表展示
- [x] 创建子账号
- [x] 编辑子账号
- [x] 删除子账号
- [x] 显示父账号关系
- [x] 分页功能
- [x] 表单验证
- [x] Loading状态
- [x] 错误处理

### UI建议

1. **视觉区分**：在列表中用不同颜色或图标标识子账号
2. **关系显示**：清晰显示父账号与子账号的关系
3. **提示说明**：在创建时提示子账号不能登录
4. **操作限制**：子账号不显示"创建子账号"按钮

### 最佳实践

1. **批量导入**：提供Excel导入功能批量创建子账号
2. **关系图谱**：可视化展示父子账号关系树
3. **快速切换**：在父账号详情页直接管理其子账号
4. **数据统计**：显示每个父账号的子账号数量

---

## 下一步

继续阅读：

📔 **member_avatar_api.md** - 头像上传管理API

