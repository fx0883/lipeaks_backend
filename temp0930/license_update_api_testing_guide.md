# 许可证更新 API 测试调试指南

## 📋 概述

本文档提供许可证更新API的完整测试方案，包括单元测试、集成测试、性能测试和调试技巧，帮助前端开发人员快速定位和解决问题。

## 🧪 API 测试工具

### Postman 测试集合

#### 环境变量设置

```json
{
    "name": "License API Environment",
    "values": [
        {
            "key": "base_url",
            "value": "http://localhost:8000/api/v1",
            "enabled": true
        },
        {
            "key": "auth_token",
            "value": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "enabled": true
        },
        {
            "key": "tenant_id",
            "value": "1",
            "enabled": true
        },
        {
            "key": "license_id",
            "value": "123",
            "enabled": true
        }
    ]
}
```

#### 预请求脚本（获取Token）

```javascript
// Pre-request Script for authentication
pm.test("Get Auth Token", function () {
    if (!pm.globals.get("auth_token")) {
        pm.sendRequest({
            url: pm.environment.get("base_url") + "/auth/login/",
            method: "POST",
            header: {
                "Content-Type": "application/json"
            },
            body: {
                mode: "raw",
                raw: JSON.stringify({
                    username: "admin",
                    password: "admin123"
                })
            }
        }, function (err, response) {
            if (err) {
                console.log("Auth failed:", err);
            } else {
                const jsonData = response.json();
                pm.environment.set("auth_token", jsonData.access_token);
                pm.globals.set("auth_token", jsonData.access_token);
            }
        });
    }
});
```

#### 完整更新测试用例

```json
{
    "name": "Update License (PUT)",
    "request": {
        "method": "PUT",
        "header": [
            {
                "key": "Authorization",
                "value": "Bearer {{auth_token}}"
            },
            {
                "key": "Content-Type",
                "value": "application/json"
            },
            {
                "key": "X-Tenant-ID",
                "value": "{{tenant_id}}"
            }
        ],
        "url": {
            "raw": "{{base_url}}/licenses/admin/licenses/{{license_id}}/",
            "host": ["{{base_url}}"],
            "path": ["licenses", "admin", "licenses", "{{license_id}}", ""]
        },
        "body": {
            "mode": "raw",
            "raw": "{\n    \"customer_name\": \"张三更新\",\n    \"customer_email\": \"zhangsan_updated@example.com\",\n    \"max_activations\": 10,\n    \"expires_at\": \"2024-12-31T23:59:59Z\",\n    \"status\": \"activated\",\n    \"notes\": \"测试更新许可证\",\n    \"metadata\": {\n        \"test\": \"updated\",\n        \"environment\": \"development\"\n    }\n}"
        }
    },
    "tests": [
        "pm.test('Status code is 200', function () {",
        "    pm.response.to.have.status(200);",
        "});",
        "",
        "pm.test('Response has correct structure', function () {",
        "    const jsonData = pm.response.json();",
        "    pm.expect(jsonData).to.have.property('id');",
        "    pm.expect(jsonData).to.have.property('customer_name');",
        "    pm.expect(jsonData).to.have.property('customer_email');",
        "});",
        "",
        "pm.test('Updated fields are correct', function () {",
        "    const jsonData = pm.response.json();",
        "    pm.expect(jsonData.customer_name).to.eql('张三更新');",
        "    pm.expect(jsonData.customer_email).to.eql('zhangsan_updated@example.com');",
        "    pm.expect(jsonData.max_activations).to.eql(10);",
        "});"
    ]
}
```

#### 部分更新测试用例

```json
{
    "name": "Partial Update License (PATCH)",
    "request": {
        "method": "PATCH",
        "header": [
            {
                "key": "Authorization",
                "value": "Bearer {{auth_token}}"
            },
            {
                "key": "Content-Type",
                "value": "application/json"
            }
        ],
        "url": {
            "raw": "{{base_url}}/licenses/admin/licenses/{{license_id}}/",
            "host": ["{{base_url}}"],
            "path": ["licenses", "admin", "licenses", "{{license_id}}", ""]
        },
        "body": {
            "mode": "raw",
            "raw": "{\n    \"notes\": \"部分更新测试\",\n    \"metadata\": {\n        \"updated_field\": \"notes_only\"\n    }\n}"
        }
    }
}
```

