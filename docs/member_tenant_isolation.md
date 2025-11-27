# Member租户隔离实现说明

**版本**: v1.0  
**最后更新**: 2025-11-24  
**作者**: 系统架构组

---

## 概述

Member（普通成员）模型使用**手动租户过滤**方式实现租户隔离，而不是使用`TenantModelViewSet`自动租户隔离。本文档说明了这种设计决策的原因和实现细节。

---

## 为什么Member不使用TenantModelViewSet？

### 核心原因

Member与Application、Order等业务数据有本质区别：

| 特性 | Application（业务数据） | Member（用户身份） |
|------|----------------------|------------------|
| **数据性质** | 业务资源 | 用户身份 |
| **查看范围** | 租户内所有 | **仅自己** |
| **创建方式** | 管理员创建 | **自助注册** |
| **删除限制** | 无特殊限制 | **不能删除自己** |
| **权限模型** | 标准租户权限 | **多层级权限** |

### 特殊的权限逻辑

#### 1. Member只能看到自己

```python
# Member登录后查看个人信息
if isinstance(user, Member):
    return Member.objects.filter(pk=user.pk, is_deleted=False)
```

**如果使用TenantModelViewSet**:
```python
# ❌ 错误：Member能看到整个租户的所有Member
queryset = queryset.filter(tenant=tenant_id)
```

这是一个**严重的安全风险**！

#### 2. 多层级权限

Member API有三个层级：

1. **Member自用** (`/api/v1/members/me/`)
   - 只能操作自己
   - 不需要租户过滤

2. **租户管理员** (`/api/v1/admin/members/`)
   - 只能操作自己租户的Member
   - 使用手动租户过滤

3. **超级管理员** (`/api/v1/admin/members/`)
   - 可以操作所有租户的Member
   - 可以通过`tenant_id`参数筛选

#### 3. 复杂的过滤条件

Member有非常多的自定义过滤：

```python
# 搜索
queryset.filter(
    Q(username__icontains=search) | 
    Q(email__icontains=search) | 
    Q(nick_name__icontains=search) |
    Q(phone__icontains=search)
)

# 子账号过滤
queryset.filter(parent__isnull=False)

# 父账号过滤
queryset.filter(parent_id=parent_id)

# 租户过滤（仅超管）
if is_super_admin(user):
    queryset.filter(tenant_id=tenant_id)
```

这些逻辑与TenantModelViewSet的标准流程不兼容。

---

## 实现方式

### 管理员端API

#### AdminMemberListCreateView

```python
class AdminMemberListCreateView(generics.ListCreateAPIView):
    def get_queryset(self):
        user = self.request.user
        
        # 超级管理员可以看到所有Member
        if is_super_admin(user):
            queryset = Member.objects.filter(is_deleted=False)
        # 租户管理员只能看到自己租户的Member
        elif is_admin(user) and user.tenant:
            queryset = Member.objects.filter(
                tenant=user.tenant, 
                is_deleted=False
            )
        else:
            queryset = Member.objects.none()
        
        # 应用各种过滤条件...
        return queryset
```

**租户隔离点**：
- ✅ 手动检查用户角色
- ✅ 手动过滤`tenant=user.tenant`
- ✅ 超管可以跨租户查看

#### AdminMemberRetrieveUpdateDeleteView

```python
class AdminMemberRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    def get_queryset(self):
        user = self.request.user
        
        # Member类型用户只能查看自己
        if isinstance(user, Member):
            return Member.objects.filter(pk=user.pk, is_deleted=False)
        
        # 管理员逻辑同上...
        
    def perform_destroy(self, instance):
        # 特殊保护：不能删除自己
        if isinstance(user, Member) and instance.pk == user.pk:
            raise PermissionDenied("Cannot delete the currently logged-in account")
        
        instance.soft_delete()
```

**租户隔离点**：
- ✅ Member只能操作自己
- ✅ 租户管理员只能操作本租户Member
- ✅ 删除保护

### Member自用API

#### CurrentMemberView

```python
class CurrentMemberView(APIView):
    def get(self, request):
        # 直接返回当前登录用户
        member = request.user
        serializer = MemberSerializer(member, context={'request': request})
        return Response(serializer.data)
```

**租户隔离点**：
- ✅ 无需租户过滤，直接使用`request.user`
- ✅ 天然隔离，无法访问其他Member

---

## 测试覆盖

### 测试用例

位置：`tests/test_tenant_isolation.py`

#### 1. test_member_tenant_isolation
```python
def test_member_tenant_isolation(self):
    """测试Member模型的租户隔离"""
    # 创建属于不同租户的Member
    member1 = Member.objects.create_user(...)
    member2 = Member.objects.create_user(...)
    
    # 验证租户1只能看到自己的Member
    # 验证租户2只能看到自己的Member
    # 验证跨租户访问失败
```

#### 2. test_member_admin_can_only_see_own_tenant_members
```python
def test_member_admin_can_only_see_own_tenant_members(self):
    """测试租户管理员只能看到自己租户的Member"""
    # 验证租户管理员的视角
    # 确保无法看到其他租户的Member
```

### 运行测试

```bash
# 运行所有租户隔离测试
python manage.py test tests.test_tenant_isolation

# 只运行Member相关测试
python manage.py test tests.test_tenant_isolation.TenantIsolationTestCase.test_member_tenant_isolation
```

---

## 与TenantModelViewSet的对比

### Application（使用TenantModelViewSet）

```python
class ApplicationViewSet(TenantModelViewSet):
    queryset = Application.objects.all()
    
    # 自动处理：
    # - get_queryset() 自动按tenant过滤
    # - perform_create() 自动设置tenant_id
    # - perform_update() 自动验证租户所有权
    # - perform_destroy() 自动验证并软删除
```

