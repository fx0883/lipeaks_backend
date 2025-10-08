# 迁移指南

## 概述

本指南帮助您将现有代码迁移到新的统一异常处理系统。迁移采用渐进式策略，不会破坏现有功能。

## 迁移策略

### 总体原则

1. **向后兼容** - 保留现有异常类的导入路径
2. **渐进迁移** - 按模块逐步迁移，不要求一次性完成
3. **新代码优先** - 所有新代码使用新异常系统
4. **重构核心** - 优先重构核心模块（租户、许可证、用户）
5. **测试保障** - 每次迁移后运行测试确保功能正常

### 迁移阶段

```
阶段1: 基础设施建立（已完成）
├─ 创建异常类体系
├─ 实现全局异常处理器
└─ 编写文档

阶段2: 新代码采用（立即开始）
├─ 所有新功能使用新异常系统
└─ Code Review 确保合规

阶段3: 核心模块迁移（2-4周）
├─ 租户模块
├─ 许可证模块
└─ 用户模块

阶段4: 其他模块迁移（持续）
├─ CMS模块
├─ 积分模块
├─ 订单模块
└─ 其他模块

阶段5: 清理工作（主版本升级时）
├─ 移除旧异常类
├─ 更新所有文档
└─ 发布迁移完成公告
```

## 兼容性映射

### 旧异常类 → 新异常类

为了向后兼容，我们在 `common/exceptions/__init__.py` 中创建别名：

```python
# common/exceptions/__init__.py

# === 新的异常类（推荐使用） ===
from .base import BusinessException
from .tenant import (
    TenantException,
    TenantNotFoundException,
    TenantInactiveException,
    TenantQuotaExceededException,
    TenantAccessDeniedException,
)
from .license import (
    LicenseException,
    LicenseExpiredException,
    LicenseNotFoundException,
    LicenseQuotaExceededException,
)
# ... 更多导入

# === 旧异常类别名（向后兼容，已废弃） ===
# ⚠️ Deprecated: Use TenantNotFoundException instead
TenantNotFound = TenantNotFoundException

# ⚠️ Deprecated: Use TenantInactiveException instead
TenantInactive = TenantInactiveException

# ⚠️ Deprecated: Use LicenseQuotaExceededException instead
QuotaExceeded = LicenseQuotaExceededException

__all__ = [
    # 新异常类
    'BusinessException',
    'TenantException',
    'TenantNotFoundException',
    'LicenseException',
    'LicenseExpiredException',
    # ... 更多
    
    # 旧异常类（已废弃）
    'TenantNotFound',
    'TenantInactive',
    'QuotaExceeded',
]
```

### 完整映射表

| 旧异常类 | 新异常类 | 状态 | 移除版本 |
|---------|---------|------|---------|
| `TenantNotFound` | `TenantNotFoundException` | Deprecated | v2.0 |
| `TenantInactive` | `TenantInactiveException` | Deprecated | v2.0 |
| `QuotaExceeded` | `LicenseQuotaExceededException` 或 `TenantQuotaExceededException` | Deprecated | v2.0 |

## 迁移步骤

### 步骤1：理解现有代码

在迁移前，先识别现有代码中的异常使用模式：

```bash
# 查找所有 raise 语句
grep -r "raise" licenses/ users/ tenants/ cms/ points/

# 查找 ValueError 和 ValidationError
grep -r "ValueError\|ValidationError" licenses/ users/

# 查找 try-except 块
grep -r "except.*:" licenses/ users/
```

### 步骤2：识别高频错误

分析日志或错误报告，识别高频错误：

```python
# 示例：分析许可证模块的错误
# 高频：许可证过期、许可证不存在、配额超限
# 低频：设备指纹不匹配、激活失败
```

### 步骤3：迁移Service层

#### 迁移前

