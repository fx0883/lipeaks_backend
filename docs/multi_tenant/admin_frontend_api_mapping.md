# 管理后台前端 API 接口映射文档

本文档提供前端组件与后端API接口的映射关系，帮助开发人员理解各个页面应该调用哪些API接口。

## 认证模块接口映射

| 前端组件 | API 接口 | 请求方法 | 描述 |
|---------|----------|---------|------|
| Login.vue | `/api/v1/auth/login/` | POST | 用户登录 |
| Register.vue | `/api/v1/auth/register/` | POST | 用户注册 |
| App.vue | `/api/v1/auth/token/refresh/` | POST | 刷新Token |
| App.vue | `/api/v1/auth/token/verify/` | POST | 验证Token |

## 用户管理模块接口映射

| 前端组件 | API 接口 | 请求方法 | 描述 |
|---------|----------|---------|------|
| user/List.vue | `/api/v1/users/` | GET | 获取用户列表 |
| user/Create.vue | `/api/v1/users/` | POST | 创建用户 |
| user/Edit.vue | `/api/v1/users/{id}/` | GET | 获取用户详情 |
| user/Edit.vue | `/api/v1/users/{id}/` | PUT | 更新用户信息 |
| user/List.vue | `/api/v1/users/{id}/` | DELETE | 删除用户 |
| profile/Index.vue | `/api/v1/users/me/` | GET | 获取当前用户信息 |
| profile/Index.vue | `/api/v1/users/me/` | PUT | 更新当前用户信息 |
| profile/Index.vue | `/api/v1/users/me/change-password/` | POST | 修改当前用户密码 |
| profile/Index.vue | `/api/v1/users/me/upload-avatar/` | POST | 上传当前用户头像 |
| user/Edit.vue | `/api/v1/users/{id}/change-password/` | POST | 管理员修改用户密码 |
| user/Edit.vue | `/api/v1/users/{id}/upload-avatar/` | POST | 管理员上传用户头像（仅编辑页面可用，创建页面不可用） |

## 租户管理模块接口映射

| 前端组件 | API 接口 | 请求方法 | 描述 |
|---------|----------|---------|------|
| tenant/List.vue | `/api/v1/tenants/` | GET | 获取租户列表 |
| tenant/Create.vue | `/api/v1/tenants/` | POST | 创建租户 |
| tenant/Edit.vue | `/api/v1/tenants/{id}/` | GET | 获取租户详情 |
| tenant/Edit.vue | `/api/v1/tenants/{id}/` | PUT | 更新租户信息 |
| tenant/List.vue | `/api/v1/tenants/{id}/` | DELETE | 删除租户 |
| tenant/Edit.vue | `/api/v1/tenants/{id}/quota/` | PUT | 更新租户配额 |
| tenant/Users.vue | `/api/v1/tenants/{id}/users/` | GET | 获取租户用户列表 |
| tenant/Edit.vue | `/api/v1/tenants/{id}/suspend/` | POST | 暂停租户 |
| tenant/Edit.vue | `/api/v1/tenants/{id}/activate/` | POST | 激活租户 |

## 仪表盘模块接口映射

| 前端组件 | API 接口 | 请求方法 | 描述 |
|---------|----------|---------|------|
| dashboard/Index.vue | `/api/v1/dashboard/stats/` | GET | 获取统计数据 |
| dashboard/Index.vue | `/api/v1/dashboard/user-trend/` | GET | 获取用户增长趋势 |
| dashboard/Index.vue | `/api/v1/dashboard/api-calls/` | GET | 获取API调用统计 |
| dashboard/Index.vue | `/api/v1/dashboard/tenant-usage/` | GET | 获取租户使用情况 |
| dashboard/Index.vue | `/api/v1/dashboard/recent-logins/` | GET | 获取最近登录记录 |

## API 请求携带 Token 说明

除了登录和注册接口外，所有的API请求都需要在请求头中携带Token：

```javascript
headers: {
  'Authorization': `Bearer ${token}`
}
```

## API 错误码处理

前端应统一处理以下错误码：

| 错误码 | 描述 | 处理方式 |
|-------|------|---------|
| 401 | 未认证或Token过期 | 跳转到登录页，或尝试刷新Token |
| 403 | 权限不足 | 显示无权限提示，或返回首页 |
| 404 | 资源不存在 | 显示资源不存在提示 |
| 400 | 请求参数错误 | 显示表单验证错误信息 |
| 500 | 服务器内部错误 | 显示通用错误提示 |

## Token 刷新机制

当Token过期时，前端应该自动尝试使用Refresh Token获取新的Access Token：

```javascript
// 在axios响应拦截器中
if (response.status === 401) {
  // 获取刷新Token
  const refreshToken = getRefreshToken();
  
  if (refreshToken) {
    try {
      // 调用刷新接口
      const res = await axios.post('/api/v1/auth/token/refresh/', {
        refresh: refreshToken
      });
      
      // 更新Token
      const { access } = res.data;
      setToken(access);
      
      // 重试原请求
      const config = response.config;
      config.headers['Authorization'] = `Bearer ${access}`;
      return axios(config);
    } catch (error) {
      // 刷新失败，清除Token并跳转到登录页
      removeTokens();
      router.push('/login');
    }
  } else {
    // 无刷新Token，跳转到登录页
    router.push('/login');
  }
}
```

## API 返回数据格式

大多数API返回的数据格式如下：

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    // 具体数据
  }
}
```

列表数据通常包含分页信息：

```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "count": 100,
    "next": "http://example.com/api/v1/users/?page=2",
    "previous": null,
    "results": [
      // 数据项
    ]
  }
}
```

## API 请求示例

### 用户登录

```javascript
const loginUser = async (username, password) => {
  try {
    const response = await request.post('/auth/login/', {
      username,
      password
    });
    
    const { token, user } = response.data;
    // 存储Token和用户信息
    setToken(token.access);
    setRefreshToken(token.refresh);
    setUserInfo(user);
    
    return user;
  } catch (error) {
    // 处理错误
    console.error('登录失败:', error);
    throw error;
  }
};
```

### 获取用户列表

```javascript
const fetchUsers = async (params) => {
  try {
    const response = await request.get('/users/', params);
    return response.data;
  } catch (error) {
    console.error('获取用户列表失败:', error);
    throw error;
  }
};
```

### 创建租户

```javascript
const createTenant = async (data) => {
  try {
    const response = await request.post('/tenants/', data);
    return response.data;
  } catch (error) {
    console.error('创建租户失败:', error);
    throw error;
  }
};
```

## 文件上传示例

上传用户头像：

```javascript
const uploadAvatar = async (file) => {
  // 创建FormData对象
  const formData = new FormData();
  formData.append('avatar', file);
  
  try {
    const response = await request.post('/users/me/upload-avatar/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  } catch (error) {
    console.error('上传头像失败:', error);
    throw error;
  }
};
```

## 数据导出示例

导出用户列表为Excel：

```javascript
const exportUsers = async (params) => {
  try {
    // 直接使用axios而不是封装的request，以便支持blob响应
    const response = await axios({
      url: 'http://localhost:8000/api/v1/users/export/',
      method: 'GET',
      params,
      responseType: 'blob',
      headers: {
        'Authorization': `Bearer ${getToken()}`
      }
    });
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'users.xlsx');
    document.body.appendChild(link);
    link.click();
    link.remove();
  } catch (error) {
    console.error('导出用户列表失败:', error);
    throw error;
  }
};