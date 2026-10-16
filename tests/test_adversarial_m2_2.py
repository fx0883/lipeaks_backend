"""
Adversarial Verification Suite for Milestone M2 (Challenger M2-2)
覆盖攻防挑战目标:
1. BUG-LOGIC-10: 批量许可证分配除零边界防御 (batch_assign_licenses 各种异常与空列表)
2. PERF-09: PaginatedDict 容器兼容性 (列表/集合推导式、整数下标、字典键、len 与切片)
3. BUG-LOGIC-09: 账号注销全量清理 (A与B复杂交叉点赞/关注/文章互动彻底清除，无 FieldError，无孤儿数据)
4. PERF-10: ComfyUIClient HTTP 超时参数注入与超时异常优雅捕获
"""
from unittest.mock import patch, MagicMock
import requests
from django.test import TestCase
from django.db.models import Q

from tenants.models import Tenant
from users.models import Member
from cms.models import Article
from interactions.models import ArticleLike, MemberLike, MemberFollow
from common.pagination import PaginatedDict
from points.services.license_service import TenantAwareLicenseAssignmentService
from users.views.member_delete_account_views import MemberDeleteAccountConfirmView
from cms.utils.comfyui_client import ComfyUIClient


class AdversarialBugLogic10BatchAssignLicensesTests(TestCase):
    """
    [BUG-LOGIC-10 对抗实证]
    验证 batch_assign_licenses 在 assignments=[]、单项失败、全量失败等边界下的除零防御与成功率计算
    """

    def setUp(self):
        self.service = TenantAwareLicenseAssignmentService()
        self.mock_member = MagicMock()
        self.mock_member.username = "adversarial_user"
        self.mock_license = MagicMock()
        self.mock_license.license_key = "LIC-TEST-12345678"

    def test_batch_assign_licenses_empty_assignments_zero_division_guard(self):
        """边界 1: assignments=[] 时绝不发生 ZeroDivisionError 并返回 0.0 成功率"""
        results = self.service.batch_assign_licenses([])
        self.assertEqual(results["total_requested"], 0)
        self.assertEqual(results["successful"], 0)
        self.assertEqual(results["failed"], 0)
        self.assertEqual(results["errors"], [])
        self.assertEqual(results["summary"]["success_rate"], 0.0)
        self.assertEqual(results["summary"]["points_awarded_count"], 0)

    def test_batch_assign_licenses_single_failure_success_rate(self):
        """边界 2: 1 个分配请求且失败，成功率为 0.0%"""
        with patch.object(self.service, "assign_license_to_member") as mock_assign:
            mock_assign.return_value = {
                "success": False,
                "error": "quota_exceeded",
                "message": "Quota limit reached"
            }
            results = self.service.batch_assign_licenses([
                {"member": self.mock_member, "license": self.mock_license}
            ])
            self.assertEqual(results["total_requested"], 1)
            self.assertEqual(results["successful"], 0)
            self.assertEqual(results["failed"], 1)
            self.assertEqual(results["summary"]["success_rate"], 0.0)
            self.assertEqual(len(results["errors"]), 1)
            self.assertEqual(results["errors"][0]["error"], "quota_exceeded")

    def test_batch_assign_licenses_all_failures_success_rate(self):
        """边界 3: 3 个分配请求全部失败，成功率为 0.0% 且累计 3 处错误记录"""
        with patch.object(self.service, "assign_license_to_member") as mock_assign:
            mock_assign.return_value = {
                "success": False,
                "error": "invalid_license",
                "message": "License expired"
            }
            assignments = [
                {"member": self.mock_member, "license": self.mock_license}
                for _ in range(3)
            ]
            results = self.service.batch_assign_licenses(assignments)
            self.assertEqual(results["total_requested"], 3)
            self.assertEqual(results["successful"], 0)
            self.assertEqual(results["failed"], 3)
            self.assertEqual(results["summary"]["success_rate"], 0.0)
            self.assertEqual(len(results["errors"]), 3)

    def test_batch_assign_licenses_partial_success_calculation(self):
        """边界 4: 4 个分配请求中 2 成功 2 失败，成功率准确为 50.0%"""
        with patch.object(self.service, "assign_license_to_member") as mock_assign:
            mock_assign.side_effect = [
                {"success": True, "assignment_id": 101},
                {"success": False, "error": "error_1", "message": "fail 1"},
                {"success": True, "assignment_id": 102},
                {"success": False, "error": "error_2", "message": "fail 2"},
            ]
            assignments = [
                {"member": self.mock_member, "license": self.mock_license}
                for _ in range(4)
            ]
            results = self.service.batch_assign_licenses(assignments)
            self.assertEqual(results["total_requested"], 4)
            self.assertEqual(results["successful"], 2)
            self.assertEqual(results["failed"], 2)
            self.assertEqual(results["summary"]["success_rate"], 50.0)
            self.assertEqual(results["assignment_ids"], [101, 102])
            self.assertEqual(len(results["errors"]), 2)

    def test_batch_assign_licenses_unexpected_exception_safety(self):
        """边界 5: 单个分配抛出底层异常时被安全捕获，整体不崩溃并计入 failed"""
        with patch.object(self.service, "assign_license_to_member", side_effect=RuntimeError("DB Crash")):
            results = self.service.batch_assign_licenses([
                {"member": self.mock_member, "license": self.mock_license}
            ])
            self.assertEqual(results["total_requested"], 1)
            self.assertEqual(results["successful"], 0)
            self.assertEqual(results["failed"], 1)
            self.assertEqual(results["summary"]["success_rate"], 0.0)
            self.assertEqual(results["errors"][0]["error"], "unexpected_error")