### cURL 命令示例

#### 基础更新测试

```bash
# 完整更新
curl -X PUT "http://localhost:8000/api/v1/licenses/admin/licenses/123/" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 1" \
  -d '{
    "customer_name": "李四",
    "customer_email": "lisi@example.com",
    "max_activations": 15,
    "expires_at": "2024-12-31T23:59:59Z",
    "status": "activated",
    "notes": "企业版客户",
    "metadata": {
        "region": "asia",
        "priority": "high"
    }
}'

# 部分更新
curl -X PATCH "http://localhost:8000/api/v1/licenses/admin/licenses/123/" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "expires_at": "2025-06-30T23:59:59Z",
    "notes": "延长6个月"
}'
```

#### 错误场景测试

```bash
# 测试无效邮箱
curl -X PUT "http://localhost:8000/api/v1/licenses/admin/licenses/123/" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_email": "invalid-email"
}'

# 测试过小的激活数
curl -X PUT "http://localhost:8000/api/v1/licenses/admin/licenses/123/" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "max_activations": 1
}'

# 测试过期时间早于当前时间
curl -X PUT "http://localhost:8000/api/v1/licenses/admin/licenses/123/" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "expires_at": "2020-01-01T00:00:00Z"
}'
```

## 🔍 前端JavaScript测试

### 单元测试 (Jest)

```javascript
// licenseUpdateService.test.js
import { LicenseUpdateService } from './licenseUpdateService';

describe('LicenseUpdateService', () => {
    let service;
    let mockFetch;
    
    beforeEach(() => {
        service = new LicenseUpdateService('http://localhost:8000/api/v1', 'mock-token');
        mockFetch = jest.fn();
        global.fetch = mockFetch;
    });
    
    afterEach(() => {
        jest.resetAllMocks();
    });
    
    describe('updateLicense', () => {
        it('should successfully update license with valid data', async () => {
            const licenseId = 123;
            const updateData = {
                customer_name: '张三',
                customer_email: 'zhangsan@example.com',
                max_activations: 5
            };
            
            const expectedResponse = {
                id: licenseId,
                customer_name: '张三',
                customer_email: 'zhangsan@example.com',
                max_activations: 5,
                status: 'activated'
            };
            
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: jest.fn().mockResolvedValueOnce(expectedResponse)
            });
            
            const result = await service.updateLicense(licenseId, updateData);
            
            expect(mockFetch).toHaveBeenCalledWith(
                `http://localhost:8000/api/v1/licenses/admin/licenses/${licenseId}/`,
                expect.objectContaining({
                    method: 'PUT',
                    headers: expect.objectContaining({
                        'Authorization': 'Bearer mock-token',
                        'Content-Type': 'application/json'
                    }),
                    body: JSON.stringify(updateData)
                })
            );
            
            expect(result).toEqual(expectedResponse);
        });
        
        it('should throw error for invalid email format', async () => {
            const licenseId = 123;
            const updateData = {
                customer_email: 'invalid-email'
            };
            
            mockFetch.mockResolvedValueOnce({
                ok: false,
                status: 400,
                json: jest.fn().mockResolvedValueOnce({
                    success: false,
                    data: {
                        customer_email: ['请输入有效的电子邮箱地址。']
                    }
                })
            });
            
            await expect(service.updateLicense(licenseId, updateData))
                .rejects.toThrow('请输入有效的电子邮箱地址。');
        });
        
        it('should handle network errors gracefully', async () => {
            const licenseId = 123;
            const updateData = { customer_name: '张三' };
            
            mockFetch.mockRejectedValueOnce(new Error('Network error'));
            
            await expect(service.updateLicense(licenseId, updateData))
                .rejects.toThrow('Network error');
        });
        
        it('should handle 401 unauthorized error', async () => {
            const licenseId = 123;
            const updateData = { customer_name: '张三' };
            
            mockFetch.mockResolvedValueOnce({
                ok: false,
                status: 401,
                json: jest.fn().mockResolvedValueOnce({
                    success: false,
                    message: '认证失败'
                })
            });
            
            await expect(service.updateLicense(licenseId, updateData))
                .rejects.toThrow('认证失败');
        });
    });
    
    describe('partialUpdateLicense', () => {
        it('should send PATCH request for partial updates', async () => {
            const licenseId = 123;
            const partialData = { notes: '更新备注' };
            
            mockFetch.mockResolvedValueOnce({
                ok: true,
                json: jest.fn().mockResolvedValueOnce({
                    id: licenseId,
                    notes: '更新备注'
                })
            });
            
            await service.partialUpdateLicense(licenseId, partialData);
            
            expect(mockFetch).toHaveBeenCalledWith(
                expect.any(String),
                expect.objectContaining({
                    method: 'PATCH'
                })
            );
        });
    });
});
```

### 表单组件测试 (React Testing Library)

```javascript
// LicenseUpdateForm.test.jsx
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LicenseUpdateForm } from './LicenseUpdateForm';