```python
# licenses/services/member_license_service.py (旧代码)

class MemberLicenseApplicationService:
    def _validate_product(self, product_id):
        try:
            product = SoftwareProduct.objects.get(
                id=product_id,
                status='active',
                is_deleted=False
            )
        except SoftwareProduct.DoesNotExist:
            raise ValueError("产品不存在或不可用")  # ❌ 使用Python原生异常
        
        return product
    
    def _check_application_eligibility(self, member, product):
        existing = LicenseAssignment.objects.filter(
            member=member,
            license__product=product,
            status__in=['active', 'pending']
        ).exists()
        
        if existing:
            raise ValueError("您已经拥有该产品的有效许可证")  # ❌
        
        if not member.is_active:
            raise ValueError("用户账户已被禁用，无法申请许可证")  # ❌
```

#### 迁移后

```python
# licenses/services/member_license_service.py (新代码)

from common.exceptions import (
    LicenseException,  # 通用类
    UserInactiveException,  # 专门类
)

class MemberLicenseApplicationService:
    def _validate_product(self, product_id):
        try:
            product = SoftwareProduct.objects.get(
                id=product_id,
                status='active',
                is_deleted=False
            )
        except SoftwareProduct.DoesNotExist:
            # ✅ 低频错误，使用通用类+错误码
            raise LicenseException(
                error_code='PRODUCT_NOT_FOUND',
                detail=f'产品ID {product_id} 不存在或不可用',
                product_id=product_id
            )
        
        return product
    
    def _check_application_eligibility(self, member, product):
        existing = LicenseAssignment.objects.filter(
            member=member,
            license__product=product,
            status__in=['active', 'pending']
        ).exists()
        
        if existing:
            # ✅ 低频错误，使用通用类+错误码
            raise LicenseException(
                error_code='LICENSE_ALREADY_ASSIGNED',
                detail='您已经拥有该产品的有效许可证',
                member_id=member.id,
                product_id=product.id
            )
        
        if not member.is_active:
            # ✅ 高频错误，使用专门类
            raise UserInactiveException(
                detail=f'用户 {member.username} 账户已被禁用',
                user_id=member.id,
                username=member.username
            )
```

### 步骤4：迁移View层

#### 迁移前

```python
# licenses/views/member_views.py (旧代码)

@api_view(['POST'])
def apply_trial_license(request):
    try:
        result = application_service.apply_trial_license(...)
        return Response(result, status=201)
    except ValueError as e:  # ❌ 捕获原生异常
        return Response({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:  # ❌ 宽泛捕获
        return Response({
            'success': False,
            'error': '申请处理失败，请稍后重试'
        }, status=500)
```

#### 迁移后

```python
# licenses/views/member_views.py (新代码)

from common.exceptions import LicenseException, UserInactiveException

@api_view(['POST'])
def apply_trial_license(request):
    # ✅ 让异常传播到全局处理器
    # Service层会抛出 LicenseException 或 UserInactiveException
    # 全局处理器会自动转换为标准响应格式
    result = application_service.apply_trial_license(...)
    return Response(result, status=201)
```

### 步骤5：更新测试

#### 迁移前

```python
# tests/test_license_service.py (旧测试)

def test_product_not_found():
    with pytest.raises(ValueError) as exc_info:  # ❌ 测试原生异常
        service._validate_product(999)
    
    assert str(exc_info.value) == "产品不存在或不可用"
```

#### 迁移后

```python
# tests/test_license_service.py (新测试)

from common.exceptions import LicenseException

def test_product_not_found():
    with pytest.raises(LicenseException) as exc_info:  # ✅ 测试新异常
        service._validate_product(999)
    
    assert exc_info.value.error_code == 'PRODUCT_NOT_FOUND'
    assert exc_info.value.business_code == 4200
    assert '产品ID 999 不存在' in str(exc_info.value.detail)
```

## 模块迁移指南

### 租户模块迁移

**优先级：高** ⭐⭐⭐

**涉及文件：**
- `tenants/views.py`
- `tenants/serializers.py`
- `common/services/tenant_resolver.py`
- `common/middleware/tenant_middleware.py`

**迁移要点：**

