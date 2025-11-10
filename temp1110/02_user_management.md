# 2. 用户管理 API 集成指南

## 🎯 概述

用户管理API提供Member用户的个人信息管理功能，包括获取、更新用户信息、修改密码、上传头像等操作。

## 📋 API 列表

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| [获取用户信息](#获取用户信息) | GET | `/members/me/` | 获取当前登录用户的详细信息 |
| [更新用户信息](#更新用户信息) | PUT/PATCH | `/members/me/` | 更新当前用户的个人信息 |
| [修改密码](#修改密码) | POST | `/members/me/password/` | 修改当前用户的登录密码 |
| [上传头像](#上传头像) | POST | `/members/avatar/upload/` | 上传当前用户的头像 |
| [为指定用户上传头像](#为指定用户上传头像) | POST | `/members/{id}/avatar/upload/` | 管理员为指定用户上传头像 |

---

## 获取用户信息

### 接口信息
- **接口地址**: `GET /api/v1/members/me/`
- **权限要求**: 需要Member用户认证
- **功能说明**: 获取当前登录Member用户的详细信息

### 请求头
```bash
Authorization: Bearer {access_token}
X-Tenant-ID: {tenant_id}
```

### 使用示例

#### cURL 命令
```bash
curl -X GET "https://your-domain.com/api/v1/members/me/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "X-Tenant-ID: 1"
```

#### JavaScript 获取用户信息
```javascript
const getUserProfile = async () => {
  try {
    const response = await fetch('https://your-domain.com/api/v1/members/me/', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'X-Tenant-ID': '1'
      }
    });

    const result = await response.json();

    if (result.success) {
      console.log('用户信息:', result.data);
      return result.data;
    } else {
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('获取用户信息失败:', error);
    throw error;
  }
};
```

### 成功响应
```json
{
  "success": true,
  "code": 2000,
  "message": "获取成功",
  "data": {
    "id": 8,
    "username": "testuser456",
    "email": "test456@example.com",
    "phone": null,
    "nick_name": null,
    "first_name": "",
    "last_name": "",
    "is_active": true,
    "avatar": "",
    "tenant": 1,
    "tenant_name": "金sir",
    "is_sub_account": false,
    "parent": null,
    "parent_username": null,
    "date_joined": "2025-11-10T06:43:51.896344Z",
    "status": "active",
    "wechat_id": null
  }
}
```

---

## 更新用户信息

### 接口信息
- **接口地址**: `PUT /api/v1/members/me/` (完整更新) 或 `PATCH /api/v1/members/me/` (部分更新)
- **权限要求**: 需要Member用户认证
- **功能说明**: 更新当前登录Member用户的个人信息

### 请求头
```bash
Authorization: Bearer {access_token}
X-Tenant-ID: {tenant_id}
Content-Type: application/json
```

### 可更新字段

| 参数 | 类型 | 必填 | 说明 | 示例值 | 验证规则 |
|------|------|------|------|------|------|----------|
| phone | string | 否 | 手机号码，租户内唯一 | "13800138001" | 有效的手机号码格式 |
| nick_name | string | 否 | 昵称 | "新昵称" | 最长50字符 |
| first_name | string | 否 | 名 | "李" | 最长30字符 |
| last_name | string | 否 | 姓 | "四" | 最长30字符 |
| wechat_id | string | 否 | 微信ID | "new_wechat_id" | 最长100字符 |

### 不可更新字段
- `username` - 用户名
- `email` - 邮箱地址
- `avatar` - 需要通过专门的上传接口更新

### 使用示例

#### cURL 命令 - 部分更新
```bash
curl -X PATCH "https://your-domain.com/api/v1/members/me/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "X-Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{
    "nick_name": "新昵称",
    "phone": "13800138001"
  }'
```

#### JavaScript 更新用户信息
```javascript
const updateUserProfile = async (updates) => {
  try {
    const response = await fetch('https://your-domain.com/api/v1/members/me/', {
      method: 'PATCH',  // 使用PATCH进行部分更新
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'X-Tenant-ID': '1',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(updates)
    });

    const result = await response.json();

    if (result.success) {
      console.log('用户信息更新成功:', result.data);

      // 更新本地存储的用户信息
      const currentUser = JSON.parse(localStorage.getItem('user_info') || '{}');
      const updatedUser = { ...currentUser, ...result.data };
      localStorage.setItem('user_info', JSON.stringify(updatedUser));

      return result.data;
    } else {
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('更新用户信息失败:', error);
    throw error;
  }
};

// 使用示例
const updates = {
  nick_name: '新昵称',
  phone: '13800138001',
  wechat_id: 'new_wechat_id'
};

updateUserProfile(updates);
```

### 成功响应
```json
{
  "success": true,
  "code": 2000,
  "message": "更新成功",
  "data": {
    "id": 10,
    "username": "member001",
    "email": "member001@example.com",
    "phone": "13800138001",
    "nick_name": "新昵称",
    "first_name": "张",
    "last_name": "三",
    "is_active": true,
    "avatar": "/media/avatars/avatar_10.jpg",
    "tenant": 1,
    "tenant_name": "测试租户",
    "is_sub_account": false,
    "parent": null,
    "parent_username": null,
    "date_joined": "2024-01-15T08:30:00Z",
    "status": "active",
    "wechat_id": "new_wechat_id"
  }
}
```

---

## 修改密码

### 接口信息
- **接口地址**: `POST /api/v1/members/me/password/`
- **权限要求**: 需要Member用户认证
- **功能说明**: 修改当前登录Member用户的登录密码

### 请求头
```bash
Authorization: Bearer {access_token}
X-Tenant-ID: {tenant_id}
Content-Type: application/json
```

### 请求参数

| 参数 | 类型 | 必填 | 说明 | 示例值 | 验证规则 |
|------|------|------|------|------|------|----------|
| old_password | string | 是 | 当前密码 | "oldpassword123" | 最少1字符，用于身份验证 |
| new_password | string | 是 | 新密码 | "newpassword123" | 最少8字符，包含大小写字母和数字 |
| new_password_confirm | string | 是 | 新密码确认 | "newpassword123" | 必须与new_password完全相同 |

### 使用示例

#### cURL 命令
```bash
curl -X POST "https://your-domain.com/api/v1/members/me/password/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "X-Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "oldpassword123",
    "new_password": "newpassword123",
    "new_password_confirm": "newpassword123"
  }'
```

#### JavaScript 修改密码
```javascript
const changePassword = async (oldPassword, newPassword) => {
  try {
    const response = await fetch('https://your-domain.com/api/v1/members/me/password/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'X-Tenant-ID': '1',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        old_password: oldPassword,
        new_password: newPassword,
        new_password_confirm: newPassword
      })
    });

    const result = await response.json();

    if (result.success) {
      console.log('密码修改成功');

      // 注意：密码修改后，所有现有的token都会失效
      // 需要重新登录或刷新token
      alert('密码修改成功，请重新登录');

      // 清除本地存储并重定向到登录页面
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user_info');

      window.location.href = '/login';
      return true;
    } else {
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('修改密码失败:', error);
    throw error;
  }
};

// 使用示例
changePassword('oldpassword123', 'newpassword123');
```

### 成功响应
```json
{
  "success": true,
  "code": 2000,
  "message": "密码更新成功",
  "data": null
}
```

### 错误响应示例
```json
{
  "success": false,
  "code": 4000,
  "message": "数据验证失败",
  "data": {
    "old_password": ["Incorrect old password"]
  },
  "error_code": "VALIDATION_ERROR"
}
```

---

## 上传头像

### 接口信息
- **接口地址**: `POST /api/v1/members/avatar/upload/`
- **权限要求**: 需要Member用户认证
- **功能说明**: 上传并更新当前登录Member用户的头像

### 请求头
```bash
Authorization: Bearer {access_token}
X-Tenant-ID: {tenant_id}
Content-Type: multipart/form-data
```

### 请求参数（表单数据）

| 参数 | 类型 | 必填 | 说明 | 示例值 | 验证规则 |
|------|------|------|------|------|------|----------|
| avatar | file | 是 | 头像图片文件 | user-avatar.jpg | JPG/PNG/GIF/WEBP/BMP格式，最大2MB |

### 文件格式要求
- **支持格式**: JPG, PNG, GIF, WEBP, BMP
- **最大文件大小**: 2MB
- **推荐尺寸**: 200x200像素以上，正方形最佳

### 使用示例

#### cURL 命令
```bash
curl -X POST "https://your-domain.com/api/v1/members/avatar/upload/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "X-Tenant-ID: 1" \
  -F "avatar=@/path/to/avatar.jpg"
```

#### JavaScript 上传头像
```javascript
const uploadAvatar = async (file) => {
  try {
    // 验证文件类型
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      throw new Error('不支持的文件格式，请选择 JPG、PNG、GIF 或 WEBP 格式的图片');
    }

    // 验证文件大小（2MB）
    if (file.size > 2 * 1024 * 1024) {
      throw new Error('文件大小不能超过 2MB');
    }

    const formData = new FormData();
    formData.append('avatar', file);

    const response = await fetch('https://your-domain.com/api/v1/members/avatar/upload/', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
        'X-Tenant-ID': '1'
        // 注意：不要设置 Content-Type，浏览器会自动设置 multipart/form-data
      },
      body: formData
    });

    const result = await response.json();

    if (result.success) {
      console.log('头像上传成功:', result.data);

      // 更新本地存储的用户信息
      const currentUser = JSON.parse(localStorage.getItem('user_info') || '{}');
      const updatedUser = { ...currentUser, avatar: result.data.avatar };
      localStorage.setItem('user_info', JSON.stringify(updatedUser));

      return result.data;
    } else {
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('上传头像失败:', error);
    throw error;
  }
};

// HTML中使用
document.getElementById('avatar-input').addEventListener('change', async (event) => {
  const file = event.target.files[0];
  if (file) {
    try {
      const result = await uploadAvatar(file);
      // 更新页面上的头像显示
      document.getElementById('user-avatar').src = `https://your-domain.com${result.avatar}`;
      alert('头像上传成功');
    } catch (error) {
      alert('头像上传失败: ' + error.message);
    }
  }
});
```

### 成功响应
```json
{
  "success": true,
  "code": 2000,
  "message": "头像上传成功",
  "data": {
    "avatar": "/media/avatars/avatar_10_1234567890.jpg"
  }
}
```

### 错误响应示例
```json
{
  "success": false,
  "code": 4000,
  "message": "数据验证失败",
  "data": {
    "avatar": ["Upload a valid image. The file you uploaded was either not an image or a corrupted image."]
  },
  "error_code": "VALIDATION_ERROR"
}
```

---

## 为指定用户上传头像

### 接口信息
- **接口地址**: `POST /api/v1/members/{id}/avatar/upload/`
- **权限要求**: 需要管理员或父账号权限
- **功能说明**: 为指定的Member用户上传头像

### 请求头
```bash
Authorization: Bearer {access_token}
X-Tenant-ID: {tenant_id}  # Member用户必填，管理员可选
Content-Type: multipart/form-data
```

### 路径参数

| 参数 | 类型 | 必填 | 说明 | 示例值 | 验证规则 |
|------|------|------|------|------|------|----------|
| id | integer | 是 | Member用户ID | 123 | 有效的Member ID |

### 请求参数（表单数据）

| 参数 | 类型 | 必填 | 说明 | 示例值 | 验证规则 |
|------|------|------|------|------|------|------|----------|
| avatar | file | 是 | 头像图片文件 | member-avatar.jpg | JPG/PNG/GIF/WEBP/BMP格式，最大2MB |

### 权限说明
- **Member用户**: 仅可为自己的子账号上传头像
- **租户管理员**: 可为本租户任意Member上传头像
- **超级管理员**: 可为任意Member上传头像

### 使用示例

#### cURL 命令 - 父账号为子账号上传头像
```bash
curl -X POST "https://your-domain.com/api/v1/members/123/avatar/upload/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..." \
  -H "X-Tenant-ID: 1" \
  -F "avatar=@/path/to/avatar.jpg"
```

#### JavaScript 管理员上传头像
```javascript
const uploadAvatarForUser = async (userId, file) => {
  try {
    const formData = new FormData();
    formData.append('avatar', file);

    const headers = {
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`
      // 注意：不要手动设置 Content-Type
    };

    // 检查用户类型，Member用户需要租户ID
    const userInfo = JSON.parse(localStorage.getItem('user_info') || '{}');
    if (userInfo.is_member) {
      headers['X-Tenant-ID'] = '1';
    }

    const response = await fetch(`https://your-domain.com/api/v1/members/${userId}/avatar/upload/`, {
      method: 'POST',
      headers: headers,
      body: formData
    });

    const result = await response.json();

    if (result.success) {
      console.log('头像上传成功:', result.data);
      return result.data;
    } else {
      throw new Error(result.message);
    }
  } catch (error) {
    console.error('上传头像失败:', error);
    throw error;
  }
};
```

### 成功响应
```json
{
  "success": true,
  "code": 2000,
  "message": "头像上传成功",
  "data": {
    "avatar": "/media/avatars/avatar_123_1234567890.jpg"
  }
}
```

---

## 🔧 前端集成最佳实践

### 1. 用户信息管理组件
```javascript
class UserProfileManager {
  constructor() {
    this.baseURL = 'https://your-domain.com/api/v1';
    this.tenantId = '1';
  }

