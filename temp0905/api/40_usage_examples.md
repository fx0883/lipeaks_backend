# API使用示例和最佳实践

## 概述

本文档提供Licenses API的完整使用示例和最佳实践指南，帮助开发者高效、安全地集成许可证管理功能。

## 完整集成示例

### 管理端集成示例

#### React + TypeScript 管理界面
```typescript
// types/license.ts
export interface License {
  id: number;
  license_key: string;
  customer_name: string;
  customer_email: string;
  status: 'generated' | 'active' | 'suspended' | 'revoked' | 'expired';
  expires_at: string;
  activation_count: number;
  max_activations: number;
}

export interface LicensePlan {
  id: number;
  name: string;
  plan_type: string;
  price: string;
  max_devices: number;
  validity_days: number;
}

// services/LicenseService.ts
import axios, { AxiosInstance } from 'axios';

class LicenseService {
  private api: AxiosInstance;
  
  constructor(baseURL: string, token: string) {
    this.api = axios.create({
      baseURL,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    });
    
    // 响应拦截器处理token过期
    this.api.interceptors.response.use(
      response => response,
      async error => {
        if (error.response?.status === 401) {
          // 处理token刷新逻辑
          await this.refreshToken();
          return this.api.request(error.config);
        }
        return Promise.reject(error);
      }
    );
  }
  
  // 产品管理
  async getProducts(params?: any) {
    const response = await this.api.get('/admin/products/', { params });
    return response.data;
  }
  
  async createProduct(data: any) {
    const response = await this.api.post('/admin/products/', data);
    return response.data;
  }
  
  // 许可证管理
  async getLicenses(params?: any) {
    const response = await this.api.get('/admin/licenses/', { params });
    return response.data;
  }
  
  async createLicense(data: any) {
    const response = await this.api.post('/admin/licenses/', data);
    return response.data;
  }
  
  async batchCreateLicenses(planId: number, customers: any[]) {
    const response = await this.api.post('/admin/licenses/batch_create/', {
      license_plan: planId,
      licenses: customers
    });
    return response.data;
  }
  
  async updateLicenseStatus(id: number, status: string, reason?: string) {
    const response = await this.api.patch(`/admin/licenses/${id}/`, {
      status,
      reason
    });
    return response.data;
  }
  
  // 报告功能
  async getDashboard(period = 'last_30_days') {
    const response = await this.api.get(`/reports/dashboard/?period=${period}`);
    return response.data;
  }
  
  private async refreshToken() {
    // 实现token刷新逻辑
  }
}

// components/LicenseManager.tsx
import React, { useState, useEffect } from 'react';
import { LicenseService } from '../services/LicenseService';

interface Props {
  licenseService: LicenseService;
}

export const LicenseManager: React.FC<Props> = ({ licenseService }) => {
  const [licenses, setLicenses] = useState<License[]>([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    status: '',
    search: '',
    page: 1
  });
  
  useEffect(() => {
    loadLicenses();
  }, [filters]);
  
  const loadLicenses = async () => {
    setLoading(true);
    try {
      const response = await licenseService.getLicenses(filters);
      setLicenses(response.data.results);
    } catch (error) {
      console.error('加载许可证失败:', error);
    } finally {
      setLoading(false);
    }
  };
  
  const handleStatusChange = async (id: number, newStatus: string) => {
    try {
      await licenseService.updateLicenseStatus(id, newStatus);
      await loadLicenses(); // 重新加载数据
    } catch (error) {
      console.error('状态更新失败:', error);
    }
  };
  
  const handleBatchCreate = async (planId: number, customerList: any[]) => {
    try {
      const result = await licenseService.batchCreateLicenses(planId, customerList);
      console.log(`成功创建 ${result.data.created.length} 个许可证`);
      await loadLicenses();
    } catch (error) {
      console.error('批量创建失败:', error);
    }
  };
  
  return (
    <div className="license-manager">
      {/* 过滤器组件 */}
      <div className="filters">
        <input
          type="text"
          placeholder="搜索许可证..."
          value={filters.search}
          onChange={(e) => setFilters({...filters, search: e.target.value})}
        />
        <select
          value={filters.status}
          onChange={(e) => setFilters({...filters, status: e.target.value})}
        >
          <option value="">所有状态</option>
          <option value="active">已激活</option>
          <option value="suspended">已挂起</option>
          <option value="expired">已过期</option>
        </select>
      </div>
      
      {/* 许可证列表 */}
      <div className="license-list">
        {loading ? (
          <div>加载中...</div>
        ) : (
          licenses.map(license => (
            <div key={license.id} className="license-item">
              <h3>{license.license_key}</h3>
              <p>客户: {license.customer_name} ({license.customer_email})</p>
              <p>状态: {license.status}</p>
              <p>激活: {license.activation_count}/{license.max_activations}</p>
              <p>过期时间: {new Date(license.expires_at).toLocaleDateString()}</p>
              
              <div className="actions">
                <button onClick={() => handleStatusChange(license.id, 'suspended')}>
                  挂起
                </button>
                <button onClick={() => handleStatusChange(license.id, 'active')}>
                  恢复
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

// 使用示例
const App: React.FC = () => {
  const licenseService = new LicenseService(
    'https://api.example.com/api/v1/licenses',
    localStorage.getItem('access_token') || ''
  );
  
  return (
    <div className="app">
      <LicenseManager licenseService={licenseService} />
    </div>
  );
};
```

