"""
测试脚本：验证feedbacks模块所有实体创建时都正确设置了租户ID

运行方式：
python manage.py shell < feedbacks/test_tenant_fix.py
"""

from django.contrib.auth import get_user_model
from tenants.models import Tenant
from feedbacks.models import (
    SoftwareCategory, Software, SoftwareVersion,
    Feedback, FeedbackReply, FeedbackAttachment,
    FeedbackStatusHistory, EmailTemplate
)
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

print("=" * 80)
print("开始测试feedbacks模块租户ID设置")
print("=" * 80)

# 获取或创建测试租户
tenant, _ = Tenant.objects.get_or_create(
    code='test_tenant',
    defaults={
        'name': '测试租户',
        'is_active': True
    }
)
print(f"\n✓ 使用租户: {tenant.name} (ID: {tenant.id})")

# 获取或创建测试用户
user, _ = User.objects.get_or_create(
    username='test_user',
    defaults={
        'email': 'test@example.com',
        'tenant': tenant
    }
)
print(f"✓ 使用用户: {user.username}")

test_results = []

# 测试1: SoftwareCategory
try:
    category = SoftwareCategory.objects.create(
        name="测试分类",
        code="test_cat_001",
        tenant=tenant
    )
    if category.tenant_id == tenant.id:
        test_results.append(("SoftwareCategory", True, "租户ID正确"))
    else:
        test_results.append(("SoftwareCategory", False, f"租户ID错误: 期望{tenant.id}, 实际{category.tenant_id}"))
    category.delete()
except Exception as e:
    test_results.append(("SoftwareCategory", False, str(e)))

# 测试2: Software
try:
    category = SoftwareCategory.objects.create(
        name="测试分类2",
        code="test_cat_002",
        tenant=tenant
    )
    software = Software.objects.create(
        name="测试软件",
        code="test_soft_001",
        description="测试描述",
        category=category,
        tenant=tenant
    )
    if software.tenant_id == tenant.id:
        test_results.append(("Software", True, "租户ID正确"))
    else:
        test_results.append(("Software", False, f"租户ID错误: 期望{tenant.id}, 实际{software.tenant_id}"))
    software.delete()
    category.delete()
except Exception as e:
    test_results.append(("Software", False, str(e)))

# 测试3: SoftwareVersion
try:
    category = SoftwareCategory.objects.create(
        name="测试分类3",
        code="test_cat_003",
        tenant=tenant
    )
    software = Software.objects.create(
        name="测试软件3",
        code="test_soft_003",
        description="测试描述",
        category=category,
        tenant=tenant
    )
    version = SoftwareVersion.objects.create(
        software=software,
        version="v1.0.0",
        version_code=100,
        tenant=tenant
    )
    if version.tenant_id == tenant.id:
        test_results.append(("SoftwareVersion", True, "租户ID正确"))
    else:
        test_results.append(("SoftwareVersion", False, f"租户ID错误: 期望{tenant.id}, 实际{version.tenant_id}"))
    version.delete()
    software.delete()
    category.delete()
except Exception as e:
    test_results.append(("SoftwareVersion", False, str(e)))

# 测试4: Feedback
try:
    category = SoftwareCategory.objects.create(
        name="测试分类4",
        code="test_cat_004",
        tenant=tenant
    )
    software = Software.objects.create(
        name="测试软件4",
        code="test_soft_004",
        description="测试描述",
        category=category,
        tenant=tenant
    )
    feedback = Feedback.objects.create(
        title="测试反馈",
        description="测试描述",
        software=software,
        contact_email="test@example.com",
        tenant=tenant
    )
    if feedback.tenant_id == tenant.id:
        test_results.append(("Feedback", True, "租户ID正确"))
    else:
        test_results.append(("Feedback", False, f"租户ID错误: 期望{tenant.id}, 实际{feedback.tenant_id}"))
    feedback.delete()
    software.delete()
    category.delete()
except Exception as e:
    test_results.append(("Feedback", False, str(e)))

# 测试5: FeedbackReply
try:
    category = SoftwareCategory.objects.create(
        name="测试分类5",
        code="test_cat_005",
        tenant=tenant
    )
    software = Software.objects.create(
        name="测试软件5",
        code="test_soft_005",
        description="测试描述",
        category=category,
        tenant=tenant
    )
    feedback = Feedback.objects.create(
        title="测试反馈5",
        description="测试描述",
        software=software,
        contact_email="test@example.com",
        tenant=tenant
    )
    reply = FeedbackReply.objects.create(
        feedback=feedback,
        content="测试回复",
        user=user,
        tenant=tenant
    )
    if reply.tenant_id == tenant.id:
        test_results.append(("FeedbackReply", True, "租户ID正确"))
    else:
        test_results.append(("FeedbackReply", False, f"租户ID错误: 期望{tenant.id}, 实际{reply.tenant_id}"))
    reply.delete()
    feedback.delete()
    software.delete()
    category.delete()
except Exception as e:
    test_results.append(("FeedbackReply", False, str(e)))

# 测试6: FeedbackStatusHistory
try:
    category = SoftwareCategory.objects.create(
        name="测试分类6",
        code="test_cat_006",
        tenant=tenant
    )
    software = Software.objects.create(
        name="测试软件6",
        code="test_soft_006",
        description="测试描述",
        category=category,
        tenant=tenant
    )
    feedback = Feedback.objects.create(
        title="测试反馈6",
        description="测试描述",
        software=software,
        contact_email="test@example.com",
        tenant=tenant
    )
    history = FeedbackStatusHistory.objects.create(
        feedback=feedback,
        from_status='submitted',
        to_status='reviewing',
        changed_by=user,
        tenant=tenant
    )
    if history.tenant_id == tenant.id:
        test_results.append(("FeedbackStatusHistory", True, "租户ID正确"))
    else:
        test_results.append(("FeedbackStatusHistory", False, f"租户ID错误: 期望{tenant.id}, 实际{history.tenant_id}"))
    history.delete()
    feedback.delete()
    software.delete()
    category.delete()
except Exception as e:
    test_results.append(("FeedbackStatusHistory", False, str(e)))

# 测试7: EmailTemplate
try:
    template = EmailTemplate.objects.create(
        name="测试模板",
        template_type='reply',
        subject="测试主题",
        body_html="<p>测试内容</p>",
        tenant=tenant
    )
    if template.tenant_id == tenant.id:
        test_results.append(("EmailTemplate", True, "租户ID正确"))
    else:
        test_results.append(("EmailTemplate", False, f"租户ID错误: 期望{tenant.id}, 实际{template.tenant_id}"))
    template.delete()
except Exception as e:
    test_results.append(("EmailTemplate", False, str(e)))

# 打印测试结果
print("\n" + "=" * 80)
print("测试结果汇总")
print("=" * 80)

passed = 0
failed = 0

for model_name, success, message in test_results:
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"\n{status} {model_name:25s} {message}")
    if success:
        passed += 1
    else:
        failed += 1

print("\n" + "=" * 80)
print(f"总计: {len(test_results)} 个测试")
print(f"通过: {passed} 个")
print(f"失败: {failed} 个")
print("=" * 80)

if failed == 0:
    print("\n✓ 所有测试通过！feedbacks模块租户ID设置正确。")
else:
    print(f"\n✗ 有 {failed} 个测试失败，请检查相关代码。")
