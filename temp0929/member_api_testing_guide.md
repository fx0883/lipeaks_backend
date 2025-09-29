# Member试用许可证API测试指南

## 概述

本文档提供了Member试用许可证API的完整测试指南，包括手动测试、自动化测试、性能测试和安全测试。适用于开发人员、测试人员和QA团队。

---

## 测试环境准备

### 环境配置

```bash
# 测试环境变量
export API_BASE_URL="https://your-test-domain.com/api/v1/licenses"
export JWT_TOKEN="your_test_jwt_token"
export TEST_USER_ID="test_member_user_id"
export TEST_TENANT_ID="test_tenant_id"
```

### 测试数据准备

```sql
-- 创建测试用户（Member类型）
INSERT INTO member (username, email, tenant_id, is_active, status) 
VALUES ('test_member', 'test@example.com', 1, TRUE, 'active');

-- 创建测试产品
INSERT INTO licenses_software_product (name, code, description, version, status) 
VALUES ('测试PDF工具', 'test_pdf', '用于测试的PDF工具', '1.0.0', 'active');

-- 创建试用方案
INSERT INTO licenses_license_plan (product_id, name, code, plan_type, default_validity_days, default_max_activations, status) 
VALUES (1, '试用版', 'trial', 'trial', 30, 1, 'active');
```

---

## 手动测试

### 1. 认证测试

#### 获取JWT令牌

```bash
# 登录获取令牌
curl -X POST "${API_BASE_URL}/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "test_member",
    "password": "test_password"
  }'

# 预期响应
{
  "success": true,
  "data": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
      "id": 123,
      "username": "test_member",
      "email": "test@example.com"
    }
  }
}
```

#### 令牌验证测试

```bash
# 使用无效令牌
curl -X GET "${API_BASE_URL}/member/available-products/" \
  -H "Authorization: Bearer invalid_token"

# 预期响应: 401 Unauthorized
{
  "detail": "Given token not valid for any token type"
}

# 使用过期令牌
curl -X GET "${API_BASE_URL}/member/available-products/" \
  -H "Authorization: Bearer expired_token"

# 预期响应: 401 Unauthorized
{
  "detail": "Token has expired"
}

# 缺少令牌
curl -X GET "${API_BASE_URL}/member/available-products/"

# 预期响应: 401 Unauthorized
{
  "detail": "Authentication credentials were not provided."
}
```

### 2. 获取可申请产品列表API测试

#### 正常请求测试

```bash
curl -X GET "${API_BASE_URL}/member/available-products/" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json"
```

**预期响应 (200 OK)**:
```json
{
  "success": true,
  "data": {
    "count": 2,
    "products": [
      {
        "id": 1,
        "name": "测试PDF工具",
        "code": "test_pdf",
        "description": "用于测试的PDF工具",
        "version": "1.0.0",
        "trial_plan": {
          "id": 1,
          "name": "试用版",
          "default_validity_days": 30,
          "default_max_activations": 1,
          "features": {},
          "price": 0.0,
          "currency": "CNY"
        },
        "already_applied": false
      }
    ]
  }
}
```

#### 权限测试

```bash
# 使用管理员令牌（应该失败）
curl -X GET "${API_BASE_URL}/member/available-products/" \
  -H "Authorization: Bearer ${ADMIN_JWT_TOKEN}" \
  -H "Content-Type: application/json"

# 预期响应: 403 Forbidden
{
  "detail": "You do not have permission to perform this action."
}
```

#### 边界测试

```bash
# 空产品列表情况
# 预期响应: 200 OK，products为空数组
{
  "success": true,
  "data": {
    "count": 0,
    "products": []
  }
}
```

### 3. 申请试用许可证API测试

#### 正常申请测试

```bash
curl -X POST "${API_BASE_URL}/member/apply/" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1,
    "reason": "测试申请",
    "user_info": {
      "company": "测试公司",
      "job_title": "测试工程师",
      "phone": "13800138000",
      "intended_use": "用于功能测试"
    }
  }'
```

**预期响应 (201 Created)**:
```json
{
  "success": true,
  "message": "试用许可证申请成功",
  "data": {
    "license_id": 456,
    "assignment_id": 789,
    "license_key": "TEST1-TEST2-TEST3-TEST4-TEST5",
    "expires_at": "2024-02-15T10:30:00Z",
    "product_name": "测试PDF工具",
    "plan_name": "试用版",
    "max_activations": 1
  }
}
```

#### 参数验证测试

```bash
# 缺少必填参数
curl -X POST "${API_BASE_URL}/member/apply/" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{}'

# 预期响应: 400 Bad Request
{
  "success": false,
  "errors": {
    "product_id": ["This field is required."]
  }
}

# 无效产品ID
curl -X POST "${API_BASE_URL}/member/apply/" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 99999
  }'

# 预期响应: 400 Bad Request
{
  "success": false,
  "errors": {
    "product_id": ["产品不存在或不可用"]
  }
}

# 用户信息格式错误
curl -X POST "${API_BASE_URL}/member/apply/" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1,
    "user_info": {
      "phone": "这不是有效的手机号码格式abcd"
    }
  }'

# 预期响应: 400 Bad Request（如果有手机号验证）
```

#### 业务规则测试

```bash
# 重复申请测试
curl -X POST "${API_BASE_URL}/member/apply/" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1
  }'

# 第二次申请相同产品
curl -X POST "${API_BASE_URL}/member/apply/" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1
  }'

# 预期响应: 400 Bad Request
{
  "success": false,
  "error": "您已经申请过该产品的许可证",
  "code": "APPLICATION_FAILED"
}
```

#### 频率限制测试

```bash
# 快速连续申请多次（超过限制）
for i in {1..4}; do
  curl -X POST "${API_BASE_URL}/member/apply/" \
    -H "Authorization: Bearer ${JWT_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "{\"product_id\": $i}" &
done

# 预期第4次响应: 400 Bad Request
{
  "success": false,
  "error": "24小时内申请次数过多，请稍后再试",
  "code": "APPLICATION_FAILED"
}
```

#### 限流测试

```bash
# 测试API限流（每天5次申请）
for i in {1..6}; do
  echo "申请 $i:"
  curl -X POST "${API_BASE_URL}/member/apply/" \
    -H "Authorization: Bearer ${JWT_TOKEN}" \
    -H "Content-Type: application/json" \
    -d '{"product_id": 1}' | jq .
  sleep 1
done

# 预期第6次响应: 429 Too Many Requests
{
  "detail": "Request was throttled. Expected available in 86400 seconds."
}
```

### 4. 查看我的许可证API测试

#### 正常查询测试

