# 用户反馈系统实施计划

## 文档信息
- **版本**: v1.0
- **创建日期**: 2025-10-22
- **预计周期**: 5周
- **开发人员**: 1-2人

## 1. 项目阶段划分

### 总体时间线

```
第一阶段: 核心功能开发 (2周)
    ├─ Week 1: 数据模型 + 基础API
    └─ Week 2: 回复功能 + 简单邮件

第二阶段: 邮件系统完善 (1周)
    ├─ Day 1-2: 邮件模板管理
    ├─ Day 3-4: 异步发送 + 重试
    └─ Day 5: 邮箱验证 + 退订

第三阶段: 增强功能 (1周)
    ├─ Day 1-2: 投票功能
    ├─ Day 3-4: 附件上传 + 统计
    └─ Day 5: 管理后台优化

第四阶段: 测试优化 (1周)
    ├─ Day 1-2: 单元测试 + 集成测试
    ├─ Day 3-4: 性能优化 + 压力测试
    └─ Day 5: 文档完善 + 部署上线
```

---

## 2. 第一阶段：核心功能 (2周)

### Week 1: 数据模型 + 基础API

#### Day 1-2: 创建应用和数据模型

**任务清单**:
- [x] 创建`feedbacks` app
- [x] 定义7个核心模型
  - [x] Feedback（反馈主表）
  - [x] FeedbackReply（反馈回复）
  - [x] FeedbackStatusHistory（状态历史）
  - [x] FeedbackAttachment（反馈附件）
  - [x] FeedbackVote（反馈投票）
  - [x] FeedbackEmailLog（邮件日志）
  - [x] EmailTemplate（邮件模板）
- [x] 编写模型方法和属性
- [x] 创建数据库迁移文件
- [x] 执行迁移

**代码实现**:
```bash
# 创建应用
python manage.py startapp feedbacks

# 编辑models.py (参考02_数据模型设计.md)

# 创建迁移
python manage.py makemigrations feedbacks

# 执行迁移
python manage.py migrate feedbacks
```

**验收标准**:
- ✅ 所有模型创建成功
- ✅ 数据库表结构正确
- ✅ 外键关系正确
- ✅ 索引创建成功

---

#### Day 3-4: 序列化器和基础API

**任务清单**:
- [x] 创建序列化器
  - [x] FeedbackListSerializer
  - [x] FeedbackDetailSerializer
  - [x] FeedbackCreateUpdateSerializer
  - [x] FeedbackReplySerializer
- [x] 创建视图集
  - [x] FeedbackViewSet (CRUD)
- [x] 配置URL路由
- [x] 实现权限控制

**代码实现**:
```python
# feedbacks/serializers.py
class FeedbackListSerializer(serializers.ModelSerializer):
    # ... (参考API设计文档)

# feedbacks/views/feedback_views.py
class FeedbackViewSet(viewsets.ModelViewSet):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackListSerializer
    permission_classes = [IsAuthenticatedOrCreateOnly]
    
    def get_queryset(self):
        # 实现权限过滤
        pass

# feedbacks/urls.py
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'', FeedbackViewSet, basename='feedback')
```

**API端点**:
- `POST /api/v1/feedbacks/` - 创建反馈
- `GET /api/v1/feedbacks/` - 反馈列表
- `GET /api/v1/feedbacks/{id}/` - 反馈详情
- `PATCH /api/v1/feedbacks/{id}/` - 更新反馈
- `DELETE /api/v1/feedbacks/{id}/` - 删除反馈

**验收标准**:
- ✅ 匿名用户可以提交反馈
- ✅ 注册用户可以提交反馈
- ✅ 用户只能看到自己的反馈
- ✅ 管理员可以看到所有反馈
- ✅ API响应格式正确

---

#### Day 5: 反馈列表过滤和搜索

**任务清单**:
- [x] 实现筛选功能
  - [x] 按类型筛选
  - [x] 按状态筛选
  - [x] 按优先级筛选
  - [x] 按日期范围筛选
