# 异常使用指南

## 概述

本指南提供异常处理的实践指导，帮助开发者正确使用统一的异常处理系统。

## 快速参考

### Service层抛出异常

```python
# 高频核心错误 - 使用专门异常类
from common.exceptions import TenantNotFoundException

raise TenantNotFoundException(
    detail=f'租户ID {tenant_id} 不存在',
    tenant_id=tenant_id
)

# 低频边缘错误 - 使用通用类+错误码
from common.exceptions import LicenseException

raise LicenseException(
    error_code='ACTIVATION_DEVICE_MISMATCH',
    detail='设备指纹不匹配',
    expected=expected_fingerprint,
    actual=actual_fingerprint
)
```

### View层不处理异常

```python
# ✅ 好的做法 - 让全局处理器处理
class TenantDetailView(APIView):
    def get(self, request, tenant_id):
        tenant = tenant_service.get_tenant(tenant_id)  # 可能抛出异常
        serializer = TenantSerializer(tenant)
        return Response(serializer.data)

# ❌ 不好的做法 - View层捕获异常
class TenantDetailView(APIView):
    def get(self, request, tenant_id):
        try:
            tenant = tenant_service.get_tenant(tenant_id)
        except TenantNotFoundException:
            return Response({'error': '不存在'}, status=404)
```

## 选择异常类型

### 决策流程

