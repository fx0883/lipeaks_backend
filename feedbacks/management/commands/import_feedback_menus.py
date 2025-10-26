"""
导入反馈系统菜单配置

从 JSON 配置文件导入菜单到数据库
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from menus.models import Menu
import json
import os


class Command(BaseCommand):
    help = '导入反馈系统菜单配置到数据库'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='temp1022_2/feedback_menu_config.json',
            help='JSON配置文件路径'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='试运行，不实际写入数据库'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制导入，如果菜单已存在则更新'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        file_path = options['file']
        dry_run = options['dry_run']
        force = options['force']

        # 读取JSON文件
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                menu_config = json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'文件未找到: {file_path}'))
            return
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f'JSON解析错误: {str(e)}'))
            return

        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('反馈系统菜单导入工具'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        if dry_run:
            self.stdout.write(self.style.WARNING('\n试运行模式 - 不会实际写入数据库\n'))

        # 导入菜单
        created_count = 0
        updated_count = 0
        skipped_count = 0

        # 处理根菜单
        root_menu, created, updated = self._import_menu(menu_config, None, force, dry_run)
        
        if created:
            created_count += 1
            self.stdout.write(self.style.SUCCESS(f'[创建] {root_menu["title"]} ({root_menu["path"]})'))
        elif updated:
            updated_count += 1
            self.stdout.write(self.style.WARNING(f'[更新] {root_menu["title"]} ({root_menu["path"]})'))
        else:
            skipped_count += 1
            self.stdout.write(f'[跳过] {root_menu["title"]} ({root_menu["path"]})')

        # 处理子菜单
        if 'children' in menu_config:
            parent_menu = root_menu if not dry_run else None
            for child_config in menu_config['children']:
                result = self._import_menu_recursive(
                    child_config, 
                    parent_menu, 
                    force, 
                    dry_run, 
                    level=1
                )
                created_count += result['created']
                updated_count += result['updated']
                skipped_count += result['skipped']

        # 输出统计
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('导入完成'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'创建: {created_count}')
        self.stdout.write(f'更新: {updated_count}')
        self.stdout.write(f'跳过: {skipped_count}')
        self.stdout.write(f'总计: {created_count + updated_count + skipped_count}')
        self.stdout.write('=' * 60)

        if dry_run:
            self.stdout.write(self.style.WARNING('\n这是试运行，未实际写入数据库'))
            self.stdout.write(self.style.WARNING('移除 --dry-run 参数以实际导入'))

    def _import_menu_recursive(self, config, parent_menu, force, dry_run, level=0):
        """递归导入菜单及其子菜单"""
        indent = '  ' * level
        menu_data, created, updated = self._import_menu(config, parent_menu, force, dry_run)
        
        result = {
            'created': 1 if created else 0,
            'updated': 1 if updated else 0,
            'skipped': 0 if (created or updated) else 1
        }

        if created:
            self.stdout.write(self.style.SUCCESS(f'{indent}[创建] {menu_data["title"]} ({menu_data["path"]})'))
        elif updated:
            self.stdout.write(self.style.WARNING(f'{indent}[更新] {menu_data["title"]} ({menu_data["path"]})'))
        else:
            self.stdout.write(f'{indent}[跳过] {menu_data["title"]} ({menu_data["path"]})')

        # 处理子菜单
        if 'children' in config:
            current_parent = menu_data if not dry_run else None
            for child_config in config['children']:
                child_result = self._import_menu_recursive(
                    child_config, 
                    current_parent, 
                    force, 
                    dry_run, 
                    level + 1
                )
                result['created'] += child_result['created']
                result['updated'] += child_result['updated']
                result['skipped'] += child_result['skipped']

        return result

    def _import_menu(self, config, parent_menu, force, dry_run):
        """导入单个菜单"""
        # 提取meta字段
        meta = config.get('meta', {})
        
        # 准备菜单数据
        menu_data = {
            'name': config['name'],
            'code': config['name'].lower(),  # 使用name的小写作为code
            'path': config['path'],
            'component': config.get('component'),
            'redirect': config.get('redirect'),
            
            # Meta 字段
            'title': meta.get('title', config['name']),
            'icon': meta.get('icon'),
            'extra_icon': meta.get('extraIcon'),
            'rank': meta.get('rank', 0),
            'show_link': meta.get('showLink', True),
            'show_parent': meta.get('showParent', True),
            'roles': meta.get('roles', []),
            'auths': meta.get('auths', []),
            'keep_alive': meta.get('keepAlive', False),
            'frame_src': meta.get('frameSrc'),
            'frame_loading': meta.get('frameLoading', False),
            'hidden_tag': meta.get('hiddenTag', False),
            'dynamic_level': meta.get('dynamicLevel'),
            'active_path': meta.get('activePath'),
            
            # Transition 字段
            'transition_name': meta.get('transition', {}).get('name') if isinstance(meta.get('transition'), dict) else None,
            'enter_transition': meta.get('transition', {}).get('enterTransition') if isinstance(meta.get('transition'), dict) else None,
            'leave_transition': meta.get('transition', {}).get('leaveTransition') if isinstance(meta.get('transition'), dict) else None,
            
            # 状态字段
            'is_active': True,
        }

        if dry_run:
            # 试运行模式，只检查不写入
            existing = Menu.objects.filter(name=menu_data['name']).exists()
            if existing:
                return (menu_data, False, force)  # 如果force则会更新
            else:
                return (menu_data, True, False)  # 会创建

        # 实际导入
        try:
            existing_menu = Menu.objects.filter(name=menu_data['name']).first()
            
            if existing_menu:
                if force:
                    # 更新现有菜单
                    for key, value in menu_data.items():
                        setattr(existing_menu, key, value)
                    
                    # 设置父菜单
                    if parent_menu:
                        existing_menu.parent_id = parent_menu['id'] if isinstance(parent_menu, dict) else parent_menu.id
                    else:
                        existing_menu.parent = None
                    
                    existing_menu.save()
                    return (self._menu_to_dict(existing_menu), False, True)
                else:
                    # 跳过已存在的菜单
                    return (self._menu_to_dict(existing_menu), False, False)
            else:
                # 创建新菜单
                if parent_menu:
                    menu_data['parent_id'] = parent_menu['id'] if isinstance(parent_menu, dict) else parent_menu.id
                
                new_menu = Menu.objects.create(**menu_data)
                return (self._menu_to_dict(new_menu), True, False)
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'导入菜单失败 {menu_data["name"]}: {str(e)}'))
            return (menu_data, False, False)

    def _menu_to_dict(self, menu):
        """将Menu对象转换为字典"""
        return {
            'id': menu.id,
            'name': menu.name,
            'code': menu.code,
            'path': menu.path,
            'title': menu.title,
            'icon': menu.icon,
            'rank': menu.rank
        }

