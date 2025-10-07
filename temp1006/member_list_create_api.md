# Member 列表和创建 API

本文档详细说明Member列表查询和创建的API接口。

---

## 目录

- [1. 获取Member列表](#1-获取member列表)
- [2. 创建新Member](#2-创建新member)
- [使用示例](#使用示例)
- [前端实现参考](#前端实现参考)

---

## 1. 获取Member列表

获取系统中的Member列表，支持搜索、筛选和分页。

### 基本信息

```
GET /api/v1/admin/members/
```

**权限要求**：管理员（超级管理员或租户管理员）

**内容类型**：`application/json`

### 请求头

```http
Authorization: Bearer <access_token>
```

### 查询参数

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | integer | 否 | 1 | 页码，从1开始 |
| page_size | integer | 否 | 20 | 每页数量，最大100 |
| search | string | 否 | - | 搜索关键词，支持用户名、邮箱、昵称、手机号模糊搜索 |
| status | string | 否 | - | 状态筛选：`active`, `suspended`, `inactive` |
| is_sub_account | boolean | 否 | - | 是否为子账号：`true`, `false` |
| parent | integer | 否 | - | 父账号ID，筛选特定父账号的子账号 |
| tenant_id | integer | 否 | - | 租户ID筛选（仅超级管理员可用） |

### 请求示例

#### 示例1：获取第一页Member列表

```http
GET /api/v1/admin/members/?page=1&page_size=20
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

```bash
curl -X GET "http://localhost:8000/api/v1/admin/members/?page=1&page_size=20" \
  -H "Authorization: Bearer <your_token>"
```

#### 示例2：搜索用户名包含"john"的Member

```http
GET /api/v1/admin/members/?search=john
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

```bash
curl -X GET "http://localhost:8000/api/v1/admin/members/?search=john" \
  -H "Authorization: Bearer <your_token>"
```

#### 示例3：筛选活跃状态的Member

```http
GET /api/v1/admin/members/?status=active&page_size=50
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### 示例4：仅获取子账号

```http
GET /api/v1/admin/members/?is_sub_account=true
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### 示例5：获取特定父账号的子账号

```http
GET /api/v1/admin/members/?parent=10
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### 示例6：超级管理员筛选特定租户的Member

```http
GET /api/v1/admin/members/?tenant_id=1&page=1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
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
    "count": 100,
    "next": "http://localhost:8000/api/v1/admin/members/?page=2",
    "previous": null,
    "results": [
      {
        "id": 10,
        "username": "john_doe",
        "email": "john@example.com",
        "phone": "13800138000",
        "nick_name": "John",
        "avatar": "/media/avatars/abc123.jpg",
        "wechat_id": "wxid_john",
        "tenant": 1,
        "tenant_name": "测试租户",
        "parent": null,
        "parent_username": null,
        "is_sub_account": false,
        "status": "active",
        "is_active": true,
        "is_deleted": false,
        "date_joined": "2025-01-01T10:00:00Z",
        "last_login": "2025-01-10T15:30:00Z",
        "last_login_ip": "192.168.1.100"
      },
      {
        "id": 11,
        "username": "jane_smith",
        "email": "jane@example.com",
        "phone": "13900139000",
        "nick_name": "Jane",
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
      }
    ]
  }
}
```

### 响应字段说明

#### 分页信息

| 字段 | 类型 | 说明 |
|------|------|------|
| count | integer | 总记录数 |
| next | string \| null | 下一页的URL，如果是最后一页则为null |
| previous | string \| null | 上一页的URL，如果是第一页则为null |
| results | array | 当前页的Member对象数组 |

#### Member对象字段

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | Member ID |
| username | string | 用户名 |
| email | string | 邮箱 |
| phone | string \| null | 手机号 |
| nick_name | string \| null | 昵称 |
| avatar | string | 头像URL |
| wechat_id | string \| null | 微信号 |
| tenant | integer | 租户ID |
| tenant_name | string | 租户名称 |
| parent | integer \| null | 父账号ID（子账号时有值） |
| parent_username | string \| null | 父账号用户名 |
| is_sub_account | boolean | 是否为子账号 |
| status | string | 状态：active/suspended/inactive |
| is_active | boolean | 是否激活 |
| is_deleted | boolean | 是否已删除 |
| date_joined | string | 注册时间（ISO 8601） |
| last_login | string \| null | 最后登录时间 |
| last_login_ip | string \| null | 最后登录IP |

### 错误响应

#### 401 未认证

```json
{
  "detail": "Authentication credentials were not provided."
}
```

#### 403 权限不足

```json
{
  "detail": "You do not have permission to perform this action."
}
```

#### 500 服务器错误

```json
{
  "detail": "获取普通用户列表失败: <error_message>"
}
```

---

## 2. 创建新Member

创建一个新的Member用户。

### 基本信息

```
POST /api/v1/admin/members/
```

**权限要求**：管理员（超级管理员或租户管理员）

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
| username | string | 用户名 | 1-150字符，只能包含字母、数字、下划线、@、+、. 和 - |
| email | string | 邮箱地址 | 必须是有效的邮箱格式 |
| password | string | 密码 | 至少8位，必须包含大小写字母和数字 |
| confirm_password | string | 确认密码 | 必须与password一致 |

#### 可选字段

| 字段 | 类型 | 说明 | 验证规则 |
|------|------|------|---------|
| phone | string | 手机号 | 最多11个字符 |
| nick_name | string | 昵称 | 最多30个字符 |
| wechat_id | string | 微信号 | 最多32个字符 |
| tenant_id | integer | 租户ID | 仅超级管理员可指定；租户管理员自动使用当前租户 |

### 请求体示例

#### 示例1：租户管理员创建Member（基本信息）

```json
{
  "username": "newmember",
  "email": "newmember@example.com",
  "password": "Password@123",
  "confirm_password": "Password@123"
}
```

#### 示例2：创建Member（完整信息）

```json
{
  "username": "john_doe",
  "email": "john@example.com",
  "password": "SecurePass@123",
  "confirm_password": "SecurePass@123",
  "phone": "13900139000",
  "nick_name": "John Doe",
  "wechat_id": "wxid_john123"
}
```

#### 示例3：超级管理员为特定租户创建Member

```json
{
  "username": "tenant_member",
  "email": "member@tenant.com",
  "password": "TenantPass@123",
  "confirm_password": "TenantPass@123",
  "phone": "13800138000",
  "nick_name": "租户成员",
  "tenant_id": 5
}
```

### cURL示例

```bash
curl -X POST "http://localhost:8000/api/v1/admin/members/" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newmember",
    "email": "newmember@example.com",
    "password": "Password@123",
    "confirm_password": "Password@123",
    "phone": "13900139000",
    "nick_name": "新成员"
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
    "id": 15,
    "username": "newmember",
    "email": "newmember@example.com",
    "phone": "13900139000",
    "nick_name": "新成员",
    "avatar": "",
    "wechat_id": null,
    "tenant": 1,
    "tenant_name": "测试租户",
    "parent": null,
    "parent_username": null,
    "is_sub_account": false,
    "status": "active",
    "is_active": true,
    "is_deleted": false,
    "date_joined": "2025-10-06T10:30:00Z",
    "last_login": null,
    "last_login_ip": null
  }
}
```

### 错误响应

#### 400 参数验证错误

**场景1：缺少必填字段**

```json
{
  "success": false,
  "errors": {
    "username": ["该字段为必填项。"],
    "email": ["该字段为必填项。"],
    "password": ["该字段为必填项。"]
  }
}
```

**场景2：密码不一致**

```json
{
  "success": false,
  "errors": {
    "confirm_password": ["两次输入的密码不一致"]
  }
}
```

**场景3：密码强度不足**

```json
{
  "success": false,
  "errors": {
    "password": ["密码必须至少8个字符，且包含大小写字母和数字"]
  }
}
```

**场景4：用户名已存在**

```json
{
  "success": false,
  "errors": {
    "username": ["该用户名已被使用"]
  }
}
```

**场景5：邮箱已存在**

```json
{
  "success": false,
  "errors": {
    "email": ["该邮箱已被使用"]
  }
}
```

**场景6：邮箱格式无效**

```json
{
  "success": false,
  "errors": {
    "email": ["请输入有效的邮箱地址"]
  }
}
```

#### 400 租户配额已满

```json
{
  "success": false,
  "error": "租户成员配额已满，无法创建更多成员",
  "code": "QUOTA_EXCEEDED"
}
```

#### 401 未认证

```json
{
  "detail": "Authentication credentials were not provided."
}
```

#### 403 权限不足

**场景1：非管理员尝试创建**

```json
{
  "detail": "You do not have permission to perform this action."
}
```

**场景2：租户管理员尝试指定其他租户**

```json
{
  "detail": "您只能在自己的租户下创建用户"
}
```

**场景3：租户管理员没有关联租户**

```json
{
  "detail": "您没有关联的租户，无法创建普通用户"
}
```

---

## 使用示例

### JavaScript/Axios示例

#### 获取Member列表

```javascript
import axios from 'axios';

