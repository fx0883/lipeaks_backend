"""
生成许可证密钥管理命令
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta
# 此命令已废弃 - SoftwareProduct已删除
from applications.models import Application
from licenses.models import LicensePlan, License
from licenses.services.license_service import LicenseGenerationService
from tenants.models import Tenant
import json


class Command(BaseCommand):
    help = '批量生成许可证密钥'

    def add_arguments(self, parser):
        parser.add_argument(
            '--product',
            type=str,
            required=True,
            help='软件产品名称'
        )
        parser.add_argument(
            '--plan',
            type=str,
            required=True,
            help='许可证方案名称'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=1,
            help='生成数量 (默认: 1)'
        )
        parser.add_argument(
            '--tenant',
            type=str,
            help='租户名称 (可选)'
        )
        parser.add_argument(
            '--expires-days',
            type=int,
            help='有效期天数 (可选，覆盖方案默认值)'
        )
        parser.add_argument(
            '--issued-to-name',
            type=str,
            help='颁发给的用户名'
        )
        parser.add_argument(
            '--issued-to-email',
            type=str,
            help='颁发给的用户邮箱'
        )
        parser.add_argument(
            '--issued-to-company',
            type=str,
            help='颁发给的公司'
        )
        parser.add_argument(
            '--max-activations',
            type=int,
            help='最大激活次数 (可选，覆盖方案默认值)'
        )
        parser.add_argument(
            '--notes',
            type=str,
            help='备注信息'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='输出文件路径 (JSON格式)'
        )

    def handle(self, *args, **options):
        raise CommandError(
            '此命令已废弃。SoftwareProduct已删除，请使用License API端点生成许可证。'
            '\n建议使用 POST /api/v1/licenses/licenses/ API进行许可证创建。'
        )
        # 以下代码已废弃
        if False:
            # 查找软件产品
            try:
                if options['tenant']:
                    tenant = Tenant.objects.get(name=options['tenant'])
                    product = Application.objects.get(
                        name=options['product'],
                        tenant=tenant
                    )
                else:
                    product = Application.objects.get(name=options['product'])
            except Application.DoesNotExist:
                raise CommandError(f"软件产品 '{options['product']}' 不存在")
            except Tenant.DoesNotExist:
                raise CommandError(f"租户 '{options['tenant']}' 不存在")

            # 查找许可证方案
            try:
                plan = LicensePlan.objects.get(
                    name=options['plan'],
                    product=product
                )
            except LicensePlan.DoesNotExist:
                raise CommandError(f"许可证方案 '{options['plan']}' 不存在")

            # 检查方案是否激活
            if not plan.is_active:
                raise CommandError(f"许可证方案 '{options['plan']}' 未激活")

            # 计算过期时间
            expires_at = None
            if options.get('expires_days'):
                expires_at = timezone.now() + timedelta(days=options['expires_days'])
            elif plan.duration_days:
                expires_at = timezone.now() + timedelta(days=plan.duration_days)

            # 初始化许可证生成服务
            generation_service = LicenseGenerationService()

            # 批量生成许可证
            generated_licenses = []
            
            self.stdout.write(
                self.style.SUCCESS(f'开始生成 {options["count"]} 个许可证密钥...')
            )

            for i in range(options['count']):
                try:
                    # 生成许可证
                    result = generation_service.generate_license(
                        product=product,
                        plan=plan,
                        issued_to_name=options.get('issued_to_name'),
                        issued_to_email=options.get('issued_to_email'),
                        issued_to_company=options.get('issued_to_company'),
                        expires_at=expires_at,
                        max_activations=options.get('max_activations'),
                        notes=options.get('notes')
                    )

                    if result['success']:
                        license_info = {
                            'license_key': result['license_key'],
                            'product': product.name,
                            'plan': plan.name,
                            'issued_at': result['license'].issued_at.isoformat(),
                            'expires_at': result['license'].expires_at.isoformat() if result['license'].expires_at else None,
                            'max_activations': result['license'].max_activations,
                            'issued_to_name': result['license'].issued_to_name,
                            'issued_to_email': result['license'].issued_to_email,
                            'issued_to_company': result['license'].issued_to_company
                        }
                        generated_licenses.append(license_info)

                        self.stdout.write(
                            self.style.SUCCESS(f'✅ 许可证 {i+1}: {result["license_key"]}')
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(f'❌ 许可证 {i+1} 生成失败: {result.get("error", "未知错误")}')
                        )

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'❌ 许可证 {i+1} 生成异常: {str(e)}')
                    )

            # 输出结果
            if generated_licenses:
                self.stdout.write(
                    self.style.SUCCESS(f'\n🎉 成功生成 {len(generated_licenses)} 个许可证密钥')
                )

                # 保存到文件
                if options.get('output'):
                    try:
                        with open(options['output'], 'w', encoding='utf-8') as f:
                            json.dump({
                                'generated_at': timezone.now().isoformat(),
                                'product': product.name,
                                'plan': plan.name,
                                'count': len(generated_licenses),
                                'licenses': generated_licenses
                            }, f, indent=2, ensure_ascii=False)
                        
                        self.stdout.write(
                            self.style.SUCCESS(f'📄 许可证信息已保存到: {options["output"]}')
                        )
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f'⚠️ 保存文件失败: {str(e)}')
                        )
                else:
                    # 显示许可证列表
                    self.stdout.write('\n📋 生成的许可证列表:')
                    for i, license_info in enumerate(generated_licenses, 1):
                        self.stdout.write(f'{i}. {license_info["license_key"]}')
            else:
                self.stdout.write(
                    self.style.ERROR('❌ 没有成功生成任何许可证')
                )

        except CommandError:
            raise
        except Exception as e:
            raise CommandError(f'Command execution failed: {str(e)}')