// Mock API service
jest.mock('./licenseUpdateService');

describe('LicenseUpdateForm', () => {
    const mockLicenseData = {
        id: 123,
        customer_name: '张三',
        customer_email: 'zhangsan@example.com',
        max_activations: 5,
        current_activations: 2,
        expires_at: '2024-12-31T23:59:59Z',
        status: 'activated',
        notes: '测试许可证',
        metadata: { test: 'value' }
    };
    
    const mockOnSuccess = jest.fn();
    const mockOnCancel = jest.fn();
    
    beforeEach(() => {
        jest.clearAllMocks();
    });
    
    it('should render form with license data', async () => {
        render(
            <LicenseUpdateForm
                licenseId={123}
                initialData={mockLicenseData}
                onSuccess={mockOnSuccess}
                onCancel={mockOnCancel}
            />
        );
        
        await waitFor(() => {
            expect(screen.getByDisplayValue('张三')).toBeInTheDocument();
            expect(screen.getByDisplayValue('zhangsan@example.com')).toBeInTheDocument();
            expect(screen.getByDisplayValue('5')).toBeInTheDocument();
        });
    });
    
    it('should validate email format on input', async () => {
        const user = userEvent.setup();
        
        render(
            <LicenseUpdateForm
                licenseId={123}
                initialData={mockLicenseData}
                onSuccess={mockOnSuccess}
                onCancel={mockOnCancel}
            />
        );
        
        const emailInput = screen.getByLabelText(/客户邮箱/);
        
        await user.clear(emailInput);
        await user.type(emailInput, 'invalid-email');
        await user.tab();
        
        await waitFor(() => {
            expect(screen.getByText(/请输入有效的邮箱地址/)).toBeInTheDocument();
        });
    });
    
    it('should prevent submission with invalid max activations', async () => {
        const user = userEvent.setup();
        
        render(
            <LicenseUpdateForm
                licenseId={123}
                initialData={mockLicenseData}
                onSuccess={mockOnSuccess}
                onCancel={mockOnCancel}
            />
        );
        
        const maxActivationsInput = screen.getByLabelText(/最大激活数/);
        const submitButton = screen.getByText('更新许可证');
        
        await user.clear(maxActivationsInput);
        await user.type(maxActivationsInput, '1'); // 小于当前激活数2
        
        fireEvent.click(submitButton);
        
        await waitFor(() => {
            expect(screen.getByText(/不能小于当前激活数/)).toBeInTheDocument();
        });
        
        expect(mockOnSuccess).not.toHaveBeenCalled();
    });
    
    it('should call onSuccess after successful update', async () => {
        const user = userEvent.setup();
        
        // Mock successful API response
        const mockUpdateService = require('./licenseUpdateService');
        mockUpdateService.updateLicense = jest.fn().mockResolvedValueOnce({
            ...mockLicenseData,
            customer_name: '李四'
        });
        
        render(
            <LicenseUpdateForm
                licenseId={123}
                initialData={mockLicenseData}
                onSuccess={mockOnSuccess}
                onCancel={mockOnCancel}
            />
        );
        
        const nameInput = screen.getByLabelText(/客户姓名/);
        const submitButton = screen.getByText('更新许可证');
        
        await user.clear(nameInput);
        await user.type(nameInput, '李四');
        
        fireEvent.click(submitButton);
        
        await waitFor(() => {
            expect(mockOnSuccess).toHaveBeenCalledWith(
                expect.objectContaining({
                    customer_name: '李四'
                })
            );
        });
    });
    
    it('should show loading state during submission', async () => {
        const user = userEvent.setup();
        
        // Mock delayed API response
        const mockUpdateService = require('./licenseUpdateService');
        mockUpdateService.updateLicense = jest.fn().mockImplementation(
            () => new Promise(resolve => setTimeout(resolve, 1000))
        );
        
        render(
            <LicenseUpdateForm
                licenseId={123}
                initialData={mockLicenseData}
                onSuccess={mockOnSuccess}
                onCancel={mockOnCancel}
            />
        );
        
        const nameInput = screen.getByLabelText(/客户姓名/);
        const submitButton = screen.getByText('更新许可证');
        
        await user.type(nameInput, ' 更新');
        fireEvent.click(submitButton);
        
        expect(screen.getByText('更新中...')).toBeInTheDocument();
        expect(submitButton).toBeDisabled();
    });
});
```

## 📊 性能测试

### API 性能测试脚本

```javascript
// performanceTest.js
const axios = require('axios');
const fs = require('fs');

