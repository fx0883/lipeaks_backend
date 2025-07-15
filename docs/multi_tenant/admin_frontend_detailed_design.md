# 管理后台前端详细设计文档

## 一、页面组件设计

### 1. 登录与认证模块

#### 1.1 登录页面 (Login.vue)

**功能描述**：用户通过用户名和密码登录系统。

**UI设计**：
- 居中显示的登录表单
- 包含用户名和密码输入框，以及登录按钮
- 包含"记住我"选项
- 提供"注册"链接

**数据模型**：
```javascript
{
  form: {
    username: '',
    password: '',
    rememberMe: false
  },
  loading: false,
  rules: { /* Element Plus表单验证规则 */ }
}
```

**主要方法**：
- `handleLogin()`: 处理登录表单提交，调用API登录
- `redirectTo()`: 登录成功后重定向到目标页面

**API接口**：`/api/v1/auth/login/`

#### 1.2 注册页面 (Register.vue)

**功能描述**：新用户注册账号。

**UI设计**：
- 居中显示的注册表单
- 包含用户名、邮箱、手机号、密码等输入框
- 提供服务条款同意选项
- 提供"返回登录"链接

**数据模型**：
```javascript
{
  form: {
    username: '',
    email: '',
    phone: '',
    password: '',
    password_confirm: '',
    real_name: '',
    agree: false
  },
  loading: false,
  rules: { /* Element Plus表单验证规则 */ }
}
```

**主要方法**：
- `handleRegister()`: 处理注册表单提交，调用API注册
- `validatePass2()`: 二次密码验证
- `redirectToLogin()`: 注册成功后重定向到登录页

**API接口**：`/api/v1/auth/register/`

### 2. 用户管理模块

#### 2.1 用户列表页面 (List.vue)

**功能描述**：显示系统中所有用户列表，支持分页、搜索、排序和筛选，以及导出数据功能。租户管理员只能查看其所属租户内的用户。

**UI设计**：
- 顶部搜索和筛选区域
- 创建用户按钮（仅对有权限的用户显示）
- 数据表格，显示用户基本信息、头像和状态
- 操作列，包含编辑、删除等按钮
- 分页控件

**数据模型**：
```javascript
{
  userList: [],
  loading: false,
  total: 0,
  queryParams: {
    search: '',
    status: '',
    tenant_id: '',
    page: 1,
    page_size: 10
  },
  tenantOptions: [], // 租户下拉选项（仅超级管理员可见）
  tenantsLoading: false
}
```

**主要方法**：
- `getUserList()`: 获取用户列表数据，租户管理员自动筛选同租户用户
- `handleQuery()`: 处理搜索和筛选
- `resetQuery()`: 重置搜索条件
- `handleSizeChange()`: 处理分页大小变化
- `handleCurrentChange()`: 处理页码变化
- `handleEdit(id)`: 编辑用户
- `handleDelete(row)`: 删除用户
- `handleCreate()`: 创建新用户
- `searchTenants()`: 搜索租户（仅超级管理员可用）
- `getUserInitials()`: 获取用户头像占位符的首字母显示

**API接口**：
- 获取列表：`/api/v1/users/`
- 删除用户：`/api/v1/users/{id}/`
- 获取租户列表：`/api/v1/tenants/` （仅超级管理员调用）

#### 2.2 创建用户页面 (Create.vue)

**功能描述**：创建新用户。租户管理员只能在自己的租户内创建用户，超级管理员可以在任意租户下创建用户。根据系统设计，用户创建时不支持上传头像，头像功能仅在用户编辑页面可用。

**UI设计**：
- 用户信息表单
- 基本信息区域（用户名、邮箱、姓名等）
- 权限设置区域
- 提交和取消按钮

**数据模型**：
```javascript
{
  userForm: {
    username: '',
    email: '',
    phone: '',
    nick_name: '',
    first_name: '',
    last_name: '',
    password: '',
    password_confirm: '',
    tenant_id: null,
    is_admin: false,
    is_member: true
  },
  loading: false,
  submitLoading: false,
  tenantOptions: [], // 租户下拉选项（仅超级管理员可见）
  tenantsLoading: false,
  rules: { /* Element Plus表单验证规则 */ }
}
```

