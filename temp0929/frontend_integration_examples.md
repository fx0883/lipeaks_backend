# 许可证解绑API前端集成示例

## 概述

本文档提供了许可证解绑API的完整前端集成示例，包括不同技术栈的实现方案和最佳实践。

## JavaScript/TypeScript 实现

### 1. 基础API客户端

```typescript
// types.ts
export interface UnbindRequest {
  activation_code: string;
  license_key: string;
  machine_fingerprint: string;
  hardware_info?: any;
  reason?: string;
}

export interface UnbindResponse {
  success: boolean;
  message: string;
  data: {
    license_id: number;
    machine_id: string;
    unbound_at: string;
    remaining_activations: number;
    max_activations: number;
    reason: string;
  };
}

export interface ApiError {
  success: false;
  error: string;
  code: string;
  similarity?: number;
}

// api-client.ts
export class LicenseApiClient {
  private baseUrl: string;
  private tenantId?: string;

  constructor(baseUrl: string, tenantId?: string) {
    this.baseUrl = baseUrl;
    this.tenantId = tenantId;
  }

  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };

    if (this.tenantId) {
      headers['X-Tenant-ID'] = this.tenantId;
    }

    return headers;
  }

  async unbindLicense(request: UnbindRequest): Promise<UnbindResponse> {
    const response = await fetch(`${this.baseUrl}/api/v1/licenses/unbind/`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(request),
    });

    const data = await response.json();

    if (!response.ok) {
      throw new ApiError(data.error, data.code, response.status, data.similarity);
    }

    return data;
  }
}

// 自定义错误类
export class ApiError extends Error {
  public readonly code: string;
  public readonly status: number;
  public readonly similarity?: number;

  constructor(message: string, code: string, status: number, similarity?: number) {
    super(message);
    this.code = code;
    this.status = status;
    this.similarity = similarity;
    this.name = 'ApiError';
  }
}
```

### 2. React Hook 实现

```typescript
// hooks/useLicenseUnbind.ts
import { useState, useCallback } from 'react';
import { LicenseApiClient, UnbindRequest, UnbindResponse, ApiError } from '../api-client';

interface UseUnbindLicenseState {
  loading: boolean;
  data: UnbindResponse | null;
  error: ApiError | null;
}

export function useUnbindLicense(apiClient: LicenseApiClient) {
  const [state, setState] = useState<UseUnbindLicenseState>({
    loading: false,
    data: null,
    error: null,
  });

  const unbind = useCallback(async (request: UnbindRequest) => {
    setState({ loading: true, data: null, error: null });

    try {
      const data = await apiClient.unbindLicense(request);
      setState({ loading: false, data, error: null });
      return data;
    } catch (error) {
      const apiError = error instanceof ApiError ? error : new ApiError(
        'Unknown error occurred',
        'UNKNOWN_ERROR',
        500
      );
      setState({ loading: false, data: null, error: apiError });
      throw apiError;
    }
  }, [apiClient]);

  const reset = useCallback(() => {
    setState({ loading: false, data: null, error: null });
  }, []);

  return {
    ...state,
    unbind,
    reset,
  };
}
```

### 3. React 组件示例

