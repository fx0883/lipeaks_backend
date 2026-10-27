"""
Milestone 1 (ARCH-08, ARCH-09, ARCH-10) 对抗性实证检验与边界压测脚本
执行者：challenger_m1_2 (EMPIRICAL CHALLENGER)

测试维度：
1. 验证 Python 导入解析与 4 个空桩彻底移除无遮蔽 (ARCH-08)
2. 验证 orders 彻底移除 (ARCH-08)
3. 验证 WhiteNoise 运行时配置与拼写修正 (ARCH-09)
4. 验证 19 个业务专属异常与全局异常处理器格式规范、鲁棒性及循环导入压力测试 (ARCH-10)
5. 验证本地受保护文件完整性
"""
import os
import sys
import glob
import json
import subprocess
import importlib
from pathlib import Path
from typing import Dict, Any, List

# 确保项目根目录在 sys.path 中
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_test')
import django
django.setup()
from django.conf import settings
from django.test import RequestFactory
from rest_framework.response import Response

results: Dict[str, Any] = {
    "total_tests": 0,
    "passed_tests": 0,
    "failed_tests": 0,
    "details": []
}

def record_result(name: str, passed: bool, message: str, data: Any = None):
    results["total_tests"] += 1
    if passed:
        results["passed_tests"] += 1
        status_str = "[PASS]"
    else:
        results["failed_tests"] += 1
        status_str = "[FAIL]"
    entry = {"name": name, "passed": passed, "message": message, "data": data}
    results["details"].append(entry)
    print(f"{status_str} {name}: {message}")


# =========================================================================
# 维度 1: 验证 Python 导入解析与空桩彻底移除无遮蔽 (ARCH-08)
# =========================================================================
def test_arch08_views_import_and_no_shadowing():
    print("\n--- 维度 1: Python 导入解析与空桩彻底移除无遮蔽 ---")
    base_dir = str(settings.BASE_DIR)

    # 1.1 磁盘文件物理存在性断言
    stub_files = [
        os.path.join(base_dir, 'customers', 'views.py'),
        os.path.join(base_dir, 'feedbacks', 'views.py'),
        os.path.join(base_dir, 'licenses', 'views.py'),
        os.path.join(base_dir, 'users', 'views.py'),
    ]
    all_stubs_absent = True
    for sf in stub_files:
        exists = os.path.exists(sf)
        if exists:
            all_stubs_absent = False
            record_result(f"stub_absent_{os.path.basename(os.path.dirname(sf))}", False, f"File still exists: {sf}")
        else:
            record_result(f"stub_absent_{os.path.basename(os.path.dirname(sf))}", True, f"File confirmed deleted: {sf}")

    # 1.2 对抗性检查：是否遗留任何 views.pyc 缓存遮蔽
    pyc_shadowing_found = False
    for app in ['customers', 'feedbacks', 'licenses', 'users']:
        pyc_pattern = os.path.join(base_dir, app, '__pycache__', 'views.*.pyc')
        matches = glob.glob(pyc_pattern)
        if matches:
            pyc_shadowing_found = True
            record_result(f"no_pyc_shadowing_{app}", False, f"Found shadowing bytecode: {matches}")
        else:
            record_result(f"no_pyc_shadowing_{app}", True, f"Zero shadowing bytecode in {app}/__pycache__")

    # 1.3 动态 import 各 views 包并验证包结构与类导出
    # customers.views
    try:
        customers_views = importlib.import_module('customers.views')
        is_pkg = hasattr(customers_views, '__path__')
        has_classes = hasattr(customers_views, 'CustomerViewSet') and hasattr(customers_views, 'TenantCustomerViewSet')
        record_result(
            "import_customers_views",
            is_pkg and has_classes,
            f"Is package: {is_pkg}, CustomerViewSet found: {hasattr(customers_views, 'CustomerViewSet')}"
        )
    except Exception as e:
        record_result("import_customers_views", False, f"Failed: {type(e).__name__}: {str(e)}")

    # feedbacks.views
    try:
        feedbacks_views = importlib.import_module('feedbacks.views')
        is_pkg = hasattr(feedbacks_views, '__path__')
        has_classes = (
            hasattr(feedbacks_views, 'FeedbackListView') and
            hasattr(feedbacks_views, 'FeedbackDetailView') and
            hasattr(feedbacks_views, 'FeedbackReplyListView')
        )
        record_result(
            "import_feedbacks_views",
            is_pkg and has_classes,
            f"Is package: {is_pkg}, FeedbackListView found: {hasattr(feedbacks_views, 'FeedbackListView')}"
        )
    except Exception as e:
        record_result("import_feedbacks_views", False, f"Failed: {type(e).__name__}: {str(e)}")

    # licenses.views
    try:
        licenses_views = importlib.import_module('licenses.views')
        is_pkg = hasattr(licenses_views, '__path__')
        # 验证子模块 views.admin_views
        licenses_admin_views = importlib.import_module('licenses.views.admin_views')
        has_admin_classes = hasattr(licenses_admin_views, 'LicenseViewSet') and hasattr(licenses_admin_views, 'MachineBindingViewSet')
        record_result(
            "import_licenses_views",
            is_pkg and has_admin_classes,
            f"Is package: {is_pkg}, LicenseViewSet found in admin_views: {has_admin_classes}"
        )
    except Exception as e:
        record_result("import_licenses_views", False, f"Failed: {type(e).__name__}: {str(e)}")

    # users.views
    try:
        users_views = importlib.import_module('users.views')
        is_pkg = hasattr(users_views, '__path__')
        has_classes = (
            hasattr(users_views, 'LoginView') and
            hasattr(users_views, 'RegisterView') and
            hasattr(users_views, 'CurrentMemberView') and
            hasattr(users_views, 'AdminUserListCreateView')
        )
        record_result(
            "import_users_views",
            is_pkg and has_classes,
            f"Is package: {is_pkg}, LoginView & AdminUserListCreateView found: {has_classes}"
        )
    except Exception as e:
        record_result("import_users_views", False, f"Failed: {type(e).__name__}: {str(e)}")


