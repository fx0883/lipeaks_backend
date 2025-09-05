# 机器绑定注册码系统 API 设计

## 1. API设计原则

### 1.1 设计标准
- **RESTful架构**: 遵循REST设计原则
- **统一响应格式**: 与现有系统保持一致
- **版本化管理**: 使用`/api/v1/`前缀
- **JWT认证**: 集成现有认证体系
- **权限控制**: 基于RBAC权限管理

### 1.2 响应格式标准
```json
{
    "success": true/false,
    "code": 2000/4xxx/5xxx,
    "message": "操作结果描述",
    "data": {} // 实际数据或null
}
```

### 1.3 状态码规范
- `2000`: 操作成功
- `4000`: 请求参数错误
- `4001`: 认证失败
- `4002`: 登录失败
- `4003`: 权限不足
- `4004`: 资源不存在
- `4005`: 资源冲突
- `5000`: 服务器内部错误

## 2. API路由设计

### 2.1 路由结构
```
/api/v1/licenses/
├── products/                    # 软件产品管理
├── plans/                      # 许可方案管理
├── licenses/                   # 许可证管理
├── activations/               # 激活验证
├── bindings/                  # 机器绑定管理
└── reports/                   # 统计报告
```

### 2.2 URL配置
```python
# licenses/urls.py
from django.urls import path, include
from . import views

app_name = 'licenses'

urlpatterns = [
    # 软件产品管理
    path('products/', include([
        path('', views.ProductListCreateView.as_view(), name='product-list'),
        path('<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
        path('<int:pk>/plans/', views.ProductPlanListView.as_view(), name='product-plans'),
        path('<int:pk>/generate-keypair/', views.ProductGenerateKeypairView.as_view(), name='product-keypair'),
    ])),
    
    # 许可方案管理
    path('plans/', include([
        path('', views.PlanListCreateView.as_view(), name='plan-list'),
        path('<int:pk>/', views.PlanDetailView.as_view(), name='plan-detail'),
    ])),
    
    # 许可证管理
    path('licenses/', include([
        path('', views.LicenseListCreateView.as_view(), name='license-list'),
        path('<int:pk>/', views.LicenseDetailView.as_view(), name='license-detail'),
        path('generate/', views.LicenseGenerateView.as_view(), name='license-generate'),
        path('batch-generate/', views.LicenseBatchGenerateView.as_view(), name='license-batch-generate'),
        path('verify/', views.LicenseVerifyView.as_view(), name='license-verify'),
    ])),
    
    # 激活验证
    path('activations/', include([
        path('activate/', views.ActivationCreateView.as_view(), name='activation-create'),
        path('verify/', views.ActivationVerifyView.as_view(), name='activation-verify'),
        path('heartbeat/', views.ActivationHeartbeatView.as_view(), name='activation-heartbeat'),
        path('deactivate/', views.ActivationDeactivateView.as_view(), name='activation-deactivate'),
    ])),
    
    # 机器绑定管理
    path('bindings/', include([
        path('', views.BindingListView.as_view(), name='binding-list'),
        path('<int:pk>/', views.BindingDetailView.as_view(), name='binding-detail'),
        path('<int:pk>/unbind/', views.BindingUnbindView.as_view(), name='binding-unbind'),
    ])),
    
    # 统计报告
    path('reports/', include([
        path('dashboard/', views.ReportDashboardView.as_view(), name='report-dashboard'),
        path('usage/', views.ReportUsageView.as_view(), name='report-usage'),
        path('activations/', views.ReportActivationView.as_view(), name='report-activations'),
    ])),
]
```

## 3. 管理端API接口

### 3.1 软件产品管理

#### 3.1.1 创建软件产品
```http
POST /api/v1/licenses/products/
Authorization: Bearer <token>
Content-Type: application/json

{
    "name": "MyMacApp",
    "code": "MMA",
    "version": "1.0.0",
    "description": "一款优秀的macOS应用程序",
    "platform": "macos"
}
```