// 创建axios实例
const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  }
});

// 添加请求拦截器，自动添加token
apiClient.interceptors.request.use(config => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 获取Member列表
async function getMemberList(params = {}) {
  try {
    const response = await apiClient.get('/users/members/', { params });
    return response.data.data;
  } catch (error) {
    console.error('获取Member列表失败:', error);
    throw error;
  }
}

// 使用示例
const listData = await getMemberList({
  page: 1,
  page_size: 20,
  search: 'john',
  status: 'active'
});

console.log('总数:', listData.count);
console.log('Member列表:', listData.results);
```

#### 创建新Member

```javascript
// 创建Member
async function createMember(memberData) {
  try {
    const response = await apiClient.post('/users/members/', memberData);
    return response.data.data;
  } catch (error) {
    if (error.response && error.response.data.errors) {
      // 处理字段验证错误
      const errors = error.response.data.errors;
      console.error('验证错误:', errors);
      throw errors;
    }
    throw error;
  }
}

// 使用示例
try {
  const newMember = await createMember({
    username: 'newuser',
    email: 'newuser@example.com',
    password: 'Password@123',
    confirm_password: 'Password@123',
    phone: '13900139000',
    nick_name: '新用户'
  });
  
  console.log('创建成功:', newMember);
  // 显示成功提示
  alert(`Member ${newMember.username} 创建成功！`);
  
} catch (errors) {
  // 显示错误信息
  if (typeof errors === 'object') {
    for (const [field, messages] of Object.entries(errors)) {
      console.error(`${field}: ${messages.join(', ')}`);
    }
  }
}
```

### Vue 3组合式API示例

```vue
<template>
  <div class="member-list">
    <!-- 搜索和筛选 -->
    <div class="filters">
      <el-input
        v-model="searchKeyword"
        placeholder="搜索用户名、邮箱、手机号"
        @input="onSearchInput"
        clearable
      />
      
      <el-select v-model="statusFilter" placeholder="状态筛选" @change="fetchMembers">
        <el-option label="全部" value="" />
        <el-option label="活跃" value="active" />
        <el-option label="暂停" value="suspended" />
        <el-option label="未激活" value="inactive" />
      </el-select>
      
      <el-button type="primary" @click="showCreateDialog">创建Member</el-button>
    </div>
    
    <!-- Member列表表格 -->
    <el-table :data="memberList" :loading="loading" border>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="email" label="邮箱" />
      <el-table-column prop="phone" label="手机号" />
      <el-table-column prop="nick_name" label="昵称" />
      <el-table-column prop="tenant_name" label="租户" />
      <el-table-column prop="status" label="状态">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200">
        <template #default="{ row }">
          <el-button size="small" @click="editMember(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="deleteMember(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <!-- 分页 -->
    <el-pagination
      v-model:current-page="currentPage"
      v-model:page-size="pageSize"
      :total="total"
      :page-sizes="[10, 20, 50, 100]"
      layout="total, sizes, prev, pager, next, jumper"
      @current-change="fetchMembers"
      @size-change="fetchMembers"
    />
    
    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
    >
      <el-form :model="formData" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="formData.username" />
        </el-form-item>
        
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="formData.email" type="email" />
        </el-form-item>
        
        <el-form-item label="密码" prop="password" v-if="!editMode">
          <el-input v-model="formData.password" type="password" show-password />
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
        
        <el-form-item label="租户" prop="tenant_id" v-if="isSuperAdmin">
          <el-select v-model="formData.tenant_id" placeholder="选择租户">
            <el-option
              v-for="tenant in tenantList"
              :key="tenant.id"
              :label="tenant.name"
              :value="tenant.id"
            />
          </el-select>
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
import { ref, computed, onMounted } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import { debounce } from 'lodash';
import axios from 'axios';

// 数据
const memberList = ref([]);
const loading = ref(false);
const currentPage = ref(1);
const pageSize = ref(20);
const total = ref(0);
const searchKeyword = ref('');
const statusFilter = ref('');

// 对话框
const dialogVisible = ref(false);
const dialogTitle = ref('创建Member');
const editMode = ref(false);
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
  tenant_id: null
});

