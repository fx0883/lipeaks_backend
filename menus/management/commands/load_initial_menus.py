"""
加载初始菜单数据的管理命令
"""
import os
import logging
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from menus.models import Menu

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '加载初始菜单数据'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制重新加载菜单数据，覆盖现有数据',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        # 检查是否已存在菜单数据
        existing_menus = Menu.objects.exists()
        
        if existing_menus and not force:
            self.stdout.write(self.style.WARNING('数据库中已存在菜单数据。如果要重新加载，请使用 --force 选项。'))
            return
        
        # 如果需要强制重新加载，先清除现有数据
        if force and existing_menus:
            self.stdout.write(self.style.WARNING('清除现有菜单数据...'))
            Menu.objects.all().delete()
        
        # 加载fixture数据
        fixtures_path = os.path.join(
            settings.BASE_DIR, 'menus', 'fixtures', 'initial_menus.json'
        )
        
        if not os.path.exists(fixtures_path):
            self.stdout.write(self.style.ERROR(f'找不到初始菜单数据文件: {fixtures_path}'))
            return
        
        try:
            self.stdout.write(self.style.NOTICE('正在加载初始菜单数据...'))
            call_command('loaddata', fixtures_path)
            self.stdout.write(self.style.SUCCESS('初始菜单数据加载成功！'))
            
            # 输出加载的菜单数量
            menu_count = Menu.objects.count()
            self.stdout.write(self.style.SUCCESS(f'共加载了 {menu_count} 个菜单项'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'加载数据时出错: {str(e)}'))
            logger.error(f"初始菜单数据加载失败: {str(e)}", exc_info=True) 