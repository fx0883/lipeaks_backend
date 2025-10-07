# 前端迁移指南 - Member API重构

## 📢 重要通知

Member管理API已重构，**管理员端API路径已变更**！

**变更日期**：2025-10-06  
**影响范围**：仅管理员端API  
**Member端API**：无变化，完全兼容

---

## 🎯 核心变更

### API路径变更

```diff
管理员端API（需要更新）:
- GET /api/v1/members/              → GET /api/v1/admin/members/
- POST /api/v1/members/             → POST /api/v1/admin/members/
- GET /api/v1/members/{id}/         → GET /api/v1/admin/members/{id}/
- PUT /api/v1/members/{id}/         → PUT /api/v1/admin/members/{id}/
- PATCH /api/v1/members/{id}/       → PATCH /api/v1/admin/members/{id}/
- DELETE /api/v1/members/{id}/      → DELETE /api/v1/admin/members/{id}/
- POST /api/v1/members/{id}/avatar/upload/ → POST /api/v1/admin/members/{id}/avatar/upload/

Member端API（无需更新）:
✓ GET /api/v1/members/me/                    （不变）
✓ PUT /api/v1/members/me/                    （不变）
✓ POST /api/v1/members/me/password/          （不变）
✓ POST /api/v1/members/avatar/upload/        （不变）
✓ GET /api/v1/members/sub-accounts/          （不变）
✓ POST /api/v1/members/sub-accounts/         （不变）
```

---

## 🔧 快速迁移步骤

### 步骤1：确定需要修改的文件

使用以下命令在项目中搜索需要修改的API调用：

```bash
# 在前端项目根目录执行
grep -r "api/v1/members/" src/ --include="*.js" --include="*.ts" --include="*.vue" --include="*.jsx" --include="*.tsx"
```

### 步骤2：识别API类型

查看每个API调用的上下文，判断是管理员API还是Member API：

**管理员API特征**：
- 在管理后台页面中调用
- 有分页、搜索、筛选功能
- 可以查看多个Member
- 可以创建/编辑/删除Member

**Member API特征**：
- 在个人中心页面中调用
- 只操作自己的数据
- 路径包含 `/me/`

### 步骤3：批量替换

#### 方法A：手动查找替换（推荐）

使用IDE的查找替换功能：

1. 查找：`/api/v1/members/`（排除 `/me/`）
2. 在管理后台相关文件中替换为：`/api/v1/admin/members/`

#### 方法B：使用脚本批量替换

**警告**：请先备份代码！

```bash
# 仅在管理后台目录中替换
find src/views/admin -type f \( -name "*.js" -o -name "*.vue" -o -name "*.ts" \) \
  -exec sed -i '' 's|/api/v1/members/|/api/v1/admin/members/|g' {} \;
```

### 步骤4：验证替换结果

确保没有误替换Member端API：

```bash
# 检查是否有错误替换
grep -r "/api/v1/admin/members/me/" src/
# 如果有结果，说明误替换了Member端API，需要改回来
```

如果发现误替换：

```bash
# 将错误的路径改回来
sed -i '' 's|/api/v1/admin/members/me/|/api/v1/members/me/|g' <affected_file>
```

---

## 📝 代码示例对比

### 旧代码（需要修改）

```javascript
// ❌ 旧的管理员端API调用
import axios from 'axios';

// 获取Member列表
const getMemberList = async () => {
  const response = await axios.get('/api/v1/members/', {
    params: { page: 1, page_size: 20 }
  });
  return response.data;
};

// 创建Member
const createMember = async (data) => {
  const response = await axios.post('/api/v1/members/', data);
  return response.data;
};

// 删除Member
const deleteMember = async (id) => {
  await axios.delete(`/api/v1/members/${id}/`);
};
```

### 新代码（推荐写法）

```javascript
// ✅ 新的管理员端API调用
import axios from 'axios';

const ADMIN_MEMBER_API = '/api/v1/admin/members';

// 获取Member列表
const getMemberList = async () => {
  const response = await axios.get(`${ADMIN_MEMBER_API}/`, {
    params: { page: 1, page_size: 20 }
  });
  return response.data;
};

// 创建Member
const createMember = async (data) => {
  const response = await axios.post(`${ADMIN_MEMBER_API}/`, data);
  return response.data;
};

// 删除Member
const deleteMember = async (id) => {
  await axios.delete(`${ADMIN_MEMBER_API}/${id}/`);
};
```

---

## 🚀 推荐的代码组织

### 创建API常量文件

**`src/api/endpoints.js`**

