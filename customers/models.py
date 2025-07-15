from django.db import models
from django.utils.translation import gettext_lazy as _
import datetime
from common.models import BaseModel

class Customer(BaseModel):
    """
    客户实体类，代表客户公司或组织
    """
    # 客户类型选项
    TYPE_CHOICES = [
        ('enterprise', '公司'),
        ('individual', '个人'),
        ('government', '政府机构'),
        ('nonprofit', '非营利组织'),
        ('education', '教育机构'),
    ]
    
    # 价值等级选项
    VALUE_LEVEL_CHOICES = [
        ('platinum', '铂金'),
        ('gold', '黄金'),
        ('silver', '白银'),
        ('bronze', '青铜'),
    ]
    
    # 公司规模选项
    COMPANY_SIZE_CHOICES = [
        ('micro', '微型'),
        ('small', '小型'),
        ('medium', '中型'),
        ('large', '大型'),
    ]
    
    # 基本信息
    name = models.CharField(_("客户名称"), max_length=100)
    type = models.CharField(_("客户类型"), max_length=20, choices=TYPE_CHOICES, default='company')
    value_level = models.CharField(_("价值等级"), max_length=20, choices=VALUE_LEVEL_CHOICES, default='normal')
    status = models.CharField(_("状态"), max_length=20, choices=[
        ('active', '活跃'),
        ('inactive', '非活跃'),
        ('potential', '潜在'),
        ('lost', '流失'),
    ], default='active')
    
    # 公司信息字段（适用于type=公司）
    business_license_number = models.CharField(_("营业执照号"), max_length=100, blank=True, null=True)
    tax_identification_number = models.CharField(_("纳税人识别号"), max_length=100, blank=True, null=True)
    registered_capital = models.CharField(_("注册资本"), max_length=50, blank=True, null=True)
    legal_representative = models.CharField(_("法定代表人"), max_length=50, blank=True, null=True)
    registered_address = models.TextField(_("注册地址"), blank=True, null=True)
    business_address = models.TextField(_("经营地址"), blank=True, null=True)
    business_scope = models.TextField(_("经营范围"), blank=True, null=True)
    industry_type = models.CharField(_("行业类型"), max_length=50, blank=True, null=True)
    company_size = models.CharField(_("公司规模"), max_length=20, choices=COMPANY_SIZE_CHOICES, blank=True, null=True)
    establishment_date = models.DateField(_("成立日期"), blank=True, null=True)
    website = models.URLField(_("公司网站"), blank=True, null=True)
    
    # 联系信息
    primary_contact_name = models.CharField(_("主要联系人姓名"), max_length=50, blank=True, null=True)
    primary_contact_phone = models.CharField(_("主要联系人电话"), max_length=20, blank=True, null=True)
    primary_contact_email = models.EmailField(_("主要联系人邮箱"), blank=True, null=True)
    
    # 财务信息
    bank_name = models.CharField(_("开户银行"), max_length=100, blank=True, null=True)
    bank_account = models.CharField(_("银行账号"), max_length=100, blank=True, null=True)
    credit_rating = models.CharField(_("信用等级"), max_length=20, blank=True, null=True)
    payment_terms = models.CharField(_("付款条件"), max_length=200, blank=True, null=True)
    
    # 其他信息
    special_requirements = models.TextField(_("特殊要求"), blank=True, null=True)
    notes = models.TextField(_("备注信息"), blank=True, null=True)
    source = models.CharField(_("客户来源"), max_length=50, blank=True, null=True)
    
    # 审计字段 (created_at, updated_at, is_deleted由BaseModel提供)
    created_by = models.CharField(_("创建者"), max_length=50, blank=True, null=True)
    updated_by = models.CharField(_("更新者"), max_length=50, blank=True, null=True)
    
    class Meta:
        verbose_name = _('客户')
        verbose_name_plural = _('客户')
        db_table = 'customer'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
    
    def soft_delete(self):
        """
        软删除客户，复写BaseModel的方法
        """
        self.is_deleted = True
        self.status = 'inactive'
        self.save(update_fields=['is_deleted', 'status', 'updated_at'])
        return self
    
    def get_primary_tenant_relation(self, relation_type=None):
        """
        获取客户的主要租户关系
        
        Args:
            relation_type: 可选，指定关系类型，如果不指定则返回任意类型的主要关系
            
        Returns:
            CustomerTenantRelation对象或None
        """
        try:
            if relation_type:
                return self.tenant_relations.filter(
                    is_primary=True,
                    relation_type=relation_type
                ).first()
            else:
                return self.tenant_relations.filter(is_primary=True).first()
        except Exception:
            return None
    
    def get_tenant_relations_by_type(self, relation_type):
        """
        获取客户指定类型的所有租户关系
        
        Args:
            relation_type: 关系类型
            
        Returns:
            QuerySet对象，包含所有指定类型的租户关系
        """
        return self.tenant_relations.filter(relation_type=relation_type)
    
    def get_all_tenants(self):
        """
        获取与客户有关系的所有租户
        
        Returns:
            QuerySet对象，包含所有相关租户
        """
        from tenants.models import Tenant
        tenant_ids = self.tenant_relations.values_list('tenant_id', flat=True)
        return Tenant.objects.filter(id__in=tenant_ids)


