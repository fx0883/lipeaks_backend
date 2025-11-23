# OpenAPI / Swagger UI 使用指南

**版本**: v1.0  
**更新日期**: 2024-11-21  
**工具**: drf-spectacular  

---

## 📋 概述

本项目使用 `drf-spectacular` 自动生成 OpenAPI 3.0 规范文档，并提供交互式 API 测试界面。

---

## 🌐 访问API文档

### 1. Swagger UI（推荐）

**访问地址**: `http://localhost:8000/api/schema/swagger-ui/`

**特点**:
- ✅ 交互式API测试
- ✅ 实时请求/响应
- ✅ 参数自动补全
- ✅ 认证Token管理

**截图说明**:
```
┌─────────────────────────────────────────────┐
│  LiPeaks Backend API - Swagger UI          │
├─────────────────────────────────────────────┤
│  🔒 Authorize  [Bearer Token]              │
├─────────────────────────────────────────────┤
│  📁 Applications                            │
│    GET  /api/v1/applications/              │
│    POST /api/v1/applications/              │
│    GET  /api/v1/applications/{id}/         │
│    ...                                      │
│  📁 CMS                                     │
│  📁 Licenses                                │
│  📁 Feedbacks                               │
└─────────────────────────────────────────────┘
```

### 2. ReDoc（文档查看）

**访问地址**: `http://localhost:8000/api/schema/redoc/`

**特点**:
- ✅ 三栏布局，易于阅读
- ✅ 完整的模型定义
- ✅ 请求/响应示例
- ✅ 适合打印和导出

### 3. OpenAPI Schema（原始JSON）

**访问地址**: `http://localhost:8000/api/schema/`

**用途**:
- 导入到 Postman
- 生成客户端SDK
- 自动化测试
- API版本管理

---

## 🔐 认证配置

### Step 1: 获取Token

使用登录API获取JWT Token：

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "your_password"
  }'
```

**响应**:
```json
{
  "success": true,
  "data": {
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {
      "id": 1,
      "username": "admin",
      "tenant_id": 1
    }
  }
}
```

### Step 2: 在Swagger UI中配置认证

1. 点击页面右上角的 `🔒 Authorize` 按钮
2. 在弹出对话框中输入：
   ```
   Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
   ```
3. 点击 `Authorize` 确认
4. 关闭对话框

### Step 3: 添加Tenant-ID（可选）

某些API需要Tenant-ID头部，在Swagger UI中：
1. 展开要测试的API
2. 找到 `Parameters` 部分
3. 输入 `Tenant-ID` 值（如：1）

---

## 🧪 使用Swagger UI测试API

### 示例1: 获取应用列表

**步骤**:
1. 导航到 `Applications` 分组
2. 展开 `GET /api/v1/applications/`
3. 点击 `Try it out` 按钮
4. （可选）填写查询参数：
   - `page`: 1
   - `is_active`: true
5. 点击 `Execute` 按钮

**结果**:
- 请求URL会自动生成
- curl命令会自动显示
- 响应状态码和数据实时显示

**示例输出**:
```
Responses
─────────────────────────────────────
Code: 200
Details
Response body:
{
  "success": true,
  "data": {
    "count": 5,
    "results": [
      {
        "id": 1,
        "name": "LiPeaks CMS",
        "code": "lipeaks-cms",
        "current_version": "1.0.0"
      }
    ]
  }
}

Response headers:
content-type: application/json
...

Curl:
curl -X 'GET' \
  'http://localhost:8000/api/v1/applications/?is_active=true' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJ0eXAi...'
```

---

### 示例2: 创建应用

**步骤**:
1. 导航到 `POST /api/v1/applications/`
2. 点击 `Try it out`
3. 在Request body中填写JSON：
   ```json
   {
     "name": "测试应用",
     "code": "test-app",
     "description": "用于测试",
     "owner": "开发团队",
     "team": "技术部"
   }
   ```
4. 点击 `Execute`

---

### 示例3: 创建反馈

**步骤**:
1. 导航到 `Feedbacks` → `POST /api/v1/feedbacks/feedbacks/`
2. 点击 `Try it out`
3. 填写Request body：
   ```json
   {
     "title": "登录问题",
     "description": "无法登录系统",
     "feedback_type": "bug",
     "priority": "high",
     "application": 1,
     "contact_email": "user@example.com"
   }
   ```
4. 点击 `Execute`

---

## 📥 导出到Postman

### 方法1: 导入OpenAPI Schema

1. 访问 `http://localhost:8000/api/schema/`
2. 复制整个JSON内容
3. 打开Postman → Import
4. 选择 "Raw text"
5. 粘贴JSON
6. 点击 "Import"

### 方法2: 使用URL直接导入

1. 打开Postman → Import
2. 选择 "Link"
3. 输入: `http://localhost:8000/api/schema/`
4. 点击 "Import"

