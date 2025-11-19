"""
图片URL处理工具函数
"""
from django.conf import settings
from urllib.parse import urlparse


def normalize_image_path(url, request):
    """
    将图片URL标准化为相对路径（用于存储到数据库）
    
    处理逻辑：
    1. 空值直接返回
    2. 如果是完整URL（http/https）：
       - 检查domain是否匹配当前服务器
       - 匹配则提取相对路径（去掉前缀斜杠）
       - 不匹配则保留完整URL（外部CDN）
    3. 如果是相对路径，去除前缀斜杠
    
    Args:
        url: 图片URL（可能是完整URL或相对路径）
        request: Django请求对象（用于获取当前domain）
    
    Returns:
        str: 标准化的相对路径（如 "media/uploads/3/xxx.jpg"）
             或完整的外部URL（如 "https://cdn.example.com/xxx.jpg"）
    
    示例：
        normalize_image_path("http://localhost:8000/media/uploads/3/xxx.jpg", request)
        => "media/uploads/3/xxx.jpg"
        
        normalize_image_path("/media/uploads/3/xxx.jpg", request)
        => "media/uploads/3/xxx.jpg"
        
        normalize_image_path("https://cdn.example.com/xxx.jpg", request)
        => "https://cdn.example.com/xxx.jpg"
    """
    if not url:
        return url
    
    # 如果是完整URL
    if url.startswith(('http://', 'https://')):
        # 解析URL
        parsed = urlparse(url)
        current_host = request.get_host()
        
        # 如果domain匹配当前服务器
        if parsed.netloc == current_host:
            # 提取路径，去掉前缀斜杠
            path = parsed.path.lstrip('/')
            return path
        else:
            # 外部URL，保持原样
            return url
    
    # 已经是相对路径，去掉前缀斜杠（兼容旧数据）
    return url.lstrip('/')


def add_domain_to_image_url(request, image_url):
    """
    为图片URL添加domain（用于返回给前端）
    
    处理逻辑：
    1. 空值直接返回
    2. 已经是完整URL直接返回
    3. 相对路径添加当前服务器的domain
    
    Args:
        request: Django请求对象
        image_url: 图片URL（相对路径或完整URL）
    
    Returns:
        str: 完整的图片URL
    
    示例：
        add_domain_to_image_url(request, "media/uploads/3/xxx.jpg")
        => "http://localhost:8000/media/uploads/3/xxx.jpg"
        
        add_domain_to_image_url(request, "/media/uploads/3/xxx.jpg")
        => "http://localhost:8000/media/uploads/3/xxx.jpg"
        
        add_domain_to_image_url(request, "https://cdn.example.com/xxx.jpg")
        => "https://cdn.example.com/xxx.jpg"
    """
    if not image_url:
        return image_url
    
    # 如果已经是完整URL（包含http或https），直接返回
    if image_url.startswith(('http://', 'https://')):
        return image_url
    
    # 处理相对路径，确保以/开头
    if not image_url.startswith('/'):
        image_url = f"/{image_url}"
    
    protocol = 'https' if request.is_secure() else 'http'
    domain = request.get_host()
    return f"{protocol}://{domain}{image_url}"


def add_domain_to_image_urls(request, data):
    """
    递归处理数据中的图片URL，为所有图片URL添加domain
    
    Args:
        request: Django请求对象
        data: 要处理的数据（字典、列表或字符串）
    
    Returns:
        处理后的数据
    """
    if isinstance(data, dict):
        return {key: add_domain_to_image_urls(request, value) for key, value in data.items()}
    elif isinstance(data, list):
        return [add_domain_to_image_urls(request, item) for item in data]
    elif isinstance(data, str):
        # 检查是否是图片URL字段
        image_fields = ['avatar', 'cover_image', 'image', 'url', 'og_image', 'seo_image']
        for field in image_fields:
            if field in str(request.path) or field in str(request.data):
                return add_domain_to_image_url(request, data)
        return data
    else:
        return data
