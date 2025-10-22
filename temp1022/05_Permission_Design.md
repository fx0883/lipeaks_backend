# 用户反馈系统权限设计

## 文档信息
- **版本**: v1.0
- **创建日期**: 2025-10-22
- **权限框架**: Django REST Framework Permissions

## 1. 权限矩阵

### 1.1 总体权限矩阵

| 操作 | 超级管理员 | 租户管理员 | 普通用户/Member | 匿名用户 |
|------|-----------|-----------|----------------|---------|
| 创建反馈 | ✅ | ✅ | ✅ | ✅ |
| 查看反馈列表 | ✅本租户 | ✅本租户 | ✅仅自己 | ❌ |
| 查看反馈详情 | ✅本租户 | ✅本租户 | ✅仅自己 | ❌ |
| 更新反馈 | ✅本租户 | ✅本租户 | ⚠️仅未回复 | ❌ |
| 删除反馈 | ✅本租户 | ✅本租户 | ⚠️仅未回复 | ❌ |
| 添加回复 | ✅ | ✅ | ❌ | ❌ |
| 查看回复列表 | ✅含内部 | ✅含内部 | ✅仅官方 | ❌ |
| 变更状态 | ✅ | ✅ | ❌ | ❌ |
| 查看状态历史 | ✅ | ✅ | ✅ | ❌ |
| 投票 | ✅ | ✅ | ✅ | ❌ |
| 取消投票 | ✅ | ✅ | ✅ | ❌ |
| 上传附件 | ✅ | ✅ | ✅仅自己 | ⚠️提交时 |
| 查看统计 | ✅ | ✅ | ❌ | ❌ |
| 管理模板 | ✅ | ✅ | ❌ | ❌ |

### 1.2 符号说明

- ✅ = 完全允许
- ❌ = 完全禁止
- ⚠️ = 有条件允许

---

## 2. 权限类实现

### 2.1 基础权限类

```python
# feedbacks/permissions.py

from rest_framework import permissions
from common.utils.user_permissions import is_super_admin, is_admin

class IsFeedbackAdmin(permissions.BasePermission):
    """
    管理员权限
    超级管理员或租户管理员
    """
    
    def has_permission(self, request, view):
        return is_super_admin(request.user) or is_admin(request.user)


class IsAuthenticatedOrCreateOnly(permissions.BasePermission):
    """
    认证用户或仅允许创建
    """
    
    def has_permission(self, request, view):
        # 创建操作允许匿名用户
        if view.action == 'create':
            return True
        
        # 其他操作需要认证
        return request.user and request.user.is_authenticated


class IsFeedbackOwnerOrAdmin(permissions.BasePermission):
    """
    反馈所有者或管理员
    """
    
    def has_object_permission(self, request, view, obj):
        # 管理员有完全权限
        if is_super_admin(request.user) or is_admin(request.user):
            # 但只能操作本租户的反馈
            return obj.tenant_id == request.user.tenant_id
        
        # 检查是否是反馈提交者
        if obj.submitted_by_user == request.user:
            return True
        
        if hasattr(request.user, 'member') and obj.submitted_by_member == request.user.member:
            return True
        
        return False


class CanModifyFeedback(permissions.BasePermission):
    """
    可以修改反馈
    管理员：随时可以修改
    普通用户：只能在未回复时修改
    """
    
    def has_object_permission(self, request, view, obj):
        # 管理员可以随时修改
        if is_super_admin(request.user) or is_admin(request.user):
            return obj.tenant_id == request.user.tenant_id
        
        # 检查是否是所有者
        is_owner = False
        if obj.submitted_by_user == request.user:
            is_owner = True
        elif hasattr(request.user, 'member') and obj.submitted_by_member == request.user.member:
            is_owner = True
        
        if not is_owner:
            return False
        
        # 普通用户只能在无回复时修改
        if obj.replies_count > 0:
            return False
        
        return True


class CanDeleteFeedback(permissions.BasePermission):
    """
    可以删除反馈
    管理员：随时可以删除
    普通用户：只能在未回复时删除
    """
    
    def has_object_permission(self, request, view, obj):
        # 管理员可以随时删除
        if is_super_admin(request.user) or is_admin(request.user):
            return obj.tenant_id == request.user.tenant_id
        
        # 检查是否是所有者
        is_owner = False
        if obj.submitted_by_user == request.user:
            is_owner = True
        elif hasattr(request.user, 'member') and obj.submitted_by_member == request.user.member:
            is_owner = True
        
        if not is_owner:
            return False
        
        # 普通用户只能在无回复时删除
        if obj.replies_count > 0:
            return False
        
        return True
```

