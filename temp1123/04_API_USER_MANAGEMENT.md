# 用户管理API文档

## API概览

**涉及的API**: 1个  
**调用方式变化**: 无 ✅  
**修改类型**: 内部类重命名（不影响endpoint）

---

## API: 更新用户角色

### 基本信息

- **端点**: `PATCH /api/v1/users/role/{id}/update/`
- **功能**: 更新指定用户的角色（管理员/普通成员）
- **认证**: 需要（Bearer Token）
- **权限**: 管理员权限

### 修改历史

| 日期 | 修改类型 | 说明 |
|------|---------|------|
| 2025-11-22 | 内部重构 | `UserRoleSerializer`重命名为`UserRoleUpdateSerializer`避免与RBAC模块冲突 |

**重要**: 此修改是**内部类名重命名**，API endpoint、请求参数、响应格式**完全没有变化**。

### 请求参数

#### URL参数
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 用户ID |

#### Headers
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Authorization | string | 是 | Bearer {access_token} |
| Content-Type | string | 是 | application/json |

#### Request Body
```json
{
  "is_admin": true,      // 是否为管理员
  "is_member": false     // 是否为普通成员（可选）
}
```

**字段说明**:
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| is_admin | boolean | 是 | 是否为管理员 |
| is_member | boolean | 否 | 是否为普通成员（取消管理员时自动设为true） |

### 响应格式

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "code": 2000,
  "message": "角色更新成功",
  "data": {
    "id": 10,
    "is_admin": true,
    "is_member": false
  }
}
```

#### 错误响应

**400 Bad Request** - 不能修改超级管理员
```json
{
  "success": false,
  "code": 4000,
  "message": "不能修改超级管理员的角色",
  "data": null
}
```

**400 Bad Request** - 不能同时为管理员和普通成员
```json
{
  "success": false,
  "code": 4000,
  "message": "用户不能同时是管理员和普通成员",
  "data": {
    "is_admin": ["用户不能同时是管理员和普通成员"]
  }
}
```

**403 Forbidden** - 权限不足
```json
{
  "success": false,
  "code": 4030,
  "message": "您没有权限修改其他租户的用户",
  "data": null
}
```

**404 Not Found** - 用户不存在
```json
{
  "success": false,
  "code": 4040,
  "message": "用户不存在",
  "data": null
}
```

### curl调用示例

#### 1. 将用户提升为管理员

```bash
# 将用户ID为10的用户提升为管理员
curl -X PATCH http://localhost:8000/api/v1/users/role/10/update/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "is_admin": true
  }'
```

#### 2. 将管理员降级为普通成员

```bash
# 将用户ID为10的管理员降级为普通成员
curl -X PATCH http://localhost:8000/api/v1/users/role/10/update/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "is_admin": false,
    "is_member": true
  }'
```

#### 3. 完整示例脚本

```bash
#!/bin/bash

API_BASE="http://localhost:8000/api/v1"
USER_ID=10

# 获取token
echo "=== 步骤1: 获取认证Token ==="
TOKEN=$(curl -s -X POST "$API_BASE/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"username": "test_admin", "password": "test123456"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['token'])")

echo "Token获取成功"

# 查看用户当前信息
echo ""
echo "=== 步骤2: 查看用户当前信息 ==="
curl -s -X GET "$API_BASE/users/$USER_ID/" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('success'):
    user = data['data']
    print(f\"用户: {user['username']}\")
    print(f\"当前是管理员: {user.get('is_admin', False)}\")
    print(f\"当前是普通成员: {user.get('is_member', False)}\")
"

# 更新用户角色
echo ""
echo "=== 步骤3: 更新用户角色 ==="
echo "将用户提升为管理员..."

RESPONSE=$(curl -s -X PATCH "$API_BASE/users/role/$USER_ID/update/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "is_admin": true
  }')

echo $RESPONSE | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('success'):
    print('✅ 角色更新成功')
    user = data['data']
    print(f\"is_admin: {user['is_admin']}\")
    print(f\"is_member: {user['is_member']}\")
else:
    print('❌ 更新失败')
    print('错误:', data.get('message'))
    if data.get('data'):
        for field, errors in data['data'].items():
            print(f\"  {field}: {errors}\")
"

# 再次查看用户信息确认
echo ""
echo "=== 步骤4: 确认角色已更新 ==="
curl -s -X GET "$API_BASE/users/$USER_ID/" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('success'):
    user = data['data']
    print(f\"✅ 确认用户 {user['username']} 的新角色:\")
    print(f\"   管理员: {user.get('is_admin', False)}\")
    print(f\"   普通成员: {user.get('is_member', False)}\")
"
```

### 业务逻辑说明

1. **权限验证**:
   - 超级管理员可以更新任何用户的角色
   - 租户管理员只能更新同一租户内的普通用户角色
   - 不能修改超级管理员的角色

2. **角色互斥性**:
   - 用户不能同时是管理员和普通成员
   - 设置`is_admin=true`时，系统自动设置`is_member=false`
   - 设置`is_admin=false`时，如果未指定`is_member`，系统自动设置`is_member=true`

3. **角色降级**:
   - 将管理员降级为普通成员时，管理员相关权限将被撤销
   - 用户将无法访问管理功能

### 使用场景

1. **提升用户为管理员**:
   ```json
   {"is_admin": true}
   ```

2. **管理员降级为普通成员**:
   ```json
   {"is_admin": false, "is_member": true}
   ```

3. **批量角色管理**:
   ```bash
   # 批量提升多个用户
   for user_id in 10 11 12 13 14; do
     curl -X PATCH "$API_BASE/users/role/$user_id/update/" \
       -H "Authorization: Bearer $TOKEN" \
       -H "Content-Type: application/json" \
       -d '{"is_admin": true}'
   done
   ```

### 注意事项

1. **超级管理员保护**:
   - 超级管理员的角色无法通过此API修改
   - 需要通过数据库或特殊管理接口

2. **租户隔离**:
   - 租户管理员只能管理本租户用户
   - 跨租户操作将返回403错误

3. **权限生效**:
   - 角色变更立即生效
   - 用户需要重新登录或刷新token才能获得新权限

4. **审计日志**:
   - 所有角色变更都会记录到审计日志
   - 包括操作人、目标用户、变更内容

### 与RBAC系统的区别

| 特性 | 此API（用户角色） | RBAC系统 |
|------|------------------|----------|
| 功能 | 设置用户是否为管理员 | 为用户分配具体的权限角色 |
| 粒度 | 粗粒度（管理员/成员） | 细粒度（具体权限） |
| 适用场景 | 快速分配基本角色 | 详细的权限管理 |
| API位置 | /api/v1/users/role/ | /api/v1/rbac/users/ |

**建议**: 
- 对于简单的管理员/成员区分，使用此API
- 对于复杂的权限控制，使用RBAC系统

### 相关API

- `GET /api/v1/users/` - 获取用户列表
- `GET /api/v1/users/{id}/` - 获取用户详情
- `PATCH /api/v1/users/{id}/` - 更新用户信息
- `POST /api/v1/rbac/users/{user_type}/{user_id}/roles/` - RBAC角色分配

---

**文档版本**: 1.0  
**最后更新**: 2025-11-23  
**API状态**: 稳定 ✅  
**向后兼容**: 是  
**内部变更**: UserRoleSerializer → UserRoleUpdateSerializer（不影响API）