```tsx
// components/UnbindLicenseForm.tsx
import React, { useState } from 'react';
import { useUnbindLicense } from '../hooks/useLicenseUnbind';
import { LicenseApiClient } from '../api-client';

interface UnbindLicenseFormProps {
  apiClient: LicenseApiClient;
  onSuccess?: (data: any) => void;
  onError?: (error: any) => void;
}

export const UnbindLicenseForm: React.FC<UnbindLicenseFormProps> = ({
  apiClient,
  onSuccess,
  onError,
}) => {
  const [formData, setFormData] = useState({
    activationCode: '',
    licenseKey: '',
    machineFingerprint: '',
    reason: '',
  });

  const { loading, error, unbind } = useUnbindLicense(apiClient);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const result = await unbind({
        activation_code: formData.activationCode,
        license_key: formData.licenseKey,
        machine_fingerprint: formData.machineFingerprint,
        reason: formData.reason || undefined,
      });
      
      onSuccess?.(result);
    } catch (error) {
      onError?.(error);
    }
  };

  const getErrorMessage = (error: any): string => {
    const errorMessages: Record<string, string> = {
      'ACTIVATION_NOT_FOUND': '激活码不存在，请检查是否输入正确',
      'LICENSE_KEY_MISMATCH': '许可证密钥不匹配',
      'FINGERPRINT_MISMATCH': '设备验证失败，请确认在正确的设备上操作',
      'BINDING_NOT_ACTIVE': '设备已经解绑，无需重复操作',
      'SUSPICIOUS_ACTIVITY': '操作被安全系统拦截，请稍后重试',
      'RATE_LIMITED': '请求过于频繁，请稍后重试',
    };

    return errorMessages[error.code] || error.message || '未知错误';
  };

  return (
    <form onSubmit={handleSubmit} className="unbind-form">
      <div className="form-group">
        <label htmlFor="activationCode">激活码 *</label>
        <input
          type="text"
          id="activationCode"
          value={formData.activationCode}
          onChange={(e) => setFormData(prev => ({ ...prev, activationCode: e.target.value }))}
          placeholder="XXXX-XXXX-XXXX-XXXX"
          required
          disabled={loading}
        />
      </div>

      <div className="form-group">
        <label htmlFor="licenseKey">许可证密钥 *</label>
        <input
          type="text"
          id="licenseKey"
          value={formData.licenseKey}
          onChange={(e) => setFormData(prev => ({ ...prev, licenseKey: e.target.value }))}
          placeholder="XXXXX-XXXXX-XXXXX-XXXXX-XXXXX"
          required
          disabled={loading}
        />
      </div>

      <div className="form-group">
        <label htmlFor="machineFingerprint">机器指纹 *</label>
        <input
          type="text"
          id="machineFingerprint"
          value={formData.machineFingerprint}
          onChange={(e) => setFormData(prev => ({ ...prev, machineFingerprint: e.target.value }))}
          placeholder="64位哈希字符串"
          required
          disabled={loading}
        />
      </div>

      <div className="form-group">
        <label htmlFor="reason">解绑原因</label>
        <textarea
          id="reason"
          value={formData.reason}
          onChange={(e) => setFormData(prev => ({ ...prev, reason: e.target.value }))}
          placeholder="请简述解绑原因（可选）"
          maxLength={500}
          disabled={loading}
        />
      </div>

      {error && (
        <div className="error-message">
          {getErrorMessage(error)}
        </div>
      )}

      <button type="submit" disabled={loading} className="submit-btn">
        {loading ? '解绑中...' : '解绑许可证'}
      </button>
    </form>
  );
};
```

## Vue.js 实现

### 1. Composable Function

```typescript
// composables/useLicenseUnbind.ts
import { ref, reactive } from 'vue';
import type { UnbindRequest, UnbindResponse } from '../types';

export function useLicenseUnbind(baseUrl: string, tenantId?: string) {
  const loading = ref(false);
  const error = ref<string | null>(null);
  const data = ref<UnbindResponse | null>(null);

  const unbind = async (request: UnbindRequest): Promise<UnbindResponse> => {
    loading.value = true;
    error.value = null;
    data.value = null;

    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };

      if (tenantId) {
        headers['X-Tenant-ID'] = tenantId;
      }

      const response = await fetch(`${baseUrl}/api/v1/licenses/unbind/`, {
        method: 'POST',
        headers,
        body: JSON.stringify(request),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Unbind failed');
      }

      data.value = result;
      return result;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      error.value = errorMessage;
      throw err;
    } finally {
      loading.value = false;
    }
  };

  const reset = () => {
    loading.value = false;
    error.value = null;
    data.value = null;
  };

  return {
    loading: readonly(loading),
    error: readonly(error),
    data: readonly(data),
    unbind,
    reset,
  };
}
```

