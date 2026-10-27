import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from menus.models import Menu

logger = logging.getLogger(__name__)


APPLICATION_MENU_DATA = {
    "path": "/application",
    "name": "ApplicationManagement",
    "code": "application",
    "redirect": "/application/index",
    "component": "Layout1",
    "meta": {
        "title": "应用管理",
        "icon": "ri:apps-line",
        "showLink": True,
        "showParent": True,
        "rank": 5
    },
    "children": [
        {
            "path": "/application/index",
            "name": "ApplicationList",
            "code": "application_list",
            "component": "/src/views/application/index.vue",
            "meta": {
                "title": "应用列表",
                "icon": "ep:list",
                "showLink": True,
                "showParent": True,
                "keepAlive": True,
                "rank": 1
            }
        },
        {
            "path": "/application/create",
            "name": "ApplicationCreate",
            "code": "application_create",
            "component": "/src/views/application/create.vue",
            "meta": {
                "title": "创建应用",
                "icon": "ep:plus",
                "showLink": False,
                "showParent": False,
                "keepAlive": False,
                "activePath": "/application/index",
                "rank": 2
            }
        },
        {
            "path": "/application/edit/:id",
            "name": "ApplicationEdit",
            "code": "application_edit",
            "component": "/src/views/application/edit.vue",
            "meta": {
                "title": "编辑应用",
                "icon": "ep:edit",
                "showLink": False,
                "showParent": False,
                "keepAlive": False,
                "activePath": "/application/index",
                "rank": 3
            }
        },
        {
            "path": "/application/detail/:id",
            "name": "ApplicationDetail",
            "code": "application_detail",
            "component": "/src/views/application/detail.vue",
            "meta": {
                "title": "应用详情",
                "icon": "ep:view",
                "showLink": False,
                "showParent": False,
                "keepAlive": False,
                "activePath": "/application/index",
                "rank": 4
            }
        }
    ]
}


class Command(BaseCommand):
    help = "加载应用管理（Application）菜单数据到 Menu 表"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="强制重新加载菜单数据，覆盖现有同名或同code菜单",
        )

    def handle(self, *args, **options):
        force = options["force"]

        try:
            self.stdout.write(self.style.NOTICE("开始加载应用管理菜单数据..."))

            with transaction.atomic():
                self._create_or_update_menu(APPLICATION_MENU_DATA, None, force)

            self.stdout.write(self.style.SUCCESS("应用管理菜单数据加载成功！"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"加载应用管理菜单数据失败: {str(e)}"))
            logger.error(f"加载应用管理菜单数据失败: {str(e)}", exc_info=True)
            raise

    def _create_or_update_menu(self, menu_data, parent_menu, force):
        name = menu_data.get("name")
        code = menu_data.get("code") or name.lower()
        path = menu_data.get("path")
        meta = menu_data.get("meta", {})

        existing_menu = Menu.objects.filter(name=name).first() or Menu.objects.filter(code=code).first()

        if existing_menu:
            if not force:
                self.stdout.write(
                    self.style.WARNING(f'菜单 "{name}" (code: {code}) 已存在，跳过。使用 --force 参数覆盖。')
                )
            else:
                existing_menu.name = name
                existing_menu.code = code
                existing_menu.path = path
                existing_menu.component = menu_data.get("component")
                existing_menu.redirect = menu_data.get("redirect")
                existing_menu.title = meta.get("title", "")
                existing_menu.icon = meta.get("icon", "")
                existing_menu.rank = meta.get("rank", 0)
                existing_menu.show_link = meta.get("showLink", True)
                existing_menu.show_parent = meta.get("showParent", True)
                existing_menu.keep_alive = meta.get("keepAlive", False)
                existing_menu.active_path = meta.get("activePath")
                existing_menu.parent = parent_menu
                existing_menu.is_active = True
                existing_menu.save()
                self.stdout.write(self.style.SUCCESS(f"更新菜单: {name} (ID={existing_menu.id})"))

            current_menu = existing_menu
        else:
            current_menu = Menu(
                name=name,
                code=code,
                path=path,
                component=menu_data.get("component"),
                redirect=menu_data.get("redirect"),
                title=meta.get("title", ""),
                icon=meta.get("icon", ""),
                rank=meta.get("rank", 0),
                show_link=meta.get("showLink", True),
                show_parent=meta.get("showParent", True),
                keep_alive=meta.get("keepAlive", False),
                active_path=meta.get("activePath"),
                parent=parent_menu,
                is_active=True,
                remarks="由 load_application_menus 命令初始化导入",
            )
            current_menu.save()
            self.stdout.write(self.style.SUCCESS(f"创建菜单: {name} (ID={current_menu.id})"))

        if "children" in menu_data:
            for child_data in menu_data.get("children", []):
                self._create_or_update_menu(child_data, current_menu, force)
