# 许可证解绑API测试指南

## 概述

本文档提供了许可证解绑API的完整测试方案，包括手动测试、自动化测试和性能测试的方法和工具。

## 测试环境准备

### 1. 测试数据准备

在开始测试前，需要准备以下测试数据：

```sql
-- 创建测试产品
INSERT INTO licenses_software_product (name, code, description, version, public_key, private_key_hash, max_activations, offline_days, status, created_at, updated_at) 
VALUES ('测试产品', 'TEST_PRODUCT', '用于API测试的产品', '1.0.0', 'TEST_PUBLIC_KEY', 'TEST_PRIVATE_HASH', 5, 30, 'active', NOW(), NOW());

-- 创建测试方案
INSERT INTO licenses_license_plan (product_id, name, code, plan_type, default_max_activations, default_validity_days, features, price, currency, status, created_at, updated_at)
VALUES (1, '测试方案', 'TEST_PLAN', 'trial', 3, 365, '{}', 0.00, 'CNY', 'active', NOW(), NOW());

-- 创建测试许可证
INSERT INTO licenses_license (product_id, plan_id, tenant_id, license_key, license_hash, customer_name, customer_email, max_activations, expires_at, status, created_at, updated_at)
VALUES (1, 1, 1, 'TEST1-TEST2-TEST3-TEST4-TEST5', 'test_hash_123', '测试客户', 'test@example.com', 3, '2025-12-31 23:59:59', 'activated', NOW(), NOW());

-- 创建测试机器绑定
INSERT INTO licenses_machine_binding (license_id, machine_id, machine_fingerprint, encrypted_hardware_info, status, created_at, updated_at)
VALUES (1, 'TEST-MACHINE-001', 'a1b2c3d4e5f6789012345678901234567890123456789012345678901234abcd', '{}', 'active', NOW(), NOW());

-- 创建测试激活记录
INSERT INTO licenses_activation (license_id, machine_binding_id, activation_type, activation_code, result, activated_at, created_at, updated_at)
VALUES (1, 1, 'online', 'TEST-ACTI-VATI-ONCO-DE01', 'success', NOW(), NOW(), NOW());
```

### 2. 环境配置

```bash
# 设置测试环境变量
export API_BASE_URL="http://localhost:8000"
export TEST_TENANT_ID="1"
export TEST_ACTIVATION_CODE="TEST-ACTI-VATI-ONCO-DE01"
export TEST_LICENSE_KEY="TEST1-TEST2-TEST3-TEST4-TEST5"
export TEST_MACHINE_FINGERPRINT="a1b2c3d4e5f6789012345678901234567890123456789012345678901234abcd"
```

## 手动测试

### 1. 使用 cURL 测试

#### 成功场景测试

```bash
# 正常解绑请求
curl -X POST "${API_BASE_URL}/api/v1/licenses/unbind/" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: ${TEST_TENANT_ID}" \
  -d '{
    "activation_code": "'${TEST_ACTIVATION_CODE}'",
    "license_key": "'${TEST_LICENSE_KEY}'",
    "machine_fingerprint": "'${TEST_MACHINE_FINGERPRINT}'",
    "reason": "手动测试解绑"
  }' \
  -v
```

#### 错误场景测试

