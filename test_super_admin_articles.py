import requests
import json

def test_super_admin_articles():
    """测试超级管理员访问文章API的情况"""
    # 超级管理员登录
    login_url = "http://localhost:8000/api/v1/auth/login/"
    login_data = {
        "username": "admin456",
        "password": "admin456"
    }
    
    print("\n===== 超级管理员登录 =====")
    login_response = requests.post(login_url, json=login_data)
    
    if login_response.status_code == 200:
        login_result = login_response.json()
        token = login_result.get("data", {}).get("token")
        print(f"登录成功，获取到令牌: {token[:10]}...")
        
        # 测试文章API（不提供X-Tenant-ID）
        print("\n===== 测试文章API（不提供X-Tenant-ID） =====")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Debug-Log": "true"
        }
        
        articles_url = "http://localhost:8000/api/v1/cms/articles/"
        response = requests.get(articles_url, headers=headers)
        
        print(f"状态码: {response.status_code}")
        print("响应头:")
        for key, value in response.headers.items():
            if key.startswith('X-'):
                print(f"  {key}: {value}")
                
        try:
            result = response.json()
            print("\n响应内容:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        except:
            print("\n响应内容:")
            print(response.text[:500])  # 只打印前500个字符
            
        # 测试文章API（提供X-Tenant-ID）
        print("\n===== 测试文章API（提供X-Tenant-ID） =====")
        headers["X-Tenant-ID"] = "1"
        
        response = requests.get(articles_url, headers=headers)
        
        print(f"状态码: {response.status_code}")
        print("响应头:")
        for key, value in response.headers.items():
            if key.startswith('X-'):
                print(f"  {key}: {value}")
                
        try:
            result = response.json()
            print("\n响应内容:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        except:
            print("\n响应内容:")
            print(response.text[:500])  # 只打印前500个字符
    else:
        print(f"登录失败: {login_response.status_code}")
        print(login_response.text)

if __name__ == "__main__":
    test_super_admin_articles() 