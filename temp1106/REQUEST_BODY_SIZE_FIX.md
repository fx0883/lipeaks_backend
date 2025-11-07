# 请求体大小限制问题修复说明

## 问题描述

在使用日志中间件时，当客户端发送的请求体超过 Django 的 `DATA_UPLOAD_MAX_MEMORY_SIZE` 设置时，会抛出 `RequestDataTooBig` 异常，导致请求处理失败。

### 错误堆栈

```
Exception: Request body exceeded settings.DATA_UPLOAD_MAX_MEMORY_SIZE.

Traceback (most recent call last):
  File "django/core/handlers/exception.py", line 55, in inner
    response = get_response(request)
  File "common/middleware/enhanced_api_logging_middleware.py", line 253, in process_request
    'request_body': self._get_request_body(request),
  File "common/middleware/enhanced_api_logging_middleware.py", line 64, in _get_request_body
    if not request.body:
  File "django/http/request.py", line 373, in body
    raise RequestDataTooBig(
        "Request body exceeded settings.DATA_UPLOAD_MAX_MEMORY_SIZE."
    )
```

### 问题原因

1. **Django 默认限制**：Django 的默认 `DATA_UPLOAD_MAX_MEMORY_SIZE` 为 2.5MB（2,621,440字节）
2. **中间件未捕获异常**：`EnhancedAPILoggingMiddleware` 的 `_get_request_body` 方法直接访问 `request.body`，没有捕获 `RequestDataTooBig` 异常
3. **业务逻辑硬编码限制**：在多个视图文件中，头像上传的大小限制被硬编码为 2MB，即使修改了 `settings.py` 中的配置，业务代码仍然使用旧的 2MB 限制
4. **大文件上传**：当用户上传图片、文档等较大文件时，容易超过此限制

### 为什么修改了 settings.py 还是提示 2MB 限制？

这是因为有**两层限制**：

1. **Django 框架层限制**（`DATA_UPLOAD_MAX_MEMORY_SIZE`）：这是在请求进入视图之前，Django 框架层面的限制
2. **业务逻辑层限制**（视图中的验证代码）：即使文件通过了框架层限制，在业务逻辑中还有一层验证

原来的代码在业务逻辑中硬编码了 2MB 的限制：

```python
# 旧代码 - 硬编码 2MB 限制
if avatar_file.size > 2 * 1024 * 1024:  # 2MB
    return Response(
        {"detail": "文件太大，头像大小不能超过2MB"},
        status=status.HTTP_400_BAD_REQUEST
    )
```

所以即使将 `DATA_UPLOAD_MAX_MEMORY_SIZE` 改为 10MB，业务逻辑仍然会在 2MB 处拦截。

## 解决方案

### 1. 增加请求体大小限制（core/settings.py）

```python
# ============================================================================
# File Upload Settings (文件上传设置)
# ============================================================================
# 增加内存上传大小限制，支持较大文件上传（例如图片、文档等）
# 默认值：2.5MB (2621440 bytes)
# 设置为 10MB，可根据实际需求调整
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB

# 请求体最大大小限制（包括文件上传）
# 设置为 50MB，防止恶意请求
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000  # 表单字段数量限制
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB - 在内存中处理的最大文件大小
```

**说明：**
- `DATA_UPLOAD_MAX_MEMORY_SIZE`：设置为 10MB，允许较大的请求体
- `DATA_UPLOAD_MAX_NUMBER_FIELDS`：限制表单字段数量，防止 DOS 攻击
- `FILE_UPLOAD_MAX_MEMORY_SIZE`：设置文件在内存中处理的最大大小

### 2. 中间件异常处理（common/middleware/enhanced_api_logging_middleware.py）

#### 2.1 添加导入

```python
from django.core.exceptions import RequestDataTooBig
```

#### 2.2 修改 `_get_request_body` 方法

```python
def _get_request_body(self, request):
    """
    安全地获取请求体内容
    
    Args:
        request: HTTP请求对象
    
    Returns:
        字典或None: 请求体内容
    """
    try:
        # 尝试访问请求体，可能会抛出RequestDataTooBig异常
        if not request.body:
            return None
    except RequestDataTooBig:
        # 请求体过大，超过DATA_UPLOAD_MAX_MEMORY_SIZE限制
        logger.warning(f"请求体过大，超过DATA_UPLOAD_MAX_MEMORY_SIZE限制: {request.path}")
        return {'error': 'Request body too large', 'message': '请求体超过大小限制'}
    except Exception as e:
        # 捕获其他异常
        logger.warning(f"访问请求体时发生错误: {str(e)}")
        return {'error': f"访问请求体失败: {str(e)}"}
    
    # ... 后续处理逻辑
```

### 3. 修改业务逻辑中的头像大小限制

修改了以下 5 处硬编码的 2MB 限制，改为从 `settings.py` 动态读取：

