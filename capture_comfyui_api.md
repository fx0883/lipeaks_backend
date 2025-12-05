# 如何捕获ComfyUI的API格式

## 方法1: 使用浏览器开发者工具

1. 打开 http://127.0.0.1:8188/
2. 按 F12 打开开发者工具
3. 切换到 "Network" (网络) 标签
4. 在ComfyUI界面中点击 "Queue Prompt" 运行工作流
5. 在Network标签中找到 `/prompt` 请求
6. 点击该请求，查看 "Payload" (负载) 标签
7. 复制完整的 JSON 数据
8. 将JSON保存到文件：`d:\GitHub\lipeaks_backend\docs\comfyui\api_payload_example.json`

## 方法2: 使用ComfyUI的save API format功能

1. 在ComfyUI界面中加载工作流
2. 点击菜单中的 "Save (API Format)" 
3. 这会下载一个JSON文件
4. 将该文件保存到：`d:\GitHub\lipeaks_backend\docs\comfyui\api_format_workflow.json`

## 我需要的信息

特别关注节点41 (CLIPTextEncodeFlux) 在API格式中的inputs结构：
- 应该包含 `clip` 连接
- 应该包含 `text` 和 `guidance` 参数
- 应该显示 `clip_l` 和 `t5xxl` 如何被引用

有了这个实际的API格式示例，我就能修复转换逻辑了。