  // 获取用户信息
  async getProfile() {
    return await this.apiRequest('/members/me/');
  }

  // 更新用户信息
  async updateProfile(updates) {
    return await this.apiRequest('/members/me/', {
      method: 'PATCH',
      body: JSON.stringify(updates)
    });
  }

  // 修改密码
  async changePassword(oldPassword, newPassword) {
    const response = await this.apiRequest('/members/me/password/', {
      method: 'POST',
      body: JSON.stringify({
        old_password: oldPassword,
        new_password: newPassword,
        new_password_confirm: newPassword
      })
    });

    if (response.success) {
      // 密码修改成功，清除本地token
      this.logout();
    }

    return response;
  }

  // 上传头像
  async uploadAvatar(file) {
    const formData = new FormData();
    formData.append('avatar', file);

    return await this.apiRequest('/members/avatar/upload/', {
      method: 'POST',
      headers: {
        // 移除 Content-Type，让浏览器自动设置
        'Content-Type': undefined
      },
      body: formData
    });
  }

  // 通用API请求方法
  async apiRequest(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const token = localStorage.getItem('access_token');

    const headers = {
      'Authorization': `Bearer ${token}`,
      ...options.headers
    };

    // 添加租户头（Member用户）
    const userInfo = JSON.parse(localStorage.getItem('user_info') || '{}');
    if (userInfo.is_member) {
      headers['X-Tenant-ID'] = this.tenantId;
    }

    try {
      const response = await fetch(url, {
        headers,
        ...options
      });

      const result = await response.json();

      if (!result.success) {
        throw new Error(result.message || '请求失败');
      }

      return result;
    } catch (error) {
      console.error('API请求失败:', error);
      throw error;
    }
  }

