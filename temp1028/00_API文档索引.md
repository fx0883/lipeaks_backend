# Lipeaks Backend API 文档索引

> **适用对象**: 前端开发人员（iOS/Web/Android）  
> **项目**: Lipeaks Backend  
> **文档版本**: 2.0  
> **最后更新**: 2025-10-31

---

## 📚 文档概览

本文档集合包含了Lipeaks Backend项目中Member用户相关的所有API接口文档。每个文档都包含详细的接口说明、请求参数、响应格式和集成流程说明，适用于各种前端技术栈（iOS/Android/Web）。

---

## 📖 文档列表

### 1. Member用户自服务API
**文件名**: `01_Member用户自服务API文档.md`  
**Base URL**: `/api/v1/members/`

#### 包含功能
- ✅ 获取当前用户信息 - `GET /me/`
- ✅ 更新当前用户信息 - `PUT /me/`
- ✅ 修改密码 - `POST /me/password/`
- ✅ 上传头像 - `POST /avatar/upload/`

#### 适用场景
- 用户个人中心页面
- 用户资料编辑功能
- 账号设置模块

---

### 2. 子账号管理API
**文件名**: `02_子账号管理API文档.md`  
**Base URL**: `/api/v1/members/sub-accounts/`

#### 包含功能
- ✅ 获取子账号列表 - `GET /`
- ✅ 创建子账号 - `POST /`
- ✅ 获取子账号详情 - `GET /{id}/`
- ✅ 更新子账号信息 - `PATCH /{id}/`
- ✅ 删除子账号 - `DELETE /{id}/`

#### 适用场景
- 多设备管理
- 家庭账户功能
- 子账号管理模块

---

### 3. Member用户互动API
**文件名**: `03_Member用户互动API文档.md`  
**Base URL**: `/api/v1/interactions/`

#### 包含功能

**点赞功能** (6个接口)
- ✅ 获取我点赞的用户列表 - `GET /likes/`
- ✅ 点赞用户 - `POST /likes/`
- ✅ 取消点赞 - `DELETE /likes/{id}/`
- ✅ 获取收到的点赞列表 - `GET /likes/received/`
- ✅ 通过用户ID取消点赞 - `DELETE /likes/by-member/{member_id}/`
- ✅ 检查是否已点赞用户 - `GET /likes/check/{member_id}/`

**关注功能** (8个接口)
- ✅ 获取我的关注列表 - `GET /follows/`
- ✅ 关注用户 - `POST /follows/`
- ✅ 取消关注 - `DELETE /follows/{id}/`
- ✅ 获取粉丝列表 - `GET /follows/followers/`
- ✅ 通过用户ID取消关注 - `DELETE /follows/by-member/{member_id}/`
- ✅ 检查是否已关注用户 - `GET /follows/check/{member_id}/`
- ✅ 获取互相关注列表 - `GET /follows/mutual/`
- ✅ 获取关注统计信息 - `GET /follows/stats/`

**收藏功能** (5个接口)
- ✅ 获取收藏列表 - `GET /favorites/`
- ✅ 收藏文章 - `POST /favorites/`
- ✅ 取消收藏 - `DELETE /favorites/{id}/`
- ✅ 通过文章ID取消收藏 - `DELETE /favorites/by-article/{article_id}/`
- ✅ 检查是否已收藏文章 - `GET /favorites/check/{article_id}/`

#### 适用场景
- 社交互动功能
- 用户关系管理
- 内容收藏功能

---

## 🔑 通用认证说明

### HTTP请求头要求

所有API请求都必须包含以下HTTP头：

```
Authorization: Bearer <your_jwt_token>
X-Tenant-ID: <tenant_id>
Content-Type: application/json  # POST/PUT请求
```

### 获取JWT Token

**接口**: `POST /api/v1/auth/member/login/`

**请求**:
```json
{
  "username": "your_username",
  "password": "your_password"
}
```