- [x] 实现搜索功能
  - [x] 标题搜索
  - [x] 描述搜索
- [x] 实现排序功能
- [x] 实现分页

**代码实现**:
```python
from django_filters import rest_framework as filters

class FeedbackFilter(filters.FilterSet):
    feedback_type = filters.ChoiceFilter(choices=Feedback.TYPE_CHOICES)
    status = filters.ChoiceFilter(choices=Feedback.STATUS_CHOICES)
    priority = filters.ChoiceFilter(choices=Feedback.PRIORITY_CHOICES)
    date_from = filters.DateFilter(field_name='created_at', lookup_expr='gte')
    date_to = filters.DateFilter(field_name='created_at', lookup_expr='lte')
    search = filters.CharFilter(method='search_filter')
    
    def search_filter(self, queryset, name, value):
        return queryset.filter(
            Q(title__icontains=value) | Q(description__icontains=value)
        )
    
    class Meta:
        model = Feedback
        fields = ['feedback_type', 'status', 'priority', 'software']

class FeedbackViewSet(viewsets.ModelViewSet):
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = FeedbackFilter
    ordering_fields = ['created_at', 'votes_count', 'priority']
    ordering = ['-created_at']
```

**验收标准**:
- ✅ 筛选功能正常
- ✅ 搜索结果准确
- ✅ 排序功能正常
- ✅ 分页正常工作

---

### Week 2: 回复功能 + 简单邮件

#### Day 1-2: 回复功能

**任务清单**:
- [x] 实现添加回复API
- [x] 区分官方回复和内部备注
- [x] 实现回复列表API
- [x] 更新反馈的回复计数
- [x] 更新首次/最后回复时间

**代码实现**:
```python
class FeedbackViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=['post'])
    def add_reply(self, request, pk=None):
        feedback = self.get_object()
        serializer = FeedbackReplySerializer(data=request.data)
        
        if serializer.is_validated():
            serializer.save(
                feedback=feedback,
                replied_by_user=request.user
            )
            return Response(serializer.data, status=201)
        
        return Response(serializer.errors, status=400)
    
    @action(detail=True, methods=['get'])
    def replies(self, request, pk=None):
        feedback = self.get_object()
        replies = feedback.replies.all()
        
        # 普通用户不能看到内部备注
        if not (is_super_admin(request.user) or is_admin(request.user)):
            replies = replies.filter(is_internal=False)
        
        serializer = FeedbackReplySerializer(replies, many=True)
        return Response(serializer.data)
```

**验收标准**:
- ✅ 管理员可以添加回复
- ✅ 普通用户不能添加回复
- ✅ 内部备注只有管理员可见
- ✅ 回复后自动更新统计

---

#### Day 3-4: 简单邮件发送

**任务清单**:
- [x] 配置SMTP设置
- [x] 创建基础邮件服务
- [x] 实现同步邮件发送
- [x] 创建简单邮件模板
- [x] 测试邮件发送

**代码实现**:
```python
# settings.py 邮件配置已存在
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.qq.com'
EMAIL_PORT = 465
EMAIL_USE_SSL = True

# feedbacks/services/email_service.py
class EmailService:
    def send_reply_email(self, reply):
        feedback = reply.feedback
        recipient = feedback.get_submitter_email()
        
        if not recipient:
            return False
        
        subject = f"[{feedback.software.name}] 您的反馈已收到回复"
        message = f"""
        尊敬的用户，
        
        您的反馈（{feedback.tracking_number}）已收到回复：
        
        {reply.content}
        
        查看详情：{settings.FRONTEND_URL}/feedbacks/{feedback.id}
        """
        
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient])
            return True
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False
```

**验收标准**:
- ✅ 官方回复自动发送邮件
- ✅ 内部备注不发送邮件
- ✅ 邮件内容格式正确
- ✅ 邮件发送成功

---

#### Day 5: 状态管理

**任务清单**:
- [x] 实现状态变更API
- [x] 记录状态历史
- [x] 发送状态变更邮件
- [x] 实现状态历史查询API

