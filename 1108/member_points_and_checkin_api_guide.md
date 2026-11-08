# Member 会员端积分与每日签到接口调用指南

> **更新时间**：2026-11-08  
> **面向对象**：移动端 App (iOS / Android)、微信小程序、Web 客户端等最终用户 (Member) 业务开发人员  
> **接口基准前缀**：`https://api.yourdomain.com/api/v1` （本地开发环境为 `http://localhost:8000/api/v1`）

---

## 目录
1. [全局调用规范与认证机制](#一全局调用规范与认证机制)
2. [接口一览表](#二接口一览表)
3. [每日签到与打卡接口详解](#三每日签到与打卡接口详解)
   - [3.1 查询签到状态与打卡日历](#31-查询签到状态与打卡日历)
   - [3.2 执行每日签到打卡](#32-执行每日签到打卡)
   - [3.3 执行漏签补签打卡](#33-执行漏签补签打卡)
   - [3.4 查询个人签到历史明细](#34-查询个人签到历史明细)
4. [应用积分账户与等级接口详解](#四应用积分账户与等级接口详解)
   - [4.1 查询自身应用专属积分账户与等级](#41-查询自身应用专属积分账户与等级)
   - [4.2 查询自身应用积分变动明细台账](#42-查询自身应用积分变动明细台账)
   - [4.3 查询应用完整等级梯队与徽章](#43-查询应用完整等级梯队与徽章)
   - [4.4 查询租户全局积分画像](#44-查询租户全局积分画像)
5. [客户端典型业务流集成代码示例](#五客户端典型业务流集成代码示例)
6. [业务错误码汇总与排错指南](#六业务错误码汇总与排错指南)

---

## 一、全局调用规范与认证机制

### 1. HTTP 请求头规范
所有会员端积分与签到接口均需要在请求头中携带以下认证与多租户信息：

| 请求头 Key | 类型 | 是否必填 | 示例值 | 说明 |
| :--- | :--- | :---: | :--- | :--- |
| `Authorization` | String | **是** | `Bearer eyJhbGciOi...` | Member 登录后获取的标准 JWT Access Token |
| `X-Tenant-ID` | Integer / String | **是** | `3` | 当前租户 ID（填色花园/自然拼读租户 ID 为 `3`） |
| `Content-Type` | String | **是** | `application/json` | 数据交互格式统一为 JSON |

> **提示**：若特定小程序框架对请求头有限制，也可以在 URL Query 参数中传递 `?tenant_id=3`。

### 2. 应用上下文隔离 (`application_id`)
* 系统支持**应用专属积分**与**应用专属签到规则**（如“填色花园”、“自然拼读”等）。
* 当在具体应用内调用接口时，建议在请求参数中携带 `application_id`（例如：`application_id=19`）。
* 若不传 `application_id`，系统默认归入该租户的**平台全局打卡与租户全局积分**。

---

## 二、接口一览表

| 序号 | 接口名称 | Method | 请求路径 | 核心业务场景 |
| :---: | :--- | :---: | :--- | :--- |
| 1 | **查询签到状态与日历** | `GET` | `/api/v1/points/checkin/status/` | 进入签到页，渲染连签天数、今日奖励、漏签日期 |
| 2 | **执行每日签到打卡** | `POST` | `/api/v1/points/checkin/execute/` | 用户点击“立即签到”，发放阶梯奖励，连签天数+1 |
| 3 | **执行漏签补签打卡** | `POST` | `/api/v1/points/checkin/recheckin/` | 用户补签过去的漏签日，扣积分，补奖励，连签天数自动接续 |
| 4 | **个人签到流水记录** | `GET` | `/api/v1/points/checkin/records/` | 查询用户本人的打卡历史凭证（标记正常打卡与补签） |
| 5 | **应用专属积分账户** | `GET` | `/api/v1/points/app-accounts/me/` | 查询当前用户在该应用的可用积分、总积分、等级与徽章 |
| 6 | **应用积分台账流水** | `GET` | `/api/v1/points/app-accounts/my_records/` | 查询积分增减账单（签到获得、补签扣除、消费明细等） |
| 7 | **应用等级体系阶梯** | `GET` | `/api/v1/points/app-levels/` | 查询应用预设的所有会员等级门槛、特权与透明徽章图标 |
| 8 | **平台全局积分画像** | `GET` | `/api/v1/points/profiles/me/` | 查询跨应用的租户全局用户积分画像 |

---

## 三、每日签到与打卡接口详解

### 3.1 查询签到状态与打卡日历

用户进入客户端签到主界面时调用。系统将返回当前用户的连签天数、今日打卡状态、今日/明日预测奖励、周期日历以及近 14 天内所有**漏签可补签的日期列表**。

* **请求方式**：`GET`
* **接口路径**：`/api/v1/points/checkin/status/`
* **Query 参数**：

| 参数名 | 类型 | 必填 | 示例值 | 说明 |
| :--- | :--- | :---: | :--- | :--- |
| `application_id` | Integer | 否 | `19` | 目标应用 ID。例如填色花园为 `19`，自然拼读为 `20` |

#### cURL 请求示例
```bash
curl -X GET "http://localhost:8000/api/v1/points/checkin/status/?application_id=19" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" \
  -H "X-Tenant-ID: 3"
```

#### 成功响应样例 (HTTP 200)
```json
{
  "has_checked_in_today": false,
  "current_streak": 4,
  "max_streak": 4,
  "total_days": 4,
  "last_checkin_date": "2026-11-07",
  "today_reward": 30,
  "tomorrow_reward": 40,
  "cycle_days": 7,
  "cycle_mode": "repeat",
  "is_active": true,
  "allow_recheckin": true,
  "recheckin_cost": 25,
  "missed_dates": [
    {
      "date": "2026-11-06",
      "cost": 25
    }
  ],
  "calendar": [
    { "day": 1, "points": 10, "status": "checked", "is_today": false, "label": "第1天" },
    { "day": 2, "points": 15, "status": "checked", "is_today": false, "label": "第2天" },
    { "day": 3, "points": 20, "status": "checked", "is_today": false, "label": "第3天" },
    { "day": 4, "points": 25, "status": "checked", "is_today": false, "label": "第4天" },
    { "day": 5, "points": 30, "status": "current", "is_today": true, "label": "第5天" },
    { "day": 6, "points": 40, "status": "upcoming", "is_today": false, "label": "第6天" },
    { "day": 7, "points": 100, "status": "upcoming", "is_today": false, "label": "第7天" }
  ]
}
```

#### 返回字段说明
* `has_checked_in_today` *(Boolean)*：今日是否已经打卡。`true` 表示今日已领奖；`false` 客户端应高亮展示“立即签到”按钮。
* `current_streak` *(Integer)*：当前有效连续打卡天数。
* `today_reward` *(Integer)*：如果今天打卡，可领取的积分数量。
* `missed_dates` *(Array)*：最近 14 天内漏签的日期数组。用于前端渲染“补签卡片”或补签弹窗列表。
* `calendar` *(Array)*：当前周期（如 7 天）日历阶梯卡片。`status` 枚举：
  * `checked`：已达成领奖天数
  * `current`：今日待领奖位置
  * `upcoming`：后续天数

---

### 3.2 执行每日签到打卡

用户在界面上点击“立即签到”时触发。系统在数据库层加悲观锁，原子化计算连签天数、依据阶梯发放积分、记录台账，并**自动判定是否达到应用专属积分等级升级门槛**。

* **请求方式**：`POST`
* **接口路径**：`/api/v1/points/checkin/execute/`
* **请求体 (Body - JSON)**：

```json
{
  "application_id": 19
}
```

#### cURL 请求示例
```bash
curl -X POST "http://localhost:8000/api/v1/points/checkin/execute/" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{"application_id": 19}'
```

#### 成功响应样例 (HTTP 200)
```json
{
  "success": true,
  "points_earned": 30,
  "current_streak": 5,
  "total_days": 5,
  "new_balance": 1050,
  "level_upgraded": true,
  "current_level": "黄金大师",
  "checkin_date": "2026-11-08"
}
```

#### 返回字段说明
* `points_earned` *(Integer)*：本次签到实际到账的奖励积分数。
* `current_streak` *(Integer)*：签到后最新的连续打卡天数。
* `new_balance` *(Integer)*：签到入账后用户在该应用的最新可用积分余额。
* `level_upgraded` *(Boolean)*：本次签到积分是否导致用户升阶！客户端可据此弹窗播放“恭喜晋级”庆祝特效。
* `current_level` *(String)*：升级判定后的当前积分等级名称。

#### 重复签到拦截 (HTTP 400)
若当天已签过，系统将主动拦截：
```json
{
  "success": false,
  "error_code": "ALREADY_CHECKED_IN",
  "message": "今日已完成签到，请明天再来"
}
```

---

### 3.3 执行漏签补签打卡

用户在日历上针对断签的历史某一天点击“补签”时调用。系统将校验用户可用积分余额，扣减配置的补签成本（如 25 分），补发对应梯级积分，并**自动向后推导连签记录，将断开的天数重新无缝连通**。

* **请求方式**：`POST`
* **接口路径**：`/api/v1/points/checkin/recheckin/`
* **请求体 (Body - JSON)**：

| 字段名 | 类型 | 必填 | 示例值 | 说明 |
| :--- | :--- | :---: | :--- | :--- |
| `target_date` | String | **是** | `"2026-11-07"` | 补签的目标日期，格式 `YYYY-MM-DD`（必须早于今天且在30天以内） |
| `application_id` | Integer | 否 | `19` | 目标应用 ID |

#### cURL 请求示例
```bash
curl -X POST "http://localhost:8000/api/v1/points/checkin/recheckin/" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" \
  -H "X-Tenant-ID: 3" \
  -H "Content-Type: application/json" \
  -d '{
    "application_id": 19,
    "target_date": "2026-11-07"
  }'
```

#### 成功响应样例 (HTTP 200)
```json
{
  "success": true,
  "target_date": "2026-11-07",
  "cost_points": 25,
  "points_earned": 25,
  "net_points_change": 0,
  "current_streak": 4,
  "total_days": 4,
  "new_balance": 1020,
  "level_upgraded": false,
  "current_level": "白银达人"
}
```

#### 常见失败响应说明
1. **积分余额不足以支付补签手续费** (HTTP 400)：
   ```json
   {
     "success": false,
     "error_code": "INSUFFICIENT_POINTS",
     "message": "积分不足，补签需要消耗 25 积分，当前可用积分仅为 10"
   }
   ```
2. **目标日期已签过或已补签** (HTTP 400)：
   ```json
   {
     "success": false,
     "error_code": "ALREADY_CHECKED_IN",
     "message": "2026-11-07 已经完成过签到或补签，无需重复补签"
   }
   ```
3. **尝试补签今天或未来日期** (HTTP 400)：
   ```json
   {
     "success": false,
     "error_code": "INVALID_RECHECKIN_DATE",
     "message": "只能补签过去的日期，今日及未来日期不可补签"
   }
   ```

---

### 3.4 查询个人签到历史明细

分页获取用户个人的打卡与补签日志。

* **请求方式**：`GET`
* **接口路径**：`/api/v1/points/checkin/records/`
* **Query 参数**：`application_id=19`、`page=1`、`page_size=10`
* **响应样例 (HTTP 200)**：
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 101,
      "application": 19,
      "application_name": "填色花园",
      "checkin_date": "2026-11-08",
      "streak_day": 5,
      "reward_points": 30,
      "is_recheckin": false,
      "created_at": "2026-11-08T09:40:22Z"
    },
    {
      "id": 99,
      "application": 19,
      "application_name": "填色花园",
      "checkin_date": "2026-11-07",
      "streak_day": 4,
      "reward_points": 25,
      "is_recheckin": true,
      "extra_data": { "cost_points": 25 },
      "created_at": "2026-11-08T09:39:10Z"
    }
  ]
}
```

---

## 四、应用积分账户与等级接口详解

### 4.1 查询自身应用专属积分账户与等级

获取当前登录用户在某款应用中的积分资产、成长等级、徽章图标及晋升进度。

* **请求方式**：`GET`
* **接口路径**：`/api/v1/points/app-accounts/me/`
* **Query 参数**：

| 参数名 | 类型 | 必填 | 说明 |
| :--- | :--- | :---: | :--- |
| `application_id` | Integer | 否 | 指定应用 ID（如 `19`）。若不传，返回该成员在所有应用下的账户列表 |

#### cURL 请求示例
```bash
curl -X GET "http://localhost:8000/api/v1/points/app-accounts/me/?application_id=19" \
  -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" \
  -H "X-Tenant-ID: 3"
```

#### 成功响应样例 (HTTP 200)
```json
{
  "id": 5,
  "tenant": 3,
  "application": 19,
  "application_name": "填色花园",
  "application_code": "001",
  "member": 43,
  "member_username": "alice_art",
  "member_email": "alice_art@test.com",
  "total_points": 1150,
  "available_points": 1050,
  "points_earned_total": 1250,
  "points_spent_total": 200,
  "current_level": 8,
  "current_level_info": {
    "id": 8,
    "level_name": "白银达人",
    "level_code": "LV_SILVER",
    "level_order": 2,
    "level_color": "#A0A0A0",
    "icon": "application/images/level_silver.png"
  },
  "is_enabled": true,
  "last_points_update": "2026-11-08T01:40:22.396078Z"
}
```

#### 关键字段说明
* `available_points` *(Integer)*：**当前可用积分余额**（用于补签、商城兑换等扣除）。
* `total_points` *(Integer)*：**累计成长值总积分**（只增不减，用于衡量会员等级晋升）。
* `current_level_info` *(Object)*：当前佩戴的应用会员等级：
  * `level_name`：头衔名称（如“白银达人”、“黄金大师”）
  * `level_color`：标识色 HEX 代码（如 `#FFD700`）
  * `icon`：透明 PNG 徽章相对路径。拼接后端根地址即可直接展示：`https://api.yourdomain.com/media/application/images/level_silver.png`

---

### 4.2 查询自身应用积分变动明细台账

查询用户在某应用中的完整财务积分台账（收入、支出、打卡、补签扣费等）。

* **请求方式**：`GET`
* **接口路径**：`/api/v1/points/app-accounts/my_records/`
* **Query 参数**：`application_id=19`、`page=1`、`page_size=10`
* **响应样例 (HTTP 200)**：
```json
{
  "count": 7,
  "results": [
    {
      "id": 501,
      "point_type": "earn",
      "category": "checkin",
      "subcategory": "checkin_reward",
      "points": 30,
      "balance_before": 1020,
      "balance_after": 1050,
      "operation_reason": "应用【填色花园】连续签到第5天奖励",
      "created_at": "2026-11-08T09:40:22Z"
    },
    {
      "id": 499,
      "point_type": "spend",
      "category": "checkin",
      "subcategory": "recheckin_cost",
      "points": -25,
      "balance_before": 1045,
      "balance_after": 1020,
      "operation_reason": "应用【填色花园】补签扣除积分（补签日期：2026-11-07）",
      "created_at": "2026-11-08T09:39:10Z"
    }
  ]
}
```

---

### 4.3 查询应用完整等级梯队与徽章

供客户端展示“等级特权成长路线图”，列出所有阶梯与勋章门槛。

* **请求方式**：`GET`
* **接口路径**：`/api/v1/points/app-levels/`
* **Query 参数**：`application=19`（应用 ID）
* **响应样例 (HTTP 200)**：
```json
{
  "results": [
    {
      "id": 7,
      "level_name": "青铜学员",
      "level_code": "LV_BRONZE",
      "level_order": 1,
      "min_points": 0,
      "max_points": 499,
      "level_color": "#CD7F32",
      "icon_url": "http://localhost:8000/media/application/images/level_bronze.png",
      "level_description": "新手画师专属每日涂色调色板"
    },
    {
      "id": 8,
      "level_name": "白银达人",
      "level_code": "LV_SILVER",
      "level_order": 2,
      "min_points": 500,
      "max_points": 1499,
      "level_color": "#A0A0A0",
      "icon_url": "http://localhost:8000/media/application/images/level_silver.png",
      "level_description": "可解锁中级绘图画册"
    },
    {
      "id": 9,
      "level_name": "黄金大师",
      "level_code": "LV_GOLD",
      "level_order": 3,
      "min_points": 1500,
      "max_points": 4999,
      "level_color": "#FFD700",
      "icon_url": "http://localhost:8000/media/application/images/level_gold.png",
      "level_description": "享有全画册无限次色彩笔刷特权"
    }
  ]
}
```

---

### 4.4 查询租户全局积分画像

获取跨应用的平台级会员积分概览。

* **请求方式**：`GET`
* **接口路径**：`/api/v1/points/profiles/me/`
* **响应样例 (HTTP 200)**：
```json
{
  "id": 4,
  "member": 43,
  "tenant": 3,
  "total_points": 1150,
  "available_points": 1050,
  "current_level": 8,
  "current_level_name": "白银达人",
  "is_points_enabled": true
}
```

---

## 五、客户端典型业务流集成代码示例

以下是基于现代前端 / 小程序（JavaScript / TypeScript / Axios / UniApp）的标准封装：

### 1. API 基础封装模块 (`api/points.js`)
```javascript
const BASE_URL = 'https://api.yourdomain.com/api/v1';

// 通用请求包装器
async function request(url, options = {}) {
  const token = localStorage.getItem('access_token') || uni.getStorageSync('access_token');
  const tenantId = 3; // 当前租户ID

  const headers = {
    'Content-Type': 'application/json',
    'X-Tenant-ID': String(tenantId),
    ...options.headers
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${BASE_URL}${url}`, {
    ...options,
    headers
  });

  const resJson = await response.json();
  if (!response.ok) {
    const errorMsg = resJson.message || resJson.detail || '请求失败';
    throw new Error(errorMsg);
  }
  return resJson.data || resJson;
}

// 导出会员专属接口
export const PointsApi = {
  // 1. 查询当前应用签到状态与日历
  getCheckinStatus(applicationId = 19) {
    return request(`/points/checkin/status/?application_id=${applicationId}`);
  },

  // 2. 立即打卡签到
  executeCheckin(applicationId = 19) {
    return request('/points/checkin/execute/', {
      method: 'POST',
      body: JSON.stringify({ application_id: applicationId })
    });
  },

  // 3. 补签指定漏签日期 (格式: YYYY-MM-DD)
  recheckinDate(targetDate, applicationId = 19) {
    return request('/points/checkin/recheckin/', {
      method: 'POST',
      body: JSON.stringify({
        application_id: applicationId,
        target_date: targetDate
      })
    });
  },

  // 4. 获取我的应用积分与等级资产
  getMyAccount(applicationId = 19) {
    return request(`/points/app-accounts/me/?application_id=${applicationId}`);
  },

  // 5. 获取我的积分流水明细
  getMyPointsLedger(applicationId = 19, page = 1) {
    return request(`/points/app-accounts/my_records/?application_id=${applicationId}&page=${page}`);
  }
};
```

---

### 2. 签到打卡交互业务流 (`pages/checkin.vue`)
```javascript
import { PointsApi } from '@/api/points';

export default {
  data() {
    return {
      appId: 19,
      loading: false,
      checkinStatus: null,
      accountInfo: null
    };
  },
  async mounted() {
    await this.loadPageData();
  },
  methods: {
    // 页面初次加载：并发拉取签到状态与积分账户
    async loadPageData() {
      this.loading = true;
      try {
        const [status, account] = await Promise.all([
          PointsApi.getCheckinStatus(this.appId),
          PointsApi.getMyAccount(this.appId)
        ]);
        this.checkinStatus = status;
        this.accountInfo = account;
      } catch (err) {
        uni.showToast({ title: err.message, icon: 'none' });
      } finally {
        this.loading = false;
      }
    },

    // 交互：用户点击“立即打卡”
    async handleCheckin() {
      if (this.checkinStatus?.has_checked_in_today) {
        uni.showToast({ title: '今日已完成打卡，明天再来哦~', icon: 'none' });
        return;
      }
      try {
        const res = await PointsApi.executeCheckin(this.appId);
        uni.showToast({
          title: `打卡成功！+${res.points_earned}积分 (连签${res.current_streak}天)`,
          icon: 'success'
        });

        // 升级特效弹窗触发
        if (res.level_upgraded) {
          uni.showModal({
            title: '🎉 恭喜晋级！',
            content: `您的积分成长值达到新门槛，晋升为【${res.current_level}】！`,
            showCancel: false
          });
        }

        // 刷新日历与积分显示
        await this.loadPageData();
      } catch (err) {
        uni.showToast({ title: err.message, icon: 'none' });
      }
    },

    // 交互：用户点击日历上的“补签”按钮
    async handleRecheckin(missedDate) {
      const cost = this.checkinStatus?.recheckin_cost || 25;
      uni.showModal({
        title: '补签确认',
        content: `补签 ${missedDate} 将扣除 ${cost} 积分并恢复连签天数，是否确认？`,
        success: async (confirmRes) => {
          if (!confirmRes.confirm) return;
          try {
            const res = await PointsApi.recheckinDate(missedDate, this.appId);
            uni.showToast({
              title: `补签成功！连签已恢复至 ${res.current_streak} 天`,
              icon: 'success'
            });
            await this.loadPageData();
          } catch (err) {
            uni.showToast({ title: err.message, icon: 'none' });
          }
        }
      });
    }
  }
};
```

---

## 六、业务错误码汇总与排错指南

当 HTTP 响应状态码为 `400 Bad Request` 时，响应体内会附带标准的 `error_code`，客户端可针对性弹窗引导：

| 错误代码 (`error_code`) | HTTP 状态码 | 产生原因 | 客户端推荐处理方式 |
| :--- | :---: | :--- | :--- |
| `ALREADY_CHECKED_IN` | 400 | 今日已经打卡，或补签的日期已经存在打卡凭证 | 提示“今日已完成打卡”或刷新页面日历 |
| `INSUFFICIENT_POINTS` | 400 | 用户当前可用积分低于补签手续费 (`recheckin_cost`) | 弹窗提示“积分不足无法补签，快去通过互动获取积分吧” |
| `INVALID_RECHECKIN_DATE` | 400 | 传递的补签日期为今天或未来日期 | 客户端日期选择器限制只能点选早于今天的过去日期 |
| `RECHECKIN_EXPIRED` | 400 | 传递的日期超出 30 天最大补签回溯窗口 | 提示“仅支持补签近30天内的漏签记录” |
| `CHECKIN_DISABLED` | 400 | 运营管理员在后台停用了该应用的每日签到规则 | 隐藏签到活动入口或提示“活动维护中” |
| `RECHECKIN_DISABLED` | 400 | 该应用签到规则未开启补签开关 | 日历隐藏补签按钮 |
| `POINTS_DISABLED` | 400 | 用户的应用积分账户或租户档案被管理员冻结 | 提示“积分账户已被冻结，请联系客服处理” |

---

### 技术支持与帮助
如有更多接口字段定制或小程序 SDK 对接疑问，请随时联系后端技术团队。
