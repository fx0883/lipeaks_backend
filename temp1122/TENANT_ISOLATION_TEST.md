# 租户隔离功能测试计划

## 测试目标

验证TenantModelViewSet重构后的租户隔离功能是否正常工作

## 测试环境准备

### 1. 数据准备

需要准备：
- 至少2个租户（Tenant 1, Tenant 2）
- 每个租户至少1个管理员用户
- 每个租户的测试数据

### 2. 认证Token准备

```bash
# 获取Tenant 1的管理员Token
curl -X POST "http://localhost:8000/api/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin1@tenant1.com",
    "password": "password123"
  }'

# 获取Tenant 2的管理员Token
curl -X POST "http://localhost:8000/api/auth/login/" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin2@tenant2.com",
    "password": "password123"
  }'
```

## 测试用例

### 测试1: Applications模块

**目标**: 验证应用管理的租户隔离

```bash
# Tenant 1 创建应用
curl -X POST "http://localhost:8000/api/applications/" \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer TENANT1_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "App for Tenant 1",
    "app_code": "APP_T1_001"
  }'

# Tenant 2 创建应用
curl -X POST "http://localhost:8000/api/applications/" \
  -H "X-Tenant-ID: 2" \
  -H "Authorization: Bearer TENANT2_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "App for Tenant 2",
    "app_code": "APP_T2_001"
  }'

# Tenant 1 查询应用列表（应该只看到自己的）
curl -X GET "http://localhost:8000/api/applications/" \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer TENANT1_TOKEN"

# Tenant 2 查询应用列表（应该只看到自己的）
curl -X GET "http://localhost:8000/api/applications/" \
  -H "X-Tenant-ID: 2" \
  -H "Authorization: Bearer TENANT2_TOKEN"

# 验证：Tenant 1不能访问Tenant 2的应用
curl -X GET "http://localhost:8000/api/applications/TENANT2_APP_ID/" \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer TENANT1_TOKEN"
# 预期：404或403错误
```

**预期结果**:
- ✅ 每个租户只能看到自己创建的应用
- ✅ 跨租户访问被拒绝
- ✅ 自动设置tenant_id

### 测试2: Orders模块

**目标**: 验证订单管理的租户隔离

```bash
# Tenant 1 创建订单
curl -X POST "http://localhost:8000/api/orders/" \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer TENANT1_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "order_number": "ORDER_T1_001",
    "total_amount": 1000.00
  }'

# Tenant 2 创建订单
curl -X POST "http://localhost:8000/api/orders/" \
  -H "X-Tenant-ID: 2" \
  -H "Authorization: Bearer TENANT2_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "order_number": "ORDER_T2_001",
    "total_amount": 2000.00
  }'

# 验证隔离
curl -X GET "http://localhost:8000/api/orders/" \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer TENANT1_TOKEN"
# 预期：只返回Tenant 1的订单

curl -X GET "http://localhost:8000/api/orders/" \
  -H "X-Tenant-ID: 2" \
  -H "Authorization: Bearer TENANT2_TOKEN"
# 预期：只返回Tenant 2的订单
```

**预期结果**:
- ✅ 订单自动关联正确的租户
- ✅ 查询时自动过滤租户数据
- ✅ 软删除不影响租户隔离

### 测试3: Customers模块

**目标**: 验证客户管理的租户隔离

```bash
# Tenant 1 创建客户
curl -X POST "http://localhost:8000/api/customers/" \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer TENANT1_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Customer A for Tenant 1",
    "status": "active"
  }'

# Tenant 2 创建客户
curl -X POST "http://localhost:8000/api/customers/" \
  -H "X-Tenant-ID: 2" \
  -H "Authorization: Bearer TENANT2_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Customer A for Tenant 2",
    "status": "active"
  }'

# 搜索测试
curl -X GET "http://localhost:8000/api/customers/?search=Customer A" \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer TENANT1_TOKEN"
# 预期：只返回Tenant 1的Customer A

curl -X GET "http://localhost:8000/api/customers/?search=Customer A" \
  -H "X-Tenant-ID: 2" \
  -H "Authorization: Bearer TENANT2_TOKEN"
# 预期：只返回Tenant 2的Customer A
```

**预期结果**:
- ✅ 搜索结果自动过滤租户
- ✅ 同名客户在不同租户间隔离
- ✅ created_by字段正确记录

### 测试4: Interactions模块

**目标**: 验证用户互动的租户隔离

