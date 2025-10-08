# 许可证管理系统 API 文档集合

## 📋 文档概述

本文件夹包含了许可证管理系统的完整API文档，专门为前端开发人员设计，涵盖了API集成、表单处理、测试调试和安全配置等各个方面。

## 📚 文档列表

### 🎯 许可证更新API文档

#### 1. [license_update_api_documentation.md](./license_update_api_documentation.md)
**核心API集成文档**
- **适用对象**: 前端开发人员
- **主要内容**:
  - PUT `/api/v1/licenses/admin/licenses/{id}/` API完整规范
  - 请求参数和响应格式详细说明
  - JavaScript/TypeScript集成示例
  - React Hook使用示例
  - 错误处理最佳实践
- **使用场景**: 需要集成许可证更新功能的前端项目

#### 2. [license_update_form_integration_guide.md](./license_update_form_integration_guide.md)
**前端表单集成指南**
- **适用对象**: 前端UI/UX开发人员
- **主要内容**:
  - 完整的表单HTML结构和CSS样式
  - 高级JavaScript表单处理类
  - 实时数据验证和自动保存功能
  - 响应式设计和可访问性支持
  - 移动端优化和键盘导航
- **使用场景**: 需要构建许可证更新界面的项目

#### 3. [license_update_api_testing_guide.md](./license_update_api_testing_guide.md)
**API测试调试指南**
- **适用对象**: 前端开发和测试人员
- **主要内容**:
  - Postman测试集合和cURL命令
  - Jest单元测试和React Testing Library示例
  - 性能测试脚本和监控方案
  - 浏览器调试技巧和问题诊断工具
  - 生产环境监控配置
- **使用场景**: API测试、性能优化和问题排查

### 🔒 安全配置文档

#### 4. [security_threshold_configuration_guide.md](./security_threshold_configuration_guide.md)
**安全阈值配置指南**
- **适用对象**: 系统管理员和DevOps工程师
- **主要内容**:
  - 许可证激活安全机制详细说明
  - 环境变量配置方法和最佳实践
  - 不同环境的推荐配置方案
  - 监控和日志管理
  - 故障排除和性能优化
- **使用场景**: 部署和运维许可证系统

#### 5. [environment_variables_reference.md](./environment_variables_reference.md)
**环境变量快速参考**
- **适用对象**: 系统管理员
- **主要内容**:
  - 所有安全阈值环境变量的完整列表
  - 场景化配置模板
  - 动态配置方法和注意事项
  - 配置调试技巧
- **使用场景**: 快速配置和调试环境变量

#### 6. [quick_configuration_examples.md](./quick_configuration_examples.md)
**快速配置示例**
- **适用对象**: 系统管理员和开发人员
- **主要内容**:
  - 一键复制的配置命令
  - Docker环境配置示例
  - 自动化配置脚本
  - 故障排除配置
  - 性能优化建议
- **使用场景**: 快速部署和环境配置

## 🚀 快速开始

### 前端开发人员

1. **首次接触**: 从 [license_update_api_documentation.md](./license_update_api_documentation.md) 开始
2. **构建界面**: 参考 [license_update_form_integration_guide.md](./license_update_form_integration_guide.md)
3. **测试调试**: 使用 [license_update_api_testing_guide.md](./license_update_api_testing_guide.md)

### 系统管理员

1. **安全配置**: 阅读 [security_threshold_configuration_guide.md](./security_threshold_configuration_guide.md)
2. **快速部署**: 使用 [quick_configuration_examples.md](./quick_configuration_examples.md)
3. **问题排查**: 参考 [environment_variables_reference.md](./environment_variables_reference.md)

## 📖 使用建议

### 按角色阅读

| 角色 | 必读文档 | 推荐文档 |
|------|----------|----------|
| **前端开发** | 1, 2 | 3 |
| **全栈开发** | 1, 2, 3 | 4, 5 |
| **系统管理员** | 4, 5, 6 | 3 |
| **DevOps工程师** | 4, 5, 6 | 1, 3 |
| **测试工程师** | 3 | 1, 2 |

### 按任务阅读

| 任务 | 相关文档 |
|------|----------|
| **集成许可证更新API** | 文档1 → 文档2 → 文档3 |
| **构建管理后台界面** | 文档2 → 文档1 → 文档3 |
| **部署生产环境** | 文档4 → 文档6 → 文档5 |
| **性能优化** | 文档3 → 文档4 → 文档6 |
| **故障排查** | 文档3 → 文档5 → 文档4 |

## 🔧 技术栈要求

### 前端技术栈

