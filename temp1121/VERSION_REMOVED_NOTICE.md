# 📢 重要更新通知：ApplicationVersion已移除

**更新日期**: 2024-11-21  
**影响范围**: applications, feedbacks 模块  

---

## ⚠️ 变更说明

为简化应用管理，我们已**完全删除**ApplicationVersion相关功能：

### 已删除内容

❌ **ApplicationVersion模型**
- 独立的版本管理表 `app_version` 已删除
- 版本管理API端点 `/api/v1/application-versions/` 已删除

❌ **Feedback.application_version字段**
- 反馈不再关联具体版本
- `feedbacks_feedback.application_version_id` 字段已删除

❌ **相关API端点**
- `GET /api/v1/application-versions/`
- `POST /api/v1/application-versions/`
- `GET /api/v1/application-versions/{id}/`
- `PUT/PATCH /api/v1/application-versions/{id}/`
- `DELETE /api/v1/application-versions/{id}/`

---

## ✅ 保留内容

### Application.current_version字段

✅ **保留为CharField**
- 类型: `VARCHAR(50)`
- 默认值: `"1.0.0"`
- 用途: 简单记录当前版本号

**示例**:
```json
{
  "id": 1,
  "name": "LiPeaks CMS",
  "current_version": "2.1.0",  // 手动更新的字符串
  "status": "active"
}
```

### Licenses模块的版本字段

✅ **保留CharField版本字段**（记录用途）:
- `LicenseActivation.client_version` - 客户端版本
- `LicenseUsageLog.software_version` - 软件版本

这些字段仅用于记录，不关联ApplicationVersion表。

---

## 🔄 迁移指南

### 后端开发者

**数据库已自动迁移**:
```sql
-- 已执行
DROP TABLE IF EXISTS app_version;
ALTER TABLE feedbacks_feedback DROP COLUMN application_version_id;
ALTER TABLE app_application MODIFY COLUMN current_version VARCHAR(50) DEFAULT '1.0.0';
```

**代码已更新**:
- 所有导入已删除
- 所有序列化器已更新
- 所有视图已更新
- 所有Admin已更新

### 前端开发者

**需要删除的代码**:

```javascript
// ❌ 删除这些
import { ApplicationVersion } from '@/api/applications';
const versions = await api.get('/application-versions/');
<Select options={versions} />

// ✅ 改为使用current_version
const app = await api.get('/applications/1/');
console.log(app.current_version); // "2.0.1"
```

**更新版本的方式**:

```javascript
// ❌ 旧方式（不再支持）
await api.post('/application-versions/', {
  application: 1,
  version: '2.1.0',
  release_notes: '...'
});

// ✅ 新方式
await api.patch('/applications/1/', {
  current_version: '2.1.0'
});
```

**反馈提交**:

```javascript
// ❌ 旧方式
await api.post('/feedbacks/feedbacks/', {
  title: '问题',
  application: 1,
  application_version: 5  // 不再需要
});

// ✅ 新方式
await api.post('/feedbacks/feedbacks/', {
  title: '问题',
  application: 1
  // application_version字段已删除
});
```

---

## 📊 影响的文档

以下文档已更新，移除了ApplicationVersion相关内容：

- ✅ `API_DOC_1_APPLICATIONS.md` - 已重写
- ✅ `API_DOC_4_FEEDBACKS.md` - 已更新
- ✅ `API_MIGRATION_GUIDE.md` - 已更新
- ✅ `API_QUICK_REFERENCE.md` - 已更新
- ✅ 所有其他文档 - 已清理

**新增文档**:
- ✅ `OPENAPI_SWAGGER_GUIDE.md` - OpenAPI/Swagger UI使用指南

---

## 🎯 新的版本管理方式

### 简化的版本管理

不再需要复杂的版本管理系统，只需：

1. **更新版本号**:
   ```bash
   curl -X PATCH "http://localhost:8000/api/v1/applications/1/" \
     -H "Authorization: Bearer ${TOKEN}" \
     -d '{"current_version": "2.1.0"}'
   ```

2. **在metadata中记录更新日志**（可选）:
   ```json
   {
     "current_version": "2.1.0",
     "metadata": {
       "changelog": [
         {"version": "2.1.0", "date": "2024-11-21", "notes": "新增功能..."},
         {"version": "2.0.1", "date": "2024-11-01", "notes": "修复bug..."}
       ]
     }
   }
   ```

---

## ❓ 常见问题

### Q1: 如何获取历史版本？
**A**: 不再支持历史版本管理。如需此功能，建议在`Application.metadata`中手动维护版本历史。

### Q2: Feedback还能关联版本吗？
**A**: 不能。Feedback现在只关联Application，不关联具体版本。

### Q3: 旧数据会丢失吗？
**A**: `application_version`关联已删除，但可以在迁移前导出数据备份。

### Q4: 如何查看应用的当前版本？
**A**: 查看`Application.current_version`字段。

### Q5: 可以恢复ApplicationVersion吗？
**A**: 技术上可以回滚Git提交，但不建议。新的简化方案更易维护。

---

## 📞 技术支持

如有疑问，请参考：
- **OpenAPI文档**: http://localhost:8000/api/schema/swagger-ui/
- **详细API文档**: `temp1121/API_DOC_*.md`
- **迁移指南**: `temp1121/API_MIGRATION_GUIDE.md`

---

**更新完成时间**: 2024-11-21 21:51  
**Git提交**: 998b7386  
**测试状态**: ✅ Django check通过
