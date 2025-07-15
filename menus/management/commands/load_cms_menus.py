import os
import json
from django.core.management.base import BaseCommand
from menus.models import Menu
from django.db import transaction
from django.conf import settings

class Command(BaseCommand):
    help = '加载CMS菜单数据'

    def handle(self, *args, **options):
        # CMS菜单数据文件路径
        cms_menus_file = os.path.join(settings.BASE_DIR, 'docs', 'cms', 'cms_menus.json')
        
        if not os.path.exists(cms_menus_file):
            self.stdout.write(self.style.ERROR(f'菜单数据文件不存在: {cms_menus_file}'))
            return
        
        try:
            with open(cms_menus_file, 'r', encoding='utf-8') as f:
                menu_data = json.load(f)
            
            self.stdout.write(self.style.SUCCESS(f'成功加载菜单数据，共 {len(menu_data)} 条记录'))
            
            # 开始事务
            with transaction.atomic():
                for item in menu_data:
                    pk = item['pk']
                    fields = item['fields']
                    
                    # 如果parent_id是整数，确保它引用的是一个已存在的菜单
                    parent_id = fields.get('parent')
                    if parent_id is not None:
                        if not Menu.objects.filter(id=parent_id).exists():
                            self.stdout.write(self.style.WARNING(f'菜单项 {fields["name"]} 的父菜单 (ID={parent_id}) 不存在，将跳过'))
                            continue
                    
                    # 检查菜单是否已存在
                    menu, created = Menu.objects.update_or_create(
                        id=pk,
                        defaults={
                            'name': fields['name'],
                            'code': fields['code'],
                            'icon': fields['icon'],
                            'path': fields['path'],
                            'component': fields['component'],
                            'rank': fields['rank'],
                            'parent_id': fields['parent'],
                            'is_active': fields['is_active'],
                            'remarks': fields['remarks'],
                        }
                    )
                    
                    if created:
                        self.stdout.write(self.style.SUCCESS(f'创建菜单: {fields["name"]} (ID={pk})'))
                    else:
                        self.stdout.write(self.style.SUCCESS(f'更新菜单: {fields["name"]} (ID={pk})'))
            
            self.stdout.write(self.style.SUCCESS('CMS菜单数据加载完成'))
            
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR('菜单数据文件格式错误，请检查JSON格式'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'加载菜单数据时出错: {str(e)}')) 