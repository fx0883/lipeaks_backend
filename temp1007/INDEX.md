# Member许可证API文档索引

**最后更新**: 2025-10-06  
**版本**: v1.0

---

## 📚 文档导航

### 🔥 优先阅读（前端开发必读）

| 序号 | 文档 | 说明 | 重要程度 |
|------|------|------|---------|
| 1 | **README.md** | API总览和快速开始 | ⭐⭐⭐⭐⭐ |
| 2 | **license_common.md** | 通用规范和业务规则 | ⭐⭐⭐⭐⭐ |
| 3 | **integration_guide.md** | 完整集成指南 | ⭐⭐⭐⭐⭐ |

### 📖 API详细文档

| 序号 | 文档 | 涵盖的API | 目标页面 |
|------|------|-----------|---------|
| 4 | **available_products_api.md** | 获取可申请产品列表 | 产品浏览页 |
| 5 | **apply_license_api.md** | 申请试用许可证 | 申请表单页 |
| 6 | **my_licenses_api.md** | 查看我的许可证 | 许可证管理页 |

### 🔥 重要更新文档

| 序号 | 文档 | 说明 | 重要程度 |
|------|------|------|---------|
| 7 | **FRONTEND_UPDATE_GUIDE.md** | 前端更新指南（多方案支持） | ⭐⭐⭐⭐⭐ |
| 8 | **API_CHANGES_SUMMARY.md** | API变更总结 | ⭐⭐⭐⭐⭐ |
| 9 | **BUG_FIX_REPORT.md** | Bug修复报告 | ⭐⭐⭐⭐ |
| 10 | **MULTIPLE_TRIAL_PLANS_SOLUTION.md** | 多试用方案技术方案 | ⭐⭐⭐ |
| 11 | **API_CALL_EXAMPLES.md** | 实际调用示例 | ⭐⭐⭐⭐ |

---

## 🎯 根据角色选择文档

### Web前端开发人员

**推荐阅读顺序**：

1. 📘 **README.md** - 快速了解API功能
2. 📗 **license_common.md** - 理解业务规则和数据模型
3. 📙 **available_products_api.md** - 实现产品列表功能
4. 📕 **apply_license_api.md** - 实现申请功能
5. 📔 **my_licenses_api.md** - 实现许可证管理功能
6. 📌 **integration_guide.md** - 了解完整流程

**核心关注点**：
- ✅ API调用方法
- ✅ 错误处理
- ✅ 用户体验优化
- ✅ 许可证密钥保护

### 客户端软件开发人员

**推荐阅读顺序**：

1. 📌 **integration_guide.md** - 了解完整激活流程
2. 📘 **README.md** - API概览

**核心关注点**：
- ✅ 许可证激活API（`/api/v1/licenses/activate/`）
- ✅ 硬件信息收集
- ✅ 激活码保存
- ✅ 心跳机制

### 产品经理/项目负责人

**推荐阅读顺序**：

1. 📘 **README.md** - 业务流程概览
2. 📗 **license_common.md** - 业务规则
3. 📌 **integration_guide.md** - 完整流程

---

## 🔍 快速查找

### 按功能查找

| 功能 | API端点 | 文档 |
|------|---------|------|
| 浏览可申请产品 | `GET /api/v1/licenses/member/available-products/` | available_products_api.md |
| 申请试用许可证 | `POST /api/v1/licenses/member/apply/` | apply_license_api.md |
| 查看我的许可证 | `GET /api/v1/licenses/member/my-licenses/` | my_licenses_api.md |
| 激活许可证（客户端） | `POST /api/v1/licenses/activate/` | integration_guide.md |
| 验证激活（客户端） | `POST /api/v1/licenses/verify/` | integration_guide.md |
| 发送心跳（客户端） | `POST /api/v1/licenses/heartbeat/` | integration_guide.md |

### 按页面查找

| 页面 | 相关API | 文档 |
|------|---------|------|
| 产品浏览页 | available-products | available_products_api.md |
| 申请表单页 | apply | apply_license_api.md |
| 许可证列表页 | my-licenses | my_licenses_api.md |
| 激活指南页 | - | integration_guide.md |
| 软件激活界面 | activate, verify | integration_guide.md |

---

## 📊 API统计

### Web前端API（3个）

```
GET  /api/v1/licenses/member/available-products/  # 产品列表
POST /api/v1/licenses/member/apply/               # 申请许可证
GET  /api/v1/licenses/member/my-licenses/         # 我的许可证
```

### 客户端软件API（3个）

```
POST /api/v1/licenses/activate/     # 激活许可证
POST /api/v1/licenses/verify/       # 验证激活
POST /api/v1/licenses/heartbeat/    # 发送心跳
```

---

## 🚀 快速开始

### Step 1: 阅读基础文档

```bash
# 建议阅读顺序
1. README.md           # 5分钟
2. license_common.md   # 10分钟
3. integration_guide.md # 15分钟
```