class LicenseUpdatePerformanceTest {
    constructor(baseUrl, authToken) {
        this.baseUrl = baseUrl;
        this.authToken = authToken;
        this.results = [];
    }
    
    async runSingleUpdateTest(licenseId, testData) {
        const startTime = Date.now();
        
        try {
            const response = await axios.put(
                `${this.baseUrl}/licenses/admin/licenses/${licenseId}/`,
                testData,
                {
                    headers: {
                        'Authorization': `Bearer ${this.authToken}`,
                        'Content-Type': 'application/json'
                    }
                }
            );
            
            const endTime = Date.now();
            const duration = endTime - startTime;
            
            return {
                success: true,
                duration,
                status: response.status,
                dataSize: JSON.stringify(response.data).length
            };
            
        } catch (error) {
            const endTime = Date.now();
            const duration = endTime - startTime;
            
            return {
                success: false,
                duration,
                status: error.response?.status || 0,
                error: error.message
            };
        }
    }
    
    async runConcurrencyTest(licenseId, testData, concurrency = 10, iterations = 100) {
        console.log(`开始并发测试: ${concurrency} 并发, ${iterations} 次迭代`);
        
        const promises = [];
        const startTime = Date.now();
        
        for (let i = 0; i < iterations; i++) {
            const promise = this.runSingleUpdateTest(licenseId, {
                ...testData,
                notes: `并发测试 #${i}`
            }).then(result => ({
                ...result,
                iteration: i
            }));
            
            promises.push(promise);
            
            // 控制并发数
            if (promises.length >= concurrency) {
                const results = await Promise.all(promises);
                this.results.push(...results);
                promises.length = 0;
                
                // 短暂延迟避免过度请求
                await this.sleep(10);
            }
        }
        
        // 处理剩余的请求
        if (promises.length > 0) {
            const results = await Promise.all(promises);
            this.results.push(...results);
        }
        
        const totalTime = Date.now() - startTime;
        return this.analyzeResults(totalTime);
    }
    
