"""
ComfyUI API 客户端
用于与ComfyUI服务器交互，生成图片
"""
import json
import time
import uuid
import requests
from typing import Optional, Dict, Any
from pathlib import Path
import logging
import websocket
import threading

logger = logging.getLogger(__name__)


class ComfyUIClient:
    """ComfyUI API客户端"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8188"):
        """
        初始化ComfyUI客户端
        
        Args:
            base_url: ComfyUI服务器地址
        """
        self.base_url = base_url.rstrip('/')
        self.client_id = str(uuid.uuid4())
        self.workflow_template = None
        self._ws = None
        self._ws_messages = []
        
    def connect_websocket(self):
        """连接WebSocket以接收实时更新"""
        try:
            ws_url = self.base_url.replace("http://", "ws://").replace("https://", "wss://")
            self._ws = websocket.WebSocketApp(
                f"{ws_url}/ws?clientId={self.client_id}",
                on_message=self._on_ws_message,
                on_error=self._on_ws_error,
                on_close=self._on_ws_close
            )
            
            # 在后台线程运行WebSocket
            ws_thread = threading.Thread(target=self._ws.run_forever)
            ws_thread.daemon = True
            ws_thread.start()
            
            # 等待连接建立
            time.sleep(1)
            logger.info("WebSocket连接已建立")
        except Exception as e:
            logger.warning(f"WebSocket连接失败: {e}，将使用轮询模式")
            
    def _on_ws_message(self, ws, message):
        """处理WebSocket消息"""
        try:
            data = json.loads(message)
            self._ws_messages.append(data)
        except:
            pass
            
    def _on_ws_error(self, ws, error):
        """处理WebSocket错误"""
        logger.error(f"WebSocket错误: {error}")
        
    def _on_ws_close(self, ws, close_status_code, close_msg):
        """处理WebSocket关闭"""
        logger.info("WebSocket连接已关闭")
        
    def load_workflow_template(self, template_path: Optional[str] = None) -> Dict:
        """
        加载工作流模板
        
        Args:
            template_path: 模板文件路径，如果为None则使用默认模板
            
        Returns:
            工作流字典
        """
        if template_path is None:
            # 使用默认的flux_schnell模板
            template_path = Path(__file__).parent.parent.parent / "docs" / "comfyui" / "flux_schnell_full_text_to_image.json"
            
        with open(template_path, 'r', encoding='utf-8') as f:
            self.workflow_template = json.load(f)
            
        return self.workflow_template
        
    def modify_workflow(self, workflow: Dict, prompt: str, width: int = 670, height: int = 360) -> Dict:
        """
        修改工作流参数
        
        Args:
            workflow: 工作流字典
            prompt: 生成图片的提示词
            width: 图片宽度
            height: 图片高度
            
        Returns:
            修改后的工作流字典
        """
        # 深拷贝工作流
        import copy
        modified_workflow = copy.deepcopy(workflow)
        
        # 移除不支持的节点（如MarkdownNote）
        modified_workflow['nodes'] = [
            node for node in modified_workflow.get('nodes', [])
            if node.get('type') != 'MarkdownNote'
        ]
        
        # 修改图片尺寸 (节点27 - EmptySD3LatentImage)
        for node in modified_workflow.get('nodes', []):
            if node.get('id') == 27 and node.get('type') == 'EmptySD3LatentImage':
                node['widgets_values'] = [width, height, 1]  # width, height, batch_size
                logger.debug(f"设置图片尺寸: {width}x{height}")
                
            # 修改提示词 (节点41 - CLIPTextEncodeFlux)
            elif node.get('id') == 41 and node.get('type') == 'CLIPTextEncodeFlux':
                # 如果prompt是字典（来自PromptGenerator），提取clip_l和t5xxl
                if isinstance(prompt, dict):
                    clip_l_prompt = prompt.get('clip_l', prompt.get('main_prompt', ''))
                    t5xxl_prompt = prompt.get('t5xxl', prompt.get('guidance_prompt', ''))
                else:
                    # 简单字符串，使用默认增强
                    from cms.utils.prompt_generator import PromptGenerator
                    pg = PromptGenerator()
                    prompt_data = pg.generate_prompt(prompt)
                    clip_l_prompt = prompt_data['clip_l']
                    t5xxl_prompt = prompt_data['t5xxl']
                
                node['widgets_values'] = [
                    clip_l_prompt,   # clip_l文本
                    t5xxl_prompt,    # t5xxl文本
                    3.5,             # guidance值
                    [False, True],   # speak_and_recognation设置
                    [False, True]    # 其他设置
                ]
                logger.debug(f"设置提示词 clip_l: {clip_l_prompt[:50]}...")
                
        return modified_workflow
        
    def queue_prompt(self, workflow: Dict) -> Optional[str]:
        """
        将工作流提交到ComfyUI队列
        
        Args:
            workflow: 工作流字典
            
        Returns:
            提示ID，如果失败返回None
        """
        # 转换工作流格式为API格式
        api_workflow = self._convert_to_api_format(workflow)
        
        payload = {
            "prompt": api_workflow,
            "client_id": self.client_id
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/prompt",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            prompt_id = result.get('prompt_id')
            logger.info(f"工作流已提交，prompt_id: {prompt_id}")
            return prompt_id
            
        except requests.RequestException as e:
            logger.error(f"提交工作流失败: {e}")
            return None
            
    def _convert_to_api_format(self, workflow: Dict) -> Dict:
        """
        将工作流转换为ComfyUI API格式
        
        Args:
            workflow: 原始工作流格式
            
        Returns:
            API格式的工作流
        """
        api_format = {}
        
        # 构建节点映射
        nodes_by_id = {node['id']: node for node in workflow.get('nodes', [])}
        
        # 构建连接映射
        connections = {}
        for link in workflow.get('links', []):
            link_id, from_node, from_slot, to_node, to_slot, data_type = link
            
            if to_node not in connections:
                connections[to_node] = {}
            
            # 获取输入名称
            if to_node in nodes_by_id:
                target_node = nodes_by_id[to_node]
                if 'inputs' in target_node and to_slot < len(target_node['inputs']):
                    input_name = target_node['inputs'][to_slot]['name']
                    connections[to_node][input_name] = [str(from_node), from_slot]
                    
        # 构建API格式
        for node in workflow.get('nodes', []):
            node_id = str(node['id'])
            
            api_node = {
                "class_type": node.get('type', ''),
                "inputs": {}
            }
            
            # 添加widget值
            if 'widgets_values' in node:
                # 根据节点类型映射widget值到输入
                api_node["inputs"] = self._map_widget_values_to_inputs(
                    node['type'],
                    node['widgets_values']
                )
                
            # 添加连接输入
            if node['id'] in connections:
                api_node["inputs"].update(connections[node['id']])
                
            api_format[node_id] = api_node
            
        return api_format
        
    def _map_widget_values_to_inputs(self, node_type: str, widget_values: list) -> Dict:
        """
        将widget值映射到输入参数
        
        Args:
            node_type: 节点类型
            widget_values: widget值列表
            
        Returns:
            输入参数字典
        """
        inputs = {}
        
        # 根据不同节点类型进行映射
        if node_type == "EmptySD3LatentImage":
            if len(widget_values) >= 3:
                inputs["width"] = widget_values[0]
                inputs["height"] = widget_values[1]
                inputs["batch_size"] = widget_values[2]
                
        elif node_type == "CLIPTextEncodeFlux":
            # widget_values: [clip_l文本, t5xxl文本, guidance值, speak_and_recognation, ...]
            if len(widget_values) >= 1:
                inputs["clip_l"] = widget_values[0]  # 第一个文本提示词
            if len(widget_values) >= 2 and isinstance(widget_values[1], str):
                inputs["t5xxl"] = widget_values[1]  # 第二个文本提示词
            if len(widget_values) >= 3 and isinstance(widget_values[2], (int, float)):
                inputs["guidance"] = float(widget_values[2])  # guidance值
            # clip连接会通过_convert_to_api_format中的connections处理
                
        elif node_type == "KSampler":
            if len(widget_values) >= 7:
                inputs["seed"] = widget_values[0]
                inputs["control_after_generate"] = widget_values[1]
                inputs["steps"] = widget_values[2]
                inputs["cfg"] = widget_values[3]
                inputs["sampler_name"] = widget_values[4]
                inputs["scheduler"] = widget_values[5]
                inputs["denoise"] = widget_values[6]
                
        elif node_type == "VAELoader":
            if len(widget_values) >= 1:
                inputs["vae_name"] = widget_values[0]
                
        elif node_type == "UNETLoader":
            if len(widget_values) >= 1:
                inputs["unet_name"] = widget_values[0]
                if len(widget_values) >= 2:
                    inputs["weight_dtype"] = widget_values[1]
                    
        elif node_type == "DualCLIPLoader":
            if len(widget_values) >= 2:
                inputs["clip_name1"] = widget_values[0]
                inputs["clip_name2"] = widget_values[1]
                if len(widget_values) >= 3:
                    inputs["type"] = widget_values[2]
                # 添加device参数（默认值）
                inputs["device"] = "default"
                    
        elif node_type == "SaveImage":
            if len(widget_values) >= 1:
                inputs["filename_prefix"] = widget_values[0]
                
        return inputs
        
    def wait_for_completion(self, prompt_id: str, timeout: int = 300) -> bool:
        """
        等待任务完成
        
        Args:
            prompt_id: 提示ID
            timeout: 超时时间（秒）
            
        Returns:
            是否成功完成
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # 检查队列状态
                response = requests.get(f"{self.base_url}/queue")
                response.raise_for_status()
                
                queue_data = response.json()
                
                # 检查是否在运行队列中
                queue_running = queue_data.get('queue_running', [])
                for item in queue_running:
                    if item[1] == prompt_id:
                        logger.debug(f"任务 {prompt_id} 正在执行...")
                        time.sleep(2)
                        break
                else:
                    # 不在运行队列中，检查是否在等待队列中
                    queue_pending = queue_data.get('queue_pending', [])
                    for item in queue_pending:
                        if item[1] == prompt_id:
                            logger.debug(f"任务 {prompt_id} 正在等待...")
                            time.sleep(2)
                            break
                    else:
                        # 既不在运行队列也不在等待队列，检查历史
                        history_response = requests.get(f"{self.base_url}/history/{prompt_id}")
                        if history_response.status_code == 200:
                            history_data = history_response.json()
                            if prompt_id in history_data:
                                # 任务已完成
                                outputs = history_data[prompt_id].get('outputs', {})
                                if outputs:
                                    logger.info(f"任务 {prompt_id} 已完成")
                                    return True
                                else:
                                    logger.error(f"任务 {prompt_id} 完成但无输出")
                                    return False
                        
                        # 任务可能失败或被取消
                        time.sleep(2)
                        
            except requests.RequestException as e:
                logger.error(f"检查任务状态失败: {e}")
                time.sleep(5)
                
        logger.error(f"任务 {prompt_id} 超时")
        return False
        
    def get_images(self, prompt_id: str) -> Optional[bytes]:
        """
        获取生成的图片
        
        Args:
            prompt_id: 提示ID
            
        Returns:
            图片字节数据，如果失败返回None
        """
        try:
            # 获取历史记录
            response = requests.get(f"{self.base_url}/history/{prompt_id}")
            response.raise_for_status()
            
            history = response.json()
            
            if prompt_id not in history:
                logger.error(f"找不到任务 {prompt_id} 的历史记录")
                return None
                
            # 查找输出图片
            outputs = history[prompt_id].get('outputs', {})
            
            for node_id, node_output in outputs.items():
                if 'images' in node_output:
                    images = node_output['images']
                    if images and len(images) > 0:
                        # 获取第一张图片
                        image_info = images[0]
                        filename = image_info['filename']
                        subfolder = image_info.get('subfolder', '')
                        folder_type = image_info.get('type', 'output')
                        
                        # 下载图片
                        params = {
                            'filename': filename,
                            'subfolder': subfolder,
                            'type': folder_type
                        }
                        
                        image_response = requests.get(
                            f"{self.base_url}/view",
                            params=params
                        )
                        image_response.raise_for_status()
                        
                        logger.info(f"成功获取图片: {filename}")
                        return image_response.content
                        
            logger.error(f"任务 {prompt_id} 没有生成图片")
            return None
            
        except requests.RequestException as e:
            logger.error(f"获取图片失败: {e}")
            return None
            
    def generate_image(self, prompt: str, width: int = 670, height: int = 360, 
                      max_retries: int = 3) -> Optional[bytes]:
        """
        生成图片的完整流程
        
        Args:
            prompt: 提示词
            width: 图片宽度
            height: 图片高度
            max_retries: 最大重试次数
            
        Returns:
            图片字节数据，如果失败返回None
        """
        for attempt in range(max_retries):
            try:
                # 获取提示词用于日志
                prompt_str = prompt.get('clip_l', str(prompt))[:50] if isinstance(prompt, dict) else str(prompt)[:50]
                logger.info(f"开始生成图片 (尝试 {attempt + 1}/{max_retries}): {prompt_str}...")
                
                # 加载工作流模板
                if self.workflow_template is None:
                    self.load_workflow_template()
                    
                # 修改工作流参数
                workflow = self.modify_workflow(
                    self.workflow_template,
                    prompt,
                    width,
                    height
                )
                
                # 提交到队列
                prompt_id = self.queue_prompt(workflow)
                if not prompt_id:
                    logger.error("提交工作流失败")
                    continue
                    
                # 等待完成
                if not self.wait_for_completion(prompt_id):
                    logger.error("等待任务完成超时或失败")
                    continue
                    
                # 获取图片
                image_data = self.get_images(prompt_id)
                if image_data:
                    return image_data
                    
            except Exception as e:
                logger.error(f"生成图片异常: {e}")
                
            if attempt < max_retries - 1:
                logger.info(f"等待5秒后重试...")
                time.sleep(5)
                
        logger.error(f"生成图片失败，已重试{max_retries}次")
        return None
        
    def test_connection(self) -> bool:
        """
        测试与ComfyUI服务器的连接
        
        Returns:
            连接是否正常
        """
        try:
            response = requests.get(f"{self.base_url}/system_stats")
            response.raise_for_status()
            logger.info("ComfyUI服务器连接正常")
            return True
        except requests.RequestException as e:
            logger.error(f"ComfyUI服务器连接失败: {e}")
            return False
