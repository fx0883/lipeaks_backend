# 反馈系统API文档

## API概览

**涉及的API**: 1个  
**调用方式变化**: 无 ✅  
**修改类型**: 文档注解（添加serializer_class）

---

## API 1: 切换反馈通知状态

### 基本信息

- **端点**: `PATCH /api/v1/feedbacks/feedbacks/{id}/notifications/`
- **功能**: 切换指定反馈的通知开关状态
- **认证**: 需要（Bearer Token）
- **权限**: 仅反馈创建者可操作

### 修改历史

| 日期 | 修改类型 | 说明 |
|------|---------|------|
| 2025-11-22 | 文档注解 | 添加`serializer_class = FeedbackDetailSerializer`用于schema生成 |

**重要**: 此修改**不影响**API调用方式，仅用于改进API文档生成。

### 请求参数

#### URL参数
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| id | integer | 是 | 反馈ID |

#### Headers
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Authorization | string | 是 | Bearer {access_token} |
| Content-Type | string | 是 | application/json |

#### Request Body
无需请求体（仅切换状态）

### 响应格式

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 1,
    "title": "反馈标题",
    "description": "反馈描述",
    "feedback_type": "bug",
    "priority": "high",
    "status": "pending",
    "notifications_enabled": false,  // 切换后的状态
    "user": {
      "id": 5,
      "username": "test_user",
      "email": "user@example.com"
    },
    "created_at": "2025-11-23T10:00:00Z",
    "updated_at": "2025-11-23T10:30:00Z"
  }
}
```

#### 错误响应

**403 Forbidden** - 没有权限
```json
{
  "success": false,
  "code": 4030,
  "message": "Permission denied.",
  "data": null
}
```

**404 Not Found** - 反馈不存在
```json
{
  "success": false,
  "code": 4040,
  "message": "Feedback not found.",
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

### curl调用示例

#### 1. 获取认证Token

```bash
# 登录获取token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }' | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['token'])")

echo "Token: $TOKEN"
```

#### 2. 调用API切换通知状态

```bash
# 切换反馈ID为1的通知状态
curl -X PATCH http://localhost:8000/api/v1/feedbacks/feedbacks/1/notifications/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  | python3 -m json.tool
```

#### 3. 完整示例（包含错误处理）

```bash
#!/bin/bash

# 配置
API_BASE="http://localhost:8000/api/v1"
FEEDBACK_ID=1

# 登录获取token
echo "=== 步骤1: 获取认证Token ==="
LOGIN_RESPONSE=$(curl -s -X POST "$API_BASE/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_admin",
    "password": "test123456"
  }')

TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['token'])")

if [ -z "$TOKEN" ]; then
  echo "登录失败"
  exit 1
fi

echo "Token获取成功"

# 切换通知状态
echo ""
echo "=== 步骤2: 切换反馈通知状态 ==="
RESPONSE=$(curl -s -X PATCH "$API_BASE/feedbacks/feedbacks/$FEEDBACK_ID/notifications/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json")

# 解析响应
echo $RESPONSE | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('success'):
    print('✅ 通知状态切换成功')
    notifications_enabled = data['data'].get('notifications_enabled')
    print(f'当前通知状态: {\"开启\" if notifications_enabled else \"关闭\"}')
else:
    print('❌ 操作失败:', data.get('message'))
"
```

### 业务逻辑说明

1. **权限验证**:
   - 检查用户是否已认证
   - 验证用户是否为反馈的创建者
   - 只有创建者可以切换自己反馈的通知状态

2. **状态切换**:
   - 自动切换`notifications_enabled`字段
   - true → false 或 false → true
   - 不需要在请求体中指定目标状态

3. **通知影响**:
   - `notifications_enabled = true`: 用户将收到该反馈的更新通知（状态变更、新回复等）
   - `notifications_enabled = false`: 用户不再收到该反馈的任何通知

### 使用场景

1. **用户关闭通知**:
   ```bash
   # 用户不想再收到某个反馈的通知
   PATCH /api/v1/feedbacks/feedbacks/123/notifications/
   ```

2. **用户重新开启通知**:
   ```bash
   # 用户想重新接收通知
   PATCH /api/v1/feedbacks/feedbacks/123/notifications/
   ```

### 注意事项

1. **幂等性**: 
   - 此API是幂等的，多次调用会在true和false之间来回切换
   - 不建议连续快速调用

2. **状态查询**:
   - 如需查询当前状态，使用GET `/api/v1/feedbacks/feedbacks/{id}/`
   - 响应中包含`notifications_enabled`字段

3. **权限限制**:
   - 管理员也无法切换其他用户的反馈通知设置
   - 必须是反馈的原始创建者

### 相关API

- `GET /api/v1/feedbacks/feedbacks/` - 获取反馈列表
- `GET /api/v1/feedbacks/feedbacks/{id}/` - 获取反馈详情
- `POST /api/v1/feedbacks/feedbacks/` - 创建反馈
- `PATCH /api/v1/feedbacks/feedbacks/{id}/` - 更新反馈
- `DELETE /api/v1/feedbacks/feedbacks/{id}/` - 删除反馈

---

**文档版本**: 1.0  
**最后更新**: 2025-11-23  
**API状态**: 稳定 ✅  
**向后兼容**: 是
