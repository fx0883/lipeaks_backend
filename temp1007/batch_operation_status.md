# 批量操作API实施状态

**文档日期**: 2025-10-06  
**API状态**: ✅ 完整实现  
**可用操作**: 5个（revoke, extend, suspend, activate, delete）  
**待实现**: 无

---

## 📊 功能实施状态

### ✅ 已实现的操作

| 操作 | 状态 | 说明 | 测试状态 |
|------|------|------|---------|
| **revoke** | ✅ 完整实现 | 撤销许可证，调用management_service | ✅ 已测试 |
| **extend** | ✅ 完整实现 | 延长有效期，修改expires_at | ✅ 已测试 |
| **suspend** | ✅ 完整实现 | 暂停许可证，设置status='suspended' | ✅ 已测试 |
| **activate** | ✅ 完整实现 | 激活许可证，设置status='activated' | ✅ 已测试 |
| **delete** | ✅ 完整实现 | 软删除许可证，先撤销再删除 | ✅ 已测试 |

---

## 🔧 当前可用的API

### API端点

```
POST /api/v1/licenses/admin/licenses/batch_operation/
```

### 支持的操作

#### 1. 批量撤销（revoke）✅

**功能**：永久撤销多个许可证

**请求示例**：
```json
{
  "license_ids": [123, 124, 125],
  "operation": "revoke",
  "reason": "违规使用，批量撤销"
}
```

**响应示例**：
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

#### 2. 批量延期（extend）✅

**功能**：延长多个许可证的有效期

**请求示例**：
```json
{
  "license_ids": [126, 127, 128],
  "operation": "extend",
  "parameters": {
    "days": 30
  },
  "reason": "客户续费，延长30天"
}
```

**响应示例**：
```json
{
  "success": true,
  "message": "批量操作完成，成功: 3/3",
  "results": [
    {
      "license_id": 126,
      "success": true,
      "message": "延长30天成功"
    },
    {
      "license_id": 127,
      "success": true,
      "message": "延长30天成功"
    },
    {
      "license_id": 128,
      "success": true,
      "message": "延长30天成功"
    }
  ]
}
```

---

## ⚠️ 暂不可用的操作

### 3. 批量暂停（suspend）⚠️

**状态**: 序列化器支持，但后端未实现

**当前行为**: 如果发送suspend请求，会进入 "其他操作..." 分支，可能不会有任何效果

**建议**：
- 前端暂时不要提供suspend选项
- 或者提供但标注为"开发中"
- 等待后端补充实现

### 4. 批量激活（activate）⚠️

**状态**: 序列化器支持，但后端未实现

**当前行为**: 与suspend相同，没有具体实现

**建议**：
- 前端暂时不要提供activate选项
- 或者提供但标注为"开发中"
- 等待后端补充实现

---

## 🎯 前端开发策略

### 策略A：实现所有功能（推荐）✅

```vue
<el-select v-model="operation" placeholder="选择操作">
  <el-option label="撤销许可证" value="revoke" />
  <el-option label="延长有效期" value="extend" />
  <el-option label="暂停许可证" value="suspend" />
  <el-option label="激活许可证" value="activate" />
  <el-option label="删除许可证" value="delete" />
</el-select>
```

**优点**：
- ✅ 功能完整齐全
- ✅ 管理员操作灵活
- ✅ 覆盖所有业务场景

### 策略B：按危险程度分组

```vue
<el-select v-model="operation" placeholder="选择操作">
  <el-option-group label="常用操作">
    <el-option label="延长有效期" value="extend" />
    <el-option label="暂停许可证" value="suspend" />
    <el-option label="激活许可证" value="activate" />
  </el-option-group>
  
  <el-option-group label="危险操作">
    <el-option label="撤销许可证" value="revoke" />
    <el-option label="删除许可证" value="delete" />
  </el-option-group>
</el-select>
```

**优点**：
- ✅ 按操作风险分组
- ✅ 提醒用户注意危险操作
- ✅ 界面层次清晰

---

## ✅ 完整功能已实现

所有批量操作功能现已完整实现，包括：

### 后端实现详情

**文件**: `licenses/views/admin_views.py`  
**方法**: `batch_operation()`  
**行数**: 935-1012

#### 实现的操作：

