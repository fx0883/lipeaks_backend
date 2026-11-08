# 1108 会员端接口规范与开发文档

本目录收录 2026年11月08日 完成的客户端会员（Member）调用规范与接口文档：

- 📄 **[Member 会员端积分与每日签到接口调用指南](./member_points_and_checkin_api_guide.md)**
  - 全局认证机制（JWT、`X-Tenant-ID`、`application_id` 应用范围）
  - 每日打卡签到接口（`POST /api/v1/points/checkin/execute/`）
  - 漏签补签接口（`POST /api/v1/points/checkin/recheckin/`，自动接续连签天数并扣减手续费）
  - 打卡状态与日历查询接口（`GET /api/v1/points/checkin/status/`，含 `missed_dates` 漏签识别）
  - 会员个人打卡流水明细（`GET /api/v1/points/checkin/records/`）
  - 会员应用专属积分账户资产与等级头衔（`GET /api/v1/points/app-accounts/me/`）
  - 会员应用积分收支明细台账（`GET /api/v1/points/app-accounts/my_records/`）
  - 应用成长等级阶梯与透明徽章列表（`GET /api/v1/points/app-levels/`）
  - 完备的前端 / 微信小程序（JavaScript / UniApp）调用封装与业务交互示例代码
  - 常见错误码字典与排错指南
