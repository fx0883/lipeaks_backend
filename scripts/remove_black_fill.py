"""
将图片中的黑色填充区域转换为只保留轮廓线
使用形态学梯度方法提取黑色区域的边缘
"""

import cv2
import numpy as np
from pathlib import Path


def remove_black_fill(input_path: str, output_path: str = None, line_thickness: int = 2):
    """
    将黑色填充区域转换为只保留轮廓线
    
    Args:
        input_path: 输入图片路径
        output_path: 输出图片路径（默认在原文件名后加 _outline）
        line_thickness: 轮廓线粗细（默认2像素）
    """
    # 读取图片
    img = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"无法读取图片: {input_path}")
    
    # 处理带透明通道的图片
    has_alpha = img.shape[2] == 4 if len(img.shape) == 3 else False
    
    if has_alpha:
        # 分离透明通道
        bgr = img[:, :, :3]
        alpha = img[:, :, 3]
    else:
        bgr = img
        alpha = None
    
    # 转换为灰度图
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    
    # 创建二值图：黑色区域为白色（255），其他为黑色（0）
    # 黑色像素值接近0，所以我们用反向阈值
    _, binary = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY_INV)
    
    # 方法1：形态学梯度 - 提取黑色区域的边缘
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (line_thickness, line_thickness))
    gradient = cv2.morphologyEx(binary, cv2.MORPH_GRADIENT, kernel)
    
    # 反转颜色：边缘变黑，背景变白
    outline = cv2.bitwise_not(gradient)
    
    # 转换回BGR
    result = cv2.cvtColor(outline, cv2.COLOR_GRAY2BGR)
    
    # 恢复透明通道（如果有）
    if has_alpha:
        result = cv2.cvtColor(result, cv2.COLOR_BGR2BGRA)
        result[:, :, 3] = alpha
    
    # 生成输出路径
    if output_path is None:
        p = Path(input_path)
        output_path = str(p.parent / f"{p.stem}_outline{p.suffix}")
    
    # 保存结果
    cv2.imwrite(output_path, result)
    print(f"已保存: {output_path}")
    
    return output_path


def remove_black_fill_preserve_lines(input_path: str, output_path: str = None, edge_thickness: int = 2, min_fill_size: int = 3):
    """
    保留原有的轮廓线，同时将填充区域转换为边缘
    
    这个方法会：
    1. 保留原图中细的黑色线条
    2. 将大面积的黑色填充转为只有边缘
    
    Args:
        min_fill_size: 最小填充区域检测尺寸，越小能检测越小的填充区域
    """
    img = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"无法读取图片: {input_path}")
    
    has_alpha = img.shape[2] == 4 if len(img.shape) == 3 else False
    
    if has_alpha:
        bgr = img[:, :, :3]
        alpha = img[:, :, 3]
    else:
        bgr = img
        alpha = None
    
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    
    # 获取黑色区域（二值化）
    _, black_mask = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY_INV)
    
    # 使用较小的腐蚀核来检测更小的填充区域
    kernel_erode = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (min_fill_size, min_fill_size))
    eroded = cv2.erode(black_mask, kernel_erode, iterations=1)
    
    # 膨胀回来，得到填充区域的掩码
    dilated = cv2.dilate(eroded, kernel_erode, iterations=1)
    
    # 对填充区域提取边缘
    kernel_gradient = cv2.getStructuringElement(cv2.MORPH_RECT, (edge_thickness, edge_thickness))
    filled_edges = cv2.morphologyEx(dilated, cv2.MORPH_GRADIENT, kernel_gradient)
    
    # 找到细线（原黑色区域减去填充区域）
    thin_lines = cv2.subtract(black_mask, dilated)
    
    # 合并：细线 + 填充区域的边缘
    combined = cv2.bitwise_or(thin_lines, filled_edges)
    
    # 反转：黑线白底
    result_gray = cv2.bitwise_not(combined)
    
    result = cv2.cvtColor(result_gray, cv2.COLOR_GRAY2BGR)
    
    if has_alpha:
        result = cv2.cvtColor(result, cv2.COLOR_BGR2BGRA)
        result[:, :, 3] = alpha
    
    if output_path is None:
        p = Path(input_path)
        output_path = str(p.parent / f"{p.stem}_outline_v2{p.suffix}")
    
    cv2.imwrite(output_path, result)
    print(f"已保存: {output_path}")
    
    return output_path


def remove_all_black_fill(input_path: str, output_path: str = None, line_thickness: int = 2):
    """
    将所有黑色区域（无论大小）都转换为轮廓线
    使用轮廓检测方法，彻底去除所有填充
    """
    img = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
    if img is None:
        raise ValueError(f"无法读取图片: {input_path}")
    
    has_alpha = img.shape[2] == 4 if len(img.shape) == 3 else False
    
    if has_alpha:
        bgr = img[:, :, :3]
        alpha = img[:, :, 3]
    else:
        bgr = img
        alpha = None
    
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    
    # 获取所有黑色区域
    _, black_mask = cv2.threshold(gray, 30, 255, cv2.THRESH_BINARY_INV)
    
    # 查找所有轮廓（包括内部轮廓）
    contours, hierarchy = cv2.findContours(black_mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    # 创建白色背景
    result = np.ones_like(bgr) * 255
    
    # 绘制所有轮廓（只绘制边缘，不填充）
    # 使用 LINE_8 获得更清晰的线条
    cv2.drawContours(result, contours, -1, (0, 0, 0), line_thickness, lineType=cv2.LINE_8)
    
    if has_alpha:
        result = cv2.cvtColor(result, cv2.COLOR_BGR2BGRA)
        result[:, :, 3] = alpha
    
    if output_path is None:
        p = Path(input_path)
        output_path = str(p.parent / f"{p.stem}_outline_all{p.suffix}")
    
    cv2.imwrite(output_path, result)
    print(f"已保存: {output_path}")
    
    return output_path


def batch_process(input_dir: str, output_dir: str = None, method: str = "preserve"):
    """
    批量处理目录下的所有图片
    
    Args:
        input_dir: 输入目录
        output_dir: 输出目录（默认在输入目录下创建 outline 子目录）
        method: "simple" 或 "preserve"
    """
    input_path = Path(input_dir)
    if output_dir is None:
        output_path = input_path / "outline"
    else:
        output_path = Path(output_dir)
    
    output_path.mkdir(parents=True, exist_ok=True)
    
    extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
    
    for img_file in input_path.iterdir():
        if img_file.suffix.lower() in extensions:
            out_file = output_path / img_file.name
            try:
                if method == "preserve":
                    remove_black_fill_preserve_lines(str(img_file), str(out_file))
                else:
                    remove_black_fill(str(img_file), str(out_file))
            except Exception as e:
                print(f"处理失败 {img_file}: {e}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        # 默认处理示例图片
        input_image = r"D:\GitHub\lipeaks_backend\media\images\mingzhu\hongloumeng_v3\jiayingchun.png"
    else:
        input_image = sys.argv[1]
    
    print("方法1: 简单形态学梯度")
    remove_black_fill(input_image)
    
    print("\n方法2: 保留细线，只处理填充区域")
    remove_black_fill_preserve_lines(input_image)
    
    print("\n方法3: 彻底去除所有黑色填充（推荐）")
    remove_all_black_fill(input_image)
