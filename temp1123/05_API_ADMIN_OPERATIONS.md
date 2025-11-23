# 管理员操作API文档

## API概览

**涉及的API**: 2个  
**调用方式变化**: 无 ✅  
**修改类型**: 文档注解（添加operation_id避免冲突）

---

## API 1: 上传当前管理员头像

### 基本信息

- **端点**: `POST /api/v1/admin-users/avatar/upload/`
- **功能**: 上传并更新当前登录管理员用户的头像图片
- **认证**: 需要（Bearer Token）
- **权限**: 管理员权限
- **Content-Type**: multipart/form-data

### 修改历史

| 日期 | 修改类型 | 说明 |
|------|---------|------|
| 2025-11-22 | 文档注解 | 添加`operation_id="admin_users_current_avatar_upload"`避免与API 2冲突 |

**重要**: 此修改**不影响**API调用方式，仅用于解决OpenAPI文档中的operationId冲突。

### 请求参数

#### Headers
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Authorization | string | 是 | Bearer {access_token} |
| Content-Type | string | 是 | multipart/form-data |

#### Form Data
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| avatar | file | 是 | 头像文件（JPG、PNG、GIF、WEBP或BMP格式） |

**文件限制**:
- 最大文件大小：5MB
- 支持格式：JPG、JPEG、PNG、GIF、WEBP、BMP
- 推荐尺寸：200x200px - 800x800px

