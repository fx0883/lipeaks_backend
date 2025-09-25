# API层设计

## 🎯 设计目标

### RESTful接口
- **标准化设计**: 遵循REST API设计规范
- **资源导向**: 以资源为中心的API设计
- **状态无关**: API调用之间无状态依赖

### 用户体验
- **直观易用**: API命名和结构符合直觉
- **文档完整**: 自动生成的API文档
- **错误友好**: 清晰的错误信息和状态码

## 🏗️ API架构设计

```
                    ┌─────────────────────────────────────┐
                    │            API网关层                 │
                    │                                     │
                    │ • 认证授权     • 限流控制           │
                    │ • 请求路由     • 日志记录           │
                    └─────────────────┬───────────────────┘
                                     │
                    ┌─────────────────┴───────────────────┐
                    │            API控制器层               │
                    └─────────────────┬───────────────────┘
                                     │
            ┌────────────────────────┼────────────────────────┐
            │                        │                        │
   ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
   │  管理员API      │      │   用户API       │      │   报表API       │
   │                 │      │                 │      │                 │
   │• 许可证分配管理 │      │• 个人许可证查询 │      │• 统计报表       │
   │• 批量操作       │      │• 许可证激活     │      │• 使用分析       │
   │• 系统管理       │      │• 状态查询       │      │• 审计日志       │
   └─────────────────┘      └─────────────────┘      └─────────────────┘
            │                        │                        │
            └────────────────────────┼────────────────────────┘
                                     │
                    ┌─────────────────┴───────────────────┐
                    │           应用服务层                 │
                    │                                     │
                    │ • 业务逻辑协调   • 事务管理         │
                    │ • 数据验证       • 异常处理         │
                    └─────────────────────────────────────┘
```

## 🔧 核心API端点设计

### 1. 许可证分配管理API

#### 基础资源路径
```
/api/v1/license-assignments/
```

#### 端点设计

##### 获取分配列表
```http
GET /api/v1/license-assignments/
```

**查询参数**:
- `member_id`: 按成员ID过滤
- `license_id`: 按许可证ID过滤  
- `status`: 按状态过滤 (assigned/active/suspended/revoked/expired)
- `tenant_id`: 按租户ID过滤 (自动根据当前用户租户)
- `expires_before`: 在指定日期前过期
- `assigned_after`: 在指定日期后分配
- `page`: 页码
- `page_size`: 每页数量
- `ordering`: 排序字段

**响应示例**:
```json
{
  "success": true,
  "data": {
    "count": 156,
    "next": "http://api.example.com/api/v1/license-assignments/?page=2",
    "previous": null,
    "results": [
      {
        "id": 1,
        "member": {
          "id": 10,
          "username": "john_doe",
          "email": "john@example.com"
        },
        "license": {
          "id": 5,
          "license_key": "ABC-DEF-GHI",
          "product_name": "SuperApp Pro",
          "plan_name": "专业版"
        },
        "status": "active",
        "assigned_at": "2024-09-01T10:00:00Z",
        "activated_at": "2024-09-01T14:30:00Z",
        "expires_at": "2025-09-01T10:00:00Z",
        "assignment_type": "user_request",
        "assignment_reason": "申请使用专业版功能",
        "days_until_expiry": 342,
        "license_quota": {
          "max_activations": 10,
          "current_activations": 3,
          "available_slots": 7
        }
      }
    ]
  }
}
```

##### 创建许可证分配
```http
POST /api/v1/license-assignments/
```

**请求体**:
```json
{
  "member_id": 10,
  "license_id": 5,
  "assignment_type": "user_request",
  "expires_days": 365,
  "assignment_reason": "申请使用专业版功能",
  "assignment_notes": "用于开发项目使用"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "许可证分配成功",
  "data": {
    "assignment_id": 157,
    "status": "assigned",
    "assigned_at": "2024-09-24T10:00:00Z",
    "expires_at": "2025-09-24T10:00:00Z"
  }
}
```

##### 批量分配操作
```http
POST /api/v1/license-assignments/batch-assign/
```

