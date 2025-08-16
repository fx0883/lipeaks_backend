"""
CMS Admin Mixins
为CMS系统提供租户过滤功能
"""
from common.admin_mixins import BaseTenantFilterMixin


class CMSAdminMixin(BaseTenantFilterMixin):
    """
    CMS专用的Admin Mixin
    继承BaseTenantFilterMixin并设置自定义模板
    """
    change_list_template = 'admin/cms/change_list.html'