```bash
# 1. 测试无效激活码
curl -X POST "${API_BASE_URL}/api/v1/licenses/unbind/" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: ${TEST_TENANT_ID}" \
  -d '{
    "activation_code": "INVALID-CODE",
    "license_key": "'${TEST_LICENSE_KEY}'",
    "machine_fingerprint": "'${TEST_MACHINE_FINGERPRINT}'"
  }'

# 2. 测试许可证密钥不匹配
curl -X POST "${API_BASE_URL}/api/v1/licenses/unbind/" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: ${TEST_TENANT_ID}" \
  -d '{
    "activation_code": "'${TEST_ACTIVATION_CODE}'",
    "license_key": "WRONG-LICEN-SE-KEY-12345",
    "machine_fingerprint": "'${TEST_MACHINE_FINGERPRINT}'"
  }'

# 3. 测试机器指纹不匹配
curl -X POST "${API_BASE_URL}/api/v1/licenses/unbind/" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: ${TEST_TENANT_ID}" \
  -d '{
    "activation_code": "'${TEST_ACTIVATION_CODE}'",
    "license_key": "'${TEST_LICENSE_KEY}'",
    "machine_fingerprint": "0000000000000000000000000000000000000000000000000000000000000000"
  }'

# 4. 测试参数格式错误
curl -X POST "${API_BASE_URL}/api/v1/licenses/unbind/" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: ${TEST_TENANT_ID}" \
  -d '{
    "activation_code": "SHORT",
    "license_key": "INVALID",
    "machine_fingerprint": "TOO_SHORT"
  }'

# 5. 测试重复解绑
# 先正常解绑一次，然后再次尝试解绑同一设备
curl -X POST "${API_BASE_URL}/api/v1/licenses/unbind/" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: ${TEST_TENANT_ID}" \
  -d '{
    "activation_code": "'${TEST_ACTIVATION_CODE}'",
    "license_key": "'${TEST_LICENSE_KEY}'",
    "machine_fingerprint": "'${TEST_MACHINE_FINGERPRINT}'"
  }'
```

### 2. 使用 Postman 测试

#### Postman Collection

```json
{
  "info": {
    "name": "License Unbind API Tests",
    "description": "许可证解绑API测试集合"
  },
  "variable": [
    {
      "key": "baseUrl",
      "value": "http://localhost:8000"
    },
    {
      "key": "tenantId",
      "value": "1"
    },
    {
      "key": "testActivationCode",
      "value": "TEST-ACTI-VATI-ONCO-DE01"
    },
    {
      "key": "testLicenseKey",
      "value": "TEST1-TEST2-TEST3-TEST4-TEST5"
    },
    {
      "key": "testMachineFingerprint",
      "value": "a1b2c3d4e5f6789012345678901234567890123456789012345678901234abcd"
    }
  ],
  "item": [
    {
      "name": "Successful Unbind",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          },
          {
            "key": "X-Tenant-ID",
            "value": "{{tenantId}}"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"activation_code\": \"{{testActivationCode}}\",\n  \"license_key\": \"{{testLicenseKey}}\",\n  \"machine_fingerprint\": \"{{testMachineFingerprint}}\",\n  \"reason\": \"Postman测试\"\n}"
        },
        "url": {
          "raw": "{{baseUrl}}/api/v1/licenses/unbind/",
          "host": ["{{baseUrl}}"],
          "path": ["api", "v1", "licenses", "unbind", ""]
        }
      },
      "event": [
        {
          "listen": "test",
          "script": {
            "exec": [
              "pm.test(\"Status code is 200\", function () {",
              "    pm.response.to.have.status(200);",
              "});",
              "",
              "pm.test(\"Response has success field\", function () {",
              "    var jsonData = pm.response.json();",
              "    pm.expect(jsonData).to.have.property('success');",
              "    pm.expect(jsonData.success).to.be.true;",
              "});",
              "",
              "pm.test(\"Response has data field\", function () {",
              "    var jsonData = pm.response.json();",
              "    pm.expect(jsonData).to.have.property('data');",
              "    pm.expect(jsonData.data).to.have.property('license_id');",
              "    pm.expect(jsonData.data).to.have.property('remaining_activations');",
              "});"
            ]
          }
        }
      ]
    },
    {
      "name": "Invalid Activation Code",
      "request": {
        "method": "POST",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          },
          {
            "key": "X-Tenant-ID",
            "value": "{{tenantId}}"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"activation_code\": \"INVALID-CODE\",\n  \"license_key\": \"{{testLicenseKey}}\",\n  \"machine_fingerprint\": \"{{testMachineFingerprint}}\"\n}"
        },
        "url": {
          "raw": "{{baseUrl}}/api/v1/licenses/unbind/",
          "host": ["{{baseUrl}}"],
          "path": ["api", "v1", "licenses", "unbind", ""]
        }
      },
      "event": [
        {
          "listen": "test",
          "script": {
            "exec": [
              "pm.test(\"Status code is 400\", function () {",
              "    pm.response.to.have.status(400);",
              "});",
              "",
              "pm.test(\"Error code is ACTIVATION_NOT_FOUND\", function () {",
              "    var jsonData = pm.response.json();",
              "    pm.expect(jsonData.code).to.eql('ACTIVATION_NOT_FOUND');",
              "});"
            ]
          }
        }
      ]
    }
  ]
}
```