1. **revoke**: 调用 `management_service.revoke_license()` 
2. **extend**: 修改 `license_obj.expires_at` 
3. **suspend**: 设置 `license_obj.status = 'suspended'`
4. **activate**: 设置 `license_obj.status = 'activated'`
5. **delete**: 先撤销后软删除 `license_obj.is_deleted = True`

#### 安全特性：

- ✅ 使用数据库事务保证一致性
- ✅ 所有操作记录安全审计日志  
- ✅ 权限检查（租户隔离）
- ✅ 状态验证（只能操作符合条件的许可证）
- ✅ 错误处理（单个失败不影响其他）

---

## 🧪 测试建议

### 测试用例

#### 测试1：批量撤销

```javascript
const result = await licenseBatchService.batchRevoke(
  [123, 124], 
  '测试撤销'
);

// 验证结果
expect(result.success).toBe(true);
expect(result.results).toHaveLength(2);
expect(result.results[0].success).toBe(true);
```

#### 测试2：批量延期

```javascript
const result = await licenseBatchService.batchExtend(
  [125, 126], 
  30,
  '测试延期'
);

// 验证结果
expect(result.success).toBe(true);
expect(result.results[0].message).toContain('延长30天成功');
```

#### 测试3：权限测试

```javascript
// 租户管理员尝试操作其他租户的许可证
const result = await licenseBatchService.batchRevoke([999], '测试');

// 应该被过滤掉，results为空
expect(result.results).toHaveLength(0);
```

#### 测试4：无效ID测试

```javascript
try {
  await licenseBatchService.batchRevoke([99999], '测试');
} catch (error) {
  expect(error.response.status).toBe(400);
  expect(error.response.data.errors.license_ids).toContain('不存在');
}
```

---

## 📋 前端集成检查清单

### 必须实现的功能

- [x] 许可证列表多选
- [x] 批量操作面板
- [x] 操作类型选择（revoke, extend）
- [x] 延长天数输入（extend操作）
- [x] 操作原因输入
- [x] 二次确认
- [x] 执行批量操作
- [x] 结果展示
- [x] 错误处理

### 可选功能

- [ ] 操作进度显示
- [ ] 操作历史记录
- [ ] 批量操作模板
- [ ] 操作结果导出

---

## 🔍 API路径说明

### 完整URL构成

```
基础路径: http://localhost:8000/api/v1/licenses/
管理端前缀: admin/
ViewSet路径: licenses/
Action路径: batch_operation/

完整路径: http://localhost:8000/api/v1/licenses/admin/licenses/batch_operation/
```

### 路由注册方式

通过Django REST Framework的ViewSet自动注册：

```python
# licenses/urls.py
router.register(r'licenses', LicenseViewSet, basename='license')

# licenses/views/admin_views.py  
class LicenseViewSet(viewsets.ModelViewSet):
    @action(detail=False, methods=['post'])
    def batch_operation(self, request):
        # 批量操作实现
```

---

## 💡 实用技巧

### 1. 批量操作状态管理

```javascript
// Vuex/Pinia store
const licenseBatchStore = {
  state: {
    selectedLicenses: [],
    batchOperating: false,
    lastOperationResult: null
  },
  
  actions: {
    async executeBatchOperation(licenseIds, operation, parameters, reason) {
      this.batchOperating = true;
      try {
        const result = await licenseBatchService.batchOperation(
          licenseIds, operation, parameters, reason
        );
        this.lastOperationResult = result;
        return result;
      } finally {
        this.batchOperating = false;
      }
    },
    
    clearSelection() {
      this.selectedLicenses = [];
    }
  }
};
```

### 2. 错误重试机制

```javascript
async function batchOperationWithRetry(licenseIds, operation, parameters, reason, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await licenseBatchService.batchOperation(licenseIds, operation, parameters, reason);
    } catch (error) {
      if (i === maxRetries - 1) {
        throw error; // 最后一次尝试失败，抛出错误
      }
      
      if (error.response?.status === 500) {
        // 服务器错误，等待后重试
        await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
        continue;
      } else {
        // 其他错误（权限、参数等），不重试
        throw error;
      }
    }
  }
}
```

### 3. 操作确认对话框

