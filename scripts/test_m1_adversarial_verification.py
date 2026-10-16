"""
Milestone 1 对抗性验证与边界实测脚本
覆盖维度：
1. 迁移解封与各类管理命令边界
2. 生产环境 vs 测试环境 响应包装与 StandardJSONRenderer 一致性 (双重包裹探测)
3. ContextVar 租户隔离高并发压力与异常鲁棒性
"""
import os
import sys
import json
import asyncio
import threading
import time
from typing import Dict, Any
from pathlib import Path

# 确保项目根目录在 sys.path 中
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

# 设置测试环境配置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings_test')
import django
django.setup()
from django.test.utils import setup_test_environment
setup_test_environment()

from django.test import RequestFactory, Client
from django.core.management import call_command
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.renderers import JSONRenderer

from common.renderers import StandardJSONRenderer
from common.exceptions.handler import custom_exception_handler
from common.exceptions.base import BusinessException
from rest_framework.exceptions import ValidationError, PermissionDenied
from common.utils.tenant_context import (
    get_current_tenant,
    set_current_tenant,
    clear_current_tenant,
    tenant_context,
)
from common.middleware.tenant_middleware import TenantMiddleware

results = {
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
# 维度 1: 迁移管理命令边界实测
# =========================================================================
def test_migrations():
    print("\n--- 维度 1: 迁移管理命令边界实测 ---")
    
    # 1.1 makemigrations points dry-run
    try:
        call_command('makemigrations', 'points', dry_run=True, verbosity=0)
        record_result("makemigrations_points_dry_run", True, "Successfully ran makemigrations points --dry-run without DisableMigrations error")
    except Exception as e:
        record_result("makemigrations_points_dry_run", False, f"Exception: {type(e).__name__}: {str(e)}")

    # 1.2 makemigrations users dry-run
    try:
        call_command('makemigrations', 'users', dry_run=True, verbosity=0)
        record_result("makemigrations_users_dry_run", True, "Successfully ran makemigrations users --dry-run")
    except Exception as e:
        record_result("makemigrations_users_dry_run", False, f"Exception: {type(e).__name__}: {str(e)}")

    # 1.3 showmigrations points
    try:
        call_command('showmigrations', 'points', verbosity=0)
        record_result("showmigrations_points", True, "Successfully ran showmigrations points")
    except Exception as e:
        record_result("showmigrations_points", False, f"Exception: {type(e).__name__}: {str(e)}")


# =========================================================================
# 维度 2: 响应包装与 StandardJSONRenderer 对抗测试 (双重包裹探测)
# =========================================================================
def test_response_rendering_adversarial():
    print("\n--- 维度 2: 响应包装与 StandardJSONRenderer 对抗测试 ---")
    renderer = StandardJSONRenderer()
    rf = RequestFactory()

    # 2.1 原始无包装字典
    req = rf.get('/api/v1/test/')
    resp = Response({"foo": "bar", "num": 42}, status=200)
    context = {"response": resp, "request": req}
    rendered = renderer.render(resp.data, renderer_context=context)
    data = json.loads(rendered.decode('utf-8'))
    
    is_valid_envelope = (
        data.get("success") is True and
        data.get("code") == 2000 and
        isinstance(data.get("data"), dict) and
        data["data"].get("foo") == "bar" and
        data["data"].get("num") == 42
    )
    # 检测双重包裹
    is_double_wrapped = (
        isinstance(data.get("data"), dict) and
        "success" in data["data"] and
        "code" in data["data"]
    )
    record_result(
        "renderer_raw_dict_wrapping",
        is_valid_envelope and not is_double_wrapped,
        f"Valid envelope: {is_valid_envelope}, Double wrapped: {is_double_wrapped}"
    )

    # 2.2 已经包含标准字段的字典 (视图显式返回标准结构) -> 绝对不能二次包装
    resp_prewrapped = Response({
        "success": True,
        "code": 2000,
        "message": "already wrapped",
        "data": {"user_id": 999}
    }, status=200)
    rendered2 = renderer.render(resp_prewrapped.data, renderer_context={"response": resp_prewrapped, "request": req})
    data2 = json.loads(rendered2.decode('utf-8'))
    double_wrapped2 = (
        isinstance(data2.get("data"), dict) and
        ("success" in data2["data"] or "code" in data2["data"])
    )
    exact_content = data2.get("data") == {"user_id": 999}
    record_result(
        "renderer_prewrapped_dict_no_double_wrap",
        not double_wrapped2 and exact_content,
        f"Double wrapped: {double_wrapped2}, Inner data preserved: {exact_content}"
    )

    # 2.3 列表类型响应
    resp_list = Response([{"id": 1}, {"id": 2}], status=200)
    rendered3 = renderer.render(resp_list.data, renderer_context={"response": resp_list, "request": req})
    data3 = json.loads(rendered3.decode('utf-8'))
    valid_list = (
        data3.get("success") is True and
        isinstance(data3.get("data"), list) and
        len(data3["data"]) == 2
    )
    record_result("renderer_list_wrapping", valid_list, f"List wrapped properly: {valid_list}")

    # 2.4 None/空响应
    resp_none = Response(None, status=200)
    rendered_none = renderer.render(resp_none.data, renderer_context={"response": resp_none, "request": req})
    data_none = json.loads(rendered_none.decode('utf-8'))
    valid_none = (
        data_none.get("success") is True and
        data_none.get("code") == 2000 and
        data_none.get("data") is None
    )
    record_result("renderer_none_handling", valid_none, f"None wrapped correctly with data=None: {valid_none}")

    # 2.5 异常与错误响应包装
    exc_val = ValidationError({"email": ["Invalid email format"]})
    err_resp = custom_exception_handler(exc_val, {"request": req, "view": None})
    rendered_err = renderer.render(err_resp.data, renderer_context={"response": err_resp, "request": req})
    err_data = json.loads(rendered_err.decode('utf-8'))
    valid_err = (
        err_data.get("success") is False and
        err_data.get("code") == 4000 and
        isinstance(err_data.get("data"), dict) and
        "email" in err_data["data"]
    )
    record_result("renderer_validation_error_wrapping", valid_err, f"Error envelope valid: {valid_err}")

    # 2.6 自定义业务异常
    class CustomAdversarialException(BusinessException):
        status_code = 400
        business_code = 4099
        error_code = "ADVERSARIAL_ERROR"
        default_detail = "Adversarial test failure"

    biz_exc = CustomAdversarialException()
    biz_resp = custom_exception_handler(biz_exc, {"request": req, "view": None})
    rendered_biz = renderer.render(biz_resp.data, renderer_context={"response": biz_resp, "request": req})
    biz_data = json.loads(rendered_biz.decode('utf-8'))
    valid_biz = (
        biz_data.get("success") is False and
        biz_data.get("code") == 4099 and
        biz_data.get("message") == "Adversarial test failure" and
        biz_data.get("error_code") == "ADVERSARIAL_ERROR"
    )
    record_result("renderer_business_exception_wrapping", valid_biz, f"Business error envelope valid: {valid_biz}")

    # 2.7 真实 HTTP 客户端调用公共测试视图 (经由完整 Django 请求管道)
    client = Client()
    for endpoint in [
        '/api/v1/common/system-info/',
        '/api/v1/common/test-format-class/',
        '/api/v1/common/test-error-class/',
        '/api/v1/common/test-pagination-class/',
    ]:
        http_resp = client.get(endpoint)
        resp_json = http_resp.json()
        
        # 严格验证是否有双重包裹
        has_outer = all(k in resp_json for k in ['success', 'code', 'message', 'data'])
        inner_data = resp_json.get('data')
        is_inner_double = (
            isinstance(inner_data, dict) and
            all(k in inner_data for k in ['success', 'code', 'message', 'data'])
        )
        record_result(
            f"http_endpoint_{endpoint.replace('/', '_')}",
            has_outer and not is_inner_double,
            f"Status: {http_resp.status_code}, Outer envelope: {has_outer}, Double wrapped: {is_inner_double}"
        )


# =========================================================================
# 维度 3: ContextVar 租户并发与异常边界压力测试
# =========================================================================
class MockTenant:
    def __init__(self, tid, name):
        self.id = tid
        self.name = name

def test_contextvar_high_concurrency():
    print("\n--- 维度 3: ContextVar 租户并发与异常边界压力测试 ---")
    
    # 3.1 100 线程高并发交叉设置与验证
    thread_count = 100
    errors = []
    barrier = threading.Barrier(thread_count)

    def worker_thread(tid):
        try:
            my_tenant = MockTenant(tid, f"Tenant_{tid}")
            # 等待所有线程就绪同步爆发
            barrier.wait()
            
            for _ in range(20):
                set_current_tenant(my_tenant)
                # 微小等待让线程调度交错
                time.sleep(0.001)
                curr = get_current_tenant()
                if curr is None or curr.id != tid:
                    errors.append(f"Thread {tid} observed bleed: expected {tid}, got {getattr(curr, 'id', None)}")
                clear_current_tenant()
                if get_current_tenant() is not None:
                    errors.append(f"Thread {tid} clear failed")
        except Exception as e:
            errors.append(f"Thread {tid} raised {str(e)}")

    threads = [threading.Thread(target=worker_thread, args=(i,)) for i in range(thread_count)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    record_result(
        "contextvar_100_thread_stress",
        len(errors) == 0,
        f"100 threads, 20 iterations each. Errors detected: {len(errors)}"
    )

    # 3.2 100 协程 asyncio 并发与交错挂起测试
    async def async_worker(tid):
        my_tenant = MockTenant(tid, f"AsyncTenant_{tid}")
        for _ in range(20):
            set_current_tenant(my_tenant)
            await asyncio.sleep(0.001)
            curr = get_current_tenant()
            if curr is None or curr.id != tid:
                raise ValueError(f"Coroutine {tid} bleed: expected {tid}, got {getattr(curr, 'id', None)}")
            clear_current_tenant()
            if get_current_tenant() is not None:
                raise ValueError(f"Coroutine {tid} clear failed")

    async def run_async_test():
        coros = [async_worker(i) for i in range(100)]
        await asyncio.gather(*coros)

    try:
        asyncio.run(run_async_test())
        record_result("contextvar_100_async_stress", True, "100 coroutines, 20 iterations each. Zero bleed.")
    except Exception as e:
        record_result("contextvar_100_async_stress", False, f"Async stress failed: {str(e)}")

    # 3.3 深度嵌套 tenant_context 异常恢复测试
    t_outer = MockTenant(1, "Outer")
    t_mid = MockTenant(2, "Mid")
    t_inner = MockTenant(3, "Inner")

    try:
        with tenant_context(t_outer):
            assert get_current_tenant().id == 1
            try:
                with tenant_context(t_mid):
                    assert get_current_tenant().id == 2
                    try:
                        with tenant_context(t_inner):
                            assert get_current_tenant().id == 3
                            raise RuntimeError("Simulated crash in inner context")
                    except RuntimeError:
                        pass
                    # 必须恢复为 mid
                    assert get_current_tenant().id == 2, f"Failed restoring to mid, got {get_current_tenant()}"
                    raise ValueError("Simulated crash in mid context")
            except ValueError:
                pass
            # 必须恢复为 outer
            assert get_current_tenant().id == 1, f"Failed restoring to outer, got {get_current_tenant()}"
        
        # 退出最外层后必须为 None
        assert get_current_tenant() is None, f"Failed clearing outer, got {get_current_tenant()}"
        record_result("contextvar_nested_exception_recovery", True, "3 levels nested exception correctly restored each outer frame")
    except Exception as e:
        record_result("contextvar_nested_exception_recovery", False, f"Nested exception recovery failed: {str(e)}")


def main():
    print("=================================================================")
    print("      LIPEAKS BACKEND - MILESTONE 1 ADVERSARIAL CHALLENGE       ")
    print("=================================================================")
    test_migrations()
    test_response_rendering_adversarial()
    test_contextvar_high_concurrency()
    print("\n=================================================================")
    print(f"ADVERSARIAL SUMMARY: Total: {results['total_tests']}, Passed: {results['passed_tests']}, Failed: {results['failed_tests']}")
    print("=================================================================")
    
    # 将结果写出为 json 便于报告引用
    out_path = os.path.join(os.path.dirname(__file__), "adversarial_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Results dumped to: {out_path}")
    
    return 0 if results["failed_tests"] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
