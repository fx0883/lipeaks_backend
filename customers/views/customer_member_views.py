"""
客户-联系人关系视图
"""
import logging
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from common.permissions import IsAdmin, IsSuperAdmin
from customers.models import Customer, CustomerMemberRelation
from customers.serializers import CustomerMemberRelationSerializer, CustomerMemberRelationDetailSerializer
from users.models import Member
from users.serializers import MemberSerializer
from customers.serializers import CustomerListSerializer

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary="获取客户的联系人关系列表",
        description="获取指定客户的所有联系人关系",
        tags=["客户-联系人关系"],
        parameters=[
            OpenApiParameter(name="customer_id", description="客户ID", required=True, type=int),
        ]
    ),
    retrieve=extend_schema(
        summary="获取客户-联系人关系详情",
        description="获取指定ID的客户-联系人关系详情",
        tags=["客户-联系人关系"]
    ),
    create=extend_schema(
        summary="创建客户-联系人关系",
        description="为客户添加新的联系人关系",
        tags=["客户-联系人关系"]
    ),
    update=extend_schema(
        summary="更新客户-联系人关系",
        description="更新指定ID的客户-联系人关系",
        tags=["客户-联系人关系"]
    ),
    partial_update=extend_schema(
        summary="部分更新客户-联系人关系",
        description="部分更新指定ID的客户-联系人关系",
        tags=["客户-联系人关系"]
    ),
    destroy=extend_schema(
        summary="删除客户-联系人关系",
        description="删除指定ID的客户-联系人关系",
        tags=["客户-联系人关系"]
    ),
)
class CustomerMemberRelationViewSet(viewsets.ModelViewSet):
    """
    客户-联系人关系视图集
    
    提供客户与联系人关系的管理功能
    """
    permission_classes = [IsAdmin]
    
    def get_serializer_class(self):
        """
        根据不同的操作返回不同的序列化器
        """
        if self.action == 'list' or self.action == 'retrieve':
            return CustomerMemberRelationDetailSerializer
        return CustomerMemberRelationSerializer
    
    def get_queryset(self):
        """
        获取查询集，可以按客户ID过滤，并且根据当前租户进行过滤
        """
        queryset = CustomerMemberRelation.objects.all()  # 使用BaseModel的TenantManager自动过滤租户
        
        # 如果提供了customer_id参数，则按客户ID过滤
        customer_id = self.request.query_params.get('customer_id')
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
            
        # 默认不显示已删除关系
        show_deleted = self.request.query_params.get('show_deleted', 'false').lower() == 'true'
        if not show_deleted:
            queryset = queryset.filter(is_deleted=False)
        
        return queryset
    
    def perform_create(self, serializer):
        """
        创建关系时设置租户
        """
        # 从请求上下文获取当前租户
        tenant = self.request.user.tenant
        serializer.save(tenant=tenant)
    
    @extend_schema(
        summary="设置主要联系人",
        description="将指定的联系人设置为客户的主要联系人",
        tags=["客户-联系人关系"],
        responses={200: CustomerMemberRelationDetailSerializer()}
    )
    @action(detail=True, methods=['post'], url_path='set-primary')
    def set_primary(self, request, pk=None):
        """
        设置主要联系人
        """
        relation = self.get_object()
        relation.is_primary = True
        relation.save()  # 保存时会自动处理其他联系人的主要状态
        
        serializer = CustomerMemberRelationDetailSerializer(relation)
        return Response(serializer.data)
    
    @extend_schema(
        summary="获取客户的主要联系人",
        description="获取指定客户的主要联系人",
        tags=["客户-联系人关系"],
        parameters=[
            OpenApiParameter(name="customer_id", description="客户ID", required=True, type=int),
        ],
        responses={200: CustomerMemberRelationDetailSerializer()}
    )
    @action(detail=False, methods=['get'], url_path='primary')
    def primary(self, request):
        """
        获取客户的主要联系人
        """
        customer_id = request.query_params.get('customer_id')
        if not customer_id:
            return Response({"error": "请提供客户ID"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            relation = CustomerMemberRelation.objects.get(customer_id=customer_id, is_primary=True)
            serializer = CustomerMemberRelationDetailSerializer(relation)
            return Response(serializer.data)
        except CustomerMemberRelation.DoesNotExist:
            return Response({"error": "未找到主要联系人"}, status=status.HTTP_404_NOT_FOUND)
            
    @extend_schema(
        summary="获取客户的所有联系人",
        description="获取指定客户ID下的所有联系人列表，同时包含联系人与客户的关系信息",
        tags=["客户-联系人关系"],
        parameters=[
            OpenApiParameter(name="customer_id", description="客户ID", required=True, type=int),
        ],
        responses={200: {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "username": {"type": "string"},
                    "email": {"type": "string", "format": "email"},
                    "phone": {"type": "string"},
                    "relation": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "role": {"type": "string"},
                            "is_primary": {"type": "boolean"},
                            "remarks": {"type": "string", "nullable": True},
                            "created_at": {"type": "string", "format": "date-time"},
                            "updated_at": {"type": "string", "format": "date-time"}
                        }
                    }
                }
            }
        }}
    )
    @action(detail=False, methods=['get'], url_path='customer-members')
    def customer_members(self, request):
        """
        获取客户的所有联系人，并附加联系人与客户的关系信息
        """
        customer_id = request.query_params.get('customer_id')
        if not customer_id:
            return Response({"error": "请提供客户ID"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 获取客户
            customer = Customer.objects.get(id=customer_id)
            
            # 获取与该客户关联的所有联系人关系
            relations = CustomerMemberRelation.objects.filter(customer=customer)
            
            # 创建结果列表
            result = []
            
            # 遍历关系，获取联系人信息并添加关系信息
            for relation in relations:
                member = relation.member
                member_data = MemberSerializer(member).data
                
                # 添加关系信息
                member_data['relation'] = {
                    'id': relation.id,
                    'role': relation.role,
                    'is_primary': relation.is_primary,
                    'remarks': relation.remarks,
                    'created_at': relation.created_at,
                    'updated_at': relation.updated_at
                }
                
                result.append(member_data)
            
            return Response(result)
        except Customer.DoesNotExist:
            return Response({"error": "客户不存在"}, status=status.HTTP_404_NOT_FOUND)
    
    @extend_schema(
        summary="获取联系人所属的所有客户",
        description="获取指定联系人ID所属的所有客户列表，同时包含客户与联系人的关系信息",
        tags=["客户-联系人关系"],
        parameters=[
            OpenApiParameter(name="member_id", description="联系人ID", required=True, type=int),
        ],
        responses={200: {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer"},
                    "name": {"type": "string"},
                    "type": {"type": "string"},
                    "value_level": {"type": "string"},
                    "status": {"type": "string"},
                    "relation": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "role": {"type": "string"},
                            "is_primary": {"type": "boolean"},
                            "remarks": {"type": "string", "nullable": True},
                            "created_at": {"type": "string", "format": "date-time"},
                            "updated_at": {"type": "string", "format": "date-time"}
                        }
                    }
                }
            }
        }}
    )
    @action(detail=False, methods=['get'], url_path='member-customers')
    def member_customers(self, request):
        """
        获取联系人所属的所有客户，并附加客户与联系人的关系信息
        """
        member_id = request.query_params.get('member_id')
        if not member_id:
            return Response({"error": "请提供联系人ID"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 获取联系人
            member = Member.objects.get(id=member_id)
            
            # 获取与该联系人关联的所有客户关系
            relations = CustomerMemberRelation.objects.filter(member=member)
            
            # 创建结果列表
            result = []
            
            # 遍历关系，获取客户信息并添加关系信息
            for relation in relations:
                customer = relation.customer
                customer_data = CustomerListSerializer(customer).data
                
                # 添加关系信息
                customer_data['relation'] = {
                    'id': relation.id,
                    'role': relation.role,
                    'is_primary': relation.is_primary,
                    'remarks': relation.remarks,
                    'created_at': relation.created_at,
                    'updated_at': relation.updated_at
                }
                
                result.append(customer_data)
            
            return Response(result)
        except Member.DoesNotExist:
            return Response({"error": "联系人不存在"}, status=status.HTTP_404_NOT_FOUND)
            
    @extend_schema(
        summary="删除客户的多个联系人关系",
        description="删除指定客户与多个联系人之间的关系",
        tags=["客户-联系人关系"],
        request={"application/json": {"type": "object", "properties": {
            "customer_id": {"type": "integer", "description": "客户ID"},
            "member_ids": {"type": "array", "items": {"type": "integer"}, "description": "联系人ID列表"}
        }, "required": ["customer_id", "member_ids"]}},
        responses={204: None}
    )
    @action(detail=False, methods=['post'], url_path='customer-members/delete')
    def delete_customer_members(self, request):
        """
        删除客户的多个联系人关系
        """
        customer_id = request.data.get('customer_id')
        member_ids = request.data.get('member_ids', [])
        
        if not customer_id:
            return Response({"error": "请提供客户ID"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not member_ids:
            return Response({"error": "请提供联系人ID列表"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 验证客户是否存在
            customer = Customer.objects.get(id=customer_id)
            
            # 删除关系
            deleted_count = CustomerMemberRelation.objects.filter(
                customer=customer,
                member_id__in=member_ids
            ).delete()[0]
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Customer.DoesNotExist:
            return Response({"error": "客户不存在"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"删除客户联系人关系时出错: {str(e)}")
            return Response({"error": "删除关系时发生错误"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    @extend_schema(
        summary="删除联系人的多个客户关系",
        description="删除指定联系人与多个客户之间的关系",
        tags=["客户-联系人关系"],
        request={"application/json": {"type": "object", "properties": {
            "member_id": {"type": "integer", "description": "联系人ID"},
            "customer_ids": {"type": "array", "items": {"type": "integer"}, "description": "客户ID列表"}
        }, "required": ["member_id", "customer_ids"]}},
        responses={204: None}
    )
    @action(detail=False, methods=['post'], url_path='member-customers/delete')
    def delete_member_customers(self, request):
        """
        删除联系人的多个客户关系
        """
        member_id = request.data.get('member_id')
        customer_ids = request.data.get('customer_ids', [])
        
        if not member_id:
            return Response({"error": "请提供联系人ID"}, status=status.HTTP_400_BAD_REQUEST)
        
        if not customer_ids:
            return Response({"error": "请提供客户ID列表"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 验证联系人是否存在
            member = Member.objects.get(id=member_id)
            
            # 删除关系
            deleted_count = CustomerMemberRelation.objects.filter(
                member=member,
                customer_id__in=customer_ids
            ).delete()[0]
            
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Member.DoesNotExist:
            return Response({"error": "联系人不存在"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"删除联系人客户关系时出错: {str(e)}")
            return Response({"error": "删除关系时发生错误"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 