    analyzeResults(totalTime) {
        const successfulRequests = this.results.filter(r => r.success);
        const failedRequests = this.results.filter(r => !r.success);
        
        const durations = successfulRequests.map(r => r.duration);
        const avgDuration = durations.reduce((a, b) => a + b, 0) / durations.length;
        const minDuration = Math.min(...durations);
        const maxDuration = Math.max(...durations);
        
        // 计算百分位数
        const sortedDurations = durations.sort((a, b) => a - b);
        const p95 = sortedDurations[Math.floor(sortedDurations.length * 0.95)];
        const p99 = sortedDurations[Math.floor(sortedDurations.length * 0.99)];
        
        const analysis = {
            totalRequests: this.results.length,
            successfulRequests: successfulRequests.length,
            failedRequests: failedRequests.length,
            successRate: (successfulRequests.length / this.results.length * 100).toFixed(2),
            totalTime,
            requestsPerSecond: (this.results.length / (totalTime / 1000)).toFixed(2),
            averageResponseTime: avgDuration.toFixed(2),
            minResponseTime: minDuration,
            maxResponseTime: maxDuration,
            p95ResponseTime: p95,
            p99ResponseTime: p99,
            errors: this.getErrorSummary(failedRequests)
        };
        
        return analysis;
    }
    
    getErrorSummary(failedRequests) {
        const errorCounts = {};
        failedRequests.forEach(request => {
            const key = `${request.status}: ${request.error}`;
            errorCounts[key] = (errorCounts[key] || 0) + 1;
        });
        return errorCounts;
    }
    
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    saveResults(filename) {
        fs.writeFileSync(filename, JSON.stringify({
            timestamp: new Date().toISOString(),
            results: this.results
        }, null, 2));
    }
}

// 使用示例
async function runPerformanceTest() {
    const tester = new LicenseUpdatePerformanceTest(
        'http://localhost:8000/api/v1',
        'your-auth-token-here'
    );
    
    const testData = {
        customer_name: '性能测试',
        customer_email: 'performance@test.com',
        max_activations: 10,
        notes: '性能测试数据'
    };
    
    // 单个请求性能测试
    console.log('单个请求测试...');
    const singleResult = await tester.runSingleUpdateTest(123, testData);
    console.log('单个请求结果:', singleResult);
    
    // 并发性能测试
    console.log('并发测试...');
    const concurrencyResult = await tester.runConcurrencyTest(123, testData, 5, 50);
    console.log('并发测试结果:', concurrencyResult);
    
    // 保存详细结果
    tester.saveResults('performance_test_results.json');
}

// 运行测试
if (require.main === module) {
    runPerformanceTest().catch(console.error);
}
```

### 前端性能监控

```javascript
// performanceMonitor.js
class LicenseUpdatePerformanceMonitor {
    constructor() {
        this.metrics = [];
        this.isMonitoring = false;
    }
    
    startMonitoring() {
        this.isMonitoring = true;
        console.log('性能监控已启动');
    }
    
    stopMonitoring() {
        this.isMonitoring = false;
        console.log('性能监控已停止');
    }
    
    recordMetric(operation, startTime, endTime, metadata = {}) {
        if (!this.isMonitoring) return;
        
        const metric = {
            operation,
            duration: endTime - startTime,
            timestamp: new Date().toISOString(),
            metadata
        };
        
        this.metrics.push(metric);
        
        // 性能警告
        if (metric.duration > 3000) { // 超过3秒
            console.warn(`性能警告: ${operation} 耗时 ${metric.duration}ms`, metadata);
        }
        
        return metric;
    }
    
    wrapApiCall(apiFunction, operationName) {
        return async (...args) => {
            if (!this.isMonitoring) {
                return await apiFunction(...args);
            }
            
            const startTime = performance.now();
            
            try {
                const result = await apiFunction(...args);
                const endTime = performance.now();
                
                this.recordMetric(operationName, startTime, endTime, {
                    status: 'success',
                    args: args.length
                });
                
                return result;
                
            } catch (error) {
                const endTime = performance.now();
                
                this.recordMetric(operationName, startTime, endTime, {
                    status: 'error',
                    error: error.message,
                    args: args.length
                });
                
                throw error;
            }
        };
    }
    
