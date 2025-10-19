# CORS 跨域问题修复

## 问题描述

访问 `http://43.142.76.105:8000/api/v1/cms/categories/tree/` 时报跨域错误。

---

## 问题原因

### 1. **CORS 配置冲突**

**原配置问题**:
```python
# 第265行：设置为 False
CORS_ALLOW_ALL_ORIGINS = False

# 第266-278行：白名单全部被注释
# CORS_ALLOWED_ORIGINS = [...]  # ❌ 注释掉了

# 第316行：又重复设置为 True
CORS_ALLOW_ALL_ORIGINS = True  # ⚠️ 配置混乱
```

### 2. **CSRF_TRUSTED_ORIGINS 未配置**

```python
# CSRF_TRUSTED_ORIGINS = [...]  # ❌ 全部被注释
```

缺少 CSRF 受信任源配置，导致跨域请求被拒绝。

### 3. **缺少 CORS 方法和响应头配置**

- 没有明确配置 `CORS_ALLOW_METHODS`
- 没有配置 `CORS_EXPOSE_HEADERS`

---

## 修复内容

### 1. **统一 CORS 配置**

**文件**: `core/settings.py` (第254-276行)

```python
# ============================================
# CORS 跨域配置
# ============================================
# 开发环境允许所有来源，生产环境建议使用白名单
CORS_ALLOW_ALL_ORIGINS = True  # 允许所有来源（适用于开发和API服务）

# 如果需要白名单模式，设置 CORS_ALLOW_ALL_ORIGINS = False 并配置以下列表
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:8848",
    "http://43.142.76.105",          # ✅ 添加生产环境IP
    "http://43.142.76.105:8000",     # ✅ 添加生产环境IP:8000
    "http://43.142.76.105:3000",     # ✅ 添加前端端口
    "http://espressox.online",
    "https://espressox.online",
    "http://backend.espressox.online",
    "https://backend.espressox.online",
    "http://admin.espressox.online",
    "https://admin.espressox.online",
]
```

### 2. **配置 CSRF 受信任源**

**文件**: `core/settings.py` (第304-319行)

```python
# CSRF 受信任的源（重要：解决跨域CSRF问题）
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://43.142.76.105',          # ✅ 添加
    'http://43.142.76.105:8000',     # ✅ 添加
    'http://43.142.76.105:3000',     # ✅ 添加
    'http://espressox.online',
    'https://espressox.online',
    'http://backend.espressox.online',
    'https://backend.espressox.online',
    'http://admin.espressox.online',
    'https://admin.espressox.online',
]
```

### 3. **添加 CORS 方法配置**

**文件**: `core/settings.py` (第280-288行)

```python
# 允许的 HTTP 方法
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
```

### 4. **添加响应头配置**

**文件**: `core/settings.py` (第304-308行)

```python
# 允许前端访问的响应头
CORS_EXPOSE_HEADERS = [
    "content-type",
    "x-csrftoken",
]
```

---

## 完整的 CORS 配置

```python
# ============================================
# CORS 跨域配置
# ============================================
CORS_ALLOW_ALL_ORIGINS = True  # 允许所有来源

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
    "http://localhost:8848",
    "http://43.142.76.105",
    "http://43.142.76.105:8000",
    "http://43.142.76.105:3000",
    "http://espressox.online",
    "https://espressox.online",
    "http://backend.espressox.online",
    "https://backend.espressox.online",
    "http://admin.espressox.online",
    "https://admin.espressox.online",
]

CORS_ALLOW_CREDENTIALS = True  # 允许携带凭证

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "x-tenant-id",
]

CORS_EXPOSE_HEADERS = [
    "content-type",
    "x-csrftoken",
]

# CSRF 配置
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://43.142.76.105',
    'http://43.142.76.105:8000',
    'http://43.142.76.105:3000',
    'http://espressox.online',
    'https://espressox.online',
    'http://backend.espressox.online',
    'https://backend.espressox.online',
    'http://admin.espressox.online',
    'https://admin.espressox.online',
]
```

---

## 验证步骤

### 1. **重启 Django 服务器**

```bash
# 停止当前服务器（Ctrl+C）

# 重新启动
python manage.py runserver 0.0.0.0:8000
```

### 2. **测试 API 访问**

#### 使用 cURL 测试

```bash
curl -X GET "http://43.142.76.105:8000/api/v1/cms/categories/tree/" \
  -H "Accept: application/json" \
  -H "Origin: http://localhost:3000" \
  -v
```

**期望输出**:
```
< HTTP/1.1 200 OK
< Access-Control-Allow-Origin: http://localhost:3000
< Access-Control-Allow-Credentials: true
< Content-Type: application/json
...
```

#### 使用浏览器测试

打开浏览器控制台（F12），执行：

```javascript
fetch('http://43.142.76.105:8000/api/v1/cms/categories/tree/', {
  method: 'GET',
  headers: {
    'Content-Type': 'application/json'
  }
})
  .then(response => response.json())
  .then(data => console.log('成功:', data))
  .catch(error => console.error('错误:', error));
```

### 3. **检查响应头**

在浏览器开发者工具的 Network 标签中，查看响应头应包含：

```
Access-Control-Allow-Origin: *
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: DELETE, GET, OPTIONS, PATCH, POST, PUT
Access-Control-Allow-Headers: ...
```

---

## 常见问题

### Q1: 仍然报跨域错误？

**检查项**:

1. **确认服务器已重启**
   ```bash
   # 停止旧进程
   pkill -f "python manage.py runserver"
   
   # 重新启动
   python manage.py runserver 0.0.0.0:8000
   ```

