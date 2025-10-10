# HTTP客户端集成指南

## 概述

本文档说明如何在HTTP客户端中集成统一的错误处理，**适用于任何HTTP客户端库**（Axios、Fetch、jQuery Ajax、XMLHttpRequest、Uni-app的request等）。

## 核心概念

### HTTP客户端的作用

```
HTTP客户端负责:
  1. 发送HTTP请求
  2. 接收HTTP响应
  3. 拦截请求/响应（如果支持）
  4. 处理网络错误
```

### 需要实现的功能

```
必需功能:
  ✅ 请求拦截 - 注入Token、租户ID等
  ✅ 响应拦截 - 统一处理错误响应
  ✅ 错误分类 - 区分网络错误和API错误
  ✅ Token管理 - 自动注入和刷新

可选功能:
  ⭐ 请求重试 - 失败后自动重试
  ⭐ 请求取消 - 组件卸载时取消pending请求
  ⭐ 请求缓存 - 减少重复请求
  ⭐ 进度监控 - 上传/下载进度
```

## 请求拦截器设计

### 拦截器流程

```
请求拦截流程:

原始请求 → [请求拦截器] → 修改后的请求 → 发送到服务器

拦截器要做的事:
  1. 添加认证Token
  2. 添加租户ID（如果需要）
  3. 添加自定义请求头
  4. 记录请求日志（开发环境）
```

### 实现逻辑（伪代码）

```
FUNCTION requestInterceptor(config):
  // 1. 注入Token
  token = 从本地存储获取Token()
  IF token 存在:
    config.headers['Authorization'] = 'Bearer ' + token
  
  // 2. 注入租户ID
  tenantId = 从本地存储获取租户ID()
  IF tenantId 存在:
    config.headers['X-Tenant-ID'] = tenantId
  
  // 3. 添加请求ID（用于追踪，开发环境）
  IF 是开发环境:
    config.headers['X-Request-ID'] = 生成唯一ID()
    记录请求日志(config)
  
  RETURN config
```

### 各HTTP客户端实现参考

**Axios：**
```
axios.interceptors.request.use(function (config) {
  // 修改config
  return config;
});
```

**Fetch API：**
```
// 包装原生fetch
function fetchWithAuth(url, options = {}) {
  const token = getToken();
  
  const headers = {
    ...options.headers,
    'Authorization': 'Bearer ' + token,
    'X-Tenant-ID': getTenantId()
  };
  
  return fetch(url, { ...options, headers });
}
```

**jQuery Ajax：**
```
$.ajaxSetup({
  beforeSend: function(xhr) {
    xhr.setRequestHeader('Authorization', 'Bearer ' + getToken());
    xhr.setRequestHeader('X-Tenant-ID', getTenantId());
  }
});
```

**Uni-app：**
```
// 在request前添加拦截
uni.addInterceptor('request', {
  invoke(args) {
    args.header = args.header || {};
    args.header['Authorization'] = 'Bearer ' + getToken();
    args.header['X-Tenant-ID'] = getTenantId();
  }
});
```

## 响应拦截器设计

### 拦截器流程

```
响应拦截流程:

服务器响应 → [响应拦截器] → 错误判断和处理 → 返回给调用者

拦截器要做的事:
  1. 解析响应JSON
  2. 检查success字段
  3. 分类错误类型
  4. 调用对应的错误处理器
  5. 记录响应日志（开发环境）
```

### 实现逻辑（伪代码）

```
FUNCTION responseInterceptor(response):
  // 记录日志（开发环境）
  IF 是开发环境:
    记录响应日志(response)
  
  // 检查响应
  IF response.data.success === true:
    RETURN response  // 成功，直接返回
  
  // 错误响应，进入错误处理
  errorResponse = response.data
  
  // 调用统一错误处理器
  handleApiError(errorResponse)
  
  // 抛出错误（让调用者的catch块也能捕获）
  THROW error


FUNCTION errorInterceptor(error):
  // 网络错误（无响应）
  IF 没有response对象:
    handleNetworkError(error)
    THROW error
  
  // 有响应，是API错误
  apiError = error.response.data
  
  // 调用统一错误处理器
  handleApiError(apiError)
  
  THROW error
```

### 各HTTP客户端实现参考

**Axios：**
```
axios.interceptors.response.use(
  function (response) {
    // 成功响应
    return response;
  },
  function (error) {
    // 错误响应
    handleApiError(error);
    return Promise.reject(error);
  }
);
```