    getMetricsSummary() {
        if (this.metrics.length === 0) {
            return { message: '暂无性能数据' };
        }
        
        const operationGroups = {};
        
        this.metrics.forEach(metric => {
            if (!operationGroups[metric.operation]) {
                operationGroups[metric.operation] = [];
            }
            operationGroups[metric.operation].push(metric);
        });
        
        const summary = {};
        
        Object.keys(operationGroups).forEach(operation => {
            const metrics = operationGroups[operation];
            const durations = metrics.map(m => m.duration);
            const successCount = metrics.filter(m => m.metadata.status === 'success').length;
            
            summary[operation] = {
                totalCalls: metrics.length,
                successCount,
                errorCount: metrics.length - successCount,
                averageDuration: (durations.reduce((a, b) => a + b, 0) / durations.length).toFixed(2),
                minDuration: Math.min(...durations).toFixed(2),
                maxDuration: Math.max(...durations).toFixed(2)
            };
        });
        
        return summary;
    }
    
    exportMetrics() {
        return {
            summary: this.getMetricsSummary(),
            rawMetrics: this.metrics,
            exportTime: new Date().toISOString()
        };
    }
    
    clearMetrics() {
        this.metrics = [];
        console.log('性能数据已清空');
    }
}

// 使用示例
const performanceMonitor = new LicenseUpdatePerformanceMonitor();

// 包装API调用
const wrappedUpdateLicense = performanceMonitor.wrapApiCall(
    updateLicenseApi, 
    'license_update'
);

// 启动监控
performanceMonitor.startMonitoring();

// 执行被监控的API调用
wrappedUpdateLicense(123, updateData)
    .then(result => {
        console.log('更新成功:', result);
        console.log('性能摘要:', performanceMonitor.getMetricsSummary());
    })
    .catch(error => {
        console.error('更新失败:', error);
    });
```

## 🐛 调试技巧

### 浏览器开发者工具调试

```javascript
// 调试工具函数
window.licenseDebugger = {
    // 启用详细日志
    enableVerboseLogging() {
        window.LICENSE_DEBUG = true;
        console.log('许可证调试模式已启用');
    },
    
    // 禁用详细日志
    disableVerboseLogging() {
        window.LICENSE_DEBUG = false;
        console.log('许可证调试模式已禁用');
    },
    
    // 模拟API错误
    simulateApiError(errorType) {
        const originalFetch = window.fetch;
        
        window.fetch = function(...args) {
            if (args[0].includes('/licenses/admin/licenses/')) {
                switch (errorType) {
                    case '400':
                        return Promise.resolve({
                            ok: false,
                            status: 400,
                            json: () => Promise.resolve({
                                success: false,
                                data: { customer_email: ['邮箱格式无效'] }
                            })
                        });
                    case '401':
                        return Promise.resolve({
                            ok: false,
                            status: 401,
                            json: () => Promise.resolve({
                                success: false,
                                message: '认证失败'
                            })
                        });
                    case '500':
                        return Promise.resolve({
                            ok: false,
                            status: 500,
                            json: () => Promise.resolve({
                                success: false,
                                message: '服务器内部错误'
                            })
                        });
                    case 'network':
                        return Promise.reject(new Error('Network error'));
                }
            }
            return originalFetch.apply(this, args);
        };
        
        console.log(`API错误模拟已启用: ${errorType}`);
        
        // 5秒后自动恢复
        setTimeout(() => {
            window.fetch = originalFetch;
            console.log('API错误模拟已禁用');
        }, 5000);
    },
    
    // 监控表单状态
    monitorFormState(formElement) {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'attributes' && mutation.attributeName === 'value') {
                    console.log('表单字段变化:', mutation.target.name, mutation.target.value);
                }
            });
        });
        
        const inputs = formElement.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            observer.observe(input, { attributes: true, attributeFilter: ['value'] });
            
            input.addEventListener('input', (e) => {
                console.log('输入事件:', e.target.name, e.target.value);
            });
        });
        
        console.log('表单状态监控已启用');
        return observer;
    },
    
    // 验证API响应格式
    validateApiResponse(response, expectedFields) {
        const missing = expectedFields.filter(field => !(field in response));
        const extra = Object.keys(response).filter(field => !expectedFields.includes(field));
        
        console.group('API响应验证');
        console.log('预期字段:', expectedFields);
        console.log('实际字段:', Object.keys(response));
        
        if (missing.length > 0) {
            console.warn('缺少字段:', missing);
        }
        
        if (extra.length > 0) {
            console.info('额外字段:', extra);
        }
        
        if (missing.length === 0) {
            console.log('✅ 响应格式正确');
        }
        
        console.groupEnd();
        
        return { missing, extra, valid: missing.length === 0 };
    },
    
    // 性能分析
    analyzePerformance(operationName, fn) {
        return async (...args) => {
            const startTime = performance.now();
            const startMemory = performance.memory?.usedJSHeapSize || 0;
            
            console.time(operationName);
            
            try {
                const result = await fn(...args);
                
                const endTime = performance.now();
                const endMemory = performance.memory?.usedJSHeapSize || 0;
                
                console.timeEnd(operationName);
                console.group(`性能分析: ${operationName}`);
                console.log(`执行时间: ${(endTime - startTime).toFixed(2)}ms`);
                console.log(`内存变化: ${(endMemory - startMemory)} bytes`);
                console.groupEnd();
                
                return result;
                
            } catch (error) {
                console.timeEnd(operationName);
                console.error(`操作失败: ${operationName}`, error);
                throw error;
            }
        };
    }
};