**代码实现**:
```python
class FeedbackViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=['patch'])
    def change_status(self, request, pk=None):
        feedback = self.get_object()
        new_status = request.data.get('new_status')
        reason = request.data.get('reason', '')
        send_email = request.data.get('send_email', True)
        
        # 验证状态
        if new_status not in dict(Feedback.STATUS_CHOICES):
            return Response({'error': '无效状态'}, status=400)
        
        # 记录历史
        old_status = feedback.status
        FeedbackStatusHistory.create_history(
            feedback=feedback,
            old_status=old_status,
            new_status=new_status,
            changed_by=request.user,
            reason=reason,
            send_email=send_email
        )
        
        # 更新状态
        feedback.status = new_status
        if new_status == 'resolved':
            feedback.resolved_at = timezone.now()
        elif new_status == 'closed':
            feedback.closed_at = timezone.now()
        feedback.save()
        
        return Response({'message': '状态更新成功'})
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        feedback = self.get_object()
        history = feedback.status_history.all()
        serializer = FeedbackStatusHistorySerializer(history, many=True)
        return Response(serializer.data)
```

**验收标准**:
- ✅ 状态变更成功
- ✅ 状态历史记录正确
- ✅ 状态变更邮件发送
- ✅ 历史查询API正常

---

## 3. 第二阶段：邮件系统完善 (1周)

### Day 1-2: 邮件模板管理

**任务清单**:
- [x] 创建默认邮件模板
- [x] 实现模板CRUD API
- [x] 实现模板渲染功能
- [x] 实现模板预览功能
- [x] 支持变量替换

**代码实现**:
```python
# 创建默认模板数据迁移
python manage.py makemigrations feedbacks --empty -n create_default_templates

# 在迁移文件中创建默认模板
def create_default_templates(apps, schema_editor):
    EmailTemplate = apps.get_model('feedbacks', 'EmailTemplate')
    # 创建默认模板...

# 模板管理ViewSet
class EmailTemplateViewSet(viewsets.ModelViewSet):
    queryset = EmailTemplate.objects.all()
    serializer_class = EmailTemplateSerializer
    permission_classes = [IsFeedbackAdmin]
    
    @action(detail=True, methods=['post'])
    def preview(self, request, pk=None):
        # 预览功能...
```

**验收标准**:
- ✅ 默认模板创建成功
- ✅ 模板CRUD正常
- ✅ 变量替换正确
- ✅ 预览功能正常

---

### Day 3-4: 异步发送 + 重试

**任务清单**:
- [x] 安装配置Celery
- [x] 创建邮件发送任务
- [x] 实现失败重试机制
- [x] 记录邮件日志
- [x] 测试异步发送

**代码实现**:
```bash
# 安装Celery和Redis
pip install celery redis

# 配置Celery
# core/celery.py
from celery import Celery
app = Celery('lipeaks_backend')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# 创建邮件任务（参考04_邮件系统设计.md）

# 启动Celery worker
celery -A core worker -l info -Q email
```

**验收标准**:
- ✅ Celery配置正确
- ✅ 邮件异步发送成功
- ✅ 失败自动重试
- ✅ 邮件日志记录完整

---

### Day 5: 邮箱验证 + 退订

**任务清单**:
- [x] 实现邮箱验证功能
- [x] 发送验证邮件
- [x] 实现验证API
- [x] 实现退订功能
- [x] 生成退订链接

**代码实现**:
```python
# 邮箱验证API
@action(detail=False, methods=['post'])
def verify_email(self, request):
    token = request.data.get('token')
    
    try:
        feedback = Feedback.objects.get(email_verification_token=token)
        
        # 检查是否过期（24小时）
        if feedback.email_verification_sent_at:
            time_diff = timezone.now() - feedback.email_verification_sent_at
            if time_diff.total_seconds() > 86400:  # 24小时
                return Response({'error': '验证链接已过期'}, status=400)
        
        # 验证成功
        feedback.email_verified = True
        feedback.save()
        
        return Response({'message': '邮箱验证成功'})
        
    except Feedback.DoesNotExist:
        return Response({'error': '无效的验证链接'}, status=400)

# 退订API
@action(detail=True, methods=['post'])
def unsubscribe(self, request, pk=None):
    feedback = self.get_object()
    feedback.email_notification_enabled = False
    feedback.save()
    return Response({'message': '已退订邮件通知'})
```

