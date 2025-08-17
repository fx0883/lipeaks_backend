"""
图片URL处理工具函数
"""
from django.conf import settings


def add_domain_to_image_url(request, image_url):
    """
    为图片URL添加domain
    
    Args:
        request: Django请求对象
        image_url: 图片URL（相对路径或完整URL）
    
    Returns:
        str: 完整的图片URL
    """
    if not image_url:
        return image_url
    
    # 如果已经是完整URL（包含http或https），直接返回
    if image_url.startswith(('http://', 'https://')):
        return image_url
    
    # 只处理媒体文件路径，不处理其他API路径
    if image_url.startswith('/media/') or image_url.startswith('media/'):
        # 确保路径以/开头
        if not image_url.startswith('/'):
            image_url = f"/{image_url}"
        
        protocol = 'https' if request.is_secure() else 'http'
        domain = request.get_host()
        return f"{protocol}://{domain}{image_url}"
    
    return image_url


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
