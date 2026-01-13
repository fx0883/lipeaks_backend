"""
客户-租户关系视图
"""
import logging
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from common.permissions import IsAdminUser, IsSuperAdminUser
from common.viewsets import TenantModelViewSet
from customers.models import Customer, CustomerTenantRelation
from customers.serializers import CustomerTenantRelationSerializer, CustomerTenantRelationDetailSerializer

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary="获取客户的租户关系列表",
        description="获取指定客户的所有租户关系",
        tags=["客户-租户关系"],
        parameters=[
            OpenApiParameter(name="customer_id", description="客户ID", required=False, type=int),
            OpenApiParameter(name="tenant_id", description="租户ID", required=False, type=int),
            OpenApiParameter(name="relation_type", description="关系类型", required=False, type=str),
        ]
    ),
    retrieve=extend_schema(
        summary="获取客户-租户关系详情",
        description="获取指定ID的客户-租户关系详情",
        tags=["客户-租户关系"]
    ),
    create=extend_schema(
        summary="创建客户-租户关系",
        description="为客户添加新的租户关系",
        tags=["客户-租户关系"]
    ),
    update=extend_schema(
        summary="更新客户-租户关系",
        description="更新指定ID的客户-租户关系",
        tags=["客户-租户关系"]
    ),
    partial_update=extend_schema(
        summary="部分更新客户-租户关系",
        description="部分更新指定ID的客户-租户关系",
        tags=["客户-租户关系"]
    ),
    destroy=extend_schema(
        summary="删除客户-租户关系",
        description="删除指定ID的客户-租户关系",
        tags=["客户-租户关系"]
    ),
)
class CustomerTenantRelationViewSet(TenantModelViewSet):
    """
    客户-租户关系视图集
    
    继承TenantModelViewSet自动处理租户过滤、设置和验证
    
    提供客户与租户关系的管理功能
    """
    queryset = CustomerTenantRelation.objects.all()
    permission_classes = [IsAdminUser]
    
    def get_serializer_class(self):
        """
        根据不同的操作返回不同的序列化器
        """
        if self.action == 'list' or self.action == 'retrieve':
            return CustomerTenantRelationDetailSerializer
        return CustomerTenantRelationSerializer
    
    def get_queryset(self):
        """
        获取查询集，TenantModelViewSet已经处理租户过滤
        可以按客户ID、租户ID和关系类型过滤
        """
        queryset = super().get_queryset()  # 租户过滤已处理
        
        # 过滤条件
        customer_id = self.request.query_params.get('customer_id')
        tenant_id = self.request.query_params.get('tenant_id')
        relation_type = self.request.query_params.get('relation_type')
        
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        
        if tenant_id:
            queryset = queryset.filter(tenant_id=tenant_id)
        
        if relation_type:
            queryset = queryset.filter(relation_type=relation_type)
            
        # 默认不显示已删除关系
        show_deleted = self.request.query_params.get('show_deleted', 'false').lower() == 'true'
        if not show_deleted:
            queryset = queryset.filter(is_deleted=False)
        
        return queryset
    
    def perform_create(self, serializer):
        """
        创建关系时记录创建者和设置租户
        """
        # 从请求上下文获取current租户
        tenant = self.request.user.tenant
        serializer.save(created_by=self.request.user.username, tenant=tenant)
    
    def perform_update(self, serializer):
        """
        更新关系时记录更新者
        """
        serializer.save(updated_by=self.request.user.username)
    
    @extend_schema(
        summary="设置主要租户关系",
        description="将指定的租户关系设置为客户的主要租户关系",
        tags=["客户-租户关系"],
        responses={200: CustomerTenantRelationDetailSerializer()}
    )
    @action(detail=True, methods=['post'], url_path='set-primary')
    def set_primary(self, request, pk=None):
        """
        设置主要租户关系
        """
        relation = self.get_object()
        relation.is_primary = True
        relation.save()  # 保存时会自动处理其他同类型关系的主要状态
        
        serializer = CustomerTenantRelationDetailSerializer(relation)
        return Response(serializer.data)
    
    @extend_schema(
        summary="获取客户的主要租户关系",
        description="获取指定客户的主要租户关系",
        tags=["客户-租户关系"],
        parameters=[
            OpenApiParameter(name="customer_id", description="客户ID", required=True, type=int),
            OpenApiParameter(name="relation_type", description="关系类型", required=False, type=str),
        ],
        responses={200: CustomerTenantRelationDetailSerializer()}
    )
    @action(detail=False, methods=['get'], url_path='primary')
    def primary(self, request):
        """
        获取客户的主要租户关系
        """
        customer_id = request.query_params.get('customer_id')
        relation_type = request.query_params.get('relation_type')
        
        if not customer_id:
            return Response({"error": "请提供客户ID"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 获取客户对象
            customer = Customer.objects.get(id=customer_id)
            
            # 获取主要租户关系
            relation = customer.get_primary_tenant_relation(relation_type)
            
            if relation:
                serializer = CustomerTenantRelationDetailSerializer(relation)
                return Response(serializer.data)
            else:
                return Response({"error": "未找到主要租户关系"}, status=status.HTTP_404_NOT_FOUND)
        except Customer.DoesNotExist:
            return Response({"error": "客户不存在"}, status=status.HTTP_404_NOT_FOUND)
    
    @extend_schema(
        summary="获取客户与租户的关系",
        description="获取特定客户与租户之间的关系",
        tags=["客户-租户关系"],
        parameters=[
            OpenApiParameter(name="customer_id", description="客户ID", required=True, type=int),
            OpenApiParameter(name="tenant_id", description="租户ID", required=True, type=int),
        ],
        responses={200: CustomerTenantRelationDetailSerializer(many=True)}
    )
    @action(detail=False, methods=['get'], url_path='between')
    def between(self, request):
        """
        获取客户与租户之间的关系
        """
        customer_id = request.query_params.get('customer_id')
        tenant_id = request.query_params.get('tenant_id')
        
        if not customer_id or not tenant_id:
            return Response({"error": "请提供客户ID和租户ID"}, status=status.HTTP_400_BAD_REQUEST)
        
        relations = CustomerTenantRelation.objects.filter(
            customer_id=customer_id,
            tenant_id=tenant_id
        )
        
        serializer = CustomerTenantRelationDetailSerializer(relations, many=True)
        return Response(serializer.data) 