**验收标准**:
- ✅ 验证邮件发送成功
- ✅ 验证功能正常
- ✅ 退订功能正常
- ✅ 已退订用户不再收到邮件

---

## 4. 第三阶段：增强功能 (1周)

### Day 1-2: 投票功能

**任务清单**:
- [x] 实现投票API
- [x] 实现取消投票API
- [x] 防止重复投票
- [x] 更新投票计数
- [x] 添加热门反馈排序

**代码实现**:
```python
@action(detail=True, methods=['post'])
def vote(self, request, pk=None):
    feedback = self.get_object()
    user = request.user
    
    # 检查是否已投票
    if FeedbackVote.objects.filter(feedback=feedback, voted_by_user=user).exists():
        return Response({'error': '已投票'}, status=400)
    
    # 创建投票
    FeedbackVote.objects.create(
        feedback=feedback,
        voted_by_user=user,
        tenant=feedback.tenant
    )
    
    feedback.update_votes_count()
    
    return Response({
        'message': '投票成功',
        'votes_count': feedback.votes_count
    })

@action(detail=True, methods=['delete'])
def cancel_vote(self, request, pk=None):
    feedback = self.get_object()
    user = request.user
    
    try:
        vote = FeedbackVote.objects.get(feedback=feedback, voted_by_user=user)
        vote.delete()
        feedback.update_votes_count()
        return Response({'message': '取消投票成功'})
    except FeedbackVote.DoesNotExist:
        return Response({'error': '未投票'}, status=400)
```

**验收标准**:
- ✅ 投票功能正常
- ✅ 取消投票正常
- ✅ 防止重复投票
- ✅ 投票计数准确

---

### Day 3-4: 附件上传 + 统计

**任务清单**:
- [x] 实现附件上传API
- [x] 文件类型验证
- [x] 文件大小限制
- [x] 文件存储
- [x] 实现统计API
- [x] 各维度统计

**代码实现**:
```python
@action(detail=True, methods=['post'])
def upload_attachment(self, request, pk=None):
    feedback = self.get_object()
    file = request.FILES.get('file')
    
    # 验证文件
    if not file:
        return Response({'error': '未上传文件'}, status=400)
    
    # 检查文件大小（10MB）
    if file.size > 10 * 1024 * 1024:
        return Response({'error': '文件过大'}, status=400)
    
    # 检查文件类型
    allowed_types = ['image/jpeg', 'image/png', 'text/plain', 'application/zip']
    if file.content_type not in allowed_types:
        return Response({'error': '不支持的文件类型'}, status=400)
    
    # 创建附件
    attachment = FeedbackAttachment.objects.create(
        feedback=feedback,
        file=file,
        original_filename=file.name,
        file_size=file.size,
        mime_type=file.content_type,
        uploaded_by_user=request.user,
        tenant=feedback.tenant
    )
    
    serializer = FeedbackAttachmentSerializer(attachment)
    return Response(serializer.data, status=201)

@action(detail=False, methods=['get'])
def statistics(self, request):
    # 统计逻辑（参考API设计文档）
    pass
```

**验收标准**:
- ✅ 附件上传成功
- ✅ 文件验证正常
- ✅ 统计数据准确
- ✅ 图表显示正常

---

### Day 5: 管理后台优化

**任务清单**:
- [x] 配置Django Admin
- [x] 自定义列表显示
- [x] 添加筛选器
- [x] 添加搜索
- [x] 优化详情页面

