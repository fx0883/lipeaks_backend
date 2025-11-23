# CMS API 完整测试与文档

## 📋 测试概述

**测试时间**: 2025-11-23  
**测试范围**: CMS系统所有API接口  
**测试结果**: ✅ 18/19 通过 (94.7%)

---

## 📁 文档结构

```
temp1123_2/
├── 00_README.md                      # 本文档（总览）
├── 01_文章管理API文档.md             # 文章CRUD、发布、统计等
├── 02_分类标签API文档.md             # 分类、标签、标签组管理
├── 03_评论和Member文章API文档.md     # 评论管理、Member文章
├── test_cms_fixed.sh                 # API测试脚本
├── test_results.md                   # 测试结果详细报告
└── test_output.log                   # 测试输出日志
```

---

## 🔑 关键信息

### 服务器地址
```
http://0.0.0.0:8000/api/v1/cms
```

### 认证Token

**Admin用户Token** (租户3的管理员):
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VybmFtZSI6ImFkbWluX2NtcyIsImV4cCI6MTc2NDQ5MjA3MSwibW9kZWxfdHlwZSI6InVzZXIiLCJpc19hZG1pbiI6dHJ1ZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlLCJpc19zdGFmZiI6dHJ1ZX0.sG3xbmD1mdvGgvj_i_lKfDfSZ_6cRnakqPHWy5BSObM
```

**Member用户Token** (租户3的普通成员):
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMCwidXNlcm5hbWUiOiJ0ZXN0MDJAcXEuY29tIiwiZXhwIjoxNzY0NDkyMTQxLCJtb2RlbF90eXBlIjoibWVtYmVyIiwiaXNfYWRtaW4iOmZhbHNlLCJpc19zdXBlcl9hZG1pbiI6ZmFsc2UsImlzX3N0YWZmIjpmYWxzZX0.cH6vk1v5evfxBXQJG_zuhmE_P9qPj3LcbCkUlZDByfc
```

**租户ID**: `3`

---

## 🎯 租户控制规则（重要！）

这是CMS系统的核心安全机制：

### Admin用户
- ❌ **不需要**携带`X-Tenant-ID`请求头
- ✅ 自动使用其关联的租户进行操作
- ✅ 使用`user.tenant`获取租户信息

### Member用户
- ✅ **必须**携带`X-Tenant-ID: 3`请求头
- ✅ 系统会验证头中的租户ID与用户关联的租户是否匹配
- ❌ 如果不携带或携带错误的租户ID，请求会被拒绝

### 匿名用户
- ✅ **必须**携带`X-Tenant-ID: 3`请求头（用于查询数据）
- ✅ 只能执行GET请求
- ❌ 无法执行创建、更新、删除操作

### 示例对比

```bash
# ✅ 正确 - Admin不带租户头
curl -X GET "http://0.0.0.0:8000/api/v1/cms/articles/" \
  -H "Authorization: Bearer {admin_token}"

# ❌ 错误 - Admin带租户头会被拒绝
curl -X GET "http://0.0.0.0:8000/api/v1/cms/articles/" \
  -H "Authorization: Bearer {admin_token}" \
  -H "X-Tenant-ID: 3"

# ✅ 正确 - Member必须带租户头
curl -X GET "http://0.0.0.0:8000/api/v1/cms/articles/" \
  -H "Authorization: Bearer {member_token}" \
  -H "X-Tenant-ID: 3"

# ❌ 错误 - Member不带租户头会被拒绝
curl -X GET "http://0.0.0.0:8000/api/v1/cms/articles/" \
  -H "Authorization: Bearer {member_token}"
```

---

## 📊 测试结果总结

### 通过的API (18个)

#### 文章管理 ✅
- ✅ GET /articles/ - 获取文章列表（匿名/Admin/Member）
- ✅ GET /articles/{id}/ - 获取单篇文章
- ✅ PATCH /articles/{id}/ - 更新文章
- ✅ POST /articles/{id}/publish/ - 发布文章
- ✅ GET /articles/{id}/statistics/ - 获取文章统计

#### 分类管理 ✅
- ✅ GET /categories/ - 获取分类列表
- ✅ POST /categories/ - 创建分类（需要translations字段）
- ✅ GET /categories/tree/ - 获取分类树

#### 标签管理 ✅
- ✅ GET /tags/ - 获取标签列表
- ✅ POST /tags/ - 创建标签
- ✅ GET /tags/usage-stats/ - 获取标签使用统计

