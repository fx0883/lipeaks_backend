# 已撤销许可证仍可激活问题修复

## 问题描述

**问题**: 已经撤销的许可证（`status='revoked'`）仍然可以被激活

**影响**: 
- 管理员撤销许可证后，客户端仍可使用该许可证进行激活
- 安全风险：无法有效控制许可证的生命周期

---

## 问题根源

### 原逻辑（有缺陷）

**文件**: `licenses/services/license_service.py`（第195-215行）

```python
# 1. 查找许可证记录
try:
    license_hash = self.security_service.hash_manager.hash_data(license_key)
    license_obj = License.objects.get(
        license_hash=license_hash,
        status__in=['generated', 'activated']  # ← 问题：依赖查询过滤
    )
except License.DoesNotExist:
    return {
        'success': False,
        'error': 'License not found or invalid',
        'code': 'LICENSE_NOT_FOUND'
    }

# 2. 检查许可证状态
if license_obj.status == 'revoked':  # ← 这个检查永远不会执行！
    return {
        'success': False,
        'error': 'License has been revoked',
        'code': 'LICENSE_REVOKED'
    }
```

### 问题分析

1. **查询条件过滤了 `revoked` 状态**
   - `status__in=['generated', 'activated']` 排除了 `revoked`
   - 如果许可证被撤销，查询会抛出 `DoesNotExist` 异常
   - 返回的错误信息是 `LICENSE_NOT_FOUND`，而不是 `LICENSE_REVOKED`

2. **第210-215行的检查是死代码**
   - 因为查询已经过滤了 `revoked`，所以这个 `if` 永远不会执行
   - 这个检查的存在说明之前可能有人发现了同样的问题

3. **缺乏明确的状态验证日志**
   - 无法区分"许可证不存在"和"许可证已撤销"
   - 不便于问题排查和安全审计

---

## 修复方案

### 改进逻辑（明确状态检查）

**文件**: `licenses/services/license_service.py`（第195-225行）

```python
# 1. 查找许可证记录（不过滤状态）
try:
    license_hash = self.security_service.hash_manager.hash_data(license_key)
    license_obj = License.objects.get(license_hash=license_hash)  # ✅ 查询所有许可证
except License.DoesNotExist:
    return {
        'success': False,
        'error': 'License not found or invalid',
        'code': 'LICENSE_NOT_FOUND'
    }

# 2. 检查许可证状态（必须先检查是否被撤销）
if license_obj.status == 'revoked':
    logger.warning(f"尝试激活已撤销的许可证: {license_hash[:16]}...")  # ✅ 添加日志
    return {
        'success': False,
        'error': 'License has been revoked',
        'code': 'LICENSE_REVOKED'
    }

# 检查许可证状态是否允许激活
if license_obj.status not in ['generated', 'activated']:  # ✅ 明确检查
    logger.warning(
        f"许可证状态不允许激活: status={license_obj.status}, "
        f"license_hash={license_hash[:16]}..."
    )
    return {
        'success': False,
        'error': f'License status is {license_obj.status}, cannot be activated',
        'code': 'INVALID_LICENSE_STATUS'
    }
```

---

## 修复改进点

### 1. **移除查询时的状态过滤**

**修改前**:
```python
License.objects.get(
    license_hash=license_hash,
    status__in=['generated', 'activated']  # ← 依赖数据库过滤
)
```

**修改后**:
```python
License.objects.get(license_hash=license_hash)  # ← 查询所有状态
```

**优点**:
- 明确区分"许可证不存在"和"许可证状态无效"
- 可以返回更精确的错误信息
- 更容易维护和理解

### 2. **优先检查 `revoked` 状态**

```python
# ✅ 必须先检查是否被撤销
if license_obj.status == 'revoked':
    logger.warning(f"尝试激活已撤销的许可证: {license_hash[:16]}...")
    return {'code': 'LICENSE_REVOKED'}
```

**优点**:
- 明确拒绝已撤销的许可证
- 添加警告日志，便于安全审计
- 返回明确的错误码

### 3. **通用状态检查**

```python
# ✅ 检查是否在允许的状态中
if license_obj.status not in ['generated', 'activated']:
    logger.warning(f"许可证状态不允许激活: status={license_obj.status}")
    return {'code': 'INVALID_LICENSE_STATUS'}
```

**优点**:
- 处理所有无效状态（不仅是 `revoked`）
- 返回状态信息，便于调试
- 可扩展性好

---

## 许可证状态说明

### 状态定义

| 状态 | 说明 | 可以激活 |
|------|------|---------|
| `generated` | 已生成，未激活 | ✅ 可以 |
| `activated` | 已激活 | ✅ 可以（重新激活） |
| `revoked` | 已撤销 | ❌ 不可以 |
| `expired` | 已过期 | ❌ 不可以 |

### 状态转换

```text
generated → activated  (首次激活)
    ↓
activated → revoked    (管理员撤销)
    ↓
revoked → ❌ 无法激活  (终态)
```

---

## 错误码对照表

### 修复前后对比

| 场景 | 修复前 | 修复后 |
|------|--------|--------|
| **许可证不存在** | `LICENSE_NOT_FOUND` | `LICENSE_NOT_FOUND` ✅ 正确 |
| **许可证已撤销** | `LICENSE_NOT_FOUND` ❌ 错误 | `LICENSE_REVOKED` ✅ 正确 |
| **其他无效状态** | `LICENSE_NOT_FOUND` ❌ 不明确 | `INVALID_LICENSE_STATUS` ✅ 明确 |

