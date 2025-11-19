"""
测试图片URL标准化功能
"""
import requests
import json

BASE_URL = "http://localhost:8000"

# 测试用的认证token（需要先登录获取）
def login():
    """登录获取token"""
    response = requests.post(f"{BASE_URL}/api/v1/auth/login/", json={
        "username": "admin",
        "password": "admin123"
    })
    if response.status_code == 200:
        data = response.json()
        return data['data']['access_token']
    else:
        print(f"登录失败: {response.text}")
        return None

def test_file_upload(token):
    """测试1: 上传图片，验证返回相对路径"""
    print("\n=== 测试1: 上传图片 ===")
    
    # 创建一个测试图片
    import io
    from PIL import Image
    
    # 创建一个简单的测试图片
    img = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)
    
    files = {'file': ('test.png', img_byte_arr, 'image/png')}
    data = {'folder': 'test'}
    headers = {'Authorization': f'Bearer {token}'}
    
    response = requests.post(
        f"{BASE_URL}/api/v1/common/upload-file/",
        files=files,
        data=data,
        headers=headers
    )
    
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"返回数据: {json.dumps(result, indent=2, ensure_ascii=False)}")
        url = result['data']['url']
        
        # 验证：不应该以斜杠开头
        if url.startswith('/'):
            print("❌ 失败: URL以斜杠开头，应该是相对路径")
            return None
        elif url.startswith('http'):
            print("❌ 失败: URL包含domain，应该是相对路径")
            return None
        else:
            print(f"✅ 成功: 返回相对路径 '{url}'")
            return url
    else:
        print(f"❌ 上传失败: {response.text}")
        return None

def test_category_create(token, image_url):
    """测试2: 创建分类，传入完整URL，验证保存为相对路径"""
    print("\n=== 测试2: 创建分类 ===")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'X-Tenant-ID': '3'
    }
    
    # 测试传入完整URL
    full_url = f"http://localhost:8000/{image_url}"
    
    data = {
        "slug": "test-category-url-fix",
        "cover_image": full_url,
        "translations": {
            "zh-hans": {
                "name": "测试分类URL修复",
                "description": "测试图片URL标准化功能"
            }
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/cms/categories/",
        json=data,
        headers=headers
    )
    
    print(f"状态码: {response.status_code}")
    if response.status_code == 201:
        result = response.json()
        print(f"返回数据: {json.dumps(result, indent=2, ensure_ascii=False)}")
        category_id = result['id']
        saved_cover_image = result['cover_image']
        
        # 验证：返回的应该是完整URL
        if not saved_cover_image.startswith('http'):
            print(f"❌ 失败: 返回的URL不包含domain: '{saved_cover_image}'")
            return None
        else:
            print(f"✅ 成功: 返回完整URL '{saved_cover_image}'")
            return category_id
    else:
        print(f"❌ 创建失败: {response.text}")
        return None

def test_category_get(token, category_id):
    """测试3: GET分类详情，验证添加domain"""
    print("\n=== 测试3: GET分类详情 ===")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'X-Tenant-ID': '3'
    }
    
    response = requests.get(
        f"{BASE_URL}/api/v1/cms/categories/{category_id}/",
        headers=headers
    )
    
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        cover_image = result.get('cover_image', '')
        print(f"cover_image: {cover_image}")
        
        # 验证：应该包含domain
        if cover_image.startswith('http'):
            print(f"✅ 成功: 返回完整URL '{cover_image}'")
        else:
            print(f"❌ 失败: 应该返回完整URL，实际返回: '{cover_image}'")
    else:
        print(f"❌ GET失败: {response.text}")

def test_external_url(token):
    """测试4: 传入外部URL，验证保持不变"""
    print("\n=== 测试4: 传入外部URL ===")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
        'X-Tenant-ID': '3'
    }
    
    external_url = "https://cdn.example.com/images/test.jpg"
    
    data = {
        "slug": "test-external-url",
        "cover_image": external_url,
        "translations": {
            "zh-hans": {
                "name": "测试外部URL",
                "description": "测试外部CDN URL保持不变"
            }
        }
    }
    
    response = requests.post(
        f"{BASE_URL}/api/v1/cms/categories/",
        json=data,
        headers=headers
    )
    
    print(f"状态码: {response.status_code}")
    if response.status_code == 201:
        result = response.json()
        saved_cover_image = result['cover_image']
        
        # 验证：外部URL应该保持不变
        if saved_cover_image == external_url:
            print(f"✅ 成功: 外部URL保持不变 '{saved_cover_image}'")
        else:
            print(f"❌ 失败: 外部URL被修改了，期望'{external_url}'，实际'{saved_cover_image}'")
    else:
        print(f"❌ 创建失败: {response.text}")

def cleanup(token, category_ids):
    """清理测试数据"""
    print("\n=== 清理测试数据 ===")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'X-Tenant-ID': '3'
    }
    
    for category_id in category_ids:
        if category_id:
            response = requests.delete(
                f"{BASE_URL}/api/v1/cms/categories/{category_id}/",
                headers=headers
            )
            if response.status_code == 204:
                print(f"✅ 删除分类 {category_id} 成功")
            else:
                print(f"⚠️  删除分类 {category_id} 失败: {response.text}")

def main():
    """主测试函数"""
    print("=" * 60)
    print("图片URL标准化功能测试")
    print("=" * 60)
    
    # 登录
    token = login()
    if not token:
        print("无法获取token，测试终止")
        return
    
    print(f"✅ 登录成功，获取token")
    
    # 测试上传
    image_url = test_file_upload(token)
    if not image_url:
        print("\n测试终止：上传失败")
        return
    
    # 测试创建分类
    category_id = test_category_create(token, image_url)
    
    # 测试GET分类
    if category_id:
        test_category_get(token, category_id)
    
    # 测试外部URL
    test_external_url(token)
    
    # 清理测试数据（可选）
    # cleanup(token, [category_id])
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