**请求体**:
```json
{
  "assignments": [
    {
      "member_id": 10,
      "license_id": 5,
      "assignment_type": "group_assign"
    },
    {
      "member_id": 11,
      "license_id": 5,
      "assignment_type": "group_assign"
    }
  ],
  "common_settings": {
    "expires_days": 365,
    "assignment_reason": "开发团队统一申请",
    "assignment_notes": "批量分配给开发团队成员"
  }
}
```

##### 撤销许可证分配
```http
POST /api/v1/license-assignments/{id}/revoke/
```

**请求体**:
```json
{
  "reason": "用户离职，回收许可证"
}
```

##### 暂停/恢复分配
```http
POST /api/v1/license-assignments/{id}/suspend/
POST /api/v1/license-assignments/{id}/resume/
```

##### 获取分配详情
```http
GET /api/v1/license-assignments/{id}/
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "id": 1,
    "member": {
      "id": 10,
      "username": "john_doe",
      "email": "john@example.com",
      "display_name": "John Doe"
    },
    "license": {
      "id": 5,
      "license_key": "ABC-DEF-GHI",
      "product": {
        "id": 2,
        "name": "SuperApp Pro",
        "version": "2.1.0"
      },
      "plan": {
        "id": 3,
        "name": "专业版",
        "features": {
          "max_projects": 50,
          "advanced_features": true,
          "priority_support": true
        }
      }
    },
    "status": "active",
    "assignment_type": "user_request",
    "assigned_at": "2024-09-01T10:00:00Z",
    "activated_at": "2024-09-01T14:30:00Z",
    "last_used_at": "2024-09-24T08:15:00Z",
    "expires_at": "2025-09-01T10:00:00Z",
    "assignment_reason": "申请使用专业版功能",
    "assignment_notes": "用于开发项目使用",
    "license_limits": {
      "max_activations": 10,
      "current_activations": 3,
      "max_machines_per_license": 5
    },
    "device_bindings": [
      {
        "device_id": "DESKTOP-ABC123",
        "bound_at": "2024-09-01T14:30:00Z",
        "last_seen_at": "2024-09-24T08:15:00Z",
        "status": "active"
      }
    ],
    "usage_stats": {
      "total_usage_hours": 120.5,
      "last_7_days_usage": 25.2,
      "avg_daily_usage": 3.6
    }
  }
}
```

### 2. 用户许可证API

#### 基础资源路径
```
/api/v1/user/licenses/
```

#### 端点设计

##### 获取当前用户的许可证列表
```http
GET /api/v1/user/licenses/
```

**查询参数**:
- `status`: 状态过滤
- `product_id`: 产品过滤
- `include_expired`: 是否包含过期的许可证

##### 激活许可证
```http
POST /api/v1/user/licenses/{assignment_id}/activate/
```

**请求体**:
```json
{
  "device_info": {
    "device_id": "DESKTOP-XYZ789",
    "device_name": "John's Workstation",
    "hardware_fingerprint": "abc123def456...",
    "os_info": {
      "name": "Windows 11",
      "version": "10.0.22000"
    }
  }
}
```

##### 查看许可证使用详情
```http
GET /api/v1/user/licenses/{assignment_id}/usage/
```

##### 解绑设备
```http
POST /api/v1/user/licenses/{assignment_id}/unbind-device/
```

**请求体**:
```json
{
  "device_id": "DESKTOP-ABC123"
}
```

### 3. 统计报表API

#### 基础资源路径
```
/api/v1/reports/
```

#### 端点设计

##### 许可证使用统计
```http
GET /api/v1/reports/license-usage/
```

**查询参数**:
- `tenant_id`: 租户ID过滤
- `product_id`: 产品ID过滤
- `date_from`: 开始日期
- `date_to`: 结束日期
- `group_by`: 分组方式 (product/plan/user/date)

##### 到期预警报告
```http
GET /api/v1/reports/expiry-alerts/
```

**查询参数**:
- `alert_days`: 预警天数 (默认30天)
- `tenant_id`: 租户过滤

##### 用户活跃度报告
```http
GET /api/v1/reports/user-activity/
```

## 🔒 认证与授权设计

### 认证机制
```
JWT Bearer Token认证流程:

1. 用户登录 → 获取JWT Token
2. API请求携带 Authorization: Bearer <token>
3. 中间件验证Token有效性
4. 解析用户身份和权限信息
5. 传递给后续处理逻辑
```

