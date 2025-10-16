"""
清理过期许可证管理命令
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from licenses.models import License, LicenseActivation, MachineBinding, LicenseUsageLog
from tenants.models import Tenant
import logging

logger = logging.getLogger('licenses.management')


class Command(BaseCommand):
    help = '清理过期和撤销的许可证及相关数据'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='清理多少天前过期的许可证 (默认: 30天)'
        )
        parser.add_argument(
            '--tenant',
            type=str,
            help='租户名称 (可选)'
        )
        parser.add_argument(
            '--include-revoked',
            action='store_true',
            help='同时清理撤销的许可证'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='模拟运行，不实际删除数据'
        )
        parser.add_argument(
            '--keep-audit-logs',
            action='store_true',
            help='保留审计日志不删除'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='批处理大小 (默认: 100)'
        )

    def handle(self, *args, **options):
        try:
            cutoff_date = timezone.now() - timezone.timedelta(days=options['days'])
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'开始清理 {cutoff_date.strftime("%Y-%m-%d %H:%M:%S")} 之前过期的许可证...'
                )
            )

            # 构建查询条件
            license_filter = {
                'is_deleted': False,
                'expires_at__lt': cutoff_date
            }

            if options.get('tenant'):
                try:
                    tenant = Tenant.objects.get(name=options['tenant'])
                    license_filter['tenant'] = tenant
                except Tenant.DoesNotExist:
                    raise CommandError(f"租户 '{options['tenant']}' 不存在")

            # 查找过期许可证
            expired_licenses_query = License.objects.filter(**license_filter)
            
            # 如果包含撤销的许可证
            if options.get('include_revoked'):
                revoked_filter = dict(license_filter)
                revoked_filter.pop('expires_at__lt')  # 撤销的许可证不需要过期条件
                revoked_filter['status'] = 'revoked'
                
                expired_licenses_query = expired_licenses_query.union(
                    License.objects.filter(**revoked_filter)
                )

            total_licenses = expired_licenses_query.count()
            
            if total_licenses == 0:
                self.stdout.write(self.style.SUCCESS('没有找到需要清理的许可证'))
                return

            self.stdout.write(f'找到 {total_licenses} 个需要清理的许可证')

            if options.get('dry_run'):
                self.stdout.write(self.style.WARNING('\n🧪 模拟运行模式，显示将要清理的数据:'))
                self._show_cleanup_preview(expired_licenses_query, options)
                return

            # 开始清理
            cleaned_stats = {
                'licenses': 0,
                'machine_bindings': 0,
                'activations': 0,
                'usage_logs': 0
            }

            batch_size = options['batch_size']
            
            # 分批处理
            for i in range(0, total_licenses, batch_size):
                batch_licenses = list(expired_licenses_query[i:i + batch_size])
                
                if not batch_licenses:
                    break

                with transaction.atomic():
                    license_ids = [license.id for license in batch_licenses]
                    
                    # 清理使用日志
                    if not options.get('keep_audit_logs'):
                        usage_logs_deleted = LicenseUsageLog.objects.filter(
                            license_id__in=license_ids
                        ).delete()[0]
                        cleaned_stats['usage_logs'] += usage_logs_deleted
                    
                    # 清理激活记录
                    activations_deleted = LicenseActivation.objects.filter(
                        license_id__in=license_ids
                    ).delete()[0]
                    cleaned_stats['activations'] += activations_deleted
                    
                    # 清理机器绑定
                    bindings_deleted = MachineBinding.objects.filter(
                        license_id__in=license_ids
                    ).delete()[0]
                    cleaned_stats['machine_bindings'] += bindings_deleted
                    
                    # 软删除许可证
                    licenses_updated = License.objects.filter(
                        id__in=license_ids
                    ).update(
                        is_deleted=True,
                        updated_at=timezone.now()
                    )
                    cleaned_stats['licenses'] += licenses_updated

                self.stdout.write(f'已处理 {min(i + batch_size, total_licenses)}/{total_licenses} 个许可证')

            # 输出清理结果
            self.stdout.write(f'\n📊 清理统计:')
            self.stdout.write(f'  🗑️ 许可证: {cleaned_stats["licenses"]} 个')
            self.stdout.write(f'  🔗 机器绑定: {cleaned_stats["machine_bindings"]} 个')
            self.stdout.write(f'  📋 激活记录: {cleaned_stats["activations"]} 个')
            
            if not options.get('keep_audit_logs'):
                self.stdout.write(f'  📝 使用日志: {cleaned_stats["usage_logs"]} 个')
            else:
                self.stdout.write(f'  📝 使用日志: 保留 (--keep-audit-logs)')

            self.stdout.write(
                self.style.SUCCESS(f'\n🎉 清理完成！总共处理了 {total_licenses} 个过期许可证')
            )

            # 记录操作日志
            logger.info(
                f'许可证清理完成: 处理了 {total_licenses} 个许可证, 统计: {cleaned_stats}'
            )

        except CommandError:
            raise
        except Exception as e:
            raise CommandError(f'Command execution failed: {str(e)}')

    def _show_cleanup_preview(self, licenses_query, options):
        """显示清理预览"""
        
        # 统计相关数据
        license_ids = list(licenses_query.values_list('id', flat=True))
        
        machine_bindings_count = MachineBinding.objects.filter(
            license_id__in=license_ids
        ).count()
        
        activations_count = LicenseActivation.objects.filter(
            license_id__in=license_ids
        ).count()
        
        usage_logs_count = LicenseUsageLog.objects.filter(
            license_id__in=license_ids
        ).count()

        self.stdout.write(f'  🗑️ 许可证: {len(license_ids)} 个')
        self.stdout.write(f'  🔗 机器绑定: {machine_bindings_count} 个')
        self.stdout.write(f'  📋 激活记录: {activations_count} 个')
        
        if not options.get('keep_audit_logs'):
            self.stdout.write(f'  📝 使用日志: {usage_logs_count} 个')
        else:
            self.stdout.write(f'  📝 使用日志: {usage_logs_count} 个 (将保留)')

        # 显示许可证样本
        sample_licenses = licenses_query[:5]
        self.stdout.write(f'\n📋 许可证样本 (前5个):')
        for license_obj in sample_licenses:
            self.stdout.write(
                f'  - {license_obj.license_key[:12]}... '
                f'({license_obj.product.name}, 过期: {license_obj.expires_at})'
            )
