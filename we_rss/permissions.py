from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied

from users.models import Member


def get_we_rss_tenant(request):
    user = getattr(request, "user", None)
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