```bash
# Tenant 1 用户收藏文章
curl -X POST "http://localhost:8000/api/interactions/favorites/" \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer TENANT1_USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "article_id": 1
  }'

# Tenant 2 用户收藏文章
curl -X POST "http://localhost:8000/api/interactions/favorites/" \
  -H "X-Tenant-ID: 2" \
  -H "Authorization: Bearer TENANT2_USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "article_id": 1
  }'

# 验证收藏列表隔离
curl -X GET "http://localhost:8000/api/interactions/favorites/" \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer TENANT1_USER_TOKEN"
# 预期：只返回Tenant 1用户的收藏

# 测试点赞隔离
curl -X POST "http://localhost:8000/api/interactions/article-likes/" \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer TENANT1_USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "article_id": 1
  }'
```

**预期结果**:
- ✅ 收藏/点赞/关注数据按租户隔离
- ✅ 同一文章在不同租户可被独立互动
- ✅ IP和User-Agent正确记录

### 测试5: Feedbacks模块

**目标**: 验证反馈系统的租户隔离

```bash
# Tenant 1 提交反馈
curl -X POST "http://localhost:8000/api/feedbacks/" \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer TENANT1_USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Bug Report from Tenant 1",
    "description": "Description here",
    "feedback_type": "bug"
  }'

# Tenant 2 提交反馈
curl -X POST "http://localhost:8000/api/feedbacks/" \
  -H "X-Tenant-ID: 2" \
  -H "Authorization: Bearer TENANT2_USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Bug Report from Tenant 2",
    "description": "Description here",
    "feedback_type": "bug"
  }'

# 管理员查看反馈
curl -X GET "http://localhost:8000/api/feedbacks/" \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer TENANT1_ADMIN_TOKEN"
# 预期：只看到Tenant 1的反馈

# 普通用户查看反馈
curl -X GET "http://localhost:8000/api/feedbacks/" \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer TENANT1_USER_TOKEN"
# 预期：只看到自己提交的反馈
```

**预期结果**:
- ✅ 反馈按租户隔离
- ✅ 普通用户只看自己的
- ✅ 管理员看租户内所有
- ✅ 回复和附件也隔离

### 测试6: Check_system模块

**目标**: 验证打卡系统的租户隔离（含特殊情况）

```bash
# Tenant 1 创建打卡类型
curl -X POST "http://localhost:8000/api/check-system/categories/" \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer TENANT1_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "早起打卡",
    "is_system": false
  }'

# Tenant 1 创建打卡任务
curl -X POST "http://localhost:8000/api/check-system/tasks/" \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer TENANT1_USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "我的早起任务",
    "category_id": 1
  }'

# 验证：系统预设类型对所有租户可见
curl -X GET "http://localhost:8000/api/check-system/categories/?is_system=true" \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer TENANT1_USER_TOKEN"

curl -X GET "http://localhost:8000/api/check-system/categories/?is_system=true" \
  -H "X-Tenant-ID: 2" \
  -H "Authorization: Bearer TENANT2_USER_TOKEN"
# 预期：两个租户看到相同的系统预设类型

# CheckRecord测试（特殊：无tenant字段）
curl -X POST "http://localhost:8000/api/check-system/records/" \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer TENANT1_USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": 1,
    "check_date": "2025-11-22"
  }'
```

**预期结果**:
- ✅ 自定义类型按租户隔离
- ✅ 系统预设对所有租户可见
- ✅ CheckRecord通过task关联实现隔离
- ✅ 用户只看自己的任务和记录

### 测试7: Points模块

**目标**: 验证积分系统的租户隔离

```bash
# Tenant 1 用户查看积分
curl -X GET "http://localhost:8000/api/points/profiles/" \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer TENANT1_USER_TOKEN"

# Tenant 2 用户查看积分
curl -X GET "http://localhost:8000/api/points/profiles/" \
  -H "X-Tenant-ID: 2" \
  -H "Authorization: Bearer TENANT2_USER_TOKEN"

# 授予VIP标签（管理员操作）
curl -X POST "http://localhost:8000/api/points/user-tags/grant_vip_tag/" \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer TENANT1_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "member_id": 1,
    "tag_id": 1,
    "duration_days": 30
  }'
```

**预期结果**:
- ✅ 用户只看到自己租户的积分档案
- ✅ VIP标签按租户隔离
- ✅ 积分记录按租户隔离

## 边界情况测试

### 测试8: 跨租户访问尝试

```bash
# 尝试用Tenant 1的Token访问Tenant 2的数据
curl -X GET "http://localhost:8000/api/applications/" \
  -H "X-Tenant-ID: 2" \
  -H "Authorization: Bearer TENANT1_TOKEN"
# 预期：401或403错误，或返回空列表

# 尝试直接访问其他租户的对象
curl -X GET "http://localhost:8000/api/orders/TENANT2_ORDER_ID/" \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer TENANT1_TOKEN"
# 预期：404错误

# 尝试更新其他租户的数据
curl -X PUT "http://localhost:8000/api/customers/TENANT2_CUSTOMER_ID/" \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer TENANT1_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Hacked Name"
  }'
# 预期：404或403错误
```