# =========================================================================
# 维度 2: 验证 orders 彻底移除 (ARCH-08)
# =========================================================================
def test_arch08_orders_completely_removed():
    print("\n--- 维度 2: 验证 orders 彻底移除 ---")
    base_dir = str(settings.BASE_DIR)

    # 2.1 物理目录不存在
    orders_dir = os.path.join(base_dir, 'orders')
    exists = os.path.exists(orders_dir)
    record_result("orders_dir_absent", not exists, f"Directory exists: {exists}")

    # 2.2 import orders 抛出 ModuleNotFoundError
    try:
        importlib.invalidate_caches()
        if 'orders' in sys.modules:
            del sys.modules['orders']
        import orders  # type: ignore
        record_result("import_orders_raises_modulenotfound", False, "Importing orders succeeded! Expected ModuleNotFoundError")
    except ModuleNotFoundError as e:
        record_result("import_orders_raises_modulenotfound", True, f"Correctly raised ModuleNotFoundError: {e}")
    except Exception as e:
        record_result("import_orders_raises_modulenotfound", False, f"Raised unexpected exception: {type(e).__name__}: {e}")

    # 2.3 检查 INSTALLED_APPS
    orders_in_installed = any('orders' in app.lower() for app in settings.INSTALLED_APPS)
    record_result("orders_not_in_installed_apps", not orders_in_installed, f"Orders found in INSTALLED_APPS: {orders_in_installed}")

    # 2.4 检查 core/urls.py 是否遗留 orders 路由
    urls_file = os.path.join(base_dir, 'core', 'urls.py')
    with open(urls_file, 'r', encoding='utf-8') as f:
        urls_code = f.read()
    orders_in_urls = 'orders' in urls_code
    record_result("orders_not_in_urls", not orders_in_urls, f"orders keyword in urls.py: {orders_in_urls}")