2. **清除浏览器缓存**
   - Chrome: `Ctrl + Shift + Delete`
   - 选择"缓存的图像和文件"
   - 清除

3. **检查中间件顺序**
   
   确认 `corsheaders.middleware.CorsMiddleware` 在 `MIDDLEWARE` 列表中排在前面：
   
   ```python
   MIDDLEWARE = [
       'whitenoise.middleware.WhiteNoiseMiddleware',
       'django.middleware.security.SecurityMiddleware',
       'corsheaders.middleware.CorsMiddleware',  # ← 必须在这里
       'django.contrib.sessions.middleware.SessionMiddleware',
       # ...
   ]
   ```

### Q2: OPTIONS 请求失败？

**原因**: 预检请求（Preflight Request）被拦截。

**解决**:

确认已配置 `CORS_ALLOW_METHODS` 包含 `'OPTIONS'`：

```python
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',  # ← 必须包含
    'PATCH',
    'POST',
    'PUT',
]
```

### Q3: 如何切换到白名单模式？

生产环境建议使用白名单模式：

```python
# 1. 设置为 False
CORS_ALLOW_ALL_ORIGINS = False

# 2. 只保留需要的域名
CORS_ALLOWED_ORIGINS = [
    "https://your-frontend-domain.com",
    "http://43.142.76.105:8000",
]

# 3. 同步更新 CSRF_TRUSTED_ORIGINS
CSRF_TRUSTED_ORIGINS = [
    "https://your-frontend-domain.com",
    "http://43.142.76.105:8000",
]
```

### Q4: 携带 Cookie 的请求失败？

**前端配置**:

```javascript
// Fetch API
fetch('http://43.142.76.105:8000/api/v1/cms/categories/tree/', {
  method: 'GET',
  credentials: 'include',  // ← 重要：携带 Cookie
  headers: {
    'Content-Type': 'application/json'
  }
})

// Axios
axios.defaults.withCredentials = true;
```

**后端配置**:

确认已设置：
```python
CORS_ALLOW_CREDENTIALS = True
```

---

## 测试脚本

创建测试脚本 `test_cors.py`：

```python
import requests

# 测试 URL
url = 'http://43.142.76.105:8000/api/v1/cms/categories/tree/'

# 测试不同的 Origin
origins = [
    'http://localhost:3000',
    'http://43.142.76.105:3000',
    'https://espressox.online',
]

for origin in origins:
    print(f"\n测试 Origin: {origin}")
    
    # 模拟预检请求 (OPTIONS)
    response = requests.options(
        url,
        headers={
            'Origin': origin,
            'Access-Control-Request-Method': 'GET',
        }
    )
    
    print(f"  OPTIONS 状态码: {response.status_code}")
    print(f"  Access-Control-Allow-Origin: {response.headers.get('Access-Control-Allow-Origin', 'None')}")
    
    # 实际请求 (GET)
    response = requests.get(
        url,
        headers={'Origin': origin}
    )
    
    print(f"  GET 状态码: {response.status_code}")
    print(f"  Access-Control-Allow-Origin: {response.headers.get('Access-Control-Allow-Origin', 'None')}")
```

运行测试：

```bash
python test_cors.py
```

---

## 生产环境部署建议

### 1. **使用白名单模式**

```python
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    "https://your-production-domain.com",
    "http://43.142.76.105:8000",
]
```

### 2. **启用 HTTPS**

```python
# 生产环境强制使用 HTTPS
CORS_ALLOWED_ORIGINS = [
    "https://your-domain.com",  # 使用 HTTPS
]

CSRF_COOKIE_SECURE = True  # Cookie 仅通过 HTTPS 传输
```

### 3. **配置反向代理**

使用 Nginx 处理 CORS（推荐）：

```nginx
server {
    listen 80;
    server_name 43.142.76.105;

    location /api/ {
        # CORS 配置
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'Content-Type, Authorization' always;
        
        # OPTIONS 预检请求
        if ($request_method = 'OPTIONS') {
            return 204;
        }
        
        # 转发到 Django
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 监控和日志

### 查看 CORS 相关日志

```python
# 在 settings.py 中启用 CORS 日志
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'corsheaders': {
            'handlers': ['console'],
            'level': 'DEBUG',  # ← 启用 CORS 调试日志
        },
    },
}
```

### 日志输出示例

```log
[DEBUG] corsheaders: Request Origin: http://localhost:3000
[DEBUG] corsheaders: CORS allowed: True
[DEBUG] corsheaders: Adding Access-Control-Allow-Origin header
```

---

## 总结

### 修复内容

✅ 统一 CORS_ALLOW_ALL_ORIGINS 配置（设为 True）  
✅ 添加生产环境 IP 到白名单  
✅ 配置 CSRF_TRUSTED_ORIGINS  
✅ 添加 CORS_ALLOW_METHODS  
✅ 添加 CORS_EXPOSE_HEADERS  
✅ 保持中间件正确顺序  

### 配置特点

- 🌐 **开发友好**: 允许所有来源（开发环境）
- 🔒 **生产就绪**: 白名单模式可用（生产环境）
- 🍪 **支持凭证**: 允许携带 Cookie
- 📋 **方法完整**: 支持所有常用 HTTP 方法
- 🔍 **可追踪**: 可启用日志调试

---

**修复版本**: 1.0.3  
**修复日期**: 2025-10-19  
**影响范围**: 所有跨域 API 请求  
**测试状态**: 待测试
