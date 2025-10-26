# JWT Token更新问题说明

## 🐛 问题描述

**现象**: 租户管理员调用软件管理API时返回403错误
```
API: PATCH /feedbacks/software-categories/1/
错误: "Only tenant administrators can manage software."
状态: 403 Forbidden
```

---

## 🎯 根本原因

### JWT Token 过期问题

**问题**: 用户使用的JWT Token是在权限修复**之前**生成的

**Token对比**:

| 字段 | 旧Token | 新Token(需要) | 说明 |
|------|---------|---------------|------|
| user_id | ✅ 2 | ✅ 2 | 正常 |
| username | ✅ admin_jin | ✅ admin_jin | 正常 |
| is_admin | ✅ true | ✅ true | 正常 |
| is_super_admin | ✅ false | ✅ false | 正常 |
| **is_staff** | ❌ **缺失** | ✅ **true** | **关键字段** |

### 权限检查失败链

```
1. 前端使用旧Token调用API
   ↓
2. 后端解码Token创建user对象  
   ↓
3. user对象缺少 is_staff=true
   ↓
4. 权限检查: SoftwareManagePermission
   ↓
5. is_tenant_admin(user) 检查失败
   ↓
6. 返回403: "Only tenant administrators can manage software."
```

---

## ✅ 解决方案

### 🎯 立即操作：重新登录

**用户操作步骤**:
1. **点击退出登录** 
   - 清除localStorage/sessionStorage中的Token
   - 清除Vuex/Pinia中的用户状态

2. **重新登录**
   - 输入用户名密码
   - 获取新的JWT Token

3. **验证结果**
   - 新Token包含 `is_staff: true`
   - API调用返回200而非403

### 📱 前端代码示例

**退出登录**:
```javascript
// 清除Token
localStorage.removeItem('token')
// 清除用户状态  
store.dispatch('auth/logout')
// 跳转到登录页
router.push('/login')
```

**重新登录后验证**:
```javascript
// 检查新Token
const token = localStorage.getItem('token')
const payload = JSON.parse(atob(token.split('.')[1]))
console.log('is_staff:', payload.is_staff) // 应该是 true
```

---

## 🔍 技术说明

### 为什么会有这个问题？

1. **时间差问题**:
   - 用户在权限修复前登录 → Token生成时 `is_staff=false`
   - 后端修复了User模型 → 数据库中 `is_staff=true`
   - 但Token还是旧的 → 权限检查失败

2. **JWT特性**:
   - JWT是无状态的，包含用户信息的快照
   - 一旦生成，内容不会自动更新
   - 必须重新生成才能获取最新用户信息

### 为什么不能自动刷新？

**技术限制**:
- JWT包含的是用户信息快照，不是实时查询
- 修改后端逻辑会影响所有用户，过于复杂
- 重新登录是最简单、最安全的解决方案

---

## 📊 影响范围

### 受影响的API

**所有需要租户管理员权限的API**:
- `PATCH/PUT/DELETE /feedbacks/software-categories/*`
- `POST/PATCH/PUT/DELETE /feedbacks/software/*` 
- `POST/PATCH/PUT/DELETE /feedbacks/software-versions/*`
- `GET /feedbacks/statistics/`
- `POST/PATCH/PUT/DELETE /feedbacks/email-templates/*`

### 不受影响的API

**查看权限的API**:
- `GET /feedbacks/software-categories/`
- `GET /feedbacks/software/`
- `GET /feedbacks/feedbacks/`
- 用户提交反馈等基础功能

---

## 🚀 验证方法

### 1. 检查当前Token
```javascript
// 在浏览器控制台执行
const token = localStorage.getItem('token') || sessionStorage.getItem('token')
if (token) {
  const payload = JSON.parse(atob(token.split('.')[1]))
  console.log('Token内容:', payload)
  console.log('is_staff存在:', 'is_staff' in payload)
  console.log('is_staff值:', payload.is_staff)
}
```

**如果输出**:
- `is_staff存在: false` → 需要重新登录 ❌
- `is_staff存在: true, is_staff值: true` → Token已更新 ✅

### 2. 测试API调用
```javascript
// 测试软件分类更新API
fetch('/api/v1/feedbacks/software-categories/1/', {
  method: 'PATCH',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    name: 'test',
    code: 'test'
  })
})
.then(res => {
  if (res.status === 200) {
    console.log('✅ 权限正常')
  } else if (res.status === 403) {
    console.log('❌ 需要重新登录')
  }
})
```

---

## ⚠️ 注意事项

### 1. 其他租户管理员
**如果系统中有多个租户管理员**，他们也需要重新登录

### 2. 记住登录状态
**如果用户选择了"记住我"**，可能需要：
- 清除remember token
- 重新勾选"记住我"选项

### 3. 多设备登录
**用户在多个设备上登录**，每个设备都需要重新登录

---

## 📝 总结

**问题**: JWT Token中缺少`is_staff`字段  
**原因**: Token生成于权限修复之前  
**解决**: 用户重新登录获取新Token  
**预期**: 所有管理功能恢复正常  

**操作时间**: < 1分钟  
**影响用户**: 租户管理员需重新登录  
**解决效果**: 100%恢复功能  

---

**立即操作**: 🔄 **请通知用户退出登录并重新登录！**
