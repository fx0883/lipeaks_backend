# Task: 将异常处理中文Message改为英文

## 任务标识
- **Task ID**: chinese_to_english_exceptions_20251016_01
- **创建日期**: 2025-10-16
- **分支**: task/chinese_to_english_exceptions_20251016_01

## 任务描述
将lipeaks_backend项目中所有异常处理的中文message改为英文显示。

## 研究发现

### 1. 异常体系结构
项目采用统一的异常体系架构：
- **基类**: `common/exceptions/base.py` - `BusinessException`
- **模块化异常类**:
  - `common/exceptions/user.py` - 用户相关异常
  - `common/exceptions/license.py` - 许可证相关异常
  - `common/exceptions/tenant.py` - 租户相关异常
  - `common/exceptions/cms.py` - CMS相关异常
  - `common/exceptions/points.py` - 积分相关异常
- **错误码和消息**: `common/exceptions/error_codes.py`
  - `ErrorCodes` 类 - 定义业务错误码（4位数字）
  - `ErrorMessages` 类 - 定义默认错误消息（**当前为中文**）

### 2. 需要修改的文件类型

#### A. 核心异常定义文件（高优先级）
1. **`common/exceptions/error_codes.py`**
   - `ErrorMessages` 类中的所有中文消息（约50+个）
   - 这是最关键的文件，包含所有默认错误消息

2. **`common/exceptions/base.py`**
   - `default_detail = '业务操作失败'` (line 50)

#### B. 业务代码中的异常抛出（中优先级）
文件涉及范围：
- `users/` - 用户模块 (多个视图文件)
- `licenses/` - 许可证模块 (序列化器和服务)
- `check_system/` - 打卡系统
- `cms/` - 内容管理
- `rbac/` - 权限管理
- `customers/` - 客户管理
- `orders/` - 订单管理
- `tenants/` - 租户管理
- `points/` - 积分系统
- `menus/` - 菜单管理
- `common/` - 通用组件

常见异常类型：
- `serializers.ValidationError` - 数据验证错误
- `PermissionDenied` - 权限拒绝
- `jwt.InvalidTokenError` - JWT令牌错误
- `Throttled` - 限流错误
- 业务异常类（继承自BusinessException）

### 3. 中文异常消息统计

根据grep搜索结果：
- `ValidationError` 相关: 163个匹配（19个文件）
- `PermissionDenied` 相关: 26个匹配（9个文件）
- `raise` 语句中包含中文: 402个匹配（56个文件）
- `detail` 参数中包含中文: 303个匹配（37个文件）

### 4. 主要受影响的文件列表（Top 20）

| 文件 | 匹配数 | 类型 |
|------|--------|------|
| `check_system/views.py` | 56 | raise语句 |
| `users/serializers.py` | 52 | raise+ValidationError |
| `cms/views.py` | 44 | detail参数 |
| `users/views/admin_user_views.py` | 43 | detail+raise |
| `licenses/serializers.py` | 30 | ValidationError |
| `users/views/member_views.py` | 28 | detail+raise |
| `common/viewsets.py` | 22 | raise语句 |
| `rbac/views.py` | 19 | detail参数 |
| `licenses/models.py` | 14 | raise语句 |
| `cms/views.py` | 13 | ValidationError |
| `users/views/member_admin_views.py` | 13 | detail参数 |
| `common/authentication/jwt_auth.py` | 11 | raise+ValidationError |
| `licenses/services/member_license_service.py` | 11 | detail+raise |
| `tenants/views.py` | 10 | raise语句 |
| `rbac/serializers.py` | 9 | ValidationError |
| `cms/permissions.py` | 8 | PermissionDenied |
| `points/models.py` | 8 | raise语句 |
| `users/views/auth_views.py` | 8 | raise语句 |
| `common/exceptions/license.py` | 7 | 文档注释 |
| `customers/serializers.py` | 7 | ValidationError |

## 提议的解决方案

### 方案选择：全面国际化改造

#### 阶段1：核心异常消息英文化（必须）
1. 修改 `common/exceptions/error_codes.py` 中的 `ErrorMessages` 类
   - 将所有中文消息改为英文
   - 保持错误码不变
   - 确保语义准确

2. 修改 `common/exceptions/base.py` 
   - 将 `default_detail` 改为英文

#### 阶段2：业务代码异常消息英文化（必须）
逐个模块处理，按优先级：
1. **认证和授权** (`common/authentication/`, `users/views/auth_views.py`)
2. **用户管理** (`users/serializers.py`, `users/views/`)
3. **许可证管理** (`licenses/serializers.py`, `licenses/services/`)
4. **租户管理** (`tenants/views.py`)
5. **其他业务模块** (cms, rbac, orders, etc.)

处理模式：
- `ValidationError` 消息 → 英文
- `PermissionDenied` 消息 → 英文
- 业务异常的 `detail` 参数 → 英文
- JWT错误消息 → 英文
- 日志消息保持中文（仅面向开发者）

#### 阶段3：文档注释更新（可选）
- 更新异常类的docstring示例
- 保持中文注释（面向中文开发团队）

### 英文翻译原则
1. **准确性**: 语义准确，符合REST API规范
2. **简洁性**: 简洁明了，避免冗长
3. **专业性**: 使用标准技术术语
4. **一致性**: 相似错误使用相似表达

### 示例翻译对照表

| 中文 | 英文 |
|------|------|
| 认证失败，请登录 | Authentication failed, please log in |
| 认证令牌无效或已过期 | Authentication token is invalid or expired |
| 您没有执行该操作的权限 | You do not have permission to perform this action |
| 租户不存在 | Tenant not found |
| 租户未激活或已被禁用 | Tenant is inactive or disabled |
| 许可证已过期 | License has expired |
| 许可证不存在 | License not found |
| 许可证配额已达上限 | License quota limit exceeded |
| 用户不存在 | User not found |
| 用户账户已被禁用 | User account is disabled |
| 积分余额不足 | Insufficient points balance |
| 文章不存在 | Article not found |
| 两次输入的密码不一致 | Passwords do not match |
| 无效的租户ID格式 | Invalid tenant ID format |
| 只有管理员才能修改其他用户的密码 | Only administrators can change other users' passwords |
| 不能删除当前登录的账号 | Cannot delete the currently logged-in account |
| 请求过于频繁，请稍后再试 | Too many requests, please try again later |

## 任务进度

### 已完成
- [x] 项目结构分析
- [x] 异常体系研究
- [x] 中文异常统计
- [x] 解决方案设计

### 待完成
- [ ] 阶段1：修改核心异常消息（error_codes.py, base.py）
- [ ] 阶段2：修改业务代码异常消息
  - [ ] common/authentication/
  - [ ] users/
  - [ ] licenses/
  - [ ] tenants/
  - [ ] check_system/
  - [ ] cms/
  - [ ] rbac/
  - [ ] customers/
  - [ ] orders/
  - [ ] points/
  - [ ] menus/
- [ ] 测试验证
- [ ] 代码审查

## 风险和注意事项
1. **前端兼容性**: 需要确认前端是否依赖特定的中文错误消息
2. **测试用例**: 需要更新测试用例中的预期错误消息
3. **日志系统**: 开发日志可以保持中文，面向用户的错误消息需要英文
4. **国际化**: 未来可考虑使用i18n框架支持多语言