### 客户端集成示例

#### C# .NET 客户端库
```csharp
// Models/LicenseInfo.cs
public class LicenseInfo
{
    public string LicenseKey { get; set; }
    public string Status { get; set; }
    public DateTime ExpiresAt { get; set; }
    public Dictionary<string, bool> Features { get; set; }
}

public class ActivationResponse
{
    public bool Success { get; set; }
    public string ActivationCode { get; set; }
    public LicenseInfo LicenseInfo { get; set; }
    public string Error { get; set; }
}

// Services/LicenseClient.cs
using System;
using System.Net.Http;
using System.Text.Json;
using System.Threading.Tasks;
using System.Security.Cryptography;
using System.Text;
using Microsoft.Win32;

public class LicenseClient
{
    private readonly HttpClient _httpClient;
    private readonly string _baseUrl;
    private string _activationCode;
    private string _machineFingerprint;
    private Timer _heartbeatTimer;
    
    public LicenseClient(string baseUrl)
    {
        _baseUrl = baseUrl;
        _httpClient = new HttpClient();
        _machineFingerprint = GenerateMachineFingerprint();
        
        // 从注册表加载已保存的激活码
        LoadActivationCode();
    }
    
    public async Task<ActivationResponse> ActivateAsync(string licenseKey)
    {
        var request = new
        {
            license_key = licenseKey,
            machine_fingerprint = _machineFingerprint,
            machine_name = Environment.MachineName,
            hardware_info = GetHardwareInfo()
        };
        
        var json = JsonSerializer.Serialize(request);
        var content = new StringContent(json, Encoding.UTF8, "application/json");
        
        try
        {
            var response = await _httpClient.PostAsync($"{_baseUrl}/activate/", content);
            var responseJson = await response.Content.ReadAsStringAsync();
            var result = JsonSerializer.Deserialize<ActivationResponse>(responseJson);
            
            if (result.Success)
            {
                _activationCode = result.ActivationCode;
                SaveActivationCode();
                StartHeartbeat();
            }
            
            return result;
        }
        catch (Exception ex)
        {
            return new ActivationResponse 
            { 
                Success = false, 
                Error = $"网络错误: {ex.Message}" 
            };
        }
    }
    
    public async Task<bool> VerifyAsync()
    {
        if (string.IsNullOrEmpty(_activationCode))
            return false;
            
        var request = new
        {
            activation_code = _activationCode,
            machine_fingerprint = _machineFingerprint
        };
        
        var json = JsonSerializer.Serialize(request);
        var content = new StringContent(json, Encoding.UTF8, "application/json");
        
        try
        {
            var response = await _httpClient.PostAsync($"{_baseUrl}/verify/", content);
            var responseJson = await response.Content.ReadAsStringAsync();
            var result = JsonSerializer.Deserialize<dynamic>(responseJson);
            
            return result.success && result.data.is_valid;
        }
        catch
        {
            return false;
        }
    }
    
    private string GenerateMachineFingerprint()
    {
        var machineInfo = new
        {
            MachineName = Environment.MachineName,
            UserName = Environment.UserName,
            OSVersion = Environment.OSVersion.ToString(),
            ProcessorCount = Environment.ProcessorCount,
            // 可以添加更多硬件特征
        };
        
        var json = JsonSerializer.Serialize(machineInfo);
        using var sha256 = SHA256.Create();
        var hash = sha256.ComputeHash(Encoding.UTF8.GetBytes(json));
        return Convert.ToHexString(hash).ToLower();
    }
    
    private object GetHardwareInfo()
    {
        return new
        {
            os = Environment.OSVersion.ToString(),
            machine_name = Environment.MachineName,
            processor_count = Environment.ProcessorCount,
            total_memory = GC.GetTotalMemory(false)
        };
    }
    
    private void StartHeartbeat()
    {
        _heartbeatTimer = new Timer(async _ => 
        {
            await SendHeartbeatAsync();
        }, null, TimeSpan.FromMinutes(1), TimeSpan.FromMinutes(1));
    }
    
    private async Task SendHeartbeatAsync()
    {
        if (string.IsNullOrEmpty(_activationCode))
            return;
            
        var request = new
        {
            activation_code = _activationCode,
            machine_fingerprint = _machineFingerprint,
            status = "online"
        };
        
        try
        {
            var json = JsonSerializer.Serialize(request);
            var content = new StringContent(json, Encoding.UTF8, "application/json");
            await _httpClient.PostAsync($"{_baseUrl}/heartbeat/", content);
        }
        catch
        {
            // 静默失败，心跳不是关键功能
        }
    }
    
    private void SaveActivationCode()
    {
        try
        {
            using var key = Registry.CurrentUser.CreateSubKey(@"SOFTWARE\MyApplication");
            key.SetValue("ActivationCode", _activationCode);
        }
        catch
        {
            // 如果无法写入注册表，可以使用其他存储方式
        }
    }
    
    private void LoadActivationCode()
    {
        try
        {
            using var key = Registry.CurrentUser.OpenSubKey(@"SOFTWARE\MyApplication");
            _activationCode = key?.GetValue("ActivationCode") as string;
        }
        catch
        {
            // 忽略错误
        }
    }
    
    public void Dispose()
    {
        _heartbeatTimer?.Dispose();
        _httpClient?.Dispose();
    }
}

// 使用示例
public class Program
{
    public static async Task Main(string[] args)
    {
        var licenseClient = new LicenseClient("https://api.example.com/api/v1/licenses");
        
        // 尝试验证现有激活
        bool isValid = await licenseClient.VerifyAsync();
        
        if (!isValid)
        {
            Console.WriteLine("请输入许可证密钥:");
            string licenseKey = Console.ReadLine();
            
            var result = await licenseClient.ActivateAsync(licenseKey);
            
            if (result.Success)
            {
                Console.WriteLine("激活成功!");
                Console.WriteLine($"许可证过期时间: {result.LicenseInfo.ExpiresAt}");
            }
            else
            {
                Console.WriteLine($"激活失败: {result.Error}");
                return;
            }
        }
        
        Console.WriteLine("应用程序已启动，许可证有效");
        
        // 应用程序主逻辑
        await RunApplication();
        
        licenseClient.Dispose();
    }
    
    private static async Task RunApplication()
    {
        // 应用程序逻辑
        Console.WriteLine("应用程序运行中...");
        await Task.Delay(10000); // 模拟运行10秒
    }
}
```

