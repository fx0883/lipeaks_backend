# Member 详情、更新和删除 API

本文档详细说明Member的详情查询、更新和删除操作的API接口。

---

## 目录

- [1. 获取Member详情](#1-获取member详情)
- [2. 完整更新Member](#2-完整更新member)
- [3. 部分更新Member](#3-部分更新member)
- [4. 删除Member](#4-删除member)
- [使用示例](#使用示例)
- [前端实现参考](#前端实现参考)

---

## 1. 获取Member详情

获取单个Member的详细信息。

### 基本信息

```
GET /api/v1/admin/members/{id}/
```

**权限要求**：
- 超级管理员：可查看任何Member
- 租户管理员：只能查看自己租户的Member
- Member：只能查看自己

**内容类型**：`application/json`

### 请求头

```http
Authorization: Bearer <access_token>
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | integer | 是 | Member的ID |

### 请求示例

```http
GET /api/v1/admin/members/10/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

```bash
curl -X GET "http://localhost:8000/api/v1/admin/members/10/" \
  -H "Authorization: Bearer <your_token>"
```

### 成功响应

**状态码**：`200 OK`

**响应体**：

```json
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
}
```

### 错误响应

#### 403 权限不足

```json
{
  "detail": "You do not have permission to perform this action."
}
```

#### 404 Member不存在

```json
{
  "detail": "Not found."
}
```

---

## 2. 完整更新Member

完整更新Member信息，需要提供所有字段。

### 基本信息

```
PUT /api/v1/admin/members/{id}/
```

**权限要求**：
- 超级管理员：可更新任何Member
- 租户管理员：只能更新自己租户的Member
- Member：只能更新自己

**内容类型**：`application/json`

### 请求头

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | integer | 是 | Member的ID |

### 请求参数

#### 可更新字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| email | string | 是 | 邮箱地址 |
| phone | string | 否 | 手机号 |
| nick_name | string | 否 | 昵称 |
| wechat_id | string | 否 | 微信号 |
| status | string | 否 | 状态：active/suspended/inactive |
| is_active | boolean | 否 | 是否激活 |

#### 不可更新字段

- `username` - 用户名不可修改
- `password` - 密码通过专门的修改密码API修改
- `tenant` - 租户不可修改
- `parent` - 父账号关系不可修改

### 请求体示例

```json
{
  "email": "newemail@example.com",
  "phone": "13900000000",
  "nick_name": "新昵称",
  "wechat_id": "new_wxid",
  "status": "active",
  "is_active": true
}
```

### cURL示例

```bash
curl -X PUT "http://localhost:8000/api/v1/admin/members/10/" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newemail@example.com",
    "phone": "13900000000",
    "nick_name": "新昵称",
    "status": "active"
  }'
```

### 成功响应

**状态码**：`200 OK`

**响应体**：返回更新后的完整Member对象

```json
{
  "id": 10,
  "username": "john_doe",
  "email": "newemail@example.com",
  "phone": "13900000000",
  "nick_name": "新昵称",
  "avatar": "/media/avatars/abc123.jpg",
  "wechat_id": "new_wxid",
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
}
```

### 错误响应

#### 400 参数验证错误

```json
{
  "success": false,
  "errors": {
    "email": ["请输入有效的邮箱地址"],
    "phone": ["手机号格式不正确"]
  }
}
```

#### 403 权限不足

```json
{
  "detail": "You do not have permission to perform this action."
}
```

#### 404 Member不存在

```json
{
  "detail": "Not found."
}
```

---

## 3. 部分更新Member

部分更新Member信息，只需要提供要修改的字段。

### 基本信息

```
PATCH /api/v1/admin/members/{id}/
```

**权限要求**：同PUT方法

**内容类型**：`application/json`

### 请求头

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | integer | 是 | Member的ID |

### 请求参数

只需提供要更新的字段，支持的字段与PUT方法相同。

### 请求体示例

#### 示例1：只更新昵称

```json
{
  "nick_name": "新昵称"
}
```

#### 示例2：更新状态

```json
{
  "status": "suspended"
}
```

#### 示例3：更新邮箱和手机号

```json
{
  "email": "newemail@example.com",
  "phone": "13900139000"
}
```

#### 示例4：暂停Member（禁用登录）

```json
{
  "status": "suspended",
  "is_active": false
}
```

### cURL示例

```bash
curl -X PATCH "http://localhost:8000/api/v1/admin/members/10/" \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "suspended",
    "is_active": false
  }'
```

### 成功响应

**状态码**：`200 OK`

**响应体**：返回更新后的完整Member对象

```json
{
  "id": 10,
  "username": "john_doe",
  "email": "john@example.com",
  "phone": "13800138000",
  "nick_name": "新昵称",
  "avatar": "/media/avatars/abc123.jpg",
  "wechat_id": "wxid_john",
  "tenant": 1,
  "tenant_name": "测试租户",
  "parent": null,
  "parent_username": null,
  "is_sub_account": false,
  "status": "suspended",
  "is_active": false,
  "is_deleted": false,
  "date_joined": "2025-01-01T10:00:00Z",
  "last_login": "2025-01-10T15:30:00Z",
  "last_login_ip": "192.168.1.100"
}
```

### 错误响应

同PUT方法。

---

## 4. 删除Member

删除Member（软删除），不会从数据库中物理删除，而是标记为已删除。

### 基本信息

```
DELETE /api/v1/admin/members/{id}/
```

**权限要求**：
- 超级管理员：可删除任何Member
- 租户管理员：只能删除自己租户的Member
- ❌ 不能删除当前登录的Member

**内容类型**：`application/json`

### 请求头

```http
Authorization: Bearer <access_token>
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | integer | 是 | Member的ID |

### 请求示例

```http
DELETE /api/v1/admin/members/10/
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

```bash
curl -X DELETE "http://localhost:8000/api/v1/admin/members/10/" \
  -H "Authorization: Bearer <your_token>"
```

### 成功响应

**状态码**：`204 No Content`

**响应体**：无内容

### 错误响应

#### 400 尝试删除当前登录账号

```json
{
  "detail": "不能删除当前登录的账号"
}
```

#### 403 权限不足

```json
{
  "detail": "You do not have permission to perform this action."
}
```

#### 404 Member不存在

```json
{
  "detail": "Not found."
}
```

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

// 1. 获取Member详情
async function getMemberDetail(memberId) {
  try {
    const response = await apiClient.get(`/users/members/${memberId}/`);
    return response.data;
  } catch (error) {
    console.error('获取Member详情失败:', error);
    throw error;
  }
}

// 使用示例
const member = await getMemberDetail(10);
console.log('Member详情:', member);

// 2. 完整更新Member
async function updateMember(memberId, memberData) {
  try {
    const response = await apiClient.put(`/users/members/${memberId}/`, memberData);
    return response.data;
  } catch (error) {
    console.error('更新Member失败:', error);
    throw error;
  }
}

// 使用示例
const updatedMember = await updateMember(10, {
  email: 'newemail@example.com',
  phone: '13900139000',
  nick_name: '新昵称',
  status: 'active'
});

// 3. 部分更新Member
async function patchMember(memberId, partialData) {
  try {
    const response = await apiClient.patch(`/users/members/${memberId}/`, partialData);
    return response.data;
  } catch (error) {
    console.error('更新Member失败:', error);
    throw error;
  }
}

// 使用示例 - 只更新昵称
await patchMember(10, { nick_name: '新昵称' });

// 使用示例 - 暂停Member
await patchMember(10, { status: 'suspended', is_active: false });

// 4. 删除Member
async function deleteMember(memberId) {
  try {
    await apiClient.delete(`/users/members/${memberId}/`);
    return true;
  } catch (error) {
    console.error('删除Member失败:', error);
    throw error;
  }
}

// 使用示例
const success = await deleteMember(10);
if (success) {
  console.log('Member删除成功');
}
```

### Vue 3 组合式API示例

```vue
<template>
  <div class="member-detail" v-loading="loading">
    <!-- 详情显示 -->
    <el-card v-if="member" class="detail-card">
      <template #header>
        <div class="card-header">
          <span>Member详情</span>
          <div class="actions">
            <el-button @click="showEditDialog">编辑</el-button>
            <el-button type="danger" @click="confirmDelete">删除</el-button>
          </div>
        </div>
      </template>
      
      <el-descriptions :column="2" border>
        <el-descriptions-item label="ID">{{ member.id }}</el-descriptions-item>
        <el-descriptions-item label="用户名">{{ member.username }}</el-descriptions-item>
        <el-descriptions-item label="邮箱">{{ member.email }}</el-descriptions-item>
        <el-descriptions-item label="手机号">{{ member.phone || '-' }}</el-descriptions-item>
        <el-descriptions-item label="昵称">{{ member.nick_name || '-' }}</el-descriptions-item>
        <el-descriptions-item label="微信号">{{ member.wechat_id || '-' }}</el-descriptions-item>
        <el-descriptions-item label="租户">{{ member.tenant_name }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(member.status)">
            {{ getStatusText(member.status) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="是否激活">
          <el-tag :type="member.is_active ? 'success' : 'danger'">
            {{ member.is_active ? '是' : '否' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="是否子账号">
          {{ member.is_sub_account ? '是' : '否' }}
        </el-descriptions-item>
        <el-descriptions-item label="父账号">
          {{ member.parent_username || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="注册时间">
          {{ formatDate(member.date_joined) }}
        </el-descriptions-item>
        <el-descriptions-item label="最后登录">
          {{ member.last_login ? formatDate(member.last_login) : '从未登录' }}
        </el-descriptions-item>
        <el-descriptions-item label="最后登录IP">
          {{ member.last_login_ip || '-' }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
    
    <!-- 编辑对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑Member"
      width="600px"
    >
      <el-form :model="editForm" :rules="editRules" ref="editFormRef" label-width="100px">
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="editForm.email" type="email" />
        </el-form-item>
        
        <el-form-item label="手机号" prop="phone">
          <el-input v-model="editForm.phone" />
        </el-form-item>
        
        <el-form-item label="昵称" prop="nick_name">
          <el-input v-model="editForm.nick_name" />
        </el-form-item>
        
        <el-form-item label="微信号" prop="wechat_id">
          <el-input v-model="editForm.wechat_id" />
        </el-form-item>
        
        <el-form-item label="状态" prop="status">
          <el-select v-model="editForm.status">
            <el-option label="活跃" value="active" />
            <el-option label="暂停" value="suspended" />
            <el-option label="未激活" value="inactive" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="是否激活" prop="is_active">
          <el-switch v-model="editForm.is_active" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitEdit" :loading="submitting">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import axios from 'axios';
import dayjs from 'dayjs';

const route = useRoute();
const router = useRouter();

// 数据
const loading = ref(false);
const member = ref(null);
const memberId = ref(parseInt(route.params.id));

// 编辑对话框
const editDialogVisible = ref(false);
const submitting = ref(false);
const editFormRef = ref(null);
const editForm = ref({
  email: '',
  phone: '',
  nick_name: '',
  wechat_id: '',
  status: 'active',
  is_active: true
});

// 表单验证规则
const editRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入有效的邮箱', trigger: 'blur' }
  ],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号', trigger: 'blur' }
  ]
};

// 获取Member详情
const fetchMemberDetail = async () => {
  loading.value = true;
  try {
    const response = await axios.get(`/api/v1/admin/members/${memberId.value}/`);
    member.value = response.data;
  } catch (error) {
    if (error.response && error.response.status === 404) {
      ElMessage.error('Member不存在');
      router.push('/members');
    } else if (error.response && error.response.status === 403) {
      ElMessage.error('权限不足');
      router.push('/members');
    } else {
      ElMessage.error('获取Member详情失败');
    }
  } finally {
    loading.value = false;
  }
};

// 显示编辑对话框
const showEditDialog = () => {
  editForm.value = {
    email: member.value.email,
    phone: member.value.phone || '',
    nick_name: member.value.nick_name || '',
    wechat_id: member.value.wechat_id || '',
    status: member.value.status,
    is_active: member.value.is_active
  };
  editDialogVisible.value = true;
};

// 提交编辑
const submitEdit = async () => {
  try {
    await editFormRef.value.validate();
    
    submitting.value = true;
    
    const response = await axios.patch(
      `/api/v1/admin/members/${memberId.value}/`,
      editForm.value
    );
    
    member.value = response.data;
    ElMessage.success('更新成功');
    editDialogVisible.value = false;
    
  } catch (error) {
    if (error.response && error.response.data.errors) {
      const errors = error.response.data.errors;
      for (const [field, messages] of Object.entries(errors)) {
        ElMessage.error(`${field}: ${messages.join(', ')}`);
      }
    } else {
      ElMessage.error('更新失败');
    }
  } finally {
    submitting.value = false;
  }
};

// 确认删除
const confirmDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除Member "${member.value.username}" 吗？此操作不可恢复！`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    );
    
    await deleteMember();
  } catch (error) {
    // 用户取消操作
  }
};

// 删除Member
const deleteMember = async () => {
  loading.value = true;
  try {
    await axios.delete(`/api/v1/admin/members/${memberId.value}/`);
    ElMessage.success('删除成功');
    router.push('/members');
  } catch (error) {
    if (error.response && error.response.status === 400) {
      ElMessage.error(error.response.data.detail);
    } else if (error.response && error.response.status === 403) {
      ElMessage.error('权限不足');
    } else {
      ElMessage.error('删除失败');
    }
  } finally {
    loading.value = false;
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

// 格式化日期
const formatDate = (dateString) => {
  return dayjs(dateString).format('YYYY-MM-DD HH:mm:ss');
};

// 组件挂载时获取数据
onMounted(() => {
  fetchMemberDetail();
});
</script>

<style scoped>
.member-detail {
  padding: 20px;
}

.detail-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
```

---

## 前端实现参考

### 详情页面功能清单

- [x] Member详情展示
- [x] 编辑按钮
- [x] 删除按钮
- [x] 编辑对话框
- [x] 表单验证
- [x] 状态显示（标签）
- [x] 日期格式化
- [x] Loading状态
- [x] 权限控制
- [x] 错误处理

### 状态管理建议

```javascript
// 状态枚举
const MemberStatus = {
  ACTIVE: 'active',
  SUSPENDED: 'suspended',
  INACTIVE: 'inactive'
};

// 状态显示配置
const statusConfig = {
  active: { text: '活跃', type: 'success', icon: '✓' },
  suspended: { text: '暂停', type: 'warning', icon: '⚠' },
  inactive: { text: '未激活', type: 'info', icon: '○' }
};

// 获取状态配置
function getStatusConfig(status) {
  return statusConfig[status] || statusConfig.inactive;
}
```

### 快速操作建议

为提高用户体验，可以在列表页直接提供快速操作：

```javascript
// 快速暂停Member
async function quickSuspend(memberId) {
  try {
    await axios.patch(`/api/v1/admin/members/${memberId}/`, {
      status: 'suspended',
      is_active: false
    });
    ElMessage.success('已暂停该Member');
  } catch (error) {
    ElMessage.error('操作失败');
  }
}

// 快速激活Member
async function quickActivate(memberId) {
  try {
    await axios.patch(`/api/v1/admin/members/${memberId}/`, {
      status: 'active',
      is_active: true
    });
    ElMessage.success('已激活该Member');
  } catch (error) {
    ElMessage.error('操作失败');
  }
}
```

### 批量操作建议

```javascript
// 批量删除Member
async function batchDelete(memberIds) {
  try {
    // 逐个删除
    const promises = memberIds.map(id => 
      axios.delete(`/api/v1/admin/members/${id}/`)
    );
    
    await Promise.all(promises);
    ElMessage.success(`成功删除${memberIds.length}个Member`);
    
  } catch (error) {
    ElMessage.error('批量删除失败');
  }
}

// 批量更新状态
async function batchUpdateStatus(memberIds, status) {
  try {
    const promises = memberIds.map(id => 
      axios.patch(`/api/v1/admin/members/${id}/`, { status })
    );
    
    await Promise.all(promises);
    ElMessage.success(`成功更新${memberIds.length}个Member的状态`);
    
  } catch (error) {
    ElMessage.error('批量更新失败');
  }
}
```

---

## 下一步

继续阅读：

📕 **member_subaccount_api.md** - 子账号管理API

