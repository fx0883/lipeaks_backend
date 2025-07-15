"""
创建超级管理员的管理命令
"""
import logging
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from tenants.models import Tenant
from users.models import User

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    """
    创建超级管理员的命令
    """
    help = '创建超级管理员用户'

    def add_arguments(self, parser):
        """
        添加命令行参数
        """
        parser.add_argument('--username', type=str, required=True, help='用户名')
        parser.add_argument('--password', type=str, required=True, help='密码')
        parser.add_argument('--email', type=str, required=True, help='电子邮箱')
        parser.add_argument('--nick_name', type=str, help='昵称（可选）')
        parser.add_argument('--phone', type=str, help='手机号（可选）')
        parser.add_argument('--tenant', type=str, help='关联租户名称（可选，如不指定则无租户）')

    def handle(self, *args, **options):
        """
        命令处理
        """
        username = options['username']
        password = options['password']
        email = options['email']
        nick_name = options.get('nick_name')
        phone = options.get('phone')
        tenant_name = options.get('tenant')

        try:
            # 检查用户是否已存在
            if User.objects.filter(username=username).exists():
                raise CommandError(f'用户名 {username} 已存在')
            
            if User.objects.filter(email=email).exists():
                raise CommandError(f'邮箱 {email} 已存在')
            
            # 获取租户（如果指定）
            tenant = None
            if tenant_name:
                try:
                    tenant = Tenant.objects.get(name=tenant_name)
                    self.stdout.write(f'关联到租户: {tenant.name}')
                except Tenant.DoesNotExist:
                    self.stdout.write(f'找不到租户 {tenant_name}，将创建新租户')
                    tenant = Tenant.objects.create(
                        name=tenant_name,
                        status='active'
                    )
            
            # 创建超级管理员
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password
                )
                
                # 设置额外字段
                user.is_superuser = True  # Django内置超级用户标志
                user.is_staff = True      # Django内置管理员标志
                user.is_super_admin = True
                user.is_admin = True
                
                if nick_name:
                    user.nick_name = nick_name
                
                if phone:
                    user.phone = phone
                
                # 超级管理员应该没有租户关联，所以这里不设置tenant字段
                
                user.save()
                
                self.stdout.write(self.style.SUCCESS(f'成功创建超级管理员: {username}'))
        
        except CommandError as e:
            logger.error(f"创建超级管理员命令失败: {str(e)}")
            raise
        
        except Exception as e:
            logger.exception(f"创建超级管理员时发生未预期的错误")
            raise CommandError(f'创建超级管理员失败: {str(e)}') 