```javascript
// API端点配置
export const API_ENDPOINTS = {
  // 认证
  auth: {
    login: '/api/v1/auth/login/',
    logout: '/api/v1/auth/logout/',
    refresh: '/api/v1/auth/token/refresh/',
  },
  
  // 管理员端 - Member管理
  adminMember: {
    base: '/api/v1/admin/members',
    list: '/api/v1/admin/members/',
    create: '/api/v1/admin/members/',
    detail: (id) => `/api/v1/admin/members/${id}/`,
    update: (id) => `/api/v1/admin/members/${id}/`,
    delete: (id) => `/api/v1/admin/members/${id}/`,
    uploadAvatar: (id) => `/api/v1/admin/members/${id}/avatar/upload/`,
    subAccounts: {
      list: '/api/v1/admin/members/sub-accounts/',
      detail: (id) => `/api/v1/admin/members/sub-accounts/${id}/`,
    }
  },
  
  // Member端 - 自用API
  member: {
    base: '/api/v1/members',
    me: '/api/v1/members/me/',
    updateMe: '/api/v1/members/me/',
    changePassword: '/api/v1/members/me/password/',
    uploadAvatar: '/api/v1/members/avatar/upload/',
    subAccounts: {
      list: '/api/v1/members/sub-accounts/',
      create: '/api/v1/members/sub-accounts/',
      detail: (id) => `/api/v1/members/sub-accounts/${id}/`,
    }
  }
};
```

### 创建API Service文件

**`src/api/services/adminMemberService.js`**

```javascript
import axios from 'axios';
import { API_ENDPOINTS } from '../endpoints';

class AdminMemberService {
  async getList(params = {}) {
    const { data } = await axios.get(API_ENDPOINTS.adminMember.list, { params });
    return data;
  }
  
  async create(memberData) {
    const { data } = await axios.post(API_ENDPOINTS.adminMember.create, memberData);
    return data;
  }
  
  async getDetail(id) {
    const { data } = await axios.get(API_ENDPOINTS.adminMember.detail(id));
    return data;
  }
  
  async update(id, memberData) {
    const { data } = await axios.patch(API_ENDPOINTS.adminMember.update(id), memberData);
    return data;
  }
  
  async delete(id) {
    await axios.delete(API_ENDPOINTS.adminMember.delete(id));
  }
  
  async uploadAvatar(id, file) {
    const formData = new FormData();
    formData.append('avatar', file);
    const { data } = await axios.post(
      API_ENDPOINTS.adminMember.uploadAvatar(id),
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return data;
  }
}

export default new AdminMemberService();
```

**`src/api/services/memberService.js`**

```javascript
import axios from 'axios';
import { API_ENDPOINTS } from '../endpoints';

class MemberService {
  async getMe() {
    const { data } = await axios.get(API_ENDPOINTS.member.me);
    return data;
  }
  
  async updateMe(memberData) {
    const { data } = await axios.put(API_ENDPOINTS.member.updateMe, memberData);
    return data;
  }
  
  async changePassword(passwordData) {
    const { data } = await axios.post(API_ENDPOINTS.member.changePassword, passwordData);
    return data;
  }
  
  async uploadAvatar(file) {
    const formData = new FormData();
    formData.append('avatar', file);
    const { data } = await axios.post(
      API_ENDPOINTS.member.uploadAvatar,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return data;
  }
}

export default new MemberService();
```

### 在组件中使用

```vue
<script setup>
import { ref } from 'vue';
import adminMemberService from '@/api/services/adminMemberService';
import memberService from '@/api/services/memberService';

const currentUser = ref(null);

// 管理员获取Member列表
async function loadMemberList() {
  if (currentUser.value.is_admin) {
    const data = await adminMemberService.getList({ page: 1 });
    console.log(data);
  }
}

// Member获取自己信息
async function loadMyProfile() {
  const data = await memberService.getMe();
  console.log(data);
}
</script>
```

---

## ✅ 迁移检查清单

前端开发完成后，请逐项检查：

### 管理员后台

- [ ] Member列表页面可以正常加载
- [ ] Member搜索功能正常
- [ ] Member筛选功能正常
- [ ] 创建Member功能正常
- [ ] 编辑Member功能正常
- [ ] 删除Member功能正常
- [ ] 上传Member头像功能正常
- [ ] 查看所有子账号功能正常（新增）

### Member个人中心

- [ ] Member查看自己信息正常
- [ ] Member编辑自己信息正常
- [ ] Member修改密码正常
- [ ] Member上传头像正常
- [ ] Member管理子账号正常

### 错误处理

- [ ] 401错误跳转登录页
- [ ] 403错误显示权限不足
- [ ] 404错误显示资源不存在
- [ ] 400错误显示参数错误详情

---

## 🆘 遇到问题？

### 问题1：API调用返回404

**原因**：使用了旧的API路径  
**解决**：检查是否正确使用了 `/api/v1/admin/members/`

### 问题2：Member端API不工作

**检查**：是否误将Member端API也改成了 `/admin/` 路径  
**解决**：Member端API应该保持 `/api/v1/members/me/` 等路径

### 问题3：权限不足403错误

**检查**：是否使用了正确的用户角色访问对应的API  
**解决**：
- 管理员应访问 `/api/v1/admin/members/`
- Member应访问 `/api/v1/members/me/`

---

## 📞 技术支持

- Swagger文档：`http://localhost:8000/api/v1/docs/`
- ReDoc文档：`http://localhost:8000/api/v1/redoc/`
- 联系后端团队获取更多支持

---

**祝迁移顺利！** 🚀

