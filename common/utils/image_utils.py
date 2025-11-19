"""
图片处理工具模块

提供图片处理相关的工具函数，如缩略图生成等
"""
import os
import logging
from PIL import Image

logger = logging.getLogger(__name__)


def create_thumbnail(image_path, thumbnail_path, width=200, quality=85):
    """
    创建图片缩略图
    
    Args:
        image_path: 原图路径
        thumbnail_path: 缩略图保存路径
        width: 缩略图宽度（像素），默认200
        quality: JPEG质量（1-100），默认85
    
    Returns:
        tuple: (成功标志, 缩略图尺寸或错误信息)
    
    Raises:
        Exception: 图片处理失败时抛出异常
    """
    try:
        # 打开原图
        with Image.open(image_path) as img:
            # 获取原图尺寸
            original_width, original_height = img.size
            
            # 转换RGBA为RGB（处理PNG透明背景）- 必须在保存前处理
            if img.mode in ('RGBA', 'LA', 'P'):
                # 创建白色背景
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 计算缩略图高度，保持宽高比
            ratio = width / original_width
            height = int(original_height * ratio)
            
            # 调整图片尺寸到目标宽度
            if original_width != width:
                # 使用resize而不是thumbnail，以支持放大和缩小
                img = img.resize((width, height), Image.Resampling.LANCZOS)
                logger.info(f"缩略图生成成功: {original_width}x{original_height} -> {width}x{height}")
            else:
                logger.info(f"原图宽度已是 {width}px，直接保存")
            
            # 保存缩略图
            img.save(thumbnail_path, 'JPEG', quality=quality, optimize=True)
            
            return True, (width, height)
            
    except Exception as e:
        logger.error(f"生成缩略图失败: {str(e)}")
        raise Exception(f"生成缩略图失败: {str(e)}")
