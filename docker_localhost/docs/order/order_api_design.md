# 普全订单管理系统API设计文档

## 1. 概述

本文档定义普全订单管理系统的API接口设计，用于支持前后端分离架构下的数据交互。API设计遵循RESTful风格，使用标准HTTP方法表示增删改查操作，使用JSON格式进行数据交换。

## 2. 基础信息

- 基础路径: `/api/v1/orders`
- 认证方式: JWT Token认证
- 数据格式: JSON
- 状态码:
  - 200: 成功
  - 201: 创建成功
  - 400: 请求参数错误
  - 401: 未认证
  - 403: 权限不足
  - 404: 资源不存在
  - 500: 服务器内部错误

## 3. API接口设计

### 3.1 订单基础操作API

#### 3.1.1 获取订单列表

- **请求**:
  - 方法: `GET`
  - URL: `/api/v1/orders/`
  - 权限要求: 需要认证和查看订单权限
  - 查询参数:
    - `page`: 页码，默认1
    - `page_size`: 每页数量，默认20
    - `customer`: 客户ID筛选
    - `status`: 订单状态筛选
    - `service_type`: 服务类型筛选
    - `payment_status`: 支付状态筛选
    - `start_date_from`: 开始日期范围(起)
    - `start_date_to`: 开始日期范围(止)
    - `due_date_from`: 截止日期范围(起)
    - `due_date_to`: 截止日期范围(止)
    - `created_at_from`: 创建日期范围(起)
    - `created_at_to`: 创建日期范围(止)
    - `search`: 搜索关键词(订单编号、客户名称、译员等)
    - `ordering`: 排序字段，支持`created_at`,`start_date`,`due_date`,`total_amount`等，前缀`-`表示降序

- **响应**:
  - 状态码: 200
  - 响应体示例:
    ```json
    {
      "count": 150,
      "next": "http://api.example.com/api/v1/orders/?page=2",
      "previous": null,
      "results": [
        {
          "id": 123,
          "order_number": "PQ-202508-1234",
          "customer": {
            "id": 1,
            "name": "ABC科技有限公司"
          },
          "status": "draft",
          "service_type": "翻译",
          "language_direction": "英译中",
          "word_count": 5000,
          "total_amount": 400.00,
          "payment_status": "unpaid",
          "start_date": "2025-08-01",
          "due_date": "2025-08-15",
          "created_at": "2025-07-20T10:30:00Z"
        },
        // 更多订单...
      ]
    }
    ```

#### 3.1.2 创建订单

- **请求**:
  - 方法: `POST`
  - URL: `/api/v1/orders/`
  - 内容类型: `application/json`
  - 权限要求: 需要认证和创建订单权限
  - 请求体示例:
    ```json
    {
      "customer": 1,
      "customer_contact": 2,
      "service_type": "翻译",
      "language_direction": "英译中",
      "translator": "张三",
      "word_count": 5000,
      "unit_price": 0.08,
      "description": "技术文档翻译",
      "start_date": "2025-08-01",
      "due_date": "2025-08-15",
      "remarks": "客户要求技术术语准确"
    }
    ```

- **响应**:
  - 状态码: 201
  - 响应体示例:
    ```json
    {
      "id": 123,
      "order_number": "PQ-202508-1234",
      "customer": {
        "id": 1,
        "name": "ABC科技有限公司"
      },
      "customer_contact": {
        "id": 2,
        "name": "李四"
      },
      "service_type": "翻译",
      "language_direction": "英译中",
      "translator": "张三",
      "word_count": 5000,
      "unit_price": 0.08,
      "total_amount": 400.00,
      "status": "draft",
      "description": "技术文档翻译",
      "start_date": "2025-08-01",
      "due_date": "2025-08-15",
      "remarks": "客户要求技术术语准确",
      "created_at": "2025-07-20T10:30:00Z",
      "created_by": {
        "id": 5,
        "name": "王五"
      }
    }
    ```

#### 3.1.3 获取订单详情

- **请求**:
  - 方法: `GET`
  - URL: `/api/v1/orders/{id}/`
  - 权限要求: 需要认证和查看订单权限