**响应示例**:
```json
{
    "success": true,
    "code": 2000,
    "message": "产品创建成功",
    "data": {
        "id": 1,
        "name": "MyMacApp",
        "code": "MMA",
        "version": "1.0.0",
        "description": "一款优秀的macOS应用程序",
        "platform": "macos",
        "status": "active",
        "public_key": "-----BEGIN PUBLIC KEY-----\n...",
        "created_at": "2025-09-05T10:00:00Z"
    }
}
```

#### 3.1.2 生成产品密钥对
```http
POST /api/v1/licenses/products/1/generate-keypair/
Authorization: Bearer <token>
```

**响应示例**:
```json
{
    "success": true,
    "code": 2000,
    "message": "密钥对生成成功",
    "data": {
        "public_key": "-----BEGIN PUBLIC KEY-----\n...",
        "private_key": "-----BEGIN PRIVATE KEY-----\n...",
        "warning": "请妥善保存私钥，系统不会存储私钥明文"
    }
}
```

### 3.2 许可方案管理

#### 3.2.1 创建许可方案
```http
POST /api/v1/licenses/plans/
Authorization: Bearer <token>
Content-Type: application/json

{
    "product_id": 1,
    "name": "专业版",
    "code": "PRO",
    "plan_type": "professional",
    "max_activations": 3,
    "validity_days": 365,
    "features": {
        "advanced_features": true,
        "cloud_sync": true,
        "priority_support": true
    },
    "price": 299.99
}
```

**响应示例**:
```json
{
    "success": true,
    "code": 2000,
    "message": "许可方案创建成功",
    "data": {
        "id": 1,
        "product": {
            "id": 1,
            "name": "MyMacApp",
            "code": "MMA"
        },
        "name": "专业版",
        "code": "PRO",
        "plan_type": "professional",
        "max_activations": 3,
        "validity_days": 365,
        "features": {
            "advanced_features": true,
            "cloud_sync": true,
            "priority_support": true
        },
        "price": "299.99",
        "status": "active"
    }
}
```

### 3.3 许可证管理

#### 3.3.1 生成许可证
```http
POST /api/v1/licenses/licenses/generate/
Authorization: Bearer <token>
Content-Type: application/json

{
    "plan_id": 1,
    "quantity": 1,
    "customer_info": {
        "name": "张三",
        "email": "zhangsan@example.com",
        "company": "示例公司"
    },
    "validity_days": 365,
    "notes": "企业客户订单"
}
```

**响应示例**:
```json
{
    "success": true,
    "code": 2000,
    "message": "许可证生成成功",
    "data": {
        "licenses": [
            {
                "id": 1,
                "license_key": "MMA1-PRO2-5F8A-9B3C-7E2D",
                "plan": {
                    "name": "专业版",
                    "max_activations": 3,
                    "validity_days": 365
                },
                "customer_info": {
                    "name": "张三",
                    "email": "zhangsan@example.com",
                    "company": "示例公司"
                },
                "issued_at": "2025-09-05T10:00:00Z",
                "expires_at": "2026-09-05T10:00:00Z",
                "status": "active",
                "activation_count": 0,
                "remaining_activations": 3
            }
        ]
    }
}
```

#### 3.3.2 批量生成许可证
```http
POST /api/v1/licenses/licenses/batch-generate/
Authorization: Bearer <token>
Content-Type: application/json

{
    "plan_id": 1,
    "quantity": 10,
    "batch_info": {
        "batch_name": "企业批次001",
        "customer_company": "示例企业集团"
    }
}
```

#### 3.3.3 许可证列表查询
```http
GET /api/v1/licenses/licenses/?page=1&size=20&status=active&plan_id=1
Authorization: Bearer <token>
```

**响应示例**:
```json
{
    "success": true,
    "code": 2000,
    "message": "查询成功",
    "data": {
        "count": 50,
        "next": "http://api.example.com/api/v1/licenses/licenses/?page=2",
        "previous": null,
        "results": [
            {
                "id": 1,
                "license_key": "MMA1-****-****-****-7E2D",
                "plan_name": "专业版",
                "customer_name": "张三",
                "status": "active",
                "activation_count": 1,
                "remaining_activations": 2,
                "issued_at": "2025-09-05T10:00:00Z",
                "expires_at": "2026-09-05T10:00:00Z"
            }
        ]
    }
}
```

