# 租户ID传递方式说明 - 三种用户类型对照

> **更新日期**: 2025-11-03  
> **重要程度**: ⭐⭐⭐ 必读  
> **适用对象**: 所有前端开发者

---

## 🎯 核心概念

不同类型的用户，访问CMS API时传递租户ID的方式**完全不同**！

---

## 📊 三种用户类型对照表

| 用户类型 | 租户ID来源 | 使用X-Tenant-ID? | 使用?tenant_id=? | 前端配置 |
|---------|-----------|-----------------|----------------|---------|
| **超级管理员** | 查询参数或全部 | ❌ **禁止** | ✅ 可选 | 不设置X-Tenant-ID |
| **租户管理员** | user.tenant或参数 | ❌ **禁止** | ✅ 可选 | 不设置X-Tenant-ID |
| **Member/匿名** | X-Tenant-ID头 | ✅ **必须** | ❌ 忽略 | 必须设置X-Tenant-ID |

---

## 👤 用户类型详解

### 类型1：超级管理员（Super Admin）

**Token特征**：
```json
{
  "is_super_admin": true,
  "is_admin": true
}
```

**访问规则**：
- ✅ 可以访问**所有租户**的数据
- ✅ 通过`?tenant_id=X`过滤特定租户
- ✅ 不带参数返回所有租户数据
- ❌ **禁止**使用`X-Tenant-ID`头

**API调用示例**：

```bash
# 获取所有租户的分类
curl 'http://localhost:8000/api/v1/cms/categories/' \
  -H 'Authorization: Bearer YOUR_TOKEN'

# 获取租户1的分类
curl 'http://localhost:8000/api/v1/cms/categories/?tenant_id=1' \
  -H 'Authorization: Bearer YOUR_TOKEN'

# 获取租户2的分类
curl 'http://localhost:8000/api/v1/cms/categories/?tenant_id=2' \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

**前端配置（React示例）**：

```javascript
// 超级管理员可以选择租户
const [selectedTenantId, setSelectedTenantId] = useState(null);

