# 许可证批量操作 API

本文档详细说明管理员端许可证批量操作API接口。

---

## API概述

### 基本信息

```
POST /api/v1/licenses/admin/licenses/batch_operation/
```

**功能**：管理员对多个许可证执行批量操作（撤销、延期、暂停、激活等）

**权限要求**：
- 需要JWT认证
- 必须是管理员身份（超级管理员或租户管理员）
- 超级管理员：可操作所有许可证
- 租户管理员：只能操作自己租户的许可证

**内容类型**：`application/json`

---

## 请求说明

### 请求头

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

### 请求参数

#### 必填字段

| 字段 | 类型 | 说明 | 验证规则 |
|------|------|------|---------|
| license_ids | array[integer] | 许可证ID列表 | 最少1个，最多100个，ID必须存在 |
| operation | string | 操作类型 | 可选值：`revoke`, `suspend`, `activate`, `extend`, `delete` |

#### 可选字段

| 字段 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| parameters | object | 操作参数（JSON对象） | `{}` |
| reason | string | 操作原因 | 空字符串 |

### 请求体示例

#### 示例1：批量撤销许可证

```json
{
  "license_ids": [123, 124, 125],
  "operation": "revoke",
  "reason": "违规使用，批量撤销"
}
```

#### 示例2：批量延长许可证（需要parameters）

```json
{
  "license_ids": [126, 127, 128],
  "operation": "extend",
  "parameters": {
    "days": 30
  },
  "reason": "活动奖励，延长30天"
}
```

#### 示例3：批量暂停许可证

```json
{
  "license_ids": [129, 130],
  "operation": "suspend",
  "reason": "临时暂停，等待审核"
}
```

#### 示例4：批量激活许可证

```json
{
  "license_ids": [131, 132, 133],
  "operation": "activate",
  "reason": "审核通过，批量激活"
}
```

#### 示例5：批量删除许可证

```json
{
  "license_ids": [134, 135],
  "operation": "delete",
  "reason": "清理无效许可证"
}
```

---

## 操作类型详解

### 1. revoke - 撤销许可证

**用途**：永久撤销许可证，用户无法继续使用

**参数**：无需特殊参数

**效果**：
- 许可证状态变为 `revoked`
- 相关的机器绑定失效
- 用户无法再激活或使用该许可证

**请求示例**：
```json
{
  "license_ids": [123, 124],
  "operation": "revoke",
  "reason": "许可证违规使用"
}
```

---

### 2. extend - 延长有效期

**用途**：延长许可证的有效期

**必需参数**：
- `parameters.days` (integer) - 延长的天数

**效果**：
- 许可证的 `expires_at` 时间增加指定天数
- 不影响其他属性

**请求示例**：
```json
{
  "license_ids": [125, 126],
  "operation": "extend",
  "parameters": {
    "days": 30
  },
  "reason": "客户续费，延长30天"
}
```

**参数详解**：

| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| parameters.days | integer | 是 | 要延长的天数，必须大于0 | 30 |

---

### 3. suspend - 暂停许可证

**用途**：临时暂停许可证，可恢复

**参数**：无需特殊参数

**前置条件**：许可证状态必须为 `generated` 或 `activated`

**效果**：
- 许可证状态变为 `suspended`
- 用户暂时无法使用，但可以恢复
- 记录安全审计日志

**请求示例**：
```json
{
  "license_ids": [127],
  "operation": "suspend",
  "reason": "账户异常，临时暂停"
}
```

**状态转换**：
```
generated → suspended ✅
activated → suspended ✅
其他状态 → 报错 ❌
```

---

### 4. activate - 激活许可证

**用途**：激活已暂停的许可证

**参数**：无需特殊参数

**前置条件**：许可证状态必须为 `suspended`

**效果**：
- 许可证状态从 `suspended` 变为 `activated`
- 用户可以正常使用许可证
- 记录安全审计日志

**请求示例**：
```json
{
  "license_ids": [128, 129],
  "operation": "activate",
  "reason": "问题解决，恢复许可证"
}
```

**状态转换**：
```
suspended → activated ✅
其他状态 → 报错 ❌
```

---

### 5. delete - 删除许可证

**用途**：软删除许可证（数据库保留，但不可见）

**参数**：无需特殊参数

