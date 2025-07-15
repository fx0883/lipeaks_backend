import json
import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from menus.models import Menu

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '基于提供的JSON数据加载CMS菜单'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制重新加载菜单数据，覆盖现有同名菜单',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        # 提供的CMS菜单数据JSON
        menu_json = '''{
  "path": "/cms",
  "name": "CMS",
  "redirect": "/cms/article",
  "meta": {
    "title": "menus.cmsManagement",
    "icon": "ri:article-line",
    "showLink": true,
    "rank": 5
  },
  "children": [
    {
      "path": "/cms/article",
      "name": "ArticleManagement",
      "component": "cms/article/index",
      "meta": {
        "title": "menus.articleManagement",
        "icon": "ri:file-list-line",
        "showLink": true,
        "keepAlive": true
      }
    },
    {
      "path": "/cms/article/create",
      "name": "ArticleCreate",
      "component": "cms/article/create",
      "meta": {
        "title": "menus.articleCreate",
        "showLink": false,
        "keepAlive": false,
        "activePath": "/cms/article"
      }
    },
    {
      "path": "/cms/article/edit/:id",
      "name": "ArticleEdit",
      "component": "cms/article/edit",
      "meta": {
        "title": "menus.articleEdit",
        "showLink": false,
        "keepAlive": false,
        "activePath": "/cms/article"
      }
    },
    {
      "path": "/cms/article/detail/:id",
      "name": "ArticleDetail",
      "component": "cms/article/detail",
      "meta": {
        "title": "menus.articleDetail",
        "showLink": false,
        "keepAlive": false,
        "activePath": "/cms/article"
      }
    },
    {
      "path": "/cms/comment",
      "name": "CommentManagement",
      "component": "cms/comment/index",
      "meta": {
        "title": "menus.commentManagement",
        "icon": "ri:chat-1-line",
        "showLink": true,
        "keepAlive": true
      }
    },
    {
      "path": "/cms/comment/detail/:id",
      "name": "CommentDetail",
      "component": "cms/comment/detail",
      "meta": {
        "title": "menus.commentDetail",
        "showLink": false,
        "keepAlive": false,
        "activePath": "/cms/comment"
      }
    },
    {
      "path": "/cms/category",
      "name": "CategoryManagement",
      "component": "cms/category/index",
      "meta": {
        "title": "menus.categoryManagement",
        "icon": "ri:folder-2-line",
        "showLink": true,
        "keepAlive": true
      }
    },
    {
      "path": "/cms/tag",
      "name": "TagManagement",
      "component": "cms/tag/index",
      "meta": {
        "title": "menus.tagManagement",
        "icon": "ri:price-tag-3-line",
        "showLink": true,
        "keepAlive": true
      }
    }
  ]
}'''
        
        try:
            menu_data = json.loads(menu_json)
            self.stdout.write(self.style.SUCCESS('成功解析菜单JSON数据'))
            
            # 开始事务
            with transaction.atomic():
                # 创建主菜单
                self._create_or_update_menu(menu_data, None, force)
                
            self.stdout.write(self.style.SUCCESS('CMS菜单数据加载完成'))
            
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR('菜单数据格式错误，请检查JSON格式'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'加载菜单数据时出错: {str(e)}'))
            logger.error(f"加载CMS菜单数据失败: {str(e)}", exc_info=True)
    
    def _create_or_update_menu(self, menu_data, parent_menu, force):
        """
        递归创建或更新菜单及其子菜单
        """
        # 检查菜单是否已存在
        name = menu_data.get('name')
        path = menu_data.get('path')
        existing_menu = Menu.objects.filter(name=name).first()
        
        meta = menu_data.get('meta', {})
        
        if existing_menu:
            if not force:
                self.stdout.write(self.style.WARNING(f'菜单 "{name}" 已存在，跳过。使用 --force 参数覆盖。'))
                # 仍然处理子菜单
                if 'children' in menu_data:
                    for child_data in menu_data.get('children', []):
                        self._create_or_update_menu(child_data, existing_menu, force)
                return existing_menu
            
            # 更新现有菜单
            existing_menu.path = path
            existing_menu.component = menu_data.get('component')
            existing_menu.redirect = menu_data.get('redirect')
            existing_menu.title = meta.get('title', '')
            existing_menu.icon = meta.get('icon', '')
            existing_menu.rank = meta.get('rank', 0)
            existing_menu.show_link = meta.get('showLink', True)
            existing_menu.show_parent = meta.get('showParent', True)
            existing_menu.keep_alive = meta.get('keepAlive', False)
            existing_menu.active_path = meta.get('activePath')
            existing_menu.parent = parent_menu
            existing_menu.is_active = True
            
            # 生成code如果不存在
            if not existing_menu.code:
                existing_menu.code = name.lower()
                
            existing_menu.save()
            self.stdout.write(self.style.SUCCESS(f'更新菜单: {name}'))
            menu = existing_menu
        else:
            # 创建新菜单
            menu = Menu(
                name=name,
                code=name.lower(),  # 使用小写name作为code
                path=path,
                component=menu_data.get('component'),
                redirect=menu_data.get('redirect'),
                title=meta.get('title', ''),
                icon=meta.get('icon', ''),
                rank=meta.get('rank', 0),
                show_link=meta.get('showLink', True),
                show_parent=meta.get('showParent', True),
                keep_alive=meta.get('keepAlive', False),
                active_path=meta.get('activePath'),
                parent=parent_menu,
                is_active=True,
                remarks=f"由load_provided_cms_menus命令导入"
            )
            menu.save()
            self.stdout.write(self.style.SUCCESS(f'创建菜单: {name}'))
        
        # 递归处理子菜单
        if 'children' in menu_data:
            for child_data in menu_data.get('children', []):
                self._create_or_update_menu(child_data, menu, force)
        
        return menu 