const fetchCategories = async () => {
  let url = '/api/v1/cms/categories/';
  if (selectedTenantId) {
    url += `?tenant_id=${selectedTenantId}`;
  }
  
  const res = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${token}`
      // 不使用X-Tenant-ID！
    }
  });
  return res.json();
};
```

---

### 类型2：租户管理员（Tenant Admin）

**Token特征**：
```json
{
  "is_super_admin": false,
  "is_admin": true
}
```

**用户特征**：
- 用户对象有`tenant`属性
- `user.tenant.id = 3`（示例）

**访问规则**：
- ✅ **自动**使用`user.tenant`的租户ID
- ✅ 可选使用`?tenant_id=X`（但只能访问自己的租户）
- ❌ 只能访问**自己租户**的数据
- ❌ **禁止**使用`X-Tenant-ID`头

**API调用示例**：

```bash
# 方式1：不带参数（推荐）
# 自动使用用户关联的租户ID（如租户3）
curl 'http://localhost:8000/api/v1/cms/categories/' \
  -H 'Authorization: Bearer YOUR_TOKEN'
# → 返回租户3的数据

# 方式2：明确指定（必须是自己的租户）
curl 'http://localhost:8000/api/v1/cms/categories/?tenant_id=3' \
  -H 'Authorization: Bearer YOUR_TOKEN'
# → 返回租户3的数据

# ❌ 错误：尝试访问其他租户
curl 'http://localhost:8000/api/v1/cms/categories/?tenant_id=1' \
  -H 'Authorization: Bearer YOUR_TOKEN'
# → 403错误：无权访问

# ❌ 错误：使用X-Tenant-ID头
curl 'http://localhost:8000/api/v1/cms/categories/' \
  -H 'X-Tenant-ID: 1' \
  -H 'Authorization: Bearer YOUR_TOKEN'
# → 400错误：管理员不应使用X-Tenant-ID
```

**前端配置（Vue示例）**：

```javascript
// 租户管理员前端 - 不需要设置X-Tenant-ID
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1'
});

api.interceptors.request.use(config => {
  // 添加Token
  const token = localStorage.getItem('token');
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }
  
  // 添加语言
  const lang = localStorage.getItem('language') || 'zh-hans';
  config.headers['Accept-Language'] = lang;
  
  // 🔑 关键：不添加X-Tenant-ID！
  // 系统会自动从Token中的用户信息获取租户
  
  return config;
});

// 使用
const categories = await api.get('/cms/categories/');
// 自动返回用户所属租户的分类
```

---

### 类型3：Member用户或匿名用户

**Token特征（Member）**：
```json
{
  "is_super_admin": false,
  "is_admin": false,
  "model_type": "member"
}
```

**访问规则**：
- ✅ **必须**使用`X-Tenant-ID`头指定租户
- ❌ 查询参数`?tenant_id=X`会被忽略
- ✅ 只能访问指定租户的数据

**API调用示例**：

```bash
# Member用户或匿名访问
curl 'http://localhost:8000/api/v1/cms/categories/' \
  -H 'X-Tenant-ID: 1' \  # ✅ 必须提供
  -H 'Authorization: Bearer YOUR_TOKEN'  # Member可选

# 匿名用户
curl 'http://localhost:8000/api/v1/cms/categories/' \
  -H 'X-Tenant-ID: 1'  # ✅ 必须提供
  # 不需要Authorization

# ❌ 错误：没有X-Tenant-ID
curl 'http://localhost:8000/api/v1/cms/categories/' \
  -H 'Authorization: Bearer YOUR_TOKEN'
# → 400错误：缺少租户ID
```

**前端配置**：

```javascript
// Member用户前端 - 必须设置X-Tenant-ID
axios.defaults.headers.common['X-Tenant-ID'] = '1';

axios.interceptors.request.use(config => {
  const tenantId = localStorage.getItem('tenantId') || '1';
  config.headers['X-Tenant-ID'] = tenantId;  // 🔑 Member必须
  
  const token = localStorage.getItem('token');
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }
  
  return config;
});
```

---

## 🔑 如何判断用户类型？

### 方法1：从Token Payload判断

登录成功后，解析Token payload：

```javascript
// 解析JWT Token（需要jwt-decode库）
import jwtDecode from 'jwt-decode';

const token = localStorage.getItem('token');
const payload = jwtDecode(token);

const userType = {
  isSuperAdmin: payload.is_super_admin === true,
  isTenantAdmin: payload.is_admin === true && payload.is_super_admin !== true,
  isMember: payload.model_type === 'member'
};

console.log(userType);
// { isSuperAdmin: false, isTenantAdmin: true, isMember: false }
```

### 方法2：从登录响应判断

```javascript
// 登录API应该返回用户类型信息
const loginResponse = await api.post('/auth/login/', { username, password });

const userInfo = loginResponse.data;
// {
//   user: {...},
//   token: "...",
//   is_admin: true,
//   is_super_admin: false,
//   tenant_id: 3
// }

// 保存用户类型
if (userInfo.is_super_admin) {
  localStorage.setItem('userRole', 'super_admin');
} else if (userInfo.is_admin) {
  localStorage.setItem('userRole', 'tenant_admin');
} else {
  localStorage.setItem('userRole', 'member');
}
```

---

## 💻 智能HTTP客户端配置

### 推荐方案：根据用户类型自动配置

```javascript
// utils/api.js
import axios from 'axios';
import jwtDecode from 'jwt-decode';

const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1'
});

// 智能请求拦截器
api.interceptors.request.use(config => {
  const token = localStorage.getItem('token');
  
  // 添加Token
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`;
    
    // 解析Token判断用户类型
    try {
      const payload = jwtDecode(token);
      const isSuperAdmin = payload.is_super_admin === true;
      const isTenantAdmin = payload.is_admin === true && !isSuperAdmin;
      const isMember = payload.model_type === 'member';
      
      // 根据用户类型设置租户信息
      if (isMember) {
        // Member用户必须使用X-Tenant-ID
        const tenantId = localStorage.getItem('tenantId');
        if (tenantId) {
          config.headers['X-Tenant-ID'] = tenantId;
        }
      } else if (isTenantAdmin) {
        // 租户管理员不使用X-Tenant-ID
        // 可选：如果需要指定租户，使用查询参数
        // config.params = config.params || {};
        // config.params.tenant_id = payload.tenant_id;
      } else if (isSuperAdmin) {
        // 超级管理员不使用X-Tenant-ID
        // 可以通过组件传递tenant_id参数
      }
    } catch (e) {
      console.error('Token解析失败:', e);
    }
  } else {
    // 匿名用户必须使用X-Tenant-ID
    const tenantId = localStorage.getItem('tenantId');
    if (tenantId) {
      config.headers['X-Tenant-ID'] = tenantId;
    }
  }
  
  // 添加语言
  const lang = localStorage.getItem('language') || 'zh-hans';
  config.headers['Accept-Language'] = lang;
  
  return config;
});

