"""
客户管理系统序列化器
"""
from rest_framework import serializers
from .models import Customer, CustomerMemberRelation, CustomerTenantRelation
from users.models import Member
from tenants.models import Tenant


class CustomerSerializer(serializers.ModelSerializer):
    """
    客户序列化器
    """
    class Meta:
        model = Customer
        fields = [
            'id', 'name', 'type', 'value_level', 'status',
            'business_license_number', 'tax_identification_number', 'registered_capital',
            'legal_representative', 'registered_address', 'business_address',
            'business_scope', 'industry_type', 'company_size', 'establishment_date',
            'website', 'primary_contact_name', 'primary_contact_phone',
            'primary_contact_email', 'bank_name', 'bank_account',
            'credit_rating', 'payment_terms', 'special_requirements',
            'notes', 'source', 'is_deleted', 'created_at', 'updated_at',
            'created_by', 'updated_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_name(self, value):
        """
        验证客户名称的唯一性
        """
        # 获取current实例（如果是更新操作）
        instance = getattr(self, 'instance', None)
        
        # 构建查询条件：名称相同且未删除的客户
        query = Customer.objects.filter(name=value, is_deleted=False)
        
        # 如果是更新操作，排除current实例
        if instance:
            query = query.exclude(pk=instance.pk)
        
        # 检查是否存在重名客户
        if query.exists():
            raise serializers.ValidationError("Customer name already exists, please use another name")
        
        return value


class CustomerListSerializer(serializers.ModelSerializer):
    """
    客户列表序列化器（简化版，用于列表展示）
    """
    class Meta:
        model = Customer
        fields = [
            'id', 'name', 'type', 'value_level', 'status',
            'primary_contact_name', 'primary_contact_phone',
            'industry_type', 'company_size', 'created_at'
        ]


class CustomerMemberRelationSerializer(serializers.ModelSerializer):
    """
    客户-联系人关系序列化器
    """
    customer_id = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(),
        source='customer'
    )
    member_id = serializers.PrimaryKeyRelatedField(
        queryset=Member.objects.all(),
        source='member'
    )
    
    class Meta:
        model = CustomerMemberRelation
        fields = ['id', 'customer_id', 'member_id', 'role', 'is_primary', 'remarks', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class CustomerMemberRelationDetailSerializer(serializers.ModelSerializer):
    """
    客户-联系人关系详情序列化器
    """
    customer_id = serializers.IntegerField(source='customer.id', read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    member_id = serializers.IntegerField(source='member.id', read_only=True)
    member_name = serializers.CharField(source='member.username', read_only=True)
    member_email = serializers.EmailField(source='member.email', read_only=True)
    member_phone = serializers.CharField(source='member.phone', read_only=True)
    
    class Meta:
        model = CustomerMemberRelation
        fields = [
            'id', 'customer_id', 'customer_name', 'member_id', 
            'member_name', 'member_email', 'member_phone',
            'role', 'is_primary', 'remarks', 'created_at', 'updated_at'
        ]


class CustomerTenantRelationSerializer(serializers.ModelSerializer):
    """
    客户-租户关系序列化器
    """
    customer_id = serializers.PrimaryKeyRelatedField(
        queryset=Customer.objects.all(),
        source='customer'
    )
    tenant_id = serializers.PrimaryKeyRelatedField(
        queryset=Tenant.objects.all(),
        source='tenant'
    )
    
    class Meta:
        model = CustomerTenantRelation
        fields = [
            'id', 'customer_id', 'tenant_id', 'relation_type', 
            'is_primary', 'contract_number', 'start_date', 'end_date', 
            'description', 'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        """
        验证关系数据
        """
        # 验证结束日期不早于开始日期
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError({"end_date": "End date cannot be earlier than start date"})
        
        return data


class CustomerTenantRelationDetailSerializer(serializers.ModelSerializer):
    """
    客户-租户关系详情序列化器
    """
    customer_id = serializers.IntegerField(source='customer.id', read_only=True)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    tenant_id = serializers.IntegerField(source='tenant.id', read_only=True)
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    relation_type_display = serializers.CharField(source='get_relation_type_display', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = CustomerTenantRelation
        fields = [
            'id', 'customer_id', 'customer_name', 'tenant_id', 'tenant_name',
            'relation_type', 'relation_type_display', 'is_primary', 
            'contract_number', 'start_date', 'end_date', 'description',
            'is_active', 'created_at', 'updated_at', 'created_by', 'updated_by'
        ]


class CustomerStatisticsSerializer(serializers.Serializer):
    """
    客户统计数据序列化器
    """
    total_count = serializers.IntegerField(help_text="客户总数")
    active_count = serializers.IntegerField(help_text="活跃客户数")
    inactive_count = serializers.IntegerField(help_text="非活跃客户数")
    potential_count = serializers.IntegerField(help_text="潜在客户数")
    lost_count = serializers.IntegerField(help_text="流失客户数")
    by_type = serializers.DictField(help_text="按类型统计", child=serializers.IntegerField())
    by_value_level = serializers.DictField(help_text="按价值等级统计", child=serializers.IntegerField())
    by_company_size = serializers.DictField(help_text="按公司规模统计", child=serializers.IntegerField())


class BulkCustomerCreateSerializer(serializers.Serializer):
    """
    批量创建客户的序列化器
    """
    customers = CustomerSerializer(many=True)
    
    def validate_customers(self, value):
        """
        验证批量创建的客户名称不重复
        """
        # 收集所有客户名称
        names = [customer_data.get('name') for customer_data in value]
        
        # 检查批量创建中是否有重复名称
        if len(names) != len(set(names)):
            raise serializers.ValidationError("Duplicate names found in batch customer creation")
        
        # 检查与数据库中已有客户是否重名
        existing_names = Customer.objects.filter(
            name__in=names, 
            is_deleted=False
        ).values_list('name', flat=True)
        
        if existing_names:
            duplicate_names = ", ".join(existing_names)
            raise serializers.ValidationError(f"The following customer names already exist: {duplicate_names}")
        
        return value
    
    def create(self, validated_data):
        customers_data = validated_data.get('customers')
        customers = []
        
        for customer_data in customers_data:
            customer = Customer.objects.create(**customer_data)
            customers.append(customer)
        
        return {'customers': customers}


class BulkCustomerUpdateSerializer(serializers.Serializer):
    """
    批量更新客户的序列化器
    """
    customers = serializers.ListField(
        child=serializers.DictField(
            child=serializers.Field(),
            allow_empty=False
        ),
        min_length=1
    )
    
    def validate_customers(self, value):
        """
        验证每个客户数据都包含id字段，并且名称不重复
        """
        # 验证每个客户数据都包含id字段
        for customer_data in value:
            if 'id' not in customer_data:
                raise serializers.ValidationError("Each customer data must contain id field")
        
        # 收集要更新的客户ID和名称
        name_id_map = {}
        for customer_data in value:
            if 'name' in customer_data:
                name_id_map[customer_data['name']] = customer_data['id']
        
        # 如果没有要更新的名称，直接返回
        if not name_id_map:
            return value
        
        # 检查批量更新中是否有重复名称
        if len(name_id_map) != len(set(name_id_map.keys())):
            raise serializers.ValidationError("Duplicate names found in batch customer update")
        
        # 检查与数据库中已有客户是否重名
        existing_customers = Customer.objects.filter(
            name__in=list(name_id_map.keys()), 
            is_deleted=False
        ).exclude(id__in=list(name_id_map.values()))
        
        if existing_customers.exists():
            duplicate_names = ", ".join(existing_customers.values_list('name', flat=True))
            raise serializers.ValidationError(f"The following customer names already exist: {duplicate_names}")
        
        return value
    
    def update(self, instance, validated_data):
        customers_data = validated_data.get('customers')
        updated_customers = []
        
        for customer_data in customers_data:
            customer_id = customer_data.pop('id')
            try:
                customer = Customer.objects.get(id=customer_id)
                for attr, value in customer_data.items():
                    setattr(customer, attr, value)
                customer.save()
                updated_customers.append(customer)
            except Customer.DoesNotExist:
                pass
        
        return {'customers': updated_customers} 