"""
客户视图
"""
import logging
from django.db.models import Q, Count, Case, When, IntegerField
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample

from common.permissions import IsAdmin, IsSuperAdmin
from customers.models import Customer
from customers.serializers import (
    CustomerSerializer, CustomerListSerializer, CustomerStatisticsSerializer,
    BulkCustomerCreateSerializer, BulkCustomerUpdateSerializer
)

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary="获取客户列表",
        description="获取系统中的所有客户，支持分页、排序和筛选",
        tags=["客户管理"],
        parameters=[
            OpenApiParameter(name="status", description="按状态筛选客户", required=False, type=str),
            OpenApiParameter(name="type", description="按类型筛选客户", required=False, type=str),
            OpenApiParameter(name="value_level", description="按价值等级筛选客户", required=False, type=str),
            OpenApiParameter(name="company_size", description="按公司规模筛选客户", required=False, type=str),
            OpenApiParameter(name="search", description="搜索客户名称、联系人等信息", required=False, type=str),
        ]
    ),
    retrieve=extend_schema(
        summary="获取单个客户",
        description="获取指定ID的客户详情",
        tags=["客户管理"]
    ),
    create=extend_schema(
        summary="创建客户",
        description="创建新的客户记录",
        tags=["客户管理"],
        examples=[
            OpenApiExample(
                '公司客户示例',
                summary='创建公司客户',
                description='创建一个新的公司客户',
                value={
                    "name": "示例科技有限公司",
                    "type": "company",
                    "value_level": "vip",
                    "status": "active",
                    "business_license_number": "91110000123456789X",
                    "tax_identification_number": "91110000123456789X",
                    "registered_capital": "1000万元",
                    "legal_representative": "张三",
                    "registered_address": "北京市海淀区中关村南大街5号",
                    "business_address": "北京市海淀区中关村南大街5号",
                    "business_scope": "软件开发、技术咨询、技术服务",
                    "industry_type": "信息技术",
                    "company_size": "medium",
                    "establishment_date": "2010-01-01",
                    "website": "http://www.example.com",
                    "primary_contact_name": "李四",
                    "primary_contact_phone": "13800138000",
                    "primary_contact_email": "contact@example.com",
                    "bank_name": "中国银行",
                    "bank_account": "6222020000123456789",
                    "credit_rating": "A",
                    "payment_terms": "月结30天",
                    "special_requirements": "需要定期技术支持",
                    "notes": "重要客户",
                    "source": "展会"
                },
                request_only=True,
            ),
            OpenApiExample(
                '个人客户示例',
                summary='创建个人客户',
                description='创建一个新的个人客户',
                value={
                    "name": "张三",
                    "type": "personal",
                    "value_level": "normal",
                    "status": "active",
                    "primary_contact_phone": "13900139000",
                    "primary_contact_email": "zhangsan@example.com",
                    "notes": "个人客户",
                    "source": "推荐"
                },
                request_only=True,
            ),
        ]
    ),
    update=extend_schema(
        summary="更新客户",
        description="更新指定ID的客户信息",
        tags=["客户管理"],
        examples=[
            OpenApiExample(
                '更新公司客户示例',
                summary='更新公司客户',
                description='更新公司客户的完整信息',
                value={
                    "name": "更新后的科技有限公司",
                    "type": "company",
                    "value_level": "vip",
                    "status": "active",
                    "business_license_number": "91110000123456789X",
                    "tax_identification_number": "91110000123456789X",
                    "registered_capital": "2000万元",
                    "legal_representative": "李四",
                    "registered_address": "北京市朝阳区建国门外大街1号",
                    "business_address": "北京市朝阳区建国门外大街1号",
                    "business_scope": "软件开发、技术咨询、技术服务、系统集成",
                    "industry_type": "信息技术",
                    "company_size": "large",
                    "establishment_date": "2010-01-01",
                    "website": "http://www.updated-example.com",
                    "primary_contact_name": "王五",
                    "primary_contact_phone": "13900139000",
                    "primary_contact_email": "contact@updated-example.com",
                    "bank_name": "中国工商银行",
                    "bank_account": "6222020000123456790",
                    "credit_rating": "AA",
                    "payment_terms": "月结45天",
                    "special_requirements": "需要7x24小时技术支持",
                    "notes": "重要客户，需要重点关注",
                    "source": "展会"
                },
                request_only=True,
            ),
            OpenApiExample(
                '更新个人客户示例',
                summary='更新个人客户',
                description='更新个人客户的信息',
                value={
                    "name": "李四",
                    "type": "personal",
                    "value_level": "vip",
                    "status": "active",
                    "primary_contact_phone": "13900139000",
                    "primary_contact_email": "lisi@example.com",
                    "notes": "VIP个人客户",
                    "source": "推荐"
                },
                request_only=True,
            ),
        ]
    ),
    partial_update=extend_schema(
        summary="部分更新客户",
        description="部分更新指定ID的客户信息",
        tags=["客户管理"],
        examples=[
            OpenApiExample(
                '部分更新客户示例',
                summary='部分更新客户',
                description='只更新客户的部分字段',
                value={
                    "status": "inactive",
                    "notes": "已暂停合作"
                },
                request_only=True,
            ),
        ]
    ),
    destroy=extend_schema(
        summary="删除客户",
        description="删除指定ID的客户（软删除）",
        tags=["客户管理"]
    ),
)
class CustomerViewSet(viewsets.ModelViewSet):
    """
    客户管理视图集
    
    提供客户的增删改查、搜索、筛选、统计等功能
    """
    permission_classes = [IsAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'type', 'value_level', 'company_size', 'is_deleted']
    search_fields = ['name', 'primary_contact_name', 'primary_contact_phone', 'primary_contact_email']
    ordering_fields = ['name', 'created_at', 'updated_at', 'value_level']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """
        根据不同的操作返回不同的序列化器
        """
        if self.action == 'list':
            return CustomerListSerializer
        elif self.action == 'statistics':
            return CustomerStatisticsSerializer
        elif self.action == 'bulk_create':
            return BulkCustomerCreateSerializer
        elif self.action == 'bulk_update':
            return BulkCustomerUpdateSerializer
        return CustomerSerializer
    
    def get_queryset(self):
        """
        获取客户查询集，默认不返回已删除的客户，并且根据当前租户进行过滤
        """
        queryset = Customer.objects.all()  # 使用BaseModel的TenantManager自动过滤租户
        
        # 默认不显示已删除客户，除非明确要求
        show_deleted = self.request.query_params.get('show_deleted', 'false').lower() == 'true'
        if not show_deleted:
            queryset = queryset.filter(is_deleted=False)
        
        return queryset
    
    def perform_create(self, serializer):
        """
        创建客户时记录创建者和设置租户
        """
        # 从请求上下文获取当前租户
        tenant = self.request.tenant
        serializer.save(created_by=self.request.user.username, tenant=tenant)
    
    def perform_update(self, serializer):
        """
        更新客户时记录更新者
        """
        serializer.save(updated_by=self.request.user.username)
    
    def perform_destroy(self, instance):
        """
        软删除客户
        """
        instance.soft_delete()
    
    @extend_schema(
        summary="搜索客户",
        description="根据关键词搜索客户信息",
        tags=["客户管理"],
        parameters=[
            OpenApiParameter(name="q", description="搜索关键词", required=True, type=str),
        ],
        responses={200: CustomerListSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='search')
    def search(self, request):
        """
        搜索客户
        """
        q = request.query_params.get('q', '')
        if not q:
            return Response({"error": "请提供搜索关键词"}, status=status.HTTP_400_BAD_REQUEST)
        
        queryset = self.get_queryset().filter(
            Q(name__icontains=q) |
            Q(primary_contact_name__icontains=q) |
            Q(primary_contact_phone__icontains=q) |
            Q(primary_contact_email__icontains=q) |
            Q(business_license_number__icontains=q) |
            Q(tax_identification_number__icontains=q)
        )
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @extend_schema(
        summary="客户统计",
        description="获取客户统计数据",
        tags=["客户管理"],
        responses={200: CustomerStatisticsSerializer()}
    )
    @action(detail=False, methods=['get'], url_path='statistics')
    def statistics(self, request):
        """
        获取客户统计数据
        """
        queryset = self.get_queryset()
        
        # 按状态统计
        total_count = queryset.count()
        active_count = queryset.filter(status='active').count()
        inactive_count = queryset.filter(status='inactive').count()
        potential_count = queryset.filter(status='potential').count()
        lost_count = queryset.filter(status='lost').count()
        
        # 按类型统计
        type_stats = dict(queryset.values_list('type').annotate(count=Count('id')).values_list('type', 'count'))
        
        # 按价值等级统计
        value_level_stats = dict(queryset.values_list('value_level').annotate(count=Count('id')).values_list('value_level', 'count'))
        
        # 按公司规模统计
        company_size_stats = dict(queryset.values_list('company_size').annotate(count=Count('id')).values_list('company_size', 'count'))
        
        statistics = {
            'total_count': total_count,
            'active_count': active_count,
            'inactive_count': inactive_count,
            'potential_count': potential_count,
            'lost_count': lost_count,
            'by_type': type_stats,
            'by_value_level': value_level_stats,
            'by_company_size': company_size_stats
        }
        
        serializer = self.get_serializer(statistics)
        return Response(serializer.data)
    
    @extend_schema(
        summary="批量创建客户",
        description="批量创建多个客户记录",
        tags=["客户管理"],
        request=BulkCustomerCreateSerializer,
        responses={201: CustomerSerializer(many=True)}
    )
    @action(detail=False, methods=['post'], url_path='bulk-create')
    def bulk_create(self, request):
        """
        批量创建客户
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.save()
        
        # 返回创建的客户
        response_serializer = CustomerSerializer(result['customers'], many=True)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @extend_schema(
        summary="批量更新客户",
        description="批量更新多个客户记录",
        tags=["客户管理"],
        request=BulkCustomerUpdateSerializer,
        responses={200: CustomerSerializer(many=True)}
    )
    @action(detail=False, methods=['post'], url_path='bulk-update')
    def bulk_update(self, request):
        """
        批量更新客户
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = serializer.update(None, serializer.validated_data)
        
        # 返回更新的客户
        response_serializer = CustomerSerializer(result['customers'], many=True)
        return Response(response_serializer.data)
    
    @extend_schema(
        summary="批量删除客户",
        description="批量删除多个客户记录（软删除）",
        tags=["客户管理"],
        request={"application/json": {"type": "object", "properties": {"ids": {"type": "array", "items": {"type": "integer"}}}}},
        responses={204: None}
    )
    @action(detail=False, methods=['post'], url_path='bulk-delete')
    def bulk_delete(self, request):
        """
        批量删除客户
        """
        ids = request.data.get('ids', [])
        if not ids:
            return Response({"error": "请提供要删除的客户ID列表"}, status=status.HTTP_400_BAD_REQUEST)
        
        customers = Customer.objects.filter(id__in=ids)
        for customer in customers:
            customer.soft_delete()
        
        return Response(status=status.HTTP_204_NO_CONTENT) 