**响应**:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 10,
    "username": "john_doe"
  }
}
```

**集成说明**:
1. 发送登录请求获取`access` token
2. 将token存储在本地（localStorage/Keychain/SharedPreferences）
3. 后续请求在Authorization头中携带：`Bearer <access_token>`
4. Token过期时使用refresh token刷新

---

## 📊 API统计总览

### 按功能模块

| 模块 | 接口数量 | HTTP方法分布 |
|------|----------|-------------|
| Member用户自服务 | 4 | GET:1, PUT:1, POST:2 |
| 子账号管理 | 5 | GET:2, POST:1, PATCH:1, DELETE:1 |
| 用户互动-点赞 | 6 | GET:3, POST:1, DELETE:2 |
| 用户互动-关注 | 8 | GET:5, POST:1, DELETE:2 |
| 用户互动-收藏 | 5 | GET:3, POST:1, DELETE:1 |
| **总计** | **28** | GET:14, POST:6, PUT:1, PATCH:1, DELETE:6 |

### 按权限要求

| 权限类型 | 接口数量 | 说明 |
|---------|----------|------|
| 需要认证 | 28 | 所有接口都需要登录 |
| 仅Member用户 | 14 | 点赞和关注功能 |
| Member+子账号 | 9 | 用户自服务功能 |
| 包含管理员 | 5 | 收藏功能 |

---

## 🎯 功能权限矩阵

### Member用户功能权限

| 功能 | Member主账号 | 子账号 | 说明 |
|------|-------------|--------|------|
| 查看个人信息 | ✅ | ✅ | 只能查看自己 |
| 修改个人信息 | ✅ | ✅ | username/email不可改 |
| 修改密码 | ✅ | ✅ | 需要旧密码验证 |
| 上传头像 | ✅ | ❌ | 子账号无此权限 |
| 管理子账号 | ✅ | ❌ | 创建/编辑/删除 |
| 点赞用户 | ✅ | ✅ | 仅限Member之间 |
| 关注用户 | ✅ | ✅ | 仅限Member之间 |
| 收藏文章 | ✅ | ✅ | 所有认证用户 |

---

## 🔍 常用场景快速查找

### 场景1: 用户个人中心

**需要的接口**:
1. `GET /api/v1/members/me/` - 获取用户信息
2. `PUT /api/v1/members/me/` - 更新用户信息
3. `POST /api/v1/members/avatar/upload/` - 上传头像
4. `GET /api/v1/interactions/follows/stats/` - 获取关注统计

**集成流程**:
```
1. 页面加载 → 调用获取用户信息API
2. 显示用户信息（头像、昵称、统计数据）
3. 用户编辑 → 调用更新API
4. 用户上传头像 → 调用上传API
```

---

### 场景2: 用户列表（带互动按钮）

**需要的接口**:
1. `GET /api/v1/interactions/likes/check/{member_id}/` - 检查点赞状态
2. `POST /api/v1/interactions/likes/` - 点赞
3. `DELETE /api/v1/interactions/likes/by-member/{member_id}/` - 取消点赞
4. `GET /api/v1/interactions/follows/check/{member_id}/` - 检查关注状态
5. `POST /api/v1/interactions/follows/` - 关注
6. `DELETE /api/v1/interactions/follows/by-member/{member_id}/` - 取消关注

**集成流程**:
```
1. 加载用户列表
2. 对每个用户：
   - 调用检查点赞API
   - 调用检查关注API
3. 显示对应的按钮状态
4. 用户点击 → 调用点赞/关注API
5. 更新UI状态
```

---

### 场景3: 文章详情（带收藏）

**需要的接口**:
1. `GET /api/v1/interactions/favorites/check/{article_id}/` - 检查收藏状态
2. `POST /api/v1/interactions/favorites/` - 收藏文章
3. `DELETE /api/v1/interactions/favorites/by-article/{article_id}/` - 取消收藏

**集成流程**:
```
1. 加载文章详情
2. 调用检查收藏API
3. 显示收藏按钮状态
4. 用户点击 → 调用收藏/取消收藏API
5. 更新按钮状态
```

---

### 场景4: 我的关注页面

**需要的接口**:
1. `GET /api/v1/interactions/follows/` - 获取关注列表
2. `GET /api/v1/interactions/follows/followers/` - 获取粉丝列表
3. `GET /api/v1/interactions/follows/mutual/` - 获取互相关注列表
4. `DELETE /api/v1/interactions/follows/by-member/{member_id}/` - 取消关注

**集成流程**:
```
1. 显示Tab切换（关注/粉丝/好友）
2. 根据Tab调用对应API
3. 显示用户列表
4. 用户点击取消关注 → 调用取消关注API
5. 刷新列表
```

---

## ⚠️ 通用注意事项

### 1. 租户隔离
- 所有请求必须包含`X-Tenant-ID`头
- 跨租户操作会返回403错误
- 在用户登录后立即获取并保存租户ID

### 2. Token管理
- Token存储在安全位置（iOS: Keychain, Android: EncryptedSharedPreferences, Web: localStorage）
- 在请求头中添加：`Authorization: Bearer <token>`
- Token过期（401错误）时跳转登录页

### 3. 错误处理
- 400: 参数错误，显示具体错误信息
- 401: 未认证，跳转登录
- 403: 权限不足，显示提示
- 404: 资源不存在，显示提示
- 500: 服务器错误，显示通用提示

### 4. 业务规则
- 不能点赞/关注自己
- 不能跨租户操作
- 不能重复点赞/关注/收藏
- 子账号不能上传头像
- 子账号不能管理子账号

---

## 🔄 通用集成流程

### 基础集成流程

```
┌─────────────────┐
│  1. 用户登录     │
│  获取JWT Token  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  2. 保存Token   │
│  保存租户ID     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  3. 配置HTTP    │
│  添加认证头     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  4. 调用API     │
│  处理响应       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  5. 更新UI      │
│  显示数据       │
└─────────────────┘
```

### 互动功能集成流程

```
┌──────────────────┐
│ 加载页面/组件     │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 调用检查状态API   │
│ (check接口)      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 显示对应按钮状态  │
│ (已点赞/未点赞)  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 用户点击按钮     │
└────────┬─────────┘
         │
         ▼
    ┌────┴────┐
    │  判断   │
    └────┬────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌────────┐
