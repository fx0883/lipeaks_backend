# RBAC权限系统API文档

## API概览

**涉及的API**: 1个  
**调用方式变化**: 无 ✅  
**修改类型**: 文档注解（添加参数类型注解）

---

## API: 从角色移除权限

### 基本信息

- **端点**: `DELETE /api/v1/rbac/roles/{id}/permissions/{permission_id}/`
- **功能**: 从指定角色中移除特定权限
- **认证**: 需要（Bearer Token）
- **权限**: 需要RBAC管理权限

### 修改历史

| 日期 | 修改类型 | 说明 |
|------|---------|------|
| 2025-11-22 | 文档注解 | 添加`OpenApiParameter`定义`permission_id`类型为integer |

**重要**: 此修改**不影响**API调用方式，仅用于改进API文档中的参数类型显示。

### 请求参数

#### URL参数
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 角色ID |
| permission_id | integer | 是 | 权限ID |

#### Headers
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Authorization | string | 是 | Bearer {access_token} |

#### Request Body
无

### 响应格式

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "code": 2000,
  "message": "权限已成功从角色中移除",
  "data": {
    "detail": "权限已成功从角色中移除"
  }
}
```

#### 错误响应

**404 Not Found** - 权限不存在
```json
{
  "success": false,
  "code": 4040,
  "message": "权限不存在",
  "data": null
}
```

**404 Not Found** - 角色没有此权限
```json
{
  "success": false,
  "code": 4040,
  "message": "角色没有此权限",
  "data": null
}
```

**401 Unauthorized** - 未认证
```json
{
  "success": false,
  "code": 4010,
  "message": "Authentication credentials were not provided.",
  "data": null
}
```

**403 Forbidden** - 无权限
```json
{
  "success": false,
  "code": 4030,
  "message": "您没有权限执行此操作",
  "data": null
}
```

### curl调用示例

#### 1. 基础调用

```bash
# 从角色ID为3的角色中移除权限ID为15的权限
curl -X DELETE http://localhost:8000/api/v1/rbac/roles/3/permissions/15/ \
  -H "Authorization: Bearer $TOKEN"
```

#### 2. 带完整响应处理

```bash
#!/bin/bash

API_BASE="http://localhost:8000/api/v1"
ROLE_ID=3
PERMISSION_ID=15

# 获取token
TOKEN=$(curl -s -X POST "$API_BASE/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"username": "test_admin", "password": "test123456"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['token'])")

# 移除权限
echo "=== 从角色移除权限 ==="
echo "角色ID: $ROLE_ID"
echo "权限ID: $PERMISSION_ID"
echo ""

RESPONSE=$(curl -s -X DELETE "$API_BASE/rbac/roles/$ROLE_ID/permissions/$PERMISSION_ID/" \
  -H "Authorization: Bearer $TOKEN")

echo $RESPONSE | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('success'):
    print('✅ 权限移除成功')
    print(data.get('message'))
else:
    print('❌ 操作失败')
    print('错误:', data.get('message'))
    print('错误代码:', data.get('code'))
"
```

#### 3. 查看角色权限 + 移除权限的完整流程

```bash
#!/bin/bash

API_BASE="http://localhost:8000/api/v1"
ROLE_ID=3

# 获取token
TOKEN=$(curl -s -X POST "$API_BASE/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"username": "test_admin", "password": "test123456"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['token'])")

# 步骤1: 查看角色当前的权限
echo "=== 步骤1: 查看角色当前权限 ==="
curl -s -X GET "$API_BASE/rbac/roles/$ROLE_ID/permissions/" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('success'):
    permissions = data['data']
    print(f'角色当前拥有 {len(permissions)} 个权限:')
    for perm in permissions[:5]:  # 只显示前5个
        print(f\"  - [{perm['id']}] {perm['name']}: {perm['description']}\")
    if len(permissions) > 5:
        print(f'  ... 还有 {len(permissions) - 5} 个权限')
"

# 步骤2: 选择要移除的权限ID (假设移除ID=15的权限)
PERMISSION_ID=15
echo ""
echo "=== 步骤2: 移除权限 ==="
echo "准备移除权限ID: $PERMISSION_ID"

RESPONSE=$(curl -s -X DELETE "$API_BASE/rbac/roles/$ROLE_ID/permissions/$PERMISSION_ID/" \
  -H "Authorization: Bearer $TOKEN")

echo $RESPONSE | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('success'):
    print('✅ 权限移除成功')
else:
    print('❌ 操作失败:', data.get('message'))
"

# 步骤3: 再次查看权限确认
echo ""
echo "=== 步骤3: 确认权限已移除 ==="
curl -s -X GET "$API_BASE/rbac/roles/$ROLE_ID/permissions/" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('success'):
    permissions = data['data']
    print(f'角色现在拥有 {len(permissions)} 个权限')
    # 检查权限是否还存在
    perm_ids = [p['id'] for p in permissions]
    if $PERMISSION_ID not in perm_ids:
        print(f'✅ 权限{$PERMISSION_ID}已成功移除')
    else:
        print(f'⚠️ 权限{$PERMISSION_ID}仍然存在')
"
```

### 业务逻辑说明

1. **权限检查**:
   - 验证角色是否存在
   - 验证权限是否存在
   - 验证角色是否拥有该权限

2. **移除操作**:
   - 从角色权限关联表中删除记录
   - 不会删除权限本身，只是解除关联

3. **缓存刷新**:
   - 自动刷新受影响用户的权限缓存
   - 确保权限变更立即生效

### 相关API

#### 查看角色权限
```bash
GET /api/v1/rbac/roles/{id}/permissions/
```

#### 为角色添加权限
```bash
POST /api/v1/rbac/roles/{id}/permissions/
Content-Type: application/json

{
  "permission_ids": [15, 16, 17]
}
```

#### 替换角色所有权限
```bash
PUT /api/v1/rbac/roles/{id}/permissions/
Content-Type: application/json

{
  "permission_ids": [1, 2, 3, 4, 5]
}
```

#### 获取所有可用权限
```bash
GET /api/v1/rbac/permissions/
```

### 使用场景

1. **降低角色权限**:
   - 从角色中移除不再需要的权限
   - 缩小角色的权限范围

2. **权限整理**:
   - 清理冗余或过期的权限
   - 优化角色权限配置

3. **安全管理**:
   - 及时撤销敏感权限
   - 响应安全审计要求

### 注意事项

1. **权限生效**:
   - 权限移除后立即生效
   - 拥有该角色的用户将立即失去对应权限

2. **批量操作**:
   - 如需移除多个权限，建议使用PUT方法替换整个权限列表
   - 避免多次调用DELETE

3. **审计日志**:
   - 所有权限变更操作都会记录到审计日志
   - 包括操作人、时间、变更内容

4. **超级管理员**:
   - 超级管理员角色的权限无法移除
   - 某些系统角色可能受保护

### 错误排查

#### 404 权限不存在
- 检查permission_id是否正确
- 使用`GET /api/v1/rbac/permissions/`查看所有权限

#### 404 角色没有此权限
- 先使用`GET /api/v1/rbac/roles/{id}/permissions/`查看角色当前权限
- 确认要移除的权限ID在列表中

#### 403 无权限
- 确认当前用户有RBAC管理权限
- 检查是否尝试修改受保护的系统角色

---

**文档版本**: 1.0  
**最后更新**: 2025-11-23  
**API状态**: 稳定 ✅  
**向后兼容**: 是