### 2.2 视图权限配置

```python
# feedbacks/views/feedback_views.py

from rest_framework import viewsets
from feedbacks.permissions import (
    IsAuthenticatedOrCreateOnly,
    IsFeedbackOwnerOrAdmin,
    CanModifyFeedback,
    CanDeleteFeedback,
    IsFeedbackAdmin
)

class FeedbackViewSet(viewsets.ModelViewSet):
    """反馈视图集"""
    
    def get_permissions(self):
        """根据操作类型返回不同权限"""
        
        if self.action == 'create':
            # 创建：所有人（包括匿名）
            permission_classes = [IsAuthenticatedOrCreateOnly]
        
        elif self.action in ['list', 'retrieve']:
            # 查看：需要登录，权限在queryset中控制
            permission_classes = [IsAuthenticatedOrCreateOnly, IsFeedbackOwnerOrAdmin]
        
        elif self.action in ['update', 'partial_update']:
            # 更新：需要登录，并且是所有者或管理员，有条件限制
            permission_classes = [IsAuthenticatedOrCreateOnly, CanModifyFeedback]
        
        elif self.action == 'destroy':
            # 删除：需要登录，并且是所有者或管理员，有条件限制
            permission_classes = [IsAuthenticatedOrCreateOnly, CanDeleteFeedback]
        
        elif self.action in ['add_reply', 'change_status']:
            # 回复、变更状态：只有管理员
            permission_classes = [IsFeedbackAdmin]
        
        elif self.action in ['vote', 'cancel_vote']:
            # 投票：需要登录
            permission_classes = [IsAuthenticatedOrCreateOnly]
        
        else:
            permission_classes = [IsAuthenticatedOrCreateOnly]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """根据用户角色过滤查询集"""
        user = self.request.user
        
        # 匿名用户无法查看
        if not user or not user.is_authenticated:
            return self.queryset.none()
        
        # 管理员：查看本租户所有反馈
        if is_super_admin(user) or is_admin(user):
            return self.queryset.filter(tenant=user.tenant)
        
        # 普通用户：只能查看自己提交的反馈
        from django.db.models import Q
        queryset = self.queryset.filter(
            Q(submitted_by_user=user) | 
            Q(submitted_by_member=getattr(user, 'member', None))
        )
        
        return queryset
```

---

## 3. 数据隔离

### 3.1 租户隔离

所有反馈数据都通过`tenant_id`字段实现租户隔离，继承自`BaseModel`。

```python
# 自动过滤租户数据
from common.utils.tenant_context import get_current_tenant

class FeedbackViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # 添加租户过滤
        tenant = get_current_tenant()
        if tenant:
            queryset = queryset.filter(tenant=tenant)
        
        return queryset
    
    def perform_create(self, serializer):
        """创建时自动设置租户"""
        tenant = get_current_tenant()
        if not tenant and self.request.user.is_authenticated:
            tenant = self.request.user.tenant
        
        serializer.save(tenant=tenant)
```

### 3.2 用户隔离

普通用户只能查看和操作自己提交的反馈。

```python
def get_queryset(self):
    """普通用户只能看到自己的反馈"""
    user = self.request.user
    
    if is_super_admin(user) or is_admin(user):
        # 管理员看到所有本租户反馈
        return Feedback.objects.filter(tenant=user.tenant)
    else:
        # 普通用户只看到自己的反馈
        from django.db.models import Q
        return Feedback.objects.filter(
            Q(submitted_by_user=user) |
            Q(submitted_by_member=getattr(user, 'member', None))
        )
```

---

## 4. 敏感信息保护

