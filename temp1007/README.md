# Member 许可证 API 文档

## 文档说明

本文档为 **lipeaks_backend** 系统中 **Member许可证申请和管理** 的前端集成文档。

文档编写日期：2025-10-06  
目标读者：前端开发人员  
后端框架：Django REST Framework  
认证方式：JWT (JSON Web Token)

---

## 🔥 重要更新（2025-10-06）

**多试用方案支持已上线！**

- ✅ 一个产品可以有多个试用方案
- ✅ 用户可以选择不同时长和激活数的方案
- ⚠️ **API响应结构变更**：`trial_plan` → `trial_plans` 数组

详见：📌 **FRONTEND_UPDATE_GUIDE.md** 和 **API_CHANGES_SUMMARY.md**

---

## 📋 文档目录

本文档集包含以下文件：

### 核心文档

1. **README.md** (本文件) - 总览和快速开始
2. **license_common.md** - 通用说明（认证、业务规则、数据模型）
3. **available_products_api.md** - 获取可申请产品列表API
4. **apply_license_api.md** - 申请试用许可证API
5. **my_licenses_api.md** - 查看我的许可证API
6. **integration_guide.md** - 完整集成指南（含客户端激活）

### 更新文档

7. **FRONTEND_UPDATE_GUIDE.md** - 🔥 前端更新指南（必读）
8. **API_CHANGES_SUMMARY.md** - API变更总结
9. **BUG_FIX_REPORT.md** - Bug修复报告
10. **MULTIPLE_TRIAL_PLANS_SOLUTION.md** - 多试用方案技术方案
11. **API_CALL_EXAMPLES.md** - API调用示例和常见问题

---

## 🎯 快速开始

### 1. 基础URL

所有许可证API的基础URL：
```
https://your-domain.com/api/v1/licenses/member/
```

本地开发环境：
```
http://localhost:8000/api/v1/licenses/member/
```

### 2. 认证方式

所有API请求都需要JWT认证，在请求头中添加：
```http
Authorization: Bearer <your_access_token>
```

### 3. 权限要求

- ✅ 必须是**Member用户**（不能是管理员）
- ✅ 用户状态必须为**活跃**
- ✅ 租户状态必须为**活跃**

---

## 📚 API功能概览

### Member许可证API

| 方法 | 端点 | 说明 | 频率限制 |
|------|------|------|---------|
| GET | `/api/v1/licenses/member/available-products/` | 获取可申请的试用产品列表 | 100次/小时 |
| POST | `/api/v1/licenses/member/apply/` | 申请试用许可证 | 5次/天 |
| GET | `/api/v1/licenses/member/my-licenses/` | 查看我的许可证列表 | 100次/小时 |

---

## 🚀 业务流程

### 完整的许可证申请流程

```
1. 用户登录
   ↓
2. 查看可申请产品列表
   GET /api/v1/licenses/member/available-products/
   ↓
3. 选择产品并申请试用许可证
   POST /api/v1/licenses/member/apply/
   ↓
4. 查看我的许可证
   GET /api/v1/licenses/member/my-licenses/
   ↓
5. 获取许可证密钥
   从许可证列表中获取license_key_preview（完整密钥需要另外获取）
   ↓
6. 在客户端软件中激活许可证
   POST /api/v1/licenses/activate/
   ↓
7. 定期发送心跳保持在线状态
   POST /api/v1/licenses/heartbeat/
```

---

## 💡 快速示例

### 示例1：获取可申请产品列表

```javascript
const response = await axios.get(
  'http://localhost:8000/api/v1/licenses/member/available-products/',
  {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  }
);

console.log('可申请产品:', response.data.data.products);
```

### 示例2：申请试用许可证

```javascript
const response = await axios.post(
  'http://localhost:8000/api/v1/licenses/member/apply/',
  {
    product_id: 1,
    reason: '我想试用这个产品',
    user_info: {
      company: '我的公司',
      job_title: '开发工程师',
      intended_use: '用于项目开发'
    }
  },
  {
    headers: {
      'Authorization': `Bearer ${accessToken}`,
      'Content-Type': 'application/json'
    }
  }
);

console.log('许可证密钥:', response.data.data.license_key);
console.log('过期时间:', response.data.data.expires_at);
```

### 示例3：查看我的许可证

```javascript
const response = await axios.get(
  'http://localhost:8000/api/v1/licenses/member/my-licenses/',
  {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    },
    params: {
      status: 'active',
      plan_type: 'trial'
    }
  }
);

console.log('许可证总数:', response.data.data.count);
console.log('有效许可证:', response.data.data.active_count);
console.log('许可证列表:', response.data.data.licenses);
```

---

## 🎨 业务规则

### 申请限制

