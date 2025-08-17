# 获取文章统计数据API

## API 端点

```
GET /api/v1/cms/articles/{id}/statistics/
```

## 描述

获取文章的详细统计数据，包括浏览量、点赞数等。

## 路径参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| id | integer | 是 | 文章ID |

## 请求头

| 名称 | 类型 | 必填 | 描述 |
|------|------|------|------|
| Authorization | string | 是 | Bearer token认证 |
| Content-Type | string | 是 | application/json |
| X-Tenant-ID | string | 否 | 租户ID |

## 查询参数

| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| period | string | 否 | 统计周期，可选值：day, week, month, year, all，默认all |
| start_date | string | 否 | 统计起始日期，格式YYYY-MM-DD |
| end_date | string | 否 | 统计结束日期，格式YYYY-MM-DD |

## 响应

### 成功响应 (200 OK)

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "basic_stats": {
      "views_count": 0,
      "unique_views_count": 0,
      "likes_count": 0,
      "dislikes_count": 0,
      "comments_count": 0,
      "shares_count": 0,
      "bookmarks_count": 0,
      "avg_reading_time": 0,
      "bounce_rate": 0
    },
    "time_series": {
      "views": []
    },
    "demographics": {
      "countries": [],
      "devices": [],
      "browsers": []
    },
    "referrers": []
  }
}
```

### 响应字段说明

| 字段 | 类型 | 描述 |
|------|------|------|
| success | boolean | 是否成功 |
| code | integer | 状态码 |
| message | string | 操作结果描述 |
| data | object | 统计数据 |
| data.basic_stats | object | 基础统计数据 |
| data.basic_stats.views_count | integer | 浏览次数 |
| data.basic_stats.unique_views_count | integer | 独立访客浏览次数 |
| data.basic_stats.likes_count | integer | 点赞数 |
| data.basic_stats.dislikes_count | integer | 踩数 |
| data.basic_stats.comments_count | integer | 评论数 |
| data.basic_stats.shares_count | integer | 分享数 |
| data.basic_stats.bookmarks_count | integer | 收藏数 |
| data.basic_stats.avg_reading_time | integer | 平均阅读时长(秒) |
| data.basic_stats.bounce_rate | number | 跳出率(%) |
| data.time_series | object | 时间序列数据 |
| data.time_series.views | array | 按时间的浏览量数据 |
| data.demographics | object | 用户群体统计 |
| data.demographics.countries | array | 访问国家/地区统计 |
| data.demographics.devices | array | 访问设备统计 |
| data.demographics.browsers | array | 访问浏览器统计 |
| data.referrers | array | 来源网站统计 |

### 错误响应

#### 401 Unauthorized

```json
{
  "detail": "身份认证信息未提供。"
}
```

#### 403 Forbidden

```json
{
  "detail": "您没有执行此操作的权限。"
}
```

#### 404 Not Found

```json
{
  "detail": "未找到。"
}
```

## 示例

### cURL示例

```bash
curl -X 'GET' \
  'http://localhost:8000/api/v1/cms/articles/15/statistics/?period=month' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
```

### Python示例

```python
import requests

article_id = 15
url = f'http://localhost:8000/api/v1/cms/articles/{article_id}/statistics/'
headers = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
    'Content-Type': 'application/json'
}
params = {
    'period': 'month',
    'start_date': '2025-05-01',
    'end_date': '2025-05-31'
}

response = requests.get(url, headers=headers, params=params)
print(response.status_code)
print(response.json())
```

## 注意事项

1. 统计数据会根据指定的时间周期进行过滤
2. 如果没有指定时间周期，默认返回所有时间的统计数据
3. 时间序列数据可用于生成趋势图表
4. 人口统计和来源数据可用于分析用户行为和流量来源 