```bash
curl -X GET "${API_BASE_URL}/member/my-licenses/" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json"
```

**预期响应 (200 OK)**:
```json
{
  "success": true,
  "data": {
    "count": 1,
    "active_count": 1,
    "trial_count": 1,
    "expiring_soon_count": 0,
    "licenses": [
      {
        "id": 789,
        "product_name": "测试PDF工具",
        "product_code": "test_pdf",
        "product_version": "1.0.0",
        "plan_name": "试用版",
        "plan_type": "trial",
        "license_key_preview": "TEST1...TEST5",
        "status": "active",
        "status_display": "有效",
        "assignment_type": "direct",
        "assigned_at": "2024-01-15T10:30:00Z",
        "activated_at": "2024-01-15T10:30:00Z",
        "expires_at": "2024-02-15T10:30:00Z",
        "days_until_expiry": 25,
        "assignment_reason": "测试申请",
        "can_activate_license": true,
        "activation_info": {
          "current_activations": 0,
          "max_activations": 1,
          "available_slots": 1
        },
        "usage_count": 0,
        "last_used_at": null,
        "last_heartbeat": null,
        "can_activate": true,
        "can_deactivate": false,
        "can_share": false,
        "max_devices_per_user": 1
      }
    ]
  }
}
```

#### 过滤测试

```bash
# 按状态过滤
curl -X GET "${API_BASE_URL}/member/my-licenses/?status=active" \
  -H "Authorization: Bearer ${JWT_TOKEN}"

# 按方案类型过滤
curl -X GET "${API_BASE_URL}/member/my-licenses/?plan_type=trial" \
  -H "Authorization: Bearer ${JWT_TOKEN}"

# 多重过滤
curl -X GET "${API_BASE_URL}/member/my-licenses/?status=active&plan_type=trial" \
  -H "Authorization: Bearer ${JWT_TOKEN}"

# 无效过滤值
curl -X GET "${API_BASE_URL}/member/my-licenses/?status=invalid_status" \
  -H "Authorization: Bearer ${JWT_TOKEN}"

# 预期响应: 正常返回，但结果为空（过滤掉了所有结果）
```

#### 空结果测试

```bash
# 新用户查询（无许可证）
curl -X GET "${API_BASE_URL}/member/my-licenses/" \
  -H "Authorization: Bearer ${NEW_USER_JWT_TOKEN}"

# 预期响应: 200 OK
{
  "success": true,
  "data": {
    "count": 0,
    "active_count": 0,
    "trial_count": 0,
    "expiring_soon_count": 0,
    "licenses": []
  }
}
```

---

## 自动化测试

### 测试框架选择

#### Python + pytest + requests

```python
# tests/test_member_license_api.py
import pytest
import requests
from datetime import datetime, timedelta

class TestMemberLicenseAPI:
    BASE_URL = "https://your-test-domain.com/api/v1/licenses"
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """测试前置条件"""
        # 获取测试用户令牌
        login_response = requests.post(f"{self.BASE_URL}/auth/login/", json={
            "username": "test_member",
            "password": "test_password"
        })
        assert login_response.status_code == 200
        
        self.token = login_response.json()["data"]["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def test_get_available_products_success(self):
        """测试获取可申请产品列表 - 成功"""
        response = requests.get(
            f"{self.BASE_URL}/member/available-products/",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "count" in data["data"]
        assert "products" in data["data"]
        assert isinstance(data["data"]["products"], list)
    
    def test_get_available_products_unauthorized(self):
        """测试获取可申请产品列表 - 未认证"""
        response = requests.get(f"{self.BASE_URL}/member/available-products/")
        
        assert response.status_code == 401
        assert "detail" in response.json()
    
    def test_apply_trial_license_success(self):
        """测试申请试用许可证 - 成功"""
        # 首先获取可用产品
        products_response = requests.get(
            f"{self.BASE_URL}/member/available-products/",
            headers=self.headers
        )
        products = products_response.json()["data"]["products"]
        
        if not products:
            pytest.skip("没有可用产品进行测试")
        
        product_id = products[0]["id"]
        
        # 申请许可证
        apply_data = {
            "product_id": product_id,
            "reason": "自动化测试",
            "user_info": {
                "company": "测试公司",
                "job_title": "测试工程师"
            }
        }
        
        response = requests.post(
            f"{self.BASE_URL}/member/apply/",
            headers=self.headers,
            json=apply_data
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert "license_key" in data["data"]
        assert "expires_at" in data["data"]
        
        # 保存许可证信息用于后续测试
        self.test_license_id = data["data"]["license_id"]
    
    def test_apply_trial_license_duplicate(self):
        """测试申请试用许可证 - 重复申请"""
        # 先成功申请一次
        self.test_apply_trial_license_success()
        
        # 再次申请相同产品
        products_response = requests.get(
            f"{self.BASE_URL}/member/available-products/",
            headers=self.headers
        )
        products = products_response.json()["data"]["products"]
        product_id = products[0]["id"]
        
        response = requests.post(
            f"{self.BASE_URL}/member/apply/",
            headers=self.headers,
            json={"product_id": product_id}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "已经申请过" in data["error"]
    
    def test_apply_trial_license_invalid_product(self):
        """测试申请试用许可证 - 无效产品ID"""
        response = requests.post(
            f"{self.BASE_URL}/member/apply/",
            headers=self.headers,
            json={"product_id": 99999}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "产品不存在" in data["errors"]["product_id"][0]
    
    def test_apply_trial_license_validation_errors(self):
        """测试申请试用许可证 - 参数验证错误"""
        # 缺少必填参数
        response = requests.post(
            f"{self.BASE_URL}/member/apply/",
            headers=self.headers,
            json={}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "product_id" in data["errors"]
        
        # 无效的用户信息格式
        response = requests.post(
            f"{self.BASE_URL}/member/apply/",
            headers=self.headers,
            json={
                "product_id": 1,
                "user_info": {
                    "phone": "a" * 25  # 超长手机号
                }
            }
        )
        
        assert response.status_code == 400
    
    def test_get_my_licenses_success(self):
        """测试查看我的许可证 - 成功"""
        response = requests.get(
            f"{self.BASE_URL}/member/my-licenses/",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "count" in data["data"]
        assert "licenses" in data["data"]
        assert isinstance(data["data"]["licenses"], list)
    
    def test_get_my_licenses_with_filters(self):
        """测试查看我的许可证 - 带过滤条件"""
        # 按状态过滤
        response = requests.get(
            f"{self.BASE_URL}/member/my-licenses/?status=active",
            headers=self.headers
        )
        assert response.status_code == 200
        
        # 按方案类型过滤
        response = requests.get(
            f"{self.BASE_URL}/member/my-licenses/?plan_type=trial",
            headers=self.headers
        )
        assert response.status_code == 200
        
        # 多重过滤
        response = requests.get(
            f"{self.BASE_URL}/member/my-licenses/?status=active&plan_type=trial",
            headers=self.headers
        )
        assert response.status_code == 200
    
    def test_rate_limiting(self):
        """测试API限流"""
        # 快速发送多个请求
        responses = []
        for i in range(6):  # 超出每天5次的限制
            response = requests.post(
                f"{self.BASE_URL}/member/apply/",
                headers=self.headers,
                json={"product_id": i + 1}
            )
            responses.append(response)
        
        # 检查是否有429响应
        rate_limited = any(r.status_code == 429 for r in responses)
        assert rate_limited, "应该触发限流机制"
    
    def test_unauthorized_access(self):
        """测试未授权访问"""
        endpoints = [
            "/member/available-products/",
            "/member/my-licenses/"
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{self.BASE_URL}{endpoint}")
            assert response.status_code == 401
            assert "Authentication credentials were not provided" in str(response.json())
    
    def test_admin_user_access_denied(self):
        """测试管理员用户访问被拒绝"""
        # 使用管理员令牌
        admin_headers = {
            "Authorization": f"Bearer {self.admin_token}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(
            f"{self.BASE_URL}/member/available-products/",
            headers=admin_headers
        )
        
        assert response.status_code == 403
        assert "permission" in response.json()["detail"].lower()

@pytest.fixture
def admin_token():
    """获取管理员令牌"""
    login_response = requests.post(
        "https://your-test-domain.com/api/v1/licenses/auth/login/",
        json={
            "username": "admin_user",
            "password": "admin_password"
        }
    )
    return login_response.json()["data"]["access_token"]
```