**主要方法**：
- `searchTenants()`: 搜索租户（仅超级管理员可用）
- `submitForm()`: 处理表单提交
- `resetForm()`: 重置表单
- `goBack()`: 返回列表页

**API接口**：
- 创建用户：`/api/v1/users/`
- 获取租户列表：`/api/v1/tenants/` （仅超级管理员调用）

#### 2.3 编辑用户页面 (Edit.vue)

**功能描述**：编辑现有用户信息。租户管理员只能编辑自己租户内的用户，超级管理员可以编辑任意用户。该页面包含头像上传功能，允许管理员为用户设置或更改头像。

**UI设计**：
- 用户信息表单
- 基本信息区域
- 头像上传区域，包含图片裁剪功能
- 权限设置区域
- 提交和取消按钮
- 修改密码功能（通过对话框实现）

**数据模型**：
```javascript
{
  userForm: {
    id: '',
    username: '',
    email: '',
    phone: '',
    nick_name: '',
    first_name: '',
    last_name: '',
    tenant_id: null,
    is_admin: false,
    is_member: true,
    is_super_admin: false,
    is_active: true,
    avatar: '',
    avatar_file: null
  },
  userId: null, // 从路由参数获取
  loading: false,
  submitLoading: false,
  tenantOptions: [], // 租户下拉选项（仅超级管理员可见）
  tenantsLoading: false,
  
  // 头像上传相关
  imageUrl: '',
  cropperVisible: false,
  
  // 密码修改相关
  showChangePassword: false,
  passwordForm: {
    password: '',
    password_confirm: ''
  },
  passwordLoading: false,
  
  rules: { /* Element Plus表单验证规则 */ }
}
```

**主要方法**：
- `getUserDetail()`: 获取用户详情数据，包含头像URL
- `searchTenants()`: 搜索租户（仅超级管理员可用）
- `submitBasicForm()`: 处理基本信息表单提交
- `beforeAvatarUpload()`: 头像上传前的验证
- `uploadAvatar()`: 上传头像
- `handleCropConfirm()`: 确认图片裁剪
- `changePassword()`: 修改用户密码
- `goBack()`: 返回列表页

**API接口**：
- 获取用户详情：`/api/v1/users/{id}/`
- 更新用户：`/api/v1/users/{id}/`
- 上传头像：`/api/v1/users/{id}/upload-avatar/`
- 修改密码：`/api/v1/users/{id}/change-password/`
- 获取租户列表：`/api/v1/tenants/` （仅超级管理员调用）

### 3. 租户管理模块

#### 3.1 租户列表页面 (List.vue)

**功能描述**：显示系统中所有租户列表，支持分页、搜索、排序和筛选，以及导出数据功能。

**UI设计**：
- 顶部搜索和筛选区域
- 导出按钮
- 数据表格，显示租户基本信息和配额使用情况
- 操作列，包含编辑、删除、查看用户等按钮
- 分页控件

**数据模型**：
```javascript
{
  tenants: [],
  loading: false,
  total: 0,
  query: {
    page: 1,
    pageSize: 10,
    search: '',
    ordering: '-created_at',
    status: null
  },
  selectedRows: [],
  statusOptions: [
    { value: 'active', label: '活跃' },
    { value: 'suspended', label: '已暂停' },
    { value: 'inactive', label: '未激活' }
  ]
}
```

**主要方法**：
- `fetchTenants()`: 获取租户列表数据
- `handleFilter()`: 处理筛选条件变化
- `handleSort()`: 处理排序变化
- `handlePageChange()`: 处理分页变化
- `handleEdit(row)`: 编辑租户
- `handleDelete(row)`: 删除租户
- `handleBatchDelete()`: 批量删除租户
- `handleViewUsers(row)`: 查看租户用户
- `exportData()`: 导出租户数据

**API接口**：
- 获取列表：`/api/v1/tenants/`
- 删除租户：`/api/v1/tenants/{id}/`

#### 3.2 创建租户页面 (Create.vue)

