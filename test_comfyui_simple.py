"""
简单测试ComfyUI连接和图片生成
"""
import requests
import json
import time
from pathlib import Path

def test_connection():
    """测试ComfyUI连接"""
    print("测试ComfyUI连接...")
    try:
        response = requests.get("http://127.0.0.1:8188/system_stats")
        if response.status_code == 200:
            print("✓ ComfyUI服务器连接成功")
            stats = response.json()
            print(f"  系统信息: {stats.get('system', {})}")
            return True
    except Exception as e:
        print(f"✗ ComfyUI服务器连接失败: {e}")
    return False

def test_workflow_submission():
    """测试提交工作流"""
    print("\n测试工作流提交...")
    
    # 加载工作流模板
    workflow_path = Path("d:/GitHub/lipeaks_backend/docs/comfyui/flux_schnell_full_text_to_image.json")
    with open(workflow_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)
    
    # 移除不支持的节点
    workflow['nodes'] = [
        node for node in workflow.get('nodes', [])
        if node.get('type') != 'MarkdownNote'
    ]
    
    # 修改参数
    for node in workflow.get('nodes', []):
        if node.get('id') == 27:  # EmptySD3LatentImage
            node['widgets_values'] = [670, 360, 1]
            print("  已设置图片尺寸: 670x360")
        elif node.get('id') == 41:  # CLIPTextEncodeFlux
            node['widgets_values'][0] = "Technology innovation concept, modern digital art style"
            print("  已设置提示词")
    
    # 转换为API格式
    api_workflow = convert_to_api_format(workflow)
    
    # 提交工作流
    import uuid
    client_id = str(uuid.uuid4())
    payload = {
        "prompt": api_workflow,
        "client_id": client_id
    }
    
    try:
        response = requests.post(
            "http://127.0.0.1:8188/prompt",
            json=payload
        )
        if response.status_code == 200:
            result = response.json()
            prompt_id = result.get('prompt_id')
            print(f"✓ 工作流已提交，prompt_id: {prompt_id}")
            return prompt_id
        else:
            print(f"✗ 提交失败: {response.status_code}")
            print(f"  响应: {response.text}")
    except Exception as e:
        print(f"✗ 提交异常: {e}")
    
    return None

def convert_to_api_format(workflow):
    """转换工作流格式"""
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
            api_node["inputs"] = map_widget_values_to_inputs(
                node['type'],
                node['widgets_values']
            )
        
        # 添加连接输入
        if node['id'] in connections:
            api_node["inputs"].update(connections[node['id']])
        
        api_format[node_id] = api_node
    
    return api_format

def map_widget_values_to_inputs(node_type, widget_values):
    """映射widget值到输入"""
    inputs = {}
    
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
        # clip连接会通过connections处理
            
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
            # 添加device参数
            inputs["device"] = "default"
                
    elif node_type == "SaveImage":
        if len(widget_values) >= 1:
            inputs["filename_prefix"] = widget_values[0]
    
    return inputs

def wait_for_result(prompt_id, timeout=60):
    """等待生成结果"""
    print(f"\n等待生成完成...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            # 检查历史
            response = requests.get(f"http://127.0.0.1:8188/history/{prompt_id}")
            if response.status_code == 200:
                history_data = response.json()
                if prompt_id in history_data:
                    outputs = history_data[prompt_id].get('outputs', {})
                    if outputs:
                        print(f"✓ 生成完成")
                        
                        # 查找图片
                        for node_id, node_output in outputs.items():
                            if 'images' in node_output:
                                images = node_output['images']
                                if images:
                                    print(f"  找到 {len(images)} 张图片")
                                    return True
                        return False
            
            # 检查队列状态
            queue_response = requests.get("http://127.0.0.1:8188/queue")
            if queue_response.status_code == 200:
                queue_data = queue_response.json()
                queue_running = queue_data.get('queue_running', [])
                queue_pending = queue_data.get('queue_pending', [])
                
                for item in queue_running:
                    if item[1] == prompt_id:
                        print(f"  正在执行...")
                        break
                
                for item in queue_pending:
                    if item[1] == prompt_id:
                        print(f"  在队列中等待...")
                        break
            
            time.sleep(2)
            
        except Exception as e:
            print(f"  检查状态异常: {e}")
            time.sleep(2)
    
    print(f"✗ 生成超时")
    return False

def main():
    print("=" * 50)
    print("ComfyUI 简单测试")
    print("=" * 50)
    
    # 测试连接
    if not test_connection():
        print("\n请确保ComfyUI服务已启动在 http://127.0.0.1:8188/")
        return False
    
    # 测试工作流提交
    prompt_id = test_workflow_submission()
    if not prompt_id:
        print("\n工作流提交失败")
        return False
    
    # 等待结果
    success = wait_for_result(prompt_id)
    
    print("\n" + "=" * 50)
    if success:
        print("✓ 测试通过！可以使用主命令：")
        print("  python manage.py update_category_images --tenant-id 3")
    else:
        print("✗ 测试失败，请检查ComfyUI配置")
    
    return success

if __name__ == "__main__":
    success = main()
    import sys
    sys.exit(0 if success else 1)
