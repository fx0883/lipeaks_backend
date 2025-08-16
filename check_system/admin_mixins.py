"""
Check_System Admin Mixins
为打卡系统提供租户过滤功能
"""
from common.admin_mixins import BaseTenantFilterMixin


class CheckSystemAdminMixin(BaseTenantFilterMixin):
    """
    Check_System专用的Admin Mixin
    继承BaseTenantFilterMixin并设置自定义模板
    """
    change_list_template = 'admin/check_system/change_list.html'