**功能描述**：创建新租户。

**UI设计**：
- 租户信息表单
- 基本信息区域
- 配额设置区域
- 提交和取消按钮

**数据模型**：
```javascript
{
  form: {
    name: '',
    code: '',
    description: '',
    quota: {
      max_users: 50,
      max_admins: 5
    }
  },
  loading: false,
  rules: { /* Element Plus表单验证规则 */ }
}
```

**主要方法**：
- `handleSubmit()`: 处理表单提交
- `resetForm()`: 重置表单
- `cancel()`: 取消创建，返回列表页

**API接口**：
- 创建租户：`/api/v1/tenants/`

#### 3.3 编辑租户页面 (Edit.vue)

**功能描述**：编辑现有租户信息。

**UI设计**：
- 租户信息表单（与创建租户页面类似）
- 显示租户已有信息
- 提交和取消按钮

**数据模型**：
```javascript
{
  form: {
    name: '',
    code: '',
    description: '',
    status: 'active',
    quota: {
      max_users: 50,
      max_admins: 5
    }
  },
  tenantId: null, // 从路由参数获取
  loading: false,
  rules: { /* Element Plus表单验证规则 */ },
  statusOptions: [
    { value: 'active', label: '活跃' },
    { value: 'suspended', label: '已暂停' },
    { value: 'inactive', label: '未激活' }
  ]
}
```

**主要方法**：
- `fetchTenantData()`: 获取租户详情数据
- `handleSubmit()`: 处理表单提交
- `resetForm()`: 重置表单
- `cancel()`: 取消编辑，返回列表页

**API接口**：
- 获取租户详情：`/api/v1/tenants/{id}/`
- 更新租户：`/api/v1/tenants/{id}/`

### 4. 仪表盘模块

#### 4.1 仪表盘首页 (Index.vue)

**功能描述**：展示系统概览信息，包括用户数量、租户数量、API调用次数等统计数据。

**UI设计**：
- 顶部统计卡片，显示关键数据
- 用户增长趋势图表
- API调用统计图表
- 租户数据使用情况图表
- 最近登录用户列表

**数据模型**：
```javascript
{
  loading: false,
  stats: {
    totalUsers: 0,
    totalTenants: 0,
    totalApiCalls: 0,
    activeUsers: 0
  },
  userTrend: [], // 用户增长趋势数据
  apiCallsData: [], // API调用数据
  tenantUsageData: [], // 租户使用情况数据
  recentLogins: [] // 最近登录用户
}
```

**主要方法**：
- `fetchDashboardData()`: 获取仪表盘数据
- `renderUserTrendChart()`: 渲染用户增长趋势图表
- `renderApiCallsChart()`: 渲染API调用图表
- `renderTenantUsageChart()`: 渲染租户使用情况图表

**API接口**：
- 获取仪表盘数据：`/api/v1/dashboard/stats/`
- 获取用户趋势：`/api/v1/dashboard/user-trend/`
- 获取API调用数据：`/api/v1/dashboard/api-calls/`
- 获取租户使用情况：`/api/v1/dashboard/tenant-usage/`
- 获取最近登录：`/api/v1/dashboard/recent-logins/`

### 5. 个人设置模块

#### 5.1 个人设置页面 (Index.vue)

**功能描述**：允许用户查看和修改个人信息，包括基本信息和密码。

**UI设计**：
- 标签页切换不同设置区域
- 基本信息表单
- 修改密码表单
- 头像上传区域

**数据模型**：
```javascript
{
  activeTab: 'basic-info',
  profileForm: {
    username: '',
    email: '',
    phone: '',
    nick_name: '',
    first_name: '',
    last_name: '',
    avatar: ''
  },
  passwordForm: {
    old_password: '',
    new_password: '',
    confirm_password: ''
  },
  loading: {
    profile: false,
    password: false,
    avatar: false
  },
  profileRules: { /* Element Plus表单验证规则 */ },
  passwordRules: { /* Element Plus表单验证规则 */ }
}
```

