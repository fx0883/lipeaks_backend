# 积分系统API文档

## API概览

**涉及的API**: 2个  
**调用方式变化**: 无 ✅  
**修改类型**: 文档注解（添加schema定义和swagger检查）

---

## API 1: 积分统计概览

### 基本信息

- **端点**: `GET /api/v1/points/statistics/`
- **功能**: 获取租户的积分系统统计数据
- **认证**: 需要（Bearer Token）
- **权限**: 已认证用户

### 修改历史

| 日期 | 修改类型 | 说明 |
|------|---------|------|
| 2025-11-22 | 文档注解 | 添加`@extend_schema`定义响应结构，添加`serializer_class = None` |

**重要**: 此修改**不影响**API调用方式，仅用于改进API文档生成。

### 请求参数

#### Headers
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Authorization | string | 是 | Bearer {access_token} |

#### Query Parameters
无

### 响应格式

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": {
    "total_users": 156,
    "active_users": 142,
    "total_points_distributed": 45230,
    "average_points_per_user": 290.06,
    "level_distribution": {
      "青铜": 45,
      "白银": 38,
      "黄金": 32,
      "铂金": 24,
      "钻石": 17
    },
    "vip_distribution": {
      "vip": 23,
      "enterprise": 12,
      "education": 8,
      "developer": 15,
      "partner": 5,
      "trial": 34,
      "custom": 3
    }
  }
}
```

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| total_users | integer | 租户下的总用户数 |
| active_users | integer | 启用积分功能的用户数 |
| total_points_distributed | number | 已分发的总积分数 |
| average_points_per_user | number | 每用户平均积分 |
| level_distribution | object | 各等级的用户分布 |
| vip_distribution | object | 各VIP标签的用户分布 |

#### 错误响应

**400 Bad Request** - 无法确定租户
```json
{
  "success": false,
  "code": 4000,
  "message": "无法确定用户租户",
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

#### 基础调用

```bash
# 获取积分统计
curl -X GET http://localhost:8000/api/v1/points/statistics/ \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -m json.tool
```

#### 完整示例（with error handling）

```bash
#!/bin/bash

API_BASE="http://localhost:8000/api/v1"

# 登录获取token
echo "=== 获取认证Token ==="
TOKEN=$(curl -s -X POST "$API_BASE/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"username": "test_admin", "password": "test123456"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['token'])")

echo "Token获取成功"

# 获取积分统计
echo ""
echo "=== 获取积分统计数据 ==="
curl -s -X GET "$API_BASE/points/statistics/" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data.get('success'):
    stats = data['data']
    print('✅ 统计数据获取成功')
    print(f\"总用户数: {stats['total_users']}\")
    print(f\"活跃用户数: {stats['active_users']}\")
    print(f\"总积分: {stats['total_points_distributed']}\")
    print(f\"平均积分: {stats['average_points_per_user']:.2f}\")
    print('')
    print('等级分布:')
    for level, count in stats['level_distribution'].items():
        print(f\"  {level}: {count}人\")
else:
    print('❌ 获取失败:', data.get('message'))
"
```

---

## API 2: 用户积分记录

### 基本信息

- **端点**: `GET /api/v1/points/user-points/`
- **功能**: 查询用户积分变动记录
- **认证**: 需要（Bearer Token）
- **权限**: 已认证用户 + 积分管理权限

### 修改历史

| 日期 | 修改类型 | 说明 |
|------|---------|------|
| 2025-11-22 | 内部优化 | 添加`swagger_fake_view`检查和`ensure_tenant_isolation`导入 |

**重要**: 此修改**不影响**API调用方式，仅用于修复schema生成时的错误。

### 请求参数

#### Headers
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Authorization | string | 是 | Bearer {access_token} |

#### Query Parameters
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| tenant | integer | 否 | 租户ID过滤 |
| point_type | string | 否 | 积分类型：earn/deduct/expire/transfer |
| category | string | 否 | 积分分类 |
| status | string | 否 | 状态：pending/completed/cancelled/expired |
| is_manual | boolean | 否 | 是否手动操作 |
| source_type | string | 否 | 来源类型 |
| search | string | 否 | 搜索关键词（operation_reason, source_description） |
| ordering | string | 否 | 排序字段：created_at, points, expires_at（前缀-表示降序） |
| page | integer | 否 | 页码（默认1） |
| page_size | integer | 否 | 每页数量（默认10） |

### 响应格式

#### 成功响应 (200 OK)

```json
{
  "success": true,
  "code": 2000,
  "message": "查询成功",
  "data": {
    "count": 150,
    "next": "http://localhost:8000/api/v1/points/user-points/?page=2",
    "previous": null,
    "results": [
      {
        "id": 1,
        "member_info": {
          "id": 10,
          "username": "john_doe",
          "nick_name": "John"
        },
        "tenant_info": {
          "id": 2,
          "name": "测试租户"
        },
        "profile_info": {
          "id": 5,
          "total_points": 1250,
          "available_points": 980
        },
        "point_type": "earn",
        "category": "task_completion",
        "points": 50,
        "operation_reason": "完成每日任务",
        "source_type": "system",
        "source_description": "每日任务系统",
        "status": "completed",
        "is_manual": false,
        "expires_at": "2026-11-23T10:00:00Z",
        "is_expired": false,
        "days_until_expiry": 365,
        "created_at": "2025-11-23T10:00:00Z",
        "updated_at": "2025-11-23T10:00:00Z"
      }
    ]
  }
}
```

#### 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| point_type | string | 积分类型：earn(获得)/deduct(扣除)/expire(过期)/transfer(转移) |
| category | string | 积分分类（可自定义） |
| points | number | 积分数量 |
| operation_reason | string | 操作原因 |
| source_type | string | 来源类型 |
| status | string | 状态：pending/completed/cancelled/expired |
| is_manual | boolean | 是否手动操作 |
| expires_at | datetime | 过期时间 |
| is_expired | boolean | 是否已过期 |
| days_until_expiry | integer | 距离过期天数 |

### curl调用示例

#### 1. 基础查询

```bash
# 查询所有积分记录
curl -X GET http://localhost:8000/api/v1/points/user-points/ \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -m json.tool
```

#### 2. 带过滤条件查询

```bash
# 查询获得积分的记录
curl -X GET "http://localhost:8000/api/v1/points/user-points/?point_type=earn&ordering=-created_at" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -m json.tool
```

#### 3. 搜索特定关键词

```bash
# 搜索包含"任务"的积分记录
curl -X GET "http://localhost:8000/api/v1/points/user-points/?search=任务" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -m json.tool
```

#### 4. 分页查询

```bash
# 查询第2页，每页20条
curl -X GET "http://localhost:8000/api/v1/points/user-points/?page=2&page_size=20" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -m json.tool
```

#### 5. 完整示例脚本

```bash
#!/bin/bash

API_BASE="http://localhost:8000/api/v1"

# 获取token
TOKEN=$(curl -s -X POST "$API_BASE/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{"username": "test_admin", "password": "test123456"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['data']['token'])")

# 查询积分记录
echo "=== 查询用户积分记录 ==="
curl -s -X GET "$API_BASE/points/user-points/?point_type=earn&ordering=-created_at&page_size=5" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c "
import sys, json
from datetime import datetime

data = json.load(sys.stdin)
if data.get('success'):
    results = data['data']['results']
    count = data['data']['count']
    
    print(f'✅ 查询成功，共{count}条记录')
    print('')
    
    for record in results:
        print(f\"ID: {record['id']}\")
        print(f\"  类型: {record['point_type']}\")
        print(f\"  积分: {record['points']}\")
        print(f\"  原因: {record['operation_reason']}\")
        print(f\"  状态: {record['status']}\")
        print(f\"  时间: {record['created_at']}\")
        print('')
else:
    print('❌ 查询失败:', data.get('message'))
"
```

### 使用场景

1. **积分明细查询**:
   - 用户查看自己的积分变动历史
   - 管理员查看所有用户的积分记录

2. **积分审计**:
   - 查询手动操作的积分记录
   - 追踪特定来源的积分变动

3. **数据分析**:
   - 统计某个时间段的积分发放情况
   - 分析积分过期情况

### 注意事项

1. **租户隔离**:
   - 自动过滤当前用户租户的数据
   - 超级管理员可看到所有租户数据

2. **性能优化**:
   - 使用分页避免一次加载大量数据
   - 建议page_size不超过100

3. **过期状态**:
   - `is_expired`和`days_until_expiry`是实时计算的
   - 可用于提醒用户即将过期的积分

---

**文档版本**: 1.0  
**最后更新**: 2025-11-23  
**API状态**: 稳定 ✅  
**向后兼容**: 是
