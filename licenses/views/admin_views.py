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
                default_max_activations=original_plan.default_max_activations,
                default_validity_days=original_plan.default_validity_days,
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
        description='''
        为指定的产品和方案创建新的许可证。

        ## 业务逻辑
        
        1. **产品与方案关联**: product字段可选，如未提供将从plan自动获取
        2. **租户自动关联**: tenant字段可选，如未提供将从当前用户的租户自动获取  
        3. **许可证密钥生成**: 系统自动生成25字符格式的许可证密钥 (XXXXX-XXXXX-XXXXX-XXXXX-XXXXX)
        4. **过期时间计算**: 可通过validity_days指定有效期，否则使用方案的default_validity_days
        5. **激活限制**: max_activations可自定义，否则使用方案的default_max_activations
        6. **客户信息必需**: 必须提供包含name和email的customer_info对象

        ## 权限要求
        - 需要JWT认证
        - 需要超级管理员或租户管理员权限
        - 租户管理员只能为自己的租户创建许可证

        ## 字段说明 (RIPER-5方案A重构版)
        - 方案字段使用 `default_max_activations`、`default_validity_days` (模板配置)
        - 许可证字段使用 `max_activations`、`expires_at` (实际使用值)
        ''',
        request=LicenseCreateSerializer,
        responses={
            201: OpenApiResponse(
                response=LicenseDetailSerializer,
                description='许可证创建成功',
                examples={
                    'application/json': {
                        'id': 123,
                        'product': 1,
                        'product_name': 'SuperApp Pro',
                        'plan': 2, 
                        'plan_name': '企业版',
                        'tenant': 1,
                        'tenant_name': '示例公司',
                        'license_key': 'ABC12-DEF34-GHI56-JKL78-MNO90',
                        'customer_name': '张三',
                        'customer_email': 'zhangsan@example.com',
                        'max_activations': 10,
                        'current_activations': 0,
                        'issued_at': '2024-09-26T10:30:00Z',
                        'expires_at': '2025-09-26T10:30:00Z',
                        'last_verified_at': None,
                        'status': 'active',
                        'machine_bindings_count': 0,
                        'days_until_expiry': 365,
                        'notes': '为重要客户创建的企业版许可证',
                        'machine_bindings': [],
                        'recent_activations': [],
                        'usage_stats': {
                            'total_usage_logs': 0,
                            'recent_usage_logs': 0
                        },
                        'metadata': {
                            'created_by': 'admin',
                            'creation_source': 'admin_panel',
                            'ip_address': '192.168.1.100'
                        }
                    }
                }
            ),
            400: OpenApiResponse(
                description='请求参数错误',
                examples={
                    'application/json': {
                        'detail': '验证失败',
                        'errors': {
                            'customer_info': ['客户信息缺少必要字段: name'],
                            'plan': ['所选方案(基础版)属于产品(AppStandard)，与所选产品(AppPro)不一致，请重新选择正确的方案。']
                        }
                    }
                }
            ),
            401: OpenApiResponse(
                description='认证失败',
                examples={
                    'application/json': {
                        'detail': '身份验证凭据无效。'
                    }
                }
            ),
            403: OpenApiResponse(
                description='权限不足',
                examples={
                    'application/json': {
                        'detail': '您没有权限执行此操作。'
                    }
                }
            ),
            500: OpenApiResponse(
                description='服务器内部错误',
                examples={
                    'application/json': {
                        'detail': '许可证创建失败，请联系系统管理员。'
                    }
                }
            )
        },
        examples=[
            {
                'name': '基础创建示例',
                'description': '使用最少必需字段创建许可证',
                'value': {
                    'plan': 2,
                    'customer_info': {
                        'name': '李四',
                        'email': 'lisi@example.com',
                        'company': '科技有限公司',
                        'phone': '+86-138-0013-8000'
                    },
                    'notes': '客户申请的标准版许可证'
                }
            },
            {
                'name': '完整创建示例',
                'description': '包含所有可选字段的完整创建示例',
                'value': {
                    'product': 1,
                    'plan': 3,
                    'tenant': 2,
                    'customer_info': {
                        'name': '王五',
                        'email': 'wangwu@enterprise.com',
                        'company': '大型企业集团',
                        'phone': '+86-139-0013-9000',
                        'address': '北京市朝阳区XXX街道123号',
                        'contact_person': '技术部-王经理'
                    },
                    'max_activations': 50,
                    'validity_days': 730,
                    'notes': '企业客户专属版本，支持高并发和集群部署'
                }
            },
            {
                'name': '批量用户场景',
                'description': '为组织用户创建许可证的典型场景',
                'value': {
                    'plan': 4,
                    'customer_info': {
                        'name': '教育机构-计算机学院',
                        'email': 'admin@university.edu.cn',
                        'company': '某某大学',
                        'department': '计算机科学与技术学院',
                        'phone': '+86-010-12345678'
                    },
                    'max_activations': 200,
                    'validity_days': 365,
                    'notes': '教育版许可证，用于学生实验和教学'
                }
            }
        ]
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
    
    @extend_schema(
        tags=['许可证管理'],
        summary='下载许可证',
        description='下载许可证文件，包含许可证密钥、客户信息、产品信息和使用说明',
        parameters=[
            OpenApiParameter(
                name='format',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description='下载格式：json(默认)、txt、xml',
                enum=['json', 'txt', 'xml'],
                default='json'
            )
        ],
        responses={
            200: OpenApiResponse(
                description='许可证下载成功',
                examples=[
                    {
                        'application/json': {
                            'license_key': 'XXXX-XXXX-XXXX-XXXX',
                            'customer_info': {'name': 'Customer Name', 'email': 'email@example.com'},
                            'product_info': {'name': 'Product Name', 'version': '1.0.0'},
                            'activation_info': {'max_activations': 5, 'current_activations': 2},
                            'validity_info': {'issued_at': '2023-01-01T00:00:00Z', 'expires_at': '2024-01-01T00:00:00Z'},
                            'instructions': 'License usage instructions...'
                        }
                    }
                ]
            ),
            404: OpenApiResponse(description='许可证不存在'),
            403: OpenApiResponse(description='无权限访问该许可证')
        }
    )
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """下载许可证"""
        try:
            license_obj = self.get_object()
            download_format = request.query_params.get('format', 'json').lower()
            
            # 构建许可证信息
            license_data = {
                'license_key': license_obj.license_key,
                'customer_info': {
                    'name': license_obj.customer_name,
                    'email': license_obj.customer_email,
                },
                'product_info': {
                    'name': license_obj.product.name,
                    'code': license_obj.product.code,
                    'version': license_obj.product.version,
                    'description': license_obj.product.description
                },
                'plan_info': {
                    'name': license_obj.plan.name,
                    'type': license_obj.plan.plan_type,
                    'features': license_obj.plan.features,
                    'default_max_activations': license_obj.plan.default_max_activations
                },
                'activation_info': {
                    'max_activations': license_obj.max_activations,
                    'current_activations': license_obj.current_activations,
                    'status': license_obj.status
                },
                'validity_info': {
                    'issued_at': license_obj.issued_at.isoformat(),
                    'expires_at': license_obj.expires_at.isoformat(),
                    'last_verified_at': license_obj.last_verified_at.isoformat() if license_obj.last_verified_at else None
                },
                'instructions': self._generate_license_instructions(license_obj),
                'generated_at': timezone.now().isoformat(),
                'download_by': request.user.username if request.user else 'Unknown'
            }
            
            # 记录下载日志
            SecurityAuditLog.objects.create(
                event_type='data_access',
                severity='LOW',
                user=request.user,
                tenant=license_obj.tenant,
                ip_address=request.META.get('REMOTE_ADDR'),
                details={
                    'license_id': license_obj.id,
                    'operation': 'download_license',
                    'format': download_format
                }
            )
            
            # 根据格式返回不同的响应
            if download_format == 'json':
                response = Response(license_data)
                response['Content-Disposition'] = f'attachment; filename="license_{license_obj.id}.json"'
                return response
                
            elif download_format == 'txt':
                txt_content = self._format_license_as_text(license_data)
                response = Response(
                    txt_content,
                    content_type='text/plain; charset=utf-8'
                )
                response['Content-Disposition'] = f'attachment; filename="license_{license_obj.id}.txt"'
                return response
                
            elif download_format == 'xml':
                xml_content = self._format_license_as_xml(license_data)
                response = Response(
                    xml_content,
                    content_type='application/xml; charset=utf-8'
                )
                response['Content-Disposition'] = f'attachment; filename="license_{license_obj.id}.xml"'
                return response
                
            else:
                return Response({
                    'success': False,
                    'error': f'不支持的下载格式: {download_format}'
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"许可证下载失败: {str(e)}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _generate_license_instructions(self, license_obj):
        """生成许可证使用说明"""
        instructions = f"""
许可证使用说明
=============

产品名称: {license_obj.product.name}
许可方案: {license_obj.plan.name}
许可证密钥: {license_obj.license_key}

安装说明:
1. 下载并安装 {license_obj.product.name} 软件
2. 启动软件后，在许可证激活界面输入上述许可证密钥
3. 按照软件提示完成激活流程

重要信息:
- 最大激活设备数: {license_obj.max_activations}
- 当前已激活设备数: {license_obj.current_activations}
- 许可证过期时间: {license_obj.expires_at.strftime('%Y年%m月%d日 %H:%M:%S')}
- 许可证状态: {license_obj.get_status_display()}

注意事项:
- 请妥善保管许可证密钥，避免泄露
- 如需在新设备激活，请先在原设备解除激活
- 如遇激活问题，请联系技术支持

技术支持:
如有任何问题，请联系我们的技术支持团队。

生成时间: {timezone.now().strftime('%Y年%m月%d日 %H:%M:%S')}
"""
        return instructions.strip()
    
    def _format_license_as_text(self, license_data):
        """将许可证信息格式化为文本"""
        text = f"""
许可证信息
=========

许可证密钥: {license_data['license_key']}

客户信息:
--------
姓名: {license_data['customer_info']['name']}
邮箱: {license_data['customer_info']['email']}

产品信息:
--------
产品名称: {license_data['product_info']['name']}
产品代码: {license_data['product_info']['code']}
产品版本: {license_data['product_info']['version']}
产品描述: {license_data['product_info']['description']}

方案信息:
--------
方案名称: {license_data['plan_info']['name']}
方案类型: {license_data['plan_info']['type']}
默认最大激活数: {license_data['plan_info']['default_max_activations']}

激活信息:
--------
最大激活数: {license_data['activation_info']['max_activations']}
当前激活数: {license_data['activation_info']['current_activations']}
许可证状态: {license_data['activation_info']['status']}

有效期信息:
----------
签发时间: {license_data['validity_info']['issued_at']}
过期时间: {license_data['validity_info']['expires_at']}
最后验证: {license_data['validity_info']['last_verified_at'] or '未验证'}

{license_data['instructions']}

下载信息:
--------
下载时间: {license_data['generated_at']}
下载用户: {license_data['download_by']}
"""
        return text.strip()
    
    def _format_license_as_xml(self, license_data):
        """将许可证信息格式化为XML"""
        from xml.etree.ElementTree import Element, SubElement, tostring
        from xml.dom import minidom
        
        root = Element('license')
        
        # 许可证密钥
        key_elem = SubElement(root, 'license_key')
        key_elem.text = license_data['license_key']
        
        # 客户信息
        customer_elem = SubElement(root, 'customer_info')
        SubElement(customer_elem, 'name').text = license_data['customer_info']['name']
        SubElement(customer_elem, 'email').text = license_data['customer_info']['email']
        
        # 产品信息
        product_elem = SubElement(root, 'product_info')
        SubElement(product_elem, 'name').text = license_data['product_info']['name']
        SubElement(product_elem, 'code').text = license_data['product_info']['code']
        SubElement(product_elem, 'version').text = license_data['product_info']['version']
        SubElement(product_elem, 'description').text = license_data['product_info']['description']
        
        # 方案信息
        plan_elem = SubElement(root, 'plan_info')
        SubElement(plan_elem, 'name').text = license_data['plan_info']['name']
        SubElement(plan_elem, 'type').text = license_data['plan_info']['type']
        SubElement(plan_elem, 'default_max_activations').text = str(license_data['plan_info']['default_max_activations'])
        
        # 激活信息
        activation_elem = SubElement(root, 'activation_info')
        SubElement(activation_elem, 'max_activations').text = str(license_data['activation_info']['max_activations'])
        SubElement(activation_elem, 'current_activations').text = str(license_data['activation_info']['current_activations'])
        SubElement(activation_elem, 'status').text = license_data['activation_info']['status']
        
        # 有效期信息
        validity_elem = SubElement(root, 'validity_info')
        SubElement(validity_elem, 'issued_at').text = license_data['validity_info']['issued_at']
        SubElement(validity_elem, 'expires_at').text = license_data['validity_info']['expires_at']
        SubElement(validity_elem, 'last_verified_at').text = license_data['validity_info']['last_verified_at'] or ''
        
        # 使用说明
        SubElement(root, 'instructions').text = license_data['instructions']
        
        # 下载信息
        download_elem = SubElement(root, 'download_info')
        SubElement(download_elem, 'generated_at').text = license_data['generated_at']
        SubElement(download_elem, 'download_by').text = license_data['download_by']
        
        # 格式化XML
        rough_string = tostring(root, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')
    
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
