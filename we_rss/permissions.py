from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied

from users.models import Member


def get_we_rss_tenant(request):
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        raise PermissionDenied("Authentication required.")

    # 超级管理员与后台管理人员允许访问
    if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
        header_tid = request.headers.get("X-Tenant-ID") or request.query_params.get("tenant_id")
        from tenants.models import Tenant
        if header_tid:
            t = Tenant.objects.filter(id=header_tid, is_deleted=False).first()
            if t:
                return t
        default_t = getattr(user, "tenant", None) or Tenant.objects.filter(is_deleted=False).first()
        if default_t:
            return default_t
        raise PermissionDenied("No active tenant found.")

    if not isinstance(user, Member):
        raise PermissionDenied("Only members can access we_rss.")

    tenant = getattr(user, "tenant", None)
    if tenant is None:
        raise PermissionDenied("Member must belong to a tenant.")

    return tenant


class IsTenantMemberForWeRss(BasePermission):
    message = "Only members with a tenant can access we_rss."

    def has_permission(self, request, view):
        try:
            get_we_rss_tenant(request)
        except PermissionDenied as exc:
            self.message = str(exc.detail)
            return False

        return True
