# 系统信息 API 实现文档

## 概述

已成功实现**系统版本信息 API**，返回系统版本、运行环境、启用的功能模块等信息。

---

## API 信息

### 基本信息

- **路径**: `GET /api/v1/common/system-info/`
- **权限**: 公开访问（无需认证）
- **标签**: `系统`
- **版本**: v1

---

## 实现内容

### 1. 版本号定义

**文件**: `core/__init__.py`

```python
"""LiPeaks Backend - 企业级多租户SaaS平台后端系统"""

__version__ = '1.0.3'
__author__ = 'LiPeaks Team'
__description__ = 'Enterprise Multi-Tenant SaaS Platform Backend'
```

**说明**: 
- 在核心模块定义系统版本号
- 统一版本管理，便于维护
- 可以在整个项目中导入使用

---

### 2. API 视图

**文件**: `common/views.py` (第697-841行)

**核心功能**:
```python
class SystemInfoView(APIView):
    """系统信息API"""
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['系统'],
        summary='获取系统信息',
        description='获取系统版本、环境、运行状态等基本信息',
        responses={200: ...}
    )
    def get(self, request):
        """获取系统信息"""
        # 返回版本、环境、Django版本、Python版本等
```

**返回的信息**:
- ✅ `version`: 系统版本号（从 `core.__version__` 读取）
- ✅ `environment`: 运行环境（development/production）
- ✅ `django_version`: Django 框架版本
- ✅ `python_version`: Python 版本
- ✅ `api_version`: API 版本（v1）
- ✅ `build_time`: 当前时间（ISO格式）
- ✅ `status`: 系统状态（running）
- ✅ `features`: 启用的功能模块列表

---

### 3. 路由配置

**文件**: `common/urls.py` (第22-23行)

```python
urlpatterns = [
    # 系统信息
    path('system-info/', SystemInfoView.as_view(), name='system-info'),
    # ...
]
```

**完整路径**: `/api/v1/common/system-info/`

---

## API 响应示例

### 成功响应

**HTTP 200 OK**

```json
{
    "success": true,
    "code": 2000,
    "message": "获取系统信息成功",
    "data": {
        "version": "1.0.3",
        "environment": "development",
        "django_version": "5.2.0",
        "python_version": "3.12.0",
        "api_version": "v1",
        "build_time": "2025-10-18T18:45:00.123456",
        "status": "running",
        "features": [
            "multi-tenant",
            "license-management",
            "rbac",
            "points-system",
            "order-management",
            "customer-management",
            "cms",
            "attendance-system"
        ]
    }
}
```

### 错误响应

**HTTP 500 Internal Server Error**

```json
{
    "success": false,
    "code": 5000,
    "message": "获取系统信息失败",
    "data": {
        "detail": "错误详情"
    }
}
```

---

## 功能模块映射

API 会根据 `INSTALLED_APPS` 自动识别启用的功能：

| INSTALLED_APPS | features 返回值 | 说明 |
|----------------|-----------------|------|
| `tenants` | `multi-tenant` | 多租户系统 |
| `licenses` | `license-management` | 许可证管理 |
| `rbac` | `rbac` | 权限系统 |
| `points` | `points-system` | 积分系统 |
| `orders` | `order-management` | 订单管理 |
| `customers` | `customer-management` | 客户管理 |
| `cms` | `cms` | 内容管理 |
| `check_system` | `attendance-system` | 打卡系统 |

---

## 使用示例

### cURL

```bash
curl -X GET "http://localhost:8000/api/v1/common/system-info/" \
  -H "Accept: application/json"
```

### JavaScript (Fetch)

```javascript
fetch('http://localhost:8000/api/v1/common/system-info/')
  .then(response => response.json())
  .then(data => {
    console.log('系统版本:', data.data.version);
    console.log('运行环境:', data.data.environment);
    console.log('启用功能:', data.data.features);
  });
```

### Python (requests)

```python
import requests

response = requests.get('http://localhost:8000/api/v1/common/system-info/')
data = response.json()

print(f"系统版本: {data['data']['version']}")
print(f"运行环境: {data['data']['environment']}")
print(f"启用功能: {', '.join(data['data']['features'])}")
```

### Axios