**代码实现**:
```python
# feedbacks/admin.py

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['tracking_number', 'title', 'feedback_type', 'status', 
                   'priority', 'software', 'votes_count', 'created_at']
    list_filter = ['feedback_type', 'status', 'priority', 'software', 'created_at']
    search_fields = ['tracking_number', 'title', 'description']
    ordering = ['-created_at']
    readonly_fields = ['tracking_number', 'created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('tracking_number', 'title', 'description', 
                      'feedback_type', 'status', 'priority')
        }),
        ('关联信息', {
            'fields': ('software', 'software_version', 'license', 'tenant')
        }),
        ('提交人信息', {
            'fields': ('submitted_by_user', 'submitted_by_member', 
                      'anonymous_name', 'contact_email', 'email_verified')
        }),
        ('统计信息', {
            'fields': ('votes_count', 'replies_count', 'views_count')
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at', 'first_replied_at', 
                      'last_replied_at', 'resolved_at', 'closed_at')
        }),
    )
```

**验收标准**:
- ✅ Admin界面美观
- ✅ 列表筛选正常
- ✅ 搜索功能正常
- ✅ 详情页面完整

---

## 5. 第四阶段：测试优化 (1周)

### Day 1-2: 单元测试 + 集成测试

**任务清单**:
- [x] 编写模型测试
- [x] 编写API测试
- [x] 编写权限测试
- [x] 编写邮件测试
- [x] 代码覆盖率 > 80%

**代码实现**:
```python
# feedbacks/tests/test_models.py
class FeedbackModelTests(TestCase):
    def test_tracking_number_generation(self):
        feedback = Feedback.objects.create(...)
        self.assertIsNotNone(feedback.tracking_number)
        self.assertTrue(feedback.tracking_number.startswith('FB-'))
    
    def test_get_submitter_email(self):
        # 测试获取邮箱逻辑
        pass

# feedbacks/tests/test_api.py
class FeedbackAPITests(APITestCase):
    def test_create_feedback_anonymous(self):
        # 测试匿名创建
        pass
    
    def test_list_feedbacks_permissions(self):
        # 测试列表权限
        pass

# feedbacks/tests/test_permissions.py
# 参考权限设计文档

# feedbacks/tests/test_email.py
class EmailTests(TestCase):
    def test_send_reply_email(self):
        # 测试邮件发送
        pass
```

**执行测试**:
```bash
# 运行所有测试
python manage.py test feedbacks

# 查看覆盖率
coverage run --source='feedbacks' manage.py test feedbacks
coverage report
```

**验收标准**:
- ✅ 所有测试通过
- ✅ 代码覆盖率 > 80%
- ✅ 无明显Bug

---

### Day 3-4: 性能优化 + 压力测试

**任务清单**:
- [x] SQL查询优化
- [x] 添加缓存
- [x] 压力测试
- [x] 性能监控

**优化措施**:
```python
# 1. 使用select_related减少查询
feedbacks = Feedback.objects.select_related(
    'software', 'tenant', 'submitted_by_user'
).all()

# 2. 使用prefetch_related
feedbacks = Feedback.objects.prefetch_related(
    'replies', 'attachments', 'votes'
).all()

# 3. 添加缓存
from django.core.cache import cache

def get_hot_feedbacks(tenant_id):
    cache_key = f'hot_feedbacks_{tenant_id}'
    result = cache.get(cache_key)
    if not result:
        result = Feedback.objects.filter(
            tenant_id=tenant_id
        ).order_by('-votes_count')[:10]
        cache.set(cache_key, result, 3600)
    return result

# 4. 数据库索引（已在模型中定义）

# 5. 使用Locust进行压力测试
# locustfile.py
from locust import HttpUser, task, between

class FeedbackUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def list_feedbacks(self):
        self.client.get("/api/v1/feedbacks/")
    
    @task
    def create_feedback(self):
        self.client.post("/api/v1/feedbacks/", json={
            "title": "测试反馈",
            "description": "压力测试",
            "feedback_type": "bug",
            "software_id": 1,
            "contact_email": "test@example.com"
        })

# 运行压力测试
# locust -f locustfile.py --host=http://localhost:8000
```