### 2. Vue 组件

```vue
<!-- components/UnbindLicenseForm.vue -->
<template>
  <form @submit.prevent="handleSubmit" class="unbind-form">
    <div class="form-group">
      <label for="activationCode">激活码 *</label>
      <input
        v-model="formData.activationCode"
        type="text"
        id="activationCode"
        placeholder="XXXX-XXXX-XXXX-XXXX"
        required
        :disabled="loading"
      />
    </div>

    <div class="form-group">
      <label for="licenseKey">许可证密钥 *</label>
      <input
        v-model="formData.licenseKey"
        type="text"
        id="licenseKey"
        placeholder="XXXXX-XXXXX-XXXXX-XXXXX-XXXXX"
        required
        :disabled="loading"
      />
    </div>

    <div class="form-group">
      <label for="machineFingerprint">机器指纹 *</label>
      <input
        v-model="formData.machineFingerprint"
        type="text"
        id="machineFingerprint"
        placeholder="64位哈希字符串"
        required
        :disabled="loading"
      />
    </div>

    <div class="form-group">
      <label for="reason">解绑原因</label>
      <textarea
        v-model="formData.reason"
        id="reason"
        placeholder="请简述解绑原因（可选）"
        maxlength="500"
        :disabled="loading"
      />
    </div>

    <div v-if="error" class="error-message">
      {{ error }}
    </div>

    <button type="submit" :disabled="loading" class="submit-btn">
      {{ loading ? '解绑中...' : '解绑许可证' }}
    </button>
  </form>
</template>

<script setup lang="ts">
import { reactive } from 'vue';
import { useLicenseUnbind } from '../composables/useLicenseUnbind';

interface Props {
  baseUrl: string;
  tenantId?: string;
}

interface Emits {
  (e: 'success', data: any): void;
  (e: 'error', error: any): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const formData = reactive({
  activationCode: '',
  licenseKey: '',
  machineFingerprint: '',
  reason: '',
});

const { loading, error, unbind } = useLicenseUnbind(props.baseUrl, props.tenantId);

const handleSubmit = async () => {
  try {
    const result = await unbind({
      activation_code: formData.activationCode,
      license_key: formData.licenseKey,
      machine_fingerprint: formData.machineFingerprint,
      reason: formData.reason || undefined,
    });
    
    emit('success', result);
    
    // 重置表单
    Object.assign(formData, {
      activationCode: '',
      licenseKey: '',
      machineFingerprint: '',
      reason: '',
    });
  } catch (error) {
    emit('error', error);
  }
};
</script>
```

## jQuery/原生JavaScript 实现

```javascript
// license-unbind.js
class LicenseUnbindManager {
  constructor(baseUrl, tenantId) {
    this.baseUrl = baseUrl;
    this.tenantId = tenantId;
  }

  async unbindLicense(params) {
    const { activationCode, licenseKey, machineFingerprint, reason, hardwareInfo } = params;

    const requestData = {
      activation_code: activationCode,
      license_key: licenseKey,
      machine_fingerprint: machineFingerprint,
    };

    if (reason) {
      requestData.reason = reason;
    }

    if (hardwareInfo) {
      requestData.hardware_info = hardwareInfo;
    }

    try {
      const response = await fetch(`${this.baseUrl}/api/v1/licenses/unbind/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(this.tenantId && { 'X-Tenant-ID': this.tenantId }),
        },
        body: JSON.stringify(requestData),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(`${data.error} (${data.code})`);
      }

      return data;
    } catch (error) {
      console.error('License unbind failed:', error);
      throw error;
    }
  }

  // 重试机制
  async unbindWithRetry(params, maxRetries = 3) {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await this.unbindLicense(params);
      } catch (error) {
        if (error.message.includes('RATE_LIMITED') && attempt < maxRetries) {
          const delay = Math.pow(2, attempt) * 1000;
          await new Promise(resolve => setTimeout(resolve, delay));
          continue;
        }
        throw error;
      }
    }
  }
}

