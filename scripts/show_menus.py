#!/usr/bin/env python
"""
显示菜单信息的脚本
"""
import os
import sys
import django

# 设置Django环境
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from menus.models import Menu

def main():
    """
    主函数
    """
    # 显示菜单总数
    total_menus = Menu.objects.count()
    print(f"菜单总数: {total_menus}")
    
    # 显示所有菜单的简单列表
    print("\n所有菜单列表:")
    print("ID | 名称 | 路径 | 父菜单")
    print("-" * 80)
    for menu in Menu.objects.all().order_by('id'):
        parent_name = f"{menu.parent.name} (ID: {menu.parent.id})" if menu.parent else "无"
        print(f"{menu.id} | {menu.name} | {menu.path} | {parent_name}")
    
    # 显示树形结构
    print("\n菜单树形结构:")
    print("=" * 80)
    
    # 获取顶级菜单
    top_menus = Menu.objects.filter(parent=None).order_by('rank', 'id')
    
    for top_menu in top_menus:
        # 显示顶级菜单
        print(f"● {top_menu.name} (ID: {top_menu.id}, 路径: {top_menu.path})")
        
        # 获取一级子菜单
        level1_menus = Menu.objects.filter(parent=top_menu).order_by('rank', 'id')
        
        for i, level1_menu in enumerate(level1_menus):
            is_last_level1 = i == len(level1_menus) - 1
            level1_prefix = "└─" if is_last_level1 else "├─"
            print(f"  {level1_prefix} {level1_menu.name} (ID: {level1_menu.id}, 路径: {level1_menu.path})")
            
            # 获取二级子菜单
            level2_menus = Menu.objects.filter(parent=level1_menu).order_by('rank', 'id')
            
            for j, level2_menu in enumerate(level2_menus):
                is_last_level2 = j == len(level2_menus) - 1
                level2_prefix = "  " if is_last_level1 else "│ "
                level2_prefix += "└─" if is_last_level2 else "├─"
                print(f"  {level2_prefix} {level2_menu.name} (ID: {level2_menu.id}, 路径: {level2_menu.path})")
                
                # 获取三级子菜单（如果有的话）
                level3_menus = Menu.objects.filter(parent=level2_menu).order_by('rank', 'id')
                
                for k, level3_menu in enumerate(level3_menus):
                    is_last_level3 = k == len(level3_menus) - 1
                    level3_prefix = "    " if is_last_level1 else "│   "
                    level3_prefix += "  " if is_last_level2 else "│ "
                    level3_prefix += "└─" if is_last_level3 else "├─"
                    print(f"  {level3_prefix} {level3_menu.name} (ID: {level3_menu.id}, 路径: {level3_menu.path})")

if __name__ == "__main__":
    main() 