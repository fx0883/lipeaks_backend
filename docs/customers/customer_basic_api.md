# 客户基础操作API

本文档详细说明了客户基础操作API的使用方法、请求参数和响应格式。

## 基础路径

所有客户基础操作API的基础路径为：`/api/v1/customers/`

## 认证与权限

- **认证方式**：JWT令牌认证，在请求头中添加 `Authorization: Bearer <your_jwt_token>`
- **权限要求**：需要管理员权限 (`IsAdmin`)

## API列表

### 1. 获取客户列表

获取系统中的客户列表，支持分页、排序和筛选。

- **URL**: `/api/v1/customers/`
- **方法**: `GET`
- **URL参数**:
  - `page`: 页码，默认为1
  - `page_size`: 每页记录数，默认为10
  - `ordering`: 排序字段，例如 `name` 或 `-created_at`（降序）
  - `type`: 按客户类型筛选
  - `value_level`: 按客户价值等级筛选
  - `status`: 按客户状态筛选
  - `company_size`: 按公司规模筛选
  - `industry_type`: 按行业类型筛选

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
        "count": 6,
        "next": null,
        "previous": null,
        "page_size": 10,
        "current_page": 1,
        "total_pages": 1
      },
      "results": [
        {
          "id": 7,
          "name": "示例科技有限公司",
          "type": "company",
          "value_level": "vip",
          "status": "active",
          "primary_contact_name": "李四",
          "primary_contact_phone": "13800138000",
          "industry_type": "信息技术",
          "company_size": "medium",
          "created_at": "2025-07-05T04:46:25.151963Z"
        },
        // 更多客户记录...
      ]
    }
  }
  ```

### 2. 获取客户详情

获取指定ID的客户详细信息。

- **URL**: `/api/v1/customers/{id}/`
- **方法**: `GET`
- **URL参数**:
  - `id`: 客户ID

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
  ```json
  {
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
      "id": 3,
      "name": "更新后的科技有限公司",
      "type": "company",
      "value_level": "vip",
      "status": "active",
      "business_license_number": "91110000123456789X",
      "tax_identification_number": "91110000123456789X",
      "registered_capital": "2000万元",
      "legal_representative": "李四",
      "registered_address": "北京市朝阳区建国门外大街1号",
      "business_address": "北京市朝阳区建国门外大街1号",
      "business_scope": "软件开发、技术咨询、技术服务、系统集成",
      "industry_type": "信息技术",
      "company_size": "large",
      "establishment_date": "2010-01-01",
      "website": "http://www.updated-example.com",
      "primary_contact_name": "王五",
      "primary_contact_phone": "13900139000",
      "primary_contact_email": "contact@updated-example.com",
      "bank_name": "中国工商银行",
      "bank_account": "6222020000123456790",
      "credit_rating": "AA",
      "payment_terms": "月结45天",
      "special_requirements": "需要7x24小时技术支持",
      "notes": "重要客户，需要重点关注",
      "source": "展会",
      "is_deleted": false,
      "created_at": "2025-07-05T03:51:28.884214Z",
      "updated_at": "2025-07-05T04:09:33.529616Z",
      "created_by": "string",
      "updated_by": "admin_cms"
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
    "message": "客户不存在"
  }
  ```

### 3. 创建客户

创建新的客户记录。

- **URL**: `/api/v1/customers/`
- **方法**: `POST`
- **请求体**:
  ```json
  {
    "name": "示例科技有限公司",
    "type": "company",
    "value_level": "vip",
    "status": "active",
    "business_license_number": "91110000123456789X",
    "tax_identification_number": "91110000123456789X",
    "registered_capital": "1000万元",
    "legal_representative": "张三",
    "registered_address": "北京市海淀区中关村南大街5号",
    "business_address": "北京市海淀区中关村南大街5号",
    "business_scope": "软件开发、技术咨询、技术服务",
    "industry_type": "信息技术",
    "company_size": "medium",
    "establishment_date": "2010-01-01",
    "website": "http://www.example.com",
    "primary_contact_name": "李四",
    "primary_contact_phone": "13800138000",
    "primary_contact_email": "contact@example.com",
    "bank_name": "中国银行",
    "bank_account": "6222020000123456789",
    "credit_rating": "A",
    "payment_terms": "月结30天",
    "special_requirements": "需要定期技术支持",
    "notes": "重要客户",
    "source": "展会"
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
      "id": 8,
      "name": "示例科技有限公司",
      "type": "company",
      "value_level": "vip",
      "status": "active",
      "business_license_number": "91110000123456789X",
      "tax_identification_number": "91110000123456789X",
      "registered_capital": "1000万元",
      "legal_representative": "张三",
      "registered_address": "北京市海淀区中关村南大街5号",
      "business_address": "北京市海淀区中关村南大街5号",
      "business_scope": "软件开发、技术咨询、技术服务",
      "industry_type": "信息技术",
      "company_size": "medium",
      "establishment_date": "2010-01-01",
      "website": "http://www.example.com",
      "primary_contact_name": "李四",
      "primary_contact_phone": "13800138000",
      "primary_contact_email": "contact@example.com",
      "bank_name": "中国银行",
      "bank_account": "6222020000123456789",
      "credit_rating": "A",
      "payment_terms": "月结30天",
      "special_requirements": "需要定期技术支持",
      "notes": "重要客户",
      "source": "展会",
      "is_deleted": false,
      "created_at": "2025-07-05T05:04:42.362927Z",
      "updated_at": "2025-07-05T05:04:42.362937Z",
      "created_by": "admin_cms",
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
      "name": ["客户名称已存在"],
      "primary_contact_phone": ["请输入有效的电话号码"]
    }
  }
  ```

### 4. 更新客户全部信息

更新指定ID的客户的全部信息。

- **URL**: `/api/v1/customers/{id}/`
- **方法**: `PUT`
- **URL参数**:
  - `id`: 客户ID
- **请求体**: 与创建客户相同的JSON结构，包含所有字段

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体: 与获取客户详情相同的JSON结构

- **错误响应**:
  - 状态码: `400 Bad Request` 或 `404 Not Found`
  - 响应体: 与创建客户或获取客户详情的错误响应相同

### 5. 部分更新客户信息

部分更新指定ID的客户信息。

- **URL**: `/api/v1/customers/{id}/`
- **方法**: `PATCH`
- **URL参数**:
  - `id`: 客户ID
- **请求体**: 仅包含需要更新的字段
  ```json
  {
    "status": "inactive",
    "notes": "已暂停合作"
  }
  ```

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体: 与获取客户详情相同的JSON结构，但包含更新后的字段值

- **错误响应**:
  - 状态码: `400 Bad Request` 或 `404 Not Found`
  - 响应体: 与创建客户或获取客户详情的错误响应相同

### 6. 删除客户

软删除指定ID的客户（将 `is_deleted` 标记为 `true`）。

- **URL**: `/api/v1/customers/{id}/`
- **方法**: `DELETE`
- **URL参数**:
  - `id`: 客户ID

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
    "message": "客户不存在"
  }
  ```

