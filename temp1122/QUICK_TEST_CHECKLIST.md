# 租户隔离快速测试检查清单

## 快速开始（5分钟测试）

### 前置准备

1. 确保项目运行中
```bash
python manage.py runserver
```

2. 确保有至少2个租户的测试数据

### 核心测试（必做）

#### ✅ 测试1: 基础隔离测试

```bash
# 获取Token（替换为实际的用户名密码）
TOKEN1=$(curl -s -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin1","password":"pass123"}' | jq -r '.token')

TOKEN2=$(curl -s -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin2","password":"pass123"}' | jq -r '.token')

# Tenant 1 创建应用
curl -X POST http://localhost:8000/api/applications/ \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer $TOKEN1" \
  -H "Content-Type: application/json" \
  -d '{"name":"App T1","app_code":"APP_T1"}'

# Tenant 2 创建应用
curl -X POST http://localhost:8000/api/applications/ \
  -H "X-Tenant-ID: 2" \
  -H "Authorization: Bearer $TOKEN2" \
  -H "Content-Type: application/json" \
  -d '{"name":"App T2","app_code":"APP_T2"}'

# 验证隔离：Tenant 1只看到自己的应用
curl -X GET http://localhost:8000/api/applications/ \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer $TOKEN1"

# 验证隔离：Tenant 2只看到自己的应用
curl -X GET http://localhost:8000/api/applications/ \
  -H "X-Tenant-ID: 2" \
  -H "Authorization: Bearer $TOKEN2"
```

**预期结果**:
- [ ] Tenant 1只看到自己的应用（App T1）
- [ ] Tenant 2只看到自己的应用（App T2）
- [ ] 返回的数据中tenant_id字段正确

#### ✅ 测试2: 跨租户访问拒绝

```bash
# 尝试用Tenant 1的Token访问Tenant 2的租户
curl -X GET http://localhost:8000/api/applications/ \
  -H "X-Tenant-ID: 2" \
  -H "Authorization: Bearer $TOKEN1"
```

**预期结果**:
- [ ] 返回空列表 或 401/403错误
- [ ] 不能看到Tenant 2的数据

#### ✅ 测试3: Orders模块测试

```bash
# Tenant 1 创建订单
curl -X POST http://localhost:8000/api/orders/ \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer $TOKEN1" \
  -H "Content-Type: application/json" \
  -d '{"order_number":"ORD001","total_amount":"100.00"}'

# Tenant 2 创建订单
curl -X POST http://localhost:8000/api/orders/ \
  -H "X-Tenant-ID: 2" \
  -H "Authorization: Bearer $TOKEN2" \
  -H "Content-Type: application/json" \
  -d '{"order_number":"ORD001","total_amount":"200.00"}'

# 验证隔离
curl -X GET http://localhost:8000/api/orders/ \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer $TOKEN1"
```

**预期结果**:
- [ ] 两个租户可以有相同订单号（隔离的）
- [ ] Tenant 1只看到自己的订单
- [ ] 订单金额不同，确认是不同订单

### 数据库验证（可选但推荐）

```sql
-- 检查应用表
SELECT id, name, app_code, tenant_id 
FROM applications 
ORDER BY tenant_id, id;

-- 检查订单表
SELECT id, order_number, total_amount, tenant_id 
FROM orders 
ORDER BY tenant_id, id;

-- 检查是否有NULL的tenant_id
SELECT 'applications' as table_name, COUNT(*) as null_count 
FROM applications WHERE tenant_id IS NULL
UNION ALL
SELECT 'orders', COUNT(*) 
FROM orders WHERE tenant_id IS NULL;
```

**预期结果**:
- [ ] 所有记录都有正确的tenant_id
- [ ] 不同租户的数据清晰分离
- [ ] 没有NULL的tenant_id（除系统数据外）

## 深入测试（可选，15-30分钟）

### ✅ 测试4: Customers模块

```bash
# Tenant 1 创建客户
curl -X POST http://localhost:8000/api/customers/ \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer $TOKEN1" \
  -H "Content-Type: application/json" \
  -d '{"name":"Customer A","status":"active"}'

# Tenant 2 创建同名客户
curl -X POST http://localhost:8000/api/customers/ \
  -H "X-Tenant-ID: 2" \
  -H "Authorization: Bearer $TOKEN2" \
  -H "Content-Type: application/json" \
  -d '{"name":"Customer A","status":"active"}'

# 搜索测试
curl -X GET "http://localhost:8000/api/customers/?search=Customer A" \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer $TOKEN1"
```

**预期结果**:
- [ ] 两个租户可以有同名客户
- [ ] 搜索只返回本租户的客户
- [ ] created_by字段正确记录

### ✅ 测试5: Feedbacks模块

```bash
# Tenant 1 提交反馈
curl -X POST http://localhost:8000/api/feedbacks/ \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer $TOKEN1" \
  -H "Content-Type: application/json" \
  -d '{"title":"Bug Report","description":"Test","feedback_type":"bug"}'

# 查询反馈
curl -X GET http://localhost:8000/api/feedbacks/ \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer $TOKEN1"
```

**预期结果**:
- [ ] 反馈成功创建
- [ ] 只能看到本租户的反馈
- [ ] 普通用户只看自己的，管理员看租户内所有