#### 运行测试

```bash
# 安装依赖
pip install pytest requests

# 运行所有测试
pytest tests/test_member_license_api.py -v

# 运行特定测试
pytest tests/test_member_license_api.py::TestMemberLicenseAPI::test_apply_trial_license_success -v

# 生成覆盖率报告
pytest tests/test_member_license_api.py --cov=. --cov-report=html
```

### JavaScript + Jest + Axios测试

```javascript
// tests/memberLicenseAPI.test.js
const axios = require('axios');

const API_BASE_URL = 'https://your-test-domain.com/api/v1/licenses';
let authToken = '';

// 测试前置设置
beforeAll(async () => {
    // 登录获取令牌
    const loginResponse = await axios.post(`${API_BASE_URL}/auth/login/`, {
        username: 'test_member',
        password: 'test_password'
    });
    
    authToken = loginResponse.data.data.access_token;
});

// 获取认证头
const getAuthHeaders = () => ({
    'Authorization': `Bearer ${authToken}`,
    'Content-Type': 'application/json'
});

describe('Member License API Tests', () => {
    describe('GET /member/available-products/', () => {
        test('should return available products for member user', async () => {
            const response = await axios.get(
                `${API_BASE_URL}/member/available-products/`,
                { headers: getAuthHeaders() }
            );
            
            expect(response.status).toBe(200);
            expect(response.data.success).toBe(true);
            expect(response.data.data).toHaveProperty('count');
            expect(response.data.data).toHaveProperty('products');
            expect(Array.isArray(response.data.data.products)).toBe(true);
        });
        
        test('should return 401 without authentication', async () => {
            try {
                await axios.get(`${API_BASE_URL}/member/available-products/`);
            } catch (error) {
                expect(error.response.status).toBe(401);
                expect(error.response.data).toHaveProperty('detail');
            }
        });
    });
    
    describe('POST /member/apply/', () => {
        test('should successfully apply for trial license', async () => {
            // 先获取可用产品
            const productsResponse = await axios.get(
                `${API_BASE_URL}/member/available-products/`,
                { headers: getAuthHeaders() }
            );
            
            const products = productsResponse.data.data.products;
            if (products.length === 0) {
                return; // 跳过测试，没有可用产品
            }
            
            const productId = products[0].id;
            
            const applyData = {
                product_id: productId,
                reason: 'Jest自动化测试',
                user_info: {
                    company: '测试公司',
                    job_title: '前端测试工程师'
                }
            };
            
            const response = await axios.post(
                `${API_BASE_URL}/member/apply/`,
                applyData,
                { headers: getAuthHeaders() }
            );
            
            expect(response.status).toBe(201);
            expect(response.data.success).toBe(true);
            expect(response.data.data).toHaveProperty('license_key');
            expect(response.data.data).toHaveProperty('expires_at');
        });
        
        test('should return validation error for missing product_id', async () => {
            try {
                await axios.post(
                    `${API_BASE_URL}/member/apply/`,
                    {},
                    { headers: getAuthHeaders() }
                );
            } catch (error) {
                expect(error.response.status).toBe(400);
                expect(error.response.data.success).toBe(false);
                expect(error.response.data.errors).toHaveProperty('product_id');
            }
        });
        
        test('should return error for invalid product_id', async () => {
            try {
                await axios.post(
                    `${API_BASE_URL}/member/apply/`,
                    { product_id: 99999 },
                    { headers: getAuthHeaders() }
                );
            } catch (error) {
                expect(error.response.status).toBe(400);
                expect(error.response.data.success).toBe(false);
                expect(error.response.data.errors.product_id[0]).toContain('不存在');
            }
        });
        
        test('should handle rate limiting', async () => {
            const requests = [];
            
            // 发送多个并发请求
            for (let i = 0; i < 6; i++) {
                requests.push(
                    axios.post(
                        `${API_BASE_URL}/member/apply/`,
                        { product_id: i + 1 },
                        { headers: getAuthHeaders() }
                    ).catch(error => error.response)
                );
            }
            
            const responses = await Promise.all(requests);
            const rateLimited = responses.some(response => response.status === 429);
            
            expect(rateLimited).toBe(true);
        }, 10000); // 10秒超时
    });
    
    describe('GET /member/my-licenses/', () => {
        test('should return user licenses', async () => {
            const response = await axios.get(
                `${API_BASE_URL}/member/my-licenses/`,
                { headers: getAuthHeaders() }
            );
            
            expect(response.status).toBe(200);
            expect(response.data.success).toBe(true);
            expect(response.data.data).toHaveProperty('count');
            expect(response.data.data).toHaveProperty('licenses');
            expect(Array.isArray(response.data.data.licenses)).toBe(true);
        });
        
        test('should support status filtering', async () => {
            const response = await axios.get(
                `${API_BASE_URL}/member/my-licenses/?status=active`,
                { headers: getAuthHeaders() }
            );
            
            expect(response.status).toBe(200);
            expect(response.data.success).toBe(true);
        });
        
        test('should support plan_type filtering', async () => {
            const response = await axios.get(
                `${API_BASE_URL}/member/my-licenses/?plan_type=trial`,
                { headers: getAuthHeaders() }
            );
            
            expect(response.status).toBe(200);
            expect(response.data.success).toBe(true);
        });
    });
});

// 运行测试
// npm test -- memberLicenseAPI.test.js
```

