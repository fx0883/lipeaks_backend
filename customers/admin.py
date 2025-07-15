from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import Customer, CustomerMemberRelation, CustomerTenantRelation

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'value_level', 'status', 'primary_contact_name', 
                   'primary_contact_phone', 'industry_type', 'company_size', 'tenant_relations_count', 'created_at')
    list_filter = ('type', 'value_level', 'status', 'company_size', 'is_deleted', 'tenant')
    search_fields = ('name', 'business_license_number', 'primary_contact_name', 'primary_contact_phone')
    # date_hierarchy = 'created_at'  # 暂时注释掉此行，避免MySQL时区问题
    readonly_fields = ('created_at', 'updated_at', 'tenant_relations_display')
    
    fieldsets = (
        (_('基本信息'), {
            'fields': ('name', 'type', 'value_level', 'status', 'source', 'tenant')
        }),
        (_('公司信息'), {
            'fields': ('business_license_number', 'tax_identification_number', 'registered_capital',
                      'legal_representative', 'registered_address', 'business_address', 
                      'business_scope', 'industry_type', 'company_size', 'establishment_date', 'website'),
            'classes': ('collapse',),
            'description': _('仅适用于公司类型的客户')
        }),
        (_('联系信息'), {
            'fields': ('primary_contact_name', 'primary_contact_phone', 'primary_contact_email')
        }),
        (_('租户关系'), {
            'fields': ('tenant_relations_display',),
        }),
        (_('财务信息'), {
            'fields': ('bank_name', 'bank_account', 'credit_rating', 'payment_terms'),
            'classes': ('collapse',)
        }),
        (_('其他信息'), {
            'fields': ('special_requirements', 'notes', 'is_deleted')
        }),
        (_('审计信息'), {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        # 记录创建者和更新者
        if not change:  # 新建对象
            obj.created_by = request.user.username
        obj.updated_by = request.user.username
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        # 默认不显示已删除的客户
        return super().get_queryset(request).filter(is_deleted=False)
    
    def tenant_relations_count(self, obj):
        """显示客户的租户关系数量"""
        count = obj.tenant_relations.count()
        if count > 0:
            return format_html(
                '<a href="{}?customer__id__exact={}">{}</a>',
                '/admin/customers/customertenantrelation/',
                obj.id,
                count
            )
        return count
    tenant_relations_count.short_description = _('租户关系数')
    
    def tenant_relations_display(self, obj):
        """在详情页显示客户的租户关系列表"""
        relations = obj.tenant_relations.all()
        if not relations:
            return _('无租户关系')
        
        html = '<table style="width:100%"><tr><th>租户</th><th>关系类型</th><th>主要关系</th><th>合同编号</th><th>开始日期</th><th>结束日期</th></tr>'
        for relation in relations:
            html += f'<tr><td>{relation.tenant.name}</td><td>{relation.get_relation_type_display()}</td><td>{"是" if relation.is_primary else "否"}</td><td>{relation.contract_number or "-"}</td><td>{relation.start_date or "-"}</td><td>{relation.end_date or "长期"}</td></tr>'
        html += '</table>'
        return format_html(html)
    tenant_relations_display.short_description = _('租户关系')

@admin.register(CustomerMemberRelation)
class CustomerMemberRelationAdmin(admin.ModelAdmin):
    list_display = ('customer', 'member', 'role', 'is_primary', 'remarks', 'created_at')
    list_filter = ('is_primary', 'customer', 'role', 'tenant')
    search_fields = ('customer__name', 'member__username', 'role', 'remarks')
    raw_id_fields = ('customer', 'member')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('customer', 'member', 'tenant')
        }),
        (_('关系信息'), {
            'fields': ('role', 'is_primary', 'remarks')
        }),
        (_('审计信息'), {
            'fields': ('created_at', 'updated_at', 'is_deleted'),
            'classes': ('collapse',)
        }),
    )

@admin.register(CustomerTenantRelation)
class CustomerTenantRelationAdmin(admin.ModelAdmin):
    list_display = ('customer', 'tenant', 'relation_type', 'is_primary', 'contract_number', 'start_date', 'end_date', 'created_at')
    list_filter = ('relation_type', 'is_primary', 'customer', 'tenant', 'is_deleted')
    search_fields = ('customer__name', 'tenant__name', 'contract_number', 'description')
    raw_id_fields = ('customer', 'tenant')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('customer', 'tenant')
        }),
        (_('关系信息'), {
            'fields': ('relation_type', 'is_primary', 'contract_number', 'start_date', 'end_date')
        }),
        (_('详细信息'), {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
        (_('审计信息'), {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by', 'is_deleted'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        # 记录创建者和更新者
        if not change:  # 新建对象
            obj.created_by = request.user.username
        obj.updated_by = request.user.username
        super().save_model(request, obj, form, change)
