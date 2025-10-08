# 异常处理架构设计

## 设计理念

### 混合方案的核心思想

本项目采用**混合方案**来平衡以下几个关键目标：

1. **类型安全** - 核心业务错误使用专门的异常类，提供编译时类型检查
2. **灵活性** - 边缘场景使用通用异常类+错误码，快速扩展
3. **可维护性** - 清晰的层次结构，易于理解和维护
4. **向后兼容** - 支持渐进式重构，不破坏现有代码

### 设计原则

#### 1. 关注点分离（Separation of Concerns）

```
┌─────────────────────────────────────────┐
│  Service/Model 层                        │
│  职责：业务逻辑 + 抛出业务异常           │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  异常类体系                              │
│  职责：定义异常类型和默认属性            │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  全局异常处理器                          │
│  职责：捕获异常 + 转换为HTTP响应         │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  View 层                                 │
│  职责：处理HTTP请求/响应（不处理异常）   │
└──────────────────────────────────────────┘
```

#### 2. 最少惊讶原则（Principle of Least Astonishment）

- 高频错误使用专门类 → 代码清晰，意图明确
- 低频错误使用通用类 → 避免类爆炸，保持简洁

#### 3. 开闭原则（Open-Closed Principle）

- 对扩展开放：通过继承或使用错误码轻松添加新异常
- 对修改封闭：不需要修改全局处理器来支持新异常

## 三层异常架构

### 第一层：基类层（Foundation Layer）

**核心组件：`BusinessException`**

```python
from rest_framework.exceptions import APIException

class BusinessException(APIException):
    """
    业务异常基类
    
    所有业务异常都应继承此类
    """
    # 业务错误码（4位数字）
    business_code = None
    
    # 错误标识符（字符串常量）
    error_code = 'BUSINESS_ERROR'
    
    # HTTP状态码（默认400）
    status_code = 400
    
    def __init__(self, detail=None, code=None, **extra):
        """
        初始化业务异常
        
        Args:
            detail: 错误详情消息
            code: 错误代码（可选）
            **extra: 额外的上下文信息
        """
        super().__init__(detail, code)
        self.extra = extra or {}
```

**职责：**
- 作为所有业务异常的根基
- 提供统一的接口和属性
- 包含额外的上下文信息（extra字段）

### 第二层：模块层（Module Layer）

**按业务模块划分的异常基类**

```python
# 租户模块异常基类
class TenantException(BusinessException):
    """租户相关异常基类"""
    business_code = 4100
    error_code = 'TENANT_ERROR'

# 许可证模块异常基类
class LicenseException(BusinessException):
    """许可证相关异常基类"""
    business_code = 4200
    error_code = 'LICENSE_ERROR'

# 用户模块异常基类
class UserException(BusinessException):
    """用户相关异常基类"""
    business_code = 4300
    error_code = 'USER_ERROR'

# 积分模块异常基类
class PointsException(BusinessException):
    """积分相关异常基类"""
    business_code = 4400
    error_code = 'POINTS_ERROR'

# CMS模块异常基类
class CMSException(BusinessException):
    """CMS相关异常基类"""
    business_code = 4500
    error_code = 'CMS_ERROR'
```

**职责：**
- 为每个业务模块提供异常基类
- 统一管理模块级别的错误码范围
- 支持两种使用方式：
  1. 继承创建具体异常类（高频错误）
  2. 直接使用并传入error_code（低频错误）

### 第三层：具体异常层（Concrete Layer）

**为高频错误创建的专门异常类**

```python
# 租户模块具体异常
class TenantNotFoundException(TenantException):
    """租户不存在"""
    status_code = 404
    business_code = 4101
    error_code = 'TENANT_NOT_FOUND'
    default_detail = '租户不存在'

class TenantInactiveException(TenantException):
    """租户未激活"""
    status_code = 403
    business_code = 4102
    error_code = 'TENANT_INACTIVE'
    default_detail = '租户未激活或已被禁用'

# 许可证模块具体异常
class LicenseExpiredException(LicenseException):
    """许可证已过期"""
    status_code = 400
    business_code = 4201
    error_code = 'LICENSE_EXPIRED'
    default_detail = '许可证已过期'

class LicenseNotFoundException(LicenseException):
    """许可证不存在"""
    status_code = 404
    business_code = 4202
    error_code = 'LICENSE_NOT_FOUND'
    default_detail = '许可证不存在'
```

