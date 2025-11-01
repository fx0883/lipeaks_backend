# 前端API文档集 - 目录

> **版本**: 2.0  
> **发布日期**: 2025-10-31  
> **适用平台**: iOS / Android / Web

---

## 📖 文档导航

### 🌟 推荐阅读顺序

1. **[README_前端API文档.md](./README_前端API文档.md)** ⭐⭐⭐
   - 📝 文档集总览
   - 🎯 快速开始指南
   - 📱 平台特定说明
   - **建议所有人先读这个！**

2. **[00_API文档索引.md](./00_API文档索引.md)** ⭐⭐⭐
   - 📊 API端点速查表
   - 🔍 常用场景查找
   - 🎯 功能权限矩阵
   - **用作速查手册**

3. **[01_Member用户自服务API文档.md](./01_Member用户自服务API文档.md)** ⭐⭐⭐
   - 👤 用户信息管理
   - 🔒 密码修改
   - 📸 头像上传
   - **4个核心接口**

4. **[02_子账号管理API文档.md](./02_子账号管理API文档.md)** ⭐⭐
   - 👥 子账号CRUD
   - 📋 子账号列表
   - **5个接口**

5. **[03_Member用户互动API文档.md](./03_Member用户互动API文档.md)** ⭐⭐⭐
   - 👍 点赞功能（6个接口）
   - ➕ 关注功能（8个接口）
   - ⭐ 收藏功能（5个接口）
   - **19个接口**

6. **[04_通用集成指南.md](./04_通用集成指南.md)** ⭐⭐⭐
   - 🛠️ 各平台集成要点
   - 🔄 完整集成流程图
   - ⚡ 性能优化建议
   - 🛡️ 安全最佳实践
   - **开发前必读**

---

## 📊 API统计

### 接口总数：28个

| 模块 | 接口数 |
|------|--------|
| Member用户自服务 | 4 |
| 子账号管理 | 5 |
| 用户互动-点赞 | 6 |
| 用户互动-关注 | 8 |
| 用户互动-收藏 | 5 |

---

## 🚀 快速开始

### 最小集成步骤

```
1. 配置API Base URL和租户ID
   ↓
2. 实现登录功能
   ↓
3. 保存Token到本地安全存储
   ↓
4. 配置HTTP客户端（自动添加认证头）
   ↓
5. 调用API获取数据
   ↓
6. 解析响应并显示
```

### 验证集成成功

**测试方法**:

```bash
# 1. 登录测试
curl -X POST "https://your-domain.com/api/v1/auth/member/login/" \
  -H "X-Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123"}'

# 2. 获取用户信息测试
curl -X GET "https://your-domain.com/api/v1/members/me/" \
  -H "Authorization: Bearer <token>" \
  -H "X-Tenant-ID: 1"
```

如果都返回正确数据 → 集成成功 ✅

---

## 📱 平台适配说明

### iOS
- 使用URLSession或Alamofire
- Token存储在Keychain
- 使用Codable解析JSON

### Android  
- 使用Retrofit + OkHttp
- Token存储在EncryptedSharedPreferences
- 使用Gson/Moshi解析JSON

### Web
- 使用axios或fetch
- Token存储在localStorage
- 使用TypeScript类型定义

---

## 🎯 核心功能导航

### 用户管理
→ [01_Member用户自服务API文档.md](./01_Member用户自服务API文档.md)

### 子账号
→ [02_子账号管理API文档.md](./02_子账号管理API文档.md)

### 社交互动
→ [03_Member用户互动API文档.md](./03_Member用户互动API文档.md)

### 集成指南
→ [04_通用集成指南.md](./04_通用集成指南.md)

---

## 📞 技术支持

### 文档反馈
如发现文档问题，请联系后端团队。

### API问题
如遇到API使用问题：
1. 查阅对应API文档
2. 使用Postman测试
3. 联系后端团队

---

## 📅 更新日志

| 版本 | 日期 | 说明 |
|------|------|------|
| 2.0 | 2025-10-31 | 重构为通用文档，移除特定框架代码 |
| 1.0 | 2025-10-31 | 初始版本 |

---

**Happy Coding! 🚀**
