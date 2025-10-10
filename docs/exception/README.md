# 异常处理系统文档

## 概述

本目录包含 Lipeaks Backend 项目的统一异常处理系统文档。我们采用**混合方案**来平衡类型安全、灵活性和可维护性。

## 为什么采用混合方案？

在调研和分析了项目现状后，我们发现了以下问题：
- ❌ 缺少统一的业务异常基类
- ❌ 异常类型选择无标准可依
- ❌ 错误码体系不完整
- ❌ Service层和View层职责不清
- ❌ 错误响应格式多样化
- ❌ 异常处理粒度太粗

**混合方案**通过以下方式解决这些问题：
- ✅ 为高频核心错误创建专门的异常类（强类型、IDE友好）
- ✅ 为低频边缘错误使用通用异常类+错误码（灵活、易扩展）
- ✅ 建立清晰的三层异常继承体系（基类层→模块层→具体异常层）
- ✅ 统一的错误响应格式
- ✅ 支持渐进式重构，向后兼容

## 文档导航

### 1. [架构设计](./01_exception_architecture.md)
- 混合方案设计理念
- 异常类继承体系
- 三层架构说明
- 设计原则和最佳实践

### 2. [流程图](./02_exception_flow_diagrams.md)
- 整体异常处理流程图
- 异常类继承体系图
- Service到View层异常处理序列图
- 错误码分配规则图
- 异常使用决策树

### 3. [错误码规范](./03_error_code_specification.md)
- 错误码命名规范
- 错误码分配表
- 各模块错误码范围
- 错误码示例

### 4. [使用指南](./04_exception_usage_guide.md)
- 如何选择异常类型
- Service层抛出异常示例
- View层处理异常示例
- 常见场景代码示例

### 5. [迁移指南](./05_migration_guide.md)
- 现有代码迁移策略
- 各模块迁移优先级
- 迁移前后对比
- 向后兼容性说明

## 快速开始

### 抛出异常（Service层）

**高频核心错误 - 使用专门异常类：**
```python
from common.exceptions import TenantNotFoundException, LicenseExpiredException

# 租户不存在
raise TenantNotFoundException(detail=f'租户ID {tenant_id} 不存在')

# 许可证过期
raise LicenseExpiredException(
    detail=f'许可证 {license_key} 已于 {expired_at} 过期'
)
```

**低频边缘错误 - 使用通用类+错误码：**
```python
from common.exceptions import LicenseException

# 设备指纹不匹配（低频错误）
raise LicenseException(
    error_code='ACTIVATION_DEVICE_MISMATCH',
    detail='设备指纹不匹配，无法激活许可证'
)
```

### 标准错误响应格式

所有异常都会被全局异常处理器转换为统一格式：

```json
{
    "success": false,
    "code": 4101,
    "message": "租户ID 123 不存在",
    "data": null,
    "error_code": "TENANT_NOT_FOUND"
}
```

### 响应字段说明

- `success`: 布尔值，表示请求是否成功
- `code`: 业务错误码（4位数字）
- `message`: 人类可读的错误消息
- `data`: 错误详情数据（通常为null）
- `error_code`: 错误标识符（字符串常量）

## 异常类层次结构

```
DRF APIException
    └── BusinessException (业务异常基类)
            ├── TenantException (租户异常基类, 41xx)
            │       ├── TenantNotFoundException (4101)
            │       ├── TenantInactiveException (4102)
            │       └── ...
            ├── LicenseException (许可证异常基类, 42xx)
            │       ├── LicenseExpiredException (4201)
            │       ├── LicenseNotFoundException (4202)
            │       └── ...
            ├── UserException (用户异常基类, 43xx)
            ├── PointsException (积分异常基类, 44xx)
            └── CMSException (CMS异常基类, 45xx)
```

## 核心原则

### 1. 单一职责
- Service层负责抛出业务异常
- 全局异常处理器负责转换为HTTP响应
- View层不应直接构建错误响应

### 2. 明确分类
- 高频错误（>10次/月）→ 专门异常类
- 低频错误（<10次/月）→ 通用类+错误码
- 核心模块（租户/许可证/用户）→ 优先使用专门类

### 3. 统一格式
- 所有API错误响应保持一致的JSON结构
- 包含业务码、HTTP状态码、错误标识符
- 支持国际化（未来扩展）

### 4. 向后兼容
- 保留现有异常类的导入路径
- 新旧异常可以共存
- 支持渐进式迁移

## 相关资源

- Django REST Framework 异常处理文档: https://www.django-rest-framework.org/api-guide/exceptions/
- 项目异常处理代码: `common/exceptions/`
- 全局异常处理器: `common/exceptions/handler.py`

## 版本历史

- v1.0.0 (2025-01-08): 初始版本，建立混合方案异常处理体系

---

**维护者**: Lipeaks Backend Team  
**最后更新**: 2025-01-08