- **必需**:
  - JavaScript ES6+
  - Fetch API 或 Axios
  - HTML5 + CSS3
  
- **推荐**:
  - React 16.8+ (Hooks)
  - TypeScript 4.0+
  - Jest + React Testing Library
  - Postman 或类似API测试工具

### 后端环境

- **Python 3.8+**
- **Django 4.0+**
- **Django REST Framework 3.14+**
- **PostgreSQL 12+** (推荐)

## 📋 API概览

### 核心端点

```bash
# 许可证更新 (本文档集合的重点)
PUT /api/v1/licenses/admin/licenses/{id}/
PATCH /api/v1/licenses/admin/licenses/{id}/

# 相关端点
GET /api/v1/licenses/admin/licenses/{id}/          # 获取详情
GET /api/v1/licenses/admin/licenses/               # 获取列表
POST /api/v1/licenses/admin/licenses/              # 创建许可证
DELETE /api/v1/licenses/admin/licenses/{id}/       # 删除许可证
```

### 认证方式

```javascript
// JWT Token认证
headers: {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
    'Content-Type': 'application/json',
    'X-Tenant-ID': '1' // 多租户环境
}
```

## 🎯 常见使用场景

### 场景1: 基础许可证更新

```javascript
// 最简单的更新示例
const updateLicense = async (licenseId, newData) => {
    const response = await fetch(`/api/v1/licenses/admin/licenses/${licenseId}/`, {
        method: 'PUT',
        headers: {
            'Authorization': `Bearer ${getAuthToken()}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(newData)
    });
    
    return response.json();
};
```

### 场景2: 表单驱动的更新

```javascript
// 完整的表单处理
import { LicenseUpdateForm } from './LicenseUpdateForm';

const MyComponent = () => {
    return (
        <LicenseUpdateForm 
            licenseId={123}
            onSuccess={(updatedLicense) => {
                console.log('更新成功:', updatedLicense);
            }}
        />
    );
};
```

### 场景3: 批量更新

```javascript
// 批量更新多个许可证
const batchUpdateLicenses = async (updates) => {
    const results = await Promise.all(
        updates.map(({ id, data }) => 
            updateLicense(id, data)
        )
    );
    return results;
};
```

## ⚠️ 重要注意事项

### 权限要求
- **超级管理员**: 可更新所有租户的许可证
- **租户管理员**: 只能更新自己租户的许可证
- **普通用户**: 无权限访问更新接口

### 数据一致性
- 更新 `max_activations` 时不能小于 `current_activations`
- 更新 `expires_at` 时不能早于当前时间
- 产品和方案必须属于同一租户

### 安全考虑
- 所有更新操作都会记录安全审计日志
- 频繁的更新操作可能触发安全限制
- 敏感信息更新需要额外验证

## 🆘 获取帮助

### 问题排查步骤
1. **检查认证**: 确认JWT Token有效性
2. **验证权限**: 确认用户有足够权限
3. **检查参数**: 使用文档中的验证方法
4. **查看日志**: 检查后端安全审计日志
5. **网络诊断**: 使用文档中的诊断工具

### 调试工具
```javascript
// 启用调试模式
window.licenseDebugger.enableVerboseLogging();

// 运行诊断
window.diagnoseLicenseUpdate(formData);

// 模拟错误场景
window.licenseDebugger.simulateApiError('400');
```

### 性能监控
```javascript
// 启用性能监控
const monitor = new LicenseUpdatePerformanceMonitor();
monitor.startMonitoring();

// 包装API调用
const monitoredUpdate = monitor.wrapApiCall(updateLicense, 'license_update');
```

## 📊 文档统计

| 文档 | 页数估算 | 代码示例 | 适用场景 |
|------|----------|----------|----------|
| API文档 | ~25页 | 50+ | API集成 |
| 表单指南 | ~30页 | 40+ | UI开发 |
| 测试指南 | ~20页 | 60+ | 测试调试 |
| 安全配置 | ~15页 | 30+ | 系统管理 |
| 环境变量 | ~10页 | 20+ | 配置管理 |
| 快速配置 | ~12页 | 25+ | 部署运维 |

## 🔄 文档更新

- **版本**: v1.0
- **创建日期**: 2024-09-30
- **最后更新**: 2024-09-30
- **维护者**: 开发团队

### 更新记录
- **v1.0** (2024-09-30): 初始版本，包含完整的API文档集合

---

**开始您的集成之旅吧！🚀**

选择适合您角色的文档，按照示例代码快速上手，遇到问题时使用调试工具快速定位。我们的文档经过精心设计，确保您能够顺利完成许可证更新功能的集成。
