# 客户-联系人关系API

本文档详细说明了客户-联系人关系API的使用方法、请求参数和响应格式。客户-联系人关系API用于管理客户与联系人（Member）之间的关系。

## 基础路径

所有客户-联系人关系API的基础路径为：`/api/v1/customers/members/relations/`

## 认证与权限

- **认证方式**：JWT令牌认证，在请求头中添加 `Authorization: Bearer <your_jwt_token>`
- **权限要求**：需要管理员权限 (`IsAdmin`)

## API列表

### 1. 获取客户的联系人关系列表

获取客户与联系人之间的关系列表，支持分页、排序和筛选。

- **URL**: `/api/v1/customers/members/relations/`
- **方法**: `GET`
- **URL参数**:
  - `page`: 页码，默认为1
  - `page_size`: 每页记录数，默认为10
  - `ordering`: 排序字段，例如 `created_at` 或 `-created_at`（降序）
  - `customer_id`: 按客户ID筛选
  - `member_id`: 按联系人ID筛选
  - `is_primary`: 按是否为主要联系人筛选（true/false）
  - `role`: 按联系人角色筛选

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
  ```json
  {
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
      "pagination": {
        "count": 5,
        "next": null,
        "previous": null,
        "page_size": 10,
        "current_page": 1,
        "total_pages": 1
      },
      "results": [
        {
          "id": 1,
          "customer": {
            "id": 1,
            "name": "上海普全公司"
          },
          "member": {
            "id": 1,
            "username": "member1",
            "name": "张三",
            "phone": "13800138000",
            "email": "zhangsan@example.com"
          },
          "role": "decision_maker",
          "position": "CEO",
          "is_primary": true,
          "notes": "主要决策者",
          "created_at": "2025-07-03T10:00:00.000000Z"
        },
        {
          "id": 2,
          "customer": {
            "id": 1,
            "name": "上海普全公司"
          },
          "member": {
            "id": 2,
            "username": "member2",
            "name": "李四",
            "phone": "13900139000",
            "email": "lisi@example.com"
          },
          "role": "technical_contact",
          "position": "CTO",
          "is_primary": false,
          "notes": "技术联系人",
          "created_at": "2025-07-03T10:05:00.000000Z"
        }
        // 更多关系记录...
      ]
    }
  }
  ```

### 2. 添加客户与联系人的关系

创建客户与联系人之间的新关系。

- **URL**: `/api/v1/customers/members/relations/`
- **方法**: `POST`
- **请求体**:
  ```json
  {
    "customer_id": 1,
    "member_id": 3,
    "role": "financial_contact",
    "position": "CFO",
    "is_primary": false,
    "remarks": "财务联系人，负责合同审批"
  }
  ```

- **成功响应**:
  - 状态码: `201 Created`
  - 响应体:
  ```json
  {
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
      "id": 3,
      "customer": {
        "id": 1,
        "name": "上海普全公司"
      },
      "member": {
        "id": 3,
        "username": "member3",
        "name": "王五",
        "phone": "13700137000",
        "email": "wangwu@example.com"
      },
      "role": "financial_contact",
      "position": "CFO",
      "is_primary": false,
      "remarks": "财务联系人，负责合同审批",
      "created_at": "2025-07-05T05:20:00.000000Z",
      "updated_at": "2025-07-05T05:20:00.000000Z",
      "created_by": "admin",
      "updated_by": null
    }
  }
  ```

- **错误响应**:
  - 状态码: `400 Bad Request`
  - 响应体:
  ```json
  {
    "success": false,
    "code": 4000,
    "message": "请求参数错误",
    "errors": {
      "customer_id": ["客户不存在"],
      "member_id": ["联系人不存在"],
      "role": ["此字段为必填项"]
    }
  }
  ```

  - 状态码: `409 Conflict`
  - 响应体:
  ```json
  {
    "success": false,
    "code": 4090,
    "message": "关系已存在",
    "errors": {
      "non_field_errors": ["该客户与联系人的关系已存在"]
    }
  }
  ```

### 3. 获取特定客户-联系人关系详情

获取指定ID的客户-联系人关系详情。

- **URL**: `/api/v1/customers/members/relations/{id}/`
- **方法**: `GET`
- **URL参数**:
  - `id`: 关系ID

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
  ```json
  {
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
      "id": 1,
      "customer": {
        "id": 1,
        "name": "上海普全公司"
      },
      "member": {
        "id": 1,
        "username": "member1",
        "name": "张三",
        "phone": "13800138000",
        "email": "zhangsan@example.com"
      },
      "role": "decision_maker",
      "position": "CEO",
      "is_primary": true,
      "remarks": "主要决策者，负责最终签字",
      "created_at": "2025-07-03T10:00:00.000000Z",
      "updated_at": "2025-07-03T10:00:00.000000Z",
      "created_by": "admin",
      "updated_by": null
    }
  }
  ```

- **错误响应**:
  - 状态码: `404 Not Found`
  - 响应体:
  ```json
  {
    "success": false,
    "code": 4004,
    "message": "关系不存在"
  }
  ```

### 4. 更新客户-联系人关系

更新指定ID的客户-联系人关系。

- **URL**: `/api/v1/customers/members/relations/{id}/`
- **方法**: `PUT`
- **URL参数**:
  - `id`: 关系ID