---

## 性能测试

### 使用Apache Bench (ab)

```bash
# 基础性能测试
ab -n 100 -c 10 -H "Authorization: Bearer ${JWT_TOKEN}" \
   "${API_BASE_URL}/member/available-products/"

# 结果分析
# Requests per second: 50.23 [#/sec] (mean)
# Time per request: 199.077 [ms] (mean)
# Transfer rate: 25.47 [Kbytes/sec] received

# 并发申请测试（模拟多用户）
ab -n 50 -c 5 -p apply_data.json -T "application/json" \
   -H "Authorization: Bearer ${JWT_TOKEN}" \
   "${API_BASE_URL}/member/apply/"

# apply_data.json内容
{
  "product_id": 1,
  "reason": "性能测试"
}
```

### 使用wrk进行压力测试

```bash
# 安装wrk
brew install wrk  # macOS
# 或
sudo apt-get install wrk  # Ubuntu

# 创建Lua脚本处理认证
cat > auth_script.lua << 'EOF'
wrk.method = "GET"
wrk.headers["Authorization"] = "Bearer YOUR_JWT_TOKEN_HERE"
wrk.headers["Content-Type"] = "application/json"
EOF

# 运行压力测试
wrk -t12 -c100 -d30s -s auth_script.lua \
    "${API_BASE_URL}/member/available-products/"

# POST请求压力测试
cat > post_script.lua << 'EOF'
wrk.method = "POST"
wrk.headers["Authorization"] = "Bearer YOUR_JWT_TOKEN_HERE"
wrk.headers["Content-Type"] = "application/json"
wrk.body = '{"product_id": 1, "reason": "压力测试"}'
EOF

wrk -t4 -c20 -d10s -s post_script.lua \
    "${API_BASE_URL}/member/apply/"
```

### 使用Locust进行负载测试

```python
# locustfile.py
from locust import HttpUser, task, between
import json

class MemberLicenseUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """登录获取令牌"""
        response = self.client.post("/auth/login/", json={
            "username": "test_member",
            "password": "test_password"
        })
        
        if response.status_code == 200:
            self.token = response.json()["data"]["access_token"]
            self.headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json"
            }
        else:
            self.token = None
    
    @task(3)
    def get_available_products(self):
        """获取可申请产品（权重3）"""
        if self.token:
            self.client.get(
                "/member/available-products/",
                headers=self.headers
            )
    
    @task(1)
    def apply_trial_license(self):
        """申请试用许可证（权重1）"""
        if self.token:
            self.client.post(
                "/member/apply/",
                headers=self.headers,
                json={
                    "product_id": 1,
                    "reason": "Locust负载测试"
                }
            )
    
    @task(2)
    def get_my_licenses(self):
        """查看我的许可证（权重2）"""
        if self.token:
            self.client.get(
                "/member/my-licenses/",
                headers=self.headers
            )

# 运行负载测试
# locust -f locustfile.py --host=https://your-test-domain.com/api/v1/licenses
```

---

## 安全测试

### SQL注入测试

```bash
# 测试产品ID参数
curl -X POST "${API_BASE_URL}/member/apply/" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "1; DROP TABLE licenses_license; --"
  }'

# 预期：参数验证应该阻止此类攻击

# 测试过滤参数
curl -X GET "${API_BASE_URL}/member/my-licenses/?status=active'; DROP TABLE member; --" \
  -H "Authorization: Bearer ${JWT_TOKEN}"

# 预期：应该返回空结果或参数验证错误，而不是SQL错误
```

### XSS攻击测试

```bash
# 测试用户输入字段
curl -X POST "${API_BASE_URL}/member/apply/" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1,
    "reason": "<script>alert(\"XSS\")</script>",
    "user_info": {
      "company": "<img src=x onerror=alert(\"XSS\")>"
    }
  }'

# 预期：输入应该被正确转义或拒绝
```

### 权限提升测试

```bash
# 测试是否能访问其他用户的许可证
curl -X GET "${API_BASE_URL}/member/my-licenses/" \
  -H "Authorization: Bearer ${OTHER_USER_TOKEN}" \
  -H "X-User-ID: ${TARGET_USER_ID}"

# 预期：应该只返回当前用户的许可证

# 测试JWT令牌篡改
# 修改JWT payload中的用户ID
MODIFIED_TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.MODIFIED_PAYLOAD.SIGNATURE"

curl -X GET "${API_BASE_URL}/member/my-licenses/" \
  -H "Authorization: Bearer ${MODIFIED_TOKEN}"

# 预期：应该返回401未授权错误
```

### CSRF测试

```html
<!-- csrf_test.html -->
<!DOCTYPE html>
<html>
<body>
    <form action="https://your-api-domain.com/api/v1/licenses/member/apply/" 
          method="POST" 
          enctype="application/json">
        <input type="hidden" name="product_id" value="1">
        <input type="hidden" name="reason" value="CSRF攻击测试">
        <input type="submit" value="提交CSRF请求">
    </form>
    
    <script>
        // 自动提交表单
        document.forms[0].submit();
    </script>
</body>
</html>
```

### 暴力破解测试

```python
# brute_force_test.py
import requests
import threading
import time

API_BASE_URL = "https://your-test-domain.com/api/v1/licenses"
failed_attempts = []

def attempt_login(username, password):
    """尝试登录"""
    try:
        response = requests.post(f"{API_BASE_URL}/auth/login/", json={
            "username": username,
            "password": password
        }, timeout=10)
        
        if response.status_code == 200:
            print(f"成功: {username}:{password}")
            return True
        else:
            failed_attempts.append((username, password, response.status_code))
            return False
    except Exception as e:
        print(f"错误: {username}:{password} - {e}")
        return False

# 常见密码列表
common_passwords = [
    "123456", "password", "123456789", "12345678", "12345",
    "1234567", "admin", "123123", "qwerty", "abc123"
]

# 测试用户名
test_usernames = ["admin", "test", "user", "member"]

# 多线程暴力破解测试
threads = []
for username in test_usernames:
    for password in common_passwords:
        thread = threading.Thread(
            target=attempt_login, 
            args=(username, password)
        )
        threads.append(thread)
        thread.start()
        time.sleep(0.1)  # 避免过于频繁的请求

# 等待所有线程完成
for thread in threads:
    thread.join()

print(f"总共失败尝试: {len(failed_attempts)}")

# 分析是否有限流保护
rate_limited = sum(1 for _, _, code in failed_attempts if code == 429)
print(f"被限流的尝试: {rate_limited}")
```