```javascript
import axios from 'axios';

const getSystemInfo = async () => {
  try {
    const response = await axios.get('/api/v1/common/system-info/');
    const { version, environment, features } = response.data.data;
    
    console.log(`系统版本: ${version}`);
    console.log(`运行环境: ${environment}`);
    console.log(`功能模块: ${features.join(', ')}`);
  } catch (error) {
    console.error('获取系统信息失败:', error);
  }
};
```

---

## OpenAPI/Swagger 文档

### 访问方式

1. **Swagger UI**: `http://localhost:8000/api/schema/swagger-ui/`
2. **ReDoc**: `http://localhost:8000/api/schema/redoc/`
3. **OpenAPI Schema**: `http://localhost:8000/api/schema/`

### 文档内容

- ✅ **标签**: `系统`
- ✅ **摘要**: "获取系统信息"
- ✅ **详细描述**: 包含完整的字段说明
- ✅ **响应示例**: 包含成功示例
- ✅ **字段说明**: 每个字段都有 `help_text`

### 文档截图示例

```
系统
  GET /api/v1/common/system-info/  获取系统信息
  
  返回信息
  - version: 系统版本号
  - environment: 运行环境 (development/production)
  - django_version: Django框架版本
  - python_version: Python版本
  - api_version: API版本
  - build_time: 系统构建时间
  - status: 系统运行状态
  - features: 启用的功能模块
```

---

## 前端集成示例

### React 组件

```jsx
import React, { useEffect, useState } from 'react';
import axios from 'axios';

function SystemInfo() {
  const [systemInfo, setSystemInfo] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSystemInfo = async () => {
      try {
        const response = await axios.get('/api/v1/common/system-info/');
        setSystemInfo(response.data.data);
      } catch (error) {
        console.error('获取系统信息失败:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchSystemInfo();
  }, []);

  if (loading) return <div>加载中...</div>;
  if (!systemInfo) return <div>获取系统信息失败</div>;

  return (
    <div className="system-info">
      <h2>系统信息</h2>
      <ul>
        <li>版本: {systemInfo.version}</li>
        <li>环境: {systemInfo.environment}</li>
        <li>Django: {systemInfo.django_version}</li>
        <li>Python: {systemInfo.python_version}</li>
        <li>状态: {systemInfo.status}</li>
      </ul>
      <h3>启用的功能模块</h3>
      <ul>
        {systemInfo.features.map(feature => (
          <li key={feature}>{feature}</li>
        ))}
      </ul>
    </div>
  );
}

export default SystemInfo;
```

### Vue 组件

```vue
<template>
  <div class="system-info">
    <h2>系统信息</h2>
    <div v-if="loading">加载中...</div>
    <div v-else-if="error">{{ error }}</div>
    <div v-else>
      <ul>
        <li>版本: {{ systemInfo.version }}</li>
        <li>环境: {{ systemInfo.environment }}</li>
        <li>Django: {{ systemInfo.django_version }}</li>
        <li>Python: {{ systemInfo.python_version }}</li>
        <li>状态: {{ systemInfo.status }}</li>
      </ul>
      <h3>启用的功能模块</h3>
      <ul>
        <li v-for="feature in systemInfo.features" :key="feature">
          {{ feature }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'SystemInfo',
  data() {
    return {
      systemInfo: null,
      loading: true,
      error: null
    };
  },
  async mounted() {
    try {
      const response = await axios.get('/api/v1/common/system-info/');
      this.systemInfo = response.data.data;
    } catch (err) {
      this.error = '获取系统信息失败';
      console.error(err);
    } finally {
      this.loading = false;
    }
  }
};
</script>
```

---

## 测试

### 单元测试示例

```python
# tests/test_system_info.py
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
import core

class SystemInfoAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = '/api/v1/common/system-info/'
    
    def test_get_system_info_success(self):
        """测试成功获取系统信息"""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(response.data['code'], 2000)
        
        data = response.data['data']
        self.assertEqual(data['version'], core.__version__)
        self.assertIn('environment', data)
        self.assertIn('django_version', data)
        self.assertIn('python_version', data)
        self.assertIn('features', data)
        self.assertIsInstance(data['features'], list)
    
    def test_system_info_no_auth_required(self):
        """测试无需认证即可访问"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_system_info_features(self):
        """测试功能模块列表"""
        response = self.client.get(self.url)
        features = response.data['data']['features']
        
        # 验证关键功能模块存在
        expected_features = [
            'multi-tenant',
            'license-management',
            'rbac'
        ]
        
        for feature in expected_features:
            self.assertIn(feature, features)
```