```python
# 旧代码
raise ValidationError({"detail": f"无效的租户ID: {tenant_id}"})

# 新代码
raise TenantException(
    error_code='INVALID_TENANT_ID',
    detail=f'无效的租户ID格式: {tenant_id}',
    tenant_id=tenant_id
)
```

### 许可证模块迁移

**优先级：高** ⭐⭐⭐

**涉及文件：**
- `licenses/services/member_license_service.py`
- `licenses/views/member_views.py`
- `licenses/models.py`

**迁移要点：**

```python
# 旧代码 - ValueError
raise ValueError("许可证已过期")

# 新代码 - 专门异常类
raise LicenseExpiredException(
    detail=f'许可证已于 {expired_at.strftime("%Y-%m-%d")} 过期',
    license_id=license.id,
    expired_at=expired_at.isoformat()
)
```

### 用户模块迁移

**优先级：高** ⭐⭐⭐

**涉及文件：**
- `users/views/`
- `users/models.py`
- `common/permissions.py`

**迁移要点：**

```python
# 旧代码
raise PermissionDenied("无权限更改其他租户的用户角色")

# 新代码
raise UserPermissionDeniedException(
    detail='无权限更改其他租户的用户角色',
    user_id=user.id,
    target_tenant_id=target_user.tenant_id
)
```

### CMS模块迁移

**优先级：中** ⭐⭐

**涉及文件：**
- `cms/views.py`
- `cms/models.py`

**迁移要点：**

```python
# 旧代码
raise ValidationError({"detail": "未提供租户ID，无法访问CMS资源"})

# 新代码
raise CMSException(
    error_code='TENANT_ID_REQUIRED',
    detail='未提供租户ID，无法访问CMS资源'
)
```

### 积分模块迁移

**优先级：中** ⭐⭐

**涉及文件：**
- `points/services/points_engine.py`
- `points/models.py`

**迁移要点：**

```python
# 旧代码
raise ValidationError("积分余额不足")

# 新代码
raise PointsInsufficientException(
    detail=f'积分余额不足，当前: {available}，需要: {required}',
    available=available,
    required=required,
    user_id=user.id
)
```

## 迁移检查清单

### 代码审查清单

迁移完成后，检查以下项目：

#### Service层
- [ ] 不再使用 `ValueError`、`TypeError` 等Python原生异常
- [ ] 高频错误使用专门异常类
- [ ] 低频错误使用通用类+错误码
- [ ] 所有异常包含丰富的上下文信息（extra参数）
- [ ] 错误消息清晰易懂，不暴露敏感信息

#### View层
- [ ] 移除了所有 `try-except` 业务异常捕获
- [ ] 使用 `serializer.is_valid(raise_exception=True)`
- [ ] 不再手动构建错误响应

#### 测试
- [ ] 更新了所有异常相关的测试
- [ ] 测试验证新的错误码和错误标识符
- [ ] 所有测试通过

#### 文档
- [ ] 更新了API文档（如果有）
- [ ] 更新了团队内部文档

### 功能测试清单

- [ ] 所有API端点正常工作
- [ ] 错误响应格式正确（包含success、code、message、data、error_code）
- [ ] 错误日志正确记录
- [ ] HTTP状态码正确
- [ ] 业务错误码正确

## 常见问题

### Q1: 现有代码什么时候必须迁移？

**A**: 立即迁移不是强制的。采用渐进式策略：
- **新代码**：立即使用新异常系统
- **修改现有代码时**：顺便迁移
- **核心模块**：在2-4周内迁移
- **其他模块**：持续迁移，无固定时间表

### Q2: 旧异常类什么时候会被移除？

**A**: 在下一个主版本（v2.0）升级时移除。在此之前，旧异常类会作为别名继续可用，不会影响现有功能。

### Q3: 如何处理第三方库的异常？

**A**: 在边界处转换为我们的业务异常：

```python
import requests
from common.exceptions import LicenseException

try:
    response = requests.get(external_api_url)
    response.raise_for_status()
except requests.RequestException as e:
    raise LicenseException(
        error_code='EXTERNAL_SERVICE_ERROR',
        detail='许可证验证服务调用失败'
    ) from e  # 保留异常链
```

