import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from menus.models import Menu

logger = logging.getLogger(__name__)


FEEDBACK_MENU_DATA = {
    "path": "/feedback",
    "name": "FeedbackManagement",
    "code": "feedback",
    "redirect": "/feedback/list",
    "component": "Layout1",
    "meta": {
        "title": "反馈管理",
        "icon": "ri:feedback-line",
        "showLink": True,
        "showParent": True,
        "rank": 6,
    },
    "children": [
        {
            "path": "/feedback/list",
            "name": "FeedbackList",
            "code": "feedback_list",
            "component": "/src/views/feedback/feedbacks/index.vue",
            "meta": {
                "title": "反馈列表",
                "icon": "ep:list",
                "showLink": True,
                "showParent": True,
                "keepAlive": True,
                "rank": 1,
            },
        },
        {
            "path": "/feedback/feedbacks/detail/:id",
            "name": "FeedbackDetail",
            "code": "feedback_detail",
            "component": "/src/views/feedback/feedbacks/detail.vue",
            "meta": {
                "title": "反馈详情",
                "icon": "ep:view",
                "showLink": False,
                "showParent": False,
                "keepAlive": False,
                "activePath": "/feedback/list",
                "rank": 2,
            },
        },
        {
            "path": "/feedback/statistics",
            "name": "FeedbackStatistics",
            "code": "feedback_statistics",
            "component": "/src/views/feedback/statistics/index.vue",
            "meta": {
                "title": "统计分析",
                "icon": "ep:data-analysis",
                "showLink": True,
                "showParent": True,
                "keepAlive": True,
                "rank": 3,
            },
        },
        {
            "path": "/feedback/notification/config",
            "name": "FeedbackNotificationConfig",
            "code": "feedback_notification_config",
            "component": "/src/views/feedback/notification/config/index.vue",
            "meta": {
                "title": "通知配置",
                "icon": "ep:bell",
                "showLink": True,
                "showParent": True,
                "keepAlive": True,
                "rank": 4,
            },
        },
        {
            "path": "/feedback/email/templates",
            "name": "FeedbackEmailTemplates",
            "code": "feedback_email_templates",
            "component": "/src/views/feedback/email/templates/index.vue",
            "meta": {
                "title": "邮件模板",
                "icon": "ep:message",
                "showLink": True,
                "showParent": True,
                "keepAlive": True,
                "rank": 5,
            },
        },
        {
            "path": "/feedback/email/logs",
            "name": "FeedbackEmailLogs",
            "code": "feedback_email_logs",
            "component": "/src/views/feedback/email/logs/index.vue",
            "meta": {
                "title": "邮件日志",
                "icon": "ep:tickets",
                "showLink": True,
                "showParent": True,
                "keepAlive": True,
                "rank": 6,
            },
        },
    ],
}


class Command(BaseCommand):
    help = "加载反馈管理（Feedback）动态菜单数据到 Menu 表"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="强制重新加载菜单数据，覆盖现有同名或同code菜单",
        )

    def handle(self, *args, **options):
        force = options["force"]

        try:
            self.stdout.write(self.style.NOTICE("开始加载反馈管理菜单数据..."))

            with transaction.atomic():
                self._create_or_update_menu(FEEDBACK_MENU_DATA, None, force)

            self.stdout.write(self.style.SUCCESS("反馈管理菜单数据加载成功！"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"加载反馈管理菜单数据失败: {str(e)}"))
            logger.error(f"加载反馈管理菜单数据失败: {str(e)}", exc_info=True)
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
                remarks="由 load_feedback_menus 命令初始化导入",
            )
            current_menu.save()
            self.stdout.write(self.style.SUCCESS(f"创建菜单: {name} (ID={current_menu.id})"))

        if "children" in menu_data:
            for child_data in menu_data.get("children", []):
                self._create_or_update_menu(child_data, current_menu, force)