### 响应格式

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "code": 2000,
  "message": "头像上传成功",
  "data": {
    "detail": "头像上传成功",
    "avatar": "https://example.com/media/avatars/admin_5_1732348800.jpg"
  }
}
```

#### 错误响应

**400 Bad Request** - 未提供文件
```json
{
  "success": false,
  "code": 4000,
  "message": "未提供头像文件",
  "data": null
}
```

**400 Bad Request** - 文件格式不支持
```json
{
  "success": false,
  "code": 4000,
  "message": "不支持的文件类型。请上传JPG、PNG、GIF、WEBP或BMP格式的图片",
  "data": null
}
```

**400 Bad Request** - 文件过大
```json
{
  "success": false,
  "code": 4000,
  "message": "文件大小超过限制（最大5MB）",
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

**403 Forbidden** - 非管理员
```json
{
  "success": false,
  "code": 4030,
  "message": "您没有权限执行此操作",
  "data": null
}
```

### curl调用示例

#### 1. 基础上传

```bash
# 上传头像文件
curl -X POST http://localhost:8000/api/v1/admin-users/avatar/upload/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "avatar=@/path/to/your/avatar.jpg"
```

#### 2. 完整示例脚本

```bash
#!/bin/bash

API_BASE="http://localhost:8000/api/v1"
AVATAR_FILE="/path/to/avatar.jpg"

# 获取token
echo "=== 步骤1: 获取认证Token ==="
TOKEN=$(curl -s -X POST "$API_BASE/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"username": "test_admin", "password": "test123456"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['token'])")

echo "Token获取成功"

# 检查文件是否存在
if [ ! -f "$AVATAR_FILE" ]; then
  echo "错误: 文件不存在: $AVATAR_FILE"
  exit 1
fi

# 检查文件大小
FILE_SIZE=$(stat -f%z "$AVATAR_FILE" 2>/dev/null || stat -c%s "$AVATAR_FILE")
MAX_SIZE=$((5 * 1024 * 1024))  # 5MB

if [ $FILE_SIZE -gt $MAX_SIZE ]; then
  echo "错误: 文件大小超过5MB限制"
  exit 1
fi

echo "文件大小: $(($FILE_SIZE / 1024))KB"

# 上传头像
echo ""
echo "=== 步骤2: 上传头像 ==="
RESPONSE=$(curl -s -X POST "$API_BASE/admin-users/avatar/upload/" \
  -H "Authorization: Bearer $TOKEN" \
  -F "avatar=@$AVATAR_FILE")

echo $RESPONSE | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('success'):
    print('✅ 头像上传成功')
    avatar_url = data['data'].get('avatar')
    print(f'头像URL: {avatar_url}')
else:
    print('❌ 上传失败')
    print('错误:', data.get('message'))
"

# 验证头像已更新
echo ""
echo "=== 步骤3: 验证头像已更新 ==="
curl -s -X GET "$API_BASE/admin-users/current/" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('success'):
    user = data['data']
    print(f\"✅ 当前用户: {user['username']}\")
    print(f\"头像URL: {user.get('avatar', '无')}\")
"
```

#### 3. 使用不同图片格式

```bash
# PNG格式
curl -X POST http://localhost:8000/api/v1/admin-users/avatar/upload/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "avatar=@avatar.png"

# GIF格式
curl -X POST http://localhost:8000/api/v1/admin-users/avatar/upload/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "avatar=@avatar.gif"

# WEBP格式
curl -X POST http://localhost:8000/api/v1/admin-users/avatar/upload/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "avatar=@avatar.webp"
```

---

## API 2: 上传指定管理员头像

### 基本信息

- **端点**: `POST /api/v1/admin-users/{id}/avatar/upload/`
- **功能**: 为特定管理员用户上传头像（需要更高权限）
- **认证**: 需要（Bearer Token）
- **权限**: 管理员权限（超级管理员可为任何人上传，租户管理员仅限本租户）
- **Content-Type**: multipart/form-data

### 修改历史

| 日期 | 修改类型 | 说明 |
|------|---------|------|
| 2025-11-22 | 文档注解 | 添加`operation_id="admin_users_specific_avatar_upload"`避免与API 1冲突 |

**重要**: 此修改**不影响**API调用方式，仅用于解决OpenAPI文档中的operationId冲突。

### 请求参数

#### URL参数
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 目标管理员用户ID |

#### Headers
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Authorization | string | 是 | Bearer {access_token} |
| Content-Type | string | 是 | multipart/form-data |

#### Form Data
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| avatar | file | 是 | 头像文件（JPG、PNG、GIF、WEBP或BMP格式） |

**文件限制**:
- 最大文件大小：5MB
- 支持格式：JPG、JPEG、PNG、GIF、WEBP、BMP
- 推荐尺寸：200x200px - 800x800px

### 响应格式

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "code": 2000,
  "message": "头像上传成功",
  "data": {
    "detail": "头像上传成功",
    "avatar": "https://example.com/media/avatars/admin_10_1732348900.jpg"
  }
}
```

#### 错误响应

**403 Forbidden** - 权限不足
```json
{
  "success": false,
  "code": 4030,
  "message": "您只能为同一租户的管理员上传头像",
  "data": null
}
```

**404 Not Found** - 管理员不存在
```json
{
  "success": false,
  "code": 4040,
  "message": "管理员不存在",
  "data": null
}
```

其他错误响应与API 1相同。

### curl调用示例

#### 1. 基础上传

```bash
# 为用户ID为10的管理员上传头像
curl -X POST http://localhost:8000/api/v1/admin-users/10/avatar/upload/ \
  -H "Authorization: Bearer $TOKEN" \
  -F "avatar=@/path/to/avatar.jpg"
```

#### 2. 完整示例脚本

```bash
#!/bin/bash

API_BASE="http://localhost:8000/api/v1"
TARGET_USER_ID=10
AVATAR_FILE="/path/to/avatar.jpg"

# 获取token（需要超级管理员或租户管理员权限）
echo "=== 步骤1: 获取认证Token ==="
TOKEN=$(curl -s -X POST "$API_BASE/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"username": "super_admin", "password": "admin123456"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['token'])")

echo "Token获取成功"

