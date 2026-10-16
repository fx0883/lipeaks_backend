"""
ComfyUI 客户端 HTTP 超时与健壮性单元测试 (PERF-10)
"""
from unittest.mock import patch, MagicMock
import requests
from django.test import TestCase
from cms.utils.comfyui_client import ComfyUIClient


class ComfyUIClientTimeoutTests(TestCase):
    def setUp(self):
        self.custom_timeout = (3, 15)
        self.client = ComfyUIClient(base_url="http://127.0.0.1:8188", timeout=self.custom_timeout)

    def test_default_timeout_configuration(self):
        """测试未传入超时时默认使用 (5, 30)"""
        default_client = ComfyUIClient(base_url="http://127.0.0.1:8188")
        self.assertEqual(default_client.timeout, (5, 30))

    @patch("requests.post")
    def test_queue_prompt_passes_timeout(self, mock_post):
        """测试 queue_prompt 发送请求时正确携带 timeout 参数"""
        mock_response = MagicMock()
        mock_response.json.return_value = {"prompt_id": "prompt-12345"}
        mock_post.return_value = mock_response

        workflow = {"nodes": [], "links": []}
        prompt_id = self.client.queue_prompt(workflow)

        self.assertEqual(prompt_id, "prompt-12345")
        self.assertEqual(mock_post.call_args.kwargs.get("timeout"), self.custom_timeout)

    @patch("requests.get")
    def test_wait_for_completion_passes_timeout(self, mock_get):
        """测试 wait_for_completion 检查队列和历史时正确携带 timeout 参数"""
        mock_queue_resp = MagicMock()
        mock_queue_resp.json.return_value = {"queue_running": [], "queue_pending": []}
        mock_queue_resp.status_code = 200

        mock_hist_resp = MagicMock()
        mock_hist_resp.status_code = 200
        mock_hist_resp.json.return_value = {
            "prompt-test": {
                "outputs": {"node-1": {"images": [{"filename": "out.png"}]}}
            }
        }

        mock_get.side_effect = [mock_queue_resp, mock_hist_resp]

        success = self.client.wait_for_completion("prompt-test", timeout=10)
        self.assertTrue(success)

        # 验证两次 get 调用均携带 timeout
        for call_item in mock_get.call_args_list:
            self.assertEqual(call_item.kwargs.get("timeout"), self.custom_timeout)

    @patch("requests.get")
    def test_get_images_passes_timeout_and_stream(self, mock_get):
        """测试 get_images 查询历史与下载图片携带 timeout 且下载图片使用流式分块"""
        mock_hist_resp = MagicMock()
        mock_hist_resp.status_code = 200
        mock_hist_resp.json.return_value = {
            "prompt-img": {
                "outputs": {
                    "9": {
                        "images": [
                            {"filename": "test.png", "subfolder": "", "type": "output"}
                        ]
                    }
                }
            }
        }

        mock_img_resp = MagicMock()
        mock_img_resp.status_code = 200
        mock_img_resp.iter_content.return_value = [b"chunk1_", b"chunk2_image_data"]
        # 支持 with 上下文管理器
        mock_img_resp.__enter__.return_value = mock_img_resp
        mock_img_resp.__exit__.return_value = False

        mock_get.side_effect = [mock_hist_resp, mock_img_resp]

        image_data = self.client.get_images("prompt-img")
        self.assertEqual(image_data, b"chunk1_chunk2_image_data")

        # 检查下载图片的调用参数
        download_call = mock_get.call_args_list[1]
        self.assertEqual(download_call.kwargs.get("timeout"), self.custom_timeout)
        self.assertTrue(download_call.kwargs.get("stream"))

    @patch("requests.get")
    def test_test_connection_passes_timeout(self, mock_get):
        """测试 test_connection 正确携带 timeout 参数"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        success = self.client.test_connection()
        self.assertTrue(success)
        self.assertEqual(mock_get.call_args.kwargs.get("timeout"), self.custom_timeout)

    @patch("requests.get", side_effect=requests.Timeout("Connection timed out"))
    def test_connection_handles_timeout_gracefully(self, mock_get):
        """测试 test_connection 在超时异常时优雅捕获并返回 False"""
        success = self.client.test_connection()
        self.assertFalse(success)