### ✅ 测试6: Check_system模块（特殊情况）

```bash
# Tenant 1 创建打卡类型
curl -X POST http://localhost:8000/api/check-system/categories/ \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer $TOKEN1" \
  -H "Content-Type: application/json" \
  -d '{"name":"早起打卡","is_system":false}'

# 查询系统预设类型（应该对所有租户可见）
curl -X GET "http://localhost:8000/api/check-system/categories/?is_system=true" \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer $TOKEN1"

curl -X GET "http://localhost:8000/api/check-system/categories/?is_system=true" \
  -H "X-Tenant-ID: 2" \
  -H "Authorization: Bearer $TOKEN2"
```

**预期结果**:
- [ ] 自定义类型按租户隔离
- [ ] 系统预设类型对所有租户可见
- [ ] 两个租户看到相同的系统预设数据

### ✅ 测试7: 更新和删除操作

```bash
# 假设已知某个应用的ID
APP_ID=1

# Tenant 1 更新自己的应用
curl -X PUT http://localhost:8000/api/applications/$APP_ID/ \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer $TOKEN1" \
  -H "Content-Type: application/json" \
  -d '{"name":"Updated App T1"}'

# Tenant 2 尝试更新Tenant 1的应用（应该失败）
curl -X PUT http://localhost:8000/api/applications/$APP_ID/ \
  -H "X-Tenant-ID: 2" \
  -H "Authorization: Bearer $TOKEN2" \
  -H "Content-Type: application/json" \
  -d '{"name":"Hacked Name"}'
```

**预期结果**:
- [ ] Tenant 1成功更新
- [ ] Tenant 2更新失败（404或403）
- [ ] 数据未被篡改

## 性能测试（可选）

### ✅ 测试8: 大量数据下的查询性能

```bash
# 创建100个应用
for i in {1..100}; do
  curl -X POST http://localhost:8000/api/applications/ \
    -H "X-Tenant-ID: 1" \
    -H "Authorization: Bearer $TOKEN1" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"App $i\",\"app_code\":\"APP_$i\"}" &
done
wait

# 测试查询性能
time curl -X GET http://localhost:8000/api/applications/ \
  -H "X-Tenant-ID: 1" \
  -H "Authorization: Bearer $TOKEN1"
```

**预期结果**:
- [ ] 查询时间在可接受范围（<1秒）
- [ ] 租户过滤不显著影响性能
- [ ] 返回正确数量的数据

## 自动化测试

使用Python测试脚本：

```bash
# 编辑脚本配置Token
vim temp1122/test_tenant_isolation.py

# 运行自动化测试
python temp1122/test_tenant_isolation.py
```

## 测试完成检查清单

### 核心功能
- [ ] 创建操作自动设置tenant_id
- [ ] 查询操作自动过滤租户数据
- [ ] 更新操作验证租户所有权
- [ ] 删除操作验证租户所有权

### 安全性
- [ ] 跨租户访问被拒绝
- [ ] Token与租户ID不匹配时拒绝
- [ ] 直接对象访问有权限检查

### 数据完整性
- [ ] 所有记录有正确的tenant_id
- [ ] 关联数据租户一致
- [ ] 软删除不影响租户隔离

### 特殊情况
- [ ] 系统预设数据正常工作
- [ ] 无tenant字段的模型通过关联隔离
- [ ] 超级管理员可以访问所有数据

## 常见问题排查

### 问题1: 跨租户可以看到数据
**原因**: 
- TenantModelViewSet未正确继承
- get_queryset未调用super()
- Middleware未正确设置租户

**排查**:
```python
# 检查ViewSet定义
class MyViewSet(TenantModelViewSet):  # 必须继承TenantModelViewSet
    queryset = Model.objects.all()
    
    def get_queryset(self):
        queryset = super().get_queryset()  # 必须调用super()
        # 额外的过滤...
        return queryset
```

### 问题2: 创建数据没有tenant_id
**原因**:
- perform_create手动设置了tenant
- 覆盖了父类的自动设置

**排查**:
```python
def perform_create(self, serializer):
    # 不要手动设置tenant
    # serializer.save(tenant=...)  # ❌ 错误
    
    # 让TenantModelViewSet自动处理
    serializer.save(user=self.request.user)  # ✅ 正确
```

### 问题3: 某些模块隔离失效
**原因**:
- ViewSet未使用TenantModelViewSet
- Model没有tenant字段

**排查**:
```bash
# 检查哪些ViewSet未使用TenantModelViewSet
grep -r "class.*ViewSet" --include="*.py" | grep -v "TenantModelViewSet"
```

## 测试报告

完成测试后，请记录：

```markdown
## 测试日期
2025-11-22

## 测试结果
- 核心功能测试: ✅ 通过 / ❌ 失败
- 安全性测试: ✅ 通过 / ❌ 失败
- 数据完整性: ✅ 通过 / ❌ 失败
- 性能测试: ✅ 通过 / ❌ 失败

## 发现的问题
1. [描述问题]
2. [描述问题]

## 测试结论
[总体评价]
```

保存测试结果到：`temp1122/test_results.md`