### 7. 搜索客户

根据关键词搜索客户。

- **URL**: `/api/v1/customers/search/`
- **方法**: `GET`
- **URL参数**:
  - `q`: 搜索关键词
  - `page`: 页码，默认为1
  - `page_size`: 每页记录数，默认为10

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
        "count": 1,
        "next": null,
        "previous": null,
        "page_size": 10,
        "current_page": 1,
        "total_pages": 1
      },
      "results": [
        {
          "id": 1,
          "name": "上海普全公司",
          "type": "company",
          "value_level": "normal",
          "status": "active",
          "business_license_number": "111",
          "tax_identification_number": "1",
          "registered_capital": "1",
          "legal_representative": "1",
          "registered_address": "洪山区大学园路4号麒麟社5栋802",
          "business_address": "1",
          "business_scope": "1",
          "industry_type": "1",
          "company_size": "small",
          "establishment_date": "2025-07-03",
          "website": "https://222.com",
          "primary_contact_name": "Feng Xuan",
          "primary_contact_phone": "13397159629",
          "primary_contact_email": "jackfeng8123@gmail.com",
          "bank_name": "1",
          "bank_account": "1",
          "credit_rating": "1",
          "payment_terms": "1",
          "special_requirements": "1",
          "notes": "1",
          "source": "hello",
          "is_deleted": false,
          "created_at": "2025-07-03T09:51:20.456142Z",
          "updated_at": "2025-07-03T09:51:20.456152Z",
          "created_by": "admin",
          "updated_by": "admin"
        }
      ]
    }
  }
  ```

### 8. 获取客户统计数据

获取客户的统计数据，包括总数、按状态分类、按类型分类、按价值等级分类、按公司规模分类等。

- **URL**: `/api/v1/customers/statistics/`
- **方法**: `GET`

- **成功响应**:
  - 状态码: `200 OK`
  - 响应体:
  ```json
  {
    "success": true,
    "code": 2000,
    "message": "操作成功",
    "data": {
      "total_count": 6,
      "active_count": 5,
      "inactive_count": 1,
      "potential_count": 0,
      "lost_count": 0,
      "by_type": {
        "company": 6
      },
      "by_value_level": {
        "normal": 2,
        "vip": 4
      },
      "by_company_size": {
        "small": 1,
        "None": 1,
        "large": 2,
        "medium": 2
      }
    }
  }
  ```

## 字段说明

| 字段名 | 类型 | 必填 | 描述 |
| --- | --- | --- | --- |
| name | 字符串 | 是 | 客户名称，唯一 |
| type | 字符串 | 是 | 客户类型，如 company（公司）、individual（个人） |
| value_level | 字符串 | 是 | 客户价值等级，如 normal（普通）、vip（重要）、strategic（战略） |
| status | 字符串 | 是 | 客户状态，如 active（活跃）、inactive（非活跃）、potential（潜在）、lost（流失） |
| business_license_number | 字符串 | 否 | 营业执照号码 |
| tax_identification_number | 字符串 | 否 | 税务登记号 |
| registered_capital | 字符串 | 否 | 注册资本 |
| legal_representative | 字符串 | 否 | 法定代表人 |
| registered_address | 字符串 | 否 | 注册地址 |
| business_address | 字符串 | 否 | 经营地址 |
| business_scope | 字符串 | 否 | 经营范围 |
| industry_type | 字符串 | 否 | 行业类型 |
| company_size | 字符串 | 否 | 公司规模，如 small（小型）、medium（中型）、large（大型） |
| establishment_date | 日期 | 否 | 成立日期 |
| website | 字符串 | 否 | 网站 |
| primary_contact_name | 字符串 | 否 | 主要联系人姓名 |
| primary_contact_phone | 字符串 | 否 | 主要联系人电话 |
| primary_contact_email | 字符串 | 否 | 主要联系人邮箱 |
| bank_name | 字符串 | 否 | 开户银行 |
| bank_account | 字符串 | 否 | 银行账号 |
| credit_rating | 字符串 | 否 | 信用评级 |
| payment_terms | 字符串 | 否 | 付款条件 |
| special_requirements | 字符串 | 否 | 特殊要求 |
| notes | 字符串 | 否 | 备注 |
| source | 字符串 | 否 | 客户来源 |
| is_deleted | 布尔值 | 否 | 是否已删除，默认为 false |
| created_at | 日期时间 | 否 | 创建时间，自动生成 |
| updated_at | 日期时间 | 否 | 更新时间，自动生成 |
| created_by | 字符串 | 否 | 创建者，自动填充当前用户 |
| updated_by | 字符串 | 否 | 更新者，自动填充当前用户 | 