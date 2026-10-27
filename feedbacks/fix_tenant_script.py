"""
测试脚本：验证feedbacks模块所有实体创建时都正确设置了租户ID

运行方式：
python manage.py shell < feedbacks/fix_tenant_script.py
或在 shell 中：
from feedbacks.fix_tenant_script import run_tenant_fix_verification
run_tenant_fix_verification()
"""

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from tenants.models import Tenant
from applications.models import Application
from feedbacks.models import (
    Feedback, FeedbackReply, FeedbackAttachment,
    FeedbackStatusHistory, EmailTemplate
)

User = get_user_model()


def run_tenant_fix_verification():
    print("=" * 80)
    print("开始测试feedbacks模块租户ID设置")
    print("=" * 80)

    # 获取或创建测试租户
    tenant, _ = Tenant.objects.get_or_create(
        code='test_tenant',
        defaults={
            'name': '测试租户',
            'status': 'active'
        }
    )
    print(f"\n[OK] 使用租户: {tenant.name} (ID: {tenant.id})")

    # 获取或创建测试用户
    user, _ = User.objects.get_or_create(
        username='test_user',
        defaults={
            'email': 'test@example.com',
            'tenant': tenant
        }
    )
    print(f"[OK] 使用用户: {user.username}")

    test_results = []

    # 测试1: Application
    try:
        application = Application.objects.create(
            name="测试应用",
            code="test_app_001",
            tenant=tenant
        )
        if application.tenant_id == tenant.id:
            test_results.append(("Application", True, "租户ID正确"))
        else:
            test_results.append(("Application", False, f"租户ID错误: 期望{tenant.id}, 实际{application.tenant_id}"))
        application.delete()
    except Exception as e:
        test_results.append(("Application", False, str(e)))

    # 测试2: Feedback
    try:
        application = Application.objects.create(
            name="测试应用2",
            code="test_app_002",
            tenant=tenant
        )
        feedback = Feedback.objects.create(
            title="测试反馈",
            description="测试描述",
            application=application,
            contact_email="test@example.com",
            tenant=tenant
        )
        if feedback.tenant_id == tenant.id:
            test_results.append(("Feedback", True, "租户ID正确"))
        else:
            test_results.append(("Feedback", False, f"租户ID错误: 期望{tenant.id}, 实际{feedback.tenant_id}"))
        feedback.delete()
        application.delete()
    except Exception as e:
        test_results.append(("Feedback", False, str(e)))

    # 测试3: FeedbackReply
    try:
        application = Application.objects.create(
            name="测试应用3",
            code="test_app_003",
            tenant=tenant
        )
        feedback = Feedback.objects.create(
            title="测试反馈3",
            description="测试描述",
            application=application,
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
        application.delete()
    except Exception as e:
        test_results.append(("FeedbackReply", False, str(e)))

    # 测试4: FeedbackStatusHistory
    try:
        application = Application.objects.create(
            name="测试应用4",
            code="test_app_004",
            tenant=tenant
        )
        feedback = Feedback.objects.create(
            title="测试反馈4",
            description="测试描述",
            application=application,
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
        application.delete()
    except Exception as e:
        test_results.append(("FeedbackStatusHistory", False, str(e)))

    # 测试5: FeedbackAttachment
    try:
        application = Application.objects.create(
            name="测试应用5",
            code="test_app_005",
            tenant=tenant
        )
        feedback = Feedback.objects.create(
            title="测试反馈5",
            description="测试描述",
            application=application,
            contact_email="test@example.com",
            tenant=tenant
        )
        dummy_file = SimpleUploadedFile("test.txt", b"dummy content", content_type="text/plain")
        attachment = FeedbackAttachment.objects.create(
            feedback=feedback,
            file=dummy_file,
            filename="test.txt",
            file_size=len(b"dummy content"),
            mime_type="text/plain",
            tenant=tenant
        )
        if attachment.tenant_id == tenant.id:
            test_results.append(("FeedbackAttachment", True, "租户ID正确"))
        else:
            test_results.append(("FeedbackAttachment", False, f"租户ID错误: 期望{tenant.id}, 实际{attachment.tenant_id}"))
        attachment.delete()
        feedback.delete()
        application.delete()
    except Exception as e:
        test_results.append(("FeedbackAttachment", False, str(e)))

    # 测试6: EmailTemplate
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
        status = "[PASS]" if success else "[FAIL]"
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
        print("\n[OK] 所有测试通过！feedbacks模块租户ID设置正确。")
    else:
        print(f"\n[FAIL] 有 {failed} 个测试失败，请检查相关代码。")

    return passed, failed


if __name__ == '__main__':
    run_tenant_fix_verification()
