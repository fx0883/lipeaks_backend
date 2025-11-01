# Lipeaks Backend - 前端API文档集

> **文档版本**: 2.0  
> **发布日期**: 2025-10-31  
> **适用平台**: iOS / Android / Web  
> **维护团队**: Backend Development Team

---

## 🎯 文档目标

本文档集旨在帮助**所有平台**的前端开发人员（iOS/Android/Web）：

✅ **快速理解** API的使用方法  
✅ **直接集成** 无需反复沟通  
✅ **了解流程** 通过流程图理解业务逻辑  
✅ **避免错误** 详细的错误处理说明  

**适用技术栈**:
- iOS: Swift (SwiftUI/UIKit)
- Android: Kotlin/Java
- Web: Vue/React/Angular
- 其他: 任何支持HTTP的客户端

---

## 📚 文档列表

### 推荐阅读顺序

#### 1. 📑 API文档索引 ⭐⭐⭐
**文件**: `00_API文档索引.md`

**内容**:
- 所有API端点速查表
- 功能权限矩阵
- 常用场景快速查找
- 通用集成流程图

**建议**: **首先阅读**，了解全局

---

#### 2. 👤 Member用户自服务API ⭐⭐⭐
**文件**: `01_Member用户自服务API文档.md`  
**Base URL**: `/api/v1/members/`

**包含接口** (4个):
- `GET /me/` - 获取当前用户信息
- `PUT /me/` - 更新用户信息
- `POST /me/password/` - 修改密码
- `POST /avatar/upload/` - 上传头像

**适用场景**:
- 用户个人中心
- 账号设置
- 资料编辑

---

#### 3. 👥 子账号管理API ⭐⭐
**文件**: `02_子账号管理API文档.md`  
**Base URL**: `/api/v1/members/sub-accounts/`

**包含接口** (5个):
- `GET /` - 获取子账号列表
- `POST /` - 创建子账号
- `GET /{id}/` - 获取子账号详情
- `PATCH /{id}/` - 更新子账号
- `DELETE /{id}/` - 删除子账号

**适用场景**:
- 多设备管理
- 家庭账户

---

#### 4. ❤️ Member用户互动API ⭐⭐⭐
**文件**: `03_Member用户互动API文档.md`  
**Base URL**: `/api/v1/interactions/`

**包含接口** (19个):

**点赞** (6个):
- 获取/创建/删除点赞
- 检查点赞状态
- 获取收到的点赞

**关注** (8个):
- 获取关注/粉丝/好友列表
- 创建/删除关注
- 检查关注状态
- 获取统计信息

**收藏** (5个):
- 获取/创建/删除收藏
- 检查收藏状态

**适用场景**:
- 社交互动
- 用户关系
- 内容收藏

---

#### 5. 🛠️ 通用集成指南 ⭐⭐⭐
**文件**: `04_通用集成指南.md`

**内容**:
- 各平台集成说明（iOS/Android/Web）
- HTTP客户端配置
- 核心集成流程图
- 最佳实践建议
- 性能优化策略

**建议**: **开始开发前阅读**

---

## 📊 API统计总览

### 接口数量统计

| 模块 | 接口数 | GET | POST | PUT | PATCH | DELETE |
|------|--------|-----|------|-----|-------|--------|
| 用户自服务 | 4 | 1 | 2 | 1 | 0 | 0 |
| 子账号管理 | 5 | 2 | 1 | 0 | 1 | 1 |
| 点赞功能 | 6 | 3 | 1 | 0 | 0 | 2 |
| 关注功能 | 8 | 5 | 1 | 0 | 0 | 2 |
| 收藏功能 | 5 | 3 | 1 | 0 | 0 | 1 |
| **总计** | **28** | **14** | **6** | **1** | **1** | **6** |

---

## 🚀 快速开始

### 5步快速集成

```
步骤1: 配置环境
  ↓
设置API_BASE_URL和TENANT_ID

步骤2: 实现登录
  ↓
调用 POST /auth/member/login/
保存返回的Token

步骤3: 配置HTTP客户端
  ↓
添加拦截器/中间件
自动添加认证头

步骤4: 调用API
  ↓
GET /members/me/
获取用户信息

步骤5: 显示数据
  ↓
解析响应，更新UI
```