**导入后**:
- 所有API端点自动创建
- 请求参数自动配置
- 响应示例自动添加
- 需要手动配置认证Token

---

## 🔍 搜索和过滤

### Swagger UI搜索功能

在Swagger UI页面右上角有搜索框：
- 输入关键词（如 "feedback"）
- 自动高亮匹配的API
- 点击结果快速跳转

### 按Tag分组

API已按模块分组：
- **Applications** - 应用管理
- **CMS** - 内容管理
- **Licenses** - 许可证管理
- **Feedbacks** - 反馈管理
- **Auth** - 认证相关

---

## 📝 模型（Schemas）定义

Swagger UI底部 `Schemas` 部分包含所有数据模型定义：

**示例**: Application模型
```json
{
  "type": "object",
  "properties": {
    "id": {"type": "integer", "readOnly": true},
    "name": {"type": "string", "maxLength": 100},
    "code": {"type": "string", "maxLength": 50},
    "current_version": {
      "type": "string",
      "maxLength": 50,
      "default": "1.0.0"
    },
    "status": {
      "enum": ["development", "testing", "active", "maintenance", "deprecated", "archived"]
    }
  },
  "required": ["name", "code", "owner", "team"]
}
```

---

## ⚙️ 配置说明

### drf-spectacular设置

在 `settings.py` 中的配置：

```python
SPECTACULAR_SETTINGS = {
    'TITLE': 'LiPeaks Backend API',
    'DESCRIPTION': 'LiPeaks 多租户后端系统API文档',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/v1/',
}
```

---

## 🎯 最佳实践

### 1. API开发流程

```
1. 编写视图和序列化器
   ↓
2. 访问Swagger UI查看自动生成的文档
   ↓
3. 在Swagger UI中测试API
   ↓
4. 发现问题 → 修改代码
   ↓
5. 刷新页面重新测试
   ↓
6. 导出OpenAPI Schema给前端
```

### 2. 添加API描述

在ViewSet中使用装饰器：

```python
from drf_spectacular.utils import extend_schema, OpenApiParameter

@extend_schema(
    tags=['Applications'],
    summary='获取应用列表',
    description='获取当前租户的所有应用，支持分页和过滤',
    parameters=[
        OpenApiParameter('is_active', bool, description='是否激活'),
        OpenApiParameter('status', str, description='应用状态'),
    ],
    responses={200: ApplicationListSerializer(many=True)}
)
def list(self, request):
    ...
```

### 3. 添加请求/响应示例

```python
from drf_spectacular.utils import extend_schema, OpenApiExample

@extend_schema(
    examples=[
        OpenApiExample(
            '创建应用示例',
            value={
                'name': 'CMS系统',
                'code': 'cms-v1',
                'owner': '张三',
                'team': 'CMS团队'
            },
            request_only=True
        ),
    ]
)
def create(self, request):
    ...
```

---

## 🚀 生产环境配置

### 禁用Swagger UI（生产）

在生产环境的 `settings.py`：

```python
if not DEBUG:
    SPECTACULAR_SETTINGS['SERVE_PERMISSIONS'] = ['rest_framework.permissions.IsAdminUser']
```

### 生成静态文档

```bash
python manage.py spectacular --file schema.yml
```

将生成的 `schema.yml` 部署到文档服务器。

---

## ❓ 常见问题

### Q1: Swagger UI显示401错误？
**A**: 检查认证Token是否已配置：
1. 点击 `Authorize` 按钮
2. 输入 `Bearer <token>`
3. 确认Tenant-ID头部正确

### Q2: 某个API没有显示？
**A**: 检查：
1. ViewSet是否注册到router
2. URL配置是否正确
3. 权限设置是否过于严格

### Q3: 如何隐藏某个API？
**A**: 在ViewSet的action上：
```python
@extend_schema(exclude=True)
def internal_method(self, request):
    ...
```

### Q4: 响应格式不对？
**A**: 确保serializer_class正确设置：
```python
class MyViewSet(viewsets.ModelViewSet):
    serializer_class = MySerializer  # 必须设置
```

---

## 📚 相关资源

- **drf-spectacular文档**: https://drf-spectacular.readthedocs.io/
- **OpenAPI规范**: https://spec.openapis.org/oas/v3.0.0
- **Swagger UI**: https://swagger.io/tools/swagger-ui/
- **ReDoc**: https://redocly.com/redoc/

---

## 🎉 总结

使用Swagger UI可以：
- ✅ 实时测试所有API
- ✅ 自动生成curl命令
- ✅ 查看完整的请求/响应示例
- ✅ 导出给前端团队
- ✅ 生成客户端SDK

**立即开始**: 访问 `http://localhost:8000/api/schema/swagger-ui/` 🚀
