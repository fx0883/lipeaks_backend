# Member 管理 API 文档

## 文档说明

本文档为 **lipeaks_backend** 系统中 **Member（普通用户）管理** 的前端集成文档。

文档编写日期：2025-10-06  
目标读者：前端开发人员  
后端框架：Django REST Framework  
认证方式：JWT (JSON Web Token)

---

## ⚠️ 重要更新（2025-10-06）

**API架构已重构！管理员端API已迁移至 `/admin/` 前缀。**

- ✅ **管理员端API**：`/api/v1/admin/members/` （已变更）
- ✅ **Member端API**：`/api/v1/members/` （不变）

详见：📌 **FRONTEND_MIGRATION_GUIDE.md** - 前端迁移指南

---

## 文档目录

本文档集包含以下文件：

### 核心文档

1. **README.md** (本文件) - 总览和快速开始
2. **member_common.md** - 通用说明（认证、权限、错误码、数据模型）
3. **member_list_create_api.md** - Member列表和创建API（管理员端）
4. **member_detail_api.md** - Member详情、更新、删除API（管理员端）
5. **member_subaccount_api.md** - 子账号管理API（管理员端和Member端）
6. **member_avatar_api.md** - 头像上传管理API（管理员端和Member端）

### 辅助文档

7. **FRONTEND_MIGRATION_GUIDE.md** - 🔥 前端迁移指南（必读）
8. **API_REFACTOR_COMPLETED.md** - API重构完成说明
9. **API_RESTRUCTURE_PROPOSAL.md** - API重构方案文档
10. **URL_PATH_CORRECTION.md** - URL路径修正说明

---

## 快速开始

### 1. 基础URL

## API基础URL

### 管理员端API
```
https://your-domain.com/api/v1/admin/members/
```

本地开发环境：
```
http://localhost:8000/api/v1/admin/members/
```

### Member端API（Member自用）
```
https://your-domain.com/api/v1/members/
```

本地开发环境：
```
http://localhost:8000/api/v1/members/
```

### 2. 认证方式

所有API请求都需要JWT认证，在请求头中添加：
```http
Authorization: Bearer <your_access_token>
```

### 3. 内容类型

除文件上传外，所有请求使用JSON格式：
```http
Content-Type: application/json
```

文件上传使用：
```http
Content-Type: multipart/form-data
```

### 4. 权限说明

系统有三种角色权限：

| 角色 | 说明 | 权限范围 |
|------|------|---------|
| **超级管理员** | is_super_admin=true | 可管理所有租户的Member |
| **租户管理员** | is_admin=true, 有tenant | 只能管理自己租户的Member |
| **普通Member** | is_member=true | 只能管理自己和自己的子账号 |

---

## API功能概览

### Member基础管理

| 方法 | 端点 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/v1/admin/members/` | 获取Member列表 | 管理员 |
| POST | `/api/v1/admin/members/` | 创建新Member | 管理员 |
| GET | `/api/v1/admin/members/{id}/` | 获取Member详情 | 管理员 |
| PUT | `/api/v1/admin/members/{id}/` | 完整更新Member | 管理员 |
| PATCH | `/api/v1/admin/members/{id}/` | 部分更新Member | 管理员 |
| DELETE | `/api/v1/admin/members/{id}/` | 删除Member（软删除） | 管理员 |

### 子账号管理

| 方法 | 端点 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/v1/admin/members/sub-accounts/` | 获取子账号列表（管理员视图） | 管理员 |
| GET | `/api/v1/members/sub-accounts/` | 获取子账号列表（Member自己的） | Member |
| POST | `/api/v1/members/sub-accounts/` | 创建子账号 | Member |
| GET | `/api/v1/members/sub-accounts/{id}/` | 获取子账号详情 | Member |
| PUT | `/api/v1/members/sub-accounts/{id}/` | 更新子账号 | Member |
| PATCH | `/api/v1/members/sub-accounts/{id}/` | 部分更新子账号 | Member |
| DELETE | `/api/v1/members/sub-accounts/{id}/` | 删除子账号 | Member |

### 头像管理

| 方法 | 端点 | 说明 | 权限 |
|------|------|------|------|
| POST | `/api/v1/admin/members/{id}/avatar/upload/` | 为指定Member上传头像 | 管理员 |

### Member自用API（非管理功能）