- **响应**:
  - 状态码: 200
  - 响应体示例:
    ```json
    {
      "id": 123,
      "order_number": "PQ-202508-1234",
      "customer": {
        "id": 1,
        "name": "ABC科技有限公司"
      },
      "customer_contact": {
        "id": 2,
        "name": "李四",
        "email": "lisi@example.com",
        "phone": "13800138000"
      },
      "service_type": "翻译",
      "language_direction": "英译中",
      "translator": "张三",
      "word_count": 5000,
      "description": "技术文档翻译",
      "start_date": "2025-08-01",
      "due_date": "2025-08-15",
      "delivery_date": null,
      "unit_price": 0.08,
      "total_amount": 400.00,
      "translator_fee": 200.00,
      "other_costs": 50.00,
      "payment_status": "unpaid",
      "payment_date": null,
      "payment_method": null,
      "payment_remarks": null,
      "invoice_status": "not_required",
      "invoice_info": null,
      "contract_number": null,
      "contract_info": null,
      "remarks": "客户要求技术术语准确",
      "attachments": null,
      "tags": null,
      "status": "draft",
      "created_at": "2025-07-20T10:30:00Z",
      "updated_at": "2025-07-20T10:30:00Z",
      "created_by": {
        "id": 5,
        "name": "王五"
      }
    }
    ```

#### 3.1.4 更新订单

- **请求**:
  - 方法: `PATCH` (部分更新) 或 `PUT` (完整更新)
  - URL: `/api/v1/orders/{id}/`
  - 内容类型: `application/json`
  - 权限要求: 需要认证和更新订单权限
  - 请求体示例(PATCH):
    ```json
    {
      "status": "in_progress",
      "word_count": 5500,
      "unit_price": 0.085,
      "translator_fee": 220.00
    }
    ```

- **响应**:
  - 状态码: 200
  - 响应体示例:
    ```json
    {
      "id": 123,
      "order_number": "PQ-202508-1234",
      "status": "in_progress",
      "word_count": 5500,
      "unit_price": 0.085,
      "total_amount": 467.50,
      "translator_fee": 220.00,
      // ... 其他字段 ...
      "updated_at": "2025-07-21T15:30:00Z"
    }
    ```

#### 3.1.5 删除订单

- **请求**:
  - 方法: `DELETE`
  - URL: `/api/v1/orders/{id}/`
  - 权限要求: 需要认证和删除订单权限

- **响应**:
  - 状态码: 204 (无内容)

### 3.2 订单历史记录API

#### 3.2.1 获取订单历史记录列表

- **请求**:
  - 方法: `GET`
  - URL: `/api/v1/orders/{order_id}/history/`
  - 权限要求: 需要认证和查看订单权限
  - 查询参数:
    - `page`: 页码，默认1
    - `page_size`: 每页数量，默认20

- **响应**:
  - 状态码: 200
  - 响应体示例:
    ```json
    {
      "count": 3,
      "next": null,
      "previous": null,
      "results": [
        {
          "id": 456,
          "order_id": 123,
          "version": 3,
          "modified_by": {
            "id": 5,
            "name": "王五"
          },
          "modified_at": "2025-07-21T15:30:00Z",
          "change_details": {
            "status": {
              "old": "draft",
              "new": "in_progress"
            },
            "word_count": {
              "old": 5000,
              "new": 5500
            },
            "unit_price": {
              "old": 0.08,
              "new": 0.085
            },
            "total_amount": {
              "old": 400.00,
              "new": 467.50
            },
            "translator_fee": {
              "old": 200.00,
              "new": 220.00
            }
          }
        },
        // 更多历史版本...
      ]
    }
    ```

#### 3.2.2 获取订单历史版本详情

- **请求**:
  - 方法: `GET`
  - URL: `/api/v1/orders/{order_id}/history/{version}/`
  - 权限要求: 需要认证和查看订单权限

- **响应**:
  - 状态码: 200
  - 响应体示例:
    ```json
    {
      "id": 456,
      "order_id": 123,
      "version": 3,
      "modified_by": {
        "id": 5,
        "name": "王五"
      },
      "modified_at": "2025-07-21T15:30:00Z",
      "change_details": {
        "status": {
          "old": "draft",
          "new": "in_progress"
        },
        "word_count": {
          "old": 5000,
          "new": 5500
        },
        // ... 其他变更字段 ...
      },
      "snapshot": {
        "id": 123,
        "order_number": "PQ-202508-1234",
        "status": "in_progress",
        "word_count": 5500,
        // ... 该版本的完整订单数据 ...
      }
    }
    ```

#### 3.2.3 比较订单版本

