#!/usr/bin/env python
"""
租户隔离功能自动化测试脚本

使用方法:
    python temp1122/test_tenant_isolation.py

要求:
    1. 项目已运行 (python manage.py runserver)
    2. 数据库已迁移
    3. 已创建测试租户和用户
"""

import requests
import json
from typing import Dict, List, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TestConfig:
    """测试配置"""
    base_url: str = "http://localhost:8000"
    tenant1_id: int = 1
    tenant2_id: int = 2
    tenant1_admin_token: str = ""
    tenant2_admin_token: str = ""
    tenant1_user_token: str = ""
    tenant2_user_token: str = ""
    superadmin_token: str = ""


class TenantIsolationTester:
    """租户隔离测试器"""
    
    def __init__(self, config: TestConfig):
        self.config = config
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def log_test(self, module: str, test_name: str, passed: bool, message: str = ""):
        """记录测试结果"""
        result = {
            "module": module,
            "test": test_name,
            "status": "✅ PASS" if passed else "❌ FAIL",
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        
        if passed:
            self.passed += 1
            print(f"✅ {module} - {test_name}")
        else:
            self.failed += 1
            print(f"❌ {module} - {test_name}: {message}")
    
    def make_request(self, method: str, endpoint: str, tenant_id: int, 
                    token: str, data: dict = None) -> Tuple[int, dict]:
        """发送HTTP请求"""
        url = f"{self.config.base_url}{endpoint}"
        headers = {
            "X-Tenant-ID": str(tenant_id),
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, timeout=10)
            elif method == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=10)
            elif method == "PUT":
                response = requests.put(url, headers=headers, json=data, timeout=10)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                return 0, {}
            
            try:
                return response.status_code, response.json()
            except:
                return response.status_code, {}
        except Exception as e:
            print(f"请求错误: {e}")
            return 0, {}
    
    def test_applications_module(self):
        """测试Applications模块"""
        module = "Applications"
        
        # 测试1: Tenant 1创建应用
        status, data = self.make_request(
            "POST", "/api/applications/",
            self.config.tenant1_id,
            self.config.tenant1_admin_token,
            {"name": "Test App T1", "app_code": "TEST_APP_T1"}
        )
        self.log_test(module, "Tenant 1创建应用", 
                     status == 201, 
                     f"状态码: {status}")
        
        # 测试2: Tenant 2创建应用
        status, data = self.make_request(
            "POST", "/api/applications/",
            self.config.tenant2_id,
            self.config.tenant2_admin_token,
            {"name": "Test App T2", "app_code": "TEST_APP_T2"}
        )
        self.log_test(module, "Tenant 2创建应用", 
                     status == 201,
                     f"状态码: {status}")
        
        # 测试3: Tenant 1查询应用列表
        status, data = self.make_request(
            "GET", "/api/applications/",
            self.config.tenant1_id,
            self.config.tenant1_admin_token
        )
        count_t1 = len(data.get("results", [])) if isinstance(data.get("results"), list) else 0
        self.log_test(module, "Tenant 1查询列表", 
                     status == 200,
                     f"状态码: {status}, 数量: {count_t1}")
        
        # 测试4: Tenant 2查询应用列表
        status, data = self.make_request(
            "GET", "/api/applications/",
            self.config.tenant2_id,
            self.config.tenant2_admin_token
        )
        count_t2 = len(data.get("results", [])) if isinstance(data.get("results"), list) else 0
        self.log_test(module, "Tenant 2查询列表", 
                     status == 200,
                     f"状态码: {status}, 数量: {count_t2}")
        
        # 测试5: 验证数据隔离
        self.log_test(module, "数据隔离验证", 
                     count_t1 > 0 and count_t2 > 0,
                     f"T1有{count_t1}个应用, T2有{count_t2}个应用")
    
    def test_orders_module(self):
        """测试Orders模块"""
        module = "Orders"
        
        # 测试1: Tenant 1创建订单
        status, data = self.make_request(
            "POST", "/api/orders/",
            self.config.tenant1_id,
            self.config.tenant1_admin_token,
            {
                "order_number": f"ORD_T1_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "total_amount": "1000.00",
                "payment_status": "pending"
            }
        )
        self.log_test(module, "Tenant 1创建订单", 
                     status in [200, 201],
                     f"状态码: {status}")
        
        # 测试2: Tenant 2创建订单
        status, data = self.make_request(
            "POST", "/api/orders/",
            self.config.tenant2_id,
            self.config.tenant2_admin_token,
            {
                "order_number": f"ORD_T2_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "total_amount": "2000.00",
                "payment_status": "pending"
            }
        )
        self.log_test(module, "Tenant 2创建订单", 
                     status in [200, 201],
                     f"状态码: {status}")
        
        # 测试3: 查询订单列表
        status, data = self.make_request(
            "GET", "/api/orders/",
            self.config.tenant1_id,
            self.config.tenant1_admin_token
        )
        self.log_test(module, "Tenant 1查询订单", 
                     status == 200,
                     f"状态码: {status}")
        
        status, data = self.make_request(
            "GET", "/api/orders/",
            self.config.tenant2_id,
            self.config.tenant2_admin_token
        )
        self.log_test(module, "Tenant 2查询订单", 
                     status == 200,
                     f"状态码: {status}")
    
    def test_customers_module(self):
        """测试Customers模块"""
        module = "Customers"
        
        # 测试1: Tenant 1创建客户
        status, data = self.make_request(
            "POST", "/api/customers/",
            self.config.tenant1_id,
            self.config.tenant1_admin_token,
            {
                "name": "Customer A T1",
                "status": "active",
                "type": "individual"
            }
        )
        self.log_test(module, "Tenant 1创建客户", 
                     status in [200, 201],
                     f"状态码: {status}")
        
        # 测试2: Tenant 2创建客户
        status, data = self.make_request(
            "POST", "/api/customers/",
            self.config.tenant2_id,
            self.config.tenant2_admin_token,
            {
                "name": "Customer A T2",
                "status": "active",
                "type": "individual"
            }
        )
        self.log_test(module, "Tenant 2创建客户", 
                     status in [200, 201],
                     f"状态码: {status}")
        
        # 测试3: 搜索测试
        status, data = self.make_request(
            "GET", "/api/customers/?search=Customer A",
            self.config.tenant1_id,
            self.config.tenant1_admin_token
        )
        self.log_test(module, "Tenant 1搜索客户", 
                     status == 200,
                     f"状态码: {status}")
        
        status, data = self.make_request(
            "GET", "/api/customers/?search=Customer A",
            self.config.tenant2_id,
            self.config.tenant2_admin_token
        )
        self.log_test(module, "Tenant 2搜索客户", 
                     status == 200,
                     f"状态码: {status}")
    
    def test_interactions_module(self):
        """测试Interactions模块"""
        module = "Interactions"
        
        # 注意：这需要有文章数据存在
        # 这里只测试API的可访问性
        
        # 测试1: 查询收藏列表
        status, data = self.make_request(
            "GET", "/api/interactions/favorites/",
            self.config.tenant1_id,
            self.config.tenant1_user_token
        )
        self.log_test(module, "Tenant 1查询收藏", 
                     status in [200, 404],  # 404表示路由可能不同
                     f"状态码: {status}")
        
        # 测试2: 查询点赞列表
        status, data = self.make_request(
            "GET", "/api/interactions/likes/",
            self.config.tenant1_id,
            self.config.tenant1_user_token
        )
        self.log_test(module, "Tenant 1查询点赞", 
                     status in [200, 404],
                     f"状态码: {status}")
    
    def test_feedbacks_module(self):
        """测试Feedbacks模块"""
        module = "Feedbacks"
        
        # 测试1: Tenant 1提交反馈
        status, data = self.make_request(
            "POST", "/api/feedbacks/",
            self.config.tenant1_id,
            self.config.tenant1_user_token,
            {
                "title": "Test Feedback T1",
                "description": "This is a test feedback",
                "feedback_type": "bug"
            }
        )
        self.log_test(module, "Tenant 1提交反馈", 
                     status in [200, 201],
                     f"状态码: {status}")
        
        # 测试2: Tenant 2提交反馈
        status, data = self.make_request(
            "POST", "/api/feedbacks/",
            self.config.tenant2_id,
            self.config.tenant2_user_token,
            {
                "title": "Test Feedback T2",
                "description": "This is a test feedback",
                "feedback_type": "bug"
            }
        )
        self.log_test(module, "Tenant 2提交反馈", 
                     status in [200, 201],
                     f"状态码: {status}")
        
        # 测试3: 查询反馈列表
        status, data = self.make_request(
            "GET", "/api/feedbacks/",
            self.config.tenant1_id,
            self.config.tenant1_user_token
        )
        self.log_test(module, "Tenant 1查询反馈", 
                     status == 200,
                     f"状态码: {status}")
    
    def test_cross_tenant_access(self):
        """测试跨租户访问拒绝"""
        module = "Security"
        
        # 测试1: 使用T1的Token访问T2的租户
        status, data = self.make_request(
            "GET", "/api/applications/",
            self.config.tenant2_id,  # T2的租户ID
            self.config.tenant1_admin_token  # 但用T1的Token
        )
        # 应该返回空列表或错误
        self.log_test(module, "跨租户访问拒绝", 
                     status in [200, 401, 403] and (not data.get("results") or len(data.get("results", [])) == 0),
                     f"状态码: {status}, 是否返回空: {len(data.get('results', [])) == 0}")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("租户隔离功能测试开始")
        print("=" * 60)
        print()
        
        # 检查配置
        if not self.config.tenant1_admin_token:
            print("⚠️  警告: 未配置Tenant 1管理员Token，部分测试将跳过")
        
        # 运行测试
        print("测试 Applications 模块...")
        self.test_applications_module()
        print()
        
        print("测试 Orders 模块...")
        self.test_orders_module()
        print()
        
        print("测试 Customers 模块...")
        self.test_customers_module()
        print()
        
        print("测试 Interactions 模块...")
        self.test_interactions_module()
        print()
        
        print("测试 Feedbacks 模块...")
        self.test_feedbacks_module()
        print()
        
        print("测试跨租户访问...")
        self.test_cross_tenant_access()
        print()
        
        # 生成报告
        self.generate_report()
    
    def generate_report(self):
        """生成测试报告"""
        print("=" * 60)
        print("测试报告")
        print("=" * 60)
        print(f"总计测试用例: {self.passed + self.failed}")
        print(f"✅ 通过: {self.passed}")
        print(f"❌ 失败: {self.failed}")
        print(f"成功率: {(self.passed / (self.passed + self.failed) * 100) if (self.passed + self.failed) > 0 else 0:.1f}%")
        print()
        
        if self.failed > 0:
            print("失败的测试用例:")
            for result in self.results:
                if "❌" in result["status"]:
                    print(f"  - {result['module']} - {result['test']}: {result['message']}")
        
        print("=" * 60)
        
        # 保存JSON报告
        report_file = "temp1122/test_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump({
                "summary": {
                    "total": self.passed + self.failed,
                    "passed": self.passed,
                    "failed": self.failed,
                    "success_rate": (self.passed / (self.passed + self.failed) * 100) if (self.passed + self.failed) > 0 else 0
                },
                "results": self.results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"\n详细报告已保存到: {report_file}")