class CustomerMemberRelation(BaseModel):
    """
    客户-联系人关联表，建立客户与Member之间的多对多关系
    """
    # 关联字段
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        related_name='member_relations',
        verbose_name=_("客户")
    )
    member = models.ForeignKey(
        'users.Member',
        on_delete=models.CASCADE,
        related_name='customer_relations',
        verbose_name=_("联系人")
    )
    
    # 关系信息
    role = models.CharField(_("角色"), max_length=50, blank=True, null=True, help_text=_("联系人在客户中的角色"))
    is_primary = models.BooleanField(_("主要联系人"), default=False, help_text=_("是否为该客户的主要联系人"))
    remarks = models.TextField(_("备注"), blank=True, null=True, help_text=_("关于该联系人与客户关系的补充说明"))
    
    # 审计字段由BaseModel提供
    
    class Meta:
        verbose_name = _('客户-联系人关系')
        verbose_name_plural = _('客户-联系人关系')
        db_table = 'customer_member_relation'
        unique_together = [['customer', 'member']]  # 确保一个联系人在一个客户中只有一条记录
        ordering = ['-is_primary', '-created_at']
    
    def __str__(self):
        return f"{self.customer.name} - {self.member.username} ({self.role if self.role else '无角色'})"
    
    def save(self, *args, **kwargs):
        # 如果设置为主要联系人，将同一客户的其他联系人设为非主要
        if self.is_primary:
            CustomerMemberRelation.objects.filter(
                customer=self.customer, 
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class CustomerTenantRelation(BaseModel):
    """
    客户-租户关联表，建立客户与Tenant之间的多对多关系
    """
    # 关系类型选项
    RELATION_TYPE_CHOICES = [
        ('provider', '服务提供方'),
        ('client', '客户方'),
        ('partner', '合作伙伴'),
        ('distributor', '分销商'),
        ('supplier', '供应商'),
        ('other', '其他'),
    ]
    
    # 关联字段
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.CASCADE,
        related_name='tenant_relations',
        verbose_name=_("客户")
    )
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='customer_relations',
        verbose_name=_("租户")
    )
    
    # 关系信息
    relation_type = models.CharField(
        _("关系类型"), 
        max_length=20, 
        choices=RELATION_TYPE_CHOICES,
        default='client',
        help_text=_("客户与租户之间的关系类型")
    )
    is_primary = models.BooleanField(
        _("主要关系"), 
        default=False, 
        help_text=_("是否为该客户的主要租户关系")
    )
    contract_number = models.CharField(
        _("合同编号"), 
        max_length=100, 
        blank=True, 
        null=True,
        help_text=_("相关合同编号，如有")
    )
    start_date = models.DateField(
        _("关系开始日期"), 
        blank=True, 
        null=True
    )
    end_date = models.DateField(
        _("关系结束日期"), 
        blank=True, 
        null=True,
        help_text=_("留空表示长期有效")
    )
    description = models.TextField(
        _("关系描述"), 
        blank=True, 
        null=True,
        help_text=_("详细说明客户与租户之间的关系")
    )
    
    # 审计字段 (created_at, updated_at, is_deleted由BaseModel提供)
    created_by = models.CharField(_("创建者"), max_length=50, blank=True, null=True)
    updated_by = models.CharField(_("更新者"), max_length=50, blank=True, null=True)
    
    class Meta:
        verbose_name = _('客户-租户关系')
        verbose_name_plural = _('客户-租户关系')
        db_table = 'customer_tenant_relation'
        unique_together = [['customer', 'tenant', 'relation_type']]  # 确保一个客户与一个租户之间的特定关系类型只有一条记录
        ordering = ['-is_primary', '-created_at']
    
    def __str__(self):
        return f"{self.customer.name} - {self.tenant.name} ({self.get_relation_type_display()})"
    
    def save(self, *args, **kwargs):
        # 如果设置为主要关系，将同一客户的其他同类型关系设为非主要
        if self.is_primary:
            CustomerTenantRelation.objects.filter(
                customer=self.customer,
                relation_type=self.relation_type,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)
    
    def is_active(self):
        """
        判断关系是否处于活跃状态
        
        Returns:
            布尔值，指示关系是否活跃
        """
        today = datetime.date.today()
        
        # 如果没有开始日期，或者开始日期已过
        has_started = not self.start_date or self.start_date <= today
        
        # 如果没有结束日期，或者结束日期未到
        not_ended = not self.end_date or self.end_date >= today
        
        return has_started and not_ended
