# 静态文件与媒体文件配置

本文档将指导您在cPanel环境中配置Django项目的静态文件和媒体文件，确保它们可以正确地被访问和服务。

## 静态文件与媒体文件概述

在Django项目中，有两种主要类型的文件需要特殊处理：

1. **静态文件**：CSS、JavaScript、图像等不会改变的文件，通常由开发者创建并与应用程序一起部署。
2. **媒体文件**：用户上传的文件，如头像、文档等，在应用程序运行时动态生成。

在生产环境中，这些文件通常由Web服务器（如Apache）直接提供，而不是通过Django应用程序，以提高性能。

## 配置静态文件

### 1. 调整Django设置

首先，确保`settings.py`中的静态文件配置正确：

```python
# 静态文件URL（浏览器访问路径）
STATIC_URL = '/static/'

# 静态文件收集目录（服务器文件系统路径）
STATIC_ROOT = os.path.join(os.path.dirname(BASE_DIR), 'public_html/static')

# 开发环境的静态文件目录（可选）
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]
```

### 2. 收集静态文件

执行Django的`collectstatic`命令，将所有静态文件收集到`STATIC_ROOT`目录：

```bash
# 激活虚拟环境
source ~/virtualenv/lipeaks_backend/3.12/bin/activate

# 切换到项目目录
cd ~/lipeaks_backend

# 收集静态文件
python manage.py collectstatic --noinput
```

### 3. 确保静态文件目录存在

如果`STATIC_ROOT`目录不存在，需要创建它：

```bash
# 创建静态文件目录
mkdir -p ~/public_html/static
```

### 4. 设置适当的权限

确保Web服务器可以访问静态文件目录：

```bash
# 设置目录权限
chmod -R 755 ~/public_html/static
```

### 5. 创建符号链接（如果需要）

如果您的项目目录不在`public_html`中，可以创建符号链接：

```bash
# 确保目标目录存在
mkdir -p ~/lipeaks_backend/staticfiles

# 创建符号链接
ln -sf ~/lipeaks_backend/staticfiles/* ~/public_html/static/
```

## 配置媒体文件

### 1. 调整Django设置

确保`settings.py`中的媒体文件配置正确：

```python
# 媒体文件URL（浏览器访问路径）
MEDIA_URL = '/media/'

# 媒体文件存储目录（服务器文件系统路径）
MEDIA_ROOT = os.path.join(os.path.dirname(BASE_DIR), 'public_html/media')
```

### 2. 创建媒体文件目录

```bash
# 创建媒体文件目录
mkdir -p ~/public_html/media

# 设置适当的权限
chmod -R 755 ~/public_html/media
```

### 3. 创建符号链接（如果需要）

如果您的项目目录不在`public_html`中，可以创建符号链接：

```bash
# 确保目标目录存在
mkdir -p ~/lipeaks_backend/media

# 创建符号链接
ln -sf ~/lipeaks_backend/media/* ~/public_html/media/
```

## 配置Apache处理静态和媒体文件

在cPanel环境中，Apache通常已配置为处理`public_html`目录中的文件。但您可能需要添加一些额外的配置来优化静态文件和媒体文件的处理。

### 创建.htaccess文件

在`public_html`目录中创建或修改`.htaccess`文件：

```bash
# 创建或编辑.htaccess文件
cat > ~/public_html/.htaccess << 'EOL'
# 启用Apache的重写引擎
RewriteEngine On

# 如果请求的是静态文件或媒体文件，直接提供
RewriteCond %{REQUEST_URI} ^/static/ [OR]
RewriteCond %{REQUEST_URI} ^/media/
RewriteRule ^(.*)$ - [L]

# 为静态文件和媒体文件设置缓存控制
<FilesMatch "\.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$">
    Header set Cache-Control "max-age=2592000, public"
</FilesMatch>

# 压缩文本文件
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/html text/plain text/xml text/css application/javascript application/json
</IfModule>

# 禁止直接访问某些类型的文件
<FilesMatch "\.(py|pyc|sqlite3|env)$">
    Order allow,deny
    Deny from all
</FilesMatch>

# 如果不是文件或目录，将请求转发到Passenger
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ /passenger_wsgi.py/$1 [QSA,L]
EOL
```

## 验证静态文件和媒体文件配置

### 1. 验证静态文件

创建一个简单的测试文件：

```bash
# 创建测试文件
echo "This is a test file" > ~/public_html/static/test.txt
```

然后，在浏览器中访问 `https://yourdomain.com/static/test.txt`，确认文件可以正常访问。

### 2. 验证媒体文件

创建一个简单的测试文件：

```bash
# 创建测试文件
echo "This is a media test file" > ~/public_html/media/test.txt
```

然后，在浏览器中访问 `https://yourdomain.com/media/test.txt`，确认文件可以正常访问。