### 运行测试

```bash
# 运行所有测试
python manage.py test

# 运行系统信息 API 测试
python manage.py test tests.test_system_info

# 使用 pytest
pytest tests/test_system_info.py -v
```

---

## 版本更新流程

当需要更新系统版本时：

### 1. 更新版本号

编辑 `core/__init__.py`:

```python
__version__ = '1.0.4'  # 从 1.0.3 升级到 1.0.4
```

### 2. 记录变更日志

在 `CHANGELOG.md` 中记录：

```markdown
## [1.0.4] - 2025-10-19

### Added
- 新增 XXX 功能

### Fixed
- 修复 XXX 问题

### Changed
- 优化 XXX 逻辑
```

### 3. 无需重启

版本号是动态读取的，无需重启服务器。

### 4. 验证

```bash
curl http://localhost:8000/api/v1/common/system-info/ | jq '.data.version'
# 输出: "1.0.4"
```

---

## 日志记录

API 调用会自动记录日志：

```log
[INFO] 系统信息查询 - 版本: 1.0.3, 环境: development
[ERROR] 获取系统信息失败: <错误信息>
```

日志位置：`logs/common.log` 或控制台输出

---

## 安全性说明

### 公开访问

- ✅ 此 API 设置为 `AllowAny`，无需认证
- ✅ 仅返回基本系统信息，不涉及敏感数据
- ✅ 不返回数据库连接、密钥等敏感信息

### 如果需要限制访问

修改 `permission_classes`:

```python
class SystemInfoView(APIView):
    # 仅管理员可访问
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    # 或仅内部访问
    permission_classes = [IsAuthenticated, IsSuperAdmin]
```

---

## 扩展建议

### 1. 添加更多系统信息

```python
data = {
    # ... 现有字段
    'database': {
        'engine': 'mysql',
        'version': '8.0.33'
    },
    'cache': {
        'backend': 'redis',
        'version': '7.0.0'
    },
    'uptime': '2 days, 5 hours, 30 minutes',
    'server_time': datetime.now().isoformat(),
}
```

### 2. 添加健康检查

```python
'health': {
    'database': 'healthy',
    'cache': 'healthy',
    'storage': 'healthy',
    'overall': 'healthy'
}
```

### 3. 添加性能指标

```python
'performance': {
    'request_count': 12345,
    'avg_response_time': '150ms',
    'error_rate': '0.1%'
}
```

---

## 常见问题

### Q1: 如何修改版本号？

**A**: 编辑 `core/__init__.py` 文件：

```python
__version__ = '1.0.4'  # 修改这里
```

### Q2: 版本号格式有要求吗？

**A**: 建议遵循语义化版本（Semantic Versioning）：
- 主版本号.次版本号.修订号
- 例如：`1.0.3`、`2.1.0`、`1.2.5`

### Q3: 如何隐藏某些功能模块？

**A**: 修改 `SystemInfoView.get()` 方法，移除不想显示的模块判断。

### Q4: 是否需要缓存？

**A**: 系统信息变化不频繁，可以添加缓存：

```python
from django.core.cache import cache

def get(self, request):
    cache_key = 'system_info'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return Response(cached_data)
    
    # 生成数据...
    cache.set(cache_key, response_data, timeout=3600)  # 缓存1小时
    return Response(response_data)
```

---

## 总结

### 已实现功能

✅ 系统版本号定义  
✅ 系统信息 API 视图  
✅ OpenAPI/Swagger 文档注解  
✅ 路由配置  
✅ 功能模块自动识别  
✅ 标准响应格式  
✅ 错误处理  
✅ 日志记录  

### API 特点

- 📡 **RESTful**: 标准 HTTP GET 请求
- 🔓 **公开访问**: 无需认证（可配置）
- 📚 **完整文档**: drf_spectacular 自动生成
- 🎯 **灵活扩展**: 易于添加新字段
- ⚡ **高性能**: 轻量级查询，可缓存

---

**实现版本**: 1.0.3  
**实现日期**: 2025-10-18  
**API 路径**: `/api/v1/common/system-info/`  
**文件位置**: 
- `core/__init__.py`
- `common/views.py` (SystemInfoView)
- `common/urls.py`