// 使用示例
console.log('许可证调试工具已加载，使用 window.licenseDebugger 访问');
```

### 常见问题诊断清单

```javascript
// 问题诊断工具
const licenseUpdateDiagnostic = {
    // 诊断认证问题
    async diagnoseAuthIssues() {
        const token = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
        
        console.group('🔐 认证诊断');
        
        if (!token) {
            console.error('❌ 未找到认证Token');
            console.info('💡 解决方案: 重新登录获取Token');
            console.groupEnd();
            return false;
        }
        
        console.log('✅ Token存在');
        
        // 检查Token格式
        const tokenParts = token.split('.');
        if (tokenParts.length !== 3) {
            console.error('❌ Token格式无效');
            console.info('💡 解决方案: 重新登录获取新Token');
            console.groupEnd();
            return false;
        }
        
        console.log('✅ Token格式正确');
        
        // 检查Token过期时间
        try {
            const payload = JSON.parse(atob(tokenParts[1]));
            const now = Math.floor(Date.now() / 1000);
            
            if (payload.exp && payload.exp < now) {
                console.error('❌ Token已过期');
                console.info('💡 解决方案: 重新登录获取新Token');
                console.groupEnd();
                return false;
            }
            
            console.log('✅ Token未过期');
            console.log('Token信息:', {
                用户ID: payload.user_id,
                用户名: payload.username,
                过期时间: new Date(payload.exp * 1000).toLocaleString()
            });
            
        } catch (e) {
            console.warn('⚠️ 无法解析Token内容');
        }
        
        console.groupEnd();
        return true;
    },
    
    // 诊断网络问题
    async diagnoseNetworkIssues() {
        console.group('🌐 网络诊断');
        
        const testUrls = [
            '/api/v1/licenses/admin/licenses/',
            '/api/v1/auth/user/',
            '/api/v1/health/'
        ];
        
        for (const url of testUrls) {
            try {
                const response = await fetch(url, { method: 'HEAD' });
                console.log(`✅ ${url} - 状态: ${response.status}`);
            } catch (error) {
                console.error(`❌ ${url} - 错误: ${error.message}`);
            }
        }
        
        console.groupEnd();
    },
    
    // 诊断表单验证问题
    diagnoseValidationIssues(formData) {
        console.group('✅ 表单验证诊断');
        
        const validationRules = {
            customer_name: {
                required: true,
                minLength: 1,
                maxLength: 100
            },
            customer_email: {
                required: true,
                pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/
            },
            max_activations: {
                type: 'number',
                min: 1,
                max: 1000
            },
            expires_at: {
                type: 'datetime',
                futureDate: true
            }
        };
        
        let isValid = true;
        
        Object.entries(validationRules).forEach(([field, rules]) => {
            const value = formData[field];
            
            console.group(`字段: ${field}`);
            
            if (rules.required && (!value || value.toString().trim() === '')) {
                console.error('❌ 必填字段为空');
                isValid = false;
            } else if (value) {
                if (rules.minLength && value.toString().length < rules.minLength) {
                    console.error(`❌ 长度不足 (最少${rules.minLength}字符)`);
                    isValid = false;
                }
                
                if (rules.maxLength && value.toString().length > rules.maxLength) {
                    console.error(`❌ 长度超限 (最多${rules.maxLength}字符)`);
                    isValid = false;
                }
                
                if (rules.pattern && !rules.pattern.test(value)) {
                    console.error('❌ 格式不正确');
                    isValid = false;
                }
                
                if (rules.type === 'number' && isNaN(value)) {
                    console.error('❌ 不是有效数字');
                    isValid = false;
                } else if (rules.type === 'number') {
                    if (rules.min && value < rules.min) {
                        console.error(`❌ 数值过小 (最小${rules.min})`);
                        isValid = false;
                    }
                    if (rules.max && value > rules.max) {
                        console.error(`❌ 数值过大 (最大${rules.max})`);
                        isValid = false;
                    }
                }
                
                if (rules.futureDate && new Date(value) <= new Date()) {
                    console.error('❌ 日期必须是未来时间');
                    isValid = false;
                }
                
                if (isValid) {
                    console.log('✅ 验证通过');
                }
            } else {
                console.log('ℹ️ 可选字段，跳过验证');
            }
            
            console.groupEnd();
        });
        
        console.log(`总体验证结果: ${isValid ? '✅ 通过' : '❌ 失败'}`);
        console.groupEnd();
        
        return isValid;
    }
};