## 4. 客户端激活API

### 4.1 许可证激活

#### 4.1.1 初始激活
```http
POST /api/v1/licenses/activations/activate/
Content-Type: application/json

{
    "license_key": "MMA1-PRO2-5F8A-9B3C-7E2D",
    "machine_info": {
        "hardware_uuid": "550e8400-e29b-41d4-a716-446655440000",
        "serial_number": "C02XG0FDH7JY",
        "mac_addresses": ["aa:bb:cc:dd:ee:ff"],
        "os_version": "macOS 14.5",
        "cpu_info": "Apple M1 Pro",
        "memory_size": 16384
    },
    "client_version": "1.0.0"
}
```

**响应示例**:
```json
{
    "success": true,
    "code": 2000,
    "message": "激活成功",
    "data": {
        "activation_certificate": {
            "license_id": 1,
            "machine_fingerprint": "abc123...",
            "activated_at": "2025-09-05T10:00:00Z",
            "expires_at": "2026-09-05T10:00:00Z",
            "features": {
                "advanced_features": true,
                "cloud_sync": true,
                "priority_support": true
            },
            "signature": "def456..."
        },
        "verification_interval": 86400,
        "offline_grace_period": 259200
    }
}
```

#### 4.1.2 激活验证
```http
POST /api/v1/licenses/activations/verify/
Content-Type: application/json

{
    "license_key": "MMA1-PRO2-5F8A-9B3C-7E2D",
    "machine_fingerprint": "abc123...",
    "client_version": "1.0.0"
}
```

**响应示例**:
```json
{
    "success": true,
    "code": 2000,
    "message": "验证成功",
    "data": {
        "status": "valid",
        "expires_at": "2026-09-05T10:00:00Z",
        "features": {
            "advanced_features": true,
            "cloud_sync": true,
            "priority_support": true
        },
        "next_verification": "2025-09-06T10:00:00Z"
    }
}
```

#### 4.1.3 心跳验证
```http
POST /api/v1/licenses/activations/heartbeat/
Content-Type: application/json

{
    "license_key": "MMA1-PRO2-5F8A-9B3C-7E2D",
    "machine_fingerprint": "abc123...",
    "session_info": {
        "start_time": "2025-09-05T09:00:00Z",
        "feature_usage": {
            "advanced_features": 15,
            "cloud_sync": 3
        }
    }
}
```

### 4.2 离线验证支持

#### 4.2.1 离线验证证书
```http
POST /api/v1/licenses/activations/offline-certificate/
Content-Type: application/json

{
    "license_key": "MMA1-PRO2-5F8A-9B3C-7E2D",
    "machine_fingerprint": "abc123...",
    "requested_duration": 604800  // 7天
}
```

**响应示例**:
```json
{
    "success": true,
    "code": 2000,
    "message": "离线证书生成成功",
    "data": {
        "offline_certificate": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9...",
        "valid_until": "2025-09-12T10:00:00Z",
        "certificate_id": "offline_cert_123"
    }
}
```

## 5. 管理统计API

### 5.1 仪表板数据

#### 5.1.1 概览统计
```http
GET /api/v1/licenses/reports/dashboard/
Authorization: Bearer <token>
```

**响应示例**:
```json
{
    "success": true,
    "code": 2000,
    "message": "查询成功",
    "data": {
        "summary": {
            "total_licenses": 1250,
            "active_licenses": 980,
            "total_activations": 2340,
            "active_machines": 1890
        },
        "recent_activations": [
            {
                "license_key": "MMA1-****-****-****-7E2D",
                "customer_name": "张三",
                "activated_at": "2025-09-05T10:00:00Z",
                "machine_info": "MacBook Pro (M1)"
            }
        ],
        "expiring_soon": [
            {
                "license_key": "MMA1-****-****-****-8F3E",
                "customer_name": "李四",
                "expires_at": "2025-09-15T10:00:00Z",
                "days_remaining": 10
            }
        ]
    }
}
```

### 5.2 使用情况报告

#### 5.2.1 激活统计
```http
GET /api/v1/licenses/reports/activations/?start_date=2025-09-01&end_date=2025-09-30
Authorization: Bearer <token>
```