## 自动化测试

### 1. Python 测试脚本

```python
#!/usr/bin/env python3
# test_unbind_api.py

import requests
import json
import time
import sys
from typing import Dict, Any

class UnbindAPITester:
    def __init__(self, base_url: str, tenant_id: str = None):
        self.base_url = base_url
        self.tenant_id = tenant_id
        self.session = requests.Session()
        
        if tenant_id:
            self.session.headers.update({'X-Tenant-ID': tenant_id})
    
    def unbind_license(self, data: Dict[str, Any]) -> requests.Response:
        """发送解绑请求"""
        url = f"{self.base_url}/api/v1/licenses/unbind/"
        return self.session.post(url, json=data)
    
    def test_successful_unbind(self) -> bool:
        """测试成功解绑"""
        print("测试: 成功解绑")
        
        data = {
            "activation_code": "TEST-ACTI-VATI-ONCO-DE01",
            "license_key": "TEST1-TEST2-TEST3-TEST4-TEST5",
            "machine_fingerprint": "a1b2c3d4e5f6789012345678901234567890123456789012345678901234abcd",
            "reason": "Python自动化测试"
        }
        
        response = self.unbind_license(data)
        
        try:
            assert response.status_code == 200, f"期望状态码200，实际{response.status_code}"
            
            result = response.json()
            assert result['success'] is True, "期望success为True"
            assert 'data' in result, "响应应包含data字段"
            assert 'license_id' in result['data'], "data应包含license_id"
            assert 'remaining_activations' in result['data'], "data应包含remaining_activations"
            
            print("✓ 成功解绑测试通过")
            return True
        except AssertionError as e:
            print(f"✗ 成功解绑测试失败: {e}")
            print(f"响应: {response.text}")
            return False
        except Exception as e:
            print(f"✗ 成功解绑测试异常: {e}")
            return False
    
    def test_invalid_activation_code(self) -> bool:
        """测试无效激活码"""
        print("测试: 无效激活码")
        
        data = {
            "activation_code": "INVALID-CODE",
            "license_key": "TEST1-TEST2-TEST3-TEST4-TEST5",
            "machine_fingerprint": "a1b2c3d4e5f6789012345678901234567890123456789012345678901234abcd"
        }
        
        response = self.unbind_license(data)
        
        try:
            assert response.status_code == 400, f"期望状态码400，实际{response.status_code}"
            
            result = response.json()
            assert result['success'] is False, "期望success为False"
            assert result['code'] == 'ACTIVATION_NOT_FOUND', "期望错误代码为ACTIVATION_NOT_FOUND"
            
            print("✓ 无效激活码测试通过")
            return True
        except AssertionError as e:
            print(f"✗ 无效激活码测试失败: {e}")
            print(f"响应: {response.text}")
            return False
        except Exception as e:
            print(f"✗ 无效激活码测试异常: {e}")
            return False
    
    def test_parameter_validation(self) -> bool:
        """测试参数验证"""
        print("测试: 参数验证")
        
        test_cases = [
            {
                "name": "激活码格式错误",
                "data": {
                    "activation_code": "SHORT",
                    "license_key": "TEST1-TEST2-TEST3-TEST4-TEST5",
                    "machine_fingerprint": "a1b2c3d4e5f6789012345678901234567890123456789012345678901234abcd"
                },
                "expected_field": "activation_code"
            },
            {
                "name": "许可证密钥格式错误",
                "data": {
                    "activation_code": "TEST-ACTI-VATI-ONCO-DE01",
                    "license_key": "SHORT",
                    "machine_fingerprint": "a1b2c3d4e5f6789012345678901234567890123456789012345678901234abcd"
                },
                "expected_field": "license_key"
            },
            {
                "name": "机器指纹长度错误",
                "data": {
                    "activation_code": "TEST-ACTI-VATI-ONCO-DE01",
                    "license_key": "TEST1-TEST2-TEST3-TEST4-TEST5",
                    "machine_fingerprint": "short_fingerprint"
                },
                "expected_field": "machine_fingerprint"
            }
        ]
        
        all_passed = True
        
        for case in test_cases:
            response = self.unbind_license(case["data"])
            
            try:
                assert response.status_code == 400, f"{case['name']}: 期望状态码400"
                
                result = response.json()
                assert 'errors' in result, f"{case['name']}: 响应应包含errors字段"
                assert case['expected_field'] in result['errors'], \
                    f"{case['name']}: errors应包含{case['expected_field']}字段"
                
                print(f"✓ {case['name']}测试通过")
            except AssertionError as e:
                print(f"✗ {case['name']}测试失败: {e}")
                print(f"响应: {response.text}")
                all_passed = False
            except Exception as e:
                print(f"✗ {case['name']}测试异常: {e}")
                all_passed = False
        
        return all_passed
    
    def test_rate_limiting(self) -> bool:
        """测试频率限制"""
        print("测试: 频率限制")
        
        data = {
            "activation_code": "TEST-ACTI-VATI-ONCO-DE01",
            "license_key": "TEST1-TEST2-TEST3-TEST4-TEST5",
            "machine_fingerprint": "a1b2c3d4e5f6789012345678901234567890123456789012345678901234abcd"
        }
        
        # 发送大量请求触发频率限制
        request_count = 0
        rate_limited = False
        
        for i in range(110):  # 超过100次/小时的限制
            response = self.unbind_license(data)
            request_count += 1
            
            if response.status_code == 429:
                try:
                    result = response.json()
                    assert result['code'] == 'RATE_LIMITED', "期望错误代码为RATE_LIMITED"
                    rate_limited = True
                    print(f"✓ 在第{request_count}次请求时触发频率限制")
                    break
                except Exception as e:
                    print(f"✗ 频率限制响应格式异常: {e}")
                    return False
            
            time.sleep(0.1)  # 避免过快请求
        
        if not rate_limited:
            print("✗ 未能触发频率限制")
            return False
        
        return True
    
    def run_all_tests(self) -> bool:
        """运行所有测试"""
        print("开始许可证解绑API测试")
        print("=" * 50)
        
        tests = [
            self.test_successful_unbind,
            self.test_invalid_activation_code,
            self.test_parameter_validation,
            # self.test_rate_limiting,  # 可选：由于会影响其他测试，可以单独运行
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            if test():
                passed += 1
            print("-" * 30)
        
        print(f"测试结果: {passed}/{total} 通过")
        
        if passed == total:
            print("✓ 所有测试通过")
            return True
        else:
            print("✗ 部分测试失败")
            return False

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python test_unbind_api.py <API_BASE_URL> [TENANT_ID]")
        sys.exit(1)
    
    base_url = sys.argv[1]
    tenant_id = sys.argv[2] if len(sys.argv) > 2 else None
    
    tester = UnbindAPITester(base_url, tenant_id)
    
    try:
        success = tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n测试被中断")
        sys.exit(1)
    except Exception as e:
        print(f"测试执行异常: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

#### 运行测试

```bash
# 安装依赖
pip install requests

