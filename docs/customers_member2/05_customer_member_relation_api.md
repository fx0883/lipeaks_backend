# 客户-联系人关系 API

本文档描述了两个关于客户与联系人（成员）之间关系的列表查询API：
1. 获取客户下的所有联系人列表
2. 获取联系人所属的所有客户列表

## API端点

客户-联系人关系API的基础URL为：`/api/v1/customers/members/relations/`

## 1. 获取客户下的所有联系人列表

获取指定客户ID下的所有联系人列表。

### 请求

- **方法**: `GET`
- **URL**: `/api/v1/customers/members/relations/customer-members/`
- **权限**: 管理员

### 查询参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| customer_id | int | 是 | 客户ID，用于获取该客户下的所有联系人 |

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": [
    {
      "id": 15,
      "username": "zhangsan",
      "email": "zhangsan@example.com",
      "phone": "13800138000",
      "nick_name": "张三",
      "tenant": 1,
      "tenant_name": "示例租户",
      "is_sub_account": false,
      "parent": null,
      "parent_username": null,
      "status": "active",
      "avatar": "https://example.com/media/avatars/zhangsan.jpg",
      "date_joined": "2025-06-01T08:30:00Z",
      "relation": {
        "id": 5,
        "role": "销售经理",
        "is_primary": true,
        "remarks": "负责销售和客户关系维护",
        "created_at": "2025-07-05T06:14:42.362927Z",
        "updated_at": "2025-07-05T06:14:42.362927Z"
      }
    },
    {
      "id": 16,
      "username": "lisi",
      "email": "lisi@example.com",
      "phone": "13900139000",
      "nick_name": "李四",
      "tenant": 1,
      "tenant_name": "示例租户",
      "is_sub_account": false,
      "parent": null,
      "parent_username": null,
      "status": "active",
      "avatar": "https://example.com/media/avatars/lisi.jpg",
      "date_joined": "2025-06-05T10:15:00Z",
      "relation": {
        "id": 6,
        "role": "技术支持",
        "is_primary": false,
        "remarks": "负责技术对接和问题解决",
        "created_at": "2025-07-05T06:15:42.362927Z",
        "updated_at": "2025-07-05T06:15:42.362927Z"
      }
    }
  ]
}
```

### 错误响应

#### 未提供客户ID

```json
{
  "success": false,
  "code": 4000,
  "message": "请求参数错误",
  "data": {
    "error": "请提供客户ID"
  }
}
```

#### 客户不存在

```json
{
  "success": false,
  "code": 4004,
  "message": "资源不存在",
  "data": {
    "error": "客户不存在"
  }
}
```

## 2. 获取联系人所属的所有客户列表

获取指定联系人ID所属的所有客户列表。

### 请求

- **方法**: `GET`
- **URL**: `/api/v1/customers/members/relations/member-customers/`
- **权限**: 管理员

### 查询参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| member_id | int | 是 | 联系人ID，用于获取该联系人所属的所有客户 |

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": [
    {
      "id": 8,
      "name": "示例科技有限公司",
      "type": "enterprise",
      "type_display": "公司",
      "value_level": "gold",
      "value_level_display": "黄金",
      "status": "active",
      "status_display": "活跃",
      "industry_type": "IT服务",
      "company_size": "medium",
      "company_size_display": "中型",
      "primary_contact_name": "张三",
      "primary_contact_phone": "13800138000",
      "primary_contact_email": "zhangsan@example.com",
      "created_at": "2025-05-15T09:30:00Z",
      "relation": {
        "id": 5,
        "role": "销售经理",
        "is_primary": true,
        "remarks": "负责销售和客户关系维护",
        "created_at": "2025-07-05T06:14:42.362927Z",
        "updated_at": "2025-07-05T06:14:42.362927Z"
      }
    },
    {
      "id": 10,
      "name": "优创数字科技有限公司",
      "type": "enterprise",
      "type_display": "公司",
      "value_level": "silver",
      "value_level_display": "白银",
      "status": "active",
      "status_display": "活跃",
      "industry_type": "软件开发",
      "company_size": "small",
      "company_size_display": "小型",
      "primary_contact_name": "张三",
      "primary_contact_phone": "13800138000",
      "primary_contact_email": "zhangsan@example.com",
      "created_at": "2025-06-10T14:20:00Z",
      "relation": {
        "id": 8,
        "role": "技术顾问",
        "is_primary": false,
        "remarks": "提供技术咨询服务",
        "created_at": "2025-07-05T06:16:42.362927Z",
        "updated_at": "2025-07-05T06:16:42.362927Z"
      }
    }
  ]
}
```

### 错误响应

#### 未提供联系人ID

```json
{
  "success": false,
  "code": 4000,
  "message": "请求参数错误",
  "data": {
    "error": "请提供联系人ID"
  }
}
```

#### 联系人不存在

```json
{
  "success": false,
  "code": 4004,
  "message": "资源不存在",
  "data": {
    "error": "联系人不存在"
  }
}
```

## 使用示例

### 获取客户下的所有联系人

```bash
curl -X GET "https://api.example.com/api/v1/customers/members/relations/customer-members/?customer_id=8" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

### 获取联系人所属的所有客户

```bash
curl -X GET "https://api.example.com/api/v1/customers/members/relations/member-customers/?member_id=15" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json"
```

## 注意事项

1. 这两个API都需要管理员权限才能访问
2. 返回的数据不包含分页信息，直接返回完整列表
3. 客户列表使用`CustomerListSerializer`序列化，只包含客户的基本信息
4. 联系人列表使用`MemberSerializer`序列化，包含联系人的详细信息 