// 用户信息
const currentUser = ref({
  is_super_admin: false,
  is_admin: true,
  tenant_id: 1
});

const isSuperAdmin = computed(() => currentUser.value.is_super_admin);

// 表单验证规则
const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 1, max: 150, message: '用户名长度1-150字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 8, message: '密码至少8位', trigger: 'blur' },
    {
      pattern: /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
      message: '密码必须包含大小写字母和数字',
      trigger: 'blur'
    }
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
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号', trigger: 'blur' }
  ]
};

// 获取Member列表
const fetchMembers = async () => {
  loading.value = true;
  try {
    const response = await axios.get('/api/v1/admin/members/', {
      params: {
        page: currentPage.value,
        page_size: pageSize.value,
        search: searchKeyword.value,
        status: statusFilter.value
      }
    });
    
    const data = response.data.data;
    memberList.value = data.results;
    total.value = data.count;
  } catch (error) {
    ElMessage.error('获取Member列表失败');
    console.error(error);
  } finally {
    loading.value = false;
  }
};

// 搜索输入（防抖）
const onSearchInput = debounce(() => {
  currentPage.value = 1;
  fetchMembers();
}, 300);

// 显示创建对话框
const showCreateDialog = () => {
  editMode.value = false;
  dialogTitle.value = '创建Member';
  formData.value = {
    username: '',
    email: '',
    password: '',
    confirm_password: '',
    phone: '',
    nick_name: '',
    tenant_id: null
  };
  dialogVisible.value = true;
};

