"""
测试 available-products API
"""
import requests
import json

# API 配置
url = "http://192.168.1.15:8000/api/v1/licenses/member/available-products/"
headers = {
    "Accept": "application/json",
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJ1c2VybmFtZSI6ImZ4MDg4MyIsImV4cCI6MTc2MDg2ODEyMiwibW9kZWxfdHlwZSI6Im1lbWJlciIsImlzX2FkbWluIjpmYWxzZSwiaXNfc3VwZXJfYWRtaW4iOmZhbHNlfQ.uFo2SnupLSjPMsqfhvmmmA7B1v0x6c-pdMgdU4yQmPI",
    "X-Tenant-ID": "1"
}

print("=" * 80)
print("测试 API: available-products")
print("=" * 80)
print(f"\nURL: {url}")
print(f"Headers: {json.dumps(headers, indent=2)}")

try:
    # 发送请求
    print("\n发送 GET 请求...")
    response = requests.get(url, headers=headers, verify=False)
    
    print(f"\n状态码: {response.status_code}")
    
    # 解析响应
    if response.status_code == 200:
        data = response.json()
        print("\n响应数据:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        # 分析 already_applied 字段
        if data.get('success') and 'data' in data:
            # 处理嵌套的 data.data 结构
            inner_data = data['data']
            if isinstance(inner_data, dict) and 'data' in inner_data:
                products = inner_data['data'].get('products', [])
            else:
                products = inner_data.get('products', [])
            print(f"\n\n{'=' * 80}")
            print(f"产品数量: {len(products)}")
            print(f"{'=' * 80}")
            
            for idx, product in enumerate(products, 1):
                print(f"\n[{idx}] 产品: {product.get('name')} (ID: {product.get('id')})")
                print(f"    - 产品代码: {product.get('code')}")
                print(f"    - already_applied: {product.get('already_applied')}")
                
                if product.get('already_applied'):
                    print(f"    ⚠️  警告: already_applied 应该为 false，但当前为 true")
                else:
                    print(f"    ✓ 正确: already_applied 为 false")
                
                trial_plans = product.get('trial_plans', [])
                print(f"    - 试用方案数: {len(trial_plans)}")
                for plan in trial_plans:
                    print(f"        • {plan.get('name')} - {plan.get('default_validity_days')}天")
        
    else:
        print(f"\n请求失败:")
        print(response.text)
        
except Exception as e:
    print(f"\n错误: {str(e)}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