### Step 2: 根据需求选择

**如果只开发Web前端**：
- 重点阅读前3个API文档
- 可以跳过客户端激活部分

**如果需要开发完整解决方案**：
- 阅读所有文档
- 重点关注integration_guide.md

### Step 3: 参考代码示例

每个文档都包含完整的代码示例，可以直接复制使用。

---

## 💡 关键提示

### ⚠️ 重要注意事项

1. **许可证密钥保护**
   - 完整密钥仅在申请成功时返回一次
   - 列表接口只显示部分密钥
   - 前端需要提示用户妥善保管

2. **频率限制**
   - 申请API：5次/天
   - 其他API：100次/小时
   - 需要做好错误处理和用户提示

3. **业务限制**
   - 每个产品只能申请一次
   - 24小时内最多申请3次
   - 最多持有1个试用许可证

4. **租户隔离**
   - 所有数据自动按租户隔离
   - Member只能看到自己的许可证

### ✅ 开发建议

1. **先实现基础功能**
   - 产品列表 → 申请 → 查看许可证

2. **再完善用户体验**
   - 过期提醒
   - 激活指南
   - 使用统计

3. **最后优化性能**
   - 缓存产品列表
   - 自动刷新许可证
   - 错误重试机制

---

## 📦 代码模板下载

### API Service封装

```javascript
// src/api/services/licenseService.js
import axios from 'axios';

const BASE_URL = '/api/v1/licenses/member';

class LicenseService {
  async getAvailableProducts() {
    const { data } = await axios.get(`${BASE_URL}/available-products/`);
    return data.data;
  }
  
  async applyTrialLicense(productId, reason, userInfo) {
    const requestData = { product_id: productId };
    if (reason) requestData.reason = reason;
    if (userInfo) requestData.user_info = userInfo;
    
    const { data } = await axios.post(`${BASE_URL}/apply/`, requestData);
    return data;
  }
  
  async getMyLicenses(filters = {}) {
    const { data } = await axios.get(`${BASE_URL}/my-licenses/`, {
      params: filters
    });
    return data.data;
  }
}

export default new LicenseService();
```

### TypeScript类型定义

```typescript
// src/types/license.ts

export interface Product {
  id: number;
  name: string;
  code: string;
  description: string;
  version: string;
  trial_plan: TrialPlan | null;
  already_applied: boolean;
}

export interface TrialPlan {
  id: number;
  name: string;
  default_validity_days: number;
  default_max_activations: number;
  features: Record<string, any>;
  price: number;
  currency: string;
}

export interface License {
  id: number;
  product_name: string;
  product_code: string;
  product_version: string;
  plan_name: string;
  plan_type: 'trial' | 'basic' | 'professional' | 'enterprise';
  license_key_preview: string;
  status: 'active' | 'expired' | 'revoked' | 'pending';
  status_display: string;
  assignment_type: string;
  assigned_at: string;
  activated_at: string | null;
  expires_at: string | null;
  days_until_expiry: number | null;
  can_activate_license: boolean;
  activation_info: ActivationInfo;
  usage_count: number;
  last_used_at: string | null;
  last_heartbeat: string | null;
  can_activate: boolean;
  can_deactivate: boolean;
  can_share: boolean;
  max_devices_per_user: number;
}

export interface ActivationInfo {
  current_activations: number;
  max_activations: number;
  available_slots: number;
}

export interface ApplicationResult {
  license_id: number;
  assignment_id: number;
  license_key: string;
  expires_at: string;
  product_name: string;
  plan_name: string;
  max_activations: number;
}
```

---

## 🆘 常见问题

### Q1: 申请成功后没有保存许可证密钥怎么办？

**A**: 许可证密钥仅在申请成功时返回一次完整密钥。建议：
1. 在申请成功对话框中强制用户复制密钥
2. 提供"下载密钥文件"功能
3. 发送邮件通知（如果后端支持）

### Q2: 用户已有试用许可证，无法申请新产品？

**A**: 这是业务规则限制（最多1个试用许可证）。建议：
1. 在产品列表页提前显示提示
2. 引导用户查看现有许可证
3. 等待现有许可证过期后再申请

### Q3: 如何检查许可证是否即将过期？

**A**: 使用`days_until_expiry`字段：
```javascript
if (license.days_until_expiry !== null && license.days_until_expiry <= 7) {
  showExpiryWarning(license);
}
```

### Q4: 客户端软件如何激活许可证？

**A**: 客户端需要：
1. 收集硬件信息
2. 调用`/api/v1/licenses/activate/` API
3. 保存返回的`activation_code`
4. 使用`activation_code`进行后续验证和心跳

详见：**integration_guide.md** 第四步

---

## 📞 技术支持

- **Swagger文档**: http://localhost:8000/api/v1/docs/
- **ReDoc文档**: http://localhost:8000/api/v1/redoc/
- **后端团队**: 如有问题请联系

---

**祝开发顺利！** ✨

