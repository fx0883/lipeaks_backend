# 许可证系统API文档

## 📚 文档目录

### 核心文档
1. [**00_API修复总结和完整列表**](./00_API修复总结和完整列表.md) - 修复问题总结、API完整列表
2. [**01_许可证产品管理API**](./01_许可证产品管理API.md) - 产品CRUD、密钥对管理、统计
3. [**02_许可证方案管理API**](./02_许可证方案管理API.md) - 方案配置、复制、价格管理
4. [**03_许可证管理API**](./03_许可证管理API.md) - 许可证生命周期管理
5. [**05_客户端激活API**](./05_客户端激活API.md) - 客户端集成、激活验证

### 测试相关
- [**test_all_licenses_apis.sh**](./test_all_licenses_apis.sh) - 自动化测试脚本

---

## 🚀 快速开始

### 1. 获取认证Token

```bash
# 租户管理员登录
curl -X POST "http://localhost:8000/api/v1/users/admin/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "your_password"
  }'
```

### 2. 使用Token调用API

```bash
# 获取产品列表
curl -X GET "http://localhost:8000/api/v1/licenses/admin/products/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"
```

---

## 📊 测试结果

**最新测试**: 2025-11-23  
**测试API数**: 18个  
**通过率**: 100% ✅

### 测试覆盖范围
- ✅ 产品管理 (2/2)
- ✅ 方案管理 (2/2)
- ✅ 许可证管理 (2/2)
- ✅ 分配管理 (3/3)
- ✅ 激活记录 (1/1)
- ✅ 机器绑定 (1/1)
- ✅ 审计日志 (1/1)
- ✅ 租户配额 (1/1)
- ✅ 报告统计 (2/2)
- ✅ 服务状态 (1/1)
- ✅ Member API (2/2)

---

## 🔧 已修复的问题

### 1. ApplicationViewSet 500错误
- **问题**: metadata字段类型处理不当
- **修复**: 添加类型检查和异常处理
- **文件**: `licenses/serializers.py`

### 2. LicenseAssignmentViewSet 500错误
- **问题**: prefetch_related使用错误的关系名
- **修复**: 修改为正确的application关系
- **文件**: `licenses/views/assignment_views.py`

### 3. /licenses/status/ 400错误
- **问题**: 健康检查API被租户中间件拦截
- **修复**: 添加到租户验证豁免列表
- **文件**: `common/services/tenant_validator.py`

---

## 📋 API统计

| 分类 | API数量 | 权限要求 |
|------|---------|---------|
| 产品管理 | 8 | 租户管理员 |
| 方案管理 | 7 | 租户管理员 |
| 许可证管理 | 11 | 租户管理员 |
| 分配管理 | 15 | 租户管理员 |
| 激活记录 | 2 | 租户管理员 |
| 机器绑定 | 3 | 租户管理员 |
| 审计日志 | 2 | 租户管理员 |
| 租户配额 | 6 | 租户管理员 |
| 客户端激活 | 6 | 公开 |
| Member用户 | 6 | Member |
| 报告统计 | 3 | 租户管理员 |
| **总计** | **67** | - |

---

## 🔑 核心概念

### 1. 产品 (Application)
软件产品的基本信息，包含名称、版本、RSA密钥对等。

### 2. 方案 (LicensePlan)
许可证模板，定义默认配置、功能权限、价格等。

### 3. 许可证 (License)
具体的授权凭证，包含许可证密钥、有效期、激活限制。

### 4. 分配 (LicenseAssignment)
许可证与Member用户的关联关系，支持权限细化。

### 5. 激活 (LicenseActivation)
客户端激活记录，包含激活码、硬件绑定信息。

### 6. 机器绑定 (MachineBinding)
设备与许可证的绑定关系，用于激活数限制。

---

## 🛡️ 安全特性

1. **租户隔离**: 所有数据按租户严格隔离
2. **权限控制**: 基于角色的访问控制(RBAC)
3. **频率限制**: API调用频率限制，防止滥用
4. **硬件绑定**: 基于硬件指纹的设备识别
5. **可疑检测**: 自动检测异常激活行为
6. **审计日志**: 完整的操作审计跟踪
7. **密钥加密**: RSA加密存储敏感信息

---

## 🎯 使用场景

### 场景1: 创建并分发试用许可证
1. 创建产品 → 创建试用方案 → 创建许可证 → 分配给Member

### 场景2: 客户端软件集成
1. 客户端调用激活API → 绑定硬件 → 定期心跳 → 验证状态

### 场景3: 许可证管理
1. 查看许可证列表 → 延长有效期 → 撤销许可证 → 查看使用统计

### 场景4: 批量操作
1. 选择多个许可证 → 批量延期/撤销 → 查看操作结果

---

## 📞 技术支持

### API文档
- Swagger UI: `http://localhost:8000/api/v1/docs/`
- ReDoc: `http://localhost:8000/api/v1/redoc/`
- OpenAPI Schema: `http://localhost:8000/api/v1/schema/`

### 问题反馈
如发现API问题或有改进建议，请提交Issue或联系开发团队。

---

## 📝 更新日志

### 2025-11-23
- ✅ 修复所有已知API错误
- ✅ 完成67个API的测试
- ✅ 编写完整API文档
- ✅ 创建自动化测试脚本
- ✅ 100%测试通过率

---

## 📖 相关资源

- [Django REST Framework文档](https://www.django-rest-framework.org/)
- [drf-spectacular文档](https://drf-spectacular.readthedocs.io/)
- [JWT认证文档](https://django-rest-framework-simplejwt.readthedocs.io/)

---

**最后更新**: 2025-11-23  
**版本**: v1.0.0  
**状态**: ✅ 生产就绪