**性能目标**:
- API响应时间 P95 < 500ms
- 支持100并发用户
- 数据库查询数 < 10次/请求

**验收标准**:
- ✅ 查询性能符合目标
- ✅ 压力测试通过
- ✅ 无明显性能瓶颈

---

### Day 5: 文档完善 + 部署上线

**任务清单**:
- [x] 完善API文档
- [x] 编写部署文档
- [x] 配置生产环境
- [x] 数据库备份
- [x] 正式上线

**部署步骤**:
```bash
# 1. 更新代码
git pull origin main

# 2. 安装依赖
pip install -r requirements.txt

# 3. 执行迁移
python manage.py migrate

# 4. 收集静态文件
python manage.py collectstatic --noinput

# 5. 重启服务
supervisorctl restart gunicorn
supervisorctl restart celery

# 6. 检查状态
supervisorctl status
```

**验收标准**:
- ✅ 文档完整准确
- ✅ 部署成功无错误
- ✅ 所有功能正常工作
- ✅ 邮件发送正常

---

## 6. 上线检查清单

### 6.1 功能检查
- [ ] 匿名用户可以提交反馈
- [ ] 注册用户可以提交反馈
- [ ] 邮箱验证功能正常
- [ ] 管理员可以回复反馈
- [ ] 邮件自动发送
- [ ] 状态变更功能正常
- [ ] 投票功能正常
- [ ] 附件上传功能正常
- [ ] 统计功能正常
- [ ] 权限控制正确

### 6.2 性能检查
- [ ] API响应时间符合要求
- [ ] 数据库查询优化
- [ ] 缓存正常工作
- [ ] 邮件异步发送

### 6.3 安全检查
- [ ] SQL注入防护
- [ ] XSS防护
- [ ] CSRF防护
- [ ] 敏感信息脱敏
- [ ] 权限验证严格

### 6.4 运维检查
- [ ] 日志记录完整
- [ ] 错误监控配置
- [ ] 数据备份计划
- [ ] Celery监控
- [ ] 邮件队列监控

---

## 7. 风险管理

### 7.1 技术风险

| 风险 | 影响 | 概率 | 应对措施 |
|------|------|------|---------|
| 邮件发送失败 | 高 | 中 | 重试机制 + 日志记录 |
| 性能瓶颈 | 中 | 中 | 优化查询 + 添加缓存 |
| 数据一致性 | 高 | 低 | 事务处理 + 测试覆盖 |
| 并发冲突 | 中 | 低 | 乐观锁 + 数据库锁 |

### 7.2 业务风险

| 风险 | 影响 | 概率 | 应对措施 |
|------|------|------|---------|
| 垃圾反馈 | 中 | 高 | 频率限制 + 邮箱验证 |
| 邮件被标记为垃圾 | 高 | 中 | SPF/DKIM + 退订机制 |
| 存储空间不足 | 中 | 低 | 限制附件大小 + 定期清理 |

---

## 8. 后续优化计划

### 短期（1-3个月）
- [ ] AI自动分类
- [ ] 反馈标签系统
- [ ] 反馈合并功能
- [ ] 移动端适配

### 中期（3-6个月）
- [ ] 知识库集成
- [ ] 用户满意度调查
- [ ] 多语言支持
- [ ] 高级统计图表

### 长期（6-12个月）
- [ ] 反馈社区论坛
- [ ] 第三方集成（GitHub/Jira）
- [ ] 机器学习优先级预测
- [ ] 实时通知系统

---

## 9. 相关文档

- [00_方案概述.md](./00_方案概述.md) - 方案总览
- [02_数据模型设计.md](./02_数据模型设计.md) - 数据模型
- [03_API设计.md](./03_API设计.md) - API规范
- [04_邮件系统设计.md](./04_邮件系统设计.md) - 邮件系统
- [05_权限设计.md](./05_权限设计.md) - 权限控制
- [07_技术选型.md](./07_技术选型.md) - 技术栈说明