**安全处理**：
- 如果许可证未撤销，会先自动撤销
- 然后执行软删除（设置 `is_deleted=True`）
- 记录高级别安全审计日志

**效果**：
- 许可证被软删除，从列表中消失
- 相关的激活和绑定失效
- 无法恢复（除非数据库操作）

**请求示例**：
```json
{
  "license_ids": [130, 131],
  "operation": "delete",
  "reason": "清理无效许可证"
}
```

**处理流程**：
```
1. 检查许可证状态
2. 如果未撤销 → 先调用revoke操作
3. 设置 is_deleted = True
4. 记录删除审计日志
```

⚠️ **警告**：删除操作不可逆，请谨慎使用！

---

## 响应说明

### 成功响应

**状态码**：`200 OK`

**响应体**：

```json
{
  "success": true,
  "message": "批量操作完成，成功: 3/3",
  "results": [
    {
      "license_id": 123,
      "success": true,
      "message": "撤销成功"
    },
    {
      "license_id": 124,
      "success": true,
      "message": "撤销成功"
    },
    {
      "license_id": 125,
      "success": true,
      "message": "撤销成功"
    }
  ]
}
```

### 部分成功响应

如果批量操作中有些成功有些失败：

```json
{
  "success": true,
  "message": "批量操作完成，成功: 2/3",
  "results": [
    {
      "license_id": 123,
      "success": true,
      "message": "撤销成功"
    },
    {
      "license_id": 124,
      "success": false,
      "error": "许可证状态不允许撤销"
    },
    {
      "license_id": 125,
      "success": true,
      "message": "撤销成功"
    }
  ]
}
```

### 响应字段说明

#### 顶层字段

| 字段 | 类型 | 说明 |
|------|------|------|
| success | boolean | 批量操作是否完整执行（即使有失败项也为true） |
| message | string | 操作结果摘要 |
| results | array | 每个许可证的操作结果 |

#### results数组元素

| 字段 | 类型 | 说明 |
|------|------|------|
| license_id | integer | 许可证ID |
| success | boolean | 该许可证操作是否成功 |
| message | string | 成功消息（success为true时） |
| error | string | 错误消息（success为false时） |

---

## 错误响应

### 400 参数验证错误

#### 场景1：缺少必填字段

```json
{
  "success": false,
  "errors": {
    "license_ids": ["该字段为必填项。"],
    "operation": ["该字段为必填项。"]
  }
}
```

#### 场景2：许可证ID不存在

```json
{
  "success": false,
  "errors": {
    "license_ids": ["以下许可证ID不存在: [999, 1000]"]
  }
}
```

#### 场景3：操作类型无效

```json
{
  "success": false,
  "errors": {
    "operation": ["\"invalid_op\"不是有效选择。"]
  }
}
```

#### 场景4：extend操作缺少days参数

```json
{
  "success": false,
  "error": "延长操作需要指定天数参数"
}
```

### 401 未认证