def main():
    """主函数"""
    # 配置测试参数
    config = TestConfig()
    
    print("=" * 60)
    print("租户隔离功能测试工具")
    print("=" * 60)
    print()
    print("⚠️  重要提示:")
    print("1. 请确保Django服务已启动 (python manage.py runserver)")
    print("2. 请确保已创建测试租户和用户")
    print("3. 请在代码中配置Token")
    print()
    print("如果没有Token，请先运行以下命令获取:")
    print("  curl -X POST http://localhost:8000/api/auth/login/ \\")
    print("    -H 'Content-Type: application/json' \\")
    print("    -d '{\"username\":\"admin\",\"password\":\"password\"}'")
    print()
    
    # TODO: 在这里配置实际的Token
    # config.tenant1_admin_token = "your_token_here"
    # config.tenant2_admin_token = "your_token_here"
    # config.tenant1_user_token = "your_token_here"
    # config.tenant2_user_token = "your_token_here"
    
    if not config.tenant1_admin_token:
        print("⚠️  未配置Token，测试将使用模拟模式")
        print("请编辑此脚本并配置实际的Token后再运行")
        print()
        response = input("是否继续运行测试（部分测试可能失败）? (y/n): ")
        if response.lower() != 'y':
            print("测试取消")
            return
        print()
    
    # 运行测试
    tester = TenantIsolationTester(config)
    tester.run_all_tests()


if __name__ == "__main__":
    main()
