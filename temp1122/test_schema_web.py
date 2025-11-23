#!/usr/bin/env python3
"""
测试Schema Web生成
"""
import requests
import json

try:
    response = requests.get('http://localhost:8000/api/v1/schema/')
    print(f"状态码: {response.status_code}")
    print(f"Content-Type: {response.headers.get('Content-Type')}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            if 'openapi' in data:
                print("✅ Schema生成成功!")
                print(f"OpenAPI版本: {data['openapi']}")
                print(f"API标题: {data['info']['title']}")
                print(f"路径数量: {len(data['paths'])}")
            else:
                print("❌ 返回数据不是OpenAPI schema")
                print(response.text[:500])
        except json.JSONDecodeError:
            print("❌ 返回数据不是JSON")
            print(response.text[:500])
    else:
        print(f"❌ HTTP错误: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"❌ 请求失败: {e}")