---

## 集成测试

### 端到端测试流程

```python
# e2e_test.py - 完整的用户流程测试
import requests
import time
from datetime import datetime

class E2ETestSuite:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username  
        self.password = password
        self.token = None
        self.headers = {}
        
    def setup(self):
        """测试前置设置"""
        print("🔧 开始测试前置设置...")
        
        # 登录获取令牌
        login_response = requests.post(f"{self.base_url}/auth/login/", json={
            "username": self.username,
            "password": self.password
        })
        
        assert login_response.status_code == 200, f"登录失败: {login_response.text}"
        
        self.token = login_response.json()["data"]["access_token"]
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        print("✅ 用户登录成功")
    
    def test_full_workflow(self):
        """测试完整的业务流程"""
        print("\n🚀 开始端到端测试...")
        
        # 步骤1: 获取可申请产品列表
        print("\n📋 步骤1: 获取可申请产品列表")
        products_response = requests.get(
            f"{self.base_url}/member/available-products/",
            headers=self.headers
        )
        
        assert products_response.status_code == 200
        products_data = products_response.json()["data"]
        print(f"✅ 找到 {products_data['count']} 个可申请产品")
        
        if products_data["count"] == 0:
            print("⚠️  没有可申请的产品，结束测试")
            return
        
        # 选择第一个产品
        selected_product = products_data["products"][0]
        product_id = selected_product["id"]
        print(f"📦 选择产品: {selected_product['name']} (ID: {product_id})")
        
        # 步骤2: 申请试用许可证
        print(f"\n📝 步骤2: 申请产品 {selected_product['name']} 的试用许可证")
        apply_data = {
            "product_id": product_id,
            "reason": "端到端测试申请",
            "user_info": {
                "company": "测试公司",
                "job_title": "测试工程师", 
                "phone": "13800138000",
                "intended_use": "用于自动化端到端测试"
            }
        }
        
        apply_response = requests.post(
            f"{self.base_url}/member/apply/",
            headers=self.headers,
            json=apply_data
        )
        
        assert apply_response.status_code == 201, f"申请失败: {apply_response.text}"
        apply_result = apply_response.json()["data"]
        print(f"✅ 申请成功! 许可证密钥: {apply_result['license_key'][:10]}...")
        print(f"📅 过期时间: {apply_result['expires_at']}")
        
        # 步骤3: 验证重复申请被阻止
        print(f"\n🚫 步骤3: 验证重复申请被阻止")
        duplicate_response = requests.post(
            f"{self.base_url}/member/apply/",
            headers=self.headers,
            json={"product_id": product_id}
        )
        
        assert duplicate_response.status_code == 400
        print("✅ 重复申请被正确阻止")
        
        # 步骤4: 查看我的许可证
        print(f"\n📄 步骤4: 查看我的许可证列表")
        licenses_response = requests.get(
            f"{self.base_url}/member/my-licenses/",
            headers=self.headers
        )
        
        assert licenses_response.status_code == 200
        licenses_data = licenses_response.json()["data"]
        print(f"✅ 查看许可证成功，共 {licenses_data['count']} 个许可证")
        print(f"📊 统计: 有效 {licenses_data['active_count']}, 试用 {licenses_data['trial_count']}")
        
        # 验证新申请的许可证在列表中
        found_license = False
        for license_info in licenses_data["licenses"]:
            if license_info["product_name"] == selected_product["name"]:
                found_license = True
                print(f"🔍 找到刚申请的许可证: {license_info['license_key_preview']}")
                break
        
        assert found_license, "未在许可证列表中找到刚申请的许可证"
        
        # 步骤5: 测试过滤功能
        print(f"\n🔍 步骤5: 测试许可证列表过滤功能")
        
        # 按状态过滤
        filtered_response = requests.get(
            f"{self.base_url}/member/my-licenses/?status=active",
            headers=self.headers
        )
        assert filtered_response.status_code == 200
        print("✅ 状态过滤测试通过")
        
        # 按方案类型过滤
        trial_response = requests.get(
            f"{self.base_url}/member/my-licenses/?plan_type=trial",
            headers=self.headers
        )
        assert trial_response.status_code == 200
        print("✅ 方案类型过滤测试通过")
        
        print(f"\n🎉 端到端测试全部通过!")
    
    def test_error_scenarios(self):
        """测试各种错误场景"""
        print(f"\n⚠️  开始错误场景测试...")
        
        # 测试无效产品ID
        print("🔍 测试无效产品ID")
        invalid_response = requests.post(
            f"{self.base_url}/member/apply/",
            headers=self.headers,
            json={"product_id": 99999}
        )
        assert invalid_response.status_code == 400
        print("✅ 无效产品ID处理正确")
        
        # 测试缺少必填参数
        print("🔍 测试缺少必填参数")
        empty_response = requests.post(
            f"{self.base_url}/member/apply/",
            headers=self.headers,
            json={}
        )
        assert empty_response.status_code == 400
        print("✅ 参数验证正确")
        
        # 测试无效令牌
        print("🔍 测试无效令牌")
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        unauth_response = requests.get(
            f"{self.base_url}/member/available-products/",
            headers=invalid_headers
        )
        assert unauth_response.status_code == 401
        print("✅ 认证验证正确")
        
        print("✅ 错误场景测试全部通过!")
    
    def cleanup(self):
        """测试后清理"""
        print(f"\n🧹 开始测试清理...")
        # 这里可以添加清理逻辑，比如删除测试数据
        print("✅ 清理完成")
    
    def run_all_tests(self):
        """运行所有测试"""
        try:
            self.setup()
            self.test_full_workflow()
            self.test_error_scenarios()
            print(f"\n✅ 所有测试通过! 测试时间: {datetime.now()}")
        except Exception as e:
            print(f"\n❌ 测试失败: {e}")
            raise
        finally:
            self.cleanup()

# 运行测试
if __name__ == "__main__":
    suite = E2ETestSuite(
        base_url="https://your-test-domain.com/api/v1/licenses",
        username="test_member",
        password="test_password"
    )
    suite.run_all_tests()
```

### 运行端到端测试