// 快捷诊断命令
window.diagnoseLicenseUpdate = async (formData) => {
    console.clear();
    console.log('🔍 许可证更新问题诊断开始...');
    
    const authOk = await licenseUpdateDiagnostic.diagnoseAuthIssues();
    await licenseUpdateDiagnostic.diagnoseNetworkIssues();
    
    if (formData) {
        licenseUpdateDiagnostic.diagnoseValidationIssues(formData);
    }
    
    console.log('✨ 诊断完成');
    
    if (!authOk) {
        console.info('🎯 建议: 优先解决认证问题');
    }
};
```

## 📈 监控和日志

### 生产环境监控

```javascript
// 生产监控配置
const productionMonitoring = {
    // 错误上报
    reportError(error, context = {}) {
        const errorReport = {
            timestamp: new Date().toISOString(),
            error: {
                message: error.message,
                stack: error.stack,
                name: error.name
            },
            context: {
                url: window.location.href,
                userAgent: navigator.userAgent,
                userId: this.getCurrentUserId(),
                ...context
            }
        };
        
        // 发送到监控服务
        this.sendToMonitoringService(errorReport);
        
        // 本地日志
        console.error('生产错误:', errorReport);
    },
    
    // 性能监控
    trackPerformance(operation, duration, metadata = {}) {
        const performanceData = {
            timestamp: new Date().toISOString(),
            operation,
            duration,
            metadata: {
                ...metadata,
                url: window.location.href,
                userId: this.getCurrentUserId()
            }
        };
        
        // 发送性能数据
        this.sendToMonitoringService(performanceData, 'performance');
        
        // 性能阈值警告
        if (duration > 5000) { // 5秒
            console.warn('性能警告:', performanceData);
        }
    },
    
    getCurrentUserId() {
        try {
            const token = localStorage.getItem('authToken');
            if (token) {
                const payload = JSON.parse(atob(token.split('.')[1]));
                return payload.user_id;
            }
        } catch (e) {
            return null;
        }
        return null;
    },
    
    sendToMonitoringService(data, type = 'error') {
        // 实际项目中替换为真实的监控服务端点
        if (process.env.NODE_ENV === 'production') {
            fetch('/api/v1/monitoring/collect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ type, data })
            }).catch(() => {
                // 监控服务不可用时不影响正常功能
            });
        }
    }
};
```

---

*文档版本: v1.0*  
*更新时间: 2024-09-30*  
*维护者: 开发团队*
