"""
许可证业务服务模块
提供许可证生成、验证、激活等核心业务功能
"""

import json
import base64
import base58
import time
import uuid
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from applications.models import Application
from licenses.models import (
    LicensePlan, License, MachineBinding, 
    LicenseActivation, SecurityAuditLog
)
from licenses.services.security_service import SecurityService
from licenses.services.fingerprint_service import MachineFingerprintService
import logging

logger = logging.getLogger('licenses.business')


class LicenseGenerationService:
    """许可证生成服务"""
    
    def __init__(self):
        self.security_service = SecurityService()
    
    def generate_license_key(
        self, 
        product: Application, 
        plan: LicensePlan, 
        customer_info: Dict[str, Any] = None
    ) -> str:
        """
        生成许可证密钥 - 使用纯UUID确保唯一性
        
        Args:
            product: 软件产品
            plan: 许可证方案
            customer_info: 客户信息
            
        Returns:
            str: 格式化的许可证密钥
        """
        try:
            # 使用UUID4生成完全唯一的许可证密钥
            license_uuid = str(uuid.uuid4()).upper()
            
            # 格式化为用户友好的格式 (XXXXX-XXXXX-XXXXX-XXXXX-XXXXX)
            # 移除连字符并取前25个字符，然后重新格式化
            clean_uuid = license_uuid.replace('-', '')[:25]
            formatted_key = '-'.join([
                clean_uuid[i:i+5] for i in range(0, min(len(clean_uuid), 25), 5)
            ])
            
            logger.info(f"许可证密钥生成成功: {formatted_key} (产品: {product.code}, 方案: {plan.code})")
            return formatted_key
            
        except Exception as e:
            logger.error(f"许可证密钥生成失败: {str(e)}")
            raise Exception(f"许可证生成失败: {str(e)}")
    
    def verify_license_key(self, license_key: str, product: Application) -> Dict[str, Any]:
        """
        验证许可证密钥有效性
        
        Args:
            license_key: 许可证密钥
            product: 软件产品
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        try:
            # 1. 清理格式并解码
            clean_key = license_key.replace('-', '').upper()
            
            try:
                decoded_payload = base64.b64decode(
                    base58.b58decode(clean_key)
                ).decode()
                license_payload = json.loads(decoded_payload)
            except Exception:
                return {'valid': False, 'error': 'Invalid key format'}
            
            # 2. 提取数据和签名
            if 'data' not in license_payload or 'signature' not in license_payload:
                return {'valid': False, 'error': 'Invalid payload structure'}
            
            raw_data = license_payload['data']
            signature = base64.b64decode(license_payload['signature'])
            
            # 3. 验证产品匹配
            if raw_data.get('product') != product.code:
                return {'valid': False, 'error': 'Product mismatch'}
            
            # 4. 验证签名
            data_str = json.dumps(raw_data, separators=(',', ':'), sort_keys=True)
            public_key_pem = product.public_key.encode()
            
            signature_valid = self.security_service.rsa_manager.verify_signature(
                public_key_pem, data_str, signature
            )
            
            if not signature_valid:
                return {'valid': False, 'error': 'Invalid signature'}
            
            # 5. 检查时间戳有效性
            license_timestamp = raw_data.get('timestamp', 0)
            current_timestamp = int(time.time())
            age_days = (current_timestamp - license_timestamp) / 86400
            
            if age_days > 3650:  # 10年最大有效期
                return {'valid': False, 'error': 'Key too old'}
            
            # 6. 返回验证结果
            return {
                'valid': True,
                'data': raw_data,
                'product_code': raw_data.get('product'),
                'plan_code': raw_data.get('plan'),
                'generated_at': datetime.fromtimestamp(license_timestamp),
                'age_days': age_days
            }
            
        except Exception as e:
            logger.error(f"许可证验证失败: {str(e)}")
            return {'valid': False, 'error': f'Verification error: {str(e)}'}
    
    def _get_product_private_key(self, product: Application) -> bytes:
        """
        获取产品私钥（实际实现中应从安全存储获取）
        
        Args:
            product: 软件产品
            
        Returns:
            bytes: 私钥PEM格式
        """
        # TODO: 实际实现中应该从HSM或密钥管理服务获取
        # 这里为演示目的，临时生成密钥对
        try:
            private_key_pem, public_key_pem = self.security_service.rsa_manager.generate_keypair()
            logger.warning("使用临时生成的密钥对，生产环境中应使用安全密钥管理")
            return private_key_pem
        except Exception as e:
            logger.error(f"私钥获取失败: {str(e)}")
            raise Exception("无法获取签名密钥")


class LicenseActivationService:
    """许可证激活服务"""
    
    def __init__(self):
        self.security_service = SecurityService()
        self.fingerprint_service = MachineFingerprintService()
    
    @transaction.atomic
    def activate_license(
        self,
        license_key: str,
        hardware_info: Dict[str, Any],
        client_info: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        激活许可证
        
        Args:
            license_key: 许可证密钥
            hardware_info: 硬件信息
            client_info: 客户端信息
            
        Returns:
            Dict[str, Any]: 激活结果
        """
        try:
            # 0. 获取租户对象（从client_info中提取）
            tenant_obj = None
            if client_info and client_info.get('tenant_info'):
                try:
                    from tenants.models import Tenant
                    tenant_obj = Tenant.objects.get(id=client_info['tenant_info'])
                    logger.info(f"激活许可证 - 使用租户: {tenant_obj.name} (ID: {tenant_obj.id})")
                except Tenant.DoesNotExist:
                    logger.warning(f"租户ID {client_info['tenant_info']} 不存在，使用许可证关联的租户")
                except Exception as e:
                    logger.warning(f"获取租户对象失败: {str(e)}，使用许可证关联的租户")
            
            # 1. 查找许可证记录
            try:
                license_hash = self.security_service.hash_manager.hash_data(license_key)
                license_obj = License.objects.get(license_hash=license_hash)
            except License.DoesNotExist:
                return {
                    'success': False,
                    'error': 'License not found or invalid',
                    'code': 'LICENSE_NOT_FOUND'
                }
            
            # 2. 检查许可证状态（必须先检查是否被撤销）
            if license_obj.status == 'revoked':
                logger.warning(f"尝试激活已撤销的许可证: {license_hash[:16]}...")
                return {
                    'success': False,
                    'error': 'License has been revoked',
                    'code': 'LICENSE_REVOKED'
                }
            
            # 检查许可证状态是否允许激活
            if license_obj.status not in ['generated', 'activated']:
                logger.warning(
                    f"许可证状态不允许激活: status={license_obj.status}, "
                    f"license_hash={license_hash[:16]}..."
                )
                return {
                    'success': False,
                    'error': f'License status is {license_obj.status}, cannot be activated',
                    'code': 'INVALID_LICENSE_STATUS'
                }
            
            if license_obj.expires_at < timezone.now():
                return {
                    'success': False,
                    'error': 'License has expired',
                    'code': 'LICENSE_EXPIRED'
                }
            
            # 3. 生成机器指纹
            machine_fingerprint = self.fingerprint_service.generate_fingerprint(
                hardware_info,
                salt=license_obj.product.code
            )
            
            machine_id = self.fingerprint_service.generate_machine_id(hardware_info)
            
            # 4. 检查现有绑定
            existing_binding = MachineBinding.objects.filter(
                license=license_obj,
                machine_fingerprint=machine_fingerprint
            ).first()
            
            if existing_binding:
                # 更新现有绑定
                existing_binding.last_seen_at = timezone.now()
                existing_binding.status = 'active'
                existing_binding.save()
                machine_binding = existing_binding
            else:
                # 检查激活数量限制
                active_bindings = MachineBinding.objects.filter(
                    license=license_obj,
                    status='active'
                ).count()
                
                if active_bindings >= license_obj.max_activations:
                    return {
                        'success': False,
                        'error': f'Maximum activations ({license_obj.max_activations}) reached',
                        'code': 'MAX_ACTIVATIONS_REACHED'
                    }
                
                # 创建新的机器绑定
                encrypted_hardware = self.security_service.aes_manager.encrypt_data(
                    hardware_info,
                    self.security_service.get_encryption_password('hardware')
                )
                
                machine_binding = MachineBinding.objects.create(
                    license=license_obj,
                    machine_id=machine_id,
                    machine_fingerprint=machine_fingerprint,
                    encrypted_hardware_info=json.dumps(encrypted_hardware),
                    os_info=hardware_info.get('system_info', {}),
                    hardware_summary=self.fingerprint_service.create_hardware_summary(hardware_info),
                    last_ip_address=client_info.get('ip_address') if client_info else None,
                    status='active',
                    tenant=tenant_obj or license_obj.tenant  # 使用解析的租户或许可证关联的租户
                )
            
            # 5. 生成激活码
            activation_code = self.security_service.token_manager.generate_activation_code(
                license_obj.product.code
            )
            
            # 6. 创建激活记录
            activation_record = LicenseActivation.objects.create(
                license=license_obj,
                machine_binding=machine_binding,
                activation_type='online',
                activation_code=activation_code,
                client_version=client_info.get('version', '') if client_info else '',
                user_agent=client_info.get('user_agent', '') if client_info else '',
                ip_address=client_info.get('ip_address') if client_info else None,
                result='success',
                expires_at=license_obj.expires_at,
                tenant=tenant_obj or license_obj.tenant  # 使用解析的租户或许可证关联的租户
            )
            
            # 7. 更新许可证状态
            license_obj.status = 'activated'
            license_obj.current_activations = MachineBinding.objects.filter(
                license=license_obj,
                status='active'
            ).count()
            license_obj.last_verified_at = timezone.now()
            license_obj.save()
            
            # 8. 记录安全日志
            SecurityAuditLog.objects.create(
                event_type='license_activated',
                severity='LOW',
                ip_address=client_info.get('ip_address') if client_info else None,
                details={
                    'license_id': license_obj.id,
                    'machine_id': machine_id,
                    'activation_code': activation_code,
                    'product': license_obj.product.code
                }
            )
            
            logger.info(f"许可证激活成功: {license_obj.id} -> {machine_id}")
            
            return {
                'success': True,
                'activation_code': activation_code,
                'machine_id': machine_id,
                'expires_at': license_obj.expires_at.isoformat(),
                'features': license_obj.plan.features,
                'default_max_activations': license_obj.plan.default_max_activations,
                'current_activations': license_obj.current_activations
            }
            
        except Exception as e:
            logger.error(f"许可证激活失败: {str(e)}")
            return {
                'success': False,
                'error': f'Activation failed: {str(e)}',
                'code': 'ACTIVATION_ERROR'
            }
    
    def verify_activation(
        self,
        activation_code: str,
        machine_fingerprint: str
    ) -> Dict[str, Any]:
        """
        验证激活状态
        
        Args:
            activation_code: 激活码
            machine_fingerprint: 机器指纹
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        try:
            # 查找激活记录
            activation = LicenseActivation.objects.filter(
                activation_code=activation_code,
                result='success'
            ).select_related('license', 'machine_binding').first()
            
            if not activation:
                return {
                    'valid': False,
                    'error': 'Activation not found',
                    'code': 'ACTIVATION_NOT_FOUND'
                }
            
            # ✅ 检查机器绑定状态（防御性检查）
            if activation.machine_binding.status != 'active':
                logger.warning(
                    f"激活验证失败: 设备已解绑 - activation_code: {activation_code}, "
                    f"machine_binding status: {activation.machine_binding.status}"
                )
                return {
                    'valid': False,
                    'error': 'Device has been unbound',
                    'code': 'DEVICE_UNBOUND',
                    'binding_status': activation.machine_binding.status
                }
            
            # 验证机器指纹（已禁用）
            # TODO: 机器指纹验证已禁用，后续根据需要重新启用
            # fingerprint_match = self.fingerprint_service.verify_fingerprint_match(
            #     activation.machine_binding.machine_fingerprint,
            #     machine_fingerprint
            # )
            # 
            # if not fingerprint_match['is_match']:
            #     return {
            #         'valid': False,
            #         'error': 'Machine fingerprint mismatch',
            #         'code': 'FINGERPRINT_MISMATCH',
            #         'similarity': fingerprint_match['similarity']
            #     }
            
            # 记录指纹信息（但不验证）
            fingerprint_preview = machine_fingerprint[:8] + '...' if machine_fingerprint else 'NOT_PROVIDED'
            logger.info(f"验证请求 - 激活码: {activation_code}, 指纹: {fingerprint_preview}")
            
            # 检查许可证状态
            license_obj = activation.license
            if license_obj.status != 'activated':
                return {
                    'valid': False,
                    'error': f'License status: {license_obj.status}',
                    'code': 'LICENSE_INACTIVE'
                }
            
            # 检查过期时间
            if activation.expires_at and activation.expires_at < timezone.now():
                return {
                    'valid': False,
                    'error': 'Activation has expired',
                    'code': 'ACTIVATION_EXPIRED'
                }
            
            # 更新最后验证时间
            license_obj.last_verified_at = timezone.now()
            license_obj.save()
            
            return {
                'valid': True,
                'license_id': license_obj.id,
                'product': license_obj.product.code,
                'plan': license_obj.plan.code,
                'expires_at': activation.expires_at.isoformat() if activation.expires_at else None,
                'features': license_obj.plan.features,
                'last_verified': license_obj.last_verified_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"激活验证失败: {str(e)}")
            return {
                'valid': False,
                'error': f'Verification failed: {str(e)}',
                'code': 'VERIFICATION_ERROR'
            }
    
    @transaction.atomic
    def unbind_license(
        self,
        activation_code: str,
        license_key: str,
        machine_fingerprint: str,
        hardware_info: Dict[str, Any] = None,
        reason: str = "用户主动解绑",
        client_info: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        解绑许可证
        
        Args:
            activation_code: 激活码
            license_key: 许可证密钥
            machine_fingerprint: 机器指纹
            hardware_info: 硬件信息（可选）
            reason: 解绑原因
            client_info: 客户端信息（IP、User-Agent等）
            
        Returns:
            Dict[str, Any]: 解绑结果
        """
        try:
            # 1. 查找激活记录
            activation = LicenseActivation.objects.filter(
                activation_code=activation_code,
                result='success'
            ).select_related('license', 'machine_binding').first()
            
            if not activation:
                return {
                    'success': False,
                    'error': 'Activation record not found',
                    'code': 'ACTIVATION_NOT_FOUND'
                }
            
            # 2. 验证许可证密钥匹配
            license_obj = activation.license
            if license_obj.license_key != license_key:
                logger.warning(f"解绑请求许可证密钥不匹配: {activation_code}")
                return {
                    'success': False,
                    'error': 'License key mismatch',
                    'code': 'LICENSE_KEY_MISMATCH'
                }
            
            # 3. 验证机器指纹匹配（暂时禁用）
            # TODO: 指纹码验证暂时不启用，后续根据需要重新开启
            # fingerprint_match = self.fingerprint_service.verify_fingerprint_match(
            #     activation.machine_binding.machine_fingerprint,
            #     machine_fingerprint,
            #     similarity_threshold=0.8  # 稍微宽松一些，防止硬件微小变化导致无法解绑
            # )
            # 
            # if not fingerprint_match['is_match']:
            #     logger.warning(f"解绑请求机器指纹不匹配: {activation_code}, 相似度: {fingerprint_match['similarity']}")
            #     return {
            #         'success': False,
            #         'error': 'Machine fingerprint mismatch',
            #         'code': 'FINGERPRINT_MISMATCH',
            #         'similarity': fingerprint_match['similarity']
            #     }
            
            # 记录指纹信息用于日志（但不进行验证）
            fingerprint_preview = machine_fingerprint[:8] + '...' if machine_fingerprint else 'NOT_PROVIDED'
            logger.info(f"解绑请求 - 激活码: {activation_code}, 指纹: {fingerprint_preview}")
            
            # 4. 检查机器绑定状态
            machine_binding = activation.machine_binding
            if machine_binding.status != 'active':
                return {
                    'success': False,
                    'error': f'Machine binding is not active (current: {machine_binding.status})',
                    'code': 'BINDING_NOT_ACTIVE'
                }
            
            # 5. 执行解绑操作
            # 更新机器绑定状态为非活跃
            machine_binding.status = 'inactive'
            machine_binding.save()
            
            # ✅ 删除或作废激活记录，防止使用旧的 activation_code 继续验证
            # 方案1: 删除激活记录（推荐）
            activation.delete()
            logger.info(f"已删除激活记录: {activation_code}")
            
            # 方案2: 或者将激活结果标记为失败（保留记录用于审计）
            # activation.result = 'failed'
            # activation.error_message = f'设备已解绑: {reason}'
            # activation.save()
            
            # 更新许可证的current激活数
            active_bindings_count = MachineBinding.objects.filter(
                license=license_obj,
                status='active'
            ).count()
            
            license_obj.current_activations = active_bindings_count
            license_obj.save()
            
            # 6. 记录安全审计日志
            SecurityAuditLog.objects.create(
                event_type='license_deactivated',
                severity='LOW',
                tenant_id=license_obj.tenant_id,
                ip_address=client_info.get('ip_address') if client_info else None,
                user_agent=client_info.get('user_agent', '') if client_info else '',
                details={
                    'license_id': license_obj.id,
                    'activation_code': activation_code,
                    'machine_id': machine_binding.machine_id,
                    'machine_fingerprint': fingerprint_preview,  # 部分指纹或NOT_PROVIDED
                    'reason': reason,
                    'product': license_obj.product.code,
                    'fingerprint_verification': 'SKIPPED',  # 指纹验证已禁用
                    'remaining_activations': active_bindings_count
                }
            )
            
            logger.info(f"许可证解绑成功: {license_obj.id} -> {machine_binding.machine_id}, 原因: {reason}")
            
            return {
                'success': True,
                'message': 'License unbound successfully',
                'data': {
                    'license_id': license_obj.id,
                    'machine_id': machine_binding.machine_id,
                    'unbound_at': timezone.now().isoformat(),
                    'remaining_activations': active_bindings_count,
                    'max_activations': license_obj.max_activations,
                    'reason': reason
                }
            }
            
        except Exception as e:
            logger.error(f"许可证解绑失败: {str(e)}")
            return {
                'success': False,
                'error': f'Unbind failed: {str(e)}',
                'code': 'UNBIND_ERROR'
            }


