"""
测试ComfyUI图片生成流程
"""
import os
import sys
import django
from pathlib import Path

# 设置Django环境
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from cms.utils.comfyui_client import ComfyUIClient
from cms.utils.prompt_generator import PromptGenerator
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_comfyui_connection():
    """测试ComfyUI连接"""
    print("\n=== 测试ComfyUI连接 ===")
    client = ComfyUIClient("http://127.0.0.1:8188")
    
    if client.test_connection():
        print("✓ ComfyUI服务器连接成功")
        return True
    else:
        print("✗ ComfyUI服务器连接失败")
        return False

def test_prompt_generation():
    """测试提示词生成"""
    print("\n=== 测试提示词生成 ===")
    generator = PromptGenerator()
    
    test_categories = [
        "技术博客",
        "金融投资",
        "自然风光",
        "创意设计",
        "健康生活"
    ]
    
    for category in test_categories:
        prompt_data = generator.generate_prompt(category)
        print(f"\n分类: {category}")
        print(f"风格: {prompt_data['style']}")
        print(f"主提示词: {prompt_data['main_prompt'][:100]}...")
        
    return True

def test_single_image_generation():
    """测试单个图片生成"""
    print("\n=== 测试单个图片生成 ===")
    
    client = ComfyUIClient("http://127.0.0.1:8188")
    generator = PromptGenerator()
    
    # 测试分类
    test_category = "科技创新"
    print(f"测试分类: {test_category}")
    
    # 生成提示词
    prompt_data = generator.generate_prompt(test_category)
    print(f"使用风格: {prompt_data['style']}")
    print(f"主提示词: {prompt_data['main_prompt']}")
    
    # 生成图片
    print("\n开始生成图片...")
    image_data = client.generate_image(
        prompt=prompt_data['main_prompt'],
        width=670,
        height=360,
        max_retries=1
    )
    
    if image_data:
        # 保存测试图片
        test_output_path = Path("test_output.png")
        with open(test_output_path, 'wb') as f:
            f.write(image_data)
        print(f"✓ 图片生成成功，已保存到: {test_output_path}")
        print(f"  文件大小: {len(image_data) / 1024:.2f} KB")
        return True
    else:
        print("✗ 图片生成失败")
        return False

def test_database_query():
    """测试数据库查询"""
    print("\n=== 测试数据库查询 ===")
    
    from cms.models import Category
    from tenants.models import Tenant
    
    try:
        # 检查租户
        tenant = Tenant.objects.get(id=3)
        print(f"✓ 找到租户: {tenant.name}")
        
        # 查询分类
        categories = Category.objects.filter(
            tenant_id=3,
            is_deleted=False
        )[:5]  # 只获取前5个
        
        print(f"✓ 找到 {categories.count()} 个分类:")
        for cat in categories:
            cat.set_current_language('zh-hans', initialize=True)
            name = cat.safe_translation_getter('name', any_language=True) or 'Unnamed'
            print(f"  - ID: {cat.id}, 名称: {name}, 封面: {cat.cover_image or '无'}")
            
        return True
        
    except Exception as e:
        print(f"✗ 数据库查询失败: {str(e)}")
        return False

def main():
    """主测试流程"""
    print("=" * 50)
    print("ComfyUI 分类图片生成测试")
    print("=" * 50)
    
    tests = [
        ("连接测试", test_comfyui_connection),
        ("提示词生成", test_prompt_generation),
        ("数据库查询", test_database_query),
        ("图片生成", test_single_image_generation),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n✗ {test_name} 异常: {str(e)}")
            results.append((test_name, False))
    
    # 输出总结
    print("\n" + "=" * 50)
    print("测试结果总结:")
    print("=" * 50)
    
    for test_name, success in results:
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{test_name}: {status}")
    
    all_passed = all(success for _, success in results)
    
    if all_passed:
        print("\n✓ 所有测试通过！可以运行主命令:")
        print("  python manage.py update_category_images --tenant-id 3")
    else:
        print("\n✗ 部分测试失败，请检查配置和服务状态")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