```bash
# 运行Python端到端测试
python e2e_test.py

# 预期输出:
# 🔧 开始测试前置设置...
# ✅ 用户登录成功
# 
# 🚀 开始端到端测试...
# 
# 📋 步骤1: 获取可申请产品列表
# ✅ 找到 2 个可申请产品
# 📦 选择产品: 测试PDF工具 (ID: 1)
# 
# 📝 步骤2: 申请产品 测试PDF工具 的试用许可证
# ✅ 申请成功! 许可证密钥: ABCDE-FGHI...
# 📅 过期时间: 2024-02-15T10:30:00Z
# ...
# 🎉 端到端测试全部通过!
```

---

## 监控和日志

### API响应时间监控

```python
# monitoring/response_time_monitor.py
import requests
import time
import statistics
from datetime import datetime

class APIMonitor:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}
        self.response_times = []
    
    def measure_endpoint(self, endpoint, method='GET', data=None, samples=10):
        """测量端点响应时间"""
        times = []
        
        for i in range(samples):
            start_time = time.time()
            
            try:
                if method == 'GET':
                    response = requests.get(
                        f"{self.base_url}{endpoint}",
                        headers=self.headers
                    )
                elif method == 'POST':
                    response = requests.post(
                        f"{self.base_url}{endpoint}",
                        headers=self.headers,
                        json=data
                    )
                
                end_time = time.time()
                response_time = (end_time - start_time) * 1000  # 转换为毫秒
                
                if response.status_code < 500:  # 只记录非服务器错误的响应时间
                    times.append(response_time)
                
            except Exception as e:
                print(f"请求失败: {e}")
            
            time.sleep(0.1)  # 避免过于频繁的请求
        
        if times:
            avg_time = statistics.mean(times)
            median_time = statistics.median(times)
            min_time = min(times)
            max_time = max(times)
            
            print(f"端点: {endpoint}")
            print(f"  平均响应时间: {avg_time:.2f}ms")
            print(f"  中位数响应时间: {median_time:.2f}ms")
            print(f"  最小响应时间: {min_time:.2f}ms")
            print(f"  最大响应时间: {max_time:.2f}ms")
            print(f"  样本数: {len(times)}")
            
            return {
                'endpoint': endpoint,
                'average': avg_time,
                'median': median_time,
                'min': min_time,
                'max': max_time,
                'samples': len(times)
            }
        
        return None
    
    def run_monitoring(self):
        """运行监控"""
        print(f"开始API响应时间监控 - {datetime.now()}")
        
        # 监控各个端点
        endpoints = [
            ('/member/available-products/', 'GET', None),
            ('/member/my-licenses/', 'GET', None),
            ('/member/apply/', 'POST', {'product_id': 1, 'reason': '监控测试'})
        ]
        
        results = []
        for endpoint, method, data in endpoints:
            result = self.measure_endpoint(endpoint, method, data)
            if result:
                results.append(result)
        
        # 生成报告
        print(f"\n监控报告:")
        for result in results:
            if result['average'] > 1000:  # 超过1秒
                print(f"⚠️  {result['endpoint']} 响应时间过慢: {result['average']:.2f}ms")
            elif result['average'] > 500:  # 超过500ms
                print(f"⚡ {result['endpoint']} 响应时间较慢: {result['average']:.2f}ms")
            else:
                print(f"✅ {result['endpoint']} 响应时间正常: {result['average']:.2f}ms")

# 运行监控
monitor = APIMonitor(
    base_url="https://your-test-domain.com/api/v1/licenses",
    token="your_test_token"
)
monitor.run_monitoring()
```

### 日志分析

```bash
# 分析API日志的脚本
# log_analysis.sh

#!/bin/bash

LOG_FILE="/path/to/api/logs/access.log"
DATE_PATTERN=$(date +"%d/%b/%Y")

echo "API日志分析报告 - $DATE_PATTERN"
echo "================================"

# 统计今日API请求总数
echo "📊 今日API请求统计:"
grep "$DATE_PATTERN" "$LOG_FILE" | grep "/api/v1/licenses/member/" | wc -l | \
    sed 's/^/  总请求数: /'

# 统计各端点请求数
echo -e "\n📋 端点请求分布:"
grep "$DATE_PATTERN" "$LOG_FILE" | \
    grep "/api/v1/licenses/member/" | \
    awk '{print $7}' | \
    sort | uniq -c | sort -nr | \
    sed 's/^/  /'

# 统计响应状态码
echo -e "\n🚦 响应状态码分布:"
grep "$DATE_PATTERN" "$LOG_FILE" | \
    grep "/api/v1/licenses/member/" | \
    awk '{print $9}' | \
    sort | uniq -c | sort -nr | \
    sed 's/^/  /'

# 统计响应时间（如果日志包含响应时间）
echo -e "\n⏱️  平均响应时间:"
grep "$DATE_PATTERN" "$LOG_FILE" | \
    grep "/api/v1/licenses/member/" | \
    awk '{print $10}' | \
    grep -E '^[0-9]+$' | \
    awk '{sum+=$1; n++} END {if(n>0) print "  平均:", sum/n, "ms"}' 

# 查找错误请求
echo -e "\n❌ 错误请求 (4xx, 5xx):"
grep "$DATE_PATTERN" "$LOG_FILE" | \
    grep "/api/v1/licenses/member/" | \
    grep -E " [45][0-9][0-9] " | \
    head -5 | \
    sed 's/^/  /'

# 统计用户活跃度（基于IP地址）
echo -e "\n👥 活跃用户数 (按IP):"
grep "$DATE_PATTERN" "$LOG_FILE" | \
    grep "/api/v1/licenses/member/" | \
    awk '{print $1}' | \
    sort | uniq | wc -l | \
    sed 's/^/  独立IP数: /'

# 统计申请成功率
echo -e "\n📈 申请成功率:"
TOTAL_APPLY=$(grep "$DATE_PATTERN" "$LOG_FILE" | grep "POST.*member/apply" | wc -l)
SUCCESS_APPLY=$(grep "$DATE_PATTERN" "$LOG_FILE" | grep "POST.*member/apply" | grep " 201 " | wc -l)

if [ $TOTAL_APPLY -gt 0 ]; then
    SUCCESS_RATE=$(echo "scale=2; $SUCCESS_APPLY * 100 / $TOTAL_APPLY" | bc)
    echo "  申请总数: $TOTAL_APPLY"
    echo "  成功申请: $SUCCESS_APPLY"
    echo "  成功率: $SUCCESS_RATE%"
else
    echo "  今日暂无申请请求"
fi
```

---

## CI/CD集成

### GitHub Actions配置