│ 已操作 │ │ 未操作 │
│ 取消   │ │ 执行   │
└───┬────┘ └───┬────┘
    │          │
    └────┬─────┘
         │
         ▼
┌──────────────────┐
│ 调用对应API      │
│ (create/delete)  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 更新UI状态       │
│ 显示反馈         │
└──────────────────┘
```

---

## 📊 API端点速查表

### Member用户自服务

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/v1/members/me/` | 获取当前用户信息 |
| PUT | `/api/v1/members/me/` | 更新用户信息 |
| POST | `/api/v1/members/me/password/` | 修改密码 |
| POST | `/api/v1/members/avatar/upload/` | 上传头像 |

### 子账号管理

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/v1/members/sub-accounts/` | 获取子账号列表 |
| POST | `/api/v1/members/sub-accounts/` | 创建子账号 |
| GET | `/api/v1/members/sub-accounts/{id}/` | 获取子账号详情 |
| PATCH | `/api/v1/members/sub-accounts/{id}/` | 更新子账号 |
| DELETE | `/api/v1/members/sub-accounts/{id}/` | 删除子账号 |

### 点赞功能

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/v1/interactions/likes/` | 我的点赞列表 |
| POST | `/api/v1/interactions/likes/` | 点赞用户 |
| DELETE | `/api/v1/interactions/likes/{id}/` | 取消点赞 |
| GET | `/api/v1/interactions/likes/received/` | 收到的点赞 |
| DELETE | `/api/v1/interactions/likes/by-member/{member_id}/` | 通过ID取消点赞 |
| GET | `/api/v1/interactions/likes/check/{member_id}/` | 检查点赞状态 |

