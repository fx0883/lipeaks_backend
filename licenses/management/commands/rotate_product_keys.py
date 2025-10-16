"""
轮换软件产品密钥对管理命令
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from licenses.models import SoftwareProduct
from licenses.services.security_service import SecurityService
from tenants.models import Tenant
import logging

logger = logging.getLogger('licenses.management')


class Command(BaseCommand):
    help = '轮换软件产品的RSA密钥对'

    def add_arguments(self, parser):
        parser.add_argument(
            '--product',
            type=str,
            help='软件产品名称 (如果不指定则轮换所有产品)'
        )
        parser.add_argument(
            '--tenant',
            type=str,
            help='租户名称 (可选)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='强制轮换，即使存在活跃许可证'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='模拟运行，不实际执行轮换'
        )

    def handle(self, *args, **options):
        try:
            security_service = SecurityService()
            
            # 获取要轮换的产品列表
            products = []
            
            if options.get('product'):
                # 轮换特定产品
                try:
                    if options.get('tenant'):
                        tenant = Tenant.objects.get(name=options['tenant'])
                        product = SoftwareProduct.objects.get(
                            name=options['product'],
                            tenant=tenant
                        )
                    else:
                        product = SoftwareProduct.objects.get(name=options['product'])
                    products = [product]
                except SoftwareProduct.DoesNotExist:
                    raise CommandError(f"软件产品 '{options['product']}' 不存在")
                except Tenant.DoesNotExist:
                    raise CommandError(f"租户 '{options['tenant']}' 不存在")
            else:
                # 轮换所有产品
                products_query = SoftwareProduct.objects.filter(is_deleted=False)
                if options.get('tenant'):
                    try:
                        tenant = Tenant.objects.get(name=options['tenant'])
                        products_query = products_query.filter(tenant=tenant)
                    except Tenant.DoesNotExist:
                        raise CommandError(f"租户 '{options['tenant']}' 不存在")
                
                products = list(products_query)

            if not products:
                self.stdout.write(self.style.WARNING('没有找到需要轮换的产品'))
                return

            self.stdout.write(
                self.style.SUCCESS(f'准备轮换 {len(products)} 个产品的密钥对...')
            )

            rotated_count = 0
            skipped_count = 0

            for product in products:
                try:
                    self.stdout.write(f'\n🔄 处理产品: {product.name} (租户: {product.tenant})')
                    
                    # 检查是否有活跃的许可证
                    active_licenses = product.licenses.filter(
                        status='activated',
                        is_deleted=False
                    ).count()
                    
                    if active_licenses > 0 and not options.get('force'):
                        self.stdout.write(
                            self.style.WARNING(
                                f'⚠️ 跳过: 产品有 {active_licenses} 个活跃许可证，使用 --force 强制轮换'
                            )
                        )
                        skipped_count += 1
                        continue

                    if options.get('dry_run'):
                        self.stdout.write(
                            self.style.SUCCESS(f'🧪 模拟: 将为产品 {product.name} 生成新密钥对')
                        )
                        rotated_count += 1
                        continue

                    # 生成新的密钥对
                    keypair = security_service.key_manager.generate_keypair()
                    
                    # 备份旧密钥信息
                    old_fingerprint = product.public_key_fingerprint
                    
                    # 更新产品密钥
                    product.public_key = keypair['public_key']
                    product.private_key = keypair['private_key']  # 在实际生产中应该安全存储
                    product.public_key_fingerprint = keypair['public_key_fingerprint']
                    product.save(update_fields=[
                        'public_key', 'private_key', 'public_key_fingerprint'
                    ])
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ 成功轮换密钥对\n'
                            f'   旧指纹: {old_fingerprint}\n'
                            f'   新指纹: {product.public_key_fingerprint}'
                        )
                    )
                    
                    # 记录操作日志
                    logger.info(
                        f'产品密钥轮换成功: {product.name}, '
                        f'旧指纹: {old_fingerprint}, 新指纹: {product.public_key_fingerprint}'
                    )
                    
                    rotated_count += 1

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'❌ 产品 {product.name} 密钥轮换失败: {str(e)}')
                    )
                    logger.error(f'产品密钥轮换失败: {product.name}, 错误: {str(e)}')

            # 输出总结
            self.stdout.write(f'\n📊 轮换总结:')
            self.stdout.write(f'  ✅ 成功轮换: {rotated_count} 个产品')
            if skipped_count > 0:
                self.stdout.write(f'  ⚠️ 跳过轮换: {skipped_count} 个产品')
            
            if options.get('dry_run'):
                self.stdout.write(self.style.WARNING('\n🧪 这是模拟运行，没有实际更改任何数据'))
            elif rotated_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'\n🎉 密钥轮换完成！受影响的许可证需要重新签发。')
                )

        except CommandError:
            raise
        except Exception as e:
            raise CommandError(f'Command execution failed: {str(e)}')