**预期结果**:
- ✅ 所有跨租户访问被拒绝
- ✅ 即使知道ID也无法访问
- ✅ 更新/删除操作也被拦截

### 测试9: 无租户场景

```bash
# 不提供X-Tenant-ID头
curl -X GET "http://localhost:8000/api/applications/" \
  -H "Authorization: Bearer TENANT1_TOKEN"
# 预期：400错误或根据配置返回默认租户数据

# 提供无效的Tenant ID
curl -X GET "http://localhost:8000/api/applications/" \
  -H "X-Tenant-ID: 9999" \
  -H "Authorization: Bearer TENANT1_TOKEN"
# 预期：403错误或返回空列表
```

### 测试10: 超级管理员测试

```bash
# 超级管理员查看所有租户数据
curl -X GET "http://localhost:8000/api/applications/" \
  -H "Authorization: Bearer SUPERADMIN_TOKEN"
# 预期：返回所有租户的应用

# 超级管理员筛选特定租户
curl -X GET "http://localhost:8000/api/applications/?tenant_id=1" \
  -H "Authorization: Bearer SUPERADMIN_TOKEN"
# 预期：返回Tenant 1的应用
```

**预期结果**:
- ✅ 超级管理员可以访问所有租户数据
- ✅ 可以按租户ID筛选
- ✅ 正常CRUD操作不受影响

## 性能测试

### 测试11: 大数据量下的隔离性能

```bash
# 创建大量数据后测试查询性能
# 使用Apache Bench或类似工具
ab -n 1000 -c 10 \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer TENANT1_TOKEN" \
  http://localhost:8000/api/orders/
```

**预期结果**:
- ✅ 租户过滤不显著影响性能
- ✅ 索引正常工作
- ✅ 查询时间在可接受范围

## 数据库验证

### 测试12: 直接数据库检查

```sql
-- 检查tenant_id字段是否正确设置
SELECT id, name, tenant_id FROM applications;
SELECT id, order_number, tenant_id FROM orders;
SELECT id, name, tenant_id FROM customers;

-- 检查索引是否存在
SHOW INDEX FROM applications WHERE Key_name LIKE '%tenant%';
SHOW INDEX FROM orders WHERE Key_name LIKE '%tenant%';

-- 验证没有NULL的tenant_id（除系统数据外）
SELECT COUNT(*) FROM applications WHERE tenant_id IS NULL;
SELECT COUNT(*) FROM orders WHERE tenant_id IS NULL;
```

**预期结果**:
- ✅ 所有记录都有正确的tenant_id
- ✅ tenant_id索引存在
- ✅ 无意外的NULL值

## 测试检查清单

### 功能测试
- [ ] Applications模块租户隔离
- [ ] Licenses模块租户隔离
- [ ] Orders模块租户隔离
- [ ] Points模块租户隔离
- [ ] Check_system模块租户隔离（含特殊情况）
- [ ] CMS模块租户隔离
- [ ] Interactions模块租户隔离
- [ ] Feedbacks模块租户隔离
- [ ] Customers模块租户隔离

### 安全测试
- [ ] 跨租户访问拒绝
- [ ] 直接对象访问防护
- [ ] 更新/删除操作隔离
- [ ] Token与租户ID匹配验证

### 边界测试
- [ ] 无租户ID场景
- [ ] 无效租户ID场景
- [ ] 超级管理员权限
- [ ] 系统预设数据可见性

### 性能测试
- [ ] 查询性能测试
- [ ] 大数据量测试
- [ ] 索引有效性验证

### 数据完整性
- [ ] tenant_id自动设置
- [ ] 数据库约束检查
- [ ] 软删除与租户隔离
- [ ] 关联数据一致性

## 测试报告模板

```markdown
# 租户隔离功能测试报告

## 测试时间
2025-11-22

## 测试环境
- Django版本：
- 数据库：MySQL/PostgreSQL
- 测试租户数量：2个
- 测试用户数量：4个

## 测试结果总结
- 通过用例：X/Y
- 失败用例：X
- 成功率：XX%

## 详细测试结果

### Applications模块
- 状态：✅ 通过 / ❌ 失败
- 问题：[描述问题]
- 备注：[额外说明]

### [其他模块...]

## 发现的问题

### 问题1
- 模块：
- 描述：
- 严重程度：高/中/低
- 复现步骤：
- 预期结果：
- 实际结果：

## 改进建议
1. ...
2. ...

## 测试结论
[总体评价]
```

## 自动化测试脚本

下一步可以创建自动化测试脚本（test_tenant_isolation.py）来批量执行这些测试。