```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 权限不足

```json
{
  "detail": "You do not have permission to perform this action."
}
```

**原因**：
- 不是管理员用户
- 租户管理员尝试操作其他租户的许可证

### 500 服务器内部错误

```json
{
  "success": false,
  "error": "批量操作失败: <error_message>"
}
```

---

## 前端实现示例

### Vue 3 完整示例

```vue
<template>
  <div class="batch-operation-panel">
    <!-- 操作面板 -->
    <el-card class="operation-card">
      <template #header>
        <span>批量操作许可证</span>
      </template>
      
      <!-- 已选择的许可证 -->
      <div class="selected-licenses">
        <el-alert
          v-if="selectedLicenses.length === 0"
          type="info"
          :closable="false"
          show-icon
        >
          请先在许可证列表中选择要操作的许可证
        </el-alert>
        
        <div v-else class="selection-info">
          <el-tag size="large" type="primary">
            已选择 {{ selectedLicenses.length }} 个许可证
          </el-tag>
          <el-button size="small" type="text" @click="clearSelection">
            清空选择
          </el-button>
        </div>
        
        <!-- 选中的许可证列表 -->
        <div v-if="selectedLicenses.length > 0" class="selected-list">
          <el-tag
            v-for="license in selectedLicenses"
            :key="license.id"
            closable
            @close="removeFromSelection(license.id)"
            style="margin: 2px;"
          >
            {{ license.customer_name || 'N/A' }} ({{ license.license_key?.slice(-8) || 'N/A' }})
          </el-tag>
        </div>
      </div>
      
      <!-- 操作选择 -->
      <el-form :model="formData" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="操作类型" prop="operation">
          <el-select
            v-model="formData.operation"
            placeholder="选择操作"
            @change="onOperationChange"
            style="width: 200px;"
          >
            <el-option label="撤销许可证" value="revoke" />
            <el-option label="延长有效期" value="extend" />
            <el-option label="暂停许可证" value="suspend" />
            <el-option label="激活许可证" value="activate" />
            <el-option label="删除许可证" value="delete" />
          </el-select>
        </el-form-item>
        
        <!-- 延长天数（仅extend操作显示） -->
        <el-form-item
          v-if="formData.operation === 'extend'"
          label="延长天数"
          prop="days"
        >
          <el-input-number
            v-model="formData.days"
            :min="1"
            :max="365"
            placeholder="输入延长天数"
          />
          <span style="margin-left: 8px; color: #909399;">天</span>
        </el-form-item>
        
        <!-- 操作原因 -->
        <el-form-item label="操作原因" prop="reason">
          <el-input
            v-model="formData.reason"
            type="textarea"
            :rows="3"
            placeholder="请填写操作原因（可选）"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>
        
        <!-- 确认框 -->
        <el-form-item v-if="formData.operation">
          <el-alert
            :title="getOperationWarning()"
            :type="getOperationAlertType()"
            :closable="false"
            show-icon
          />
        </el-form-item>
        
        <!-- 执行按钮 -->
        <el-form-item>
          <el-button
            type="primary"
            @click="executeOperation"
            :loading="executing"
            :disabled="!canExecute"
          >
            {{ executing ? '执行中...' : `执行${getOperationName()}操作` }}
          </el-button>
          <el-button @click="resetForm">
            重置
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <!-- 执行结果对话框 -->
    <el-dialog
      v-model="resultDialogVisible"
      title="批量操作结果"
      width="700px"
    >
      <div class="result-summary">
        <el-result
          :icon="overallSuccess ? 'success' : 'warning'"
          :title="resultSummary.title"
          :sub-title="resultSummary.subtitle"
        />
      </div>
      
      <!-- 详细结果 -->
      <el-table :data="operationResults" border>
        <el-table-column prop="license_id" label="许可证ID" width="100" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.success ? 'success' : 'danger'">
              {{ row.success ? '成功' : '失败' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="结果信息">
          <template #default="{ row }">
            <span :class="row.success ? 'success-text' : 'error-text'">
              {{ row.success ? row.message : row.error }}
            </span>
          </template>
        </el-table-column>
      </el-table>
      
      <template #footer>
        <el-button type="primary" @click="resultDialogVisible = false">
          关闭
        </el-button>
        <el-button @click="refreshLicenseList">
          刷新列表
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue';
import { ElMessage, ElMessageBox } from 'element-plus';
import axios from 'axios';

const props = defineProps({
  selectedLicenses: {
    type: Array,
    default: () => []
  }
});

const emit = defineEmits(['refresh', 'clearSelection']);

// 数据
const executing = ref(false);
const resultDialogVisible = ref(false);
const operationResults = ref([]);
const formRef = ref(null);

// 表单数据
const formData = ref({
  operation: '',
  days: null,
  reason: ''
});

// 验证规则
const rules = {
  operation: [
    { required: true, message: '请选择操作类型', trigger: 'change' }
  ],
  days: [
    {
      validator: (rule, value, callback) => {
        if (formData.value.operation === 'extend' && (!value || value <= 0)) {
          callback(new Error('延长天数必须大于0'));
        } else {
          callback();
        }
      },
      trigger: 'blur'
    }
  ]
};

// 计算属性
const canExecute = computed(() => {
  return props.selectedLicenses.length > 0 && 
         formData.value.operation &&
         (formData.value.operation !== 'extend' || formData.value.days > 0);
});

const overallSuccess = computed(() => {
  return operationResults.value.length > 0 &&
         operationResults.value.every(r => r.success);
});

const resultSummary = computed(() => {
  const total = operationResults.value.length;
  const successful = operationResults.value.filter(r => r.success).length;
  const failed = total - successful;
  
  if (successful === total) {
    return {
      title: '操作完成',
      subtitle: `所有 ${total} 个许可证操作成功`
    };
  } else if (successful > 0) {
    return {
      title: '部分成功',
      subtitle: `${successful} 个成功，${failed} 个失败`
    };
  } else {
    return {
      title: '操作失败',
      subtitle: `所有 ${total} 个许可证操作失败`
    };
  }
});

// 方法
const onOperationChange = (operation) => {
  if (operation === 'extend') {
    formData.value.days = 30; // 默认30天
  } else {
    formData.value.days = null;
  }
};

const getOperationName = () => {
  const map = {
    revoke: '撤销',
    extend: '延期',
    suspend: '暂停',
    activate: '激活',
    delete: '删除'
  };
  return map[formData.value.operation] || '';
};

const getOperationWarning = () => {
  const operation = formData.value.operation;
  const count = props.selectedLicenses.length;
  
  const warnings = {
    revoke: `⚠️ 即将撤销 ${count} 个许可证，此操作不可逆！`,
    extend: `📅 即将为 ${count} 个许可证延长 ${formData.value.days || 0} 天`,
    suspend: `⏸️ 即将暂停 ${count} 个许可证，用户将无法使用`,
    activate: `▶️ 即将激活 ${count} 个许可证`,
    delete: `🗑️ 即将删除 ${count} 个许可证，此操作不可逆！`
  };
  
  return warnings[operation] || `即将对 ${count} 个许可证执行${getOperationName()}操作`;
};

const getOperationAlertType = () => {
  const dangerousOps = ['revoke', 'delete'];
  return dangerousOps.includes(formData.value.operation) ? 'error' : 'warning';
};

// 执行批量操作
const executeOperation = async () => {
  try {
    await formRef.value.validate();
    
    // 二次确认
    await ElMessageBox.confirm(
      getOperationWarning(),
      '确认执行批量操作',
      {
        confirmButtonText: '确认执行',
        cancelButtonText: '取消',
        type: formData.value.operation === 'revoke' ? 'error' : 'warning'
      }
    );
    
    executing.value = true;
    
    // 准备请求数据
    const requestData = {
      license_ids: props.selectedLicenses.map(l => l.id),
      operation: formData.value.operation,
      reason: formData.value.reason || ''
    };
    
    // 添加操作参数
    if (formData.value.operation === 'extend' && formData.value.days) {
      requestData.parameters = {
        days: formData.value.days
      };
    }
    
    // 发送请求
    const response = await axios.post(
      '/api/v1/licenses/admin/licenses/batch_operation/',
      requestData
    );
    
    if (response.data.success) {
      operationResults.value = response.data.results;
      resultDialogVisible.value = true;
      
      const successful = response.data.results.filter(r => r.success).length;
      const total = response.data.results.length;
      
      if (successful === total) {
        ElMessage.success(`批量${getOperationName()}操作完成，全部成功！`);
      } else {
        ElMessage.warning(`批量操作完成，成功 ${successful}/${total}`);
      }
      
      // 清空选择
      emit('clearSelection');
      
    } else {
      ElMessage.error(response.data.error || '批量操作失败');
    }
    
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量操作失败:', error);
      
      if (error.response) {
        const { status, data } = error.response;
        
        if (status === 400 && data.errors) {
          // 显示验证错误
          const messages = [];
          for (const [field, errors] of Object.entries(data.errors)) {
            messages.push(`${field}: ${errors.join(', ')}`);
          }
          ElMessage.error(messages.join('\n'));
        } else if (status === 403) {
          ElMessage.error('权限不足，无法执行此操作');
        } else {
          ElMessage.error(data.error || '操作失败');
        }
      } else {
        ElMessage.error('网络连接失败');
      }
    }
  } finally {
    executing.value = false;
  }
};

// 重置表单
const resetForm = () => {
  formRef.value.resetFields();
  formData.value = {
    operation: '',
    days: null,
    reason: ''
  };
};

// 刷新许可证列表
const refreshLicenseList = () => {
  resultDialogVisible.value = false;
  emit('refresh');
};

// 清空选择
const clearSelection = () => {
  emit('clearSelection');
};

// 从选择中移除
const removeFromSelection = (licenseId) => {
  // 通知父组件移除指定ID
  const remaining = props.selectedLicenses.filter(l => l.id !== licenseId);
  emit('updateSelection', remaining);
};
</script>

<style scoped>
.batch-operation-panel {
  margin-bottom: 20px;
}

.operation-card {
  border: 1px solid #E4E7ED;
}

.selected-licenses {
  margin-bottom: 20px;
}

.selection-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.selected-list {
  max-height: 100px;
  overflow-y: auto;
  padding: 10px;
  background-color: #F5F7FA;
  border-radius: 4px;
}

.result-summary {
  text-align: center;
  margin-bottom: 20px;
}

.success-text {
  color: #67C23A;
}

.error-text {
  color: #F56C6C;
}
</style>
```

---

## JavaScript/Axios Service封装

### 批量操作API封装

```javascript
// src/api/services/licenseBatchService.js
import axios from 'axios';

class LicenseBatchService {
  baseURL = '/api/v1/licenses/admin/licenses';
  
  /**
   * 批量操作许可证
   * @param {Array} licenseIds - 许可证ID数组
   * @param {string} operation - 操作类型：revoke, extend, suspend, activate
   * @param {Object} parameters - 操作参数（如延长天数）
   * @param {string} reason - 操作原因
   * @returns {Promise}
   */
  async batchOperation(licenseIds, operation, parameters = {}, reason = '') {
    const requestData = {
      license_ids: licenseIds,
      operation: operation,
      reason: reason
    };
    
    // 如果有参数，添加到请求
    if (Object.keys(parameters).length > 0) {
      requestData.parameters = parameters;
    }
    
    const response = await axios.post(
      `${this.baseURL}/batch_operation/`,
      requestData
    );
    
    return response.data;
  }
  
  /**
   * 批量撤销许可证
   * @param {Array} licenseIds - 许可证ID数组
   * @param {string} reason - 撤销原因
   * @returns {Promise}
   */
  async batchRevoke(licenseIds, reason) {
    return this.batchOperation(licenseIds, 'revoke', {}, reason);
  }
  
  /**
   * 批量延长许可证
   * @param {Array} licenseIds - 许可证ID数组
   * @param {number} days - 延长天数
   * @param {string} reason - 延长原因
   * @returns {Promise}
   */
  async batchExtend(licenseIds, days, reason) {
    return this.batchOperation(licenseIds, 'extend', { days }, reason);
  }
  
  /**
   * 批量暂停许可证
   * @param {Array} licenseIds - 许可证ID数组
   * @param {string} reason - 暂停原因
   * @returns {Promise}
   */
  async batchSuspend(licenseIds, reason) {
    return this.batchOperation(licenseIds, 'suspend', {}, reason);
  }
  
  /**
   * 批量激活许可证
   * @param {Array} licenseIds - 许可证ID数组
   * @param {string} reason - 激活原因
   * @returns {Promise}
   */
  async batchActivate(licenseIds, reason) {
    return this.batchOperation(licenseIds, 'activate', {}, reason);
  }
  
  /**
   * 批量删除许可证
   * @param {Array} licenseIds - 许可证ID数组
   * @param {string} reason - 删除原因
   * @returns {Promise}
   */
  async batchDelete(licenseIds, reason) {
    return this.batchOperation(licenseIds, 'delete', {}, reason);
  }
}

export default new LicenseBatchService();
```

---

## 使用示例

### 基本使用

```javascript
import licenseBatchService from '@/api/services/licenseBatchService';

// 批量撤销
const result = await licenseBatchService.batchRevoke(
  [123, 124, 125],
  '违规使用，批量撤销'
);

console.log('操作结果:', result);
// {
//   success: true,
//   message: "批量操作完成，成功: 3/3",
//   results: [...]
// }

// 批量延长30天
const extendResult = await licenseBatchService.batchExtend(
  [126, 127],
  30,
  '客户续费延期'
);

// 批量暂停
const suspendResult = await licenseBatchService.batchSuspend(
  [128],
  '账户异常暂停'
);

// 批量激活
const activateResult = await licenseBatchService.batchActivate(
  [128],
  '问题解决，恢复许可证'
);

// 批量删除
const deleteResult = await licenseBatchService.batchDelete(
  [129, 130],
  '清理无效许可证'
);
```

### 结合许可证列表的完整示例

```vue
<template>
  <div class="license-management">
    <!-- 批量操作面板 -->
    <BatchOperationPanel
      :selected-licenses="selectedLicenses"
      @refresh="fetchLicenses"
      @clear-selection="selectedLicenses = []"
    />
    
    <!-- 许可证列表 -->
    <el-card>
      <template #header>
        <div class="list-header">
          <span>许可证列表</span>
          <div class="header-actions">
            <el-button
              v-if="selectedLicenses.length > 0"
              type="text"
              @click="selectedLicenses = []"
            >
              取消选择 ({{ selectedLicenses.length }})
            </el-button>
          </div>
        </div>
      </template>
      
      <el-table
        :data="licenses"
        :loading="loading"
        @selection-change="handleSelectionChange"
        border
      >
        <!-- 多选列 -->
        <el-table-column type="selection" width="50" />
        
        <el-table-column prop="id" label="ID" width="80" />
        
        <el-table-column label="许可证密钥" width="150">
          <template #default="{ row }">
            <code class="license-key">
              {{ row.license_key?.slice(-8) || 'N/A' }}***
            </code>
          </template>
        </el-table-column>
        
        <el-table-column prop="customer_name" label="客户名称" />
        <el-table-column prop="customer_email" label="客户邮箱" />
        
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="过期时间">
          <template #default="{ row }">
            {{ row.expires_at ? formatDate(row.expires_at) : '永久' }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" @click="viewDetail(row)">
              详情
            </el-button>
            <el-button
              size="small"
              type="danger"
              @click="quickRevoke(row)"
            >
              撤销
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @current-change="fetchLicenses"
        @size-change="fetchLicenses"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { ElMessage } from 'element-plus';
import BatchOperationPanel from './BatchOperationPanel.vue';
import licenseBatchService from '@/api/services/licenseBatchService';
import dayjs from 'dayjs';

// 数据
const loading = ref(false);
const licenses = ref([]);
const selectedLicenses = ref([]);
const currentPage = ref(1);
const pageSize = ref(20);
const total = ref(0);

// 获取许可证列表
const fetchLicenses = async () => {
  loading.value = true;
  try {
    const response = await axios.get('/api/v1/licenses/admin/licenses/', {
      params: {
        page: currentPage.value,
        page_size: pageSize.value
      }
    });
    
    licenses.value = response.data.results;
    total.value = response.data.count;
  } catch (error) {
    ElMessage.error('获取许可证列表失败');
  } finally {
    loading.value = false;
  }
};

// 选择变化
const handleSelectionChange = (selection) => {
  selectedLicenses.value = selection;
};

// 状态类型
const getStatusType = (status) => {
  const map = {
    generated: 'info',
    activated: 'success',
    expired: 'warning',
    revoked: 'danger',
    suspended: 'warning'
  };
  return map[status] || 'info';
};

// 状态文本
const getStatusText = (status) => {
  const map = {
    generated: '已生成',
    activated: '已激活',
    expired: '已过期',
    revoked: '已撤销',
    suspended: '已暂停'
  };
  return map[status] || status;
};

// 格式化日期
const formatDate = (dateString) => {
  return dayjs(dateString).format('YYYY-MM-DD HH:mm');
};

// 查看详情
const viewDetail = (license) => {
  // 跳转到详情页或打开详情弹窗
  router.push(`/admin/licenses/${license.id}`);
};

// 快速撤销单个许可证
const quickRevoke = async (license) => {
  try {
    await ElMessageBox.confirm(
      `确定要撤销许可证 "${license.license_key?.slice(-8)}***" 吗？`,
      '确认撤销',
      {
        confirmButtonText: '确认',
        cancelButtonText: '取消',
        type: 'error'
      }
    );
    
    await licenseBatchService.batchRevoke([license.id], '单个撤销');
    ElMessage.success('许可证撤销成功');
    fetchLicenses();
    
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('撤销失败');
    }
  }
};

onMounted(() => {
  fetchLicenses();
});
</script>
```

---

## cURL示例

### 批量撤销

```bash
curl -X POST 'http://localhost:8000/api/v1/licenses/admin/licenses/batch_operation/' \
  -H 'Authorization: Bearer <your_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "license_ids": [123, 124, 125],
    "operation": "revoke",
    "reason": "违规使用，批量撤销"
  }'