### 测试集成是否成功

使用cURL或Postman测试：

```bash
# 1. 登录
POST /api/v1/auth/member/login/
请求体: {"username":"test","password":"test123"}
请求头: X-Tenant-ID: 1

# 2. 获取用户信息
GET /api/v1/members/me/
请求头: 
  Authorization: Bearer <token>
  X-Tenant-ID: 1

# 如果都返回正确数据，说明集成成功 ✅
```

---

## 🔑 认证机制

### JWT Token认证流程

```
┌─────────────┐
│ 用户登录     │
│ 输入账号密码 │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ POST /auth/ │
│ member/     │
│ login/      │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 返回Token   │
│ - access    │
│ - refresh   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 保存到本地   │
│ 安全存储     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 后续请求     │
│ 自动携带     │
│ Token        │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 401错误时   │
│ 清除Token   │
│ 跳转登录    │
└─────────────┘
```

### Token存储建议

| 平台 | 推荐方案 | 安全性 |
|------|---------|--------|
| iOS | Keychain | ⭐⭐⭐⭐⭐ |
| Android | EncryptedSharedPreferences | ⭐⭐⭐⭐⭐ |
| Web | localStorage/sessionStorage | ⭐⭐⭐ |

---

## 📱 平台特定说明

### iOS开发建议

**网络库选择**:
- URLSession（系统自带）
- Alamofire（第三方）

**关键点**:
- 使用`Codable`解析JSON
- Token存储在Keychain
- 实现`RequestAdapter`添加认证头
- 使用`Combine`或`async/await`处理异步

---

### Android开发建议

**网络库选择**:
- Retrofit + OkHttp（推荐）
- Ktor Client

**关键点**:
- 使用`data class`定义模型
- Token存储在EncryptedSharedPreferences
- 实现OkHttp `Interceptor`添加认证头
- 使用Coroutines处理异步

---

### Web开发建议

**网络库选择**:
- axios（推荐）
- fetch（原生）

**关键点**:
- 使用TypeScript定义类型
- Token存储在localStorage
- 使用axios拦截器
- 处理CORS问题（开发环境代理）

---

## 🎯 典型使用场景

### 场景1: 个人中心页面

**需要的API**:
1. `GET /members/me/` - 获取用户信息
2. `GET /follows/stats/` - 获取关注统计

**显示内容**:
- 用户头像（拼接完整URL）
- 用户昵称
- 关注数、粉丝数、好友数
- 编辑资料按钮

---

### 场景2: 用户卡片组件

**需要的API**:
1. `GET /likes/check/{member_id}/` - 检查点赞状态
2. `GET /follows/check/{member_id}/` - 检查关注状态

**显示内容**:
- 用户基本信息
- 点赞按钮（已点赞/未点赞）
- 关注按钮（已关注/互关/未关注）

**交互**:
- 点击点赞 → 调用点赞/取消点赞API
- 点击关注 → 调用关注/取消关注API

---

### 场景3: 文章详情页

**需要的API**:
1. `GET /favorites/check/{article_id}/` - 检查收藏状态
2. `POST /favorites/` - 收藏文章
3. `DELETE /favorites/by-article/{article_id}/` - 取消收藏

**显示内容**:
- 文章内容
- 收藏按钮（已收藏/未收藏）

---

## ⚠️ 重要注意事项

### 1. 租户隔离
- **所有请求必须包含`X-Tenant-ID`头**
- 跨租户操作会被拒绝（403错误）
- 租户ID在登录时确定，后续不可更改

### 2. 用户类型限制
- 点赞和关注功能**仅限Member用户**
- User（管理员）无法使用这些功能
- 请求时会验证用户类型

### 3. 自我操作限制
- **不能点赞自己**
- **不能关注自己**
- 尝试这样做会返回400错误

### 4. 唯一性约束
- 同一用户不能重复点赞同一用户
- 同一用户不能重复关注同一用户
- 同一用户不能重复收藏同一文章

---

## 🔍 调试和测试

### Postman测试建议

1. **创建环境变量**:
   - `base_url`: API基础URL
   - `tenant_id`: 租户ID
   - `access_token`: 登录后的Token