// jQuery 表单处理示例
$(document).ready(function() {
  const unbindManager = new LicenseUnbindManager('https://api.example.com', '123');

  $('#unbind-form').on('submit', async function(e) {
    e.preventDefault();

    const $form = $(this);
    const $submitBtn = $form.find('button[type="submit"]');
    const $errorDiv = $form.find('.error-message');

    // 禁用提交按钮
    $submitBtn.prop('disabled', true).text('解绑中...');
    $errorDiv.hide();

    try {
      const result = await unbindManager.unbindWithRetry({
        activationCode: $('#activation-code').val(),
        licenseKey: $('#license-key').val(),
        machineFingerprint: $('#machine-fingerprint').val(),
        reason: $('#reason').val(),
      });

      // 成功处理
      alert('解绑成功！');
      $form[0].reset();
      
      console.log('Unbind result:', result);
    } catch (error) {
      // 错误处理
      $errorDiv.text(getErrorMessage(error.message)).show();
    } finally {
      // 恢复提交按钮
      $submitBtn.prop('disabled', false).text('解绑许可证');
    }
  });

  function getErrorMessage(errorText) {
    const errorMap = {
      'ACTIVATION_NOT_FOUND': '激活码不存在',
      'LICENSE_KEY_MISMATCH': '许可证密钥不匹配',
      'FINGERPRINT_MISMATCH': '设备验证失败',
      'BINDING_NOT_ACTIVE': '设备已经解绑',
      'SUSPICIOUS_ACTIVITY': '操作被拦截，请稍后重试',
      'RATE_LIMITED': '请求过于频繁，请稍后重试',
    };

    for (const [code, message] of Object.entries(errorMap)) {
      if (errorText.includes(code)) {
        return message;
      }
    }

    return '解绑失败，请重试';
  }
});
```

## 机器指纹获取示例

```javascript
// fingerprint-generator.js
class MachineFingerprint {
  static async generate() {
    const components = [];

    // 收集各种浏览器指纹信息
    components.push(navigator.userAgent);
    components.push(navigator.language);
    components.push(screen.width + 'x' + screen.height);
    components.push(screen.colorDepth);
    components.push(new Date().getTimezoneOffset());
    components.push(navigator.hardwareConcurrency || 'unknown');
    components.push(navigator.deviceMemory || 'unknown');

    // WebGL指纹
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    if (gl) {
      const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
      if (debugInfo) {
        components.push(gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL));
        components.push(gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL));
      }
    }

    // Canvas指纹
    const ctx = canvas.getContext('2d');
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillText('Machine Fingerprint', 2, 2);
    components.push(canvas.toDataURL());

    // 字体检测
    const fonts = ['Arial', 'Helvetica', 'Times New Roman', 'Courier New'];
    for (const font of fonts) {
      components.push(this.detectFont(font));
    }

    // 生成哈希
    const fingerprint = await this.hash(components.join('|'));
    return fingerprint;
  }

  static detectFont(fontName) {
    const testString = 'mmmmmmmmmmlli';
    const testSize = '72px';
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    ctx.font = testSize + ' monospace';
    const baselineWidth = ctx.measureText(testString).width;

    ctx.font = testSize + ' ' + fontName + ', monospace';
    const testWidth = ctx.measureText(testString).width;

    return testWidth !== baselineWidth;
  }

  static async hash(text) {
    const encoder = new TextEncoder();
    const data = encoder.encode(text);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }
}