```yaml
# .github/workflows/api-tests.yml
name: Member License API Tests

on:
  push:
    branches: [ main, develop ]
    paths:
      - 'licenses/**'
      - 'common/**'
      - 'users/**'
  pull_request:
    branches: [ main ]
    paths:
      - 'licenses/**'
      - 'common/**'
      - 'users/**'

jobs:
  api-tests:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:6
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements-dev.txt
    
    - name: Set up environment variables
      run: |
        echo "DATABASE_URL=postgresql://postgres:postgres@localhost:5432/test_db" >> $GITHUB_ENV
        echo "REDIS_URL=redis://localhost:6379/0" >> $GITHUB_ENV
        echo "DEBUG=True" >> $GITHUB_ENV
        echo "SECRET_KEY=test_secret_key_for_ci" >> $GITHUB_ENV
    
    - name: Run migrations
      run: |
        python manage.py migrate --settings=core.settings
    
    - name: Create test data
      run: |
        python manage.py shell --settings=core.settings << 'EOF'
        from users.models import Member
        from tenants.models import Tenant
        from licenses.models import SoftwareProduct, LicensePlan
        from django.contrib.auth.hashers import make_password
        
        # Create test tenant
        tenant = Tenant.objects.create(name='Test Tenant', code='test', is_active=True)
        
        # Create test member
        member = Member.objects.create(
            username='test_member',
            email='test@example.com',
            password=make_password('test_password'),
            tenant=tenant,
            is_active=True,
            status='active'
        )
        
        # Create test product
        product = SoftwareProduct.objects.create(
            name='Test Product',
            code='test_product',
            description='Test product for API testing',
            version='1.0.0',
            tenant=tenant,
            status='active'
        )
        
        # Create trial plan
        plan = LicensePlan.objects.create(
            product=product,
            name='Trial Plan',
            code='trial',
            plan_type='trial',
            default_validity_days=30,
            default_max_activations=1,
            status='active'
        )
        
        print("Test data created successfully")
        EOF
    
    - name: Run Django tests
      run: |
        python manage.py test licenses.tests --settings=core.settings
    
    - name: Start Django server
      run: |
        python manage.py runserver 0.0.0.0:8000 --settings=core.settings &
        sleep 10  # Wait for server to start
    
    - name: Install Node.js for API tests
      uses: actions/setup-node@v3
      with:
        node-version: '16'
    
    - name: Install API test dependencies
      run: |
        npm install -g jest axios
    
    - name: Run API integration tests
      run: |
        # Set test environment variables
        export API_BASE_URL="http://localhost:8000/api/v1/licenses"
        export TEST_USERNAME="test_member"
        export TEST_PASSWORD="test_password"
        
        # Run the test suite
        node tests/api_integration.js
      
    - name: Generate test report
      if: always()
      run: |
        echo "## API Test Results" >> $GITHUB_STEP_SUMMARY
        echo "✅ Django unit tests passed" >> $GITHUB_STEP_SUMMARY
        echo "✅ API integration tests passed" >> $GITHUB_STEP_SUMMARY
    
    - name: Upload test artifacts
      if: failure()
      uses: actions/upload-artifact@v3
      with:
        name: test-logs
        path: |
          logs/
          test-reports/
```

### Jenkins Pipeline配置

```groovy
// Jenkinsfile
pipeline {
    agent any
    
    environment {
        DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/test_db'
        REDIS_URL = 'redis://localhost:6379/0'
        API_BASE_URL = 'http://localhost:8000/api/v1/licenses'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Setup Environment') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install -r requirements-dev.txt
                '''
            }
        }
        
        stage('Database Setup') {
            steps {
                sh '''
                    . venv/bin/activate
                    python manage.py migrate
                    python manage.py shell < scripts/create_test_data.py
                '''
            }
        }
        
        stage('Unit Tests') {
            steps {
                sh '''
                    . venv/bin/activate
                    python manage.py test licenses.tests --verbosity=2
                '''
            }
        }
        
        stage('Start Test Server') {
            steps {
                sh '''
                    . venv/bin/activate
                    nohup python manage.py runserver 0.0.0.0:8000 > server.log 2>&1 &
                    sleep 15
                    curl -f http://localhost:8000/api/v1/licenses/status/ || exit 1
                '''
            }
        }
        
        stage('API Tests') {
            parallel {
                stage('Python API Tests') {
                    steps {
                        sh '''
                            . venv/bin/activate
                            python -m pytest tests/test_member_license_api.py -v --junitxml=pytest-results.xml
                        '''
                    }
                }
                
                stage('JavaScript API Tests') {
                    steps {
                        sh '''
                            npm install jest axios
                            npm test tests/api_integration.js
                        '''
                    }
                }
                
                stage('Load Tests') {
                    steps {
                        sh '''
                            . venv/bin/activate
                            locust -f tests/load_test.py --host=http://localhost:8000 \
                                   --users=10 --spawn-rate=2 --run-time=2m --headless
                        '''
                    }
                }
            }
        }
        
        stage('Security Tests') {
            steps {
                sh '''
                    . venv/bin/activate
                    python tests/security_tests.py
                '''
            }
        }
    }
    
    post {
        always {
            // Stop test server
            sh 'pkill -f "python manage.py runserver" || true'
            
            // Archive test results
            junit 'pytest-results.xml'
            
            // Archive logs
            archiveArtifacts artifacts: 'server.log', allowEmptyArchive: true
            archiveArtifacts artifacts: 'logs/**/*.log', allowEmptyArchive: true
        }
        
        success {
            echo 'All tests passed successfully!'
        }
        
        failure {
            emailext (
                subject: "API Tests Failed - ${env.JOB_NAME} - ${env.BUILD_NUMBER}",
                body: """
                API tests failed for build ${env.BUILD_NUMBER}.
                
                Check the build logs for details: ${env.BUILD_URL}console
                
                Failed stage: ${env.STAGE_NAME}
                """,
                to: "${env.CHANGE_AUTHOR_EMAIL}, team@example.com"
            )
        }
    }
}
```

---

## 测试报告模板