# 运行测试
python test_unbind_api.py http://localhost:8000 1

# 只测试频率限制
python -c "
from test_unbind_api import UnbindAPITester
tester = UnbindAPITester('http://localhost:8000', '1')
tester.test_rate_limiting()
"
```

### 2. JavaScript/Node.js 测试

```javascript
// test-unbind-api.js
const axios = require('axios');

class UnbindAPITester {
  constructor(baseUrl, tenantId) {
    this.baseUrl = baseUrl;
    this.tenantId = tenantId;
    this.client = axios.create({
      baseURL: baseUrl,
      headers: {
        'Content-Type': 'application/json',
        ...(tenantId && { 'X-Tenant-ID': tenantId })
      }
    });
  }

  async unbindLicense(data) {
    try {
      const response = await this.client.post('/api/v1/licenses/unbind/', data);
      return { success: true, data: response.data, status: response.status };
    } catch (error) {
      return {
        success: false,
        error: error.response?.data || error.message,
        status: error.response?.status || 500
      };
    }
  }

  async testSuccessfulUnbind() {
    console.log('测试: 成功解绑');

    const data = {
      activation_code: 'TEST-ACTI-VATI-ONCO-DE01',
      license_key: 'TEST1-TEST2-TEST3-TEST4-TEST5',
      machine_fingerprint: 'a1b2c3d4e5f6789012345678901234567890123456789012345678901234abcd',
      reason: 'Node.js自动化测试'
    };

    const result = await this.unbindLicense(data);

    try {
      console.assert(result.status === 200, `期望状态码200，实际${result.status}`);
      console.assert(result.data.success === true, '期望success为true');
      console.assert('data' in result.data, '响应应包含data字段');
      console.assert('license_id' in result.data.data, 'data应包含license_id');

      console.log('✓ 成功解绑测试通过');
      return true;
    } catch (error) {
      console.log(`✗ 成功解绑测试失败: ${error.message}`);
      console.log(`响应:`, result);
      return false;
    }
  }

