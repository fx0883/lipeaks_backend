# 用户反馈系统邮件系统设计

## 文档信息
- **版本**: v1.0
- **创建日期**: 2025-10-22
- **邮件服务**: QQ邮箱 SMTP
- **异步任务**: Celery

## 1. 邮件系统概述

### 1.1 设计目标

- ✅ **可靠性**: 邮件发送成功率 > 99%
- ✅ **异步处理**: 不阻塞API响应
- ✅ **失败重试**: 自动重试机制
- ✅ **完整日志**: 追踪所有邮件发送
- ✅ **模板化**: 可自定义邮件模板
- ✅ **退订机制**: 用户可选择退订

### 1.2 邮件类型

| 类型 | 说明 | 触发时机 | 接收对象 |
|------|------|---------|---------|
| verification | 邮箱验证 | 匿名用户提交反馈 | 提交人 |
| reply | 反馈回复 | 管理员添加官方回复 | 提交人 |
| status_change | 状态变更 | 反馈状态改变 | 提交人 |
| reminder | 提醒通知 | 反馈长时间未处理 | 管理员 |

---

## 2. 邮件发送流程

### 2.1 总体流程图

```
事件触发
    ↓
获取收件人邮箱
    ├─ 注册用户：使用账号邮箱
    └─ 匿名用户：使用提交时的邮箱
    ↓
检查是否可发送
    ├─ 无邮箱：跳过
    ├─ 邮箱未验证：验证邮件外跳过
    ├─ 用户退订：跳过
    └─ 内部备注：跳过
    ↓
生成邮件内容
    ├─ 获取邮件模板
    ├─ 准备变量上下文
    └─ 渲染模板
    ↓
创建异步任务
    ↓
Celery任务队列
    ↓
执行邮件发送
    ├─ 调用SMTP发送
    ├─ 记录邮件日志
    └─ 更新发送状态
    ↓
发送成功？
    ├─ 是：更新email_sent=True
    └─ 否：
        ├─ 记录错误信息
        ├─ 重试次数+1
        └─ 重试次数<3？
            ├─ 是：5分钟后重试
            └─ 否：标记失败
```

### 2.2 收件人邮箱获取逻辑

```python
def get_recipient_email(feedback):
    """获取收件人邮箱"""
    
    # 1. 优先使用User邮箱
    if feedback.submitted_by_user:
        return feedback.submitted_by_user.email
    
    # 2. 其次使用Member邮箱
    if feedback.submitted_by_member:
        return feedback.submitted_by_member.email
    
    # 3. 最后使用匿名用户邮箱
    if feedback.contact_email:
        # 检查邮箱是否已验证（验证邮件除外）
        if feedback.email_verified or email_type == 'verification':
            return feedback.contact_email
    
    return None
```

---

## 3. 邮件模板系统

### 3.1 模板结构

每个邮件模板包含：
- **主题模板**: 支持变量替换
- **正文模板**: HTML格式，支持变量替换
- **变量列表**: 模板中可用的变量

### 3.2 支持的变量

```python
# 通用变量
{tenant_name}          # 租户名称
{tenant_logo}          # 租户Logo URL
{site_url}             # 网站URL
{current_year}         # 当前年份

# 反馈相关变量
{feedback_id}          # 反馈ID
{tracking_number}      # 追踪编号
{feedback_title}       # 反馈标题
{feedback_description} # 反馈描述（截断）
{feedback_type}        # 反馈类型
{status_display}       # 状态显示名
{priority_display}     # 优先级显示名
{feedback_url}         # 反馈详情URL

# 软件相关变量
{software_name}        # 软件名称
{software_version}     # 软件版本
{software_logo}        # 软件Logo URL

# 用户相关变量
{submitter_name}       # 提交人名称
{recipient_email}      # 收件人邮箱

# 回复相关变量
{reply_content}        # 回复内容
{replier_name}         # 回复人名称
{reply_time}           # 回复时间

# 状态变更相关变量
{old_status}           # 原状态
{new_status}           # 新状态
{change_reason}        # 变更原因

# 操作链接
{verification_url}     # 邮箱验证链接
{unsubscribe_url}      # 退订链接
```