**何时创建具体异常类？**

✅ **应该创建专门类的情况：**
- 高频错误（预计每月出现 >10 次）
- 核心业务流程的关键错误
- 需要特殊处理逻辑的错误
- 需要清晰语义的错误

❌ **应该使用通用类+错误码的情况：**
- 低频错误（预计每月出现 <10 次）
- 边缘场景的错误
- 临时性的错误
- 业务规则频繁变化的错误

## 完整继承体系图

```
DRF APIException (Django REST Framework)
    │
    └── BusinessException (业务异常基类)
            │
            ├── TenantException (租户异常基类)
            │       ├── TenantNotFoundException (具体异常)
            │       ├── TenantInactiveException (具体异常)
            │       ├── TenantQuotaExceededException (具体异常)
            │       └── TenantAccessDeniedException (具体异常)
            │
            ├── LicenseException (许可证异常基类)
            │       ├── LicenseExpiredException (具体异常)
            │       ├── LicenseNotFoundException (具体异常)
            │       ├── LicenseQuotaExceededException (具体异常)
            │       ├── LicenseRevokedException (具体异常)
            │       └── LicenseActivationFailedException (具体异常)
            │
            ├── UserException (用户异常基类)
            │       ├── UserNotFoundException (具体异常)
            │       ├── UserInactiveException (具体异常)
            │       └── UserPermissionDeniedException (具体异常)
            │
            ├── PointsException (积分异常基类)
            │       ├── PointsInsufficientException (具体异常)
            │       └── PointsExpiredException (具体异常)
            │
            └── CMSException (CMS异常基类)
                    ├── ArticleNotFoundException (具体异常)
                    └── CategoryNotFoundException (具体异常)
```

## 异常属性说明

### 核心属性

| 属性 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `status_code` | int | HTTP状态码 | 404, 400, 403 |
| `business_code` | int | 业务错误码（4位） | 4101, 4201 |
| `error_code` | str | 错误标识符（字符串常量） | 'TENANT_NOT_FOUND' |
| `default_detail` | str | 默认错误消息 | '租户不存在' |
| `detail` | str | 实际错误消息（实例化时传入） | '租户ID 123 不存在' |
| `extra` | dict | 额外上下文信息 | {'tenant_id': 123} |

### 属性优先级

1. **实例化时传入的 `detail`** - 最高优先级
2. **类定义的 `default_detail`** - 次优先级
3. **父类的默认值** - 最低优先级

```python
# 示例
class TenantNotFoundException(TenantException):
    default_detail = '租户不存在'  # 类级别默认值

# 使用默认消息
raise TenantNotFoundException()  
# → detail = '租户不存在'

# 使用自定义消息
raise TenantNotFoundException(detail=f'租户ID {tenant_id} 不存在')
# → detail = '租户ID 123 不存在'
```

## 错误码分配策略

### 错误码结构

```
业务错误码：4XXX（4位数字）
│
├─ 第1位：错误类别
│   └─ 4 = 客户端错误
│   └─ 5 = 服务端错误
│
├─ 第2位：业务模块
│   ├─ 40XX = 认证授权
│   ├─ 41XX = 租户相关
│   ├─ 42XX = 许可证相关
│   ├─ 43XX = 用户相关
│   ├─ 44XX = 积分相关
│   └─ 45XX = CMS相关
│
└─ 第3-4位：具体错误
    └─ 00 = 模块通用错误
    └─ 01-99 = 具体错误类型
```

### 模块错误码范围

| 模块 | 错误码范围 | 示例 |
|------|-----------|------|
| 认证授权 | 4000-4099 | 4001: 未认证, 4003: 无权限 |
| 租户 | 4100-4199 | 4101: 不存在, 4102: 未激活 |
| 许可证 | 4200-4299 | 4201: 已过期, 4202: 不存在 |
| 用户 | 4300-4399 | 4301: 不存在, 4302: 未激活 |
| 积分 | 4400-4499 | 4401: 余额不足, 4402: 已过期 |
| CMS | 4500-4599 | 4501: 文章不存在 |
| 订单 | 4600-4699 | 4601: 订单不存在 |
| 服务器错误 | 5000-5999 | 5000: 通用错误, 5001: 数据库错误 |

