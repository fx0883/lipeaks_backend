"""
初始化RBAC系统的示例数据
"""
import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from rbac.models import Permission, Role, RolePermission, UserRole

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '初始化RBAC系统的示例权限和角色数据'

    def handle(self, *args, **kwargs):
        try:
            with transaction.atomic():
                self._create_permissions()
                self._create_roles()
                self._assign_permissions_to_roles()
                
            self.stdout.write(self.style.SUCCESS('成功初始化RBAC示例数据'))
        except Exception as e:
            logger.error(f"初始化RBAC数据失败: {str(e)}", exc_info=True)
            self.stdout.write(self.style.ERROR(f'初始化RBAC数据失败: {str(e)}'))

    def _create_permissions(self):
        """创建权限数据"""
        self.stdout.write('正在创建权限数据...')
        
        # 用户管理权限
        permissions_data = [
            # 用户管理权限
            {
                'code': 'user:view', 
                'name': '查看用户', 
                'description': '允许查看用户列表和详情', 
                'category': '用户管理',
                'is_system': True
            },
            {
                'code': 'user:create', 
                'name': '创建用户', 
                'description': '允许创建新用户', 
                'category': '用户管理',
                'is_system': True
            },
            {
                'code': 'user:edit', 
                'name': '编辑用户', 
                'description': '允许编辑用户信息', 
                'category': '用户管理',
                'is_system': True
            },
            {
                'code': 'user:delete', 
                'name': '删除用户', 
                'description': '允许删除用户', 
                'category': '用户管理',
                'is_system': True
            },
            
            # 权限管理
            {
                'code': 'permission:view', 
                'name': '查看权限', 
                'description': '允许查看权限列表和详情', 
                'category': '权限管理',
                'is_system': True
            },
            {
                'code': 'permission:create', 
                'name': '创建权限', 
                'description': '允许创建新权限', 
                'category': '权限管理',
                'is_system': True
            },
            {
                'code': 'permission:edit', 
                'name': '编辑权限', 
                'description': '允许编辑权限信息', 
                'category': '权限管理',
                'is_system': True
            },
            {
                'code': 'permission:delete', 
                'name': '删除权限', 
                'description': '允许删除权限', 
                'category': '权限管理',
                'is_system': True
            },
            {
                'code': 'permission:assign', 
                'name': '分配权限', 
                'description': '允许将权限分配给角色', 
                'category': '权限管理',
                'is_system': True
            },
            {
                'code': 'permission:manage', 
                'name': '管理权限', 
                'description': '允许管理权限缓存和高级设置', 
                'category': '权限管理',
                'is_system': True
            },
            
            # 角色管理
            {
                'code': 'role:view', 
                'name': '查看角色', 
                'description': '允许查看角色列表和详情', 
                'category': '角色管理',
                'is_system': True
            },
            {
                'code': 'role:create', 
                'name': '创建角色', 
                'description': '允许创建新角色', 
                'category': '角色管理',
                'is_system': True
            },
            {
                'code': 'role:edit', 
                'name': '编辑角色', 
                'description': '允许编辑角色信息', 
                'category': '角色管理',
                'is_system': True
            },
            {
                'code': 'role:delete', 
                'name': '删除角色', 
                'description': '允许删除角色', 
                'category': '角色管理',
                'is_system': True
            },
            {
                'code': 'role:assign', 
                'name': '分配角色', 
                'description': '允许将角色分配给用户', 
                'category': '角色管理',
                'is_system': True
            },
            
            # 租户管理
            {
                'code': 'tenant:view', 
                'name': '查看租户', 
                'description': '允许查看租户列表和详情', 
                'category': '租户管理',
                'is_system': True
            },
            {
                'code': 'tenant:create', 
                'name': '创建租户', 
                'description': '允许创建新租户', 
                'category': '租户管理',
                'is_system': True
            },
            {
                'code': 'tenant:edit', 
                'name': '编辑租户', 
                'description': '允许编辑租户信息', 
                'category': '租户管理',
                'is_system': True
            },
            {
                'code': 'tenant:delete', 
                'name': '删除租户', 
                'description': '允许删除租户', 
                'category': '租户管理',
                'is_system': True
            },
            
            # 内容管理
            {
                'code': 'content:view', 
                'name': '查看内容', 
                'description': '允许查看内容列表和详情', 
                'category': '内容管理',
                'is_system': True
            },
            {
                'code': 'content:create', 
                'name': '创建内容', 
                'description': '允许创建新内容', 
                'category': '内容管理',
                'is_system': True
            },
            {
                'code': 'content:edit', 
                'name': '编辑内容', 
                'description': '允许编辑内容', 
                'category': '内容管理',
                'is_system': True
            },
            {
                'code': 'content:delete', 
                'name': '删除内容', 
                'description': '允许删除内容', 
                'category': '内容管理',
                'is_system': True
            },
            {
                'code': 'content:publish', 
                'name': '发布内容', 
                'description': '允许发布内容', 
                'category': '内容管理',
                'is_system': True
            },
            
            # 系统管理
            {
                'code': 'system:view', 
                'name': '查看系统设置', 
                'description': '允许查看系统设置', 
                'category': '系统管理',
                'is_system': True
            },
            {
                'code': 'system:edit', 
                'name': '编辑系统设置', 
                'description': '允许编辑系统设置', 
                'category': '系统管理',
                'is_system': True
            },
        ]
        
        created_count = 0
        for perm_data in permissions_data:
            permission, created = Permission.objects.update_or_create(
                code=perm_data['code'],
                defaults={
                    'name': perm_data['name'],
                    'description': perm_data['description'],
                    'category': perm_data['category'],
                    'is_system': perm_data['is_system']
                }
            )
            if created:
                created_count += 1
        
        self.stdout.write(f'创建了 {created_count} 条权限数据')

    def _create_roles(self):
        """创建角色数据"""
        self.stdout.write('正在创建角色数据...')
        
        roles_data = [
            # 系统级角色
            {
                'name': '系统管理员',
                'code': 'system_admin',
                'description': '系统级管理员，可以管理所有系统设置和权限',
                'tenant': None,
                'is_system': True
            },
            {
                'name': '用户管理员',
                'code': 'user_admin',
                'description': '负责管理系统用户',
                'tenant': None,
                'is_system': True
            },
            {
                'name': '内容管理员',
                'code': 'content_admin',
                'description': '负责管理系统所有内容',
                'tenant': None,
                'is_system': True
            },
            {
                'name': '只读用户',
                'code': 'readonly_user',
                'description': '只有查看权限的用户',
                'tenant': None,
                'is_system': True
            },
            
            # 示例：为租户1创建一些角色（如果已有租户表）
            # 注意：这里假设租户ID为1，如果需要，请调整或注释掉
            # {
            #     'name': '租户管理员',
            #     'code': 'tenant_admin',
            #     'description': '租户级管理员，可以管理租户内的所有设置',
            #     'tenant_id': 1,
            #     'is_system': False
            # },
            # {
            #     'name': '租户编辑',
            #     'code': 'tenant_editor',
            #     'description': '可以管理租户内容',
            #     'tenant_id': 1,
            #     'is_system': False
            # },
            # {
            #     'name': '租户成员',
            #     'code': 'tenant_member',
            #     'description': '基本租户成员，拥有有限权限',
            #     'tenant_id': 1,
            #     'is_system': False
            # },
        ]
        
        created_count = 0
        for role_data in roles_data:
            role, created = Role.objects.update_or_create(
                code=role_data['code'],
                tenant=role_data.get('tenant'),
                defaults={
                    'name': role_data['name'],
                    'description': role_data['description'],
                    'is_system': role_data['is_system']
                }
            )
            if created:
                created_count += 1
        
        self.stdout.write(f'创建了 {created_count} 条角色数据')

    def _assign_permissions_to_roles(self):
        """给角色分配权限"""
        self.stdout.write('正在分配权限到角色...')
        
        # 为系统管理员分配所有权限
        try:
            system_admin = Role.objects.get(code='system_admin')
            all_permissions = Permission.objects.all()
            for permission in all_permissions:
                RolePermission.objects.get_or_create(
                    role=system_admin,
                    permission=permission
                )
            self.stdout.write(f'为系统管理员分配了 {all_permissions.count()} 个权限')
        except Role.DoesNotExist:
            self.stdout.write(self.style.WARNING('未找到系统管理员角色'))
        
        # 为用户管理员分配用户管理权限
        try:
            user_admin = Role.objects.get(code='user_admin')
            user_permissions = Permission.objects.filter(category='用户管理')
            for permission in user_permissions:
                RolePermission.objects.get_or_create(
                    role=user_admin,
                    permission=permission
                )
            
            # 也需要角色查看和分配权限
            role_view_perm = Permission.objects.filter(code='role:view').first()
            role_assign_perm = Permission.objects.filter(code='role:assign').first()
            
            if role_view_perm:
                RolePermission.objects.get_or_create(
                    role=user_admin,
                    permission=role_view_perm
                )
            
            if role_assign_perm:
                RolePermission.objects.get_or_create(
                    role=user_admin,
                    permission=role_assign_perm
                )
            
            self.stdout.write(f'为用户管理员分配了 {user_permissions.count()} 个用户管理权限')
        except Role.DoesNotExist:
            self.stdout.write(self.style.WARNING('未找到用户管理员角色'))
        
        # 为内容管理员分配内容管理权限
        try:
            content_admin = Role.objects.get(code='content_admin')
            content_permissions = Permission.objects.filter(category='内容管理')
            for permission in content_permissions:
                RolePermission.objects.get_or_create(
                    role=content_admin,
                    permission=permission
                )
            self.stdout.write(f'为内容管理员分配了 {content_permissions.count()} 个内容管理权限')
        except Role.DoesNotExist:
            self.stdout.write(self.style.WARNING('未找到内容管理员角色'))
        
        # 为只读用户分配查看权限
        try:
            readonly_user = Role.objects.get(code='readonly_user')
            view_permissions = Permission.objects.filter(code__endswith=':view')
            for permission in view_permissions:
                RolePermission.objects.get_or_create(
                    role=readonly_user,
                    permission=permission
                )
            self.stdout.write(f'为只读用户分配了 {view_permissions.count()} 个查看权限')
        except Role.DoesNotExist:
            self.stdout.write(self.style.WARNING('未找到只读用户角色')) 