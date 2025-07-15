#!/usr/bin/env python
"""
显示菜单树结构的脚本
"""
import os
import sys
import django

# 设置Django环境
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from menus.models import Menu

def print_tree(menu, prefix=""):
    """
    递归打印菜单树
    """
    print(f"{prefix}● {menu.name} (ID: {menu.id}, 路径: {menu.path})")
    
    children = Menu.objects.filter(parent=menu).order_by('rank', 'id')
    count = children.count()
    
    for i, child in enumerate(children):
        is_last = i == count - 1
        child_prefix = prefix + ("└── " if is_last else "├── ")
        next_prefix = prefix + ("    " if is_last else "│   ")
        print_tree(child, child_prefix)

def main():
    """
    主函数
    """
    # 确认CMS菜单存在
    try:
        cms_menu = Menu.objects.get(name='CMS')
        
        print("=" * 60)
        print(f"CMS菜单树结构 (总计 {Menu.objects.count()} 个菜单项)")
        print("=" * 60)
        
        print_tree(cms_menu)
        
    except Menu.DoesNotExist:
        print("错误: CMS菜单不存在!")
        sys.exit(1)

if __name__ == "__main__":
    main() 