2. **创建请求集合**:
   - Authentication（登录）
   - Member APIs（用户相关）
   - Interactions APIs（互动相关）

3. **使用环境变量**:
   ```
   URL: {{base_url}}/api/v1/members/me/
   Headers:
     Authorization: Bearer {{access_token}}
     X-Tenant-ID: {{tenant_id}}
   ```

### cURL测试模板

```bash
# 设置变量
BASE_URL="https://api.your-domain.com"
TENANT_ID="1"
TOKEN="your_access_token"

# 测试模板
curl -X GET "${BASE_URL}/api/v1/members/me/" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "X-Tenant-ID: ${TENANT_ID}"
```

---

## 📖 文档使用指南

### 对于iOS开发者

**阅读顺序**:
1. API文档索引 → 了解全局
2. Member用户自服务API → 实现用户资料
3. Member用户互动API → 实现社交功能
4. 通用集成指南 → 了解iOS集成要点

**重点关注**:
- Keychain存储Token
- Codable解析JSON
- URLSession配置
- 错误处理

---

### 对于Android开发者

**阅读顺序**:
1. API文档索引 → 了解全局
2. Member用户自服务API → 实现用户功能
3. Member用户互动API → 实现互动功能
4. 通用集成指南 → 了解Android集成要点

**重点关注**:
- EncryptedSharedPreferences存储
- Retrofit配置
- OkHttp Interceptor
- 协程处理异步

---

### 对于Web开发者

**阅读顺序**:
1. API文档索引 → 了解全局
2. 各个具体API文档 → 了解接口详情
3. 通用集成指南 → 了解Web集成要点

**重点关注**:
- axios拦截器
- CORS处理
- TypeScript类型定义
- 状态管理

---

## 🎨 UI/UX建议

### 按钮状态设计

**点赞按钮**:
- 未点赞：灰色/白色 + "点赞" 或 👍
- 已点赞：蓝色/红色 + "已点赞" 或 👍（填充）

**关注按钮**:
- 未关注：灰色/白色边框 + "+ 关注"
- 已关注：蓝色/绿色 + "✓ 已关注"
- 互相关注：金色/紫色 + "✓ 互相关注"

**收藏按钮**:
- 未收藏：空心图标 ♡
- 已收藏：实心图标 ❤️（红色）

### 加载状态显示

**推荐方式**:
- 列表加载：显示骨架屏
- 按钮操作：禁用按钮 + 显示加载图标
- 全局操作：显示顶部进度条或遮罩

### 错误提示

**推荐方式**:
- 字段错误：显示在输入框下方
- 操作错误：使用Toast/Snackbar
- 严重错误：使用Alert/Dialog

---

## 📊 数据模型概览

### 核心数据对象

**用户信息**:
```
id, username, email, phone, nick_name, avatar,
wechat_id, status, tenant, is_sub_account, parent
```

**点赞记录**:
```
id, from_member, to_member, from_member_info,
to_member_info, tenant, created_at
```

**关注记录**:
```
id, follower, following, follower_info,
following_info, is_mutual, tenant, created_at
```

**收藏记录**:
```
id, user, article, article_detail, user_info,
tenant, created_at
```

### 分页响应格式

```json
{
  "count": 总记录数,
  "next": "下一页URL或null",
  "previous": "上一页URL或null",
  "results": [数据数组]
}
```

---

## ⚡ 性能优化建议

### 1. 请求优化
- ✅ 实现请求缓存（5分钟）
- ✅ 使用分页加载
- ✅ 避免重复请求
- ✅ 请求去重

### 2. 用户体验优化
- ✅ 乐观更新（立即反馈）
- ✅ 显示加载状态
- ✅ 平滑动画过渡
- ✅ 错误提示友好

### 3. 图片优化
- ✅ 头像使用CDN
- ✅ 实现懒加载
- ✅ 使用缓存
- ✅ 压缩上传图片

---

## 🛡️ 安全建议

### Token安全
- ✅ 使用安全存储（Keychain/EncryptedSharedPreferences）
- ❌ 不在URL中传递Token
- ❌ 不在日志中输出Token
- ✅ Token过期后立即清除

### 数据传输
- ✅ 生产环境必须使用HTTPS
- ✅ 验证SSL证书
- ❌ 不允许HTTP降级
- ✅ 敏感数据加密传输