export default api;
```

---

## 🚨 常见错误和解决方案

### 错误1：租户管理员使用X-Tenant-ID

**症状**：
```
HTTP 400
{
  "message": "管理员不应使用X-Tenant-ID请求头"
}
```

**原因**：代码设计禁止管理员使用X-Tenant-ID

**解决**：
```javascript
// ❌ 错误
config.headers['X-Tenant-ID'] = '1';  // 管理员不要设置这个！

// ✅ 正确
// 不设置X-Tenant-ID，让系统自动从user.tenant获取
```

### 错误2：Member用户没有X-Tenant-ID

**症状**：
```
HTTP 400
{
  "message": "未提供租户ID，无法访问CMS资源"
}
```

**解决**：
```javascript
// ✅ 正确
config.headers['X-Tenant-ID'] = localStorage.getItem('tenantId');
```

### 错误3：租户管理员想访问其他租户

**症状**：
```
HTTP 403
{
  "message": "无法访问其他租户的资源"
}
```

**原因**：租户管理员只能访问自己的租户

**解决**：
- 使用该租户的管理员账号
- 或请求超级管理员协助

---

## 📋 快速判断指南

### 我应该使用哪种方式？

**问题1：你的角色是什么？**

查看Token payload中的字段：
```javascript
const payload = jwtDecode(token);

if (payload.is_super_admin === true) {
  console.log("你是超级管理员");
  console.log("→ 不使用X-Tenant-ID，使用?tenant_id=X参数");
}
else if (payload.is_admin === true && payload.is_super_admin === false) {
  console.log("你是租户管理员");
  console.log("→ 不使用X-Tenant-ID，自动获取租户或使用?tenant_id=X");
}
else if (payload.model_type === 'member') {
  console.log("你是Member用户");
  console.log("→ 必须使用X-Tenant-ID头");
}
else {
  console.log("无法判断，可能是匿名用户");
  console.log("→ 必须使用X-Tenant-ID头");
}
```

---

## 🎯 实际案例分析

### 案例：租户管理员admin_cms

**用户信息**：
- 用户名：admin_cms
- 角色：租户管理员
- 关联租户：租户3（"填色"）

**正确调用**：

```bash
# ✅ 方式1：自动使用租户3
curl 'http://localhost:8000/api/v1/cms/categories/' \
  -H 'Authorization: Bearer YOUR_TOKEN'
# 返回：租户3的分类

# ✅ 方式2：明确指定租户3
curl 'http://localhost:8000/api/v1/cms/categories/?tenant_id=3' \
  -H 'Authorization: Bearer YOUR_TOKEN'
# 返回：租户3的分类
```

**错误调用**：

```bash
# ❌ 使用X-Tenant-ID
curl 'http://localhost:8000/api/v1/cms/categories/' \
  -H 'X-Tenant-ID: 1' \
  -H 'Authorization: Bearer YOUR_TOKEN'
# 错误：管理员不应使用X-Tenant-ID

# ❌ 尝试访问其他租户
curl 'http://localhost:8000/api/v1/cms/categories/?tenant_id=1' \
  -H 'Authorization: Bearer YOUR_TOKEN'
# 错误：无权访问租户1
```

---

## 🛠️ 前端实现建议

### 统一的API客户端

```javascript
// api/client.js
import axios from 'axios';
import jwtDecode from 'jwt-decode';