## 最佳实践指南

### 1. 认证和安全

#### Token管理最佳实践
```javascript
class TokenManager {
    constructor() {
        this.accessToken = localStorage.getItem('access_token');
        this.refreshToken = localStorage.getItem('refresh_token');
        this.tokenExpiry = localStorage.getItem('token_expiry');
    }
    
    async ensureValidToken() {
        if (!this.accessToken) {
            throw new Error('未登录');
        }
        
        // 检查token是否即将过期（提前5分钟刷新）
        const now = new Date().getTime();
        const expiry = new Date(this.tokenExpiry).getTime();
        
        if (expiry - now < 5 * 60 * 1000) {
            await this.refreshAccessToken();
        }
        
        return this.accessToken;
    }
    
    async refreshAccessToken() {
        const response = await fetch('/api/v1/auth/token/refresh/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh: this.refreshToken })
        });
        
        if (response.ok) {
            const data = await response.json();
            this.accessToken = data.access;
            this.tokenExpiry = new Date(Date.now() + 3600000).toISOString(); // 1小时后过期
            
            localStorage.setItem('access_token', this.accessToken);
            localStorage.setItem('token_expiry', this.tokenExpiry);
        } else {
            // 刷新失败，需要重新登录
            this.clearTokens();
            window.location.href = '/login';
        }
    }
    
    clearTokens() {
        this.accessToken = null;
        this.refreshToken = null;
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('token_expiry');
    }
}
```

