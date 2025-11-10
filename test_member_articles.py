#!/usr/bin/env python3
import requests
import json

BASE_URL = "http://localhost:8000"
TENANT_ID = 2
USERNAME = "test_member"
PASSWORD = "Test123456"

class MemberArticleTest:
    def __init__(self):
        self.base_url = BASE_URL
        self.tenant_id = TENANT_ID
        self.headers = {
            "Content-Type": "application/json",
            "X-Tenant-ID": str(self.tenant_id)
        }
        self.access_token = None
    
    def login(self):
        """登录获取token"""
        url = f"{self.base_url}/api/v1/auth/login/"
        data = {
            "username": USERNAME,
            "password": PASSWORD
        }
        response = requests.post(url, json=data, headers=self.headers)
        result = response.json()
        
        if response.status_code == 200 and result.get('success'):
            self.access_token = result['data'].get('token') or result['data'].get('access_token')
            self.headers['Authorization'] = f"Bearer {self.access_token}"
            print("✅ 登录成功")
            print(f"   Token: {self.access_token[:50]}...")
            return True
        else:
            print(f"❌ 登录失败: {result}")
            return False
    
    def list_articles(self):
        """获取文章列表"""
        url = f"{self.base_url}/api/v1/cms/member/articles/"
        response = requests.get(url, headers=self.headers)
        result = response.json()
        
        if response.status_code == 200:
            count = result.get('data', {}).get('count', 0)
            print(f"✅ 获取文章列表成功: {count}篇文章")
            return result
        else:
            print(f"❌ 获取文章列表失败 ({response.status_code}): {result}")
            return None
    
    def create_article(self):
        """创建文章"""
        url = f"{self.base_url}/api/v1/cms/member/articles/"
        data = {
            "title": "自动化测试文章",
            "content": "这是通过API创建的测试文章内容",
            "content_type": "markdown",
            "status": "draft",
            "visibility": "public",
            "allow_comment": True
        }
        response = requests.post(url, json=data, headers=self.headers)
        result = response.json()
        
        if response.status_code == 201 and result.get('success'):
            article_id = result['data']['id']
            print(f"✅ 创建文章成功: ID={article_id}")
            print(f"   标题: {result['data']['title']}")
            if 'author_info' in result['data']:
                print(f"   作者: {result['data']['author_info'].get('username', 'N/A')}")
            if 'author_type' in result['data']:
                print(f"   作者类型: {result['data']['author_type']}")
            return article_id
        else:
            print(f"❌ 创建文章失败 ({response.status_code}): {result}")
            return None
    
    def update_article(self, article_id):
        """更新文章"""
        url = f"{self.base_url}/api/v1/cms/member/articles/{article_id}/"
        data = {
            "title": "更新后的测试文章标题"
        }
        response = requests.patch(url, json=data, headers=self.headers)
        result = response.json()
        
        if response.status_code == 200:
            print(f"✅ 更新文章成功: ID={article_id}")
            print(f"   新标题: {result['data']['title']}")
            return True
        else:
            print(f"❌ 更新文章失败 ({response.status_code}): {result}")
            return False
    
    def publish_article(self, article_id):
        """发布文章"""
        url = f"{self.base_url}/api/v1/cms/member/articles/{article_id}/publish/"
        response = requests.post(url, headers=self.headers)
        result = response.json()
        
        if response.status_code == 200:
            print(f"✅ 发布文章成功: ID={article_id}")
            print(f"   状态: {result['data']['status']}")
            return True
        else:
            print(f"❌ 发布文章失败 ({response.status_code}): {result}")
            return False
    
    def get_statistics(self, article_id):
        """获取文章统计"""
        url = f"{self.base_url}/api/v1/cms/member/articles/{article_id}/statistics/"
        response = requests.get(url, headers=self.headers)
        result = response.json()
        
        if response.status_code == 200:
            print(f"✅ 获取统计成功: ID={article_id}")
            stats = result['data']
            print(f"   浏览: {stats.get('views_count', 0)}, 点赞: {stats.get('likes_count', 0)}, 评论: {stats.get('comments_count', 0)}")
            return True
        else:
            print(f"❌ 获取统计失败 ({response.status_code}): {result}")
            return False
    
    def delete_article(self, article_id):
        """删除文章"""
        url = f"{self.base_url}/api/v1/cms/member/articles/{article_id}/"
        response = requests.delete(url, headers=self.headers)
        
        if response.status_code == 204:
            print(f"✅ 删除文章成功: ID={article_id}")
            return True
        else:
            try:
                result = response.json()
                print(f"❌ 删除文章失败 ({response.status_code}): {result}")
            except:
                print(f"❌ 删除文章失败: {response.status_code}")
            return False
    
    def run_full_test(self):
        """运行完整测试流程"""
        print("=" * 70)
        print("Member文章管理API完整测试")
        print("=" * 70)
        print(f"测试环境: {self.base_url}")
        print(f"租户ID: {self.tenant_id}")
        print(f"测试用户: {USERNAME}")
        print("=" * 70)
        
        # 1. 登录
        print("\n[步骤 1/8] 登录测试...")
        if not self.login():
            print("\n❌ 登录失败，终止测试")
            return
        
        # 2. 列表（初始）
        print("\n[步骤 2/8] 获取初始文章列表...")
        self.list_articles()
        
        # 3. 创建
        print("\n[步骤 3/8] 创建新文章...")
        article_id = self.create_article()
        if not article_id:
            print("\n❌ 创建文章失败，终止测试")
            return
        
        # 4. 更新
        print("\n[步骤 4/8] 更新文章...")
        if not self.update_article(article_id):
            print("\n⚠️ 更新文章失败，继续测试")
        
        # 5. 发布
        print("\n[步骤 5/8] 发布文章...")
        if not self.publish_article(article_id):
            print("\n⚠️ 发布文章失败，继续测试")
        
        # 6. 获取统计
        print("\n[步骤 6/8] 获取文章统计...")
        self.get_statistics(article_id)
        
        # 7. 再次查看列表
        print("\n[步骤 7/8] 获取更新后的文章列表...")
        self.list_articles()
        
        # 8. 删除
        print("\n[步骤 8/8] 删除测试文章...")
        self.delete_article(article_id)
        
        print("\n" + "=" * 70)
        print("✅ 测试流程完成！")
        print("=" * 70)

if __name__ == '__main__':
    test = MemberArticleTest()
    test.run_full_test()
