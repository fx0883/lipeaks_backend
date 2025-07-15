"""
租户视角的客户视图
"""
import logging
from django.db.models import Count, Q
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from common.permissions import IsAdmin, IsTenantAdmin
from customers.models import Customer, CustomerTenantRelation
from customers.serializers import (
    CustomerSerializer, CustomerListSerializer, 
    CustomerTenantRelationSerializer, CustomerTenantRelationDetailSerializer,
    CustomerStatisticsSerializer
)

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary="获取租户关联的客户列表",
        description="获取与指定租户有关系的所有客户",
        tags=["租户-客户关系"],
        parameters=[
            OpenApiParameter(name="tenant_id", description="租户ID", required=True, type=int),
            OpenApiParameter(name="relation_type", description="关系类型", required=False, type=str),
            OpenApiParameter(name="status", description="客户状态", required=False, type=str),
        ]
    ),
    retrieve=extend_schema(
        summary="获取租户视角下的客户详情",
        description="获取指定租户视角下的客户详情",
        tags=["租户-客户关系"]
    ),
)
class TenantCustomerViewSet(viewsets.ReadOnlyModelViewSet):
    """
    租户视角的客户视图集
    
    提供租户视角下的客户查询功能
    """
    permission_classes = [IsAdmin | IsTenantAdmin]
    
    def get_serializer_class(self):
        """
        根据不同的操作返回不同的序列化器
        """
        if self.action == 'list':
            return CustomerListSerializer
        elif self.action == 'statistics':
            return CustomerStatisticsSerializer
        elif self.action == 'relations':
            return CustomerTenantRelationDetailSerializer
        return CustomerSerializer
    
    def get_queryset(self):
        """
        获取与指定租户有关系的客户
        """
        tenant_id = self.request.query_params.get('tenant_id')
        if not tenant_id:
            return Customer.objects.none()
        
        # 获取关系类型过滤条件
        relation_type = self.request.query_params.get('relation_type')
        
        # 获取客户状态过滤条件
        status = self.request.query_params.get('status')
        
        # 构建查询
        queryset = Customer.objects.filter(
            tenant_relations__tenant_id=tenant_id,
            is_deleted=False
        )
        
        # 应用关系类型过滤
        if relation_type:
            queryset = queryset.filter(tenant_relations__relation_type=relation_type)
        
        # 应用客户状态过滤
        if status:
            queryset = queryset.filter(status=status)
        
        # 去重
        return queryset.distinct()
    
    def get_object(self):
        """
        获取租户视角下的客户详情
        """
        tenant_id = self.request.query_params.get('tenant_id')
        if not tenant_id:
            return Response({"error": "请提供租户ID"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取客户对象
        customer = super().get_object()
        
        # 确保客户与租户有关系
        if not CustomerTenantRelation.objects.filter(customer=customer, tenant_id=tenant_id).exists():
            return Response({"error": "该客户与租户没有关系"}, status=status.HTTP_404_NOT_FOUND)
        
        return customer
    
    @extend_schema(
        summary="获取租户的客户统计数据",
        description="获取指定租户关联的客户统计数据",
        tags=["租户-客户关系"],
        parameters=[
            OpenApiParameter(name="tenant_id", description="租户ID", required=True, type=int),
        ],
        responses={200: CustomerStatisticsSerializer()}
    )
    @action(detail=False, methods=['get'], url_path='statistics')
    def statistics(self, request):
        """
        获取租户的客户统计数据
        """
        tenant_id = request.query_params.get('tenant_id')
        if not tenant_id:
            return Response({"error": "请提供租户ID"}, status=status.HTTP_400_BAD_REQUEST)
        
        # 获取与租户有关系的客户
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
        summary="获取客户与租户的关系",
        description="获取指定客户与租户之间的所有关系",
        tags=["租户-客户关系"],
        parameters=[
            OpenApiParameter(name="tenant_id", description="租户ID", required=True, type=int),
        ],
        responses={200: CustomerTenantRelationDetailSerializer(many=True)}
    )
    @action(detail=True, methods=['get'], url_path='relations')
    def relations(self, request, pk=None):
        """
        获取客户与租户之间的关系
        """
        tenant_id = request.query_params.get('tenant_id')
        if not tenant_id:
            return Response({"error": "请提供租户ID"}, status=status.HTTP_400_BAD_REQUEST)
        
        customer = self.get_object()
        
        relations = CustomerTenantRelation.objects.filter(
            customer=customer,
            tenant_id=tenant_id
        )
        
        serializer = self.get_serializer(relations, many=True)
        return Response(serializer.data)