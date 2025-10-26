"""
更新管理员用户的 staff 状态

确保所有管理员用户（包括租户管理员）的 is_staff 字段都设置为 True
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from users.models import User


class Command(BaseCommand):
    help = '更新所有管理员用户的 is_staff 状态'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='试运行，不实际修改数据'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        dry_run = options['dry_run']

        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('更新管理员 is_staff 状态'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        if dry_run:
            self.stdout.write(self.style.WARNING('\n试运行模式 - 不会实际修改数据\n'))

        # 查找所有管理员用户
        admin_users = User.objects.filter(is_admin=True)
        total_count = admin_users.count()
        
        self.stdout.write(f'\n找到 {total_count} 个管理员用户')

        # 查找需要更新的用户
        need_update = admin_users.filter(is_staff=False)
        update_count = need_update.count()

        self.stdout.write(f'需要更新 is_staff 的用户: {update_count}')

        if update_count == 0:
            self.stdout.write(self.style.SUCCESS('\n所有管理员用户的 is_staff 状态已正确！'))
            return

        # 显示需要更新的用户
        self.stdout.write('\n需要更新的用户:')
        for user in need_update:
            role = "超级管理员" if user.is_super_admin else "租户管理员"
            tenant = user.tenant.name if user.tenant else "无租户"
            self.stdout.write(f'  - {user.username} ({role}, {tenant})')

        if not dry_run:
            # 执行更新
            self.stdout.write('\n开始更新...')
            updated_count = need_update.update(is_staff=True)
            
            self.stdout.write('\n' + '=' * 60)
            self.stdout.write(self.style.SUCCESS(f'成功更新 {updated_count} 个用户'))
            self.stdout.write('=' * 60)
        else:
            self.stdout.write('\n' + '=' * 60)
            self.stdout.write(self.style.WARNING('试运行完成，未实际修改数据'))
            self.stdout.write(self.style.WARNING('移除 --dry-run 参数以实际更新'))
            self.stdout.write('=' * 60)