// 使用示例
async function generateMachineFingerprint() {
  try {
    const fingerprint = await MachineFingerprint.generate();
    console.log('Machine fingerprint:', fingerprint);
    return fingerprint;
  } catch (error) {
    console.error('Failed to generate fingerprint:', error);
    return null;
  }
}
```

## 完整集成示例

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>许可证解绑</title>
    <style>
        .form-group {
            margin-bottom: 1rem;
        }
        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: bold;
        }
        .form-group input,
        .form-group textarea {
            width: 100%;
            padding: 0.5rem;
            border: 1px solid #ddd;
            border-radius: 4px;
        }
        .error-message {
            color: #d32f2f;
            background-color: #ffebee;
            padding: 0.5rem;
            border-radius: 4px;
            margin-bottom: 1rem;
        }
        .success-message {
            color: #2e7d32;
            background-color: #e8f5e8;
            padding: 0.5rem;
            border-radius: 4px;
            margin-bottom: 1rem;
        }
        .submit-btn {
            background-color: #1976d2;
            color: white;
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        .submit-btn:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>许可证解绑</h1>
        
        <form id="unbind-form">
            <div class="form-group">
                <label for="activation-code">激活码 *</label>
                <input type="text" id="activation-code" placeholder="XXXX-XXXX-XXXX-XXXX" required>
            </div>

            <div class="form-group">
                <label for="license-key">许可证密钥 *</label>
                <input type="text" id="license-key" placeholder="XXXXX-XXXXX-XXXXX-XXXXX-XXXXX" required>
            </div>

            <div class="form-group">
                <label for="machine-fingerprint">机器指纹 *</label>
                <input type="text" id="machine-fingerprint" readonly>
                <button type="button" id="generate-fingerprint">生成指纹</button>
            </div>

            <div class="form-group">
                <label for="reason">解绑原因</label>
                <textarea id="reason" placeholder="请简述解绑原因（可选）" maxlength="500"></textarea>
            </div>

            <div id="message-area"></div>

            <button type="submit" class="submit-btn">解绑许可证</button>
        </form>
    </div>

    <script src="fingerprint-generator.js"></script>
    <script src="license-unbind.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            const unbindManager = new LicenseUnbindManager('https://api.example.com', '123');
            const form = document.getElementById('unbind-form');
            const messageArea = document.getElementById('message-area');

            // 自动生成机器指纹
            document.getElementById('generate-fingerprint').addEventListener('click', async function() {
                const fingerprint = await generateMachineFingerprint();
                if (fingerprint) {
                    document.getElementById('machine-fingerprint').value = fingerprint;
                }
            });

            // 页面加载时自动生成指纹
            generateMachineFingerprint().then(fingerprint => {
                if (fingerprint) {
                    document.getElementById('machine-fingerprint').value = fingerprint;
                }
            });

            // 表单提交处理
            form.addEventListener('submit', async function(e) {
                e.preventDefault();

                const submitBtn = form.querySelector('button[type="submit"]');
                submitBtn.disabled = true;
                submitBtn.textContent = '解绑中...';
                messageArea.innerHTML = '';

                try {
                    const result = await unbindManager.unbindWithRetry({
                        activationCode: document.getElementById('activation-code').value,
                        licenseKey: document.getElementById('license-key').value,
                        machineFingerprint: document.getElementById('machine-fingerprint').value,
                        reason: document.getElementById('reason').value,
                    });

                    messageArea.innerHTML = `
                        <div class="success-message">
                            解绑成功！剩余激活数：${result.data.remaining_activations}/${result.data.max_activations}
                        </div>
                    `;
                    form.reset();
                    
                    // 重新生成指纹以备下次使用
                    const newFingerprint = await generateMachineFingerprint();
                    if (newFingerprint) {
                        document.getElementById('machine-fingerprint').value = newFingerprint;
                    }
                } catch (error) {
                    messageArea.innerHTML = `
                        <div class="error-message">
                            ${getErrorMessage(error.message)}
                        </div>
                    `;
                } finally {
                    submitBtn.disabled = false;
                    submitBtn.textContent = '解绑许可证';
                }
            });
        });

        function getErrorMessage(errorText) {
            const errorMap = {
                'ACTIVATION_NOT_FOUND': '激活码不存在，请检查是否输入正确',
                'LICENSE_KEY_MISMATCH': '许可证密钥与激活记录不匹配',
                'FINGERPRINT_MISMATCH': '设备验证失败，请确认在正确的设备上操作',
                'BINDING_NOT_ACTIVE': '设备已经解绑，无需重复操作',
                'SUSPICIOUS_ACTIVITY': '操作被安全系统拦截，请稍后重试',
                'RATE_LIMITED': '请求过于频繁，请稍后重试',
            };

            for (const [code, message] of Object.entries(errorMap)) {
                if (errorText.includes(code)) {
                    return message;
                }
            }

            return errorText || '解绑失败，请重试';
        }
    </script>
</body>
</html>
```