  async testParameterValidation() {
    console.log('测试: 参数验证');

    const testCases = [
      {
        name: '激活码格式错误',
        data: {
          activation_code: 'SHORT',
          license_key: 'TEST1-TEST2-TEST3-TEST4-TEST5',
          machine_fingerprint: 'a1b2c3d4e5f6789012345678901234567890123456789012345678901234abcd'
        }
      },
      {
        name: '机器指纹长度错误',
        data: {
          activation_code: 'TEST-ACTI-VATI-ONCO-DE01',
          license_key: 'TEST1-TEST2-TEST3-TEST4-TEST5',
          machine_fingerprint: 'short'
        }
      }
    ];

    let allPassed = true;

    for (const testCase of testCases) {
      const result = await this.unbindLicense(testCase.data);

      try {
        console.assert(result.status === 400, `${testCase.name}: 期望状态码400`);
        console.assert('errors' in result.error, `${testCase.name}: 响应应包含errors字段`);

        console.log(`✓ ${testCase.name}测试通过`);
      } catch (error) {
        console.log(`✗ ${testCase.name}测试失败: ${error.message}`);
        allPassed = false;
      }
    }

    return allPassed;
  }

  async runAllTests() {
    console.log('开始许可证解绑API测试');
    console.log('='.repeat(50));

    const tests = [
      () => this.testSuccessfulUnbind(),
      () => this.testParameterValidation()
    ];

    let passed = 0;
    const total = tests.length;

    for (const test of tests) {
      if (await test()) {
        passed++;
      }
      console.log('-'.repeat(30));
    }

    console.log(`测试结果: ${passed}/${total} 通过`);

    if (passed === total) {
      console.log('✓ 所有测试通过');
      return true;
    } else {
      console.log('✗ 部分测试失败');
      return false;
    }
  }
}

