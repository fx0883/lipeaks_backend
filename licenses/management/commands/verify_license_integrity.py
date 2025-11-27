"""
验证许可证完整性管理命令
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
# 此命令已废弃 - License模型不再有product字段
# 请使用新的验证方法
from licenses.models import License
from licenses.services.license_service import LicenseGenerationService
from tenants.models import Tenant
import logging

logger = logging.getLogger('licenses.management')


class Command(BaseCommand):
    help = '验证许可证密钥的完整性和有效性'

    def add_arguments(self, parser):
        parser.add_argument(
            '--license-key',
            type=str,
            help='验证特定许可证密钥'
        )
        parser.add_argument(
            '--product',
            type=str,
            help='软件产品名称 (验证该产品的所有许可证)'
        )
        parser.add_argument(
            '--tenant',
            type=str,
            help='租户名称 (可选)'
        )
        parser.add_argument(
            '--fix-corrupted',
            action='store_true',
            help='自动修复损坏的许可证 (将其标记为撤销)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='批处理大小 (默认: 100)'
        )

    def handle(self, *args, **options):
        raise CommandError(
            '此命令已废弃。License模型已重构，不再有product字段。'
            '\n请使用新的许可证验证API端点进行验证。'
        )
        # 以下代码已废弃
        if False:
            generation_service = LicenseGenerationService()
            
            # 获取要验证的许可证列表
            licenses = []
            
            if options.get('license_key'):
                # 验证特定许可证
                try:
                    license_obj = License.objects.select_related('product').get(
                        license_key=options['license_key'],
                        is_deleted=False
                    )
                    licenses = [license_obj]
                except License.DoesNotExist:
                    raise CommandError(f"许可证密钥 '{options['license_key']}' 不存在")
            
            elif options.get('product'):
                # 验证特定产品的所有许可证
                try:
                    if options.get('tenant'):
                        tenant = Tenant.objects.get(name=options['tenant'])
                        product = SoftwareProduct.objects.get(
                            name=options['product'],
                            tenant=tenant
                        )
                    else:
                        product = SoftwareProduct.objects.get(name=options['product'])
                    
                    licenses = list(
                        License.objects.select_related('product').filter(
                            product=product,
                            is_deleted=False
                        )
                    )
                except SoftwareProduct.DoesNotExist:
                    raise CommandError(f"软件产品 '{options['product']}' 不存在")
                except Tenant.DoesNotExist:
                    raise CommandError(f"租户 '{options['tenant']}' 不存在")
            
            else:
                # 验证所有许可证
                licenses_query = License.objects.select_related('product').filter(
                    is_deleted=False
                )
                
                if options.get('tenant'):
                    try:
                        tenant = Tenant.objects.get(name=options['tenant'])
                        licenses_query = licenses_query.filter(product__tenant=tenant)
                    except Tenant.DoesNotExist:
                        raise CommandError(f"租户 '{options['tenant']}' 不存在")
                
                licenses = list(licenses_query)

            if not licenses:
                self.stdout.write(self.style.WARNING('没有找到需要验证的许可证'))
                return

            self.stdout.write(
                self.style.SUCCESS(f'开始验证 {len(licenses)} 个许可证的完整性...')
            )

            # 验证统计
            stats = {
                'total': len(licenses),
                'valid': 0,
                'invalid': 0,
                'corrupted': 0,
                'fixed': 0
            }

            batch_size = options['batch_size']
            
            # 分批验证
            for i in range(0, len(licenses), batch_size):
                batch_licenses = licenses[i:i + batch_size]
                
                for license_obj in batch_licenses:
                    try:
                        # 验证许可证密钥
                        verification_result = generation_service.verify_license_key(
                            license_obj.license_key,
                            license_obj.product
                        )
                        
                        if verification_result['valid']:
                            stats['valid'] += 1
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f'✅ {license_obj.license_key[:12]}... - 有效'
                                )
                            )
                        else:
                            stats['invalid'] += 1
                            error_msg = verification_result.get('error', '未知错误')
                            
                            self.stdout.write(
                                self.style.ERROR(
                                    f'❌ {license_obj.license_key[:12]}... - 无效: {error_msg}'
                                )
                            )
                            
                            # 如果是签名验证失败，可能是密钥损坏
                            if 'signature verification failed' in error_msg.lower():
                                stats['corrupted'] += 1
                                
                                if options.get('fix_corrupted'):
                                    # 自动修复：标记为撤销
                                    license_obj.status = 'revoked'
                                    license_obj.notes = (
                                        license_obj.notes or ''
                                    ) + f'\n[AUTO-REVOKED] 签名验证失败，于 {timezone.now()} 自动撤销'
                                    license_obj.save(update_fields=['status', 'notes'])
                                    
                                    stats['fixed'] += 1
                                    self.stdout.write(
                                        self.style.WARNING(
                                            f'🔧 {license_obj.license_key[:12]}... - 已自动撤销'
                                        )
                                    )
                                    
                                    logger.warning(
                                        f'许可证自动撤销: {license_obj.license_key}, '
                                        f'原因: 签名验证失败'
                                    )

                    except Exception as e:
                        stats['invalid'] += 1
                        self.stdout.write(
                            self.style.ERROR(
                                f'❌ {license_obj.license_key[:12]}... - 验证异常: {str(e)}'
                            )
                        )

                # 显示进度
                processed = min(i + batch_size, len(licenses))
                self.stdout.write(f'已验证 {processed}/{len(licenses)} 个许可证')

            # 输出验证结果统计
            self.stdout.write(f'\n📊 验证结果统计:')
            self.stdout.write(f'  📋 总计: {stats["total"]} 个许可证')
            self.stdout.write(f'  ✅ 有效: {stats["valid"]} 个')
            self.stdout.write(f'  ❌ 无效: {stats["invalid"]} 个')
            
            if stats['corrupted'] > 0:
                self.stdout.write(f'  🔧 损坏: {stats["corrupted"]} 个')
                if options.get('fix_corrupted'):
                    self.stdout.write(f'  🔧 已修复: {stats["fixed"]} 个')
                else:
                    self.stdout.write(f'  💡 提示: 使用 --fix-corrupted 自动修复损坏的许可证')

            # 计算成功率
            success_rate = (stats['valid'] / stats['total']) * 100 if stats['total'] > 0 else 0
            
            if success_rate == 100:
                self.stdout.write(
                    self.style.SUCCESS(f'\n🎉 验证完成！所有许可证都是有效的 ({success_rate:.1f}%)')
                )
            elif success_rate >= 95:
                self.stdout.write(
                    self.style.SUCCESS(f'\n✅ 验证完成！成功率: {success_rate:.1f}%')
                )
            elif success_rate >= 80:
                self.stdout.write(
                    self.style.WARNING(f'\n⚠️ 验证完成！成功率: {success_rate:.1f}%，建议检查无效许可证')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'\n❌ 验证完成！成功率: {success_rate:.1f}%，存在严重问题')
                )

            # 记录操作日志
            logger.info(
                f'许可证完整性验证完成: 总计 {stats["total"]}, '
                f'有效 {stats["valid"]}, 无效 {stats["invalid"]}, '
                f'成功率 {success_rate:.1f}%'
            )

        except CommandError:
            raise
        except Exception as e:
            raise CommandError(f'Command execution failed: {str(e)}')