## 测试建议

### 1. 单元测试

```typescript
// __tests__/license-unbind.test.ts
import { LicenseApiClient, ApiError } from '../api-client';

describe('LicenseApiClient', () => {
  let client: LicenseApiClient;

  beforeEach(() => {
    client = new LicenseApiClient('https://api.test.com', '123');
  });

  test('should unbind license successfully', async () => {
    // Mock successful response
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({
        success: true,
        message: 'License unbound successfully',
        data: {
          license_id: 123,
          machine_id: 'MACHINE-TEST',
          unbound_at: '2024-01-15T10:30:00Z',
          remaining_activations: 2,
          max_activations: 5,
          reason: '测试解绑'
        }
      })
    });

    const result = await client.unbindLicense({
      activation_code: 'TEST-CODE',
      license_key: 'TEST-KEY',
      machine_fingerprint: 'a'.repeat(64),
      reason: '测试解绑'
    });

    expect(result.success).toBe(true);
    expect(result.data.license_id).toBe(123);
  });

  test('should handle error responses', async () => {
    // Mock error response
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 400,
      json: () => Promise.resolve({
        success: false,
        error: 'Activation record not found',
        code: 'ACTIVATION_NOT_FOUND'
      })
    });

    await expect(client.unbindLicense({
      activation_code: 'INVALID-CODE',
      license_key: 'TEST-KEY',
      machine_fingerprint: 'a'.repeat(64)
    })).rejects.toThrow(ApiError);
  });
});
```

### 2. 集成测试

```javascript
// integration-test.js
async function testUnbindIntegration() {
  const testCases = [
    {
      name: '正常解绑',
      data: {
        activation_code: 'VALID-CODE',
        license_key: 'VALID-KEY',
        machine_fingerprint: 'a'.repeat(64),
        reason: '集成测试'
      },
      expectSuccess: true
    },
    {
      name: '无效激活码',
      data: {
        activation_code: 'INVALID-CODE',
        license_key: 'VALID-KEY',
        machine_fingerprint: 'a'.repeat(64)
      },
      expectSuccess: false,
      expectedError: 'ACTIVATION_NOT_FOUND'
    },
    // 更多测试用例...
  ];

  for (const testCase of testCases) {
    console.log(`运行测试: ${testCase.name}`);
    
    try {
      const response = await fetch('/api/v1/licenses/unbind/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(testCase.data)
      });

      const result = await response.json();

      if (testCase.expectSuccess) {
        console.assert(result.success === true, `${testCase.name} 应该成功`);
      } else {
        console.assert(result.success === false, `${testCase.name} 应该失败`);
        if (testCase.expectedError) {
          console.assert(result.code === testCase.expectedError, 
            `${testCase.name} 错误代码不匹配`);
        }
      }
      
      console.log(`✓ ${testCase.name} 通过`);
    } catch (error) {
      console.error(`✗ ${testCase.name} 失败:`, error);
    }
  }
}

// 运行集成测试
testUnbindIntegration();
```

## 性能优化建议

1. **请求缓存**: 对于相同的指纹生成请求可以进行缓存
2. **错误重试**: 实现指数退避的重试机制
3. **用户体验**: 提供清晰的加载状态和错误提示
4. **批量操作**: 如需要批量解绑，可以实现队列机制
5. **本地存储**: 合理使用localStorage保存用户输入

这些示例应该能帮助前端开发人员快速集成许可证解绑功能。
