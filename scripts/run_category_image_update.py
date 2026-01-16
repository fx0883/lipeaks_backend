#!/usr/bin/env python
"""
快速运行分类图片更新脚本
"""
import os
import sys
import django
from pathlib import Path

# 设置Django环境
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# 导入命令
from django.core.management import call_command

def main():
    """运行分类图片更新"""
    print("=" * 60)
    print("开始更新分类图片")
    print("=" * 60)
    
    # 首先测试少量分类
    print("\n测试模式：处理前3个分类...")
    
    try:
        call_command(
            'update_category_images',
            tenant_id=3,
            category_ids='10,11,12',  # 只处理3个分类作为测试
            dry_run=False,  # 实际生成
            skip_existing=False,  # 不跳过已有图片
            backup=True,  # 备份原图片
            verbosity=2  # 详细输出
        )
        print("\n✓ 测试成功完成！")
        
        # 询问是否继续处理所有分类
        response = input("\n是否继续处理所有分类？(y/n): ")
        if response.lower() == 'y':
            print("\n处理所有分类...")
            call_command(
                'update_category_images',
                tenant_id=3,
                skip_existing=True,  # 跳过已处理的
                backup=True,
                concurrent=2,  # 使用2个并发
                verbosity=2
            )
            print("\n✓ 所有分类处理完成！")
        else:
            print("\n已取消")
            
    except Exception as e:
        print(f"\n✗ 错误: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