# =========================================================================
# 维度 3: 验证 WhiteNoise 运行时配置与拼写修正 (ARCH-09)
# =========================================================================
def test_arch09_whitenoise_setting():
    print("\n--- 维度 3: WhiteNoise 运行时配置与拼写修正 ---")
    base_dir = str(settings.BASE_DIR)

    # 3.1 运行时 settings 检查
    has_correct = hasattr(settings, 'WHITENOISE_AUTOREFRESH')
    has_typo = hasattr(settings, 'WHITENENOISE_AUTOREFRESH')
    val = getattr(settings, 'WHITENOISE_AUTOREFRESH', None)
    is_bool = isinstance(val, bool)
    record_result(
        "whitenoise_setting_runtime",
        has_correct and is_bool and not has_typo,
        f"WHITENOISE_AUTOREFRESH={val} (bool={is_bool}), typo exists={has_typo}"
    )

    # 3.2 源码 core/settings.py 静态检查
    settings_file = os.path.join(base_dir, 'core', 'settings.py')
    with open(settings_file, 'r', encoding='utf-8') as f:
        settings_text = f.read()

    has_source_correct = 'WHITENOISE_AUTOREFRESH = DEBUG' in settings_text
    has_source_typo = 'WHITENENOISE' in settings_text
    record_result(
        "whitenoise_setting_source",
        has_source_correct and not has_source_typo,
        f"Source has 'WHITENOISE_AUTOREFRESH = DEBUG': {has_source_correct}, typo absent: {not has_source_typo}"
    )

    # 3.3 中间件列表包含 WhiteNoiseMiddleware
    has_middleware = 'whitenoise.middleware.WhiteNoiseMiddleware' in settings.MIDDLEWARE
    record_result(
        "whitenoise_middleware_configured",
        has_middleware,
        f"WhiteNoiseMiddleware present in MIDDLEWARE: {has_middleware}"
    )