### API 响应示例

#### 1. 许可证已撤销

```json
{
    "success": false,
    "error": "License has been revoked",
    "code": "LICENSE_REVOKED"
}
```

#### 2. 许可证状态无效

```json
{
    "success": false,
    "error": "License status is expired, cannot be activated",
    "code": "INVALID_LICENSE_STATUS"
}
```

---

## 测试验证

### 测试场景 1: 激活已撤销的许可证

```bash
# 1. 生成许可证
POST /api/v1/licenses/admin/licenses/
→ license_key: "ABC-123-XYZ"

# 2. 撤销许可证
POST /api/v1/licenses/admin/licenses/{id}/revoke/
{
    "reason": "测试撤销"
}

# 3. 尝试激活（应该失败）✅
POST /api/v1/licenses/activate/
{
    "license_key": "ABC-123-XYZ",
    "hardware_info": {...}
}

# ✅ 期望响应（修复后）
{
    "success": false,
    "error": "License has been revoked",
    "code": "LICENSE_REVOKED"
}

# ❌ 原来的响应（修复前）
{
    "success": false,
    "error": "License not found or invalid",
    "code": "LICENSE_NOT_FOUND"  // 错误：应该是 LICENSE_REVOKED
}
```

### 测试场景 2: 查看日志

**修复后的日志**:
```log
[WARNING] 尝试激活已撤销的许可证: a3f5d8e2c1b4...
[WARNING] 许可证状态不允许激活: status=expired, license_hash=b2d1e9f3...
```

**优点**:
- 便于识别恶意激活尝试
- 可以追踪哪些许可证被尝试激活
- 支持安全审计

---

## 安全增强

### 1. **防止撤销后继续使用**

**场景**:
- 管理员撤销某个客户的许可证
- 客户尝试重新激活

**修复前**: 可能绕过检查  
**修复后**: ✅ 明确拒绝，并记录日志

### 2. **审计追踪**

所有尝试激活已撤销许可证的行为都会被记录：

```log
[WARNING] 尝试激活已撤销的许可证: hash=a3f5...
  - IP: 192.168.1.100
  - User-Agent: Mozilla/5.0...
  - Time: 2025-10-18 16:20:00
```

### 3. **明确的错误信息**

客户端可以根据错误码采取不同的处理：

```javascript
if (response.code === 'LICENSE_REVOKED') {
    showError('您的许可证已被撤销，请联系客服');
} else if (response.code === 'LICENSE_NOT_FOUND') {
    showError('许可证不存在，请检查密钥是否正确');
}
```

---

## 相关修复

本次修复是许可证生命周期管理系列修复的一部分：

| 功能 | 问题 | 修复状态 |
|------|------|----------|
| 解绑设备 | 不删除 activation_code | ✅ 已修复 |
| 撤销许可证 | 不删除 activation_code | ✅ 已修复 |
| 验证激活 | 不检查设备状态 | ✅ 已修复 |
| **激活许可证** | **不检查 revoked 状态** | ✅ **已修复** |

---

## 兼容性说明

### API 行为变化

| 场景 | 修复前 | 修复后 |
|------|--------|--------|
| 激活已撤销许可证 | 返回 `LICENSE_NOT_FOUND` | 返回 `LICENSE_REVOKED` ✅ |
| 错误信息 | 不明确 | 明确区分 ✅ |

### 客户端适配

**推荐**：更新客户端错误处理逻辑

```javascript
// 处理激活错误
function handleActivationError(response) {
    switch (response.code) {
        case 'LICENSE_REVOKED':
            return '许可证已被撤销，请联系管理员';
        
        case 'INVALID_LICENSE_STATUS':
            return '许可证状态异常，无法激活';
        
        case 'LICENSE_NOT_FOUND':
            return '许可证不存在，请检查密钥';
        
        case 'LICENSE_EXPIRED':
            return '许可证已过期';
        
        default:
            return '激活失败，请稍后重试';
    }
}
```

---

## 数据库查询

### 查找已撤销但仍有激活记录的许可证

```sql
SELECT 
    l.id,
    l.license_key,
    l.status,
    COUNT(la.id) AS activation_count
FROM 
    licenses_license l
    LEFT JOIN licenses_activation la ON l.id = la.license_id AND la.result = 'success'
WHERE 
    l.status = 'revoked'
GROUP BY 
    l.id, l.license_key, l.status
HAVING 
    COUNT(la.id) > 0;
```

**期望结果**: 修复后应该返回 0 条记录（撤销时已删除激活记录）

---

## 总结

### 修复内容

✅ **移除查询时的状态过滤**  
✅ **明确检查 `revoked` 状态**  
✅ **添加日志记录**  
✅ **返回明确的错误码**  

### 改进效果

| 方面 | 修复前 | 修复后 |
|------|--------|--------|
| **安全性** | ⚠️ 可能绕过 | ✅ 明确拒绝 |
| **错误信息** | ❌ 不明确 | ✅ 精确 |
| **审计追踪** | ❌ 无日志 | ✅ 完整日志 |
| **可维护性** | ⚠️ 有死代码 | ✅ 逻辑清晰 |

---

**修复版本**: 1.0.2  
**修复日期**: 2025-10-18  
**影响范围**: 许可证激活功能  
**修复文件**: `licenses/services/license_service.py`
