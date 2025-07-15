#!/usr/bin/env python
"""
将菜单树结构保存到文件
"""
import os
import sys
import django

# 设置Django环境
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from menus.models import Menu

def print_tree(menu, prefix="", output_file=None):
    """
    递归打印菜单树并写入文件
    """
    line = f"{prefix}● {menu.name} (ID: {menu.id}, 路径: {menu.path})"
    print(line)
    if output_file:
        output_file.write(line + "\n")
    
    children = Menu.objects.filter(parent=menu).order_by('rank', 'id')
    count = children.count()
    
    for i, child in enumerate(children):
        is_last = i == count - 1
        child_prefix = prefix + ("└── " if is_last else "├── ")
        next_prefix = prefix + ("    " if is_last else "│   ")
        print_tree(child, child_prefix, output_file)

def main():
    """
    主函数
    """
    output_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "menu_tree.txt")
    
    with open(output_file_path, "w", encoding="utf-8") as output_file:
        # 确认CMS菜单存在
        try:
            cms_menu = Menu.objects.get(name='CMS')
            
            header = "=" * 60
            title = f"CMS菜单树结构 (总计 {Menu.objects.count()} 个菜单项)"
            
            print(header)
            print(title)
            print(header)
            
            output_file.write(header + "\n")
            output_file.write(title + "\n")
            output_file.write(header + "\n")
            
            print_tree(cms_menu, "", output_file)
            
            print(f"\n菜单树结构已保存到: {output_file_path}")
            
        except Menu.DoesNotExist:
            error_msg = "错误: CMS菜单不存在!"
            print(error_msg)
            output_file.write(error_msg)
            sys.exit(1)

if __name__ == "__main__":
    main() 