// 提交表单
const submitForm = async () => {
  try {
    await formRef.value.validate();
    
    submitting.value = true;
    
    const response = await axios.post('/api/v1/admin/members/', formData.value);
    
    ElMessage.success('创建成功');
    dialogVisible.value = false;
    fetchMembers();
    
  } catch (error) {
    if (error.response && error.response.data.errors) {
      // 显示字段验证错误
      const errors = error.response.data.errors;
      for (const [field, messages] of Object.entries(errors)) {
        ElMessage.error(`${field}: ${messages.join(', ')}`);
      }
    } else {
      ElMessage.error('创建失败');
    }
  } finally {
    submitting.value = false;
  }
};

// 状态类型映射
const getStatusType = (status) => {
  const map = {
    active: 'success',
    suspended: 'warning',
    inactive: 'info'
  };
  return map[status] || 'info';
};

// 状态文本映射
const getStatusText = (status) => {
  const map = {
    active: '活跃',
    suspended: '暂停',
    inactive: '未激活'
  };
  return map[status] || status;
};

// 组件挂载时获取数据
onMounted(() => {
  fetchMembers();
});
</script>
```

---

## 前端实现参考

### 列表页面功能清单

- [x] Member列表展示（表格）
- [x] 分页功能
- [x] 搜索功能（用户名、邮箱、手机号）
- [x] 状态筛选
- [x] 子账号筛选
- [x] 租户筛选（超级管理员）
- [x] 创建按钮
- [x] 编辑按钮
- [x] 删除按钮
- [x] Loading状态
- [x] 错误处理

### 创建表单功能清单

- [x] 用户名输入
- [x] 邮箱输入
- [x] 密码输入（带强度提示）
- [x] 确认密码输入
- [x] 手机号输入
- [x] 昵称输入
- [x] 租户选择（仅超级管理员）
- [x] 表单验证
- [x] 提交Loading状态
- [x] 错误提示

### 建议的UI组件库

- **Element Plus** (Vue 3)
- **Ant Design Vue** (Vue 3)
- **Ant Design** (React)
- **Material-UI** (React)

---

## 下一步

继续阅读：

📙 **member_detail_api.md** - Member详情、更新和删除API

