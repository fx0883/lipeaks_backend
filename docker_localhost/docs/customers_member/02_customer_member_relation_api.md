# 客户-联系人关系API

本文档描述客户与联系人（成员）之间关系管理的API，包括获取客户的联系人列表、创建联系人关系、更新联系人关系和设置主要联系人等功能。

## API端点

所有客户-联系人关系API的基础URL为：`/api/v1/customers/members/relations/`

## 1. 获取客户的联系人关系列表

获取指定客户的所有联系人关系。

### 请求

- **方法**: `GET`
- **URL**: `/api/v1/customers/members/relations/`
- **权限**: 管理员

### 查询参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| customer_id | int | 否 | 客户ID，用于筛选特定客户的联系人关系 |
| page | int | 否 | 页码，默认为1 |
| limit | int | 否 | 每页记录数，默认为10 |

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "pagination": {
      "count": 2,
      "next": null,
      "previous": null,
      "page_size": 10,
      "current_page": 1,
      "total_pages": 1
    },
    "results": [
      {
        "id": 5,
        "customer_id": 8,
        "customer_name": "示例科技有限公司",
        "member_id": 15,
        "member_name": "张三",
        "member_email": "zhangsan@example.com",
        "member_phone": "13800138000",
        "role": "销售经理",
        "is_primary": true,
        "created_at": "2025-07-05T06:14:42.362927Z",
        "updated_at": "2025-07-05T06:14:42.362927Z"
      },
      {
        "id": 6,
        "customer_id": 8,
        "customer_name": "示例科技有限公司",
        "member_id": 16,
        "member_name": "李四",
        "member_email": "lisi@example.com",
        "member_phone": "13900139000",
        "role": "技术支持",
        "is_primary": false,
        "created_at": "2025-07-05T06:15:42.362927Z",
        "updated_at": "2025-07-05T06:15:42.362927Z"
      }
    ]
  }
}
```

## 2. 获取客户-联系人关系详情

获取指定ID的客户-联系人关系详情。

### 请求

- **方法**: `GET`
- **URL**: `/api/v1/customers/members/relations/{id}/`
- **权限**: 管理员

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| id | int | 是 | 客户-联系人关系ID |

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 6,
    "customer_id": 8,
    "customer_name": "示例科技有限公司",
    "member_id": 16,
    "member_name": "李四",
    "member_email": "lisi@example.com",
    "member_phone": "13900139000",
    "role": "技术支持",
    "is_primary": true,
    "remarks": "负责技术对接和问题解决",
    "created_at": "2025-07-05T06:15:42.362927Z",
    "updated_at": "2025-07-05T06:15:42.362927Z"
  }
}
```

## 3. 创建客户-联系人关系

为客户添加新的联系人关系。

### 请求

- **方法**: `POST`
- **URL**: `/api/v1/customers/members/relations/`
- **权限**: 管理员
- **Content-Type**: `application/json`

### 请求体

```json
{
  "customer_id": 8,
  "member_id": 17,
  "role": "财务联系人",
  "is_primary": false,
  "remarks": "负责合同审批和付款事宜"
}
```

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 7,
    "customer_id": 8,
    "customer_name": "示例科技有限公司",
    "member_id": 17,
    "member_name": "王五",
    "member_email": "wangwu@example.com",
    "member_phone": "13700137000",
    "role": "财务联系人",
    "is_primary": false,
    "remarks": "负责合同审批和付款事宜",
    "created_at": "2025-07-10T08:15:30.123456Z",
    "updated_at": "2025-07-10T08:15:30.123456Z"
  }
}
```

## 4. 更新客户-联系人关系

更新指定ID的客户-联系人关系。

### 请求

- **方法**: `PUT`
- **URL**: `/api/v1/customers/members/relations/{id}/`
- **权限**: 管理员
- **Content-Type**: `application/json`

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| id | int | 是 | 客户-联系人关系ID |

### 请求体

```json
{
  "role": "财务总监",
  "is_primary": false,
  "remarks": "负责财务审批，可以直接联系"
}
```

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 7,
    "customer_id": 8,
    "customer_name": "示例科技有限公司",
    "member_id": 17,
    "member_name": "王五",
    "member_email": "wangwu@example.com",
    "member_phone": "13700137000",
    "role": "财务总监",
    "is_primary": false,
    "remarks": "负责财务审批，可以直接联系",
    "created_at": "2025-07-10T08:15:30.123456Z",
    "updated_at": "2025-07-10T09:20:15.123456Z"
  }
}
```

