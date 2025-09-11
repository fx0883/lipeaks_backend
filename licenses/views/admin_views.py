"""
许可证管理员API视图
提供产品、方案、许可证的CRUD操作和管理功能
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiResponse, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from common.permissions import IsSuperAdminOrTenantAdmin
from common.authentication.jwt_auth import JWTAuthentication
from licenses.models import (
    SoftwareProduct, LicensePlan, License, MachineBinding, 
    LicenseActivation, SecurityAuditLog, TenantLicenseQuota
)
from licenses.serializers import (
    SoftwareProductSerializer, SoftwareProductCreateSerializer,
    LicensePlanSerializer, LicenseSerializer, LicenseDetailSerializer,
    LicenseCreateSerializer, MachineBindingSerializer,
    LicenseActivationSerializer, SecurityAuditLogSerializer,
    TenantLicenseQuotaSerializer, LicenseReportSerializer,
    BatchOperationSerializer
)
from licenses.services.license_service import LicenseManagementService
import logging

logger = logging.getLogger('licenses.admin')


@extend_schema_view(
    list=extend_schema(
        tags=['许可证产品管理'],
        summary='获取软件产品列表',
        description='获取软件产品的分页列表，支持搜索和过滤'
    ),
    create=extend_schema(
        tags=['许可证产品管理'],
        summary='创建软件产品',
        description='创建新的软件产品并生成RSA密钥对'
    ),
    retrieve=extend_schema(
        tags=['许可证产品管理'],
        summary='获取软件产品详情',
        description='根据ID获取指定软件产品的详细信息'
    ),
    update=extend_schema(
        tags=['许可证产品管理'],
        summary='更新软件产品',
        description='更新指定软件产品的信息'
    ),
    partial_update=extend_schema(
        tags=['许可证产品管理'],
        summary='部分更新软件产品',
        description='部分更新指定软件产品的信息'
    ),
    destroy=extend_schema(
        tags=['许可证产品管理'],
        summary='删除软件产品',
        description='软删除指定的软件产品'
    ),
    regenerate_keypair=extend_schema(
        tags=['许可证产品管理'],
        summary='重新生成产品密钥对',
        description='为软件产品重新生成RSA密钥对',
        responses={200: OpenApiResponse(description='密钥对重新生成成功')}
    ),
    statistics=extend_schema(
        tags=['许可证产品管理'],
        summary='获取产品统计信息',
        description='获取指定产品的许可证、激活和机器绑定统计信息',
        responses={200: OpenApiResponse(description='统计信息')}
    )
)
class SoftwareProductViewSet(viewsets.ModelViewSet):
    """软件产品管理视图集"""
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsSuperAdminOrTenantAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """根据用户权限返回产品列表"""
        queryset = SoftwareProduct.objects.filter(is_deleted=False)
        
        if self.request.user.is_super_admin:
            return queryset
        
        # 租户管理员只能看到自己租户的产品
        if hasattr(self.request.user, 'tenant') and self.request.user.tenant:
            return queryset.filter(tenant=self.request.user.tenant)
        
        return queryset.none()
    
    def get_serializer_class(self):
        """根据操作返回不同的序列化器"""
        if self.action == 'create':
            return SoftwareProductCreateSerializer
        return SoftwareProductSerializer
    
    def perform_create(self, serializer):
        """创建产品时自动设置租户信息"""
        # 从中间件获取当前租户信息
        tenant_id = getattr(self.request, 'tenant_id', None)
        if tenant_id:
            from tenants.models import Tenant
            try:
                tenant = Tenant.objects.get(id=int(tenant_id))
                serializer.save(tenant=tenant)
                logger.info(f"产品创建成功，关联租户: {tenant.name} (ID: {tenant_id})")
            except Tenant.DoesNotExist:
                logger.error(f"指定的租户ID不存在: {tenant_id}")
                serializer.save()
        else:
            # 如果没有租户信息但用户已认证，尝试使用用户关联的租户
            if hasattr(self.request.user, 'tenant') and self.request.user.tenant:
                serializer.save(tenant=self.request.user.tenant)
                logger.info(f"产品创建成功，使用用户关联租户: {self.request.user.tenant.name}")
            else:
                serializer.save()
                logger.warning("产品创建时未设置租户信息")
    
    @action(detail=True, methods=['post'])
    def regenerate_keypair(self, request, pk=None):
        """重新生成产品密钥对"""
        try:
            product = self.get_object()
            
            from licenses.services.security_service import SecurityService
            security_service = SecurityService()
            
            # 生成新的密钥对
            private_key_pem, public_key_pem = security_service.rsa_manager.generate_keypair()
            private_key_hash = security_service.hash_manager.hash_data(
                private_key_pem.decode()
            )
            
            # 更新产品密钥
            product.public_key = public_key_pem.decode()
            product.private_key_hash = private_key_hash
            product.save()
            
            # 记录安全日志
            SecurityAuditLog.objects.create(
                event_type='keypair_generated',
                severity='MEDIUM',
                user=request.user,
                details={
                    'product_id': product.id,
                    'product_code': product.code,
                    'operation': 'keypair_regeneration'
                }
            )
            
            logger.info(f"产品密钥对重新生成: {product.code}")
            return Response({
                'success': True,
                'message': '密钥对重新生成成功',
                'public_key_preview': public_key_pem.decode()[:100] + '...'
            })
            
        except Exception as e:
            logger.error(f"密钥对重新生成失败: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """获取产品统计信息"""
        try:
            product = self.get_object()
            
            # 许可证统计
            license_stats = product.licenses.aggregate(
                total=Count('id'),
                active=Count('id', filter=Q(status='activated')),
                expired=Count('id', filter=Q(expires_at__lt=timezone.now())),
                revoked=Count('id', filter=Q(status='revoked'))
            )
            
            # 激活统计
            activation_stats = LicenseActivation.objects.filter(
                license__product=product
            ).aggregate(
                total_attempts=Count('id'),
                successful=Count('id', filter=Q(result='success')),
                failed=Count('id', filter=Q(result='failed'))
            )
            
            # 机器绑定统计
            binding_stats = MachineBinding.objects.filter(
                license__product=product
            ).aggregate(
                total_machines=Count('id'),
                active_machines=Count('id', filter=Q(status='active'))
            )
            
            return Response({
                'product_id': product.id,
                'product_name': product.name,
                'licenses': license_stats,
                'activations': activation_stats,
                'machine_bindings': binding_stats,
                'generated_at': timezone.now().isoformat()
            })
            
        except Exception as e:
            logger.error(f"产品统计获取失败: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema_view(
    list=extend_schema(
        tags=['许可证方案管理'],
        summary='获取许可证方案列表',
        description='获取许可证方案的分页列表，支持搜索和过滤'
    ),
    create=extend_schema(
        tags=['许可证方案管理'],
        summary='创建许可证方案',
        description='为指定产品创建新的许可证方案'
    ),
    retrieve=extend_schema(
        tags=['许可证方案管理'],
        summary='获取许可证方案详情',
        description='根据ID获取指定许可证方案的详细信息'
    ),
    update=extend_schema(
        tags=['许可证方案管理'],
        summary='更新许可证方案',
        description='更新指定许可证方案的信息'
    ),
    partial_update=extend_schema(
        tags=['许可证方案管理'],
        summary='部分更新许可证方案',
        description='部分更新指定许可证方案的信息'
    ),
    destroy=extend_schema(
        tags=['许可证方案管理'],
        summary='删除许可证方案',
        description='软删除指定的许可证方案'
    ),
    duplicate=extend_schema(
        tags=['许可证方案管理'],
        summary='复制许可证方案',
        description='复制现有的许可证方案并创建副本',
        responses={201: OpenApiResponse(description='方案复制成功')}
    )
)
class LicensePlanViewSet(viewsets.ModelViewSet):
    """许可证方案管理视图集"""
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsSuperAdminOrTenantAdmin]
    serializer_class = LicensePlanSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['product', 'plan_type', 'status']
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'price', 'created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """根据用户权限返回方案列表"""
        queryset = LicensePlan.objects.filter(is_deleted=False)
        
        if self.request.user.is_super_admin:
            return queryset
        
        # 租户管理员只能看到自己租户的方案
        if hasattr(self.request.user, 'tenant') and self.request.user.tenant:
            return queryset.filter(tenant=self.request.user.tenant)
        
        return queryset.none()
    
    def perform_create(self, serializer):
        """创建方案时自动设置租户信息"""
        # 从中间件获取当前租户信息
        tenant_id = getattr(self.request, 'tenant_id', None)
        if tenant_id:
            from tenants.models import Tenant
            try:
                tenant = Tenant.objects.get(id=int(tenant_id))
                serializer.save(tenant=tenant)
                logger.info(f"方案创建成功，关联租户: {tenant.name} (ID: {tenant_id})")
            except Tenant.DoesNotExist:
                logger.error(f"指定的租户ID不存在: {tenant_id}")
                serializer.save()
        else:
            # 如果没有租户信息但用户已认证，尝试使用用户关联的租户
            if hasattr(self.request.user, 'tenant') and self.request.user.tenant:
                serializer.save(tenant=self.request.user.tenant)
                logger.info(f"方案创建成功，使用用户关联租户: {self.request.user.tenant.name}")
            else:
                serializer.save()
                logger.warning("方案创建时未设置租户信息")
    
    @action(detail=True, methods=['post'])
    def duplicate(self, request, pk=None):
        """复制许可证方案"""
        try:
            original_plan = self.get_object()
            
            # 复制方案，确保设置正确的租户信息
            new_code = f"{original_plan.code}_copy_{timezone.now().strftime('%Y%m%d_%H%M%S')}"
            
            # 确定租户信息
            target_tenant = original_plan.tenant
            tenant_id = getattr(self.request, 'tenant_id', None)
            if tenant_id:
                from tenants.models import Tenant
                try:
                    target_tenant = Tenant.objects.get(id=int(tenant_id))
                except Tenant.DoesNotExist:
                    pass
            elif hasattr(self.request.user, 'tenant') and self.request.user.tenant:
                target_tenant = self.request.user.tenant
            
            new_plan = LicensePlan.objects.create(
                product=original_plan.product,
                tenant=target_tenant,  # 设置租户信息
                name=f"{original_plan.name} (副本)",
                code=new_code,
                plan_type=original_plan.plan_type,
                max_machines=original_plan.max_machines,
                validity_days=original_plan.validity_days,
                features=original_plan.features.copy(),
                price=original_plan.price,
                currency=original_plan.currency,
                status='inactive'  # 新复制的方案默认为非激活状态
            )
            
            serializer = self.get_serializer(new_plan)
            return Response({
                'success': True,
                'message': '方案复制成功',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"方案复制失败: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema_view(
    list=extend_schema(
        tags=['许可证管理'],
        summary='获取许可证列表',
        description='获取许可证的分页列表，支持搜索和过滤'
    ),
    create=extend_schema(
        tags=['许可证管理'],
        summary='创建许可证',
        description='为指定产品和方案创建新的许可证'
    ),
    retrieve=extend_schema(
        tags=['许可证管理'],
        summary='获取许可证详情',
        description='根据ID获取指定许可证的详细信息'
    ),
    update=extend_schema(
        tags=['许可证管理'],
        summary='更新许可证',
        description='更新指定许可证的信息'
    ),
    partial_update=extend_schema(
        tags=['许可证管理'],
        summary='部分更新许可证',
        description='部分更新指定许可证的信息'
    ),
    destroy=extend_schema(
        tags=['许可证管理'],
        summary='删除许可证',
        description='软删除指定的许可证'
    ),
    revoke=extend_schema(
        tags=['许可证管理'],
        summary='撤销许可证',
        description='撤销指定的许可证并记录原因',
        responses={200: OpenApiResponse(description='许可证撤销成功')}
    ),
    extend=extend_schema(
        tags=['许可证管理'],
        summary='延长许可证有效期',
        description='延长指定许可证的有效期',
        responses={200: OpenApiResponse(description='许可证延期成功')}
    ),
    usage_stats=extend_schema(
        tags=['许可证管理'],
        summary='获取许可证使用统计',
        description='获取指定许可证的使用统计信息',
        responses={200: OpenApiResponse(description='使用统计信息')}
    ),
    batch_operation=extend_schema(
        tags=['许可证管理'],
        summary='批量操作许可证',
        description='对多个许可证执行批量操作（撤销、延期等）',
        responses={200: OpenApiResponse(description='批量操作结果')}
    )
)
class LicenseViewSet(viewsets.ModelViewSet):
    """许可证管理视图集"""
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsSuperAdminOrTenantAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['product', 'plan', 'status', 'tenant']
    search_fields = ['license_key', 'customer_name', 'customer_email']
    ordering_fields = ['issued_at', 'expires_at', 'customer_name']
    ordering = ['-issued_at']
    
    def get_queryset(self):
        """根据用户权限返回许可证列表"""
        queryset = License.objects.filter(is_deleted=False)
        
        if self.request.user.is_super_admin:
            return queryset
        
        # 租户管理员只能看到自己租户的许可证
        if hasattr(self.request.user, 'tenant'):
            return queryset.filter(tenant=self.request.user.tenant)
        
        return queryset.none()
    
    def get_serializer_class(self):
        """根据操作返回不同的序列化器"""
        if self.action == 'create':
            return LicenseCreateSerializer
        elif self.action == 'retrieve':
            return LicenseDetailSerializer
        return LicenseSerializer
    
    def perform_create(self, serializer):
        """创建许可证时自动填充缺失的字段"""
        save_kwargs = {}
        
        # 自动获取product字段
        if not serializer.validated_data.get('product') and serializer.validated_data.get('plan'):
            plan = serializer.validated_data['plan']
            save_kwargs['product'] = plan.product
            logger.info(f"自动从plan获取product: {plan.product.name}")
        
        # 自动获取tenant字段
        if not serializer.validated_data.get('tenant'):
            # 尝试从中间件获取当前租户信息
            tenant_id = getattr(self.request, 'tenant_id', None)
            if tenant_id:
                from tenants.models import Tenant
                try:
                    tenant = Tenant.objects.get(id=int(tenant_id))
                    save_kwargs['tenant'] = tenant
                    logger.info(f"从中间件获取租户: {tenant.name} (ID: {tenant_id})")
                except Tenant.DoesNotExist:
                    logger.error(f"指定的租户ID不存在: {tenant_id}")
            
            # 如果仍然没有租户信息，尝试使用用户关联的租户
            if 'tenant' not in save_kwargs and hasattr(self.request.user, 'tenant') and self.request.user.tenant:
                save_kwargs['tenant'] = self.request.user.tenant
                logger.info(f"使用用户关联租户: {self.request.user.tenant.name}")
            
            # 如果还是没有租户信息，记录警告
            if 'tenant' not in save_kwargs:
                logger.warning("许可证创建时未能自动获取租户信息")
        
        # 调用serializer.save()，传入额外的字段
        return serializer.save(**save_kwargs)
    
    @action(detail=True, methods=['post'])
    def revoke(self, request, pk=None):
        """撤销许可证"""
        try:
            license_obj = self.get_object()
            reason = request.data.get('reason', '管理员撤销')
            
            management_service = LicenseManagementService()
            success = management_service.revoke_license(
                license_id=license_obj.id,
                reason=reason,
                user_id=request.user.id
            )
            
            if success:
                return Response({
                    'success': True,
                    'message': '许可证撤销成功'
                })
            else:
                return Response({
                    'success': False,
                    'error': '许可证撤销失败'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"许可证撤销失败: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def extend(self, request, pk=None):
        """延长许可证有效期"""
        try:
            license_obj = self.get_object()
            days = request.data.get('days', 0)
            
            if days <= 0:
                return Response({
                    'success': False,
                    'error': '延长天数必须大于0'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 延长有效期
            license_obj.expires_at += timedelta(days=days)
            license_obj.save()
            
            # 记录安全日志
            SecurityAuditLog.objects.create(
                event_type='system_change',
                severity='LOW',
                user=request.user,
                tenant=license_obj.tenant,
                details={
                    'license_id': license_obj.id,
                    'operation': 'extend_license',
                    'days_extended': days,
                    'new_expiry': license_obj.expires_at.isoformat()
                }
            )
            
            return Response({
                'success': True,
                'message': f'许可证有效期已延长{days}天',
                'new_expiry': license_obj.expires_at.isoformat()
            })
            
        except Exception as e:
            logger.error(f"许可证延期失败: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def usage_stats(self, request, pk=None):
        """获取许可证使用统计"""
        try:
            license_obj = self.get_object()
            management_service = LicenseManagementService()
            
            stats = management_service.get_license_usage_stats(license_obj.id)
            return Response(stats)
            
        except Exception as e:
            logger.error(f"许可证统计获取失败: {str(e)}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'])
    def batch_operation(self, request):
        """批量操作许可证"""
        serializer = BatchOperationSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            license_ids = serializer.validated_data['license_ids']
            operation = serializer.validated_data['operation']
            parameters = serializer.validated_data.get('parameters', {})
            reason = serializer.validated_data.get('reason', '')
            
            # 获取许可证列表
            licenses = License.objects.filter(
                id__in=license_ids,
                is_deleted=False
            )
            
            # 检查权限
            if not request.user.is_super_admin:
                if hasattr(request.user, 'tenant'):
                    licenses = licenses.filter(tenant=request.user.tenant)
            
            results = []
            management_service = LicenseManagementService()
            
            with transaction.atomic():
                for license_obj in licenses:
                    try:
                        if operation == 'revoke':
                            success = management_service.revoke_license(
                                license_obj.id, reason, request.user.id
                            )
                            results.append({
                                'license_id': license_obj.id,
                                'success': success,
                                'message': '撤销成功' if success else '撤销失败'
                            })
                        
                        elif operation == 'extend':
                            days = parameters.get('days', 0)
                            if days > 0:
                                license_obj.expires_at += timedelta(days=days)
                                license_obj.save()
                                results.append({
                                    'license_id': license_obj.id,
                                    'success': True,
                                    'message': f'延长{days}天成功'
                                })
                        
                        # 其他操作...
                        
                    except Exception as e:
                        results.append({
                            'license_id': license_obj.id,
                            'success': False,
                            'error': str(e)
                        })
            
            # 统计结果
            successful = sum(1 for r in results if r.get('success', False))
            total = len(results)
            
            return Response({
                'success': True,
                'message': f'批量操作完成，成功: {successful}/{total}',
                'results': results
            })
            
        except Exception as e:
            logger.error(f"批量操作失败: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema_view(
    list=extend_schema(
        tags=['机器绑定管理'],
        summary='获取机器绑定列表',
        description='获取机器绑定的分页列表，支持搜索和过滤'
    ),
    retrieve=extend_schema(
        tags=['机器绑定管理'],
        summary='获取机器绑定详情',
        description='根据ID获取指定机器绑定的详细信息'
    ),
    block=extend_schema(
        tags=['机器绑定管理'],
        summary='阻止机器绑定',
        description='阻止指定的机器绑定并记录原因',
        responses={200: OpenApiResponse(description='机器绑定已阻止')}
    )
)
class MachineBindingViewSet(viewsets.ReadOnlyModelViewSet):
    """机器绑定管理视图集（只读）"""
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsSuperAdminOrTenantAdmin]
    serializer_class = MachineBindingSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['license', 'status']
    search_fields = ['machine_id']
    ordering_fields = ['first_seen_at', 'last_seen_at']
    ordering = ['-last_seen_at']
    
    def get_queryset(self):
        """根据用户权限返回机器绑定列表"""
        queryset = MachineBinding.objects.all()
        
        if self.request.user.is_super_admin:
            return queryset
        
        # 租户管理员只能看到自己租户的机器绑定
        if hasattr(self.request.user, 'tenant'):
            return queryset.filter(license__tenant=self.request.user.tenant)
        
        return queryset.none()
    
    @action(detail=True, methods=['post'])
    def block(self, request, pk=None):
        """阻止机器绑定"""
        try:
            binding = self.get_object()
            reason = request.data.get('reason', '管理员阻止')
            
            binding.status = 'blocked'
            binding.save()
            
            # 记录安全日志
            SecurityAuditLog.objects.create(
                event_type='system_change',
                severity='MEDIUM',
                user=request.user,
                tenant=binding.license.tenant,
                details={
                    'machine_binding_id': binding.id,
                    'machine_id': binding.machine_id,
                    'operation': 'block_machine',
                    'reason': reason
                }
            )
            
            return Response({
                'success': True,
                'message': '机器绑定已阻止'
            })
            
        except Exception as e:
            logger.error(f"机器绑定阻止失败: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema_view(
    list=extend_schema(
        tags=['许可证激活记录'],
        summary='获取许可证激活记录列表',
        description='获取许可证激活记录的分页列表，支持搜索和过滤'
    ),
    retrieve=extend_schema(
        tags=['许可证激活记录'],
        summary='获取许可证激活记录详情',
        description='根据ID获取指定许可证激活记录的详细信息'
    )
)
class LicenseActivationViewSet(viewsets.ReadOnlyModelViewSet):
    """许可证激活记录视图集（只读）"""
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsSuperAdminOrTenantAdmin]
    serializer_class = LicenseActivationSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['license', 'activation_type', 'result']
    search_fields = ['activation_code', 'ip_address']
    ordering_fields = ['activated_at']
    ordering = ['-activated_at']
    
    def get_queryset(self):
        """根据用户权限返回激活记录列表"""
        queryset = LicenseActivation.objects.all()
        
        if self.request.user.is_super_admin:
            return queryset
        
        # 租户管理员只能看到自己租户的激活记录
        if hasattr(self.request.user, 'tenant'):
            return queryset.filter(license__tenant=self.request.user.tenant)
        
        return queryset.none()


@extend_schema_view(
    list=extend_schema(
        tags=['安全审计日志'],
        summary='获取安全审计日志列表',
        description='获取安全审计日志的分页列表，支持按事件类型和严重程度过滤'
    ),
    retrieve=extend_schema(
        tags=['安全审计日志'],
        summary='获取安全审计日志详情',
        description='根据ID获取指定安全审计日志的详细信息'
    )
)
class SecurityAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """安全审计日志视图集（只读）"""
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsSuperAdminOrTenantAdmin]
    serializer_class = SecurityAuditLogSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['event_type', 'severity', 'user', 'tenant']
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        """根据用户权限返回审计日志列表"""
        queryset = SecurityAuditLog.objects.all()
        
        if self.request.user.is_super_admin:
            return queryset
        
        # 租户管理员只能看到自己租户的审计日志
        if hasattr(self.request.user, 'tenant'):
            return queryset.filter(
                Q(tenant=self.request.user.tenant) | Q(tenant__isnull=True)
            )
        
        return queryset.none()


@extend_schema_view(
    list=extend_schema(
        tags=['租户许可证配额管理'],
        summary='获取租户许可证配额列表',
        description='获取租户许可证配额的分页列表，支持按租户和产品过滤'
    ),
    create=extend_schema(
        tags=['租户许可证配额管理'],
        summary='创建租户许可证配额',
        description='为指定租户和产品创建许可证配额限制'
    ),
    retrieve=extend_schema(
        tags=['租户许可证配额管理'],
        summary='获取租户许可证配额详情',
        description='根据ID获取指定租户许可证配额的详细信息'
    ),
    update=extend_schema(
        tags=['租户许可证配额管理'],
        summary='更新租户许可证配额',
        description='更新指定租户许可证配额的信息'
    ),
    partial_update=extend_schema(
        tags=['租户许可证配额管理'],
        summary='部分更新租户许可证配额',
        description='部分更新指定租户许可证配额的信息'
    ),
    destroy=extend_schema(
        tags=['租户许可证配额管理'],
        summary='删除租户许可证配额',
        description='软删除指定的租户许可证配额'
    )
)
class TenantLicenseQuotaViewSet(viewsets.ModelViewSet):
    """租户许可证配额管理视图集"""
    
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsSuperAdminOrTenantAdmin]
    serializer_class = TenantLicenseQuotaSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['tenant', 'product', 'is_active']
    ordering_fields = ['quota_start_date', 'quota_end_date']
    ordering = ['-quota_start_date']
    
    def get_queryset(self):
        """根据用户权限返回配额列表"""
        queryset = TenantLicenseQuota.objects.filter(is_deleted=False)
        
        if self.request.user.is_super_admin:
            return queryset
        
        # 租户管理员只能看到自己租户的配额
        if hasattr(self.request.user, 'tenant'):
            return queryset.filter(tenant=self.request.user.tenant)
        
        return queryset.none()