class LicenseManagementService:
    """许可证管理服务"""
    
    @transaction.atomic
    def create_license(
        self,
        application_id: int,
        plan_id: int,
        tenant_id: int,
        customer_info: Dict[str, Any],
        expires_at: datetime = None,
        max_activations: int = None
    ) -> License:
        """
        创建新许可证
        
        Args:
            application_id: 应用ID
            plan_id: 方案ID
            tenant_id: 租户ID
            customer_info: 客户信息
            expires_at: 过期时间
            max_activations: 最大激活数
            
        Returns:
            License: 许可证对象
        """
        try:
            # 获取应用和方案
            application = Application.objects.get(id=application_id)
            plan = LicensePlan.objects.get(id=plan_id, application=application)
            
            # 生成许可证密钥
            generation_service = LicenseGenerationService()
            license_key = generation_service.generate_license_key(
                application, plan, customer_info
            )
            
            # 计算过期时间
            if expires_at is None:
                expires_at = timezone.now() + timedelta(days=plan.default_validity_days)
            
            # 确定最大激活数
            if max_activations is None:
                max_activations = plan.default_max_activations
            
            # 加密客户信息
            security_service = SecurityService()
            encrypted_customer_info = security_service.aes_manager.encrypt_data(
                customer_info,
                security_service.get_encryption_password('customer')
            )
            
            # 创建许可证记录
            license_obj = License.objects.create(
                application=application,
                plan=plan,
                tenant_id=tenant_id,
                license_key=license_key,
                customer_name=customer_info.get('name', ''),
                customer_email=customer_info.get('email', ''),
                encrypted_customer_info=json.dumps(encrypted_customer_info),
                max_activations=max_activations,
                expires_at=expires_at,
                status='generated',
                metadata={'creation_source': 'api'}
            )
            
            # 记录安全日志
            SecurityAuditLog.objects.create(
                event_type='license_generated',
                severity='LOW',
                tenant_id=tenant_id,
                details={
                    'license_id': license_obj.id,
                    'application': application.code,
                    'plan': plan.code,
                    'customer_name': customer_info.get('name', '')
                }
            )
            
            logger.info(f"许可证创建成功: {license_obj.id}")
            return license_obj
            
        except Exception as e:
            logger.error(f"许可证创建失败: {str(e)}")
            raise Exception(f"许可证创建失败: {str(e)}")
    
    @transaction.atomic
    def revoke_license(
        self,
        license_id: int,
        reason: str = '',
        user_id: int = None
    ) -> bool:
        """
        撤销许可证
        
        Args:
            license_id: 许可证ID
            reason: 撤销原因
            user_id: 操作用户ID
            
        Returns:
            bool: 操作结果
        """
        try:
            license_obj = License.objects.get(id=license_id)
            
            # 更新许可证状态
            license_obj.status = 'revoked'
            license_obj.notes = f"撤销原因: {reason}"
            license_obj.save()
            
            # ✅ 删除所有激活记录，防止使用旧的 activation_code 继续验证
            deleted_activations = LicenseActivation.objects.filter(
                license=license_obj,
                result='success'
            ).delete()
            
            activation_count = deleted_activations[0] if deleted_activations else 0
            logger.info(
                f"撤销许可证 {license_id}：删除了 {activation_count} 条激活记录"
            )
            
            # 禁用所有机器绑定
            MachineBinding.objects.filter(license=license_obj).update(
                status='blocked'
            )
            
            # 记录安全日志
            SecurityAuditLog.objects.create(
                event_type='license_revoked',
                severity='MEDIUM',
                user_id=user_id,
                tenant_id=license_obj.tenant_id,
                details={
                    'license_id': license_obj.id,
                    'reason': reason,
                    'product': license_obj.product.code,
                    'deleted_activation_records': activation_count  # 记录删除的激活记录数
                }
            )
            
            logger.warning(f"许可证已撤销: {license_id}, 原因: {reason}")
            return True
            
        except License.DoesNotExist:
            logger.error(f"许可证不存在: {license_id}")
            return False
        except Exception as e:
            logger.error(f"许可证撤销失败: {str(e)}")
            return False
    
    def get_license_usage_stats(self, license_id: int) -> Dict[str, Any]:
        """
        获取许可证使用统计
        
        Args:
            license_id: 许可证ID
            
        Returns:
            Dict[str, Any]: 使用统计
        """
        try:
            license_obj = License.objects.get(id=license_id)
            
            # 机器绑定统计
            bindings = MachineBinding.objects.filter(license=license_obj)
            active_bindings = bindings.filter(status='active')
            
            # 激活记录统计
            activations = LicenseActivation.objects.filter(license=license_obj)
            successful_activations = activations.filter(result='success')
            
            # 使用日志统计（最近30天）
            thirty_days_ago = timezone.now() - timedelta(days=30)
            recent_usage = license_obj.usage_logs.filter(
                timestamp__gte=thirty_days_ago
            ).count()
            
            return {
                'license_id': license_id,
                'status': license_obj.status,
                'created_at': license_obj.created_at.isoformat(),
                'expires_at': license_obj.expires_at.isoformat(),
                'machine_bindings': {
                    'total': bindings.count(),
                    'active': active_bindings.count(),
                    'max_allowed': license_obj.max_activations
                },
                'activations': {
                    'total_attempts': activations.count(),
                    'successful': successful_activations.count(),
                    'last_activation': successful_activations.order_by('-activated_at').first().activated_at.isoformat() if successful_activations.exists() else None
                },
                'usage': {
                    'recent_events': recent_usage,
                    'last_verified': license_obj.last_verified_at.isoformat() if license_obj.last_verified_at else None
                }
            }
            
        except License.DoesNotExist:
            return {'error': 'License not found'}
        except Exception as e:
            logger.error(f"许可证统计获取失败: {str(e)}")
            return {'error': str(e)}