#### 安全的API调用
```python
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import logging

class SecureAPIClient:
    def __init__(self, base_url, verify_ssl=True):
        self.base_url = base_url
        self.session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # SSL验证
        self.session.verify = verify_ssl
        
        # 设置超时
        self.timeout = 30
        
    def make_request(self, method, endpoint, **kwargs):
        url = f"{self.base_url}{endpoint}"
        
        # 添加认证头
        if hasattr(self, 'access_token'):
            kwargs.setdefault('headers', {})['Authorization'] = f'Bearer {self.access_token}'
        
        # 设置默认超时
        kwargs.setdefault('timeout', self.timeout)
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"API请求失败: {e}")
            raise
```

### 2. 错误处理和重试

#### 统一错误处理
```typescript
interface APIError {
  code: string;
  message: string;
  details?: any;
}

class APIException extends Error {
  public code: string;
  public details?: any;
  
  constructor(error: APIError) {
    super(error.message);
    this.code = error.code;
    this.details = error.details;
  }
}

class APIClient {
  async callAPI(endpoint: string, options: RequestInit = {}): Promise<any> {
    const maxRetries = 3;
    let attempt = 0;
    
    while (attempt < maxRetries) {
      try {
        const response = await fetch(`${this.baseURL}${endpoint}`, {
          ...options,
          headers: {
            'Content-Type': 'application/json',
            ...options.headers
          }
        });
        
        const data = await response.json();
        
        if (!response.ok) {
          throw new APIException({
            code: data.code || 'UNKNOWN_ERROR',
            message: data.error || 'Unknown error occurred',
            details: data.details
          });
        }
        
        return data;
      } catch (error) {
        attempt++;
        
        if (error instanceof APIException) {
          // 业务错误不重试
          throw error;
        }
        
        if (attempt >= maxRetries) {
          throw new APIException({
            code: 'NETWORK_ERROR',
            message: 'Network request failed after retries'
          });
        }
        
        // 指数退避
        await this.delay(Math.pow(2, attempt) * 1000);
      }
    }
  }
  
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
```

### 3. 性能优化

#### 数据缓存策略
```javascript
class CacheManager {
    constructor(ttl = 5 * 60 * 1000) { // 默认5分钟缓存
        this.cache = new Map();
        this.ttl = ttl;
    }
    
    set(key, data) {
        this.cache.set(key, {
            data,
            timestamp: Date.now(),
            expires: Date.now() + this.ttl
        });
    }
    
    get(key) {
        const item = this.cache.get(key);
        
        if (!item) {
            return null;
        }
        
        if (Date.now() > item.expires) {
            this.cache.delete(key);
            return null;
        }
        
        return item.data;
    }
    
    clear() {
        this.cache.clear();
    }
}

class OptimizedAPIClient {
    constructor(baseURL) {
        this.baseURL = baseURL;
        this.cache = new CacheManager();
    }
    
    async getLicenses(params = {}, useCache = true) {
        const cacheKey = `licenses_${JSON.stringify(params)}`;
        
        if (useCache) {
            const cached = this.cache.get(cacheKey);
            if (cached) {
                return cached;
            }
        }
        
        const data = await this.apiCall('/admin/licenses/', { params });
        
        if (useCache) {
            this.cache.set(cacheKey, data);
        }
        
        return data;
    }
    
    // 批量操作
    async batchUpdateLicenseStatus(licenseIds, status, reason) {
        // 使用批量接口而不是循环调用单个接口
        return await this.apiCall('/admin/licenses/batch_update_status/', {
            method: 'POST',
            body: JSON.stringify({
                license_ids: licenseIds,
                status,
                reason
            })
        });
    }
}
```

### 4. 监控和日志

#### 客户端监控
```python
import logging
import time
from functools import wraps

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('license_client.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def monitor_api_call(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        endpoint = kwargs.get('endpoint', 'unknown')
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            
            logger.info(f"API调用成功: {endpoint}, 耗时: {duration:.2f}s")
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"API调用失败: {endpoint}, 错误: {e}, 耗时: {duration:.2f}s")
            raise
            
    return wrapper

class MonitoredAPIClient:
    @monitor_api_call
    def api_call(self, endpoint, **kwargs):
        # API调用逻辑
        pass
    
    def track_license_usage(self, license_key, feature_used):
        """跟踪许可证功能使用情况"""
        logger.info(f"功能使用: {feature_used}, 许可证: {license_key}")
        
        # 可以发送到分析服务
        self.send_usage_analytics(license_key, feature_used)
    
    def send_usage_analytics(self, license_key, feature):
        """发送使用分析数据（可选）"""
        try:
            # 发送到分析服务的逻辑
            pass
        except Exception as e:
            logger.warning(f"发送分析数据失败: {e}")
```