**Fetch API：**
```
function fetchWithErrorHandler(url, options) {
  return fetch(url, options)
    .then(response => {
      if (!response.ok) {
        return response.json().then(data => {
          handleApiError(data);
          throw new Error(data.message);
        });
      }
      return response.json();
    })
    .catch(error => {
      // 网络错误或其他错误
      if (!error.response) {
        handleNetworkError(error);
      }
      throw error;
    });
}
```

**jQuery Ajax：**
```
$.ajaxSetup({
  error: function(xhr, status, error) {
    if (xhr.responseJSON) {
      handleApiError(xhr.responseJSON);
    } else {
      handleNetworkError(error);
    }
  }
});
```

## Token管理方案

### Token自动注入

```
Token注入流程:

每次请求前:
  1. 从本地存储获取Token
     token = localStorage.get('token')
  
  2. 添加到请求头
     headers['Authorization'] = 'Bearer ' + token
  
  3. 如果Token不存在
     某些API: 允许匿名访问
     某些API: 直接返回，提示先登录
```

### Token自动刷新

```
Token刷新流程:

FUNCTION handleTokenExpired(originalRequest):
  // 检查是否正在刷新
  IF 正在刷新Token:
    等待刷新完成
    用新Token重试原始请求
    RETURN
  
  设置: 正在刷新 = true
  
  TRY:
    refreshToken = 从本地存储获取RefreshToken()
    
    IF refreshToken不存在:
      抛出错误 "无refresh token"
    
    // 调用刷新接口
    响应 = POST /api/v1/auth/refresh/
            Body: { refresh: refreshToken }
    
    IF 响应成功:
      新Token = 响应.data.access
      保存新Token到本地存储
      
      // 用新Token重试原始请求
      原始请求.headers['Authorization'] = 'Bearer ' + 新Token
      RETURN 重新发送(原始请求)
    
    ELSE:
      抛出错误 "刷新失败"
  
  CATCH 错误:
    清除所有Token
    跳转到登录页
  
  FINALLY:
    设置: 正在刷新 = false
```

### 刷新Token时的并发请求处理

```
问题: 多个请求同时遇到Token过期

解决方案（请求队列）:

变量:
  refreshing = false
  waitingQueue = []

FUNCTION refreshTokenWithQueue():
  IF refreshing === true:
    // 已经在刷新，加入等待队列
    RETURN new Promise((resolve, reject) => {
      waitingQueue.push({ resolve, reject })
    })
  
  refreshing = true
  
  TRY:
    新Token = 调用刷新接口()
    保存新Token
    
    // 通知所有等待的请求
    FOR EACH waiter in waitingQueue:
      waiter.resolve(新Token)
    
    清空waitingQueue
    RETURN 新Token
  
  CATCH 错误:
    // 通知所有等待的请求失败
    FOR EACH waiter in waitingQueue:
      waiter.reject(错误)
    
    清空waitingQueue
    清除所有Token
    跳转登录页
  
  FINALLY:
    refreshing = false
```

## 请求重试机制

### 重试策略设计

```
重试配置:
  maxRetries: 3                    // 最多重试3次
  retryDelay: [1000, 2000, 4000]  // 延迟时间（毫秒）
  retryableErrors: [               // 可重试的错误
    '网络错误',
    '服务器错误(5XXX)',
    '429限流错误'
  ]

重试逻辑:
  FUNCTION sendRequestWithRetry(request):
    尝试次数 = 0
    
    WHILE 尝试次数 <= maxRetries:
      TRY:
        响应 = 发送请求(request)
        RETURN 响应  // 成功，返回
      
      CATCH 错误:
        IF shouldRetry(错误, 尝试次数):
          延迟 = retryDelay[尝试次数]
          记录日志: "请求失败，{延迟}ms后重试 ({尝试次数}/{maxRetries})"
          等待(延迟)
          尝试次数++
          CONTINUE  // 继续重试
        ELSE:
          THROW 错误  // 不可重试，直接抛出
    
    THROW 最后一次的错误  // 超过最大重试次数
```

## 请求取消机制

### 取消请求的场景

```
何时需要取消请求:
  1. 组件卸载时 - 避免更新已卸载组件的状态
  2. 用户导航离开 - 不需要的pending请求
  3. 用户主动取消 - 点击取消按钮
  4. 新请求发起时 - 取消之前的请求（搜索场景）
```

### 取消逻辑（概念）