- **请求体**:
  ```json
  {
    "role": "decision_maker",
    "position": "董事长",
    "is_primary": true,
    "remarks": "最终决策者，全面负责项目"
  }
  ```

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
  ```json
  {
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
      "id": 1,
      "customer": {
        "id": 1,
        "name": "上海普全公司"
      },
      "member": {
        "id": 1,
        "username": "member1",
        "name": "张三",
        "phone": "13800138000",
        "email": "zhangsan@example.com"
      },
      "role": "decision_maker",
      "position": "董事长",
      "is_primary": true,
      "remarks": "最终决策者，全面负责项目",
      "created_at": "2025-07-03T10:00:00.000000Z",
      "updated_at": "2025-07-05T05:25:00.000000Z",
      "created_by": "admin",
      "updated_by": "admin"
    }
  }
  ```

- **错误响应**:
  - 状态码: `400 Bad Request` 或 `404 Not Found`
  - 响应体: 与创建关系或获取关系详情的错误响应相同

### 5. 删除客户-联系人关系

删除指定ID的客户-联系人关系。

- **URL**: `/api/v1/customers/members/relations/{id}/`
- **方法**: `DELETE`
- **URL参数**:
  - `id`: 关系ID

- **成功响应**:
  - 状态码: `204 No Content`
  - 响应体: 无

- **错误响应**:
  - 状态码: `404 Not Found`
  - 响应体:
  ```json
  {
    "success": false,
    "code": 4004,
    "message": "关系不存在"
  }
  ```

  - 状态码: `400 Bad Request`
  - 响应体:
  ```json
  {
    "success": false,
    "code": 4000,
    "message": "无法删除主要联系人关系",
    "errors": {
      "non_field_errors": ["无法删除主要联系人关系，请先设置其他联系人为主要联系人"]
    }
  }
  ```

### 6. 设置主要联系人

将指定ID的客户-联系人关系设置为主要联系人关系。

- **URL**: `/api/v1/customers/members/relations/{id}/set-primary/`
- **方法**: `POST`
- **URL参数**:
  - `id`: 关系ID

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
  ```json
  {
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
      "id": 2,
      "customer": {
        "id": 1,
        "name": "上海普全公司"
      },
      "member": {
        "id": 2,
        "username": "member2",
        "name": "李四",
        "phone": "13900139000",
        "email": "lisi@example.com"
      },
      "role": "technical_contact",
      "position": "CTO",
      "is_primary": true,
      "remarks": "技术联系人，负责技术对接",
      "created_at": "2025-07-03T10:05:00.000000Z",
      "updated_at": "2025-07-05T05:30:00.000000Z",
      "created_by": "admin",
      "updated_by": "admin"
    }
  }
  ```

- **错误响应**:
  - 状态码: `404 Not Found`
  - 响应体:
  ```json
  {
    "success": false,
    "code": 4004,
    "message": "关系不存在"
  }
  ```

### 7. 获取客户的主要联系人

获取指定客户的主要联系人关系。

- **URL**: `/api/v1/customers/members/relations/primary/`
- **方法**: `GET`
- **URL参数**:
  - `customer_id`: 客户ID

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
  ```json
  {
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
      "id": 2,
      "customer": {
        "id": 1,
        "name": "上海普全公司"
      },
      "member": {
        "id": 2,
        "username": "member2",
        "name": "李四",
        "phone": "13900139000",
        "email": "lisi@example.com"
      },
      "role": "technical_contact",
      "position": "CTO",
      "is_primary": true,
      "remarks": "技术联系人，负责技术对接",
      "created_at": "2025-07-03T10:05:00.000000Z",
      "updated_at": "2025-07-05T05:30:00.000000Z",
      "created_by": "admin",
      "updated_by": "admin"
    }
  }
  ```

- **错误响应**:
  - 状态码: `404 Not Found`
  - 响应体:
  ```json
  {
    "success": false,
    "code": 4004,
    "message": "未找到主要联系人"
  }
  ```

  - 状态码: `400 Bad Request`
  - 响应体:
  ```json
  {
    "success": false,
    "code": 4000,
    "message": "请求参数错误",
    "errors": {
      "customer_id": ["此字段为必填项"]
    }
  }
  ```

## 字段说明

| 字段名 | 类型 | 必填 | 描述 |
| --- | --- | --- | --- |
| customer_id | 整数 | 是 | 客户ID |
| member_id | 整数 | 是 | 联系人ID |
| role | 字符串 | 是 | 联系人角色，如 decision_maker（决策者）、technical_contact（技术联系人）、financial_contact（财务联系人）等 |
| position | 字符串 | 否 | 联系人职位 |
| is_primary | 布尔值 | 否 | 是否为主要联系人，默认为 false |
| remarks | 字符串 | 否 | 关于该联系人与客户关系的补充说明 |
| created_at | 日期时间 | 否 | 创建时间，自动生成 |
| updated_at | 日期时间 | 否 | 更新时间，自动生成 |
| created_by | 字符串 | 否 | 创建者，自动填充当前用户 |
| updated_by | 字符串 | 否 | 更新者，自动填充当前用户 |

## 注意事项

1. **主要联系人**：每个客户只能有一个主要联系人。当设置一个联系人为主要联系人时，系统会自动将该客户的其他联系人设置为非主要联系人。

2. **删除限制**：无法直接删除主要联系人关系。如果需要删除主要联系人关系，请先将其他联系人设置为主要联系人，或者将该关系的 `is_primary` 设置为 `false`。

3. **联系人信息同步**：当创建或更新客户-联系人关系时，系统会自动将主要联系人的姓名和电话同步到客户记录的 `primary_contact_name` 和 `primary_contact_phone` 字段。

4. **角色枚举值**：联系人角色（`role`）字段支持以下枚举值：
   - `decision_maker`：决策者
   - `technical_contact`：技术联系人
   - `financial_contact`：财务联系人
   - `business_contact`：业务联系人
   - `administrative_contact`：行政联系人
   - `other`：其他 