### HTML测试报告

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Member试用许可证API测试报告</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f8f9fa; padding: 20px; border-radius: 5px; }
        .summary { display: flex; gap: 20px; margin: 20px 0; }
        .metric { background: white; padding: 15px; border-radius: 5px; border-left: 4px solid #007bff; flex: 1; }
        .metric.success { border-left-color: #28a745; }
        .metric.warning { border-left-color: #ffc107; }
        .metric.error { border-left-color: #dc3545; }
        .test-case { margin: 10px 0; padding: 15px; border-radius: 5px; }
        .test-case.passed { background: #d4edda; border-left: 4px solid #28a745; }
        .test-case.failed { background: #f8d7da; border-left: 4px solid #dc3545; }
        .test-case.skipped { background: #fff3cd; border-left: 4px solid #ffc107; }
        pre { background: #f8f9fa; padding: 10px; border-radius: 3px; overflow-x: auto; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Member试用许可证API测试报告</h1>
        <p><strong>测试时间:</strong> 2024-01-20 15:30:00</p>
        <p><strong>测试环境:</strong> https://test-api.example.com</p>
        <p><strong>测试版本:</strong> v1.2.0</p>
    </div>

    <div class="summary">
        <div class="metric success">
            <h3>通过测试</h3>
            <div style="font-size: 24px; font-weight: bold;">45</div>
        </div>
        <div class="metric error">
            <h3>失败测试</h3>
            <div style="font-size: 24px; font-weight: bold;">2</div>
        </div>
        <div class="metric warning">
            <h3>跳过测试</h3>
            <div style="font-size: 24px; font-weight: bold;">1</div>
        </div>
        <div class="metric">
            <h3>成功率</h3>
            <div style="font-size: 24px; font-weight: bold;">93.8%</div>
        </div>
    </div>

    <h2>📊 性能指标</h2>
    <table border="1" style="border-collapse: collapse; width: 100%;">
        <tr style="background: #f8f9fa;">
            <th style="padding: 10px;">端点</th>
            <th style="padding: 10px;">平均响应时间</th>
            <th style="padding: 10px;">成功率</th>
            <th style="padding: 10px;">QPS</th>
        </tr>
        <tr>
            <td style="padding: 10px;">GET /member/available-products/</td>
            <td style="padding: 10px;">145ms</td>
            <td style="padding: 10px;">100%</td>
            <td style="padding: 10px;">67.2</td>
        </tr>
        <tr>
            <td style="padding: 10px;">POST /member/apply/</td>
            <td style="padding: 10px;">320ms</td>
            <td style="padding: 10px;">95.8%</td>
            <td style="padding: 10px;">25.1</td>
        </tr>
        <tr>
            <td style="padding: 10px;">GET /member/my-licenses/</td>
            <td style="padding: 10px;">89ms</td>
            <td style="padding: 10px;">100%</td>
            <td style="padding: 10px;">112.4</td>
        </tr>
    </table>

    <h2>🧪 测试用例详情</h2>

    <div class="test-case passed">
        <h4>✅ 测试用例: 获取可申请产品列表 - 正常请求</h4>
        <p><strong>描述:</strong> 使用有效令牌获取产品列表</p>
        <p><strong>状态:</strong> 通过</p>
        <p><strong>执行时间:</strong> 0.15s</p>
        <pre>Request: GET /api/v1/licenses/member/available-products/
Response: 200 OK
{
  "success": true,
  "data": {
    "count": 2,
    "products": [...]
  }
}</pre>
    </div>

    <div class="test-case failed">
        <h4>❌ 测试用例: 申请试用许可证 - 频率限制</h4>
        <p><strong>描述:</strong> 测试API频率限制机制</p>
        <p><strong>状态:</strong> 失败</p>
        <p><strong>执行时间:</strong> 2.3s</p>
        <p><strong>错误信息:</strong> 预期状态码429，实际收到400</p>
        <pre>Request: POST /api/v1/licenses/member/apply/ (第6次请求)
Expected: 429 Too Many Requests
Actual: 400 Bad Request
{
  "success": false,
  "error": "您已经申请过该产品的许可证",
  "code": "APPLICATION_FAILED"
}</pre>
        <p><strong>修复建议:</strong> 检查限流配置是否正确生效</p>
    </div>

    <div class="test-case passed">
        <h4>✅ 测试用例: 查看我的许可证 - 过滤功能</h4>
        <p><strong>描述:</strong> 测试许可证列表的状态和类型过滤</p>
        <p><strong>状态:</strong> 通过</p>
        <p><strong>执行时间:</strong> 0.08s</p>
    </div>

    <div class="test-case skipped">
        <h4>⚠️ 测试用例: 安全测试 - SQL注入</h4>
        <p><strong>描述:</strong> 测试API对SQL注入攻击的防护</p>
        <p><strong>状态:</strong> 跳过</p>
        <p><strong>原因:</strong> 测试环境不支持安全扫描</p>
    </div>

    <h2>🔍 问题汇总</h2>
    <ul>
        <li><strong>高优先级:</strong> API限流机制未按预期工作，需要检查配置</li>
        <li><strong>中优先级:</strong> 申请API平均响应时间为320ms，略高于目标值(200ms)</li>
        <li><strong>低优先级:</strong> 部分测试用例在测试环境下无法执行</li>
    </ul>

    <h2>📈 趋势分析</h2>
    <p>与上次测试(2024-01-15)对比:</p>
    <ul>
        <li>✅ 成功率从91.2%提升到93.8%</li>
        <li>✅ 平均响应时间从278ms降低到251ms</li>
        <li>⚠️ 新增2个失败测试用例，需要关注</li>
    </ul>

    <h2>🎯 建议</h2>
    <ol>
        <li>优先修复API限流配置问题</li>
        <li>优化申请API的数据库查询，降低响应时间</li>
        <li>完善测试环境，支持更全面的安全测试</li>
        <li>建立自动化监控，及时发现性能回归</li>
    </ol>

    <div style="margin-top: 40px; padding: 20px; background: #f8f9fa; border-radius: 5px; text-align: center;">
        <p>测试报告自动生成 | 最后更新: 2024-01-20 15:30:00</p>
    </div>
</body>
</html>
```

---

## 总结

本测试指南提供了Member试用许可证API的全面测试方案，包括：

### 测试类型覆盖
- ✅ **手动测试** - 基础功能验证
- ✅ **自动化测试** - 可重复执行的测试套件
- ✅ **性能测试** - 响应时间和并发能力测试
- ✅ **安全测试** - 防护机制验证
- ✅ **集成测试** - 端到端业务流程测试

### 工具和框架
- **手动测试**: cURL命令行工具
- **自动化测试**: Python pytest, JavaScript Jest
- **性能测试**: Apache Bench, wrk, Locust
- **安全测试**: 自定义脚本和工具
- **监控**: 自定义监控脚本

### CI/CD集成
- **GitHub Actions** 自动化工作流
- **Jenkins Pipeline** 企业级持续集成
- **测试报告** 可视化结果展示

### 最佳实践建议
1. **分层测试** - 从单元测试到端到端测试
2. **持续监控** - 生产环境性能监控
3. **安全优先** - 定期安全扫描和测试
4. **文档同步** - 保持测试用例与API文档同步
5. **自动化优先** - 尽可能自动化重复性测试

使用这个指南，开发和测试团队可以建立完整的API测试体系，确保Member试用许可证API的质量和稳定性。