```
请求取消流程:

创建可取消的请求:
  1. 创建取消令牌(cancelToken)
  2. 发起请求时传入cancelToken
  3. 需要取消时调用cancel()

伪代码:
  // 组件挂载
  cancelToken = 创建取消令牌()
  
  // 发起请求
  请求配置 = {
    url: '/api/tenants/',
    cancelToken: cancelToken
  }
  
  // 组件卸载
  FUNCTION cleanup():
    cancelToken.cancel('组件已卸载')
```

## 请求缓存方案

### 缓存策略

```
缓存适用场景:
  ✅ 短时间内多次请求相同数据
  ✅ 静态或很少变化的数据（字典、配置）
  ✅ 分页列表（缓存已加载的页）

不适用缓存:
  ❌ 实时数据（订单状态、积分余额）
  ❌ 用户敏感数据
  ❌ POST/PUT/DELETE请求

缓存逻辑:
  FUNCTION getCachedRequest(url, params):
    cacheKey = generateKey(url, params)
    cached = cache.get(cacheKey)
    
    IF cached存在 AND 未过期:
      RETURN cached.data  // 从缓存返回
    
    // 发起请求
    response = sendRequest(url, params)
    
    // 保存到缓存（5分钟有效期）
    cache.set(cacheKey, response, expiry=300000)
    
    RETURN response
```

## 进度监控

### 上传进度

```
上传进度处理:

FUNCTION uploadFile(file, onProgress):
  发送请求:
    URL: /api/v1/upload/
    Method: POST
    Body: FormData包含文件
    
    onUploadProgress: FUNCTION(progressEvent):
      total = progressEvent.total
      loaded = progressEvent.loaded
      percent = (loaded / total) * 100
      
      调用回调: onProgress(percent)

使用:
  uploadFile(selectedFile, function(progress) {
    更新UI显示进度条: progress%
  })
```

### 下载进度

```
下载进度处理:

FUNCTION downloadFile(url, onProgress):
  发送请求:
    URL: url
    Method: GET
    ResponseType: 'blob'  // 二进制数据
    
    onDownloadProgress: FUNCTION(progressEvent):
      total = progressEvent.total
      loaded = progressEvent.loaded
      percent = (loaded / total) * 100
      
      调用回调: onProgress(percent)
```

## 完整集成方案

### 统一HTTP客户端封装

```
创建统一的HTTP客户端:

FUNCTION createHttpClient(config):
  // 1. 创建客户端实例
  client = new HttpClient(config)
  
  // 2. 配置请求拦截器
  client.interceptors.request.use(requestInterceptor)
  
  // 3. 配置响应拦截器
  client.interceptors.response.use(
    responseInterceptor,     // 成功处理
    errorInterceptor          // 错误处理
  )
  
  // 4. 返回客户端
  RETURN client

配置:
  baseURL: API基础URL
  timeout: 10000  // 10秒超时
  headers: {
    'Content-Type': 'application/json'
  }
```

### 错误处理器集成

```
FUNCTION handleApiError(error):
  // 1. 区分错误类型
  IF 没有响应对象:
    handleNetworkError(error)
    RETURN
  
  apiError = error.response.data
  
  // 2. 提取错误信息
  code = apiError.code
  message = apiError.message
  errorCode = apiError.error_code
  
  // 3. 分类处理
  IF code === 4001 OR code === 4004:
    // 认证错误
    IF errorCode === 'AUTH_TOKEN_EXPIRED':
      尝试刷新Token并重试
    ELSE:
      清除Token并跳转登录
  
  ELSE IF code === 4003 OR code === 4303:
    // 权限错误
    显示权限不足提示
  
  ELSE IF code === 4000 AND errorCode === 'VALIDATION_ERROR':
    // 验证错误（组件自己处理，这里不做全局提示）
    // 让错误传递给调用者
  
  ELSE IF code >= 4100 AND code < 5000:
    // 业务错误
    显示Toast提示: message
  
  ELSE IF code >= 5000:
    // 服务器错误
    显示错误提示: "服务器暂时不可用"
    记录错误日志
    上报监控系统（生产环境）
```

## 配置示例

### 基础配置

```
HTTP客户端基础配置:

baseURL: 
  开发环境: 'http://localhost:8000'
  生产环境: 'https://api.example.com'

timeout: 10000  // 10秒超时

headers:
  'Content-Type': 'application/json'
  'Accept': 'application/json'

withCredentials: false  // 是否发送Cookie（根据需求）
```

### 环境配置

```
根据环境调整配置:

IF 开发环境:
  启用详细日志
  显示请求/响应详情
  不上报错误监控
  超时时间: 30秒（方便调试）

IF 生产环境:
  关闭详细日志
  上报错误到监控系统
  超时时间: 10秒
  开启请求压缩
```