```

### 批量延长

```bash
curl -X POST 'http://localhost:8000/api/v1/licenses/admin/licenses/batch_operation/' \
  -H 'Authorization: Bearer <your_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "license_ids": [126, 127, 128],
    "operation": "extend",
    "parameters": {
      "days": 30
    },
    "reason": "客户续费，延长30天"
  }'
```

### 批量暂停

```bash
curl -X POST 'http://localhost:8000/api/v1/licenses/admin/licenses/batch_operation/' \
  -H 'Authorization: Bearer <your_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "license_ids": [129, 130],
    "operation": "suspend",
    "reason": "账户异常，临时暂停"
  }'
```

### 批量激活

```bash
curl -X POST 'http://localhost:8000/api/v1/licenses/admin/licenses/batch_operation/' \
  -H 'Authorization: Bearer <your_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "license_ids": [129, 130],
    "operation": "activate",
    "reason": "问题解决，恢复许可证"
  }'
```

### 批量删除

```bash
curl -X POST 'http://localhost:8000/api/v1/licenses/admin/licenses/batch_operation/' \
  -H 'Authorization: Bearer <your_token>' \
  -H 'Content-Type: application/json' \
  -d '{
    "license_ids": [131, 132],
    "operation": "delete",
    "reason": "清理无效许可证"
  }'
