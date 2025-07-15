"""
初始化RBAC系统权限和角色
"""
import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from rbac.models import Permission, Role, RolePermission

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '初始化RBAC权限系统的基础权限和角色'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='重置所有RBAC数据（谨慎使用，将删除所有权限和角色）'
        )

    def handle(self, *args, **options):
        reset = options.get('reset', False)
        
        if reset:
            self.stdout.write(self.style.WARNING('警告：即将重置所有RBAC数据...'))
            confirm = input('确认重置所有RBAC权限和角色数据？(y/n): ')
            if confirm.lower() != 'y':
                self.stdout.write(self.style.ERROR('操作已取消'))
                return
            
            # 删除所有数据
            RolePermission.objects.all().delete()
            Role.objects.all().delete()
            Permission.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('已删除所有RBAC数据'))
        
        self.stdout.write(self.style.NOTICE('开始初始化RBAC权限系统...'))
        
        try:
            with transaction.atomic():
                # 创建基础权限
                self.create_permissions()
                
                # 创建基础角色
                self.create_roles()
                
                # 分配角色权限
                self.assign_permissions()
                
            self.stdout.write(self.style.SUCCESS('RBAC权限系统初始化完成'))
        
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'初始化过程中发生错误: {str(e)}'))
            logger.exception('初始化RBAC权限系统失败')

    def create_permissions(self):
        """
        创建基础权限
        """
        self.stdout.write('正在创建基础权限...')
        
        # 用户管理权限
        user_permissions = [
            {'code': 'user:view', 'name': '查看用户', 'category': '用户管理', 'is_system': True},
            {'code': 'user:create', 'name': '创建用户', 'category': '用户管理', 'is_system': True},
            {'code': 'user:edit', 'name': '编辑用户', 'category': '用户管理', 'is_system': True},
            {'code': 'user:delete', 'name': '删除用户', 'category': '用户管理', 'is_system': True},
        ]
        
        # 角色管理权限
        role_permissions = [
            {'code': 'role:view', 'name': '查看角色', 'category': '角色管理', 'is_system': True},
            {'code': 'role:create', 'name': '创建角色', 'category': '角色管理', 'is_system': True},
            {'code': 'role:edit', 'name': '编辑角色', 'category': '角色管理', 'is_system': True},
            {'code': 'role:delete', 'name': '删除角色', 'category': '角色管理', 'is_system': True},
        ]
        
        # 权限管理权限
        permission_permissions = [
            {'code': 'permission:view', 'name': '查看权限', 'category': '权限管理', 'is_system': True},
            {'code': 'permission:assign', 'name': '分配权限', 'category': '权限管理', 'is_system': True},
        ]
        
        # 租户管理权限
        tenant_permissions = [
            {'code': 'tenant:view', 'name': '查看租户', 'category': '租户管理', 'is_system': True},
            {'code': 'tenant:create', 'name': '创建租户', 'category': '租户管理', 'is_system': True},
            {'code': 'tenant:edit', 'name': '编辑租户', 'category': '租户管理', 'is_system': True},
            {'code': 'tenant:delete', 'name': '删除租户', 'category': '租户管理', 'is_system': True},
        ]
        
        # CMS权限
        cms_permissions = [
            {'code': 'cms:view', 'name': '查看内容', 'category': 'CMS管理', 'is_system': True},
            {'code': 'cms:create', 'name': '创建内容', 'category': 'CMS管理', 'is_system': True},
            {'code': 'cms:edit', 'name': '编辑内容', 'category': 'CMS管理', 'is_system': True},
            {'code': 'cms:publish', 'name': '发布内容', 'category': 'CMS管理', 'is_system': True},
            {'code': 'cms:delete', 'name': '删除内容', 'category': 'CMS管理', 'is_system': True},
        ]
        
        # 打卡系统权限
        check_permissions = [
            {'code': 'check:view', 'name': '查看打卡记录', 'category': '打卡系统', 'is_system': True},
            {'code': 'check:create', 'name': '创建打卡记录', 'category': '打卡系统', 'is_system': True},
            {'code': 'check:edit', 'name': '编辑打卡记录', 'category': '打卡系统', 'is_system': True},
            {'code': 'check:report', 'name': '生成打卡报表', 'category': '打卡系统', 'is_system': True},
            {'code': 'check:export', 'name': '导出打卡数据', 'category': '打卡系统', 'is_system': True},
        ]
        
        # 菜单管理权限
        menu_permissions = [
            {'code': 'menu:view', 'name': '查看菜单', 'category': '菜单管理', 'is_system': True},
            {'code': 'menu:create', 'name': '创建菜单', 'category': '菜单管理', 'is_system': True},
            {'code': 'menu:edit', 'name': '编辑菜单', 'category': '菜单管理', 'is_system': True},
            {'code': 'menu:delete', 'name': '删除菜单', 'category': '菜单管理', 'is_system': True},
        ]
        
        # 图表权限
        chart_permissions = [
            {'code': 'chart:view', 'name': '查看图表', 'category': '图表管理', 'is_system': True},
            {'code': 'chart:create', 'name': '创建图表', 'category': '图表管理', 'is_system': True},
            {'code': 'chart:edit', 'name': '编辑图表', 'category': '图表管理', 'is_system': True},
            {'code': 'chart:delete', 'name': '删除图表', 'category': '图表管理', 'is_system': True},
            {'code': 'chart:export', 'name': '导出图表', 'category': '图表管理', 'is_system': True},
        ]
        
        # 合并所有权限
        all_permissions = (
            user_permissions + 
            role_permissions + 
            permission_permissions + 
            tenant_permissions + 
            cms_permissions + 
            check_permissions +
            menu_permissions +
            chart_permissions
        )
        
        # 创建权限
        created_count = 0
        for perm_data in all_permissions:
            permission, created = Permission.objects.get_or_create(
                code=perm_data['code'],
                defaults={
                    'name': perm_data['name'],
                    'category': perm_data['category'],
                    'is_system': perm_data['is_system']
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'  - 创建权限: {permission.name} ({permission.code})')
            else:
                # 更新已有权限
                updated = False
                for field in ['name', 'category', 'is_system']:
                    if getattr(permission, field) != perm_data[field]:
                        setattr(permission, field, perm_data[field])
                        updated = True
                
                if updated:
                    permission.save()
                    self.stdout.write(f'  - 更新权限: {permission.name} ({permission.code})')
        
        self.stdout.write(self.style.SUCCESS(f'创建了 {created_count} 个权限'))

    def create_roles(self):
        """
        创建基础角色
        """
        self.stdout.write('正在创建基础角色...')
        
        # 系统角色（不关联租户）
        system_roles = [
            {
                'name': '超级管理员', 
                'code': 'super_admin', 
                'is_system': True,
                'description': '拥有所有权限的超级管理员'
            },
            {
                'name': '租户管理员', 
                'code': 'tenant_admin', 
                'is_system': True,
                'description': '租户的管理员角色，拥有租户内的所有权限'
            },
        ]
        
        # 租户角色（需要在使用时关联到具体租户）
        tenant_roles = [
            {
                'name': '内容编辑', 
                'code': 'content_editor', 
                'is_system': True,
                'description': '拥有内容管理相关权限的角色'
            },
            {
                'name': '用户管理员', 
                'code': 'user_manager', 
                'is_system': True,
                'description': '拥有用户管理相关权限的角色'
            },
            {
                'name': '普通成员', 
                'code': 'normal_user', 
                'is_system': True,
                'description': '普通成员角色，拥有基本操作权限'
            },
        ]
        
        # 创建系统角色
        created_count = 0
        for role_data in system_roles:
            role, created = Role.objects.get_or_create(
                code=role_data['code'],
                defaults={
                    'name': role_data['name'],
                    'description': role_data['description'],
                    'is_system': role_data['is_system'],
                    'tenant': None  # 系统角色不关联租户
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'  - 创建角色: {role.name} ({role.code})')
            else:
                # 更新已有角色
                updated = False
                for field in ['name', 'description', 'is_system']:
                    if getattr(role, field) != role_data[field]:
                        setattr(role, field, role_data[field])
                        updated = True
                
                if updated:
                    role.save()
                    self.stdout.write(f'  - 更新角色: {role.name} ({role.code})')
        
        # 可以在这里创建租户角色的模板，但实际使用时需要关联到具体租户
        # 这里只是保存模板，不实际创建关联到租户的角色
        for role_data in tenant_roles:
            role, created = Role.objects.get_or_create(
                code=role_data['code'],
                tenant=None,  # 作为模板，不关联租户
                defaults={
                    'name': role_data['name'],
                    'description': role_data['description'],
                    'is_system': role_data['is_system'],
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'  - 创建角色模板: {role.name} ({role.code})')
            else:
                # 更新已有角色
                updated = False
                for field in ['name', 'description', 'is_system']:
                    if getattr(role, field) != role_data[field]:
                        setattr(role, field, role_data[field])
                        updated = True
                
                if updated:
                    role.save()
                    self.stdout.write(f'  - 更新角色模板: {role.name} ({role.code})')
        
        self.stdout.write(self.style.SUCCESS(f'创建了 {created_count} 个角色'))

    def assign_permissions(self):
        """
        为基础角色分配权限
        """
        self.stdout.write('正在为角色分配权限...')
        
        # 超级管理员拥有所有权限，不需要显式分配
        
        # 租户管理员权限
        tenant_admin_permissions = [
            'user:view', 'user:create', 'user:edit', 'user:delete',
            'role:view', 'role:create', 'role:edit', 'role:delete',
            'permission:view', 'permission:assign',
            'cms:view', 'cms:create', 'cms:edit', 'cms:publish', 'cms:delete',
            'check:view', 'check:create', 'check:edit', 'check:report', 'check:export',
            'menu:view', 'menu:create', 'menu:edit', 'menu:delete',
            'chart:view', 'chart:create', 'chart:edit', 'chart:delete', 'chart:export',
        ]
        
        # 内容编辑权限
        content_editor_permissions = [
            'cms:view', 'cms:create', 'cms:edit', 'cms:publish',
            'menu:view',
            'chart:view',
        ]
        
        # 用户管理员权限
        user_manager_permissions = [
            'user:view', 'user:create', 'user:edit',
            'role:view',
            'permission:view',
        ]
        
        # 普通成员权限
        normal_user_permissions = [
            'cms:view',
            'check:view', 'check:create',
            'menu:view',
            'chart:view',
        ]
        
        # 角色权限映射
        role_permissions_map = {
            'tenant_admin': tenant_admin_permissions,
            'content_editor': content_editor_permissions,
            'user_manager': user_manager_permissions,
            'normal_user': normal_user_permissions,
        }
        
        # 为每个角色分配权限
        for role_code, permission_codes in role_permissions_map.items():
            try:
                role = Role.objects.get(code=role_code, tenant=None)
                
                # 获取权限对象
                permissions = Permission.objects.filter(code__in=permission_codes)
                
                # 记录分配的权限
                assigned_count = 0
                for permission in permissions:
                    _, created = RolePermission.objects.get_or_create(
                        role=role,
                        permission=permission
                    )
                    if created:
                        assigned_count += 1
                
                self.stdout.write(f'  - 为角色 {role.name} 分配了 {assigned_count} 个权限')
                
            except Role.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'角色 {role_code} 不存在，跳过权限分配'))
        
        self.stdout.write(self.style.SUCCESS('角色权限分配完成')) 