## 最佳实践

### 1. Service层抛出异常

```python
# ✅ 好的做法
class TenantService:
    def get_tenant(self, tenant_id):
        try:
            tenant = Tenant.objects.get(id=tenant_id, is_deleted=False)
        except Tenant.DoesNotExist:
            raise TenantNotFoundException(
                detail=f'租户ID {tenant_id} 不存在',
                tenant_id=tenant_id  # 额外上下文
            )
        
        if tenant.status != 'active':
            raise TenantInactiveException(
                detail=f'租户 {tenant.name} 已被禁用',
                tenant_id=tenant_id,
                status=tenant.status
            )
        
        return tenant

# ❌ 不好的做法
class TenantService:
    def get_tenant(self, tenant_id):
        tenant = Tenant.objects.get(id=tenant_id)  # 让Django异常传播
        return tenant  # 没有业务验证
```

### 2. View层不处理异常

```python
# ✅ 好的做法
class TenantDetailView(APIView):
    def get(self, request, tenant_id):
        # 让Service层抛出异常，由全局处理器处理
        tenant = tenant_service.get_tenant(tenant_id)
        serializer = TenantSerializer(tenant)
        return Response(serializer.data)

# ❌ 不好的做法
class TenantDetailView(APIView):
    def get(self, request, tenant_id):
        try:
            tenant = tenant_service.get_tenant(tenant_id)
            serializer = TenantSerializer(tenant)
            return Response(serializer.data)
        except TenantNotFoundException as e:
            # 不要在View层手动处理业务异常
            return Response({
                'error': str(e)
            }, status=404)
```

### 3. 选择异常类型

```python
# ✅ 高频核心错误 - 使用专门类
if not tenant:
    raise TenantNotFoundException(detail=f'租户 {tenant_id} 不存在')

# ✅ 低频边缘错误 - 使用通用类+错误码
if device_fingerprint_mismatch:
    raise LicenseException(
        error_code='ACTIVATION_DEVICE_MISMATCH',
        detail='设备指纹不匹配，无法激活许可证',
        expected=expected_fingerprint,
        actual=actual_fingerprint
    )
```

### 4. 提供有用的错误信息

```python
# ✅ 好的做法 - 包含上下文信息
raise LicenseExpiredException(
    detail=f'许可证 {license_key} 已于 {expired_at.strftime("%Y-%m-%d")} 过期',
    license_id=license.id,
    license_key=license_key,
    expired_at=expired_at.isoformat()
)

# ❌ 不好的做法 - 信息不足
raise LicenseExpiredException()  # 使用默认消息，缺少上下文
```

## 与现有代码的兼容性

### 保留旧异常类

现有的异常类（如 `TenantNotFound`, `QuotaExceeded`）将继续可用，但会被标记为废弃：

```python
# common/exceptions/__init__.py

# 新的异常类（推荐使用）
from .tenant import TenantNotFoundException, TenantInactiveException
from .license import LicenseExpiredException

# 旧的异常类（向后兼容，但已废弃）
TenantNotFound = TenantNotFoundException  # 别名
TenantInactive = TenantInactiveException  # 别名
```

### 渐进式迁移

1. **阶段1**：新代码使用新异常类
2. **阶段2**：重构核心模块（租户、许可证、用户）
3. **阶段3**：逐步迁移其他模块
4. **阶段4**：移除旧异常类（在主版本升级时）

## 总结

混合方案通过三层架构实现了：
- ✅ **类型安全**：核心错误有专门的异常类
- ✅ **灵活扩展**：边缘错误使用通用类+错误码
- ✅ **清晰语义**：代码意图明确，易于理解
- ✅ **易于维护**：层次清晰，职责分明
- ✅ **向后兼容**：支持渐进式迁移

这套架构既满足了大型项目对类型安全和可维护性的要求，又保持了足够的灵活性来应对快速变化的业务需求。