```

---

## 业务规则

### 权限控制

- **超级管理员**：可以对所有许可证执行批量操作
- **租户管理员**：只能对自己租户的许可证执行操作

### 操作限制

| 操作 | 可操作状态 | 限制条件 | 说明 |
|------|-----------|---------|------|
| **revoke** | generated, activated, suspended | 未撤销的许可证 | 已撤销的不能再撤销 |
| **suspend** | generated, activated | 有效或已生成的许可证 | 已暂停的不能再暂停 |
| **activate** | suspended | 已暂停的许可证 | 只能激活暂停的许可证 |
| **extend** | 任何状态 | 许可证有过期时间 | 永久许可证不能延期 |
| **delete** | 任何状态 | 无特殊限制 | 会先撤销再删除 |

### 状态转换图

```
generated ──┐
            ├─→ suspended ──→ activated
activated ──┘       ↓           ↓
                    └──→ revoked ←──┘
                            ↓
                        deleted
```

### 批量限制

- 最多一次操作100个许可证
- 最少要选择1个许可证
- 使用数据库事务，要么全部成功要么全部失败

---

## 错误处理指南

### 统一错误处理

```javascript
function handleBatchOperationError(error) {
  if (!error.response) {
    return '网络连接失败';
  }
  
  const { status, data } = error.response;
  
  switch (status) {
    case 400:
      if (data.errors) {
        const messages = [];
        for (const [field, errors] of Object.entries(data.errors)) {
          if (field === 'license_ids') {
            messages.push(`许可证ID错误: ${errors.join(', ')}`);
          } else {
            messages.push(`${field}: ${errors.join(', ')}`);
          }
        }
        return messages.join('\n');
      }
      return data.error || '请求参数错误';
      
    case 401:
      return '登录已过期，请重新登录';
      
    case 403:
      return '权限不足，无法执行批量操作';
      
    case 500:
      return '服务器错误，请稍后重试';
      
    default:
      return '操作失败';
  }
}
```

---

## 前端开发建议

### 功能清单

- [x] 许可证多选功能
- [x] 批量操作面板
- [x] 操作类型选择
- [x] 参数输入（延长天数等）
- [x] 二次确认对话框
- [x] 操作结果展示
- [x] 错误处理
- [x] 成功/失败统计

### UI/UX建议

1. **多选操作**：在许可证列表中提供复选框
2. **操作面板**：固定在列表上方，显示已选择数量
3. **危险操作确认**：撤销操作使用红色警告
4. **结果反馈**：详细显示每个许可证的操作结果
5. **进度指示**：长时间操作显示进度条

---

## 下一步

我已经为批量操作API创建了详细的文档。如果你需要更多细节或其他相关API的文档，请告诉我！

**文档已保存到**: `temp1007/batch_operation_api.md`
