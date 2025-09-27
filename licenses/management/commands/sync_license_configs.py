"""
同步许可证配置管理命令
定期检查并同步过时的许可证配置
"""

from django.core.management.base import BaseCommand
from django.db.models import F
from licenses.models import License
import logging

logger = logging.getLogger('licenses.management')


class Command(BaseCommand):
    help = '同步过时的许可证配置（与计划不一致的许可证）'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='模拟运行，不实际更新数据',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制更新所有许可证，无论是否过时',
        )
        parser.add_argument(
            '--status',
            choices=['generated', 'activated', 'suspended'],
            nargs='+',
            default=['generated', 'activated'],
            help='指定要同步的许可证状态',
        )

    def handle(self, *args, **options):
        """执行同步任务"""
        dry_run = options['dry_run']
        force = options['force']
        status_list = options['status']
        
        self.stdout.write(
            self.style.SUCCESS(f'开始同步许可证配置...')
        )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('模拟运行模式，不会实际更新数据')
            )
        
        # 查找需要同步的许可证
        if force:
            # 强制模式：所有指定状态的许可证
            outdated_licenses = License.objects.filter(
                status__in=status_list,
                is_deleted=False
            ).select_related('plan', 'product')
            
            self.stdout.write(f'强制模式：找到 {outdated_licenses.count()} 个许可证')
        else:
            # 正常模式：只处理过时的许可证
            outdated_licenses = License.objects.filter(
                status__in=status_list,
                is_deleted=False
            ).select_related('plan', 'product')
            
            # 过滤出真正过时的许可证
            outdated_licenses = [
                license_obj for license_obj in outdated_licenses
                if license_obj.is_outdated_config()
            ]
            
            self.stdout.write(f'找到 {len(outdated_licenses)} 个过时配置的许可证')
        
        if not outdated_licenses:
            self.stdout.write(
                self.style.SUCCESS('没有需要同步的许可证')
            )
            return
        
        # 执行同步
        updated_count = 0
        error_count = 0
        
        for license_obj in outdated_licenses:
            try:
                if dry_run:
                    # 模拟运行：显示将要执行的操作
                    self.stdout.write(
                        f'[模拟] 许可证 {license_obj.id}: '
                        f'max_activations {license_obj.max_activations} -> {license_obj.plan.default_max_activations}'
                    )
                    updated_count += 1
                else:
                    # 实际执行同步
                    if license_obj.update_from_plan(force=force):
                        self.stdout.write(
                            f'✓ 许可证 {license_obj.id} 配置已同步'
                        )
                        updated_count += 1
                    else:
                        self.stdout.write(
                            f'- 许可证 {license_obj.id} 配置无需更新'
                        )
                        
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'✗ 许可证 {license_obj.id} 同步失败: {str(e)}'
                    )
                )
                logger.error(f'许可证 {license_obj.id} 同步失败: {str(e)}')
        
        # 输出统计结果
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'模拟运行完成：将更新 {updated_count} 个许可证'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'同步完成：成功更新 {updated_count} 个许可证'
                )
            )
            
            if error_count > 0:
                self.stdout.write(
                    self.style.ERROR(f'失败 {error_count} 个许可证')
                )
        
        # 记录到日志
        if not dry_run and updated_count > 0:
            logger.info(f'许可证配置同步完成：更新 {updated_count} 个，失败 {error_count} 个')
    
    def get_outdated_licenses_query(self, status_list):
        """
        获取过时许可证的查询
        
        Args:
            status_list: 许可证状态列表
            
        Returns:
            QuerySet: 过时许可证查询集
        """
        return License.objects.filter(
            status__in=status_list,
            is_deleted=False
        ).annotate(
            plan_updated_at=F('plan__updated_at')
        ).filter(
            # 许可证的更新时间早于计划的更新时间
            updated_at__lt=F('plan_updated_at')
        ).select_related('plan', 'product')