## 5. 部分更新客户-联系人关系

部分更新指定ID的客户-联系人关系。

### 请求

- **方法**: `PATCH`
- **URL**: `/api/v1/customers/members/relations/{id}/`
- **权限**: 管理员
- **Content-Type**: `application/json`

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| id | int | 是 | 客户-联系人关系ID |

### 请求体

```json
{
  "role": "财务总监",
  "remarks": "新任财务总监，负责所有财务决策"
}
```

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 7,
    "customer_id": 8,
    "customer_name": "示例科技有限公司",
    "member_id": 17,
    "member_name": "王五",
    "member_email": "wangwu@example.com",
    "member_phone": "13700137000",
    "role": "财务总监",
    "is_primary": false,
    "remarks": "新任财务总监，负责所有财务决策",
    "created_at": "2025-07-10T08:15:30.123456Z",
    "updated_at": "2025-07-10T09:20:15.123456Z"
  }
}
```

## 6. 删除客户-联系人关系

删除指定ID的客户-联系人关系。

### 请求

- **方法**: `DELETE`
- **URL**: `/api/v1/customers/members/relations/{id}/`
- **权限**: 管理员

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| id | int | 是 | 客户-联系人关系ID |

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "删除成功",
  "data": null
}
```

## 7. 设置主要联系人

将指定的联系人设置为客户的主要联系人。

### 请求

- **方法**: `POST`
- **URL**: `/api/v1/customers/members/relations/{id}/set-primary/`
- **权限**: 管理员

### 路径参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| id | int | 是 | 客户-联系人关系ID |

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 6,
    "customer_id": 8,
    "customer_name": "示例科技有限公司",
    "member_id": 16,
    "member_name": "李四",
    "member_email": "lisi@example.com",
    "member_phone": "13900139000",
    "role": "技术支持",
    "is_primary": true,
    "remarks": "主要技术联系人，负责所有技术对接",
    "created_at": "2025-07-05T06:15:42.362927Z",
    "updated_at": "2025-07-10T10:30:45.123456Z"
  }
}
```

## 8. 获取客户的主要联系人

获取指定客户的主要联系人。

### 请求

- **方法**: `GET`
- **URL**: `/api/v1/customers/members/relations/primary/`
- **权限**: 管理员

### 查询参数

| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| customer_id | int | 是 | 客户ID |

### 响应

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "id": 6,
    "customer_id": 8,
    "customer_name": "示例科技有限公司",
    "member_id": 16,
    "member_name": "李四",
    "member_email": "lisi@example.com",
    "member_phone": "13900139000",
    "role": "技术支持",
    "is_primary": true,
    "remarks": "主要技术联系人，负责所有技术对接",
    "created_at": "2025-07-05T06:15:42.362927Z",
    "updated_at": "2025-07-10T10:30:45.123456Z"
  }
}
```

## 错误响应示例

### 1. 客户ID不存在

```json
{
  "success": false,
  "code": 4004,
  "message": "未找到主要联系人",
  "data": null
}
```

### 2. 缺少必要参数

```json
{
  "success": false,
  "code": 4000,
  "message": "请提供客户ID",
  "data": null
}
```

## 数据模型

### 客户-联系人关系字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| id | int | 关系ID |
| customer_id | int | 客户ID |
| customer_name | string | 客户名称 |
| member_id | int | 联系人(成员)ID |
| member_name | string | 联系人姓名 |
| member_email | string | 联系人邮箱 |
| member_phone | string | 联系人电话 |
| role | string | 联系人在客户中的角色 |
| is_primary | boolean | 是否为主要联系人 |
| remarks | string | 关于该联系人与客户关系的补充说明 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 | 