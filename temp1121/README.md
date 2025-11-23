# LiPeaks Backend API 文档

## 📚 文档目录

### API文档
- [Applications API](./API_DOC_1_APPLICATIONS.md) - 应用管理API
- [CMS API](./API_DOC_2_CMS.md) - 内容管理API（分类、文章）
- [Licenses API](./API_DOC_3_LICENSES.md) - 许可证管理API
- [Feedbacks API](./API_DOC_4_FEEDBACKS.md) - 反馈管理API

### 其他文档
- [OpenAPI / Swagger UI 指南](./OPENAPI_SWAGGER_GUIDE.md) - 在线API文档使用指南
- [版本变更通知](./VERSION_REMOVED_NOTICE.md) - ApplicationVersion删除说明
- [数据库同步报告](./DATABASE_SYNC_COMPLETE.md) - 数据库清理记录

### 测试工具
- [API测试脚本](./test_apis.sh) - 自动化测试脚本

---

## 🚀 快速开始

### 1. 启动服务器

```bash
python3 manage.py runserver
```

### 2. 访问在线文档

打开浏览器访问: http://localhost:8000/api/schema/swagger-ui/

### 3. 获取认证Token

```bash
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}' \
  | jq -r '.data.token')

echo $TOKEN
```

### 4. 测试API

```bash
# 设置Token环境变量
export TOKEN="your_token_here"

# 获取应用列表
curl "http://localhost:8000/api/v1/applications/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1" | jq
```

---

## 📋 重要变更

### ❌ 已删除的功能

1. **ApplicationVersion模型** - 不再支持独立版本管理
2. **Feedback.application_version字段** - 反馈不再关联具体版本
3. **SoftwareProduct表** - 已完全删除，使用Application代替

### ✅ 保留的功能

1. **Application.current_version** - 字符串类型，默认"1.0.0"
2. **向后兼容层** - SoftwareProductSerializer仍然可用，实际使用Application

---

## 🔗 在线资源

| 工具 | URL | 说明 |
|------|-----|------|
| Swagger UI | http://localhost:8000/api/schema/swagger-ui/ | 交互式API测试 |
| ReDoc | http://localhost:8000/api/schema/redoc/ | API文档查看 |
| OpenAPI Schema | http://localhost:8000/api/schema/ | JSON格式 |

---

## 📞 技术支持

如有问题，请参考相应模块的API文档，每个文档都包含完整的curl示例。