### Q4: 迁移会破坏现有API吗？

**A**: 不会。全局异常处理器会将所有异常转换为统一的JSON格式。即使Service层抛出的异常类型改变，API响应格式也保持一致。

### Q5: 是否需要一次性迁移整个模块？

**A**: 不需要。可以在同一个模块中混用新旧异常类。新代码使用新异常，旧代码保持不变，逐步迁移即可。

## 迁移示例

### 完整示例：许可证服务迁移

#### 迁移前（旧代码）

```python
# licenses/services/member_license_service.py

class MemberLicenseApplicationService:
    def apply_trial_license(self, member, product_id, plan_id=None):
        # 验证产品
        try:
            product = SoftwareProduct.objects.get(id=product_id)
        except SoftwareProduct.DoesNotExist:
            raise ValueError("产品不存在或不可用")
        
        # 检查重复申请
        if LicenseAssignment.objects.filter(
            member=member,
            license__product=product,
            status='active'
        ).exists():
            raise ValueError("您已经拥有该产品的有效许可证")
        
        # 检查配额
        trial_count = self._get_user_trial_count(member)
        if trial_count >= 1:
            raise ValueError("您的试用许可证数量已达上限（1个）")
        
        # 创建许可证
        license = self._create_trial_license(product, plan_id)
        return license
```

#### 迁移后（新代码）

```python
# licenses/services/member_license_service.py

from common.exceptions import (
    LicenseException,
    LicenseQuotaExceededException,
)

class MemberLicenseApplicationService:
    def apply_trial_license(self, member, product_id, plan_id=None):
        # 验证产品
        try:
            product = SoftwareProduct.objects.get(
                id=product_id,
                status='active',
                is_deleted=False
            )
        except SoftwareProduct.DoesNotExist:
            # 低频错误，使用通用类+错误码
            raise LicenseException(
                error_code='PRODUCT_NOT_FOUND',
                detail=f'产品ID {product_id} 不存在或不可用',
                product_id=product_id
            )
        
        # 检查重复申请
        existing = LicenseAssignment.objects.filter(
            member=member,
            license__product=product,
            status__in=['active', 'pending']
        ).exists()
        
        if existing:
            # 低频错误，使用通用类+错误码
            raise LicenseException(
                error_code='LICENSE_ALREADY_ASSIGNED',
                detail='您已经拥有该产品的有效许可证',
                member_id=member.id,
                product_id=product.id
            )
        
        # 检查配额
        trial_count = self._get_user_trial_count(member)
        max_trial_licenses = getattr(member, 'max_trial_licenses', 1)
        
        if trial_count >= max_trial_licenses:
            # 高频错误，使用专门异常类
            raise LicenseQuotaExceededException(
                detail=f'您的试用许可证数量已达上限（{max_trial_licenses}个）',
                current_count=trial_count,
                max_count=max_trial_licenses,
                member_id=member.id
            )
        
        # 创建许可证
        license = self._create_trial_license(product, plan_id)
        return license
```

## 总结

### 关键要点

1. **向后兼容** - 旧代码继续工作，不需要一次性迁移
2. **渐进迁移** - 按模块逐步迁移，优先核心模块
3. **新代码新规范** - 所有新代码立即采用新异常系统
4. **测试保障** - 每次迁移后运行测试
5. **文档同步** - 更新相关文档

### 推荐迁移顺序

1. ✅ **新功能**（立即） - 所有新代码使用新异常系统
2. ⭐⭐⭐ **租户模块**（第1-2周） - 核心基础设施
3. ⭐⭐⭐ **许可证模块**（第2-3周） - 核心业务逻辑
4. ⭐⭐⭐ **用户模块**（第3-4周） - 核心业务逻辑
5. ⭐⭐ **CMS模块**（第5-6周） - 重要功能
6. ⭐⭐ **积分模块**（第7-8周） - 重要功能
7. ⭐ **其他模块**（持续） - 非核心功能

---

**维护者**: Lipeaks Backend Team  
**最后更新**: 2025-01-08

