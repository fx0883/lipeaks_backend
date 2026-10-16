"""
BUG-LOGIC-02 对抗性并发挑战测试套件
验证:
1. 单机版许可证 (max_activations=1) 双线程并发冲撞:
   两线程同时对同一许可证发起激活，验证悲观锁 License.objects.select_for_update() 能否
   确保严格只有 1 台机器成功绑定，另 1 请求被拦截并返回 MAX_ACTIVATIONS_REACHED，绑定数严格为 1。
2. 单机版许可证 (max_activations=1) 5 线程高并发冲撞:
   5 台不同硬件机器同时发起激活，严格仅有 1 台成功，其余 4 台全部被拦截返回 MAX_ACTIVATIONS_REACHED。
3. 多机版许可证 (max_activations=2) 5 线程高并发冲撞:
   5 台不同硬件机器同时发起激活，严格仅有 2 台成功，其余 3 台全部被拦截返回 MAX_ACTIVATIONS_REACHED。
"""
import os
import time
import uuid
import shutil
import tempfile
import threading
from datetime import timedelta
from unittest import TestCase
from django.conf import settings
from django.core.management import call_command
from django.db import connection
from django.utils import timezone
from tenants.models import Tenant
from users.models import Member
from applications.models import Application
from licenses.models import LicensePlan, License, MachineBinding
from licenses.services.license_service import LicenseActivationService


