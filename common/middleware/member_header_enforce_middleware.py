"""
MemberHeaderEnforceMiddleware

Purpose:
- Enforce X-Tenant-ID presence for member/anonymous on CMS paths
- Forbid X-Tenant-ID for admin/super-admin on all CMS requests
- Map errors to fixed Chinese messages via custom exceptions (4001/4003)

Notes:
- Should be placed BEFORE TenantMiddleware in MIDDLEWARE so that invalid headers are rejected early.
- Does not set tenant context; it only validates header policy and roles.
"""
from __future__ import annotations

import logging
from typing import Optional

from django.http import HttpRequest
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

from common.utils.tenant_header import get_header_tenant_id, require_member_header_match
from common.exceptions import (
    TenantHeaderInvalidOrMissing,
)

logger = logging.getLogger(__name__)


class MemberHeaderEnforceMiddleware(MiddlewareMixin):
    API_PREFIX = "/api/v1/"

    def process_request(self, request: HttpRequest):
        # feature flag gating
        if not getattr(settings, "FEATURE_ENFORCE_TENANT_HEADER_FOR_MEMBER", True):
            return None
        path = getattr(request, "path", "") or ""
        if not path.startswith(self.API_PREFIX):
            return None

        user = getattr(request, "user", None)
        is_authenticated = getattr(user, "is_authenticated", False)
        is_super_admin = bool(is_authenticated and getattr(request, "auth_type", None) == "jwt" and getattr(user, "is_super_admin", False))
        is_tenant_admin = bool(is_authenticated and getattr(user, "is_admin", False) and not is_super_admin)

        header_tid_present = get_header_tenant_id(request) is not None

        # Admin and Super Admin: header is forbidden on CMS
        if is_super_admin or is_tenant_admin:
            if header_tid_present:
                logger.warning("Admin/SuperAdmin sent X-Tenant-ID on CMS path, forbidden.")
                raise TenantHeaderInvalidOrMissing()
            # Admin default tenant or SA all-tenant behavior is handled by downstream logic
            return None

        # Member or Anonymous on CMS: header required, and for members it must match
        # This will also log ignored query/body tenant_id when member request
        require_member_header_match(request)
        return None