### 5. 部署和环境配置

#### 环境配置最佳实践
```python
# config.py
import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class APIConfig:
    base_url: str
    timeout: int = 30
    max_retries: int = 3
    verify_ssl: bool = True
    log_level: str = 'INFO'
    
    @classmethod
    def from_env(cls) -> 'APIConfig':
        return cls(
            base_url=os.getenv('LICENSE_API_URL', 'https://api.example.com/api/v1/licenses'),
            timeout=int(os.getenv('LICENSE_API_TIMEOUT', '30')),
            max_retries=int(os.getenv('LICENSE_API_MAX_RETRIES', '3')),
            verify_ssl=os.getenv('LICENSE_API_VERIFY_SSL', 'true').lower() == 'true',
            log_level=os.getenv('LICENSE_LOG_LEVEL', 'INFO')
        )

# 不同环境的配置
ENVIRONMENTS = {
    'development': APIConfig(
        base_url='http://localhost:8000/api/v1/licenses',
        verify_ssl=False,
        log_level='DEBUG'
    ),
    'staging': APIConfig(
        base_url='https://staging-api.example.com/api/v1/licenses',
        log_level='INFO'
    ),
    'production': APIConfig(
        base_url='https://api.example.com/api/v1/licenses',
        log_level='WARNING'
    )
}

def get_config() -> APIConfig:
    env = os.getenv('ENVIRONMENT', 'development')
    if env in ENVIRONMENTS:
        return ENVIRONMENTS[env]
    return APIConfig.from_env()
```

### 6. 测试策略

#### 单元测试示例
```python
import unittest
from unittest.mock import Mock, patch
from license_client import LicenseClient

class TestLicenseClient(unittest.TestCase):
    def setUp(self):
        self.client = LicenseClient('https://api.test.com/api/v1/licenses')
    
    @patch('requests.post')
    def test_successful_activation(self, mock_post):
        # 模拟成功响应
        mock_response = Mock()
        mock_response.json.return_value = {
            'success': True,
            'data': {
                'activation_code': 'ACT-TEST-123',
                'license_info': {
                    'expires_at': '2025-01-01T00:00:00Z'
                }
            }
        }
        mock_post.return_value = mock_response
        
        result = self.client.activate('TEST-LICENSE-KEY')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['data']['activation_code'], 'ACT-TEST-123')
    
    @patch('requests.post')
    def test_activation_with_expired_license(self, mock_post):
        # 模拟过期许可证响应
        mock_response = Mock()
        mock_response.json.return_value = {
            'success': False,
            'error': '许可证已过期',
            'code': 'LICENSE_EXPIRED'
        }
        mock_post.return_value = mock_response
        
        result = self.client.activate('EXPIRED-LICENSE-KEY')
        
        self.assertFalse(result['success'])
        self.assertEqual(result['code'], 'LICENSE_EXPIRED')

if __name__ == '__main__':
    unittest.main()
```

## 故障排除指南

### 常见问题解决方案

1. **Token过期处理**
   - 实现自动刷新机制
   - 提供用户友好的重新登录流程
   - 缓存用户操作，登录后恢复

2. **网络连接问题**
   - 实现重试机制
   - 提供离线模式
   - 显示网络状态

3. **许可证验证失败**
   - 检查系统时间
   - 验证许可证密钥格式
   - 确认许可证状态

4. **性能问题**
   - 使用分页加载大数据集
   - 实现数据缓存
   - 优化API调用频率

### 监控指标

```javascript
class PerformanceMonitor {
    constructor() {
        this.metrics = {
            apiCalls: 0,
            failures: 0,
            averageResponseTime: 0,
            cacheHitRate: 0
        };
    }
    
    recordAPICall(duration, success) {
        this.metrics.apiCalls++;
        if (!success) this.metrics.failures++;
        
        // 计算平均响应时间
        this.metrics.averageResponseTime = 
            (this.metrics.averageResponseTime * (this.metrics.apiCalls - 1) + duration) / 
            this.metrics.apiCalls;
    }
    
    getHealthScore() {
        const successRate = (this.metrics.apiCalls - this.metrics.failures) / this.metrics.apiCalls;
        const responseScore = this.metrics.averageResponseTime < 1000 ? 1 : 0.5;
        const cacheScore = this.metrics.cacheHitRate;
        
        return (successRate + responseScore + cacheScore) / 3 * 100;
    }
}
```

这份完整的API文档提供了从基础概念到高级集成的全面指导，帮助开发者高效地使用Licenses API构建robust的许可证管理解决方案。