### 4.1 邮箱脱敏

```python
# feedbacks/serializers.py

class FeedbackListSerializer(serializers.ModelSerializer):
    """反馈列表序列化器"""
    
    contact_email = serializers.SerializerMethodField()
    
    def get_contact_email(self, obj):
        """邮箱脱敏显示"""
        user = self.context['request'].user
        
        # 管理员可以看到完整邮箱
        if is_super_admin(user) or is_admin(user):
            return obj.contact_email
        
        # 所有者可以看到完整邮箱
        if obj.submitted_by_user == user:
            return obj.contact_email
        
        # 其他人看到脱敏邮箱
        if obj.contact_email:
            email = obj.contact_email
            parts = email.split('@')
            if len(parts) == 2:
                name, domain = parts
                masked_name = name[0] + '***' + name[-1] if len(name) > 2 else '***'
                return f"{masked_name}@{domain}"
        
        return None
```

### 4.2 内部备注隐藏

```python
class FeedbackReplySerializer(serializers.ModelSerializer):
    """回复序列化器"""
    
    def to_representation(self, instance):
        """根据用户角色决定是否显示内部备注"""
        data = super().to_representation(instance)
        user = self.context['request'].user
        
        # 如果是内部备注，只有管理员可见
        if instance.is_internal:
            if not (is_super_admin(user) or is_admin(user)):
                # 非管理员不返回内部备注
                return None
        
        return data
```

---

## 5. API权限验证流程

### 5.1 完整验证流程

```
HTTP请求
    ↓
认证中间件 (JWT验证)
    ↓
识别用户身份
    ├─ 匿名用户
    ├─ 普通用户/Member
    ├─ 租户管理员
    └─ 超级管理员
    ↓
权限检查 (has_permission)
    ├─ 检查操作是否允许
    └─ 检查租户权限
    ↓
获取数据 (get_queryset)
    ├─ 应用租户过滤
    └─ 应用用户过滤
    ↓
对象权限检查 (has_object_permission)
    ├─ 检查对象所有权
    └─ 检查操作条件
    ↓
执行操作
```

---

## 6. 权限测试用例

### 6.1 创建反馈权限测试

```python
# tests/test_permissions.py

class FeedbackPermissionTests(TestCase):
    """反馈权限测试"""
    
    def test_anonymous_can_create_feedback(self):
        """匿名用户可以创建反馈"""
        response = self.client.post('/api/v1/feedbacks/', {
            'title': '测试反馈',
            'description': '测试描述',
            'feedback_type': 'bug',
            'software_id': 1,
            'contact_email': 'test@example.com'
        })
        self.assertEqual(response.status_code, 201)
    
    def test_user_can_create_feedback(self):
        """注册用户可以创建反馈"""
        self.client.force_authenticate(user=self.normal_user)
        response = self.client.post('/api/v1/feedbacks/', {
            'title': '测试反馈',
            'description': '测试描述',
            'feedback_type': 'bug',
            'software_id': 1
        })
        self.assertEqual(response.status_code, 201)
```

### 6.2 查看权限测试

```python
def test_user_can_only_see_own_feedbacks(self):
    """普通用户只能看到自己的反馈"""
    # 创建两个用户和反馈
    user1 = User.objects.create_user('user1', 'user1@test.com', 'pass')
    user2 = User.objects.create_user('user2', 'user2@test.com', 'pass')
    
    feedback1 = Feedback.objects.create(
        title='User1的反馈',
        submitted_by_user=user1,
        software_id=1
    )
    feedback2 = Feedback.objects.create(
        title='User2的反馈',
        submitted_by_user=user2,
        software_id=1
    )
    
    # user1登录后只能看到自己的反馈
    self.client.force_authenticate(user=user1)
    response = self.client.get('/api/v1/feedbacks/')
    
    self.assertEqual(len(response.data['results']), 1)
    self.assertEqual(response.data['results'][0]['id'], feedback1.id)

def test_admin_can_see_all_tenant_feedbacks(self):
    """管理员可以看到本租户所有反馈"""
    # 创建管理员和普通用户
    admin = User.objects.create_user('admin', 'admin@test.com', 'pass', is_admin=True)
    user = User.objects.create_user('user', 'user@test.com', 'pass')
    
    # 两人创建反馈
    feedback1 = Feedback.objects.create(
        title='管理员的反馈',
        submitted_by_user=admin,
        software_id=1
    )
    feedback2 = Feedback.objects.create(
        title='用户的反馈',
        submitted_by_user=user,
        software_id=1
    )
    
    # 管理员可以看到两个反馈
    self.client.force_authenticate(user=admin)
    response = self.client.get('/api/v1/feedbacks/')
    
    self.assertEqual(len(response.data['results']), 2)
```