### 权限控制
```
租户内分层权限设计:

┌─────────────────┐
│   租户管理员     │ ← 租户范围管理权限
├─────────────────┤
│   普通成员       │ ← 个人数据访问权限
└─────────────────┘
```

### 权限装饰器
```python
# 示例权限控制
@api_view(['POST'])
@permission_classes([IsTenantAdmin])
def assign_license(request):
    """分配许可证 - 需要管理员权限"""
    pass

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_licenses(request):
    """获取用户许可证 - 需要认证"""
    pass
```

## 📊 API文档设计

### Swagger/OpenAPI集成
```python
# API文档装饰器示例
@extend_schema(
    tags=['许可证分配管理'],
    summary='创建许可证分配',
    description='为指定成员分配许可证，支持多种分配类型和配置选项',
    request=LicenseAssignmentCreateSerializer,
    responses={
        201: OpenApiResponse(
            response=LicenseAssignmentSerializer,
            description='分配创建成功'
        ),
        400: OpenApiResponse(description='请求参数错误'),
        403: OpenApiResponse(description='权限不足'),
        404: OpenApiResponse(description='资源不存在')
    },
    examples=[
        OpenApiExample(
            'Direct Assignment',
            summary='直接分配示例',
            description='直接为用户分配许可证',
            value={
                "member_id": 10,
                "license_id": 5,
                "assignment_type": "direct",
                "max_concurrent_devices": 3
            }
        )
    ]
)
def create_assignment(request):
    pass
```

## 🔧 错误处理设计

### 标准错误响应格式
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数验证失败",
    "details": {
      "member_id": ["此字段为必填项"],
      "license_id": ["无效的许可证ID"]
    }
  },
  "timestamp": "2024-09-24T10:00:00Z",
  "request_id": "req_abc123def456"
}
```

### 错误类型定义
```python
class APIErrorCodes:
    # 认证错误
    AUTHENTICATION_FAILED = "AUTH_001"
    TOKEN_EXPIRED = "AUTH_002"
    TOKEN_INVALID = "AUTH_003"
    
    # 授权错误  
    PERMISSION_DENIED = "PERM_001"
    INSUFFICIENT_PRIVILEGES = "PERM_002"
    
    # 业务错误
    RESOURCE_NOT_FOUND = "BIZ_001"
    QUOTA_EXCEEDED = "BIZ_002"
    DUPLICATE_ASSIGNMENT = "BIZ_003"
    
    # 系统错误
    INTERNAL_SERVER_ERROR = "SYS_001"
    SERVICE_UNAVAILABLE = "SYS_002"
```

## 📈 性能优化

### 分页策略
```python
class StandardPagination(PageNumberPagination):
    """标准分页器"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'success': True,
            'data': {
                'count': self.page.paginator.count,
                'next': self.get_next_link(),
                'previous': self.get_previous_link(),
                'results': data,
                'page_info': {
                    'current_page': self.page.number,
                    'total_pages': self.page.paginator.num_pages,
                    'page_size': self.page_size
                }
            }
        })
```

### 缓存策略
```python
@cache_response(60 * 5)  # 5分钟缓存
@api_view(['GET'])
def get_license_stats(request):
    """获取许可证统计 - 带缓存"""
    pass

@vary_on_headers('Authorization')
@cache_response(60 * 10)  # 10分钟缓存，按用户区分
def get_user_licenses(request):
    """获取用户许可证 - 按用户缓存"""
    pass
```

### 批量操作优化
```python
class BatchOperationMixin:
    """批量操作混入类"""
    
    @action(detail=False, methods=['post'])
    def batch_create(self, request):
        """批量创建"""
        serializer = self.get_serializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        
        # 批量创建优化
        instances = self.perform_batch_create(serializer.validated_data)
        
        return Response({
            'success': True,
            'message': f'成功创建 {len(instances)} 条记录',
            'data': self.get_serializer(instances, many=True).data
        })
```

---

**下一步**: 查看[实施步骤](07_实施步骤.md)了解具体的实施计划和时间安排
