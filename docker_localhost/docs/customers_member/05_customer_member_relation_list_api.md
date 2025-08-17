# 客户-联系人关系列表API

本文档描述了两个关于客户与联系人（成员）之间关系的列表查询API：
1. 获取客户下的所有联系人列表
2. 获取联系人所属的所有客户列表

以及两个批量删除关系的API：
1. 删除客户与多个联系人的关系
2. 删除联系人与多个客户的关系

## API端点

客户-联系人关系API的基础URL为：`/api/v1/customers/members/relations/`

## 1. 获取客户下的所有联系人列表

获取指定客户ID下的所有联系人列表，同时返回联系人与客户的关系信息。

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
[
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
```

### 错误响应

#### 未提供客户ID

```json
{
  "error": "请提供客户ID"
}
```

#### 客户不存在

```json
{
  "error": "客户不存在"
}
```

## 2. 获取联系人所属的所有客户列表

获取指定联系人ID所属的所有客户列表，同时返回客户与联系人的关系信息。

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
[
  {
    "id": 8,
    "name": "示例科技有限公司",
    "type": "company",
    "value_level": "vip",
    "status": "active",
    "primary_contact_name": "张三",
    "primary_contact_phone": "13800138000",
    "primary_contact_email": "zhangsan@example.com",
    "created_at": "2025-05-20T14:30:00Z",
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
    "id": 9,
    "name": "测试有限公司",
    "type": "company",
    "value_level": "normal",
    "status": "active",
    "primary_contact_name": "李四",
    "primary_contact_phone": "13900139000",
    "primary_contact_email": "lisi@example.com",
    "created_at": "2025-05-25T09:45:00Z",
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
```

### 错误响应

#### 未提供联系人ID

```json
{
  "error": "请提供联系人ID"
}
```

#### 联系人不存在

```json
{
  "error": "联系人不存在"
}
```

## 3. 删除客户与多个联系人的关系

删除指定客户与多个联系人之间的关系。

### 请求

- **方法**: `POST`
- **URL**: `/api/v1/customers/members/relations/customer-members/delete/`
- **权限**: 管理员
- **Content-Type**: `application/json`

### 请求体

```json
{
  "customer_id": 8,
  "member_ids": [15, 16, 17]
}
```

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| customer_id | int | 是 | 客户ID |
| member_ids | array | 是 | 联系人ID列表 |

### 响应

- **状态码**: `204 No Content`

### 错误响应

#### 未提供客户ID

```json
{
  "error": "请提供客户ID"
}
```

#### 未提供联系人ID列表

```json
{
  "error": "请提供联系人ID列表"
}
```

#### 客户不存在

```json
{
  "error": "客户不存在"
}
```

#### 服务器错误

```json
{
  "error": "删除关系时发生错误"
}
```

## 4. 删除联系人与多个客户的关系

删除指定联系人与多个客户之间的关系。

### 请求

- **方法**: `POST`
- **URL**: `/api/v1/customers/members/relations/member-customers/delete/`
- **权限**: 管理员
- **Content-Type**: `application/json`

### 请求体

```json
{
  "member_id": 15,
  "customer_ids": [8, 9, 10]
}
```

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| member_id | int | 是 | 联系人ID |
| customer_ids | array | 是 | 客户ID列表 |

### 响应

- **状态码**: `204 No Content`

### 错误响应

#### 未提供联系人ID

```json
{
  "error": "请提供联系人ID"
}
```

#### 未提供客户ID列表

```json
{
  "error": "请提供客户ID列表"
}
```

#### 联系人不存在

```json
{
  "error": "联系人不存在"
}
```

#### 服务器错误

```json
{
  "error": "删除关系时发生错误"
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