from we_rss.permissions import get_we_rss_tenant


def tenant_queryset(queryset, request):
    return queryset.filter(tenant=get_we_rss_tenant(request))


def tenant_write_kwargs(request, **kwargs):
    return {
        "tenant": get_we_rss_tenant(request),
        **kwargs,
    }