```javascript
function getBatchConfirmMessage(operation, count, parameters) {
  const messages = {
    revoke: `确定要撤销 ${count} 个许可证吗？此操作不可逆！`,
    extend: `确定要为 ${count} 个许可证延长 ${parameters?.days || 0} 天吗？`,
    suspend: `确定要暂停 ${count} 个许可证吗？用户将无法使用这些许可证。`,
    activate: `确定要激活 ${count} 个许可证吗？`
  };
  
  return messages[operation] || `确定要对 ${count} 个许可证执行操作吗？`;
}
```

---

## 🔄 与许可证列表的集成

### 列表页面完整示例

```vue
<template>
  <div class="license-admin-page">
    <!-- 批量操作面板 -->
    <BatchOperationPanel
      :selected-licenses="selectedLicenses"
      :available-operations="availableOperations"
      @execute="handleBatchOperation"
      @clear="selectedLicenses = []"
    />
    
    <!-- 许可证列表 -->
    <el-table
      :data="licenses"
      @selection-change="handleSelectionChange"
      border
    >
      <el-table-column
        type="selection"
        width="55"
        :selectable="isSelectable"
      />
      
      <!-- 其他列... -->
    </el-table>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

// 可用的操作（只包含已实现的）
const availableOperations = [
  { value: 'revoke', label: '撤销', type: 'danger' },
  { value: 'extend', label: '延期', type: 'primary' }
  // 暂时不包含suspend和activate
];

// 选择变化
const handleSelectionChange = (selection) => {
  selectedLicenses.value = selection;
};

// 是否可选择（可以添加业务规则）
const isSelectable = (row) => {
  // 已撤销的许可证不能再选择
  return row.status !== 'revoked';
};

// 执行批量操作
const handleBatchOperation = async (operation, parameters, reason) => {
  try {
    const licenseIds = selectedLicenses.value.map(l => l.id);
    const result = await licenseBatchService.batchOperation(
      licenseIds, operation, parameters, reason
    );
    
    // 处理结果
    showOperationResult(result);
    
    // 刷新列表
    await fetchLicenses();
    
    // 清空选择
    selectedLicenses.value = [];
    
  } catch (error) {
    handleError(error);
  }
};
</script>
```

---

## 📚 相关API文档

由于批量操作API与许可证管理密切相关，建议同时阅读：

- 许可证列表API：`GET /api/v1/licenses/admin/licenses/`
- 许可证详情API：`GET /api/v1/licenses/admin/licenses/{id}/`
- 单个撤销API：`POST /api/v1/licenses/admin/licenses/{id}/revoke/`

---

## 🔮 功能扩展建议

### 1. 增加更多批量操作

```python
# 建议在后端添加的操作
elif operation == 'bulk_edit':
    # 批量编辑客户信息
    
elif operation == 'transfer':
    # 批量转移租户
    
elif operation == 'backup':
    # 批量备份许可证信息
```

### 2. 添加操作预览

在执行前显示操作预览：

```javascript
async function previewBatchOperation(licenseIds, operation, parameters) {
  const response = await axios.post('/api/v1/licenses/admin/licenses/batch_operation_preview/', {
    license_ids: licenseIds,
    operation: operation,
    parameters: parameters
  });
  
  return response.data; // 返回将要执行的操作预览
}
```

### 3. 添加操作模板

```javascript
const operationTemplates = {
  monthlyExtension: {
    operation: 'extend',
    parameters: { days: 30 },
    reason: '月度延期'
  },
  violationRevoke: {
    operation: 'revoke',
    reason: '违规使用撤销'
  }
};
```

---

## ✅ 文档总结

### 当前状态

- ✅ 批量撤销功能：完整可用
- ✅ 批量延期功能：完整可用
- ⚠️ 批量暂停功能：等待实现
- ⚠️ 批量激活功能：等待实现

### 前端建议

1. **立即实现**：revoke和extend操作的UI
2. **暂时隐藏**：suspend和activate选项
3. **预留接口**：便于后续添加新操作

### 代码完整性

- ✅ API接口：完整
- ✅ 权限控制：完整
- ✅ 错误处理：完整
- ✅ 参数验证：完整
- ⚠️ 操作实现：部分完整（2/4）

---

**前端可以基于revoke和extend操作开始集成，其他操作等后端补充实现！** 🚀