class LicenseConcurrencyChallengeTests(TestCase):
    """对抗实测: LicenseActivationService 悲观行锁防超额并发击穿"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.temp_dir = tempfile.mkdtemp()
        cls.db_path = os.path.join(cls.temp_dir, 'lic_challenge_test.sqlite3')
        cls.orig_db_name = settings.DATABASES['default']['NAME']
        settings.DATABASES['default']['NAME'] = cls.db_path
        connection.close()

        with connection.cursor() as cursor:
            cursor.execute("PRAGMA journal_mode = WAL;")
            cursor.execute("PRAGMA busy_timeout = 5000;")

        call_command('migrate', run_syncdb=True, verbosity=0)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        connection.close()
        settings.DATABASES['default']['NAME'] = cls.orig_db_name
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def setUp(self):
        super().setUp()
        uid = uuid.uuid4().hex[:8]
        self.tenant = Tenant.objects.create(name=f"Lic Tenant {uid}", code=f"c_lic_{uid}", status="active")
        self.app = Application.objects.create(name=f"Lic App {uid}", code=f"APP_{uid}", status="active")
        self.service = LicenseActivationService()

    def _create_license(self, max_activations=1):
        uid = uuid.uuid4().hex[:8]
        plan = LicensePlan.objects.create(
            name=f"Plan {uid}",
            code=f"PLAN_{uid}",
            plan_type="basic",
            application=self.app,
            default_validity_days=30,
            default_max_activations=max_activations,
            price=100
        )
        license_key = f"KEY-CONCURRENCY-{uid}"
        license_hash = self.service.security_service.hash_manager.hash_data(license_key)
        license_obj = License.objects.create(
            tenant=self.tenant,
            application=self.app,
            plan=plan,
            license_key=license_key,
            license_hash=license_hash,
            status="generated",
            max_activations=max_activations,
            expires_at=timezone.now() + timedelta(days=30)
        )
        return license_key, license_obj

    def test_concurrent_activate_single_machine_two_threads(self):
        """
        [BUG-LOGIC-02 并发挑战 1: 双线程并发激活单机版]
        模拟单机版许可证（max_activations=1），多线程同时对未激活的 license 发起激活请求。
        严格验证:
        - 仅有 1 个请求能成功绑定
        - 另 1 个请求被拦截并返回 MAX_ACTIVATIONS_REACHED
        - 数据库中 MachineBinding active 计数严格为 1
        """
        license_key, license_obj = self._create_license(max_activations=1)
        barrier = threading.Barrier(2)
        success_list = []
        max_activation_list = []
        other_list = []

        def worker(idx):
            hw = {
                "hardware_uuid": f"UUID-SINGLE-2T-{idx}",
                "network_info": {"mac_addresses": [f"00:11:22:33:44:{idx:02x}"]},
                "disk_info": {"serial": f"DISK-SINGLE-2T-{idx}"}
            }
            barrier.wait()
            for attempt in range(25):
                try:
                    res = self.service.activate_license(license_key=license_key, hardware_info=hw)
                    if res.get("success"):
                        success_list.append((idx, res))
                        break
                    elif res.get("code") == "MAX_ACTIVATIONS_REACHED":
                        max_activation_list.append((idx, res))
                        break
                    elif "database is locked" in res.get("error", ""):
                        time.sleep(0.05)
                        continue
                    else:
                        other_list.append((idx, res))
                        break
                except Exception as ex:
                    if "database is locked" in str(ex):
                        time.sleep(0.05)
                        continue
                    other_list.append((idx, ex))
                    break
            connection.close()

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(other_list), 0, f"不应出现未预期的错误: {other_list}")
        self.assertEqual(len(success_list), 1, f"严格仅允许 1 台机器激活成功，实际成功数: {len(success_list)}")
        self.assertEqual(len(max_activation_list), 1, f"严格拦截 1 台超额机器，实际拦截数: {len(max_activation_list)}")

        active_count = MachineBinding.objects.filter(license=license_obj, status='active').count()
        self.assertEqual(active_count, 1, f"数据库有效机器绑定必须严格等于 1，实际为: {active_count}")

    def test_concurrent_activate_single_machine_five_threads(self):
        """
        [BUG-LOGIC-02 并发挑战 2: 5 线程高并发冲撞单机版]
        5 台不同硬件机器同时激活 max_activations=1 的同一单机许可证。
        严格验证:
        - 仅 1 台成功
        - 4 台全部被拦截返回 MAX_ACTIVATIONS_REACHED
        - 数据库绑定数严格等于 1，绝无法突破最大激活数
        """
        license_key, license_obj = self._create_license(max_activations=1)
        num_threads = 5
        barrier = threading.Barrier(num_threads)
        success_list = []
        max_activation_list = []
        other_list = []

        def worker(idx):
            hw = {
                "hardware_uuid": f"UUID-SINGLE-5T-{idx}",
                "network_info": {"mac_addresses": [f"00:11:22:33:55:{idx:02x}"]},
                "disk_info": {"serial": f"DISK-SINGLE-5T-{idx}"}
            }
            barrier.wait()
            for attempt in range(25):
                try:
                    res = self.service.activate_license(license_key=license_key, hardware_info=hw)
                    if res.get("success"):
                        success_list.append((idx, res))
                        break
                    elif res.get("code") == "MAX_ACTIVATIONS_REACHED":
                        max_activation_list.append((idx, res))
                        break
                    elif "database is locked" in res.get("error", ""):
                        time.sleep(0.05)
                        continue
                    else:
                        other_list.append((idx, res))
                        break
                except Exception as ex:
                    if "database is locked" in str(ex):
                        time.sleep(0.05)
                        continue
                    other_list.append((idx, ex))
                    break
            connection.close()

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(other_list), 0, f"不应出现未预期的错误: {other_list}")
        self.assertEqual(len(success_list), 1, f"严格仅允许 1 台机器激活成功，实际成功数: {len(success_list)}")
        self.assertEqual(len(max_activation_list), 4, f"严格拦截 4 台超额机器，实际拦截数: {len(max_activation_list)}")

        active_count = MachineBinding.objects.filter(license=license_obj, status='active').count()
        self.assertEqual(active_count, 1, f"数据库有效机器绑定必须严格等于 1，实际为: {active_count}")

    def test_concurrent_activate_multi_machine_five_threads(self):
        """
        [BUG-LOGIC-02 并发挑战 3: 5 线程并发冲撞双机版]
        5 台不同硬件机器同时激活 max_activations=2 的许可证。
        严格验证:
        - 严格仅 2 台成功
        - 另外 3 台全部被拦截返回 MAX_ACTIVATIONS_REACHED
        - 数据库绑定数严格等于 2
        """
        license_key, license_obj = self._create_license(max_activations=2)
        num_threads = 5
        barrier = threading.Barrier(num_threads)
        success_list = []
        max_activation_list = []
        other_list = []

        def worker(idx):
            hw = {
                "hardware_uuid": f"UUID-DUAL-5T-{idx}",
                "network_info": {"mac_addresses": [f"00:11:22:33:66:{idx:02x}"]},
                "disk_info": {"serial": f"DISK-DUAL-5T-{idx}"}
            }
            barrier.wait()
            for attempt in range(25):
                try:
                    res = self.service.activate_license(license_key=license_key, hardware_info=hw)
                    if res.get("success"):
                        success_list.append((idx, res))
                        break
                    elif res.get("code") == "MAX_ACTIVATIONS_REACHED":
                        max_activation_list.append((idx, res))
                        break
                    elif "database is locked" in res.get("error", ""):
                        time.sleep(0.05)
                        continue
                    else:
                        other_list.append((idx, res))
                        break
                except Exception as ex:
                    if "database is locked" in str(ex):
                        time.sleep(0.05)
                        continue
                    other_list.append((idx, ex))
                    break
            connection.close()

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(other_list), 0, f"不应出现未预期的错误: {other_list}")
        self.assertEqual(len(success_list), 2, f"严格仅允许 2 台机器激活成功，实际成功数: {len(success_list)}")
        self.assertEqual(len(max_activation_list), 3, f"严格拦截 3 台超额机器，实际拦截数: {len(max_activation_list)}")

        active_count = MachineBinding.objects.filter(license=license_obj, status='active').count()
        self.assertEqual(active_count, 2, f"数据库有效机器绑定必须严格等于 2，实际为: {active_count}")