### 3.3 默认模板

#### 3.3.1 邮箱验证模板

**主题**:
```
[{software_name}] 请验证您的邮箱
```

**正文**:
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #4CAF50; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background: #f9f9f9; }
        .button { display: inline-block; padding: 12px 24px; background: #4CAF50; 
                  color: white; text-decoration: none; border-radius: 4px; }
        .footer { text-align: center; padding: 20px; font-size: 12px; color: #999; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>欢迎使用 {software_name}</h1>
        </div>
        
        <div class="content">
            <h2>请验证您的邮箱</h2>
            
            <p>尊敬的用户，</p>
            
            <p>感谢您提交反馈。为了确保我们能够及时回复您，请点击下方按钮验证您的邮箱地址：</p>
            
            <p style="text-align: center; margin: 30px 0;">
                <a href="{verification_url}" class="button">验证邮箱</a>
            </p>
            
            <p>或复制以下链接到浏览器：</p>
            <p><a href="{verification_url}">{verification_url}</a></p>
            
            <p>此验证链接将在24小时后失效。</p>
            
            <hr>
            
            <p><strong>您的反馈信息：</strong></p>
            <ul>
                <li>追踪编号：{tracking_number}</li>
                <li>反馈标题：{feedback_title}</li>
                <li>提交时间：{created_at}</li>
            </ul>
        </div>
        
        <div class="footer">
            <p>此邮件由系统自动发送，请勿直接回复。</p>
            <p>&copy; {current_year} {tenant_name}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
```

#### 3.3.2 反馈回复模板

**主题**:
```
[{software_name}] 您的反馈已收到回复
```

**正文**:
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        /* 样式与验证邮件类似 */
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{software_name} 技术支持</h1>
        </div>
        
        <div class="content">
            <h2>您的反馈已收到回复</h2>
            
            <p>尊敬的 {submitter_name}，</p>
            
            <p>您提交的反馈已收到我们的回复：</p>
            
            <div style="background: white; padding: 15px; border-left: 4px solid #4CAF50;">
                <p><strong>反馈编号：</strong>{tracking_number}</p>
                <p><strong>反馈主题：</strong>{feedback_title}</p>
                <p><strong>当前状态：</strong>{status_display}</p>
                <p><strong>回复时间：</strong>{reply_time}</p>
            </div>
            
            <hr>
            
            <h3>官方回复：</h3>
            <div style="background: white; padding: 15px; border-radius: 4px;">
                {reply_content}
            </div>
            
            <hr>
            
            <p style="text-align: center; margin: 30px 0;">
                <a href="{feedback_url}" class="button">查看完整反馈</a>
            </p>
            
            <p style="font-size: 12px; color: #666;">
                如不希望继续接收此类邮件，请点击 
                <a href="{unsubscribe_url}">退订</a>
            </p>
        </div>
        
        <div class="footer">
            <p>此邮件由系统自动发送，如需进一步咨询，请访问我们的支持页面。</p>
            <p>&copy; {current_year} {tenant_name}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
```

#### 3.3.3 状态变更模板

**主题**:
```
[{software_name}] 您的反馈状态已更新
```

**正文**:
```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        /* 样式类似 */
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{software_name} 反馈追踪</h1>
        </div>
        
        <div class="content">
            <h2>反馈状态已更新</h2>
            
            <p>尊敬的 {submitter_name}，</p>
            
            <p>您的反馈状态已更新：</p>
            
            <div style="background: white; padding: 15px; border-left: 4px solid #2196F3;">
                <p><strong>反馈编号：</strong>{tracking_number}</p>
                <p><strong>反馈主题：</strong>{feedback_title}</p>
                <p><strong>原状态：</strong>{old_status}</p>
                <p><strong>新状态：</strong>{new_status}</p>
            </div>
            
            <hr>
            
            <p><strong>变更说明：</strong></p>
            <div style="background: white; padding: 15px; border-radius: 4px;">
                {change_reason}
            </div>
            
            <hr>
            
            <p style="text-align: center; margin: 30px 0;">
                <a href="{feedback_url}" class="button">查看详情</a>
            </p>
            
            <p style="font-size: 12px; color: #666;">
                如不希望继续接收此类邮件，请点击 
                <a href="{unsubscribe_url}">退订</a>
            </p>
        </div>
        
        <div class="footer">
            <p>&copy; {current_year} {tenant_name}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
```

---

## 4. 异步任务实现

### 4.1 Celery配置

```python
# settings.py

# Celery配置
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# 任务路由
CELERY_TASK_ROUTES = {
    'feedbacks.tasks.email_tasks.*': {'queue': 'email'},
}

# 重试配置
CELERY_TASK_MAX_RETRIES = 3
CELERY_TASK_DEFAULT_RETRY_DELAY = 300  # 5分钟
```

### 4.2 邮件发送任务

```python
# feedbacks/tasks/email_tasks.py

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_feedback_reply_email(self, reply_id):
    """
    发送反馈回复邮件
    
    Args:
        reply_id: FeedbackReply ID
    """
    from feedbacks.models import FeedbackReply, FeedbackEmailLog
    from feedbacks.services.email_service import EmailService
    
    try:
        # 获取回复对象
        reply = FeedbackReply.objects.select_related(
            'feedback',
            'feedback__software',
            'feedback__tenant',
            'replied_by_user'
        ).get(id=reply_id)
        
        feedback = reply.feedback
        
        # 检查是否应该发送邮件
        if reply.is_internal:
            logger.info(f"回复 {reply_id} 是内部备注，跳过邮件发送")
            return
        
        # 获取收件人邮箱
        recipient_email = feedback.get_submitter_email()
        if not recipient_email:
            logger.warning(f"反馈 {feedback.id} 无收件人邮箱，跳过邮件发送")
            reply.email_error = "无收件人邮箱"
            reply.save(update_fields=['email_error'])
            return
        
        # 检查邮箱验证状态（匿名用户）
        if not feedback.submitted_by_user and not feedback.submitted_by_member:
            if not feedback.email_verified:
                logger.warning(f"反馈 {feedback.id} 邮箱未验证，跳过邮件发送")
                return
        
        # 检查是否退订
        if not feedback.email_notification_enabled:
            logger.info(f"反馈 {feedback.id} 已退订邮件通知")
            return
        
        # 使用EmailService发送邮件
        email_service = EmailService()
        success = email_service.send_reply_email(reply)
        
        if success:
            # 更新发送状态
            reply.email_sent = True
            reply.email_sent_at = timezone.now()
            reply.email_retry_count = 0
            reply.save(update_fields=['email_sent', 'email_sent_at', 'email_retry_count'])
            
            logger.info(f"回复 {reply_id} 邮件发送成功")
        else:
            raise Exception("邮件发送失败")
            
    except FeedbackReply.DoesNotExist:
        logger.error(f"回复 {reply_id} 不存在")
        return
    
    except Exception as e:
        logger.error(f"发送回复邮件失败: {str(e)}", exc_info=True)
        
        # 更新重试次数
        reply.email_retry_count += 1
        reply.email_error = str(e)
        reply.save(update_fields=['email_retry_count', 'email_error'])
        
        # 判断是否需要重试
        if reply.email_retry_count < 3:
            # 5分钟后重试
            logger.info(f"将在5分钟后重试发送邮件 (第{reply.email_retry_count}次)")
            raise self.retry(exc=e, countdown=300)
        else:
            logger.error(f"邮件发送失败，已达最大重试次数")


@shared_task(bind=True, max_retries=3)
def send_status_change_email(self, history_id):
    """
    发送状态变更邮件
    
    Args:
        history_id: FeedbackStatusHistory ID
    """
    from feedbacks.models import FeedbackStatusHistory
    from feedbacks.services.email_service import EmailService
    
    try:
        history = FeedbackStatusHistory.objects.select_related(
            'feedback',
            'feedback__software',
            'feedback__tenant'
        ).get(id=history_id)
        
        feedback = history.feedback
        
        # 获取收件人邮箱
        recipient_email = feedback.get_submitter_email()
        if not recipient_email:
            return
        
        # 检查是否退订
        if not feedback.email_notification_enabled:
            return
        
        # 发送邮件
        email_service = EmailService()
        success = email_service.send_status_change_email(history)
        
        if success:
            history.email_sent = True
            history.save(update_fields=['email_sent'])
            logger.info(f"状态变更邮件发送成功: {history_id}")
        else:
            raise Exception("邮件发送失败")
            
    except FeedbackStatusHistory.DoesNotExist:
        logger.error(f"状态历史 {history_id} 不存在")
        return
    
    except Exception as e:
        logger.error(f"发送状态变更邮件失败: {str(e)}", exc_info=True)
        
        # 重试
        if self.request.retries < 3:
            raise self.retry(exc=e, countdown=300)


@shared_task
def send_verification_email(feedback_id):
    """
    发送邮箱验证邮件
    
    Args:
        feedback_id: Feedback ID
    """
    from feedbacks.models import Feedback
    from feedbacks.services.email_service import EmailService
    
    try:
        feedback = Feedback.objects.select_related(
            'software',
            'tenant'
        ).get(id=feedback_id)
        
        # 只给匿名用户发送验证邮件
        if feedback.submitted_by_user or feedback.submitted_by_member:
            logger.info(f"反馈 {feedback_id} 不是匿名用户，跳过验证邮件")
            return
        
        if not feedback.contact_email:
            logger.warning(f"反馈 {feedback_id} 无邮箱，无法发送验证邮件")
            return
        
        # 发送邮件
        email_service = EmailService()
        success = email_service.send_verification_email(feedback)
        
        if success:
            # 更新发送时间
            feedback.email_verification_sent_at = timezone.now()
            feedback.save(update_fields=['email_verification_sent_at'])
            logger.info(f"验证邮件发送成功: {feedback_id}")
        
    except Feedback.DoesNotExist:
        logger.error(f"反馈 {feedback_id} 不存在")
    
    except Exception as e:
        logger.error(f"发送验证邮件失败: {str(e)}", exc_info=True)
```

### 4.3 邮件服务类

```python
# feedbacks/services/email_service.py

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class EmailService:
    """邮件发送服务"""
    
    def __init__(self):
        self.from_email = settings.DEFAULT_FROM_EMAIL
    
    def send_reply_email(self, reply):
        """发送回复邮件"""
        feedback = reply.feedback
        
        # 获取邮件模板
        from feedbacks.models import EmailTemplate
        template = EmailTemplate.get_template(
            tenant=feedback.tenant,
            template_type='reply'
        )
        
        if not template:
            logger.error("未找到回复邮件模板")
            return False
        
        # 准备变量上下文
        context = {
            'tenant_name': feedback.tenant.name,
            'software_name': feedback.software.name,
            'tracking_number': feedback.tracking_number,
            'feedback_title': feedback.title,
            'feedback_description': feedback.description[:100] + '...',
            'status_display': feedback.get_status_display(),
            'reply_content': reply.content,
            'replier_name': reply.get_replier_name(),
            'reply_time': reply.created_at.strftime('%Y-%m-%d %H:%M'),
            'submitter_name': feedback.get_submitter_name(),
            'feedback_url': f"{settings.FRONTEND_URL}/feedbacks/{feedback.id}",
            'unsubscribe_url': self._generate_unsubscribe_url(feedback),
            'current_year': timezone.now().year,
        }
        
        # 渲染模板
        subject, body = template.render(context)
        
        # 发送邮件
        recipient = feedback.get_submitter_email()
        success = self._send_email(
            subject=subject,
            body=body,
            recipient=recipient,
            feedback=feedback,
            email_type='reply',
            reply=reply
        )
        
        return success
    
    def send_status_change_email(self, history):
        """发送状态变更邮件"""
        feedback = history.feedback
        
        # 获取邮件模板
        from feedbacks.models import EmailTemplate
        template = EmailTemplate.get_template(
            tenant=feedback.tenant,
            template_type='status_change'
        )
        
        if not template:
            logger.error("未找到状态变更邮件模板")
            return False
        
        # 准备变量上下文
        context = {
            'tenant_name': feedback.tenant.name,
            'software_name': feedback.software.name,
            'tracking_number': feedback.tracking_number,
            'feedback_title': feedback.title,
            'old_status': history.get_old_status_display(),
            'new_status': history.get_new_status_display(),
            'change_reason': history.reason or '无',
            'submitter_name': feedback.get_submitter_name(),
            'feedback_url': f"{settings.FRONTEND_URL}/feedbacks/{feedback.id}",
            'unsubscribe_url': self._generate_unsubscribe_url(feedback),
            'current_year': timezone.now().year,
        }
        
        # 渲染模板
        subject, body = template.render(context)
        
        # 发送邮件
        recipient = feedback.get_submitter_email()
        success = self._send_email(
            subject=subject,
            body=body,
            recipient=recipient,
            feedback=feedback,
            email_type='status_change',
            status_history=history
        )
        
        return success
    
    def send_verification_email(self, feedback):
        """发送验证邮件"""
        # 生成验证token
        import uuid
        token = str(uuid.uuid4())
        feedback.email_verification_token = token
        feedback.save(update_fields=['email_verification_token'])
        
        # 获取邮件模板
        from feedbacks.models import EmailTemplate
        template = EmailTemplate.get_template(
            tenant=feedback.tenant,
            template_type='verification'
        )
        
        if not template:
            logger.error("未找到验证邮件模板")
            return False
        
        # 准备变量上下文
        context = {
            'tenant_name': feedback.tenant.name,
            'software_name': feedback.software.name,
            'tracking_number': feedback.tracking_number,
            'feedback_title': feedback.title,
            'verification_url': f"{settings.FRONTEND_URL}/verify-email?token={token}",
            'created_at': feedback.created_at.strftime('%Y-%m-%d %H:%M'),
            'current_year': timezone.now().year,
        }
        
        # 渲染模板
        subject, body = template.render(context)
        
        # 发送邮件
        success = self._send_email(
            subject=subject,
            body=body,
            recipient=feedback.contact_email,
            feedback=feedback,
            email_type='verification'
        )
        
        return success
    
    def _send_email(self, subject, body, recipient, feedback, email_type, reply=None, status_history=None):
        """
        实际发送邮件
        
        Args:
            subject: 邮件主题
            body: 邮件正文(HTML)
            recipient: 收件人邮箱
            feedback: Feedback对象
            email_type: 邮件类型
            reply: FeedbackReply对象(可选)
            status_history: FeedbackStatusHistory对象(可选)
        
        Returns:
            bool: 是否发送成功
        """
        from feedbacks.models import FeedbackEmailLog
        
        try:
            # 创建邮件对象
            email = EmailMultiAlternatives(
                subject=subject,
                body=body,
                from_email=self.from_email,
                to=[recipient]
            )
            email.attach_alternative(body, "text/html")
            
            # 发送邮件
            email.send()
            
            # 记录邮件日志
            FeedbackEmailLog.objects.create(
                feedback=feedback,
                reply=reply,
                status_history=status_history,
                email_type=email_type,
                recipient_email=recipient,
                subject=subject,
                body=body,
                status='sent',
                sent_at=timezone.now()
            )
            
            return True
            
        except Exception as e:
            logger.error(f"邮件发送失败: {str(e)}", exc_info=True)
            
            # 记录失败日志
            FeedbackEmailLog.objects.create(
                feedback=feedback,
                reply=reply,
                status_history=status_history,
                email_type=email_type,
                recipient_email=recipient,
                subject=subject,
                body=body,
                status='failed',
                error_message=str(e),
                sent_at=timezone.now()
            )
            
            return False
    
    def _generate_unsubscribe_url(self, feedback):
        """生成退订URL"""
        import hashlib
        
        # 生成退订token
        raw = f"{feedback.id}:{feedback.get_submitter_email()}:{settings.SECRET_KEY}"
        token = hashlib.sha256(raw.encode()).hexdigest()
        
        return f"{settings.FRONTEND_URL}/unsubscribe?token={token}&feedback_id={feedback.id}"
```

---

## 5. 邮件模板管理

### 5.1 模板CRUD

```python
# feedbacks/views/template_views.py

from rest_framework import viewsets
from feedbacks.models import EmailTemplate
from feedbacks.serializers import EmailTemplateSerializer

class EmailTemplateViewSet(viewsets.ModelViewSet):
    """邮件模板管理"""
    
    queryset = EmailTemplate.objects.all()
    serializer_class = EmailTemplateSerializer
    
    def get_queryset(self):
        """只返回当前租户的模板"""
        user = self.request.user
        return EmailTemplate.objects.filter(tenant=user.tenant)
```

### 5.2 模板预览

```python
@action(detail=True, methods=['post'])
def preview(self, request, pk=None):
    """预览邮件模板"""
    template = self.get_object()
    
    # 使用示例数据渲染
    context = {
        'tenant_name': '示例租户',
        'software_name': '示例软件',
        'tracking_number': 'FB-20251022-001',
        'feedback_title': '示例反馈标题',
        'reply_content': '这是一个示例回复内容',
        # ... 其他变量
    }
    
    subject, body = template.render(context)
    
    return Response({
        'subject': subject,
        'body': body
    })
```

---

## 6. 邮件监控与追踪

### 6.1 发送统计

```python
# 统计各类型邮件发送情况
from feedbacks.models import FeedbackEmailLog
from django.db.models import Count

stats = FeedbackEmailLog.objects.values('email_type', 'status').annotate(
    count=Count('id')
)

# 输出示例:
# [
#     {'email_type': 'reply', 'status': 'sent', 'count': 150},
#     {'email_type': 'reply', 'status': 'failed', 'count': 5},
#     {'email_type': 'verification', 'status': 'sent', 'count': 80},
#     ...
# ]
```

### 6.2 失败分析

```python
# 分析邮件发送失败原因
failed_logs = FeedbackEmailLog.objects.filter(
    status='failed'
).values('error_message').annotate(
    count=Count('id')
).order_by('-count')
```

---

## 7. 最佳实践

### 7.1 避免被标记为垃圾邮件

1. **使用真实的发件人地址**
2. **添加退订链接**
3. **避免使用垃圾邮件触发词**
4. **保持合理的发送频率**
5. **使用SPF、DKIM认证**

### 7.2 提高送达率

1. **使用可靠的SMTP服务**
2. **实施失败重试机制**
3. **监控邮件退信**
4. **定期清理无效邮箱**

### 7.3 性能优化

1. **异步发送，不阻塞主流程**
2. **批量发送使用Celery的group**
3. **使用连接池**
4. **限制发送频率**

---

## 8. 相关文档

- [02_数据模型设计.md](./02_数据模型设计.md) - 邮件日志模型
- [03_API设计.md](./03_API设计.md) - 邮件相关API
- [06_实施计划.md](./06_实施计划.md) - 邮件系统实施步骤