### 关注功能

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/v1/interactions/follows/` | 我的关注列表 |
| POST | `/api/v1/interactions/follows/` | 关注用户 |
| DELETE | `/api/v1/interactions/follows/{id}/` | 取消关注 |
| GET | `/api/v1/interactions/follows/followers/` | 粉丝列表 |
| DELETE | `/api/v1/interactions/follows/by-member/{member_id}/` | 通过ID取消关注 |
| GET | `/api/v1/interactions/follows/check/{member_id}/` | 检查关注状态 |
| GET | `/api/v1/interactions/follows/mutual/` | 互相关注列表 |
| GET | `/api/v1/interactions/follows/stats/` | 关注统计 |

### 收藏功能

| 方法 | 端点 | 说明 |
|------|------|------|
| GET | `/api/v1/interactions/favorites/` | 收藏列表 |
| POST | `/api/v1/interactions/favorites/` | 收藏文章 |
| DELETE | `/api/v1/interactions/favorites/{id}/` | 取消收藏 |
| DELETE | `/api/v1/interactions/favorites/by-article/{article_id}/` | 通过ID取消收藏 |
| GET | `/api/v1/interactions/favorites/check/{article_id}/` | 检查收藏状态 |

---

## 🌍 多平台集成注意事项

### iOS (SwiftUI/UIKit)
- 使用`URLSession`或`Alamofire`发送HTTP请求
- Token存储在`Keychain`中
- 租户ID可存储在`UserDefaults`
- 处理JSON响应使用`Codable`协议

### Android (Kotlin)
- 使用`Retrofit`或`OkHttp`
- Token存储在`EncryptedSharedPreferences`
- 使用`Gson`或`Moshi`解析JSON
- 实现Token拦截器自动添加认证头

### Web (Vue/React/Angular)
- 使用`axios`或`fetch`
- Token存储在`localStorage`或`sessionStorage`
- 使用axios拦截器自动添加认证头
- 处理CORS问题（开发环境代理）

### 小程序 (微信/支付宝)
- 使用`wx.request`或`my.request`
- Token存储在`storage`
- 注意请求域名白名单配置
- 处理请求超时

---

## ⚡ 性能优化建议

### 1. 请求优化
- ✅ 实现请求缓存机制（5分钟）
- ✅ 使用分页加载大量数据
- ✅ 避免重复请求（去重）
- ✅ 合并相似的请求

### 2. 状态管理
- ✅ 缓存用户信息（减少重复获取）
- ✅ 缓存点赞/关注状态
- ✅ 实现乐观更新（立即UI反馈）
- ✅ 定期刷新统计数据

### 3. 图片优化
- ✅ 头像使用CDN加速
- ✅ 实现图片懒加载
- ✅ 使用缩略图（列表页）
- ✅ 压缩上传的图片

---

## 🛡️ 安全最佳实践

### 1. Token安全
- ✅ 使用安全存储（Keychain/Encrypted Storage）
- ❌ 不在URL中传递Token
- ❌ 不在日志中输出Token
- ✅ 实现Token自动刷新

### 2. 输入验证
- ✅ 客户端验证所有输入
- ✅ 文件上传前验证类型和大小
- ✅ 防止XSS攻击
- ✅ 敏感信息加密传输

### 3. HTTPS
- ✅ 生产环境强制HTTPS
- ✅ 验证SSL证书
- ❌ 不允许HTTP降级

---

## 📱 响应式数据结构

### 分页响应格式

所有列表接口都使用统一的分页格式：

```json
{
  "count": 100,           // 总记录数
  "next": "url",          // 下一页URL，null表示没有下一页
  "previous": "url",      // 上一页URL，null表示没有上一页
  "results": []           // 当前页数据数组
}
```

### 错误响应格式

**字段级错误**:
```json
{
  "field_name": ["错误信息1", "错误信息2"]
}
```

**通用错误**:
```json
{
  "detail": "错误描述信息"
}
```

---

## 🧭 集成步骤建议

### 第一阶段：基础功能（1-2天）
1. 实现登录功能
2. 实现HTTP客户端配置
3. 实现获取用户信息
4. 实现Token自动添加

### 第二阶段：核心功能（3-5天）
1. 实现用户资料查看和编辑
2. 实现头像上传
3. 实现密码修改
4. 实现基础错误处理

### 第三阶段：互动功能（3-4天）
1. 实现点赞功能
2. 实现关注功能
3. 实现收藏功能
4. 实现状态检查

### 第四阶段：优化（2-3天）
1. 添加请求缓存
2. 实现乐观更新
3. 优化性能
4. 完善错误处理

---

## 📖 文档阅读建议

### 对于iOS开发者
1. 先阅读API文档索引（本文档）
2. 查看具体API文档了解接口详情
3. 使用Swift的`Codable`定义响应模型
4. 参考HTTP请求格式实现网络层

### 对于Web开发者
1. 先阅读API文档索引（本文档）
2. 查看具体API文档
3. 实现axios配置和拦截器
4. 根据响应格式定义TypeScript类型

### 对于Android开发者
1. 先阅读API文档索引（本文档）
2. 查看具体API文档
3. 使用Retrofit定义接口
4. 实现拦截器添加认证头

---

## 🎓 相关资源

### API文档工具
- **Swagger UI**: https://your-domain.com/api/v1/docs/
- **ReDoc**: https://your-domain.com/api/v1/redoc/
- **OpenAPI Schema**: https://your-domain.com/api/v1/schema/

### 推荐工具
- **Postman**: API测试工具
- **Insomnia**: API测试工具
- **curl**: 命令行测试工具

---

## 📞 技术支持

### 问题反馈

如遇到以下问题，请按对应方式处理：

| 问题类型 | 处理方式 |
|---------|---------|
| API使用疑问 | 查阅对应API文档 |
| API行为异常 | 联系后端团队 |
| 文档错误 | 提交文档反馈 |
| 功能建议 | 提交需求建议 |

---

## 更新日志

| 版本 | 日期 | 说明 |
|------|------|------|
| 2.0 | 2025-10-31 | 移除前端代码示例，改为通用集成说明 |
| 1.0 | 2025-10-31 | 初始版本 |

---

**开始您的集成之旅！ 🚀**