**主要方法**：
- `fetchUserProfile()`: 获取用户个人信息
- `updateProfile()`: 更新用户个人信息
- `changePassword()`: 修改用户密码
- `uploadAvatar()`: 上传用户头像
- `validatePass()`: 验证新密码有效性
- `validatePass2()`: 验证确认密码与新密码是否一致

**API接口**：
- 获取个人信息：`/api/v1/users/me/`
- 更新个人信息：`/api/v1/users/me/`
- 修改密码：`/api/v1/users/me/change-password/`
- 上传头像：`/api/v1/users/me/upload-avatar/`

## 二、公共组件设计

### 1. 布局组件

#### 1.1 应用布局 (Layout.vue)

**功能描述**：应用的主布局组件，包含侧边栏、顶部导航栏和内容区域。

**UI设计**：
- 固定顶部导航栏
- 可折叠侧边栏
- 内容区域
- 面包屑导航

**数据模型**：
```javascript
{
  isCollapse: false, // 侧边栏是否折叠
  menuVisible: true // 移动端菜单是否可见
}
```

**主要方法**：
- `toggleSidebar()`: 切换侧边栏折叠状态
- `toggleMenu()`: 切换移动端菜单可见状态
- `handleResize()`: 处理窗口大小变化

#### 1.2 头部组件 (AppHeader.vue)

**功能描述**：顶部导航栏组件，显示logo、用户信息、通知和快捷操作。

**UI设计**：
- 左侧应用logo和菜单折叠按钮
- 中间搜索框和面包屑导航
- 右侧用户头像和下拉菜单

**数据模型**：
```javascript
{
  userInfo: null, // 当前用户信息
  dropdownVisible: false // 用户下拉菜单是否可见
}
```

**主要方法**：
- `toggleDropdown()`: 切换用户下拉菜单显示状态
- `logout()`: 用户登出
- `goToProfile()`: 跳转到个人设置页面

#### 1.3 侧边栏组件 (AppSidebar.vue)

**功能描述**：侧边导航栏组件，根据用户权限动态显示菜单项。

**UI设计**：
- 垂直菜单列表
- 支持多级菜单
- 高亮当前路由

**数据模型**：
```javascript
{
  menus: [], // 菜单数据，根据用户权限动态生成
  isCollapse: false, // 是否折叠侧边栏
  activeMenu: '' // 当前激活的菜单项
}
```

**主要方法**：
- `generateMenus()`: 根据用户权限生成菜单数据
- `handleSelect()`: 处理菜单项选择

### 2. 通用组件

#### 2.1 数据表格组件 (DataTable.vue)

**功能描述**：封装Element Plus的Table组件，提供统一的表格功能，包括分页、排序、筛选和选择。

**UI设计**：
- 数据表格
- 分页控件
- 选择功能
- 支持自定义列模板

**Props**：
```javascript
{
  data: Array, // 表格数据
  columns: Array, // 列配置
  total: Number, // 总记录数
  loading: Boolean, // 加载状态
  pagination: Object, // 分页配置
  selection: Boolean, // 是否开启多选
  showIndex: Boolean, // 是否显示序号列
  border: { // 是否显示边框
    type: Boolean,
    default: true
  },
  height: [String, Number] // 表格高度
}
```

**Events**：
```javascript
{
  'page-change': 页码变化事件,
  'sort-change': 排序变化事件,
  'selection-change': 选择变化事件,
  'row-click': 行点击事件
}
```

**Slots**：
- `column-${field}`: 自定义列模板
- `empty`: 自定义空数据模板
- `pagination`: 自定义分页模板

#### 2.2 搜索表单组件 (SearchForm.vue)

**功能描述**：封装查询条件表单，支持多种查询条件和重置功能。

**UI设计**：
- 水平布局的表单
- 支持多种输入控件（输入框、下拉框、日期选择器等）
- 搜索和重置按钮

**Props**：
```javascript
{
  fields: Array, // 表单字段配置
  model: Object, // 表单数据模型
  inline: { // 是否使用行内表单
    type: Boolean,
    default: true
  },
  labelWidth: { // 标签宽度
    type: String,
    default: '80px'
  }
}
```