**修改前（硬编码）：**
```python
# 验证文件大小
if avatar_file.size > 2 * 1024 * 1024:  # 2MB
    return Response(
        {"detail": "文件太大，头像大小不能超过2MB"},
        status=status.HTTP_400_BAD_REQUEST
    )
```

**修改后（动态读取）：**
```python
# 验证文件大小（从settings获取配置，默认10MB）
max_size = getattr(settings, 'DATA_UPLOAD_MAX_MEMORY_SIZE', 10 * 1024 * 1024)
if avatar_file.size > max_size:
    max_size_mb = max_size / (1024 * 1024)
    return Response(
        {"detail": f"文件太大，头像大小不能超过{max_size_mb:.0f}MB"},
        status=status.HTTP_400_BAD_REQUEST
    )
```

**修改的文件：**
1. `users/views/member_views.py` - 2 处
   - Member 自己上传头像的接口
   - 管理员为 Member 上传头像的接口
2. `users/views/member_admin_views.py` - 1 处
   - 管理员为 Member 上传头像的接口
3. `users/views/admin_user_views.py` - 2 处
   - 管理员自己上传头像的接口
   - 管理员为其他管理员上传头像的接口

## 修复效果

1. **优雅降级**：当请求体过大时，中间件会记录警告日志，但不会导致请求失败
2. **日志记录**：在日志中记录 `{'error': 'Request body too large', 'message': '请求体超过大小限制'}`，便于追踪
3. **支持大文件**：将限制从 2.5MB 提升到 10MB，满足大部分文件上传需求
4. **安全性**：设置了字段数量限制，防止 DOS 攻击

## 注意事项

### 1. 根据实际需求调整限制

如果您的应用需要支持更大的文件上传（如视频），可以进一步增加限制：

```python
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB
```

### 2. 考虑使用流式上传

对于非常大的文件（>50MB），建议：
- 使用流式上传方式
- 配置 Nginx/Apache 等 Web 服务器处理大文件上传
- 考虑使用对象存储服务（如 OSS、S3）的直传功能

### 3. 监控日志

定期检查日志中是否有大量"请求体过大"的警告，如果频繁出现，可能需要：
- 调整限制大小
- 优化前端上传逻辑
- 添加前端文件大小验证

### 4. 生产环境配置

在生产环境中，建议通过环境变量配置这些限制：

```python
# settings.py
DATA_UPLOAD_MAX_MEMORY_SIZE = int(os.getenv('DATA_UPLOAD_MAX_MEMORY_SIZE', 10485760))
FILE_UPLOAD_MAX_MEMORY_SIZE = int(os.getenv('FILE_UPLOAD_MAX_MEMORY_SIZE', 10485760))
```

## 测试验证

### 1. 测试小文件上传

```bash
curl -X POST http://localhost:8000/api/v1/upload/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@small_image.jpg"
```

### 2. 测试大文件上传（接近限制）

```bash
# 创建一个 9MB 的测试文件
dd if=/dev/zero of=test_9mb.bin bs=1M count=9

# 上传测试
curl -X POST http://localhost:8000/api/v1/upload/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test_9mb.bin"
```

### 3. 测试超过限制的文件

```bash
# 创建一个 15MB 的测试文件
dd if=/dev/zero of=test_15mb.bin bs=1M count=15

# 上传测试（应该被拒绝，但不会导致服务器错误）
curl -X POST http://localhost:8000/api/v1/upload/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test_15mb.bin"
```

## 相关文档

- [Django File Uploads](https://docs.djangoproject.com/en/stable/topics/http/file-uploads/)
- [Django Settings - DATA_UPLOAD_MAX_MEMORY_SIZE](https://docs.djangoproject.com/en/stable/ref/settings/#data-upload-max-memory-size)
- [Django Settings - FILE_UPLOAD_MAX_MEMORY_SIZE](https://docs.djangoproject.com/en/stable/ref/settings/#file-upload-max-memory-size)

## 修改文件列表

### 1. 配置文件
- `core/settings.py`：添加 `DATA_UPLOAD_MAX_MEMORY_SIZE` 等文件上传相关配置

### 2. 中间件
- `common/middleware/enhanced_api_logging_middleware.py`：添加 `RequestDataTooBig` 异常处理

### 3. 业务逻辑（头像上传限制）
- `users/views/member_views.py`：修改了 2 处头像大小验证逻辑
- `users/views/member_admin_views.py`：修改了 1 处头像大小验证逻辑
- `users/views/admin_user_views.py`：修改了 2 处头像大小验证逻辑

## 修改时间

- 2025-11-07：初次修复（中间件异常处理 + settings配置）
- 2025-11-07：业务逻辑修复（头像上传限制从硬编码改为从settings读取）
- 修复人员：AI Assistant
- 影响范围：
  - 所有使用 `EnhancedAPILoggingMiddleware` 的 API 端点
  - 所有头像上传 API 端点（Member、AdminUser）

