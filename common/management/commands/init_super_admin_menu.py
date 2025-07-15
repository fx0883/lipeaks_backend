"""
初始化超级管理员菜单配置
"""
import json
import logging
from django.core.management.base import BaseCommand
from common.models import Config

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '初始化超级管理员菜单配置'

    def handle(self, *args, **options):
        # 超级管理员菜单配置
        super_admin_menu = [
            {
                "path": "/tenant",
                "name": "Tenant",
                "component": "Layout",
                "redirect": "/tenant/list",
                "meta": {
                    "icon": "ep:office-building",
                    "title": "租户管理",
                    "rank": 4,
                    "roles": ["admin", "tenant_admin"]
                },
                "children": [
                    {
                        "path": "list",
                        "name": "TenantList",
                        "component": "/src/views/tenant/list",
                        "meta": {
                            "title": "租户列表",
                            "roles": ["admin", "tenant_admin"]
                        }
                    },
                    {
                        "path": "detail/:id",
                        "name": "TenantDetail",
                        "component": "/src/views/tenant/detail",
                        "meta": {
                            "title": "租户详情",
                            "showLink": False,
                            "activePath": "/tenant/list",
                            "roles": ["admin", "tenant_admin"]
                        }
                    },
                    {
                        "path": "create",
                        "name": "TenantCreate",
                        "component": "/src/views/tenant/form",
                        "meta": {
                            "title": "创建租户",
                            "showLink": False,
                            "activePath": "/tenant/list",
                            "roles": ["admin", "tenant_admin"]
                        }
                    },
                    {
                        "path": "edit/:id",
                        "name": "TenantEdit",
                        "component": "/src/views/tenant/form",
                        "meta": {
                            "title": "编辑租户",
                            "showLink": False,
                            "activePath": "/tenant/list",
                            "roles": ["admin", "tenant_admin"]
                        }
                    }
                ]
            },
            {
                "path": "/user",
                "name": "User",
                "component": "Layout",
                "redirect": "/user/list",
                "meta": {
                    "title": "用户管理",
                    "icon": "ri:user-line",
                    "rank": 5,
                    "roles": ["admin", "tenant_admin"]
                },
                "children": [
                    {
                        "path": "list",
                        "name": "UserList",
                        "component": "/src/views/user/list/index",
                        "meta": {
                            "title": "用户列表",
                            "roles": ["admin", "tenant_admin"]
                        }
                    },
                    {
                        "path": "detail/:id",
                        "name": "UserDetail",
                        "component": "/src/views/user/detail/index",
                        "meta": {
                            "title": "用户详情",
                            "showLink": False,
                            "activePath": "/user/list",
                            "roles": ["admin", "tenant_admin"]
                        }
                    }
                ]
            },
            {
                "path": "/cms",
                "name": "CMS",
                "component": "Layout", 
                "redirect": "/cms/article/list",
                "meta": {
                    "icon": "ri:article-line",
                    "title": "内容管理",
                    "rank": 2,
                    "roles": ["admin", "content_editor"]
                },
                "children": [
                    {
                        "path": "statistics",
                        "name": "CMSStatistics",
                        "component": "/src/views/cms/statistics/index",
                        "meta": {
                            "title": "统计分析",
                            "icon": "ep:data-analysis",
                            "roles": ["admin", "content_editor"]
                        }
                    },
                    {
                        "path": "article",
                        "name": "CMSArticle",
                        "component": "/src/views/cms/article/index",
                        "redirect": "article/list",
                        "meta": {
                            "icon": "ri:article-line",
                            "title": "文章管理",
                            "roles": ["admin", "content_editor"]
                        },
                        "children": [
                            {
                                "path": "list",
                                "name": "ArticleList",
                                "component": "/src/views/cms/article/list",
                                "meta": {
                                    "title": "文章列表",
                                    "roles": ["admin", "content_editor"]
                                }
                            }
                        ]
                    }
                ]
            },
            {
                "path": "/system",
                "name": "System",
                "component": "Layout",
                "redirect": "/system/config",
                "meta": {
                    "icon": "ep:setting",
                    "title": "系统设置",
                    "rank": 10,
                    "roles": ["admin"]
                },
                "children": [
                    {
                        "path": "config",
                        "name": "SystemConfig",
                        "component": "/src/views/system/config/index",
                        "meta": {
                            "title": "系统配置",
                            "roles": ["admin"]
                        }
                    },
                    {
                        "path": "menu",
                        "name": "MenuManagement",
                        "component": "/src/views/system/menu/index",
                        "meta": {
                            "title": "菜单管理",
                            "roles": ["admin"]
                        }
                    },
                    {
                        "path": "log",
                        "name": "SystemLog",
                        "component": "/src/views/system/log/index",
                        "meta": {
                            "title": "系统日志",
                            "roles": ["admin"]
                        }
                    }
                ]
            }
        ]
        
        # 检查是否已存在超级管理员菜单配置
        if Config.objects.filter(key='super_admin_menu').exists():
            config = Config.objects.get(key='super_admin_menu')
            config.value = super_admin_menu
            config.save()
            self.stdout.write(self.style.SUCCESS('已更新超级管理员菜单配置'))
        else:
            # 创建超级管理员菜单配置
            Config.objects.create(
                name='超级管理员菜单配置',
                key='super_admin_menu',
                type='menu',
                value=super_admin_menu,
                description='超级管理员的菜单配置，包含系统所有功能模块的菜单项'
            )
            self.stdout.write(self.style.SUCCESS('已创建超级管理员菜单配置'))
        
        # 输出配置信息
        config = Config.objects.get(key='super_admin_menu')
        self.stdout.write(f"配置ID: {config.id}")
        self.stdout.write(f"配置名称: {config.name}")
        self.stdout.write(f"配置键: {config.key}")
        self.stdout.write(f"配置类型: {config.type}")
        self.stdout.write(f"菜单项数量: {len(config.value)}") 