### 6.3 修改权限测试

```python
def test_user_cannot_modify_replied_feedback(self):
    """用户不能修改已回复的反馈"""
    user = User.objects.create_user('user', 'user@test.com', 'pass')
    feedback = Feedback.objects.create(
        title='测试反馈',
        submitted_by_user=user,
        software_id=1,
        replies_count=1  # 已有回复
    )
    
    self.client.force_authenticate(user=user)
    response = self.client.patch(f'/api/v1/feedbacks/{feedback.id}/', {
        'title': '修改标题'
    })
    
    self.assertEqual(response.status_code, 403)

def test_admin_can_modify_any_feedback(self):
    """管理员可以修改任何反馈"""
    admin = User.objects.create_user('admin', 'admin@test.com', 'pass', is_admin=True)
    user = User.objects.create_user('user', 'user@test.com', 'pass')
    
    feedback = Feedback.objects.create(
        title='用户反馈',
        submitted_by_user=user,
        software_id=1,
        replies_count=5  # 已有多个回复
    )
    
    self.client.force_authenticate(user=admin)
    response = self.client.patch(f'/api/v1/feedbacks/{feedback.id}/', {
        'title': '管理员修改的标题'
    })
    
    self.assertEqual(response.status_code, 200)
```

### 6.4 回复权限测试

```python
def test_user_cannot_add_reply(self):
    """普通用户不能添加回复"""
    user = User.objects.create_user('user', 'user@test.com', 'pass')
    feedback = Feedback.objects.create(
        title='测试反馈',
        submitted_by_user=user,
        software_id=1
    )
    
    self.client.force_authenticate(user=user)
    response = self.client.post(f'/api/v1/feedbacks/{feedback.id}/replies/', {
        'content': '尝试回复',
        'reply_type': 'official'
    })
    
    self.assertEqual(response.status_code, 403)

def test_admin_can_add_reply(self):
    """管理员可以添加回复"""
    admin = User.objects.create_user('admin', 'admin@test.com', 'pass', is_admin=True)
    user = User.objects.create_user('user', 'user@test.com', 'pass')
    
    feedback = Feedback.objects.create(
        title='测试反馈',
        submitted_by_user=user,
        software_id=1
    )
    
    self.client.force_authenticate(user=admin)
    response = self.client.post(f'/api/v1/feedbacks/{feedback.id}/replies/', {
        'content': '管理员回复',
        'reply_type': 'official'
    })
    
    self.assertEqual(response.status_code, 201)
```

---

## 7. 安全建议

### 7.1 防止越权访问

1. **对象级权限检查**: 所有单个对象操作都要检查has_object_permission
2. **QuerySet过滤**: 在get_queryset中强制过滤
3. **双重验证**: Permission + QuerySet Filter

### 7.2 防止信息泄露

1. **邮箱脱敏**: 非所有者看到的邮箱需要脱敏
2. **内部备注隐藏**: 只有管理员可见
3. **环境信息保护**: 敏感环境信息只有管理员可见

### 7.3 防止滥用

1. **频率限制**: 使用DRF的Throttling
2. **IP限制**: 同一IP限制提交频率
3. **邮箱验证**: 匿名用户必须验证邮箱

---

## 8. 相关文档

- [01_需求分析.md](./01_需求分析.md) - 权限需求
- [03_API设计.md](./03_API设计.md) - API权限要求
- [02_数据模型设计.md](./02_数据模型设计.md) - 数据隔离设计