**响应示例**:
```json
{
    "success": true,
    "code": 2000,
    "message": "查询成功",
    "data": {
        "period": {
            "start_date": "2025-09-01",
            "end_date": "2025-09-30"
        },
        "statistics": {
            "total_activations": 156,
            "successful_activations": 145,
            "failed_activations": 11,
            "success_rate": 92.9
        },
        "daily_stats": [
            {
                "date": "2025-09-05",
                "activations": 8,
                "verifications": 245,
                "unique_machines": 128
            }
        ],
        "top_products": [
            {
                "product_name": "MyMacApp",
                "activations": 98,
                "percentage": 62.8
            }
        ]
    }
}
```

## 6. 错误处理

### 6.1 常见错误响应

#### 6.1.1 无效注册码
```json
{
    "success": false,
    "code": 4004,
    "message": "注册码不存在或已失效",
    "data": {
        "error_type": "INVALID_LICENSE_KEY",
        "details": "The provided license key is not found in our system"
    }
}
```

#### 6.1.2 激活次数超限
```json
{
    "success": false,
    "code": 4005,
    "message": "激活次数已达上限",
    "data": {
        "error_type": "ACTIVATION_LIMIT_EXCEEDED",
        "max_activations": 3,
        "current_activations": 3,
        "details": "This license has reached its maximum activation limit"
    }
}
```

#### 6.1.3 机器绑定冲突
```json
{
    "success": false,
    "code": 4005,
    "message": "该注册码已绑定到其他设备",
    "data": {
        "error_type": "MACHINE_BINDING_CONFLICT",
        "bound_machine": "MacBook Pro (Partial: C02XG***H7JY)",
        "details": "This license is already bound to a different machine"
    }
}
```

### 6.2 服务器错误处理
```json
{
    "success": false,
    "code": 5000,
    "message": "服务器内部错误",
    "data": {
        "error_id": "ERR_20250905_001",
        "timestamp": "2025-09-05T10:00:00Z",
        "details": "An unexpected error occurred. Please contact support with error ID."
    }
}
```

## 7. API安全机制

### 7.1 认证授权
- **管理端API**: 需要JWT认证 + 管理员权限
- **客户端激活API**: 公开接口，但有频率限制
- **敏感操作**: 需要额外的操作确认

### 7.2 请求限制
```python
# 激活API限制
ACTIVATION_RATE_LIMIT = "10/hour"  # 每小时10次激活请求
VERIFICATION_RATE_LIMIT = "60/hour"  # 每小时60次验证请求
HEARTBEAT_RATE_LIMIT = "1440/day"  # 每天1440次心跳（每分钟1次）

# 管理端API限制  
ADMIN_RATE_LIMIT = "1000/hour"  # 每小时1000次管理操作
```

### 7.3 数据脱敏
- 许可证列表中的注册码部分掩码显示
- 机器信息中的敏感硬件信息脱敏
- 客户信息按权限级别显示

## 8. API文档生成

### 8.1 drf-spectacular配置
```python
# licenses/views/base_views.py
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample

@extend_schema(
    summary="激活许可证",
    description="使用注册码激活软件许可证并绑定到当前设备",
    request=ActivationSerializer,
    responses={
        200: OpenApiResponse(
            description="激活成功",
            examples=[OpenApiExample(
                name="激活成功示例",
                value={
                    "success": True,
                    "code": 2000,
                    "message": "激活成功",
                    "data": {"activation_certificate": "..."}
                }
            )]
        ),
        400: OpenApiResponse(description="请求参数错误"),
        404: OpenApiResponse(description="注册码不存在"),
        409: OpenApiResponse(description="激活冲突")
    },
    tags=["许可证激活"]
)
def post(self, request):
    # 实现激活逻辑
    pass
```

这个API设计充分考虑了与现有系统的集成，遵循了RESTful设计原则，并提供了完整的错误处理和安全机制。所有接口都支持OpenAPI文档自动生成，便于前端开发和测试。

---

*设计完成时间: 2025-09-05*  
*设计原则: RESTful架构、统一响应格式、安全可靠*