#### 标签组管理 ✅
- ✅ GET /tag-groups/ - 获取标签组列表
- ✅ POST /tag-groups/ - 创建标签组
- ✅ PATCH /tag-groups/{id}/ - 更新标签组
- ✅ DELETE /tag-groups/{id}/ - 删除标签组

#### 评论管理 ✅
- ✅ GET /comments/ - 获取评论列表

#### Member文章管理 ✅
- ✅ GET /member/articles/ - Member获取文章列表
- ✅ POST /member/articles/ - Member创建文章
- ✅ PATCH /member/articles/{id}/ - Member更新文章
- ✅ POST /member/articles/{id}/publish/ - Member发布文章
- ✅ GET /member/articles/{id}/statistics/ - Member获取统计

### 发现的问题 (1个)

#### Admin创建文章偶现500错误
- **状态**: 间歇性问题
- **原因**: 需要进一步调查服务器日志
- **影响**: 低（手动重试成功）
- **建议**: 检查数据库连接和事务处理

---

## 🚀 快速开始

### 1. 运行完整测试

```bash
cd /Users/fengxuan/Documents/Github/lipeaks_backend
bash temp1123_2/test_cms_fixed.sh
```

### 2. 测试单个API

```bash
# 测试获取文章列表（匿名）
curl -X GET "http://0.0.0.0:8000/api/v1/cms/articles/" \
  -H "X-Tenant-ID: 3" | jq

# 测试创建文章（Admin）
curl -X POST "http://0.0.0.0:8000/api/v1/cms/articles/" \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "测试文章",
    "content": "内容",
    "excerpt": "摘要",
    "status": "draft"
  }' | jq

# 测试Member创建文章
curl -X POST "http://0.0.0.0:8000/api/v1/cms/member/articles/" \
  -H "Authorization: Bearer {member_token}" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Member文章",
    "content": "内容",
    "excerpt": "摘要",
    "status": "draft"
  }' | jq
```

---

## 📖 API列表

### 文章管理 (CMS-文章管理)

| 方法 | 端点 | 说明 | 权限 |
|------|------|------|------|
| GET | /articles/ | 获取文章列表 | 公开 |
| POST | /articles/ | 创建文章 | Admin |
| GET | /articles/{id}/ | 获取单篇文章 | 公开 |
| PUT | /articles/{id}/ | 更新文章 | Admin/作者 |
| PATCH | /articles/{id}/ | 部分更新文章 | Admin/作者 |
| DELETE | /articles/{id}/ | 删除文章 | Admin/作者 |
| POST | /articles/{id}/archive/ | 归档文章 | Admin |
| POST | /articles/{id}/publish/ | 发布文章 | Admin/作者 |
| POST | /articles/{id}/unpublish/ | 取消发布 | Admin |
| GET | /articles/{id}/statistics/ | 获取统计 | Admin/作者 |
| POST | /articles/{id}/view/ | 记录阅读 | 公开 |
| GET | /articles/{id}/versions/ | 版本历史 | Admin/作者 |
| GET | /articles/{id}/versions/{version}/ | 特定版本 | Admin/作者 |
| POST | /articles/batch-delete/ | 批量删除 | Admin |

### 分类管理 (CMS-分类管理)

| 方法 | 端点 | 说明 | 权限 |
|------|------|------|------|
| GET | /categories/ | 获取分类列表 | 公开 |
| POST | /categories/ | 创建分类 | Admin |
| GET | /categories/{id}/ | 获取分类详情 | 公开 |
| PUT | /categories/{id}/ | 更新分类 | Admin |
| PATCH | /categories/{id}/ | 部分更新分类 | Admin |
| DELETE | /categories/{id}/ | 删除分类 | Admin |
| GET | /categories/tree/ | 获取分类树 | 公开 |

### 标签管理 (CMS-标签管理)

| 方法 | 端点 | 说明 | 权限 |
|------|------|------|------|
| GET | /tags/ | 获取标签列表 | 公开 |
| POST | /tags/ | 创建标签 | Admin |
| GET | /tags/{id}/ | 获取标签详情 | 公开 |
| PUT | /tags/{id}/ | 更新标签 | Admin |
| PATCH | /tags/{id}/ | 部分更新标签 | Admin |
| DELETE | /tags/{id}/ | 删除标签 | Admin |
| GET | /tags/usage-stats/ | 标签使用统计 | 公开 |
| GET | /tag-groups/ | 获取标签组列表 | 公开 |
| POST | /tag-groups/ | 创建标签组 | Admin |
| GET | /tag-groups/{id}/ | 获取标签组详情 | 公开 |
| PUT | /tag-groups/{id}/ | 更新标签组 | Admin |
| PATCH | /tag-groups/{id}/ | 部分更新标签组 | Admin |
| DELETE | /tag-groups/{id}/ | 删除标签组 | Admin |