# =========================================================================
# 维度 4: 业务专属异常体系与全局异常处理器 (ARCH-10)
# =========================================================================
def test_arch10_exceptions_and_handler():
    print("\n--- 维度 4: 业务专属异常体系与全局异常处理器 ---")
    base_dir = str(settings.BASE_DIR)
    from common.exceptions.base import BusinessException
    from common.exceptions.handler import custom_exception_handler

    # 4.1 架构解耦核验：handler.py 绝无业务模型/业务包直接反向导入
    handler_file = os.path.join(base_dir, 'common', 'exceptions', 'handler.py')
    with open(handler_file, 'r', encoding='utf-8') as f:
        handler_code = f.read()
    
    no_tenant_import = 'from .tenant import TenantException' not in handler_code
    no_biz_imports = not any(
        f'import {app}' in handler_code or f'from {app}' in handler_code
        for app in ['licenses', 'points', 'cms', 'tenants', 'users']
    )
    record_result(
        "handler_dip_decoupling",
        no_tenant_import and no_biz_imports,
        f"No TenantException import: {no_tenant_import}, No reverse biz app imports: {no_biz_imports}"
    )

    # 4.2 导入并验证各模块 19 个业务专属异常
    from licenses.exceptions import (
        LicenseException,
        LicenseExpiredException,
        LicenseNotFoundException,
        LicenseQuotaExceededException,
        LicenseRevokedException,
        LicenseActivationFailedException,
    )
    from points.exceptions import (
        PointsException,
        PointsInsufficientException,
        PointsExpiredException,
    )
    from cms.exceptions import (
        CMSException,
        ArticleNotFoundException,
        CategoryNotFoundException,
    )
    from tenants.exceptions import (
        TenantException,
        TenantNotFoundException,
        TenantInactiveException,
        TenantQuotaExceededException,
        TenantAccessDeniedException,
    )
    from users.exceptions import (
        UserException,
        UserNotFoundException,
        UserInactiveException,
        UserPermissionDeniedException,
    )

    all_domain_exceptions = [
        # licenses
        (LicenseException, 400, 'LICENSE_ERROR'),
        (LicenseExpiredException, 400, 'LICENSE_EXPIRED'),
        (LicenseNotFoundException, 404, 'LICENSE_NOT_FOUND'),
        (LicenseQuotaExceededException, 429, 'LICENSE_QUOTA_EXCEEDED'),
        (LicenseRevokedException, 400, 'LICENSE_REVOKED'),
        (LicenseActivationFailedException, 400, 'LICENSE_ACTIVATION_FAILED'),
        # points
        (PointsException, 400, 'POINTS_ERROR'),
        (PointsInsufficientException, 400, 'POINTS_INSUFFICIENT'),
        (PointsExpiredException, 400, 'POINTS_EXPIRED'),
        # cms
        (CMSException, 400, 'CMS_ERROR'),
        (ArticleNotFoundException, 404, 'ARTICLE_NOT_FOUND'),
        (CategoryNotFoundException, 404, 'CATEGORY_NOT_FOUND'),
        # tenants
        (TenantException, 400, 'TENANT_ERROR'),
        (TenantNotFoundException, 404, 'TENANT_NOT_FOUND'),
        (TenantInactiveException, 403, 'TENANT_INACTIVE'),
        (TenantQuotaExceededException, 429, 'TENANT_QUOTA_EXCEEDED'),
        (TenantAccessDeniedException, 403, 'TENANT_ACCESS_DENIED'),
        # users
        (UserException, 400, 'USER_ERROR'),
        (UserNotFoundException, 404, 'USER_NOT_FOUND'),
        (UserInactiveException, 403, 'USER_INACTIVE'),
        (UserPermissionDeniedException, 403, 'USER_PERMISSION_DENIED'),
    ]

    rf = RequestFactory()
    req = rf.get('/api/v1/test-adversarial/')
    context = {'request': req, 'view': None}

    # 4.3 批量验证 19 个异常类的继承关系与 custom_exception_handler 统一输出
    all_passed = True
    for exc_cls, expected_status, expected_error_code in all_domain_exceptions:
        # 1. 继承检查
        if not issubclass(exc_cls, BusinessException):
            record_result(f"subclass_{exc_cls.__name__}", False, f"{exc_cls.__name__} does not inherit from BusinessException")
            all_passed = False
            continue

        # 2. 默认实例化调用
        instance = exc_cls()
        resp = custom_exception_handler(instance, context)
        
        valid_resp = (
            isinstance(resp, Response) and
            resp.status_code == expected_status and
            resp.data.get('success') is False and
            isinstance(resp.data.get('code'), int) and
            resp.data.get('error_code') == expected_error_code and
            'message' in resp.data and
            resp.data.get('data') is None
        )
        if not valid_resp:
            record_result(f"handler_{exc_cls.__name__}", False, f"Unexpected response: {resp.status_code}, data={resp.data}")
            all_passed = False
        
        # 3. 自定义 detail 实例化调用
        custom_detail = f"Adversarial detail for {exc_cls.__name__}"
        instance_custom = exc_cls(detail=custom_detail, extra_meta="test_data")
        resp_custom = custom_exception_handler(instance_custom, context)
        valid_custom = (
            resp_custom.status_code == expected_status and
            resp_custom.data.get('message') == custom_detail and
            resp_custom.data.get('error_code') == expected_error_code
        )
        if not valid_custom:
            record_result(f"handler_custom_{exc_cls.__name__}", False, f"Custom detail failed: {resp_custom.data}")
            all_passed = False

    record_result(
        "all_19_domain_exceptions_handler_contract",
        all_passed,
        f"Successfully tested all 19 domain exceptions across 5 modules. Status codes & envelopes 100% conform."
    )

    # 4.4 极端边界测试：context 为空字典 {} 或缺少 request/view
    try:
        exc_test = TenantNotFoundException(detail="No context test")
        resp_no_context = custom_exception_handler(exc_test, {})
        valid_no_context = (
            resp_no_context.status_code == 404 and
            resp_no_context.data['success'] is False and
            resp_no_context.data['error_code'] == 'TENANT_NOT_FOUND'
        )
        record_result("handler_robustness_empty_context", valid_no_context, "Handler handles empty context robustly")
    except Exception as e:
        record_result("handler_robustness_empty_context", False, f"Exception with empty context: {e}")

    # 4.5 对抗性循环导入压力测试（在独立的全新 Python 子进程中验证 4 种拓扑导入顺序）
    test_topologies = [
        # 顺序 1: common.exceptions -> 所有领域专属异常 -> handler
        """
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_test')
django.setup()
import common.exceptions
import licenses.exceptions
import points.exceptions
import cms.exceptions
import tenants.exceptions
import users.exceptions
import common.exceptions.handler
print('TOPOLOGY_1_OK')
""",
        # 顺序 2: 反向顺序，先各领域业务异常，最后导入 common
        """
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_test')
django.setup()
import users.exceptions
import tenants.exceptions
import cms.exceptions
import points.exceptions
import licenses.exceptions
import common.exceptions
import common.exceptions.handler
print('TOPOLOGY_2_OK')
""",
        # 顺序 3: 仅导入各业务专属异常，验证应用间无互锁
        """
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_test')
django.setup()
from tenants.exceptions import TenantNotFoundException
from users.exceptions import UserException
from licenses.exceptions import LicenseException
from points.exceptions import PointsException
from cms.exceptions import CMSException
print('TOPOLOGY_3_OK')
""",
        # 顺序 4: 从 common.exceptions 批量导入旧兼容别名与新类
        """
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_test')
django.setup()
from common.exceptions import TenantNotFound, QuotaExceeded, custom_exception_handler, BusinessException
print('TOPOLOGY_4_OK')
""",
    ]

    topology_all_pass = True
    for idx, snippet in enumerate(test_topologies, 1):
        proc = subprocess.run(
            [sys.executable, "-c", snippet],
            cwd=base_dir,
            capture_output=True,
            text=True
        )
        if proc.returncode != 0:
            topology_all_pass = False
            record_result(f"circular_import_topology_{idx}", False, f"Topology {idx} failed with exit code {proc.returncode}: {proc.stderr}")
        else:
            record_result(f"circular_import_topology_{idx}", True, f"Topology {idx} clean without circular import. Output: {proc.stdout.strip()}")

    record_result(
        "circular_import_stress_harness",
        topology_all_pass,
        "All 4 circular import topologies cleanly executed in isolated processes"
    )


