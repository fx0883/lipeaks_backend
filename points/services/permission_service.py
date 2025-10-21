"""
租户权限计算服务

提供基于积分等级和VIP标签的多层权限计算
"""
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta

from django.utils import timezone
from django.core.cache import cache

from ..models import (
    TenantUserProfile,
    UserLevel,
    UserTypeTag,
    TenantUserTypeTag
)

logger = logging.getLogger(__name__)


class TenantAwarePermissionService:
    """
    租户感知权限计算服务
    
    负责计算用户在特定租户下的有效权限，整合：
    1. 基础权限
    2. 积分等级权限增强
    3. VIP标签权限增强
    4. 租户特定配置
    """
    
    # 基础权限模板
    BASE_PERMISSIONS = {
        # 许可证相关权限
        'license': {
            'max_licenses': 1,
            'max_devices_per_license': 1,
            'can_share_license': False,
            'license_duration_multiplier': 1.0,
            'can_backup_license': False,
            'can_export_license': False,
        },
        
        # 功能权限
        'features': {
            'api_access': True,
            'bulk_operations': False,
            'advanced_analytics': False,
            'priority_support': False,
            'custom_integration': False,
            'white_label': False,
        },
        
        # 资源配额
        'quotas': {
            'storage_mb': 100,
            'bandwidth_mb_monthly': 1000,
            'api_calls_daily': 1000,
            'export_count_daily': 5,
            'support_tickets_monthly': 2,
        },
        
        # 系统限制
        'limits': {
            'session_timeout_minutes': 30,
            'concurrent_sessions': 1,
            'file_upload_mb': 10,
            'batch_size_limit': 100,
        }
    }
    
    def __init__(self):
        self.logger = logger
        self.cache_timeout = 300  # 5分钟缓存
    
    def calculate_user_permissions(
        self,
        member: Any,
        tenant: Any,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        计算用户的有效权限
        
        Args:
            member: Member对象
            tenant: Tenant对象
            force_refresh: 是否强制刷新缓存
            
        Returns:
            Dict: 有效权限配置
        """
        cache_key = f"user_permissions:{tenant.id}:{member.id}"
        
        if not force_refresh:
            cached_permissions = cache.get(cache_key)
            if cached_permissions:
                return cached_permissions
        
        # 获取用户档案
        tenant_user_profile = self._get_or_create_profile(member, tenant)
        
        # 开始权限计算
        effective_permissions = self._deep_copy_permissions(self.BASE_PERMISSIONS)
        
        # 1. 应用积分等级权限增强
        effective_permissions = self._apply_level_permissions(
            effective_permissions,
            tenant_user_profile
        )
        
        # 2. 应用VIP标签权限增强
        effective_permissions = self._apply_tag_permissions(
            effective_permissions,
            tenant_user_profile
        )
        
        # 3. 应用租户特定配置
        effective_permissions = self._apply_tenant_configurations(
            effective_permissions,
            tenant
        )
        
        # 4. 添加元数据
        effective_permissions['_metadata'] = {
            'calculated_at': timezone.now().isoformat(),
            'user_level': {
                'name': tenant_user_profile.current_level.level_name if tenant_user_profile.current_level else '无等级',
                'order': tenant_user_profile.current_level.level_order if tenant_user_profile.current_level else 0
            },
            'active_tags': self._get_active_tags_summary(tenant_user_profile),
            'total_points': tenant_user_profile.total_points,
            'points_multiplier': float(tenant_user_profile.points_multiplier)
        }
        
        # 缓存结果
        cache.set(cache_key, effective_permissions, self.cache_timeout)
        
        self.logger.info(
            f"权限计算完成: {member.username}@{tenant.name} "
            f"等级: {effective_permissions['_metadata']['user_level']['name']} "
            f"活跃标签: {len(effective_permissions['_metadata']['active_tags'])}"
        )
        
        return effective_permissions
    
    def check_permission(
        self,
        member: Any,
        tenant: Any,
        permission_path: str,
        required_value: Any = True
    ) -> bool:
        """
        检查用户是否具有特定权限
        
        Args:
            member: Member对象
            tenant: Tenant对象
            permission_path: 权限路径，如 'features.api_access'
            required_value: 需要的权限值
            
        Returns:
            bool: 是否具有权限
        """
        permissions = self.calculate_user_permissions(member, tenant)
        
        # 解析权限路径
        current = permissions
        for part in permission_path.split('.'):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return False
        
        # 比较权限值
        if isinstance(required_value, (int, float)):
            # 数值类型，检查是否满足最小要求
            return isinstance(current, (int, float)) and current >= required_value
        elif isinstance(required_value, bool):
            # 布尔类型，直接比较
            return bool(current) == required_value
        else:
            # 其他类型，直接比较
            return current == required_value
    
    def get_quota_value(
        self,
        member: Any,
        tenant: Any,
        quota_name: str
    ) -> Optional[Union[int, float]]:
        """
        获取用户的配额值
        
        Args:
            member: Member对象
            tenant: Tenant对象
            quota_name: 配额名称
            
        Returns:
            配额值
        """
        permissions = self.calculate_user_permissions(member, tenant)
        quotas = permissions.get('quotas', {})
        return quotas.get(quota_name)
    
    def clear_user_permission_cache(self, member: Any, tenant: Any):
        """
        清除用户权限缓存
        
        Args:
            member: Member对象
            tenant: Tenant对象
        """
        cache_key = f"user_permissions:{tenant.id}:{member.id}"
        cache.delete(cache_key)
        
        self.logger.info(f"已清除权限缓存: {member.username}@{tenant.name}")
    
    def get_permission_comparison(
        self,
        member: Any,
        tenant: Any,
        target_level: Optional[UserLevel] = None,
        target_tags: Optional[List[UserTypeTag]] = None
    ) -> Dict[str, Any]:
        """
        获取权限对比信息（用于升级预览）
        
        Args:
            member: Member对象
            tenant: Tenant对象
            target_level: 目标等级
            target_tags: 目标标签列表
            
        Returns:
            Dict: 权限对比数据
        """
        current_permissions = self.calculate_user_permissions(member, tenant)
        
        # 模拟目标权限
        tenant_user_profile = self._get_or_create_profile(member, tenant)
        
        # 临时修改等级和标签来计算目标权限
        original_level = tenant_user_profile.current_level
        
        try:
            if target_level:
                tenant_user_profile.current_level = target_level
            
            # 计算目标权限（这里简化处理，实际应该模拟标签变更）
            target_permissions = self._deep_copy_permissions(self.BASE_PERMISSIONS)
            target_permissions = self._apply_level_permissions(target_permissions, tenant_user_profile)
            
            if target_tags:
                # 模拟标签权限（简化处理）
                for tag in target_tags:
                    target_permissions = self._apply_tag_modifiers(target_permissions, tag.permission_modifiers)
            
            # 对比差异
            differences = self._compare_permissions(current_permissions, target_permissions)
            
            return {
                'current': current_permissions,
                'target': target_permissions,
                'improvements': differences['improvements'],
                'summary': {
                    'improved_permissions': len(differences['improvements']),
                    'target_level': target_level.level_name if target_level else None,
                    'target_tags': [tag.tag_name for tag in (target_tags or [])]
                }
            }
        
        finally:
            # 恢复原始等级
            tenant_user_profile.current_level = original_level
    
    def _get_or_create_profile(self, member: Any, tenant: Any) -> TenantUserProfile:
        """获取或创建租户用户档案"""
        profile, created = TenantUserProfile.objects.get_or_create(
            member=member,
            tenant=tenant,
            defaults={
                'total_points': 0,
                'available_points': 0,
            }
        )
        
        if created:
            self.logger.info(f"创建新的租户用户档案: {member.username}@{tenant.name}")
        
        return profile
    
    def _apply_level_permissions(
        self,
        permissions: Dict[str, Any],
        tenant_user_profile: TenantUserProfile
    ) -> Dict[str, Any]:
        """应用积分等级权限增强"""
        if not tenant_user_profile.current_level:
            return permissions
        
        level_permissions = tenant_user_profile.current_level.permissions or {}
        level_quotas = tenant_user_profile.current_level.quota_config or {}
        
        # 应用权限修改器
        for key, modifier in level_permissions.items():
            if key in permissions.get('features', {}):
                permissions['features'][key] = modifier
            elif key in permissions.get('license', {}):
                permissions['license'][key] = modifier
        
        # 应用配额修改器
        for key, multiplier in level_quotas.items():
            if key in permissions.get('quotas', {}):
                if isinstance(multiplier, (int, float)) and isinstance(permissions['quotas'][key], (int, float)):
                    permissions['quotas'][key] = int(permissions['quotas'][key] * multiplier)
        
        return permissions
    
    def _apply_tag_permissions(
        self,
        permissions: Dict[str, Any],
        tenant_user_profile: TenantUserProfile
    ) -> Dict[str, Any]:
        """应用VIP标签权限增强"""
        active_tags = tenant_user_profile.user_tags.filter(
            is_active=True,
            status='active'
        ).select_related('tag')
        
        for user_tag in active_tags:
            # 检查VIP状态
            vip_status = user_tag.calculate_vip_status()
            if not vip_status['is_active']:
                continue
            
            # 应用标签权限
            permissions = self._apply_tag_modifiers(permissions, user_tag.tag.permission_modifiers)
            permissions = self._apply_tag_modifiers(permissions, user_tag.tag.quota_modifiers, is_quota=True)
            
            # 记录标签使用
            user_tag.record_usage('permission_calculation')
        
        return permissions
    
    def _apply_tag_modifiers(
        self,
        permissions: Dict[str, Any],
        modifiers: Dict[str, Any],
        is_quota: bool = False
    ) -> Dict[str, Any]:
        """应用标签修改器"""
        target_section = 'quotas' if is_quota else None
        
        for key, modifier in modifiers.items():
            # 确定目标位置
            if target_section:
                target = permissions.get(target_section, {})
            else:
                # 自动检测位置
                target = None
                for section in ['features', 'license', 'quotas', 'limits']:
                    if key in permissions.get(section, {}):
                        target = permissions[section]
                        break
                
                if not target:
                    continue
            
            # 应用修改器
            if key in target:
                current_value = target[key]
                
                if isinstance(modifier, bool):
                    # 布尔型：VIP标签通常解锁功能
                    target[key] = current_value or modifier
                elif isinstance(modifier, (int, float)) and isinstance(current_value, (int, float)):
                    # 数值型：应用倍数
                    target[key] = int(current_value * modifier)
                else:
                    # 直接覆盖
                    target[key] = modifier
        
        return permissions
    
    def _apply_tenant_configurations(
        self,
        permissions: Dict[str, Any],
        tenant: Any
    ) -> Dict[str, Any]:
        """应用租户特定配置"""
        # 这里可以根据租户的配置进行权限调整
        # 例如：企业租户可能有不同的基础配额
        
        # 示例：如果租户有特殊配置
        if hasattr(tenant, 'permission_config') and tenant.permission_config:
            tenant_config = tenant.permission_config
            
            # 应用租户级别的权限覆盖
            for section, configs in tenant_config.items():
                if section in permissions:
                    permissions[section].update(configs)
        
        return permissions
    
    def _get_active_tags_summary(self, tenant_user_profile: TenantUserProfile) -> List[Dict[str, Any]]:
        """获取活跃标签摘要"""
        active_tags = tenant_user_profile.user_tags.filter(
            is_active=True,
            status='active'
        ).select_related('tag')
        
        summary = []
        for user_tag in active_tags:
            vip_status = user_tag.calculate_vip_status()
            
            summary.append({
                'name': user_tag.tag.tag_name,
                'type': user_tag.tag.tag_type,
                'level': user_tag.tag.tag_level,
                'color': user_tag.tag.tag_color,
                'status': vip_status['status'],
                'is_active': vip_status['is_active'],
                'days_remaining': vip_status.get('days_remaining'),
                'expires_at': user_tag.expires_at.isoformat() if user_tag.expires_at else None
            })
        
        return sorted(summary, key=lambda x: x['level'], reverse=True)
    
    def _deep_copy_permissions(self, permissions: Dict[str, Any]) -> Dict[str, Any]:
        """深拷贝权限字典"""
        import copy
        return copy.deepcopy(permissions)
    
    def _compare_permissions(
        self,
        current: Dict[str, Any],
        target: Dict[str, Any]
    ) -> Dict[str, Any]:
        """对比权限差异"""
        improvements = {}
        
        def compare_section(curr_section, target_section, section_name):
            section_improvements = {}
            
            for key, target_value in target_section.items():
                if key.startswith('_'):  # 跳过元数据
                    continue
                
                current_value = curr_section.get(key, None)
                
                if isinstance(target_value, bool) and target_value and not current_value:
                    section_improvements[key] = {
                        'from': current_value,
                        'to': target_value,
                        'improvement': 'unlocked'
                    }
                elif isinstance(target_value, (int, float)) and isinstance(current_value, (int, float)):
                    if target_value > current_value:
                        section_improvements[key] = {
                            'from': current_value,
                            'to': target_value,
                            'improvement': f'+{target_value - current_value}'
                        }
            
            if section_improvements:
                improvements[section_name] = section_improvements
        
        # 比较各个部分
        for section in ['features', 'license', 'quotas', 'limits']:
            if section in current and section in target:
                compare_section(current[section], target[section], section)
        
        return {'improvements': improvements}


class PermissionValidator:
    """
    权限验证器
    
    提供常用的权限检查方法
    """
    
    def __init__(self, permission_service: TenantAwarePermissionService):
        self.permission_service = permission_service
    
    def validate_license_assignment(
        self,
        member: Any,
        tenant: Any,
        license_count: int = 1
    ) -> Dict[str, Any]:
        """
        验证许可证分配权限
        
        Args:
            member: Member对象
            tenant: Tenant对象
            license_count: 需要分配的许可证数量
            
        Returns:
            Dict: 验证结果
        """
        permissions = self.permission_service.calculate_user_permissions(member, tenant)
        
        max_licenses = permissions['license']['max_licenses']
        
        # 查询current已分配的许可证数量
        from licenses.models import LicenseAssignment
        current_assignments = LicenseAssignment.objects.filter(
            member=member,
            tenant=tenant,
            status='active'
        ).count()
        
        available_slots = max_licenses - current_assignments
        
        return {
            'is_valid': available_slots >= license_count,
            'max_licenses': max_licenses,
            'current_assignments': current_assignments,
            'available_slots': available_slots,
            'requested_count': license_count,
            'message': (
                f"许可证配额充足" if available_slots >= license_count
                else f"许可证配额不足，最多还能分配 {available_slots} 个"
            )
        }
    
    def validate_api_access(self, member: Any, tenant: Any) -> bool:
        """验证API访问权限"""
        return self.permission_service.check_permission(
            member, tenant, 'features.api_access', True
        )
    
    def validate_bulk_operations(self, member: Any, tenant: Any) -> bool:
        """验证批量操作权限"""
        return self.permission_service.check_permission(
            member, tenant, 'features.bulk_operations', True
        )
    
    def validate_storage_quota(
        self,
        member: Any,
        tenant: Any,
        required_mb: int
    ) -> Dict[str, Any]:
        """
        验证存储配额
        
        Args:
            member: Member对象
            tenant: Tenant对象
            required_mb: 需要的存储空间（MB）
            
        Returns:
            Dict: 验证结果
        """
        storage_quota = self.permission_service.get_quota_value(
            member, tenant, 'storage_mb'
        )
        
        # 这里应该查询current已使用的存储空间
        # 简化处理，假设已使用存储为0
        used_storage = 0
        available_storage = storage_quota - used_storage
        
        return {
            'is_valid': available_storage >= required_mb,
            'quota_mb': storage_quota,
            'used_mb': used_storage,
            'available_mb': available_storage,
            'required_mb': required_mb,
            'message': (
                f"存储配额充足" if available_storage >= required_mb
                else f"存储配额不足，还需要 {required_mb - available_storage} MB"
            )
        }