// 主执行函数
async function main() {
  const baseUrl = process.argv[2];
  const tenantId = process.argv[3];

  if (!baseUrl) {
    console.log('用法: node test-unbind-api.js <API_BASE_URL> [TENANT_ID]');
    process.exit(1);
  }

  const tester = new UnbindAPITester(baseUrl, tenantId);

  try {
    const success = await tester.runAllTests();
    process.exit(success ? 0 : 1);
  } catch (error) {
    console.error('测试执行异常:', error);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = UnbindAPITester;
```

#### 运行测试

```bash
# 安装依赖
npm install axios

# 运行测试
node test-unbind-api.js http://localhost:8000 1
```

## 性能测试

### 1. 并发测试脚本

```python
#!/usr/bin/env python3
# performance_test.py

import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict

class PerformanceTester:
    def __init__(self, base_url: str, tenant_id: str = None):
        self.base_url = base_url
        self.tenant_id = tenant_id
        self.results: List[Dict] = []
    
    async def single_request(self, session: aiohttp.ClientSession, request_id: int) -> Dict:
        """发送单个请求"""
        data = {
            "activation_code": f"TEST-{request_id:04d}-VATI-ONCO-DE01",
            "license_key": "TEST1-TEST2-TEST3-TEST4-TEST5",
            "machine_fingerprint": "a1b2c3d4e5f6789012345678901234567890123456789012345678901234abcd",
            "reason": f"性能测试请求{request_id}"
        }
        
        headers = {'Content-Type': 'application/json'}
        if self.tenant_id:
            headers['X-Tenant-ID'] = self.tenant_id
        
        start_time = time.time()
        
        try:
            async with session.post(
                f"{self.base_url}/api/v1/licenses/unbind/",
                json=data,
                headers=headers
            ) as response:
                response_data = await response.json()
                end_time = time.time()
                
                return {
                    'request_id': request_id,
                    'status_code': response.status,
                    'response_time': end_time - start_time,
                    'success': response.status < 400,
                    'error': None
                }
        except Exception as e:
            end_time = time.time()
            return {
                'request_id': request_id,
                'status_code': 0,
                'response_time': end_time - start_time,
                'success': False,
                'error': str(e)
            }
    
    async def run_concurrent_test(self, concurrent_users: int, total_requests: int):
        """运行并发测试"""
        print(f"开始性能测试: {concurrent_users}个并发用户，总共{total_requests}个请求")
        
        connector = aiohttp.TCPConnector(limit=concurrent_users)
        async with aiohttp.ClientSession(connector=connector) as session:
            # 创建任务
            tasks = []
            for i in range(total_requests):
                task = asyncio.create_task(self.single_request(session, i))
                tasks.append(task)
                
                # 控制并发数
                if len(tasks) >= concurrent_users:
                    completed_tasks = await asyncio.gather(*tasks)
                    self.results.extend(completed_tasks)
                    tasks = []
            
            # 处理剩余任务
            if tasks:
                completed_tasks = await asyncio.gather(*tasks)
                self.results.extend(completed_tasks)
    
    def analyze_results(self):
        """分析测试结果"""
        if not self.results:
            print("没有测试结果")
            return
        
        successful_requests = [r for r in self.results if r['success']]
        failed_requests = [r for r in self.results if not r['success']]
        
        response_times = [r['response_time'] for r in successful_requests]
        
        print("\n性能测试结果:")
        print("=" * 50)
        print(f"总请求数: {len(self.results)}")
        print(f"成功请求数: {len(successful_requests)}")
        print(f"失败请求数: {len(failed_requests)}")
        print(f"成功率: {len(successful_requests)/len(self.results)*100:.2f}%")
        
        if response_times:
            print(f"\n响应时间统计:")
            print(f"平均响应时间: {statistics.mean(response_times):.3f}s")
            print(f"中位数响应时间: {statistics.median(response_times):.3f}s")
            print(f"最小响应时间: {min(response_times):.3f}s")
            print(f"最大响应时间: {max(response_times):.3f}s")
            print(f"95%分位数: {sorted(response_times)[int(len(response_times)*0.95)]:.3f}s")
        
        # 分析错误
        if failed_requests:
            print(f"\n错误分析:")
            error_types = {}
            status_codes = {}
            
            for req in failed_requests:
                error = req.get('error', 'Unknown')
                status = req.get('status_code', 0)
                
                error_types[error] = error_types.get(error, 0) + 1
                status_codes[status] = status_codes.get(status, 0) + 1
            
            print(f"错误类型分布:")
            for error, count in error_types.items():
                print(f"  {error}: {count}")
            
            print(f"状态码分布:")
            for status, count in status_codes.items():
                print(f"  {status}: {count}")

async def main():
    tester = PerformanceTester('http://localhost:8000', '1')
    
    # 测试场景
    test_scenarios = [
        (1, 10),    # 单用户，10个请求
        (5, 50),    # 5个并发用户，50个请求
        (10, 100),  # 10个并发用户，100个请求
    ]
    
    for concurrent, total in test_scenarios:
        print(f"\n运行测试场景: {concurrent}并发用户, {total}总请求")
        tester.results = []  # 重置结果
        
        start_time = time.time()
        await tester.run_concurrent_test(concurrent, total)
        end_time = time.time()
        
        print(f"总耗时: {end_time - start_time:.2f}s")
        tester.analyze_results()
        print("-" * 60)

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. 使用 Apache Bench 测试

```bash
#!/bin/bash
# ab_test.sh

API_URL="http://localhost:8000/api/v1/licenses/unbind/"
TENANT_ID="1"

# 创建测试数据文件
cat > test_data.json << EOF
{
  "activation_code": "TEST-ACTI-VATI-ONCO-DE01",
  "license_key": "TEST1-TEST2-TEST3-TEST4-TEST5",
  "machine_fingerprint": "a1b2c3d4e5f6789012345678901234567890123456789012345678901234abcd",
  "reason": "Apache Bench测试"
}
EOF

# 测试场景1: 基础性能测试
echo "基础性能测试: 100个请求，并发数10"
ab -n 100 -c 10 \
   -H "Content-Type: application/json" \
   -H "X-Tenant-ID: ${TENANT_ID}" \
   -p test_data.json \
   -T "application/json" \
   ${API_URL}

echo "--------------------"

# 测试场景2: 高并发测试
echo "高并发测试: 500个请求，并发数50"
ab -n 500 -c 50 \
   -H "Content-Type: application/json" \
   -H "X-Tenant-ID: ${TENANT_ID}" \
   -p test_data.json \
   -T "application/json" \
   ${API_URL}

# 清理
rm test_data.json
```

## 监控和日志

### 1. 监控脚本

```python
#!/usr/bin/env python3
# monitor_api.py

import requests
import time
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('api_monitor.log'),
        logging.StreamHandler()
    ]
)

class APIMonitor:
    def __init__(self, base_url: str, tenant_id: str = None):
        self.base_url = base_url
        self.tenant_id = tenant_id
        self.session = requests.Session()
        
        if tenant_id:
            self.session.headers.update({'X-Tenant-ID': tenant_id})
    
    def health_check(self) -> bool:
        """健康检查"""
        try:
            # 发送一个预期会失败的请求来检查API是否响应
            response = self.session.post(
                f"{self.base_url}/api/v1/licenses/unbind/",
                json={
                    "activation_code": "HEALTH-CHECK",
                    "license_key": "HEALTH-CHECK",
                    "machine_fingerprint": "0" * 64
                },
                timeout=5
            )
            
            # 任何响应都表示API在工作
            return True
        except requests.exceptions.RequestException as e:
            logging.error(f"API健康检查失败: {e}")
            return False
    
    def performance_check(self) -> dict:
        """性能检查"""
        test_data = {
            "activation_code": "PERF-TEST-CODE",
            "license_key": "PERF-TEST-KEY",
            "machine_fingerprint": "a" * 64
        }
        
        start_time = time.time()
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/licenses/unbind/",
                json=test_data,
                timeout=10
            )
            end_time = time.time()
            response_time = end_time - start_time
            
            return {
                'success': True,
                'response_time': response_time,
                'status_code': response.status_code
            }
        except requests.exceptions.RequestException as e:
            end_time = time.time()
            response_time = end_time - start_time
            
            return {
                'success': False,
                'response_time': response_time,
                'error': str(e)
            }
    
    def run_monitoring(self, interval: int = 60):
        """运行监控"""
        logging.info("开始API监控")
        
        while True:
            try:
                # 健康检查
                is_healthy = self.health_check()
                
                # 性能检查
                perf_result = self.performance_check()
                
                # 记录结果
                status = "HEALTHY" if is_healthy else "UNHEALTHY"
                response_time = perf_result.get('response_time', 0)
                
                logging.info(f"API状态: {status}, 响应时间: {response_time:.3f}s")
                
                if not is_healthy:
                    logging.warning("API健康检查失败")
                
                if response_time > 5.0:
                    logging.warning(f"API响应时间过长: {response_time:.3f}s")
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                logging.info("监控停止")
                break
            except Exception as e:
                logging.error(f"监控异常: {e}")
                time.sleep(interval)

if __name__ == "__main__":
    monitor = APIMonitor('http://localhost:8000', '1')
    monitor.run_monitoring(60)  # 每分钟检查一次
```

### 2. 日志分析脚本

```bash
#!/bin/bash
# analyze_logs.sh

LOG_FILE="/path/to/django/logs/licenses.log"
DATE=$(date +%Y-%m-%d)

echo "API日志分析报告 - $DATE"
echo "=================================="

# 解绑请求统计
echo "解绑请求统计:"
grep "许可证解绑" $LOG_FILE | grep $(date +%Y-%m-%d) | wc -l | xargs -I {} echo "今日解绑请求总数: {}"

# 成功/失败统计
grep "许可证解绑成功" $LOG_FILE | grep $(date +%Y-%m-%d) | wc -l | xargs -I {} echo "成功解绑: {}"
grep "许可证解绑失败" $LOG_FILE | grep $(date +%Y-%m-%d) | wc -l | xargs -I {} echo "失败解绑: {}"

# 错误类型统计
echo -e "\n错误类型分布:"
grep "解绑请求处理异常\|许可证解绑失败" $LOG_FILE | grep $(date +%Y-%m-%d) | \
  sed -n 's/.*: \(.*\)/\1/p' | sort | uniq -c | sort -rn

# 可疑活动统计
echo -e "\n可疑活动统计:"
grep "可疑活动" $LOG_FILE | grep $(date +%Y-%m-%d) | wc -l | xargs -I {} echo "可疑活动检测: {}"

# 频率限制统计
echo -e "\n频率限制统计:"
grep "频率限制" $LOG_FILE | grep $(date +%Y-%m-%d) | wc -l | xargs -I {} echo "触发频率限制: {}"

# 响应时间分析（需要在日志中记录响应时间）
echo -e "\n热门解绑时间段:"
grep "许可证解绑" $LOG_FILE | grep $(date +%Y-%m-%d) | \
  awk '{print $2}' | cut -d: -f1 | sort | uniq -c | sort -rn | head -5
```

## 测试最佳实践

### 1. 测试环境隔离
- 使用独立的测试数据库
- 配置独立的测试租户
- 使用测试专用的API密钥

### 2. 数据清理
```sql
-- 测试后清理数据
DELETE FROM licenses_activation WHERE activation_code LIKE 'TEST-%';
DELETE FROM licenses_machine_binding WHERE machine_id LIKE 'TEST-%';
DELETE FROM licenses_license WHERE license_key LIKE 'TEST%';
DELETE FROM licenses_security_audit_log WHERE details::text LIKE '%测试%';
```

### 3. 测试数据生成
```python
def generate_test_data(count: int):
    """生成测试数据"""
    import uuid
    
    test_data = []
    for i in range(count):
        data = {
            "activation_code": f"TEST-{i:04d}-{uuid.uuid4().hex[:4].upper()}-CODE",
            "license_key": f"TEST{i:02d}-{uuid.uuid4().hex[:4].upper()}-KEY",
            "machine_fingerprint": uuid.uuid4().hex * 2  # 64字符
        }
        test_data.append(data)
    
    return test_data
```

这个测试指南提供了全面的测试方案，包括手动测试、自动化测试、性能测试和监控。通过这些测试，可以确保许可证解绑API的稳定性、可靠性和性能。