## 优化静态文件和媒体文件服务

### 1. 使用内容分发网络（CDN）

如果您的网站有全球用户，可以考虑使用CDN来提供静态文件：

1. 注册CDN服务（如Cloudflare、Amazon CloudFront等）
2. 配置CDN以缓存您的静态文件和媒体文件
3. 更新`settings.py`中的`STATIC_URL`和`MEDIA_URL`以指向CDN URL

### 2. 图像优化

为了减少页面加载时间，优化上传的图像：

```bash
# 创建图像优化脚本
cat > ~/lipeaks_backend/optimize_images.py << 'EOL'
#!/usr/bin/env python
import os
import sys
from PIL import Image
import concurrent.futures

def optimize_image(filepath):
    """优化单个图像文件"""
    try:
        # 检查文件是否为图像
        if not filepath.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            return f"跳过非图像文件: {filepath}"
        
        # 打开图像
        img = Image.open(filepath)
        
        # 保存原始文件大小
        original_size = os.path.getsize(filepath)
        
        # 创建优化后的文件路径
        filename, ext = os.path.splitext(filepath)
        optimized_path = f"{filename}_optimized{ext}"
        
        # 保存优化后的图像
        if ext.lower() in ['.jpg', '.jpeg']:
            img.save(optimized_path, 'JPEG', quality=85, optimize=True)
        elif ext.lower() == '.png':
            img.save(optimized_path, 'PNG', optimize=True)
        elif ext.lower() == '.gif':
            img.save(optimized_path, 'GIF', optimize=True)
        
        # 检查优化后的文件大小
        optimized_size = os.path.getsize(optimized_path)
        
        # 如果优化后的文件更小，则替换原始文件
        if optimized_size < original_size:
            os.replace(optimized_path, filepath)
            return f"优化成功: {filepath} ({original_size/1024:.1f}KB -> {optimized_size/1024:.1f}KB, 节省 {(original_size-optimized_size)/original_size*100:.1f}%)"
        else:
            os.remove(optimized_path)
            return f"无需优化: {filepath} (已是最佳大小)"
    
    except Exception as e:
        return f"处理 {filepath} 时出错: {str(e)}"

def optimize_directory(directory):
    """优化目录中的所有图像"""
    image_files = []
    
    # 收集所有图像文件
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                image_files.append(os.path.join(root, file))
    
    print(f"找到 {len(image_files)} 个图像文件")
    
    # 使用线程池并行优化图像
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(optimize_image, image_files))
    
    # 打印结果
    for result in results:
        print(result)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        directory = sys.argv[1]
    else:
        directory = os.path.join(os.path.expanduser('~'), 'public_html/media')
    
    print(f"正在优化目录: {directory}")
    optimize_directory(directory)
EOL

# 设置执行权限
chmod +x ~/lipeaks_backend/optimize_images.py
```

### 3. 设置定期图像优化任务

```bash
# 在cPanel中设置cron作业，每周优化一次图像
(crontab -l 2>/dev/null; echo "0 3 * * 0 cd ~/lipeaks_backend && python optimize_images.py >> ~/image_optimization.log 2>&1") | crontab -
```

## 监控文件使用情况

创建一个脚本来监控静态文件和媒体文件的使用情况：

```bash
# 创建监控脚本
cat > ~/monitor_files.sh << 'EOL'
#!/bin/bash

# 设置目录
STATIC_DIR=~/public_html/static
MEDIA_DIR=~/public_html/media

# 输出标题
echo "文件使用情况报告 - $(date)"
echo "================================="

# 检查静态文件目录
echo "静态文件目录 ($STATIC_DIR):"
echo "总大小: $(du -sh $STATIC_DIR | cut -f1)"
echo "文件数量: $(find $STATIC_DIR -type f | wc -l)"
echo "按类型统计:"
find $STATIC_DIR -type f | grep -o '\.[^\.]*$' | sort | uniq -c | sort -nr

echo ""

# 检查媒体文件目录
echo "媒体文件目录 ($MEDIA_DIR):"
echo "总大小: $(du -sh $MEDIA_DIR | cut -f1)"
echo "文件数量: $(find $MEDIA_DIR -type f | wc -l)"
echo "按类型统计:"
find $MEDIA_DIR -type f | grep -o '\.[^\.]*$' | sort | uniq -c | sort -nr

echo ""

# 检查最大的文件
echo "最大的10个文件:"
find $STATIC_DIR $MEDIA_DIR -type f -exec ls -lh {} \; | sort -k5 -hr | head -10 | awk '{print $5, $9}'

echo "================================="
EOL

# 设置执行权限
chmod +x ~/monitor_files.sh
```

## 下一步

完成静态文件和媒体文件配置后，您可以继续[域名配置与应用启动](07_domain_launch.md)。 