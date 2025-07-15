"""
管理命令：修复租户配额
"""
import logging
from django.core.management.base import BaseCommand
from tenants.models import Tenant, TenantQuota

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '检查并修复所有缺少配额记录的租户'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force', 
            action='store_true',
            help='强制为所有租户重新创建配额，即使已有配额也会重置为默认值',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=== 开始检查租户配额 ==="))
        
        fixed_count = 0
        total_count = 0
        force = options.get('force', False)
        
        for tenant in Tenant.objects.all():
            total_count += 1
            try:
                if force:
                    # 强制模式：删除现有配额并重新创建
                    try:
                        tenant.quota.delete()
                        self.stdout.write(f"已删除租户 {tenant.name} 的现有配额")
                    except Tenant.quota.RelatedObjectDoesNotExist:
                        pass
                    
                    quota = TenantQuota.objects.create(
                        tenant=tenant,
                        max_users=10,
                        max_admins=2,
                        max_storage_mb=1024,
                        max_products=100
                    )
                    fixed_count += 1
                    self.stdout.write(self.style.SUCCESS(f"已为租户 {tenant.name} 创建新的默认配额"))
                else:
                    # 常规模式：仅检查并修复缺失的配额
                    try:
                        quota = tenant.quota
                        self.stdout.write(f"租户 {tenant.name} 的配额记录正常")
                    except Tenant.quota.RelatedObjectDoesNotExist:
                        quota = TenantQuota.objects.create(
                            tenant=tenant,
                            max_users=10,
                            max_admins=2,
                            max_storage_mb=1024,
                            max_products=100
                        )
                        fixed_count += 1
                        self.stdout.write(self.style.SUCCESS(f"已为租户 {tenant.name} 创建缺失的配额记录"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"处理租户 {tenant.name} 时出错: {str(e)}"))
        
        self.stdout.write(self.style.SUCCESS(f"=== 租户配额检查完成 ==="))
        self.stdout.write(self.style.SUCCESS(f"总租户数: {total_count}"))
        self.stdout.write(self.style.SUCCESS(f"修复的租户数: {fixed_count}"))
        
        if force:
            self.stdout.write(self.style.WARNING("注意: 在强制模式下运行，所有租户的配额已重置为默认值")) 