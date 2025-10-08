# 许可证管理API文档索引

**文档类型**: 管理员端许可证管理  
**目标读者**: 前端开发人员（管理后台）  
**最后更新**: 2025-10-06

---

## 📚 文档导航

### 🔥 新增管理员API

| 序号 | 文档 | API端点 | 说明 | 重要程度 |
|------|------|---------|------|---------|
| 1 | **batch_operation_api.md** | POST /admin/licenses/batch_operation/ | 批量操作许可证 | ⭐⭐⭐⭐⭐ |
| 2 | **batch_operation_status.md** | - | 批量操作实施状态说明 | ⭐⭐⭐⭐ |

### 📖 Member许可证API（已有）

| 序号 | 文档 | API端点 | 说明 |
|------|------|---------|------|
| 3 | **available_products_api.md** | GET /member/available-products/ | Member获取产品列表 |
| 4 | **apply_license_api.md** | POST /member/apply/ | Member申请试用许可证 |
| 5 | **my_licenses_api.md** | GET /member/my-licenses/ | Member查看许可证 |

---

## 🎯 根据功能模块选择

### 管理员后台开发

如果你在开发**管理员后台**的许可证管理功能：

**推荐阅读顺序**：
1. 📕 **batch_operation_api.md** - 批量操作API详解
2. 📔 **batch_operation_status.md** - 了解功能实施状态
3. 📗 **license_common.md** - 理解许可证数据模型

**核心功能**：
- 许可证列表展示（多选）
- 批量撤销许可证
- 批量延长有效期
- 操作结果展示

### Member前端开发

如果你在开发**Member用户**的许可证申请功能：

**推荐阅读顺序**：
1. 📘 **README.md** - 快速开始
2. 📗 **license_common.md** - 业务规则
3. 📙 **apply_license_api.md** - 申请功能

---

## 🔍 API功能对比

### 管理员端 vs Member端

| 功能 | 管理员端 | Member端 | 说明 |
|------|---------|----------|------|
| **查看许可证** | 所有/本租户 | 仅自己的 | 权限范围不同 |
| **创建许可证** | ✅ 支持 | ❌ 不支持 | 管理员专用 |
| **撤销许可证** | ✅ 支持 | ❌ 不支持 | 管理员专用 |
| **延长许可证** | ✅ 支持 | ❌ 不支持 | 管理员专用 |
| **申请试用** | ❌ 不支持 | ✅ 支持 | Member专用 |
| **批量操作** | ✅ 支持 | ❌ 不支持 | 管理员专用 |

---

## 📊 API端点汇总

### 管理员端API

```
基础路径: /api/v1/licenses/admin/

GET    /licenses/                     # 许可证列表
POST   /licenses/                     # 创建许可证
GET    /licenses/{id}/                # 许可证详情
PUT    /licenses/{id}/                # 更新许可证
DELETE /licenses/{id}/                # 删除许可证
POST   /licenses/{id}/revoke/         # 单个撤销
POST   /licenses/batch_operation/     # 批量操作 🔥
```

### Member端API

```
基础路径: /api/v1/licenses/member/

GET    /available-products/           # 可申请产品
POST   /apply/                        # 申请试用
GET    /my-licenses/                  # 我的许可证
```

---

## 🧪 测试环境

### 测试数据准备

建议准备以下测试数据：

```javascript
// 测试用许可证
const testLicenses = [
  { id: 101, status: 'generated', customer_name: 'Test User 1' },
  { id: 102, status: 'activated', customer_name: 'Test User 2' },
  { id: 103, status: 'suspended', customer_name: 'Test User 3' },
];

// 测试场景
const testScenarios = [
  {
    name: '批量撤销',
    licenseIds: [101, 102],
    operation: 'revoke',
    expectedSuccess: true
  },
  {
    name: '批量延期',
    licenseIds: [102],
    operation: 'extend',
    parameters: { days: 30 },
    expectedSuccess: true
  }
];
```

### Swagger测试

访问 `http://localhost:8000/api/v1/docs/` 可以在线测试批量操作API。

---

## 📞 技术支持

### 在线文档

- **Swagger**: http://localhost:8000/api/v1/docs/
- **ReDoc**: http://localhost:8000/api/v1/redoc/

### 代码位置

- **后端代码**: `licenses/views/admin_views.py` (第935行开始)
- **序列化器**: `licenses/serializers.py` (第567行开始)
- **URL配置**: `licenses/urls.py`

### 相关模型

- **License**: 许可证主模型
- **LicenseAssignment**: 许可证分配关系
- **SecurityAuditLog**: 操作审计日志

---

## ✨ 开发建议

### 开发顺序

1. **第一步**：实现许可证列表的多选功能
2. **第二步**：实现批量撤销功能（相对简单）
3. **第三步**：实现批量延期功能（需要参数输入）
4. **第四步**：完善错误处理和结果展示
5. **第五步**：等待后端实现suspend/activate后添加

### UI建议

- 使用 Element Plus 的 Table 组件多选功能
- 批量操作面板固定在列表上方
- 危险操作（如撤销）使用红色主题
- 操作结果使用 Dialog 或 Drawer 展示

---

**文档完成，可以开始前端开发！** 🚀