| 限制类型 | 规则 | 说明 |
|---------|------|------|
| **重复申请** | 每个产品只能申请一次 | 避免重复申请同一产品 |
| **申请频率** | 24小时内最多3次 | 防止恶意频繁申请 |
| **试用配额** | 最多持有1个试用许可证 | 可配置，默认为1 |
| **API频率** | 5次/天 | 申请API的频率限制 |

### 自动化处理

- ✅ **自动审批**：试用申请自动通过，无需等待
- ✅ **自动生成**：许可证立即生成，可直接使用
- ✅ **自动分配**：创建Member与许可证的分配关系
- ✅ **自动有效期**：根据试用方案自动设置过期时间

---

## 📊 响应格式

### 成功响应

```json
{
  "success": true,
  "data": {
    // 实际数据内容
  }
}
```

### 错误响应

```json
{
  "success": false,
  "error": "错误描述",
  "code": "ERROR_CODE"
}
```

或

```json
{
  "success": false,
  "errors": {
    "field_name": ["字段错误信息"]
  }
}
```

---

## 🔐 安全说明

### 许可证密钥保护

- 📱 **列表接口**：只显示部分密钥（如 `ABCDE...VWXYZ`）
- 🔑 **申请接口**：返回完整密钥，前端需要安全存储
- 🚫 **不要**：将完整密钥显示在界面或日志中
- ✅ **建议**：提供"复制密钥"功能，用户主动复制

### 前端安全建议

```javascript
// ✅ 推荐：使用单独的复制功能
function copyLicenseKey(licenseKey) {
  navigator.clipboard.writeText(licenseKey);
  showToast('许可证密钥已复制到剪贴板');
}

// ❌ 不推荐：直接显示完整密钥
<div>许可证密钥：{{ fullLicenseKey }}</div>

// ✅ 推荐：默认隐藏，点击显示
<div>
  许可证密钥：{{ showKey ? fullLicenseKey : maskedKey }}
  <button @click="showKey = !showKey">
    {{ showKey ? '隐藏' : '显示' }}
  </button>
</div>
```

---

## 🎯 使用场景

### 场景1：产品试用流程

1. **展示产品列表**：显示所有可申请的试用产品
2. **申请试用**：用户选择产品并填写申请信息
3. **获取许可证**：申请成功后获得许可证密钥
4. **下载软件**：提供软件下载链接
5. **激活使用**：在软件中输入许可证密钥激活

### 场景2：许可证管理

1. **查看许可证**：显示所有已申请的许可证
2. **查看状态**：显示许可证状态（有效、已过期等）
3. **查看有效期**：显示距离过期的天数
4. **管理激活**：查看激活设备数和可用配额

---

## 📱 前端开发建议

### 需要实现的主要页面

1. **产品列表页面**
   - 展示可申请的试用产品
   - 显示产品信息和试用方案
   - 标记已申请状态
   - 申请按钮

2. **申请表单页面**
   - 产品选择
   - 申请原因输入
   - 补充信息（公司、职位、用途等）
   - 提交按钮

3. **许可证列表页面**
   - 展示已申请的许可证
   - 显示许可证状态和有效期
   - 许可证密钥复制功能
   - 激活信息展示

4. **许可证详情页面**
   - 完整的许可证信息
   - 激活设备列表
   - 使用统计
   - 下载软件链接

### 推荐的UI组件

- **产品卡片**：展示产品信息
- **状态标签**：显示许可证状态（有效/过期/撤销）
- **倒计时**：显示距离过期天数
- **进度条**：显示激活配额使用情况
- **复制按钮**：一键复制许可证密钥

---

## 🔍 常见错误码

| 错误码 | 说明 | 处理建议 |
|--------|------|---------|
| `APPLICATION_FAILED` | 申请失败 | 显示具体错误信息给用户 |
| `FETCH_PRODUCTS_FAILED` | 获取产品列表失败 | 提示用户稍后重试 |
| `FETCH_LICENSES_FAILED` | 获取许可证列表失败 | 提示用户稍后重试 |
| `QUOTA_EXCEEDED` | 配额已满 | 提示用户已达上限 |
| `RATE_LIMITED` | 频率限制 | 提示用户请求过于频繁 |

---

## 📖 下一步

请按顺序阅读以下文档：

1. 📘 **license_common.md** - 了解业务规则和数据模型
2. 📗 **available_products_api.md** - 实现产品列表功能
3. 📙 **apply_license_api.md** - 实现许可证申请功能
4. 📕 **my_licenses_api.md** - 实现许可证管理功能
5. 📔 **integration_guide.md** - 完整集成指南（含客户端激活）

---

## 🆘 技术支持

如有疑问，请联系后端团队或查阅：
- Swagger文档：`http://localhost:8000/api/v1/docs/`
- ReDoc文档：`http://localhost:8000/api/v1/redoc/`

---

**版本历史**
- v1.0 (2025-10-06) - 初始版本

