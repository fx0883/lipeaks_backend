"""
测试图片上传并生成缩略图功能

使用方法：
1. 确保Django服务正在运行
2. 替换YOUR_JWT_TOKEN为有效的JWT令牌
3. 准备一张测试图片，替换test_image.png路径
4. 运行: python3 test_thumbnail_upload.py
"""
import requests
import os

# 配置
API_URL = "http://localhost:8000/api/v1/common/upload-image-with-thumbnail/"
JWT_TOKEN = "YOUR_JWT_TOKEN"  # 替换为实际的JWT令牌
TEST_IMAGE_PATH = "test_image.png"  # 替换为实际的图片路径
FOLDER_NAME = "test_uploads"  # 可选的文件夹名称

def test_upload():
    """测试图片上传并生成缩略图"""
    
    # 检查测试图片是否存在
    if not os.path.exists(TEST_IMAGE_PATH):
        print(f"错误: 测试图片 {TEST_IMAGE_PATH} 不存在")
        print("请准备一张测试图片并更新 TEST_IMAGE_PATH 变量")
        return
    
    # 准备请求头
    headers = {
        "Authorization": f"Bearer {JWT_TOKEN}"
    }
    
    # 准备文件和数据
    files = {
        "file": open(TEST_IMAGE_PATH, "rb")
    }
    data = {
        "folder": FOLDER_NAME
    }
    
    print(f"正在上传图片: {TEST_IMAGE_PATH}")
    print(f"目标文件夹: {FOLDER_NAME}")
    print("-" * 50)
    
    try:
        # 发送POST请求
        response = requests.post(API_URL, headers=headers, files=files, data=data)
        
        # 打印响应状态码
        print(f"响应状态码: {response.status_code}")
        print("-" * 50)
        
        # 打印响应内容
        result = response.json()
        print("响应内容:")
        print(f"成功: {result.get('success')}")
        print(f"代码: {result.get('code')}")
        print(f"消息: {result.get('message')}")
        print("-" * 50)
        
        if result.get('success'):
            data = result.get('data', {})
            print("上传成功！")
            print(f"\n原图信息:")
            print(f"  URL: {data.get('url')}")
            print(f"  文件名: {data.get('filename')}")
            print(f"  大小: {data.get('size')} 字节")
            print(f"\n缩略图信息:")
            print(f"  URL: {data.get('thumbnail_url')}")
            print(f"  文件名: {data.get('thumbnail_filename')}")
            print(f"  大小: {data.get('thumbnail_size')} 字节")
        else:
            print("上传失败！")
            print(f"错误详情: {result.get('data', {}).get('detail')}")
            
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {str(e)}")
    except Exception as e:
        print(f"发生错误: {str(e)}")
    finally:
        files['file'].close()

if __name__ == "__main__":
    print("=" * 50)
    print("图片上传并生成缩略图功能测试")
    print("=" * 50)
    
    # 检查配置
    if JWT_TOKEN == "YOUR_JWT_TOKEN":
        print("\n警告: 请先配置有效的JWT令牌")
        print("1. 登录系统获取JWT令牌")
        print("2. 在脚本中替换 JWT_TOKEN 变量的值")
        print("3. 重新运行测试脚本")
    else:
        test_upload()
    
    print("\n" + "=" * 50)