使用[异常使用决策树](./02_exception_flow_diagrams.md#5-异常使用决策树)判断：

1. **是否为高频错误**（每月>10次）？
   - 是 → 继续判断
   - 否 → 使用通用类+错误码

2. **是否为核心模块**（租户/许可证/用户）？
   - 是 → 使用专门异常类
   - 否 → 使用通用类+错误码

3. **是否需要特殊处理**（特定捕获逻辑）？
   - 是 → 使用专门异常类
   - 否 → 使用通用类+错误码

### 使用专门异常类

**适用场景：**
- ✅ 高频核心业务错误
- ✅ 需要精准捕获和处理
- ✅ 异常语义需要清晰表达
- ✅ IDE自动补全和类型检查重要

**示例：**

```python
from common.exceptions import (
    TenantNotFoundException,
    LicenseExpiredException,
    UserInactiveException
)

# 租户不存在
def get_tenant(tenant_id):
    try:
        tenant = Tenant.objects.get(id=tenant_id, is_deleted=False)
    except Tenant.DoesNotExist:
        raise TenantNotFoundException(
            detail=f'租户ID {tenant_id} 不存在',
            tenant_id=tenant_id
        )
    return tenant

# 许可证过期
def check_license_validity(license):
    if license.is_expired:
        raise LicenseExpiredException(
            detail=f'许可证已于 {license.expires_at.strftime("%Y-%m-%d")} 过期',
            license_id=license.id,
            expired_at=license.expires_at.isoformat()
        )

# 用户未激活
def check_user_active(user):
    if not user.is_active:
        raise UserInactiveException(
            detail=f'用户 {user.username} 已被禁用',
            user_id=user.id,
            username=user.username
        )
```

### 使用通用类+错误码

**适用场景：**
- ✅ 低频边缘场景错误
- ✅ 临时性或可能变化的错误
- ✅ 快速开发，无需创建新类
- ✅ 错误类型众多但不值得每个都创建类

**示例：**

```python
from common.exceptions import LicenseException, CMSException

# 设备指纹不匹配（低频）
def validate_device_fingerprint(license, device_info):
    expected = license.device_fingerprint
    actual = generate_fingerprint(device_info)
    
    if expected != actual:
        raise LicenseException(
            error_code='ACTIVATION_DEVICE_MISMATCH',
            detail='设备指纹不匹配，无法激活许可证',
            expected_fingerprint=expected,
            actual_fingerprint=actual
        )

# 导出格式不支持（边缘场景）
def export_article(article, format):
    supported_formats = ['pdf', 'docx', 'html']
    
    if format not in supported_formats:
        raise CMSException(
            error_code='EXPORT_FORMAT_UNSUPPORTED',
            detail=f'不支持的导出格式: {format}',
            requested_format=format,
            supported_formats=supported_formats
        )
```

## Service层最佳实践

### 1. 业务验证抛出异常

```python
class LicenseService:
    def apply_trial_license(self, member, product_id):
        # 验证产品存在
        try:
            product = SoftwareProduct.objects.get(
                id=product_id,
                status='active',
                is_deleted=False
            )
        except SoftwareProduct.DoesNotExist:
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
            raise LicenseException(
                error_code='LICENSE_ALREADY_ASSIGNED',
                detail='您已经拥有该产品的有效许可证',
                member_id=member.id,
                product_id=product_id
            )
        
        # 检查配额
        user_trial_count = self._get_user_trial_count(member)
        max_trial_licenses = getattr(member, 'max_trial_licenses', 1)
        
        if user_trial_count >= max_trial_licenses:
            raise LicenseQuotaExceededException(
                detail=f'您的试用许可证数量已达上限（{max_trial_licenses}个）',
                current_count=user_trial_count,
                max_count=max_trial_licenses,
                member_id=member.id
            )
        
        # 创建许可证...
        return license
```

### 2. 提供有用的错误上下文

```python
# ✅ 好的做法 - 包含丰富的上下文信息
raise TenantNotFoundException(
    detail=f'租户ID {tenant_id} 不存在',
    tenant_id=tenant_id,
    requested_by=request.user.id,
    request_path=request.path
)

# ✅ 好的做法 - 包含相关数据
raise LicenseQuotaExceededException(
    detail=f'许可证配额已满，当前: {current}/{max_licenses}',
    current_count=current,
    max_count=max_licenses,
    tenant_id=tenant.id
)

# ❌ 不好的做法 - 信息不足
raise TenantNotFoundException()  # 没有上下文

# ❌ 不好的做法 - 暴露敏感信息
raise TenantNotFoundException(
    detail=f'Tenant not found in database table tenant_table',
    sql_query='SELECT * FROM tenant_table WHERE id=123'  # 不要暴露SQL
)
```

### 3. 转换Django模型异常

```python
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError

def create_tenant(data):
    try:
        tenant = Tenant(**data)
        tenant.full_clean()  # 可能抛出Django ValidationError
        tenant.save()
    except DjangoValidationError as e:
        # 转换为DRF ValidationError
        raise DRFValidationError(detail=e.message_dict)
    except IntegrityError as e:
        # 转换为业务异常
        if 'unique constraint' in str(e).lower():
            raise TenantException(
                error_code='TENANT_DUPLICATE',
                detail='租户名称已存在',
                name=data.get('name')
            )
        raise
```

### 4. 链式验证

```python
def validate_and_get_tenant(tenant_id, user):
    # 验证租户存在
    try:
        tenant = Tenant.objects.get(id=tenant_id, is_deleted=False)
    except Tenant.DoesNotExist:
        raise TenantNotFoundException(
            detail=f'租户ID {tenant_id} 不存在',
            tenant_id=tenant_id
        )
    
    # 验证租户激活
    if tenant.status != 'active':
        raise TenantInactiveException(
            detail=f'租户 {tenant.name} 未激活（状态: {tenant.status}）',
            tenant_id=tenant_id,
            status=tenant.status
        )
    
    # 验证访问权限
    if not user.is_super_admin and user.tenant_id != tenant_id:
        raise TenantAccessDeniedException(
            detail='无法访问其他租户的资源',
            user_id=user.id,
            user_tenant_id=user.tenant_id,
            requested_tenant_id=tenant_id
        )
    
    return tenant
```

## View层最佳实践

### 1. 不要捕获业务异常

```python
from rest_framework.views import APIView
from rest_framework.response import Response

# ✅ 好的做法 - 让异常传播到全局处理器
class TenantDetailView(APIView):
    def get(self, request, pk):
        tenant = tenant_service.get_tenant(pk)  # 可能抛出 TenantNotFoundException
        serializer = TenantSerializer(tenant)
        return Response(serializer.data)

# ❌ 不好的做法 - View层捕获业务异常
class TenantDetailView(APIView):
    def get(self, request, pk):
        try:
            tenant = tenant_service.get_tenant(pk)
            serializer = TenantSerializer(tenant)
            return Response(serializer.data)
        except TenantNotFoundException as e:
            # 不要这样做！让全局处理器处理
            return Response({
                'success': False,
                'message': str(e)
            }, status=404)
```

### 2. 使用DRF的raise_exception

```python
from rest_framework import serializers

# ✅ 好的做法 - 使用 raise_exception=True
class TenantCreateView(APIView):
    def post(self, request):
        serializer = TenantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # 自动抛出ValidationError
        tenant = serializer.save()
        return Response(TenantSerializer(tenant).data, status=201)

# ❌ 不好的做法 - 手动处理验证错误
class TenantCreateView(APIView):
    def post(self, request):
        serializer = TenantSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'errors': serializer.errors
            }, status=400)
        tenant = serializer.save()
        return Response(TenantSerializer(tenant).data, status=201)
```

### 3. 只捕获需要特殊处理的异常

```python
# ✅ 可以接受 - 捕获特定异常做特殊处理
class LicenseActivationView(APIView):
    def post(self, request):
        try:
            license = license_service.activate(request.data)
            return Response(LicenseSerializer(license).data)
        except LicenseActivationFailedException as e:
            # 特殊处理：记录激活失败事件
            logger.warning(f'License activation failed: {e.extra}')
            # 然后继续抛出，让全局处理器处理响应
            raise
```

## 异常捕获最佳实践

### 1. 精准捕获

```python
# ✅ 好的做法 - 精准捕获特定异常
try:
    tenant = Tenant.objects.get(id=tenant_id)
except Tenant.DoesNotExist:
    raise TenantNotFoundException(tenant_id=tenant_id)

# ❌ 不好的做法 - 宽泛捕获
try:
    tenant = Tenant.objects.get(id=tenant_id)
except Exception as e:  # 太宽泛
    raise TenantNotFoundException(tenant_id=tenant_id)
```

### 2. 异常链

```python
# ✅ 好的做法 - 保留原始异常
try:
    result = external_api.call()
except requests.RequestException as e:
    raise LicenseException(
        error_code='EXTERNAL_SERVICE_ERROR',
        detail='许可证验证服务调用失败'
    ) from e  # 保留原始异常链

# ❌ 不好的做法 - 丢失原始异常
try:
    result = external_api.call()
except requests.RequestException as e:
    raise LicenseException(
        error_code='EXTERNAL_SERVICE_ERROR',
        detail='许可证验证服务调用失败'
    )  # 丢失了原始异常信息
```

### 3. 不要吞没异常

```python
# ❌ 非常不好的做法 - 吞没异常
try:
    dangerous_operation()
except Exception:
    pass  # 完全忽略异常，非常危险！

# ✅ 好的做法 - 至少记录日志
try:
    dangerous_operation()
except Exception as e:
    logger.exception('Dangerous operation failed')
    raise  # 继续抛出
```

## 错误消息编写指南

### 1. 清晰简洁

```python
# ✅ 好的消息
"租户ID 123 不存在"
"许可证已于 2024-01-15 过期"
"积分余额不足，当前: 100，需要: 500"

# ❌ 不好的消息
"Error"
"Something went wrong"
"Operation failed with code 42"
```

### 2. 用户友好

```python
# ✅ 用户友好
raise PointsInsufficientException(
    detail=f'积分余额不足，当前可用积分: {available}，需要: {required}',
    available=available,
    required=required
)

# ❌ 技术化
raise PointsInsufficientException(
    detail=f'Insufficient balance in points_balance field: {available} < {required}'
)
```

### 3. 不暴露敏感信息

```python
# ✅ 安全
raise UserInactiveException(
    detail='用户账户已被禁用',
    user_id=user.id
)

# ❌ 暴露敏感信息
raise UserInactiveException(
    detail=f'User {user.username} with email {user.email} is inactive',
    password_hash=user.password  # 绝对不要暴露密码！
)
```

### 4. 提供上下文

```python
# ✅ 提供上下文
raise LicenseQuotaExceededException(
    detail=f'租户许可证配额已满（{current}/{max_licenses}），请联系管理员',
    current_count=current,
    max_count=max_licenses,
    tenant_id=tenant.id
)

# ❌ 缺少上下文
raise LicenseQuotaExceededException(
    detail='配额已满'
)
```

## 日志记录

### 异常日志级别

```python
import logging

logger = logging.getLogger(__name__)

# INFO - 正常业务流程（如验证失败）
logger.info(f'User {user_id} failed login attempt')

# WARNING - 业务异常（如配额超限）
logger.warning(f'Tenant {tenant_id} quota exceeded')

# ERROR - 系统异常（需要关注）
logger.error(f'Database connection failed')

# CRITICAL - 严重系统错误
logger.critical(f'System configuration error')
```

### 记录异常堆栈

```python
# ✅ 好的做法 - 使用 logger.exception()
try:
    result = complex_operation()
except Exception as e:
    logger.exception('Complex operation failed')  # 自动记录堆栈
    raise

# ✅ 也可以 - 使用 exc_info=True
try:
    result = complex_operation()
except Exception as e:
    logger.error('Complex operation failed', exc_info=True)
    raise

# ❌ 不好的做法 - 只记录消息
try:
    result = complex_operation()
except Exception as e:
    logger.error(f'Error: {str(e)}')  # 丢失了堆栈信息
    raise
```

## 常见场景示例

### 场景1：资源不存在

```python
def get_license(license_id):
    try:
        license = License.objects.get(id=license_id, is_deleted=False)
    except License.DoesNotExist:
        raise LicenseNotFoundException(
            detail=f'许可证ID {license_id} 不存在',
            license_id=license_id
        )
    return license
```

### 场景2：业务规则验证

```python
def assign_license(member, license):
    # 检查成员和许可证的租户一致性
    if member.tenant_id != license.tenant_id:
        raise LicenseException(
            error_code='TENANT_MISMATCH',
            detail=f'成员和许可证必须属于同一租户',
            member_tenant_id=member.tenant_id,
            license_tenant_id=license.tenant_id
        )
    
    # 检查激活配额
    if license.current_activations >= license.max_activations:
        raise LicenseQuotaExceededException(
            detail=f'许可证激活配额已满（{license.max_activations}个）',
            current_count=license.current_activations,
            max_count=license.max_activations,
            license_id=license.id
        )
```

### 场景3：权限检查

```python
def check_tenant_access(user, tenant_id):
    if not user.is_super_admin and user.tenant_id != tenant_id:
        raise TenantAccessDeniedException(
            detail='无法访问其他租户的资源',
            user_id=user.id,
            user_tenant_id=user.tenant_id,
            requested_tenant_id=tenant_id
        )
```

### 场景4：配额限制

```python
def check_trial_license_quota(member):
    trial_count = LicenseAssignment.objects.filter(
        member=member,
        license__plan__plan_type='trial',
        status='active'
    ).count()
    
    max_trial_licenses = getattr(member, 'max_trial_licenses', 1)
    
    if trial_count >= max_trial_licenses:
        raise LicenseQuotaExceededException(
            detail=f'您的试用许可证数量已达上限（{max_trial_licenses}个）',
            current_count=trial_count,
            max_count=max_trial_licenses,
            member_id=member.id
        )
```

## 总结

### 核心原则

1. **Service层抛异常** - 业务逻辑层负责抛出业务异常
2. **View层不捕获** - 让全局处理器统一处理
3. **精准选择** - 高频用专门类，低频用通用类
4. **丰富上下文** - 提供足够的调试信息
5. **用户友好** - 错误消息清晰易懂
6. **安全第一** - 不暴露敏感信息

### 检查清单

开发时确认：
- [ ] 选择了合适的异常类型（专门类 vs 通用类）
- [ ] 提供了清晰的错误消息
- [ ] 包含了足够的上下文信息（extra参数）
- [ ] 没有在View层捕获业务异常
- [ ] 错误消息不包含敏感信息
- [ ] 使用了合适的日志级别
- [ ] 保留了异常链（使用from e）

---

**维护者**: Lipeaks Backend Team  
**最后更新**: 2025-01-08