class APIClient {
  constructor() {
    this.client = axios.create({
      baseURL: 'http://localhost:8000/api/v1'
    });
    
    this.setupInterceptors();
  }
  
  setupInterceptors() {
    this.client.interceptors.request.use(config => {
      const token = localStorage.getItem('token');
      
      if (token) {
        config.headers['Authorization'] = `Bearer ${token}`;
        
        // 根据用户类型配置租户ID
        const userType = this.getUserType(token);
        
        if (userType === 'member' || userType === 'anonymous') {
          // Member和匿名用户使用X-Tenant-ID
          const tenantId = localStorage.getItem('tenantId');
          if (tenantId) {
            config.headers['X-Tenant-ID'] = tenantId;
          }
        }
        // 管理员和超级管理员不使用X-Tenant-ID
        // 他们使用查询参数或自动获取
      } else {
        // 匿名用户使用X-Tenant-ID
        const tenantId = localStorage.getItem('tenantId');
        if (tenantId) {
          config.headers['X-Tenant-ID'] = tenantId;
        }
      }
      
      // 添加语言
      const lang = localStorage.getItem('language') || 'zh-hans';
      config.headers['Accept-Language'] = lang;
      
      return config;
    });
  }
  
  getUserType(token) {
    try {
      const payload = jwtDecode(token);
      
      if (payload.is_super_admin === true) {
        return 'super_admin';
      }
      if (payload.is_admin === true && payload.is_super_admin === false) {
        return 'tenant_admin';
      }
      if (payload.model_type === 'member') {
        return 'member';
      }
      
      return 'unknown';
    } catch {
      return 'anonymous';
    }
  }
  
  // API方法
  getCategories(tenantId = null) {
    let params = {};
    
    // 只有超级管理员才使用tenant_id参数
    if (tenantId && this.getUserType(localStorage.getItem('token')) === 'super_admin') {
      params.tenant_id = tenantId;
    }
    
    return this.client.get('/cms/categories/', { params });
  }
}

export default new APIClient();

// 使用
import api from '@/api/client';
const categories = await api.getCategories();
```

---

## 📚 代码位置参考

关键代码在：

**租户过滤逻辑**：
- `common/viewsets.py` 第63-113行
- `TenantModelViewSet.get_queryset()`方法

**关键判断**：
```python
# 第67-68行
is_super_admin = bool(is_auth and getattr(request, 'auth_type', None) == 'jwt' and getattr(user, 'is_super_admin', False))
is_tenant_admin = bool(is_auth and getattr(user, 'is_admin', False) and not is_super_admin)

# 第72-74行：管理员禁止使用X-Tenant-ID
if (is_super_admin or is_tenant_admin) and header_tid is not None:
    raise TenantHeaderInvalidOrMissing()

# 第89-102行：租户管理员自动获取租户
elif is_tenant_admin:
    q_tid = request.GET.get('tenant_id')
    if q_tid is not None:
        effective_tenant_id = int(q_tid)
    else:
        user_tenant = getattr(user, 'tenant', None)
        if user_tenant:
            effective_tenant_id = int(user_tenant.id)  # 🔑 关键
```

---

## ✅ 总结

### 核心要点

1. **租户管理员**（你的情况）：
   - ❌ 不要使用X-Tenant-ID头
   - ✅ 系统自动从user.tenant获取租户ID
   - ✅ 只能访问自己租户的数据

2. **Member用户**：
   - ✅ 必须使用X-Tenant-ID头
   - ❌ 不能使用tenant_id参数

3. **超级管理员**：
   - ❌ 不要使用X-Tenant-ID头
   - ✅ 使用tenant_id参数选择租户
   - ✅ 可以访问所有租户

### 你的正确调用方式

```bash
# 作为租户管理员，只需要Token
curl 'http://localhost:8000/api/v1/cms/categories/' \
  -H 'Authorization: Bearer YOUR_TOKEN'

# 自动返回你的租户（租户3）的数据
```

---

**你是对的！租户管理员确实不需要X-Tenant-ID，系统会自动从Token获取租户信息！** ✅

