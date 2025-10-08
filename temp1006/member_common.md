# Member API 通用说明

本文档包含Member管理API的通用说明，包括认证、权限、错误码和数据模型。

---

## 目录

- [认证说明](#认证说明)
- [权限体系](#权限体系)
- [错误码说明](#错误码说明)
- [数据模型](#数据模型)
- [公共参数](#公共参数)
- [租户隔离](#租户隔离)

---

## 认证说明

### JWT令牌认证

所有API请求必须在请求头中携带有效的JWT访问令牌：

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 获取令牌

通过登录API获取令牌：

```http
POST /api/v1/users/auth/login/
Content-Type: application/json

{
  "username": "admin",
  "password": "admin_password"
}
```

响应：
```json
{
  "success": true,
  "code": 2000,
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 1,
      "username": "admin",
      "is_admin": true,
      "is_super_admin": true
    }
  }
}
```

### 令牌刷新

访问令牌过期后，使用刷新令牌获取新的访问令牌：

```http
POST /api/v1/users/auth/token/refresh/
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 令牌有效期

- **访问令牌(Access Token)**：24小时
- **刷新令牌(Refresh Token)**：7天

---

## 权限体系

### 用户角色类型

系统中有两种用户类型：

| 用户类型 | 模型 | 说明 |
|---------|------|------|
| 管理员用户 | User | 包括超级管理员和租户管理员 |
| 普通用户 | Member | 包括普通成员和子账号 |

### 权限级别

#### 1. 超级管理员 (Super Admin)

**识别标志**：
- `is_super_admin = true`
- `is_admin = true`
- `tenant = null`

**权限范围**：
- ✅ 查看所有租户的所有Member
- ✅ 创建任意租户下的Member
- ✅ 编辑/删除任意租户的Member
- ✅ 为任意Member上传头像
- ✅ 查看所有子账号
- ✅ 可以指定Member的租户

#### 2. 租户管理员 (Tenant Admin)

**识别标志**：
- `is_super_admin = false`
- `is_admin = true`
- `tenant` 存在

**权限范围**：
- ✅ 查看自己租户的Member
- ✅ 创建自己租户的Member（自动设置为当前租户）
- ✅ 编辑/删除自己租户的Member
- ✅ 为自己租户的Member上传头像
- ✅ 查看自己租户的子账号
- ❌ 不能访问其他租户的Member
- ❌ 不能指定Member的租户

#### 3. 普通Member

**识别标志**：
- `is_admin = false`
- `is_member = true`

**权限范围**：
- ✅ 查看/编辑自己的信息
- ✅ 创建/管理自己的子账号
- ✅ 上传自己和子账号的头像
- ❌ 不能访问其他Member信息
- ❌ 不能进行管理操作

### 权限验证流程

```javascript
// 前端API路径选择示例
function getMemberAPIBasePath(currentUser) {
  // 管理员使用管理员端API
  if (currentUser.is_admin || currentUser.is_super_admin) {
    return '/api/v1/admin/members';
  }
  // Member使用Member端API
  return '/api/v1/members';
}

// 前端权限检查示例
function canManageMember(currentUser, targetMember) {
  // 超级管理员可以管理所有Member
  if (currentUser.is_super_admin) {
    return true;
  }
  
  // 租户管理员只能管理同租户的Member
  if (currentUser.is_admin && currentUser.tenant_id === targetMember.tenant_id) {
    return true;
  }
  
  // Member只能管理自己
  if (currentUser.id === targetMember.id) {
    return true;
  }
  
  return false;
}
```

---

## 错误码说明

### HTTP状态码

| 状态码 | 说明 | 处理建议 |
|--------|------|---------|
| 200 | 请求成功 | 正常处理响应数据 |
| 201 | 创建成功 | 显示成功提示，刷新列表 |
| 204 | 删除成功（无内容） | 显示成功提示，刷新列表 |
| 400 | 请求参数错误 | 显示具体错误信息，修正参数 |
| 401 | 未认证 | 跳转到登录页 |
| 403 | 权限不足 | 显示权限不足提示 |
| 404 | 资源不存在 | 显示资源不存在提示 |
| 429 | 请求频率限制 | 显示请求过于频繁提示 |
| 500 | 服务器内部错误 | 显示服务器错误提示，联系管理员 |

### 业务错误码

| 错误码 | 说明 | 示例场景 |
|--------|------|---------|
| 2000 | 操作成功 | 正常响应 |
| 2001 | 创建成功 | 创建Member成功 |
| 4000 | 请求参数错误 | 缺少必填字段、格式不正确 |
| 4001 | 认证失败 | 令牌无效或过期 |
| 4002 | 登录失败 | 用户名或密码错误 |
| 4003 | 权限不足 | 尝试访问无权限的资源 |
| 4004 | 资源不存在 | Member ID不存在 |
| 4009 | 资源冲突 | 用户名已存在 |
| 5000 | 服务器内部错误 | 未预期的系统错误 |

### 常见错误响应示例

#### 1. 参数验证错误 (400)

```json
{
  "success": false,
  "errors": {
    "username": ["该字段为必填项。"],
    "email": ["请输入有效的邮箱地址。"],
    "password": ["密码长度至少8位，必须包含大小写字母和数字。"]
  }
}
```

#### 2. 认证失败 (401)

```json
{
  "detail": "Authentication credentials were not provided."
}
```

或

```json
{
  "detail": "Given token not valid for any token type",
  "code": "token_not_valid",
  "messages": [
    {
      "token_class": "AccessToken",
      "token_type": "access",
      "message": "Token is invalid or expired"
    }
  ]
}
```

#### 3. 权限不足 (403)

```json
{
  "detail": "You do not have permission to perform this action."
}
```

或

```json
{
  "detail": "您只能管理自己租户下的Member"
}
```

#### 4. 资源不存在 (404)

```json
{
  "detail": "Not found."
}
```

#### 5. 业务逻辑错误 (400)

```json
{
  "success": false,
  "error": "租户成员配额已满，无法创建更多成员",
  "code": "QUOTA_EXCEEDED"
}
```

---

## 数据模型

### Member对象完整结构

```typescript
interface Member {
  // 基本信息
  id: number;                    // Member ID
  username: string;              // 用户名（唯一）
  email: string;                 // 邮箱地址
  phone: string | null;          // 手机号
  nick_name: string | null;      // 昵称
  avatar: string;                // 头像URL
  wechat_id: string | null;      // 微信号
  
  // 租户信息
  tenant: number | null;         // 租户ID
  tenant_name: string | null;    // 租户名称（只读）
  
  // 账号关系
  parent: number | null;         // 父账号ID（如果是子账号）
  parent_username: string | null;// 父账号用户名（只读）
  is_sub_account: boolean;       // 是否为子账号（只读）
  
  // 状态信息
  status: 'active' | 'suspended' | 'inactive'; // 账号状态
  is_active: boolean;            // 是否激活
  is_deleted: boolean;           // 是否已删除（软删除）
  
  // 时间信息
  date_joined: string;           // 注册时间（ISO 8601格式）
  last_login: string | null;     // 最后登录时间
  last_login_ip: string | null;  // 最后登录IP
}
```

### 字段说明

#### username (string, 必填)
- 用户名，系统唯一
- 长度：1-150个字符
- 允许字母、数字、下划线、@、+、. 和 -
- 示例：`"john_doe"`, `"user@123"`

#### email (string, 必填)
- 邮箱地址，必须有效
- 用于登录和通知
- 示例：`"john@example.com"`

#### password (string, 创建时必填)
- 密码（仅在创建/修改密码时使用，不会在响应中返回）
- 长度：至少8个字符
- 要求：必须包含大小写字母、数字
- 示例：`"Password@123"`

#### phone (string, 可选)
- 手机号码
- 长度：最多11个字符
- 示例：`"13900139000"`

#### nick_name (string, 可选)
- 用户昵称，用于显示
- 长度：最多30个字符
- 示例：`"小明"`

#### avatar (string)
- 头像图片URL
- 格式：相对路径或完整URL
- 示例：`"/media/avatars/abc123.jpg"`
- 默认：空字符串

#### wechat_id (string, 可选)
- 微信号
- 长度：最多32个字符
- 示例：`"wxid_abc123"`

#### tenant (number, 必填)
- 所属租户的ID
- 超级管理员创建时可指定
- 租户管理员创建时自动设置为当前租户
- 示例：`1`

#### parent (number, 可选)
- 父账号ID，仅子账号有值
- 用于标识账号关系
- 示例：`10`

#### status (string)
- 账号状态
- 可选值：
  - `"active"` - 活跃，正常使用
  - `"suspended"` - 暂停，临时禁用
  - `"inactive"` - 未激活，新建账号
- 默认：`"active"`

#### is_active (boolean)
- 是否激活，控制登录权限
- `true` - 可以登录
- `false` - 不能登录
- 子账号强制为 `false`
- 默认：`true`

#### is_deleted (boolean)
- 是否已软删除
- `true` - 已删除，不显示在列表中
- `false` - 正常
- 默认：`false`

#### date_joined (string, ISO 8601)
- 注册时间，自动生成
- 格式：`"2025-01-01T00:00:00Z"`
- 只读字段

#### last_login (string, ISO 8601)
- 最后登录时间
- 格式：`"2025-01-10T10:30:00Z"`
- 只读字段

---

## 公共参数

### 分页参数

所有列表API支持分页参数：

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | integer | 否 | 1 | 页码，从1开始 |
| page_size | integer | 否 | 20 | 每页数量，最大100 |

### 搜索参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| search | string | 否 | 搜索关键词，支持用户名、邮箱、昵称、手机号模糊搜索 |

### 筛选参数

| 参数 | 类型 | 必填 | 可选值 | 说明 |
|------|------|------|--------|------|
| status | string | 否 | active, suspended, inactive | 按状态筛选 |
| is_sub_account | boolean | 否 | true, false | 是否为子账号 |
| parent | integer | 否 | - | 父账号ID，筛选特定父账号的子账号 |
| tenant_id | integer | 否 | - | 租户ID（仅超级管理员可用） |

### 排序参数

默认排序：按创建时间倒序（最新创建的在前）

---

## 租户隔离

### 租户隔离原则

系统采用严格的租户隔离机制：

1. **租户管理员**只能看到和操作**自己租户**的数据
2. **Member**只能看到和操作**自己**的数据
3. **超级管理员**可以看到和操作**所有租户**的数据

### 数据隔离实现

后端会根据用户身份自动过滤数据：

```python
# 租户管理员查询Member列表
if is_admin(user) and user.tenant:
    queryset = Member.objects.filter(tenant=user.tenant)
    
# 超级管理员查询Member列表
if is_super_admin(user):
    queryset = Member.objects.all()
```

### 前端处理建议

#### 1. 租户选择器显示逻辑

```javascript
// 只有超级管理员才显示租户选择器
computed: {
  showTenantSelector() {
    return this.$store.state.currentUser.is_super_admin;
  }
}
```

#### 2. 租户ID参数处理

```javascript
// 创建Member时
async createMember(memberData) {
  const payload = { ...memberData };
  
  // 只有超级管理员才发送tenant_id
  if (!this.$store.state.currentUser.is_super_admin) {
    delete payload.tenant_id;
  }
  
  return await axios.post('/api/v1/members/', payload);
}
```

#### 3. 权限相关的UI控制

```javascript
// 检查是否可以编辑Member
canEditMember(member) {
  const user = this.$store.state.currentUser;
  
  // 超级管理员可以编辑所有Member
  if (user.is_super_admin) {
    return true;
  }
  
  // 租户管理员只能编辑同租户的Member
  if (user.is_admin && user.tenant_id === member.tenant) {
    return true;
  }
  
  return false;
}
```

---

## 数据验证规则

### 前端验证建议

在提交数据前，建议在前端进行以下验证：

#### 1. 用户名验证

```javascript
function validateUsername(username) {
  // 长度：1-150字符
  if (!username || username.length < 1 || username.length > 150) {
    return '用户名长度必须在1-150个字符之间';
  }
  
  // 格式：字母、数字、下划线、@、+、. 和 -
  const regex = /^[\w.@+-]+$/;
  if (!regex.test(username)) {
    return '用户名只能包含字母、数字、下划线、@、+、. 和 -';
  }
  
  return null;
}
```

#### 2. 邮箱验证

```javascript
function validateEmail(email) {
  const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!regex.test(email)) {
    return '请输入有效的邮箱地址';
  }
  return null;
}
```

#### 3. 密码验证

```javascript
function validatePassword(password) {
  // 长度至少8位
  if (password.length < 8) {
    return '密码长度至少8位';
  }
  
  // 必须包含大写字母
  if (!/[A-Z]/.test(password)) {
    return '密码必须包含大写字母';
  }
  
  // 必须包含小写字母
  if (!/[a-z]/.test(password)) {
    return '密码必须包含小写字母';
  }
  
  // 必须包含数字
  if (!/[0-9]/.test(password)) {
    return '密码必须包含数字';
  }
  
  return null;
}
```

#### 4. 手机号验证

```javascript
function validatePhone(phone) {
  if (!phone) return null;  // 可选字段
  
  // 中国大陆手机号：11位数字，1开头
  const regex = /^1[3-9]\d{9}$/;
  if (!regex.test(phone)) {
    return '请输入有效的手机号';
  }
  
  return null;
}
```

---

## 最佳实践

### 1. 错误处理

```javascript
// 统一的错误处理函数
function handleAPIError(error) {
  if (error.response) {
    const { status, data } = error.response;
    
    switch (status) {
      case 400:
        // 参数验证错误
        if (data.errors) {
          // 显示字段级别的错误
          return Object.entries(data.errors).map(([field, errors]) => 
            `${field}: ${errors.join(', ')}`
          ).join('\n');
        }
        return data.detail || data.error || '请求参数错误';
        
      case 401:
        // 未认证，跳转登录
        store.dispatch('logout');
        router.push('/login');
        return '登录已过期，请重新登录';
        
      case 403:
        return '权限不足，无法执行此操作';
        
      case 404:
        return '请求的资源不存在';
        
      case 429:
        return '请求过于频繁，请稍后再试';
        
      case 500:
        return '服务器错误，请联系管理员';
        
      default:
        return data.message || data.detail || '操作失败';
    }
  } else if (error.request) {
    return '网络连接失败，请检查网络设置';
  } else {
    return '请求失败：' + error.message;
  }
}
```

### 2. Loading状态管理

```javascript
// 使用loading状态提升用户体验
data() {
  return {
    loading: false,
    memberList: [],
  };
},
methods: {
  async fetchMembers() {
    this.loading = true;
    try {
      const response = await memberAPI.getList();
      this.memberList = response.data.data.results;
    } catch (error) {
      this.$message.error(handleAPIError(error));
    } finally {
      this.loading = false;
    }
  }
}
```

### 3. 防抖和节流

```javascript
// 搜索输入使用防抖
import { debounce } from 'lodash';

methods: {
  // 延迟300ms执行搜索
  onSearchInput: debounce(function(value) {
    this.searchKeyword = value;
    this.fetchMembers();
  }, 300)
}
```

---

## 下一步

请继续阅读具体的API文档：

- 📗 **member_list_create_api.md** - Member列表和创建API
- 📙 **member_detail_api.md** - Member详情和编辑API
- 📕 **member_subaccount_api.md** - 子账号管理API
- 📔 **member_avatar_api.md** - 头像上传API

