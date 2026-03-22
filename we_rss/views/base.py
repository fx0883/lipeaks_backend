from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from common.views import TenantApiView
from common.viewsets import TenantModelViewSet
from we_rss.permissions import IsTenantMemberForWeRss


class WeRssTenantContextMixin:
    permission_classes = [IsAuthenticated, IsTenantMemberForWeRss]
    get_tenant_id = TenantApiView.get_tenant_id
    verify_tenant_access = TenantApiView.verify_tenant_access

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        self.get_tenant_id()


class WeRssTenantApiView(WeRssTenantContextMixin, TenantApiView):
    pass


class WeRssTenantModelViewSet(WeRssTenantContextMixin, TenantModelViewSet):
    pagination_class = None


class WeRssTenantGenericViewSet(WeRssTenantContextMixin, viewsets.GenericViewSet):
    pagination_class = None