**Events**：
```javascript
{
  'search': 搜索事件,
  'reset': 重置事件,
  'model-change': 表单数据变化事件
}
```

**Slots**：
- `field-${field}`: 自定义字段模板
- `actions`: 自定义操作按钮模板

#### 2.3 导出按钮组件 (ExportButton.vue)

**功能描述**：封装数据导出功能，支持Excel格式导出。

**UI设计**：
- 导出按钮
- 导出格式选择下拉菜单
- 导出进度提示

**Props**：
```javascript
{
  data: Array, // 要导出的数据
  filename: { // 导出文件名
    type: String,
    default: 'export'
  },
  showFormat: { // 是否显示格式选择
    type: Boolean,
    default: true
  },
  formats: { // 支持的导出格式
    type: Array,
    default: () => ['xlsx', 'csv']
  }
}
```

**Methods**：
```javascript
{
  exportData(format): 导出数据方法
}
```

## 三、工具函数设计

### 1. 请求工具 (request.js)

**功能描述**：封装Axios，统一处理HTTP请求、响应和错误。

**主要函数**：
```javascript
// 创建Axios实例
const service = axios.create({
  baseURL: 'http://localhost:8000/api/v1/',
  timeout: 15000
});

// 请求方法
export const request = {
  get(url, params, config = {}) { /* 实现 */ },
  post(url, data, config = {}) { /* 实现 */ },
  put(url, data, config = {}) { /* 实现 */ },
  delete(url, config = {}) { /* 实现 */ },
  upload(url, file, config = {}) { /* 实现 */ },
  download(url, params, config = {}) { /* 实现 */ }
};
```

### 2. 认证工具 (auth.js)

**功能描述**：管理用户认证相关的功能，包括Token管理、权限检查等。

**主要函数**：
```javascript
// Token管理
export const getToken = () => localStorage.getItem('access_token');
export const setToken = (token) => localStorage.setItem('access_token', token);
export const getRefreshToken = () => localStorage.getItem('refresh_token');
export const setRefreshToken = (token) => localStorage.setItem('refresh_token', token);
export const removeTokens = () => { /* 实现 */ };

// 权限检查
export const hasPermission = (permission) => { /* 实现 */ };
export const hasRole = (role) => { /* 实现 */ };
export const isSuperAdmin = () => { /* 实现 */ };
export const isAdmin = () => { /* 实现 */ };
```

### 3. 格式化工具 (format.js)

**功能描述**：提供各种数据格式化函数。

**主要函数**：
```javascript
// 日期格式化
export const formatDate = (date, format = 'YYYY-MM-DD') => { /* 实现 */ };
export const formatDateTime = (date, format = 'YYYY-MM-DD HH:mm:ss') => { /* 实现 */ };

// 数字格式化
export const formatNumber = (num, options = {}) => { /* 实现 */ };
export const formatPercent = (num, digits = 2) => { /* 实现 */ };

// 文本格式化
export const truncate = (text, length = 20, suffix = '...') => { /* 实现 */ };
export const capitalize = (text) => { /* 实现 */ };
```

### 4. 验证工具 (validator.js)

**功能描述**：提供表单验证相关的函数。

**主要函数**：
```javascript
// 通用验证规则
export const required = { required: true, message: '此项为必填项' };
export const email = { type: 'email', message: '请输入有效的邮箱地址' };
export const mobilePhone = { pattern: /^1[3-9]\d{9}$/, message: '请输入有效的手机号码' };

// 自定义验证函数
export const validatePassword = (rule, value, callback) => { /* 实现 */ };
export const validateConfirmPassword = (password) => (rule, value, callback) => { /* 实现 */ };
export const validateUsername = (rule, value, callback) => { /* 实现 */ };
```

### 5. 导出工具 (export.js)

**功能描述**：提供数据导出相关的函数。

**主要函数**：
```javascript
// 导出为Excel
export const exportToExcel = (data, filename, options = {}) => { /* 实现 */ };

// 导出为CSV
export const exportToCSV = (data, filename, options = {}) => { /* 实现 */ };

// 通用导出函数
export const exportData = (data, filename, format = 'xlsx', options = {}) => { /* 实现 */ };