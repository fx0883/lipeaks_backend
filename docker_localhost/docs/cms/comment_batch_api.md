# 批量评论处理API

## 接口说明

批量处理多条评论，支持批量审核、拒绝、标记为垃圾评论或删除。

- **接口路径**: `/api/v1/cms/comments/batch/`
- **请求方法**: POST
- **认证要求**: 需要JWT认证
- **权限要求**: 
  - 文章作者可以批量处理其文章下的评论
  - 租户管理员可以批量处理该租户下的所有评论
  - 超级管理员可以批量处理所有评论

## 请求参数

### 请求头

```
Authorization: Bearer {your_jwt_token}
Content-Type: application/json
X-Tenant-ID: {tenant_id}
```

### 请求体

| 字段名      | 类型    | 必填 | 描述                                                |
|-------------|---------|------|-----------------------------------------------------|
| comment_ids | array   | 是   | 要处理的评论ID数组                                  |
| action      | string  | 是   | 执行的操作，可选值: approve, reject, spam, delete   |

## 请求示例

### 批量批准评论

```json
{
  "comment_ids": [1, 2, 3, 4, 5],
  "action": "approve"
}
```

### 批量删除评论

```json
{
  "comment_ids": [10, 11, 12],
  "action": "delete"
}
```

## 响应

### 成功响应

**状态码**: 200 OK

```json
{
  "success": true,
  "message": "成功处理5条评论",
  "processed_count": 5,
  "failed_count": 0,
  "details": {
    "approved": 5,
    "rejected": 0,
    "spam": 0,
    "deleted": 0,
    "failed": []
  }
}
```

### 部分成功响应

**状态码**: 200 OK

```json
{
  "success": true,
  "message": "成功处理3条评论，1条评论处理失败",
  "processed_count": 3,
  "failed_count": 1,
  "details": {
    "approved": 3,
    "rejected": 0,
    "spam": 0,
    "deleted": 0,
    "failed": [
      {
        "id": 5,
        "reason": "权限不足"
      }
    ]
  }
}
```

### 错误响应

**状态码**: 400 Bad Request

```json
{
  "detail": "请提供要处理的评论ID列表"
}
```

```json
{
  "detail": "无效的操作，可选值为: approve, reject, spam, delete"
}
```

**状态码**: 401 Unauthorized

```json
{
  "detail": "身份认证信息未提供。"
}
```

**状态码**: 403 Forbidden

```json
{
  "detail": "您没有执行该操作的权限。"
}
```

## 支持的批量操作

1. **批准评论** (`approve`): 将评论状态改为已批准
2. **拒绝评论** (`reject`): 将评论状态改为已拒绝
3. **标记为垃圾评论** (`spam`): 将评论状态改为垃圾评论
4. **删除评论** (`delete`): 删除评论

## 注意事项

1. 批量操作会自动更新相关文章的评论统计数据
2. 批量操作会记录每个评论的操作日志
3. 批量操作支持部分成功，即使部分评论处理失败，其他评论仍会被处理
4. 批量操作对每个评论都会进行权限检查，用户只能处理有权限的评论
5. 批量操作的结果会详细列出成功和失败的数量及原因 