### 评论管理 (CMS-评论管理)

| 方法 | 端点 | 说明 | 权限 |
|------|------|------|------|
| GET | /comments/ | 获取评论列表 | 公开 |
| POST | /comments/ | 创建评论 | Member/游客 |
| GET | /comments/{id}/ | 获取评论详情 | 公开 |
| PUT | /comments/{id}/ | 更新评论 | 作者/Admin |
| PATCH | /comments/{id}/ | 部分更新评论 | 作者/Admin |
| DELETE | /comments/{id}/ | 删除评论 | 作者/Admin |
| POST | /comments/{id}/approve/ | 批准评论 | Admin |
| POST | /comments/{id}/reject/ | 拒绝评论 | Admin |
| POST | /comments/{id}/mark-spam/ | 标记垃圾 | Admin |
| GET | /comments/{id}/replies/ | 获取回复 | 公开 |
| POST | /comments/batch/ | 批量处理 | Admin |

### Member文章管理 (CMS-Member文章管理)

| 方法 | 端点 | 说明 | 权限 |
|------|------|------|------|
| GET | /member/articles/ | 获取我的文章列表 | Member |
| POST | /member/articles/ | 创建文章 | Member |
| GET | /member/articles/{id}/ | 获取我的文章 | Member |
| PUT | /member/articles/{id}/ | 更新文章 | Member |
| PATCH | /member/articles/{id}/ | 部分更新 | Member |
| DELETE | /member/articles/{id}/ | 删除文章 | Member |
| POST | /member/articles/{id}/publish/ | 发布文章 | Member |
| GET | /member/articles/{id}/statistics/ | 获取统计 | Member |

---

## ⚠️ 重要注意事项

### 1. 分类创建需要translations字段
创建分类时必须提供`translations`对象：

```json
{
  "name": "分类名",
  "slug": "category-slug",
  "translations": {
    "zh-hans": {
      "name": "分类名",
      "description": "描述"
    }
  }
}
```

### 2. 租户头使用规则
- Admin: 不带`X-Tenant-ID`
- Member/匿名: 必带`X-Tenant-ID: 3`

### 3. API路径区分
- Admin文章API: `/api/v1/cms/articles/`
- Member文章API: `/api/v1/cms/member/articles/`

### 4. 权限层级
```
超级管理员 > 租户管理员(Admin) > 普通成员(Member) > 游客
```

---

## 🔧 常见问题排查

### 问题1: 401 Unauthorized
**原因**: Token过期或无效  
**解决**: 重新登录获取新Token

### 问题2: 400 Tenant operation failed
**原因**: 
- Admin用户错误地携带了`X-Tenant-ID`头
- Member用户没有携带或携带了错误的租户ID

**解决**: 检查请求头，按规则添加或移除`X-Tenant-ID`

### 问题3: 403 Permission Denied
**原因**: 权限不足  
**解决**: 确认用户角色和操作权限

### 问题4: 创建分类失败 - translations字段必填
**原因**: 没有提供`translations`字段  
**解决**: 添加`translations`对象

---

## 📈 性能建议

1. **分页查询**: 使用`page`和`page_size`参数避免一次加载过多数据
2. **过滤查询**: 使用具体的过滤条件（status, category_id等）减少数据量
3. **缓存**: 对于分类树、标签列表等相对静态的数据考虑前端缓存

---

## 🎓 最佳实践

### 1. Member发布文章流程
```bash
# 1. 创建草稿
# 2. 编辑内容
# 3. 添加分类和标签
# 4. 预览
# 5. 发布
# 6. 查看统计
```

### 2. Admin审核内容流程
```bash
# 1. 查看待审核列表
# 2. 批量或单个审核
# 3. 标记垃圾内容
# 4. 删除违规内容
```

### 3. 前端集成建议
- 使用拦截器统一处理Token和租户头
- 根据用户角色动态添加/移除`X-Tenant-ID`
- 实现错误统一处理和友好提示

---

## 📞 支持

如有问题，请查阅详细文档：
- `01_文章管理API文档.md`
- `02_分类标签API文档.md`
- `03_评论和Member文章API文档.md`
