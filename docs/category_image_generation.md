# 分类图片自动生成功能

## 概述

本功能使用ComfyUI和Flux Schnell模型，根据分类名称自动生成高质量的封面图片。支持批量处理、并发生成、自动风格检测等特性。

## 前置要求

1. **ComfyUI服务**
   - 确保ComfyUI已启动: `http://127.0.0.1:8188/`
   - 已安装Flux Schnell模型和必要的组件

2. **数据库配置**

   ```ini
   DB_NAME=multi_tenant_db_dev
   DB_USER=root
   DB_PASSWORD=123456
   DB_HOST=localhost
   DB_PORT=3306
   ```

3. **Python依赖**

   ```bash
   pip install requests websocket-client pillow
   ```

## 功能特性

### 1. 智能风格检测

系统会根据分类名称自动选择合适的图片风格：

- **tech**: 科技、编程、AI相关
- **business**: 商业、金融、管理相关
- **nature**: 自然、环境、健康相关
- **creative**: 艺术、设计、创意相关
- **modern**: 默认现代简约风格

### 2. 提示词优化

- 自动增强提示词质量
- 添加专业渲染关键词
- 支持多语言分类名称

### 3. 批量处理

- 支持处理所有分类或指定分类
- 可并发生成提高效率
- 断点续传能力

## 使用方法

### 1. 测试连接

首先运行测试脚本确保所有组件正常：

```bash
cd d:\GitHub\lipeaks_backend
python test_comfyui_generation.py
```

### 2. 基本使用

更新租户3的所有分类图片：

```bash
python manage.py update_category_images --tenant-id 3
```

### 3. 高级选项

#### 指定特定分类

```bash
python manage.py update_category_images --tenant-id 3 --category-ids 10,11,12
```

#### 使用并发加速

```bash
python manage.py update_category_images --tenant-id 3 --concurrent 3
```

#### 跳过已有图片

```bash
python manage.py update_category_images --tenant-id 3 --skip-existing
```

#### 备份原图片

```bash
python manage.py update_category_images --tenant-id 3 --backup
```

#### 指定图片尺寸

```bash
python manage.py update_category_images --tenant-id 3 --width 800 --height 450
```

#### 强制使用特定风格

```bash
python manage.py update_category_images --tenant-id 3 --style tech
```

#### 模拟运行（不实际生成）

```bash
python manage.py update_category_images --tenant-id 3 --dry-run
```

#### 使用英文分类名称

```bash
python manage.py update_category_images --tenant-id 3 --language en
```

### 4. 完整示例

处理租户3的分类10-20，使用3个并发，备份原图，跳过已有图片：

```bash
python manage.py update_category_images \
    --tenant-id 3 \
    --category-ids 10,11,12,13,14,15,16,17,18,19,20 \
    --concurrent 3 \
    --backup \
    --skip-existing
```

## 文件结构

```text
lipeaks_backend/
├── cms/
│   ├── management/
│   │   └── commands/
│   │       └── update_category_images.py  # Django管理命令
│   └── utils/
│       ├── comfyui_client.py             # ComfyUI API客户端
│       └── prompt_generator.py           # 提示词生成器
├── media/
│   └── category_image/                   # 生成的图片存储位置
│       ├── 10.png
│       ├── 11.png
│       └── ...
└── docs/
    └── comfyui/
        └── flux_schnell_full_text_to_image.json  # 工作流模板
```

## 工作原理

1. **查询分类**: 从数据库获取指定租户的分类信息
2. **生成提示词**: 根据分类名称和检测到的风格生成优化的提示词
3. **修改工作流**: 动态调整ComfyUI工作流参数（尺寸、提示词等）
4. **提交任务**: 将工作流提交到ComfyUI队列
5. **等待完成**: 轮询任务状态直到生成完成
6. **下载保存**: 下载生成的图片并保存到指定位置
7. **更新数据库**: 更新分类的cover_image字段

## 故障排除

### ComfyUI连接失败

- 检查ComfyUI是否已启动
- 确认端口8188未被占用
- 尝试访问 `http://127.0.0.1:8188/`

### 图片生成失败

- 检查模型是否已下载完整
- 查看ComfyUI控制台错误信息
- 降低并发数量重试

### 数据库连接错误

- 验证数据库配置正确
- 确认MySQL服务运行中
- 检查用户权限

## 性能优化建议

1. **并发数量**: 建议不超过3个，避免内存溢出
2. **批处理**: 大量分类时分批处理
3. **缓存模型**: 确保模型已预加载到内存
4. **网络优化**: 使用本地ComfyUI服务

## 注意事项

- 生成每张图片约需30-60秒（取决于硬件）
- 建议先用少量分类测试
- 备份重要的原始图片
- 监控磁盘空间使用

## 扩展功能

未来可以添加的功能：
- 图片质量评分和自动重试
- 支持更多AI模型
- 批量预览和人工筛选
- 自动压缩和优化
- CDN上传集成