  // 登出
  logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_info');
    window.location.href = '/login';
  }
}

// 使用示例
const profileManager = new UserProfileManager();

// 获取并显示用户信息
const loadUserProfile = async () => {
  try {
    const result = await profileManager.getProfile();
    displayUserInfo(result.data);
  } catch (error) {
    console.error('加载用户信息失败:', error);
  }
};

// 更新用户信息
const updateProfile = async (updates) => {
  try {
    const result = await profileManager.updateProfile(updates);
    displayUserInfo(result.data);
    showToast('个人信息更新成功', 'success');
  } catch (error) {
    showToast('更新失败: ' + error.message, 'error');
  }
};
```

### 2. 头像上传组件
```javascript
class AvatarUploader {
  constructor(options = {}) {
    this.maxSize = options.maxSize || 2 * 1024 * 1024; // 2MB
    this.allowedTypes = options.allowedTypes || [
      'image/jpeg', 'image/png', 'image/gif', 'image/webp'
    ];
    this.previewElement = options.previewElement;
    this.uploadButton = options.uploadButton;
    this.fileInput = options.fileInput;

    this.init();
  }

  init() {
    if (this.fileInput) {
      this.fileInput.addEventListener('change', (e) => this.handleFileSelect(e));
    }

    if (this.uploadButton) {
      this.uploadButton.addEventListener('click', () => this.upload());
    }
  }

  handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;

    // 验证文件
    const validation = this.validateFile(file);
    if (!validation.valid) {
      this.showError(validation.error);
      return;
    }

    // 显示预览
    this.showPreview(file);

    // 自动上传或等待用户确认
    if (this.autoUpload) {
      this.upload(file);
    }
  }

  validateFile(file) {
    if (!file) {
      return { valid: false, error: '请选择文件' };
    }

    if (!this.allowedTypes.includes(file.type)) {
      return { valid: false, error: '不支持的文件格式，请选择 JPG、PNG、GIF 或 WEBP 格式的图片' };
    }

    if (file.size > this.maxSize) {
      return { valid: false, error: '文件大小不能超过 2MB' };
    }

    return { valid: true };
  }

  showPreview(file) {
    if (!this.previewElement) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      this.previewElement.src = e.target.result;
    };
    reader.readAsDataURL(file);

    this.selectedFile = file;
  }

  async upload(file = this.selectedFile) {
    if (!file) {
      this.showError('请先选择文件');
      return;
    }

    try {
      this.showLoading(true);

      const profileManager = new UserProfileManager();
      const result = await profileManager.uploadAvatar(file);

      this.showSuccess('头像上传成功');
      this.updateUserAvatar(result.data.avatar);

    } catch (error) {
      this.showError('上传失败: ' + error.message);
    } finally {
      this.showLoading(false);
    }
  }

  showLoading(loading) {
    // 显示/隐藏加载状态
    const button = this.uploadButton;
    if (button) {
      button.disabled = loading;
      button.textContent = loading ? '上传中...' : '上传头像';
    }
  }

  showError(message) {
    // 显示错误提示
    console.error(message);
    alert(message); // 可以替换为更好的UI提示
  }

  showSuccess(message) {
    // 显示成功提示
    console.log(message);
    alert(message); // 可以替换为更好的UI提示
  }

  updateUserAvatar(avatarUrl) {
    // 更新页面上的头像显示
    const fullUrl = `https://your-domain.com${avatarUrl}`;

    // 更新预览
    if (this.previewElement) {
      this.previewElement.src = fullUrl;
    }

    // 更新其他头像显示元素
    const avatars = document.querySelectorAll('.user-avatar');
    avatars.forEach(avatar => {
      avatar.src = fullUrl;
    });
  }
}

