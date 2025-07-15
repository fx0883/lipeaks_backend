# 标准响应格式渲染器

本文档介绍了项目中实现的全局标准响应格式渲染器，它确保所有 API 返回统一的响应格式。

## 响应格式

所有 API 响应都将被包装为以下标准格式：

```json
{
  "success": true/false,
  "code": 2000,
  "message": "操作成功/失败信息",
  "data": { ... }
}
```

字段说明：
- `success`: 布尔值，表示请求是否成功
- `code`: 整数，业务状态码，成功为 2000，错误为 4xxx 或 5xxx
- `message`: 字符串，操作结果消息
- `data`: 对象或数组，实际响应数据

## 实现原理

标准响应格式通过自定义 DRF 渲染器实现，主要组件包括：

1. `StandardJSONRenderer`: 继承自 DRF 的 `JSONRenderer`，对所有响应进行标准格式包装
2. 修改 `settings.py` 中的 `DEFAULT_RENDERER_CLASSES` 设置，将自定义渲染器设为默认
3. 优化分页响应格式，使其与标准格式一致

## 业务状态码

| 状态码 | 说明 |
|--------|------|
| 2000 | 操作成功 |
| 4000 | 客户端错误 |
| 4001 | 认证失败 |
| 4003 | 权限不足 |
| 4004 | 资源不存在 |
| 5000 | 服务器错误 |

## 测试接口

为了测试渲染器的功能，我们提供了以下测试接口：

- `GET /api/v1/common/test-format/`: 测试成功响应格式
- `GET /api/v1/common/test-error/`: 测试错误响应格式
- `GET /api/v1/common/test-auth-error/`: 测试认证失败响应格式
- `GET /api/v1/common/test-pagination/`: 测试分页响应格式

## 使用示例

开发人员无需做任何特殊处理，只需正常使用 DRF 的 `Response` 类返回数据即可，渲染器会自动将响应包装为标准格式。

### 成功响应示例

```python
from rest_framework.response import Response

def my_view(request):
    data = {'key': 'value'}
    return Response(data)
```

输出：

```json
{
  "success": true,
  "code": 2000,
  "message": "操作成功",
  "data": {
    "key": "value"
  }
}
```

### 错误响应示例

```python
from rest_framework.response import Response
from rest_framework import status

def my_view(request):
    return Response(
        {'detail': '无效的请求参数'}, 
        status=status.HTTP_400_BAD_REQUEST
    )
```

输出：

```json
{
  "success": false,
  "code": 4000,
  "message": "无效的请求参数",
  "data": {}
}
```

## 注意事项

1. 如果响应已经是标准格式（包含 success, code, message, data 字段），渲染器不会重复包装
2. 错误响应中的 `detail` 字段会被提取到 `message` 字段
3. 分页响应会保留 `pagination` 和 `results` 结构，并包装在 `data` 字段中
4. BrowsableAPIRenderer 仍然保留，以便在浏览器中查看 API 