class AdversarialPerf09PaginatedDictTests(TestCase):
    """
    [PERF-09 对抗实证]
    测试 PaginatedDict 字典特性、迭代器遍历 (列表/集合推导式)、整数下标与切片访问
    """

    def setUp(self):
        self.items = [
            {"id": 1, "name": "Item 1"},
            {"id": 2, "name": "Item 2"},
            {"id": 3, "name": "Item 3"},
        ]
        self.data_dict = {
            "count": 3,
            "next": None,
            "previous": None,
            "results": self.items,
            "pagination": {"current_page": 1, "total_pages": 1}
        }
        self.pdict = PaginatedDict(self.data_dict, self.items)

    def test_paginated_dict_dictionary_access(self):
        """验证标准字典键访问与 get() 方法"""
        self.assertEqual(self.pdict["count"], 3)
        self.assertEqual(self.pdict["results"], self.items)
        self.assertEqual(self.pdict["pagination"]["current_page"], 1)
        self.assertEqual(self.pdict.get("count"), 3)
        self.assertEqual(set(self.pdict.keys()), {"count", "next", "previous", "results", "pagination"})

    def test_paginated_dict_len(self):
        """验证 len(pdict) 反映结果集数量"""
        self.assertEqual(len(self.pdict), 3)

    def test_paginated_dict_integer_index_access(self):
        """验证整数下标正向与逆向索引访问"""
        self.assertEqual(self.pdict[0], {"id": 1, "name": "Item 1"})
        self.assertEqual(self.pdict[1], {"id": 2, "name": "Item 2"})
        self.assertEqual(self.pdict[-1], {"id": 3, "name": "Item 3"})

    def test_paginated_dict_list_comprehension(self):
        """验证列表推导式遍历 [x for x in pdict]"""
        extracted = [x["name"] for x in self.pdict]
        self.assertEqual(extracted, ["Item 1", "Item 2", "Item 3"])

    def test_paginated_dict_set_comprehension(self):
        """验证集合推导式遍历 {x for x in pdict}"""
        id_set = {x["id"] for x in self.pdict}
        self.assertEqual(id_set, {1, 2, 3})

    def test_paginated_dict_slicing_adversarial_challenge(self):
        """
        [切片攻防挑战] 验证 PaginatedDict 支持切片访问 res[0:2]、res[:1]、res[1:]。
        实证目标: 当切片对象传入 __getitem__ 时，应当返回切片子列表，
        若实现仅判断 isinstance(key, int)，则会将切片委托给 dict.__getitem__ 抛出 KeyError。
        """
        sliced = self.pdict[0:2]
        self.assertEqual(sliced, self.items[0:2])