| 方法 | 端点 | 说明 | 权限 |
|------|------|------|------|
| GET | `/api/v1/members/me/` | 获取当前Member信息 | Member本人 |
| PUT | `/api/v1/members/me/` | 更新当前Member信息 | Member本人 |
| POST | `/api/v1/members/me/password/` | 修改当前Member密码 | Member本人 |
| POST | `/api/v1/members/avatar/upload/` | 上传当前Member头像 | Member本人 |

---

## 快速示例

### 示例1：获取Member列表

```javascript
// 使用 axios
const response = await axios.get('http://localhost:8000/api/v1/admin/members/', {
  headers: {
    'Authorization': `Bearer ${accessToken}`,
  },
  params: {
    page: 1,
    page_size: 20,
    search: 'john',
    status: 'active'
  }
});

console.log(response.data.data.results);
```

### 示例2：创建新Member

```javascript
const response = await axios.post('http://localhost:8000/api/v1/admin/members/', {
  username: 'newmember',
  email: 'newmember@example.com',
  password: 'Password@123',
  confirm_password: 'Password@123',
  phone: '13900139000',
  nick_name: '新用户',
  tenant_id: 1  // 超级管理员可指定
}, {
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  }
});

console.log(response.data.data);
```

### 示例3：上传头像

```javascript
const formData = new FormData();
formData.append('avatar', file);

const response = await axios.post(
  `http://localhost:8000/api/v1/admin/members/123/avatar/upload/`,
  formData,
  {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'multipart/form-data'
    }
  }
);

console.log(response.data.avatar);
```

---

## 响应格式

### 成功响应格式

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    // 实际数据内容
  }
}
```

### 错误响应格式

```json
{
  "success": false,
  "code": 4003,
  "message": "权限不足",
  "data": null
}
```

### 列表响应格式（分页）

```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "count": 100,
    "next": "http://localhost:8000/api/v1/members/?page=2",
    "previous": null,
    "results": [
      // Member对象数组
    ]
  }
}
```

---

## 常用HTTP状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 201 | 创建成功 |
| 204 | 删除成功（无内容返回） |
| 400 | 请求参数错误 |
| 401 | 未认证或令牌无效 |
| 403 | 权限不足 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 开发建议

### 前端需要实现的主要页面

1. **Member列表页面**
   - 数据表格展示
   - 搜索和筛选功能
   - 分页组件
   - 创建按钮
   - 编辑/删除操作

2. **Member创建/编辑表单**
   - 表单验证
   - 密码强度检查
   - 租户选择（根据权限显示）
   - 状态管理

3. **Member详情页面**
   - 基本信息展示
   - 头像显示和上传
   - 子账号列表
   - 操作按钮

4. **子账号管理**
   - 子账号列表
   - 创建/编辑子账号
   - 关联父账号信息

### 推荐的状态管理

```javascript
// 建议使用 Vuex/Pinia 或 Redux 管理以下状态
const memberStore = {
  memberList: [],        // Member列表
  currentMember: null,   // 当前查看的Member
  pagination: {
    page: 1,
    pageSize: 20,
    total: 0
  },
  filters: {
    search: '',
    status: '',
    tenant_id: null
  }
}
```

### 错误处理建议

```javascript
try {
  const response = await memberAPI.getList();
  // 处理成功响应
} catch (error) {
  if (error.response) {
    // 服务器返回错误
    const { status, data } = error.response;
    
    switch (status) {
      case 401:
        // 跳转到登录页
        router.push('/login');
        break;
      case 403:
        // 显示权限不足提示
        showError('权限不足');
        break;
      case 404:
        // 资源不存在
        showError('用户不存在');
        break;
      default:
        // 其他错误
        showError(data.message || '操作失败');
    }
  } else {
    // 网络错误
    showError('网络连接失败，请稍后重试');
  }
}
```

---

## 下一步

请按顺序阅读以下文档：

1. 📘 **member_common.md** - 了解通用规范和数据模型
2. 📗 **member_list_create_api.md** - 实现列表和创建功能
3. 📙 **member_detail_api.md** - 实现详情和编辑功能
4. 📕 **member_subaccount_api.md** - 实现子账号管理
5. 📔 **member_avatar_api.md** - 实现头像上传功能

---

## 技术支持

如有疑问，请联系后端团队或查阅：
- Swagger文档：`http://localhost:8000/swagger/`
- ReDoc文档：`http://localhost:8000/redoc/`

---

**版本历史**
- v1.0 (2025-10-06) - 初始版本

