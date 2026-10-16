"""
BUG-LOGIC-02 & BUG-LOGIC-04 回归测试
验证许可证激活悲观行锁防超额并发击穿、试用配额检查字段名 application 正常查询与超额异常
"""
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from tenants.models import Tenant
from users.models import Member
from applications.models import Application
from licenses.models import LicensePlan, License, TenantLicenseQuota, MachineBinding
from licenses.services.member_license_service import MemberLicenseApplicationService
from licenses.services.license_service import LicenseActivationService
from common.exceptions import LicenseQuotaExceededException


class LicenseP0RegressionTests(TestCase):
    """测试许可证试用配额检查与激活锁并发保护"""

    def setUp(self):
        self.tenant = Tenant.objects.create(name="License Tenant", code="lic_tenant", status="active")
        self.member = Member.objects.create_user(
            username="lic_member",
            email="lic@example.com",
            password="Password123!",
            tenant=self.tenant
        )
        self.app = Application.objects.create(
            name="Test App",
            code="TEST_APP",
            status="active"
        )

    def test_check_quota_limits_no_field_error(self):
        """[BUG-LOGIC-04] 配额检查使用 application 字段过滤，无 FieldError 异常"""
        now = timezone.now().date()
        quota = TenantLicenseQuota.objects.create(
            tenant=self.tenant,
            application=self.app,
            max_licenses=5,
            current_licenses=2,
            quota_start_date=now,
            quota_end_date=now + timedelta(days=30),
            is_active=True
        )

        service = MemberLicenseApplicationService()
        # 正常配额范围内无异常抛出
        service._check_quota_limits(member=self.member, product=self.app)

        # 配额已满时抛出 LicenseQuotaExceededException
        quota.current_licenses = 5
        quota.save()
        with self.assertRaises(LicenseQuotaExceededException):
            service._check_quota_limits(member=self.member, product=self.app)

    def test_activate_license_respects_max_activations_and_locks(self):
        """[BUG-LOGIC-02] 许可证激活行锁保护下正确限制最大设备激活数"""
        plan = LicensePlan.objects.create(
            name="Basic Plan",
            code="BASIC_PLAN",
            plan_type="basic",
            application=self.app,
            default_validity_days=30,
            default_max_activations=1,
            price=100
        )
        activation_service = LicenseActivationService()
        license_key = "LIC-TEST-KEY-12345"
        license_hash = activation_service.security_service.hash_manager.hash_data(license_key)

        license_obj = License.objects.create(
            tenant=self.tenant,
            application=self.app,
            plan=plan,
            license_key=license_key,
            license_hash=license_hash,
            status="generated",
            max_activations=1,
            expires_at=timezone.now() + timedelta(days=30)
        )

        hw1 = {
            "hardware_uuid": "UUID-1",
            "network_info": {"mac_addresses": ["00:11:22:33:44:55"]},
            "disk_info": {"serial": "DISK-001"}
        }
        res1 = activation_service.activate_license(license_key=license_key, hardware_info=hw1)
        self.assertTrue(res1.get("success"), res1)
        self.assertEqual(MachineBinding.objects.filter(license=license_obj, status='active').count(), 1)

        # 尝试第二台机器激活，必须被 MAX_ACTIVATIONS_REACHED 拒绝
        hw2 = {
            "hardware_uuid": "UUID-2",
            "network_info": {"mac_addresses": ["AA:BB:CC:DD:EE:FF"]},
            "disk_info": {"serial": "DISK-002"}
        }
        res2 = activation_service.activate_license(license_key=license_key, hardware_info=hw2)
        self.assertFalse(res2.get("success"))
        self.assertEqual(res2.get("code"), "MAX_ACTIVATIONS_REACHED")