- **请求**:
  - 方法: `GET`
  - URL: `/api/v1/orders/{order_id}/history/compare/`
  - 权限要求: 需要认证和查看订单权限
  - 查询参数:
    - `version1`: 第一个版本号
    - `version2`: 第二个版本号

- **响应**:
  - 状态码: 200
  - 响应体示例:
    ```json
    {
      "order_id": 123,
      "order_number": "PQ-202508-1234",
      "version1": 1,
      "version2": 3,
      "differences": {
        "status": {
          "version1": "draft",
          "version2": "in_progress"
        },
        "word_count": {
          "version1": 5000,
          "version2": 5500
        },
        "unit_price": {
          "version1": 0.08,
          "version2": 0.085
        },
        "total_amount": {
          "version1": 400.00,
          "version2": 467.50
        },
        "translator_fee": {
          "version1": 200.00,
          "version2": 220.00
        }
      }
    }
    ```

#### 3.2.4 还原到历史版本

- **请求**:
  - 方法: `POST`
  - URL: `/api/v1/orders/{order_id}/history/{version}/restore/`
  - 权限要求: 需要认证和更新订单权限
  - 请求体示例:
    ```json
    {
      "remarks": "恢复到之前版本，因为最近的修改有误"
    }
    ```

- **响应**:
  - 状态码: 200
  - 响应体示例:
    ```json
    {
      "id": 123,
      "order_number": "PQ-202508-1234",
      "status": "draft",
      "word_count": 5000,
      // ... 还原后的订单完整信息 ...
      "updated_at": "2025-07-22T10:15:00Z",
      "restored_from_version": 1
    }
    ```

### 3.3 订单高级功能API

#### 3.3.1 导出订单数据

- **请求**:
  - 方法: `GET`
  - URL: `/api/v1/orders/export/`
  - 权限要求: 需要认证和导出订单权限
  - 查询参数:
    - `format`: 导出格式，可选值: `excel`, `pdf`, `csv`，默认`excel`
    - `ids`: 订单ID列表，多个ID以逗号分隔，如果不提供则导出筛选结果
    - 其他筛选参数: 同获取订单列表的筛选参数

- **响应**:
  - 状态码: 200
  - 内容类型: 根据请求的格式，可能是`application/vnd.ms-excel`, `application/pdf`或`text/csv`
  - 响应体: 文件内容

#### 3.3.2 导入订单数据

- **请求**:
  - 方法: `POST`
  - URL: `/api/v1/orders/import/`
  - 内容类型: `multipart/form-data`
  - 权限要求: 需要认证和导入订单权限
  - 表单数据:
    - `file`: Excel文件
    - `update_existing`: 是否更新已存在的订单，布尔值，默认`false`

- **响应**:
  - 状态码: 200
  - 响应体示例:
    ```json
    {
      "status": "success",
      "total_records": 10,
      "created": 8,
      "updated": 2,
      "failed": 0,
      "errors": []
    }
    ```

#### 3.3.3 获取订单统计数据

- **请求**:
  - 方法: `GET`
  - URL: `/api/v1/orders/statistics/`
  - 权限要求: 需要认证和查看统计权限
  - 查询参数:
    - `period`: 统计周期，可选值: `daily`, `weekly`, `monthly`, `yearly`，默认`monthly`
    - `start_date`: 开始日期
    - `end_date`: 结束日期
    - `customer`: 客户ID筛选
    - `service_type`: 服务类型筛选

- **响应**:
  - 状态码: 200
  - 响应体示例:
    ```json
    {
      "period": "monthly",
      "start_date": "2025-01-01",
      "end_date": "2025-12-31",
      "total_orders": 320,
      "total_amount": 256000.00,
      "total_profit": 128000.00,
      "average_profit_rate": 0.50,
      "by_period": [
        {
          "period": "2025-01",
          "orders": 25,
          "amount": 20000.00,
          "profit": 10000.00
        },
        // 更多周期...
      ],
      "by_service_type": [
        {
          "service_type": "翻译",
          "orders": 200,
          "amount": 160000.00
        },
        {
          "service_type": "口译",
          "orders": 120,
          "amount": 96000.00
        }
      ],
      "by_status": [
        {
          "status": "completed",
          "orders": 280,
          "amount": 224000.00
        },
        {
          "status": "in_progress",
          "orders": 40,
          "amount": 32000.00
        }
      ]
    }
    ```

#### 3.3.4 获取订单提醒