### 输入验证
- ✅ 客户端验证所有输入
- ✅ 文件上传前检查类型和大小
- ✅ 防止注入攻击
- ✅ 限制输入长度

---

## 🧪 测试检查清单

### 基础功能
- [ ] 登录成功并获取Token
- [ ] Token正确保存到本地
- [ ] Token自动添加到请求头
- [ ] 成功获取用户信息
- [ ] 成功更新用户信息
- [ ] 成功修改密码
- [ ] 成功上传头像

### 互动功能
- [ ] 点赞功能正常
- [ ] 关注功能正常
- [ ] 收藏功能正常
- [ ] 状态检查准确
- [ ] 重复操作被拒绝
- [ ] 自我操作被拒绝

### 错误处理
- [ ] 401错误跳转登录
- [ ] 400错误显示具体信息
- [ ] 403错误显示权限不足
- [ ] 网络错误显示重试
- [ ] 所有错误都有友好提示

---

## 🔄 状态同步策略

### 本地状态维护

**推荐维护的状态**:

```
用户状态:
- currentUser: 当前用户信息对象
- isLoggedIn: Boolean

互动状态:
- likedMemberIds: 已点赞用户ID集合
- followedMemberIds: 已关注用户ID集合  
- favoritedArticleIds: 已收藏文章ID集合

统计数据:
- followingCount: 关注数
- followersCount: 粉丝数
- mutualCount: 好友数
```

**更新时机**:
- 登录时：初始化状态
- 操作成功后：更新对应状态
- 登出时：清空所有状态
- 定期：刷新统计数据

---

## 📞 技术支持

### 获取帮助

**问题处理流程**:

```
遇到问题
  ↓
查阅相关API文档
  ↓
问题解决? → 是 → 继续开发
  ↓ 否
使用Postman/cURL测试API
  ↓
问题解决? → 是 → 继续开发
  ↓ 否
联系后端团队
```

### 联系方式

| 问题类型 | 联系方式 |
|---------|---------|
| API使用问题 | 查阅文档 |
| API异常 | 联系后端团队 |
| 文档错误 | 提交文档反馈 |
| 功能建议 | 提交需求 |

---

## 📚 相关资源

### 在线API文档

访问以下URL查看交互式API文档：

- **Swagger UI**: `https://your-domain.com/api/v1/docs/`
- **ReDoc**: `https://your-domain.com/api/v1/redoc/`
- **OpenAPI Schema**: `https://your-domain.com/api/v1/schema/`

### 推荐工具

- **Postman**: API测试和调试
- **Insomnia**: API测试工具
- **Charles**: 网络抓包工具
- **Swagger Editor**: OpenAPI编辑器

---

## 🎓 最佳实践

### 1. 错误处理

**统一错误处理机制**:
```
所有API调用 → 
  try {
    发送请求
    处理响应
  } catch (error) {
    根据状态码处理:
      401 → 跳转登录
      403 → 显示权限不足
      400 → 显示具体错误
      其他 → 显示通用错误
  }
```

### 2. 状态管理

**推荐模式**:
- iOS: ObservableObject + @Published
- Android: ViewModel + LiveData/StateFlow
- Web: Pinia/Redux/Zustand

### 3. 网络请求

**推荐模式**:
- 创建单独的网络层/服务层
- 封装所有API调用
- 统一错误处理
- 支持请求取消

---

## 📝 数据类型参考

### 基础类型

```
Integer: 整数
String: 字符串
Boolean: 布尔值
DateTime: ISO 8601格式日期时间字符串
  例如: "2025-10-31T10:30:00Z"
```

### 枚举类型

```
用户状态 (status):
- "active": 活跃
- "suspended": 暂停
- "inactive": 未激活
```

### Null处理

某些字段可能为null，需要正确处理：
- `parent`: 主账号时为null
- `next`/`previous`: 无上下页时为null
- 各种check接口的`*_id`字段：未操作时为null

---

## 更新日志

| 版本 | 日期 | 说明 |
|------|------|------|
| 2.0 | 2025-10-31 | 重写为通用集成指南，适配所有平台 |
| 1.0 | 2025-10-31 | 初始版本 |

---

**开始您的集成之旅！ 🚀**