**优点**：
- ✅ 代码简洁
- ✅ 统一的租户隔离机制
- ✅ 自动处理所有CRUD操作

**适用于**：标准业务数据（Application, Order, Customer等）

### Member（使用手动过滤）

```python
class AdminMemberListCreateView(generics.ListCreateAPIView):
    def get_queryset(self):
        # 手动实现复杂的权限逻辑
        if is_super_admin(user):
            queryset = Member.objects.filter(is_deleted=False)
        elif is_admin(user) and user.tenant:
            queryset = Member.objects.filter(tenant=user.tenant, ...)
        elif isinstance(user, Member):
            queryset = Member.objects.filter(pk=user.pk, ...)
        # ...复杂的过滤条件
```

**优点**：
- ✅ 灵活的权限控制
- ✅ 支持复杂过滤条件
- ✅ Member特有的安全保护

**适用于**：用户身份模型，需要特殊权限逻辑

---

## 安全考虑

### 1. Member只能看到自己

✅ **已实现**：在`CurrentMemberView`和`MemberRetrieveUpdateDeleteView`中强制执行

```python
if isinstance(user, Member):
    return Member.objects.filter(pk=user.pk, is_deleted=False)
```

### 2. 租户管理员隔离

✅ **已实现**：在`get_queryset`中手动过滤

```python
elif is_admin(user) and user.tenant:
    queryset = Member.objects.filter(tenant=user.tenant, is_deleted=False)
```

### 3. 不能删除自己

✅ **已实现**：在`perform_destroy`中检查

```python
if isinstance(user, Member) and instance.pk == user.pk:
    raise PermissionDenied("Cannot delete the currently logged-in account")
```

### 4. 子账号隔离

✅ **已实现**：子账号继承父账号的tenant，自动隔离

---

## API路由说明

### 管理员端

**路径**: `/api/v1/admin/members/`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | / | 获取Member列表 | 租户管理员 |
| POST | / | 创建Member | 租户管理员 |
| GET | /{id}/ | 获取Member详情 | 租户管理员 |
| PUT | /{id}/ | 更新Member | 租户管理员 |
| DELETE | /{id}/ | 删除Member | 租户管理员 |

### Member自用

**路径**: `/api/v1/members/`

| 方法 | 路径 | 说明 | 权限 |
|------|------|------|------|
| GET | /me/ | 获取自己信息 | Member |
| PUT | /me/ | 更新自己信息 | Member |
| PUT | /me/password/ | 修改密码 | Member |
| GET | /sub-accounts/ | 子账号列表 | Member（父账号） |
| POST | /sub-accounts/ | 创建子账号 | Member（父账号） |

---

## 最佳实践

### 何时使用TenantModelViewSet？

✅ **推荐使用**：
- 标准业务数据（Application, Order, Product等）
- 租户内所有用户都可以查看的数据
- 没有复杂的权限层级
- CRUD操作遵循标准模式

### 何时使用手动过滤？

✅ **推荐使用**：
- 用户身份模型（User, Member等）
- 需要"只能看到自己"的权限
- 有复杂的过滤条件
- 有多层级的权限模型
- 需要特殊的业务逻辑

---

## 常见问题

### Q1: 为什么不重构Member为TenantModelViewSet？

**A**: 主要原因：
1. Member的权限模型与业务数据完全不同
2. 重构会破坏现有的安全机制（Member只能看自己）
3. 当前实现已经过测试验证，功能完整且安全
4. 重构风险大于收益

### Q2: 手动过滤会不会有安全漏洞？

**A**: 不会。我们有：
- ✅ 完整的单元测试覆盖
- ✅ 明确的代码注释和文档
- ✅ 多层防护（权限类 + get_queryset + perform_* 方法）
- ✅ 定期的安全审计

### Q3: 如何确保租户隔离？

**A**: 三层保护：
1. **权限类**：`IsAdmin`检查用户角色
2. **get_queryset**：手动过滤`tenant=user.tenant`
3. **perform_*方法**：操作前再次验证

### Q4: 未来会统一为TenantModelViewSet吗？

**A**: 不会。Member的业务特性决定了它需要特殊处理。保持现有实现是最佳选择。

---

## 维护指南

### 添加新的Member API时

1. **确定API类型**：
   - Member自用？使用APIView，直接访问`request.user`
   - 管理员操作Member？继承`generics.*APIView`，手动过滤

2. **实现get_queryset**：
   ```python
   def get_queryset(self):
       user = self.request.user
       
       if isinstance(user, Member):
           # Member只能看自己
           return Member.objects.filter(pk=user.pk, is_deleted=False)
       
       if is_super_admin(user):
           # 超管看所有
           return Member.objects.filter(is_deleted=False)
       
       if is_admin(user) and user.tenant:
           # 租户管理员看自己租户
           return Member.objects.filter(tenant=user.tenant, is_deleted=False)
       
       return Member.objects.none()
   ```

3. **添加测试**：
   - 在`tests/test_tenant_isolation.py`添加测试用例
   - 验证租户隔离
   - 验证权限控制

4. **更新文档**：
   - 更新API文档
   - 说明权限要求
   - 提供curl示例

---

## 相关文档

- [租户隔离架构设计](/docs/tenant_middleware_refactor.md)
- [TenantModelViewSet使用指南](/docs/tenant_model_viewset.md)
- [Application API文档](/temp1123_6_application/02_应用管理API完整文档.md)

---

## 更新日志

### v1.0.0 (2025-11-24)
- ✅ 初始版本
- ✅ 添加Member租户隔离测试
- ✅ 完善代码注释
- ✅ 编写完整文档

---

**维护人员**: 如有问题或建议，请联系系统架构组