- **请求**:
  - 方法: `GET`
  - URL: `/api/v1/orders/reminders/`
  - 权限要求: 需要认证
  - 查询参数:
    - `type`: 提醒类型，可选值: `start`, `due`, `all`，默认`all`
    - `days`: 天数范围，默认7

- **响应**:
  - 状态码: 200
  - 响应体示例:
    ```json
    {
      "count": 5,
      "reminders": [
        {
          "id": 123,
          "order_number": "PQ-202508-1234",
          "customer": {
            "id": 1,
            "name": "ABC科技有限公司"
          },
          "reminder_type": "start",
          "date": "2025-08-01",
          "days_left": 3,
          "service_type": "翻译",
          "language_direction": "英译中"
        },
        // 更多提醒...
      ]
    }
    ```

### 3.4 客户订单API

#### 3.4.1 获取特定客户的订单

- **请求**:
  - 方法: `GET`
  - URL: `/api/v1/customers/{customer_id}/orders/`
  - 权限要求: 需要认证和查看客户权限
  - 查询参数: 同订单列表API

- **响应**:
  - 状态码: 200
  - 响应体: 同订单列表API

## 4. 数据模型

API使用的主要数据模型包括：

### 4.1 订单(Order)

| 字段名 | 类型 | 描述 | 是否必填 |
|-------|------|------|---------|
| id | Integer | 订单ID | 自动生成 |
| order_number | String | 订单编号 | 自动生成 |
| customer | Integer | 客户ID | 是 |
| customer_contact | Integer | 客户联系人ID | 否 |
| service_type | String | 服务类型 | 是 |
| language_direction | String | 语言方向 | 是 |
| word_count | Integer | 字数 | 是 |
| description | String | 项目描述 | 否 |
| translator | String | 译员 | 否 |
| start_date | Date | 开始日期 | 否 |
| due_date | Date | 截止日期 | 否 |
| delivery_date | Date | 交付日期 | 否 |
| unit_price | Decimal | 单价(元/千字) | 是 |
| total_amount | Decimal | 总金额 | 自动计算 |
| translator_fee | Decimal | 译员费用 | 否 |
| other_costs | Decimal | 其他成本 | 否，默认0 |
| payment_status | String | 支付状态 | 否，默认'unpaid' |
| payment_date | Date | 支付日期 | 否 |
| payment_method | String | 支付方式 | 否 |
| payment_remarks | String | 支付备注 | 否 |
| invoice_status | String | 发票状态 | 否，默认'not_required' |
| invoice_info | JSON | 发票信息 | 否 |
| contract_number | String | 合同编号 | 否 |
| contract_info | JSON | 合同信息 | 否 |
| remarks | String | 备注 | 否 |
| attachments | JSON | 附件列表 | 否 |
| tags | JSON | 标签 | 否 |
| status | String | 订单状态 | 否，默认'draft' |
| created_at | DateTime | 创建时间 | 自动生成 |
| updated_at | DateTime | 更新时间 | 自动更新 |
| created_by | Integer | 创建人ID | 自动填充 |
| tenant | Integer | 租户ID | 自动填充 |
| is_deleted | Boolean | 是否删除 | 否，默认false |

### 4.2 订单历史(OrderHistory)

| 字段名 | 类型 | 描述 | 是否必填 |
|-------|------|------|---------|
| id | Integer | 记录ID | 自动生成 |
| order | Integer | 订单ID | 是 |
| version | Integer | 版本号 | 自动生成 |
| modified_by | Integer | 修改人ID | 自动填充 |
| modified_at | DateTime | 修改时间 | 自动生成 |
| change_details | JSON | 变更详情 | 是 |
| snapshot | JSON | 订单快照 | 是 |

## 5. 注意事项

1. 所有API请求都需要在HTTP头部包含有效的授权令牌：
   ```
   Authorization: Bearer <your_token>
   ```

2. 对于分页结果，响应中包含以下信息：
   - `count`: 总记录数
   - `next`: 下一页URL，如果没有下一页则为null
   - `previous`: 上一页URL，如果是第一页则为null
   - `results`: 当前页的数据列表

3. 错误响应统一格式为：
   ```json
   {
     "error": "错误代码",
     "message": "错误详细描述",
     "fields": {
       "字段名": ["字段相关的错误信息"]
     }
   }
   ```

4. 所有金额字段均以元为单位，保留两位小数。

5. 所有API的访问均受到基于角色的权限控制。 