# =========================================================================
# 维度 5: 验证本地受保护文件完整性
# =========================================================================
def test_protected_files_intact():
    print("\n--- 维度 5: 验证本地受保护文件完整性 ---")
    base_dir = str(settings.BASE_DIR)
    protected_files = [
        ('.env', True),
        ('.env.prod', True),
        (os.path.join('wechat', 'wechat_config.json'), True),
        ('CODE_REVIEW_REPORT.md', True),
    ]

    all_intact = True
    for rel_path, check_nonempty in protected_files:
        full_path = os.path.join(base_dir, rel_path)
        exists = os.path.exists(full_path)
        if not exists:
            all_intact = False
            record_result(f"protected_file_{rel_path}", False, f"File missing: {full_path}")
            continue
        
        size = os.path.getsize(full_path)
        if check_nonempty and size == 0:
            all_intact = False
            record_result(f"protected_file_{rel_path}", False, f"File empty (size=0): {full_path}")
            continue
        
        # 对 json 文件做合法性校验
        if rel_path.endswith('.json'):
            try:
                with open(full_path, 'r', encoding='utf-8') as jf:
                    json.load(jf)
            except Exception as e:
                all_intact = False
                record_result(f"protected_file_{rel_path}", False, f"Invalid JSON format: {e}")
                continue

        record_result(f"protected_file_{rel_path}", True, f"Intact (size={size} bytes)")

    # 检查 git diff 中没有对受保护文件的修改
    git_diff_proc = subprocess.run(
        ['git', 'diff', '--name-only'],
        cwd=base_dir,
        capture_output=True,
        text=True
    )
    changed_files = git_diff_proc.stdout.splitlines()
    protected_in_diff = [p[0].replace('\\', '/') for p in protected_files if p[0].replace('\\', '/') in changed_files or p[0] in changed_files]
    record_result(
        "protected_files_not_modified_in_git",
        len(protected_in_diff) == 0,
        f"Protected files modified in git diff: {protected_in_diff}"
    )


# =========================================================================
# 主函数入口
# =========================================================================
def main():
    print("=================================================================")
    print("  LIPEAKS BACKEND - M1 (ARCH-08, 09, 10) EMPIRICAL CHALLENGE    ")
    print("=================================================================")
    
    test_arch08_views_import_and_no_shadowing()
    test_arch08_orders_completely_removed()
    test_arch09_whitenoise_setting()
    test_arch10_exceptions_and_handler()
    test_protected_files_intact()

    print("\n=================================================================")
    print(f"CHALLENGE SUMMARY: Total: {results['total_tests']}, Passed: {results['passed_tests']}, Failed: {results['failed_tests']}")
    print("=================================================================")

    # 导出实证检验结果为 JSON
    output_json = os.path.join(str(settings.BASE_DIR), "scripts", "adversarial_m1_p2_results.json")
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Empirical results written to: {output_json}")

    return 0 if results["failed_tests"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