# 查看目标用户信息
echo ""
echo "=== 步骤2: 查看目标用户信息 ==="
curl -s -X GET "$API_BASE/admin-users/$TARGET_USER_ID/" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('success'):
    user = data['data']
    print(f\"目标用户: {user['username']}\")
    print(f\"当前头像: {user.get('avatar', '无')}\")
    print(f\"租户: {user.get('tenant_name', '无')}\")
"

# 上传头像
echo ""
echo "=== 步骤3: 为目标用户上传头像 ==="
RESPONSE=$(curl -s -X POST "$API_BASE/admin-users/$TARGET_USER_ID/avatar/upload/" \
  -H "Authorization: Bearer $TOKEN" \
  -F "avatar=@$AVATAR_FILE")

echo $RESPONSE | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('success'):
    print('✅ 头像上传成功')
    print(f\"新头像URL: {data['data'].get('avatar')}\")
else:
    print('❌ 上传失败')
    print('错误:', data.get('message'))
"

# 确认头像已更新
echo ""
echo "=== 步骤4: 确认头像已更新 ==="
curl -s -X GET "$API_BASE/admin-users/$TARGET_USER_ID/" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('success'):
    user = data['data']
    print(f\"✅ 用户 {user['username']} 的头像已更新\")
    print(f\"新头像: {user.get('avatar')}\")
"
```

#### 3. 批量为多个管理员上传头像

```bash
#!/bin/bash

API_BASE="http://localhost:8000/api/v1"
AVATAR_FILE="/path/to/default_avatar.jpg"

# 管理员ID列表
ADMIN_IDS=(10 11 12 13 14)

# 获取token
TOKEN=$(curl -s -X POST "$API_BASE/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"username": "super_admin", "password": "admin123456"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['token'])")

echo "=== 批量上传管理员头像 ==="
for admin_id in "${ADMIN_IDS[@]}"; do
  echo ""
  echo "处理管理员ID: $admin_id"
  
  RESPONSE=$(curl -s -X POST "$API_BASE/admin-users/$admin_id/avatar/upload/" \
    -H "Authorization: Bearer $TOKEN" \
    -F "avatar=@$AVATAR_FILE")
  
  echo $RESPONSE | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('success'):
    print('  ✅ 上传成功')
else:
    print('  ❌ 上传失败:', data.get('message'))
"
done

echo ""
echo "=== 批量上传完成 ==="
```

### 权限说明

| 操作者角色 | 权限范围 |
|-----------|----------|
| 超级管理员 | 可为任何管理员上传头像 |
| 租户管理员 | 仅可为同一租户的管理员上传头像 |
| 普通管理员 | 仅可为自己上传头像（使用API 1） |

### 使用场景

#### API 1 vs API 2

| 场景 | 使用API |
|------|---------|
| 用户更新自己的头像 | API 1 |
| 管理员批量设置默认头像 | API 2 |
| HR为新员工设置头像 | API 2 |
| 系统管理员统一更换头像 | API 2 |

### 注意事项

1. **文件存储**:
   - 头像文件存储在`media/avatars/`目录
   - 文件名格式：`admin_{user_id}_{timestamp}.{ext}`
   - 上传新头像会覆盖旧头像

2. **图片处理**:
   - 系统可能会自动调整图片大小
   - 建议上传正方形图片
   - 推荐分辨率：200x200 - 800x800

3. **安全性**:
   - 严格验证文件类型
   - 限制文件大小
   - 检查文件内容防止恶意文件

4. **性能优化**:
   - 使用CDN加速头像访问
   - 考虑图片压缩
   - 实现缓存策略

### 错误排查

#### 上传失败常见原因

1. **文件格式错误**:
   ```bash
   # 检查文件类型
   file /path/to/avatar.jpg
   ```

2. **文件过大**:
   ```bash
   # 检查文件大小（字节）
   ls -l /path/to/avatar.jpg
   ```

3. **权限不足**:
   - 确认token是管理员token
   - 检查租户限制

4. **路径错误**:
   - 确认文件路径正确
   - 使用绝对路径

### 相关API

- `GET /api/v1/admin-users/current/` - 获取当前管理员信息
- `GET /api/v1/admin-users/{id}/` - 获取指定管理员信息
- `PATCH /api/v1/admin-users/{id}/` - 更新管理员信息

---

## 两个API的对比

| 特性 | API 1（当前用户） | API 2（指定用户） |
|------|------------------|------------------|
| 端点 | `/admin-users/avatar/upload/` | `/admin-users/{id}/avatar/upload/` |
| 权限要求 | 管理员 | 管理员（有租户限制） |
| 目标用户 | 当前登录用户 | URL参数指定的用户 |
| 使用场景 | 用户自己更新头像 | 管理员为他人更新头像 |
| operation_id | admin_users_current_avatar_upload | admin_users_specific_avatar_upload |

---

**文档版本**: 1.0  
**最后更新**: 2025-11-23  
**API状态**: 稳定 ✅  
**向后兼容**: 是  
**文档变更**: 添加operation_id（不影响API调用）
