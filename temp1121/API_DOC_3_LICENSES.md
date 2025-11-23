# Licenses API 文档

## 基础信息

**Base URL**: `http://localhost:8000/api/v1/licenses`  
**认证方式**: JWT Bearer Token  
**必需请求头**:
- `Authorization: Bearer {token}`
- `Tenant-ID: {tenant_id}`

---

## License Plans API

### 1. 获取许可方案列表

**GET** `/license-plans/`

```bash
curl "http://localhost:8000/api/v1/licenses/license-plans/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1"
```

**响应示例**:
```json
{
  "success": true,
  "data": {
    "count": 3,
    "results": [
      {
        "id": 1,
        "name": "专业版",
        "code": "PRO",
        "plan_type": "professional",
        "application": 1,
        "price": 999.00,
        "default_max_activations": 5,
        "default_validity_days": 365
      }
    ]
  }
}
```

---

### 2. 创建许可方案

**POST** `/license-plans/`

```bash
curl -X POST "http://localhost:8000/api/v1/licenses/license-plans/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "企业版",
    "code": "ENT",
    "plan_type": "enterprise",
    "application": 1,
    "price": 9999.00,
    "default_max_activations": 100,
    "default_validity_days": 365
  }'
```

---

## Licenses API

### 1. 获取许可证列表

**GET** `/licenses/`

```bash
curl "http://localhost:8000/api/v1/licenses/licenses/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1"
```

---

### 2. 创建许可证

**POST** `/licenses/`

```bash
curl -X POST "http://localhost:8000/api/v1/licenses/licenses/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Tenant-ID: 1" \
  -H "Content-Type: application/json" \
  -d '{
    "application": 1,
    "plan": 1,
    "member": 1,
    "max_activations": 5,
    "validity_days": 365
  }'
```

---

### 3. 验证许可证

**POST** `/licenses/verify/`

```bash
curl -X POST "http://localhost:8000/api/v1/licenses/licenses/verify/" \
  -H "Content-Type: application/json" \
  -d '{
    "license_key": "LPKS-XXXX-XXXX-XXXX-XXXX",
    "machine_code": "MACHINE123",
    "application_id": 1
  }'
```

---

### 4. 激活许可证

**POST** `/licenses/activate/`

```bash
curl -X POST "http://localhost:8000/api/v1/licenses/licenses/activate/" \
  -H "Content-Type: application/json" \
  -d '{
    "license_key": "LPKS-XXXX-XXXX-XXXX-XXXX",
    "machine_code": "MACHINE123",
    "application_id": 1
  }'
```

---

## 注意事项

1. **product字段已重命名为application** - 使用application替代原有的product
2. **SoftwareProduct已删除** - 直接使用Application模型
3. **密钥格式** - LPKS-XXXX-XXXX-XXXX-XXXX
4. **激活限制** - 每个许可证有最大激活数限制