class AdversarialBugLogic09AccountDeletionPurgingTests(TestCase):
    """
    [BUG-LOGIC-09 对抗实证]
    测试账号注销流程在存在深度交叉关联引用时的彻底清理：
    场景: A 点赞 B 的文章，B 点赞 A 的文章，A 和 B 互赞，A 和 B 互相关注；
    同时存在无关第三方用户 C 与 B 产生互动。
    验证注销 A 时：
    1. A 相关的所有互动（点赞文章、被点赞文章、发出用户赞、收到用户赞、发起关注、被关注）100% 被清理
    2. 绝不抛出 FieldError
    3. C 与 B 的互动数据完好保留，未发生越界误删
    """

    def setUp(self):
        self.tenant = Tenant.objects.create(name="Purge Tenant", code="purge_tenant", status="active")
        self.member_a = Member.objects.create_user(
            username="member_a", email="a@purge.com", password="Password123!", tenant=self.tenant
        )
        self.member_b = Member.objects.create_user(
            username="member_b", email="b@purge.com", password="Password123!", tenant=self.tenant
        )
        self.member_c = Member.objects.create_user(
            username="member_c", email="c@purge.com", password="Password123!", tenant=self.tenant
        )

        self.article_a = Article.objects.create(
            title="Article by A", slug="art-by-a", content="A's content",
            member=self.member_a, tenant=self.tenant
        )
        self.article_b = Article.objects.create(
            title="Article by B", slug="art-by-b", content="B's content",
            member=self.member_b, tenant=self.tenant
        )

        # 交叉点赞文章
        self.like_a_on_b_art = ArticleLike.objects.create(
            from_member=self.member_a, article=self.article_b, tenant=self.tenant
        )
        self.like_b_on_a_art = ArticleLike.objects.create(
            from_member=self.member_b, article=self.article_a, tenant=self.tenant
        )
        self.like_c_on_b_art = ArticleLike.objects.create(
            from_member=self.member_c, article=self.article_b, tenant=self.tenant
        )

        # 交叉用户点赞 (A 和 B 互赞，C 赞 B)
        self.like_a_to_b = MemberLike.objects.create(
            from_member=self.member_a, to_member=self.member_b, tenant=self.tenant
        )
        self.like_b_to_a = MemberLike.objects.create(
            from_member=self.member_b, to_member=self.member_a, tenant=self.tenant
        )
        self.like_c_to_b = MemberLike.objects.create(
            from_member=self.member_c, to_member=self.member_b, tenant=self.tenant
        )

        # 交叉关注 (A 和 B 互关，C 关注 B)
        self.follow_a_to_b = MemberFollow.objects.create(
            follower=self.member_a, following=self.member_b, tenant=self.tenant
        )
        self.follow_b_to_a = MemberFollow.objects.create(
            follower=self.member_b, following=self.member_a, tenant=self.tenant
        )
        self.follow_c_to_b = MemberFollow.objects.create(
            follower=self.member_c, following=self.member_b, tenant=self.tenant
        )

    def test_delete_member_data_cross_referenced_clean_purging(self):
        """实证注销 Member A 时的清理彻底性与隔离保护"""
        member_a_id = self.member_a.id
        member_b_id = self.member_b.id
        member_c_id = self.member_c.id
        article_a_id = self.article_a.id
        article_b_id = self.article_b.id

        view = MemberDeleteAccountConfirmView()

        # 执行注销数据清理，严格断言无任何 FieldError 或未捕获异常
        try:
            deleted_data = view.delete_member_data(self.member_a)
        except Exception as e:
            self.fail(f"delete_member_data 抛出了意外异常: {type(e).__name__}: {e}")

        # 1. 验证涉及 member_a 的所有文章点赞被完全清除
        self.assertEqual(ArticleLike.objects.filter(from_member_id=member_a_id).count(), 0)
        self.assertEqual(ArticleLike.objects.filter(article_id=article_a_id).count(), 0)

        # 2. 验证涉及 member_a 的双向用户互赞完全被清除
        self.assertEqual(MemberLike.objects.filter(Q(from_member_id=member_a_id) | Q(to_member_id=member_a_id)).count(), 0)

        # 3. 验证涉及 member_a 的双向关注完全被清除
        self.assertEqual(MemberFollow.objects.filter(Q(follower_id=member_a_id) | Q(following_id=member_a_id)).count(), 0)

        # 4. 验证 member_a 账号本身已被删除
        self.assertFalse(Member.objects.filter(id=member_a_id).exists())

        # 5. 验证第三方用户 C 与 B 之间的互动记录完好无损，未发生误删越界
        self.assertTrue(ArticleLike.objects.filter(from_member_id=member_c_id, article_id=article_b_id).exists())
        self.assertTrue(MemberLike.objects.filter(from_member_id=member_c_id, to_member_id=member_b_id).exists())
        self.assertTrue(MemberFollow.objects.filter(follower_id=member_c_id, following_id=member_b_id).exists())

        # 6. 验证 deleted_data 准确汇报清理项目
        self.assertTrue(any("Article likes:" in s for s in deleted_data))
        self.assertTrue(any("Member likes:" in s for s in deleted_data))
        self.assertTrue(any("Follows:" in s for s in deleted_data))
        self.assertTrue(any("Articles:" in s for s in deleted_data))