## 特殊场景处理

### 文件上传

```
文件上传配置:

FUNCTION uploadFile(file):
  创建FormData:
    formData = new FormData()
    formData.append('file', file)
  
  发送请求:
    URL: /api/v1/upload/
    Method: POST
    Body: formData
    Headers:
      // 不要设置Content-Type，让浏览器自动设置multipart/form-data
      // 保留Authorization等其他请求头
    
    onUploadProgress: 更新进度条

注意事项:
  - 文件上传不要设置Content-Type为application/json
  - 超时时间应该更长（根据文件大小）
  - 提供上传进度反馈
```

### 文件下载

```
文件下载配置:

FUNCTION downloadFile(url):
  发送请求:
    URL: url
    Method: GET
    ResponseType: 'blob'  // 二进制数据
  
  处理响应:
    IF 响应成功:
      创建下载链接并触发下载
    
    ELSE IF 响应失败:
      // Blob响应中的错误需要特殊处理
      blob = response.data
      text = await blob.text()
      errorData = JSON.parse(text)
      显示错误: errorData.message
```

### 并发请求控制

```
限制同时进行的请求数:

变量:
  pendingRequests = 0
  maxConcurrent = 5
  requestQueue = []

FUNCTION addRequest(requestFn):
  IF pendingRequests < maxConcurrent:
    执行请求(requestFn)
  ELSE:
    加入队列: requestQueue.push(requestFn)

FUNCTION onRequestComplete():
  pendingRequests--
  
  IF requestQueue不为空:
    nextRequest = requestQueue.shift()
    执行请求(nextRequest)
```

## 开发调试

### 请求日志格式

```
开发环境日志输出:

请求日志:
  📤 [POST] /api/v1/tenants/
  ├─ Headers: { Authorization: "Bearer...", X-Tenant-ID: "123" }
  ├─ Body: { name: "测试租户" }
  └─ Time: 2024-01-08 10:30:00

响应日志:
  📥 [POST] /api/v1/tenants/ - 250ms
  ├─ Status: 201
  ├─ Success: true
  ├─ Code: 2000
  └─ Data: { id: 456, name: "测试租户" }

错误日志:
  ❌ [POST] /api/v1/tenants/ - 180ms - FAILED
  ├─ Status: 400
  ├─ Code: 4000
  ├─ Error Code: VALIDATION_ERROR
  └─ Message: "数据验证失败"
```

### 调试工具

```
开发环境辅助功能:

1. 请求ID追踪
   每个请求添加唯一ID
   X-Request-ID: req_1641614400000_abc123

2. 请求耗时统计
   记录请求开始和结束时间
   计算并显示耗时

3. 错误详情展示
   开发环境显示完整错误对象
   包括堆栈、上下文等

4. 网络面板模拟
   在控制台输出类似Chrome DevTools的信息
```

## 实施检查清单

### HTTP客户端配置清单

- [ ] 配置了baseURL
- [ ] 设置了合理的timeout
- [ ] 添加了请求拦截器
- [ ] 添加了响应拦截器
- [ ] 实现了Token自动注入
- [ ] 实现了Token自动刷新（如果支持）
- [ ] 处理了网络错误
- [ ] 处理了超时错误
- [ ] 开发环境有详细日志

### 错误处理集成清单

- [ ] 统一的错误处理函数
- [ ] 根据错误码分类处理
- [ ] 认证错误自动跳转登录
- [ ] 权限错误有明确提示
- [ ] 验证错误传递给组件
- [ ] 业务错误显示message
- [ ] 服务器错误提供重试
- [ ] 网络错误提供重试

## 总结

### 核心要点

1. ✅ **请求拦截** - 自动注入Token和租户ID
2. ✅ **响应拦截** - 统一处理所有错误
3. ✅ **Token管理** - 自动刷新，无感知更新
4. ✅ **重试机制** - 可恢复错误自动重试
5. ✅ **框架无关** - 概念适用于任何HTTP客户端

### 实施优先级

**P0（必须）：**
- 请求/响应拦截器
- Token注入
- 基本错误处理

**P1（重要）：**
- Token刷新
- 错误分类处理
- 用户友好提示

**P2（可选）：**
- 请求重试
- 请求缓存
- 进度监控

---

**下一步**: 阅读 [常见场景处理方案](./05_common_scenarios.md)

**维护者**: Lipeaks Frontend Team  
**最后更新**: 2025-01-08