// 使用示例
document.addEventListener('DOMContentLoaded', () => {
  const uploader = new AvatarUploader({
    fileInput: document.getElementById('avatar-input'),
    uploadButton: document.getElementById('upload-btn'),
    previewElement: document.getElementById('avatar-preview'),
    autoUpload: true  // 选择文件后自动上传
  });
});
```

### 3. 密码修改组件
```javascript
const createPasswordChangeForm = () => {
  const form = document.createElement('form');
  form.innerHTML = `
    <div class="form-group">
      <label for="old_password">当前密码</label>
      <input type="password" id="old_password" required>
    </div>

    <div class="form-group">
      <label for="new_password">新密码</label>
      <input type="password" id="new_password" required minlength="8">
      <small class="help-text">密码至少8位，包含大小写字母和数字</small>
    </div>

    <div class="form-group">
      <label for="confirm_password">确认新密码</label>
      <input type="password" id="confirm_password" required>
    </div>

    <button type="submit" class="btn btn-primary">修改密码</button>
  `;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const oldPassword = form.querySelector('#old_password').value;
    const newPassword = form.querySelector('#new_password').value;
    const confirmPassword = form.querySelector('#confirm_password').value;

    // 验证密码一致性
    if (newPassword !== confirmPassword) {
      alert('新密码和确认密码不一致');
      return;
    }

    // 验证密码强度
    if (!isValidPassword(newPassword)) {
      alert('密码不符合要求：至少8位，包含大小写字母和数字');
      return;
    }

    try {
      const profileManager = new UserProfileManager();
      await profileManager.changePassword(oldPassword, newPassword);

      // 密码修改成功会自动跳转到登录页面
    } catch (error) {
      alert('密码修改失败: ' + error.message);
    }
  });

  return form;
};

const isValidPassword = (password) => {
  // 密码强度验证：至少8位，包含大小写字母和数字
  const minLength = password.length >= 8;
  const hasLower = /[a-z]/.test(password);
  const hasUpper = /[A-Z]/.test(password);
  const hasNumber = /\d/.test(password);

  return minLength && hasLower && hasUpper && hasNumber;
};
```