class AdversarialPerf10ComfyUIClientTimeoutsTests(TestCase):
    """
    [PERF-10 对抗实证]
    测试 ComfyUIClient 全部 6 处 HTTP 调用超时参数注入与 Timeout 异常优雅捕获降级
    """

    def setUp(self):
        self.timeout_tuple = (2, 10)
        self.client = ComfyUIClient(base_url="http://127.0.0.1:8188", timeout=self.timeout_tuple)

    @patch("requests.post")
    def test_queue_prompt_passes_timeout_and_handles_timeout_exception(self, mock_post):
        """测试 queue_prompt 正确注入 timeout，并在遭遇 Timeout 异常时优雅返回 None"""
        # 1. 验证携带 timeout 参数
        mock_response = MagicMock()
        mock_response.json.return_value = {"prompt_id": "prompt-adv-1"}
        mock_post.return_value = mock_response

        res = self.client.queue_prompt({"nodes": [], "links": []})
        self.assertEqual(res, "prompt-adv-1")
        self.assertEqual(mock_post.call_args.kwargs.get("timeout"), self.timeout_tuple)

        # 2. 模拟 Timeout 异常，验证不向外抛出异常，优雅返回 None
        mock_post.side_effect = requests.Timeout("Gateway timeout")
        res_timeout = self.client.queue_prompt({"nodes": [], "links": []})
        self.assertIsNone(res_timeout)

    @patch("requests.get")
    def test_wait_for_completion_passes_timeout_and_handles_timeout_exception(self, mock_get):
        """测试 wait_for_completion 在队列查询与历史查询携带 timeout，并在遇到 Timeout 异常时优雅返回 False"""
        # 模拟连续抛出 Timeout 异常
        mock_get.side_effect = requests.Timeout("Queue polling timeout")
        # 设置短外层超时以便单测快速退出
        completed = self.client.wait_for_completion("prompt-adv-wait", timeout=1)
        self.assertFalse(completed)
        # 验证至少发起了带有 timeout 的请求
        self.assertTrue(mock_get.called)
        self.assertEqual(mock_get.call_args.kwargs.get("timeout"), self.timeout_tuple)

    @patch("requests.get")
    def test_get_images_passes_timeout_and_handles_timeout_exception(self, mock_get):
        """测试 get_images 历史查询与图片下载携带 timeout，并在遇到 Timeout 时优雅返回 None"""
        # 1. 模拟历史查询发生 Timeout
        mock_get.side_effect = requests.Timeout("History fetch timeout")
        img = self.client.get_images("prompt-adv-img")
        self.assertIsNone(img)

        # 2. 模拟历史查询成功但图片下载发生 Timeout
        mock_hist_resp = MagicMock()
        mock_hist_resp.status_code = 200
        mock_hist_resp.json.return_value = {
            "prompt-adv-img": {
                "outputs": {"node": {"images": [{"filename": "a.png"}]}}
            }
        }
        mock_get.side_effect = [mock_hist_resp, requests.Timeout("Image download stream timeout")]
        img_download_fail = self.client.get_images("prompt-adv-img")
        self.assertIsNone(img_download_fail)

    @patch("requests.get")
    def test_test_connection_passes_timeout_and_handles_timeout_exception(self, mock_get):
        """测试 test_connection 携带 timeout，并在遇到 Timeout 时优雅返回 False"""
        # 1. 正常响应
        mock_ok = MagicMock()
        mock_ok.status_code = 200
        mock_get.side_effect = None
        mock_get.return_value = mock_ok

        self.assertTrue(self.client.test_connection())
        self.assertEqual(mock_get.call_args.kwargs.get("timeout"), self.timeout_tuple)

        # 2. 模拟 Timeout 异常
        mock_get.side_effect = requests.Timeout("Connection check timed out")
        self.assertFalse(self.client.test_connection())

    @patch("requests.post", side_effect=requests.Timeout("Generate prompt post timeout"))
    def test_generate_image_retry_and_graceful_timeout_handling(self, mock_post):
        """测试 generate_image 全流程在连续网络超时下的重试与优雅退出，绝不产生未捕获异常"""
        self.client.workflow_template = {"nodes": [], "links": []}
        with patch.object(self.client, "modify_workflow", return_value={"nodes": [], "links": []}):
            with patch("time.sleep"):  # 消除重试等待时间
                result = self.client.generate_image("A futuristic city", max_retries=2)
                self.assertIsNone(result)
                self.assertEqual(mock_post.call_count, 2)
