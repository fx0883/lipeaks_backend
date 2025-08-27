"""
Tenant header utilities for enforcing X-Tenant-ID rules.

- get_header_tenant_id(request) -> Optional[int]
- require_member_header_match(request) -> None or raises APIException

Rules reflected here (for member/anonymous context use):
- Header is the single source of truth for tenant_id for members/anonymous
- Missing/invalid header -> 4001 "缺少或非法的租户ID"
- Mismatch with member's own tenant -> 4003 "租户不匹配，或者没有权限"
- Any tenant_id in query/body for member requests is ignored, but logged as Warning
"""
from __future__ import annotations

import logging
from typing import Optional

from django.http import HttpRequest

from common.exceptions import (
    TenantHeaderInvalidOrMissing,
    TenantMismatchOrNoPermission,
)

logger = logging.getLogger(__name__)

TENANT_HEADER = "X-Tenant-ID"


def _get_raw_header(request: HttpRequest) -> Optional[str]:
    # DRF/Django provide both .headers and .META entries
    if hasattr(request, "headers"):
        val = request.headers.get(TENANT_HEADER)
        if val is not None:
            return val
    # Fallback to WSGI meta key
    return request.META.get("HTTP_" + TENANT_HEADER.replace("-", "_"))


def get_header_tenant_id(request: HttpRequest) -> Optional[int]:
    raw = _get_raw_header(request)
    if raw is None:
        return None
    try:
        return int(str(raw).strip())
    except (TypeError, ValueError):
        logger.warning("Invalid X-Tenant-ID header value: %r", raw)
        return None


def _log_ignored_member_params_if_any(request: HttpRequest) -> None:
    # For member requests, any tenant_id in query/body should be ignored but logged
    q_tid = request.GET.get("tenant_id") if hasattr(request, "GET") else None
    b_tid = None
    try:
        if hasattr(request, "data") and isinstance(request.data, dict):
            b_tid = request.data.get("tenant_id")
    except Exception:
        # request.data may not be parsed yet; be conservative
        pass
    if q_tid is not None or b_tid is not None:
        logger.warning(
            "Member request provided tenant_id in query/body will be ignored. query=%r, body=%r",
            q_tid,
            b_tid,
        )


def require_member_header_match(request: HttpRequest) -> None:
    """Validate member/anonymous requests for tenant header presence and match.

    Raises:
        TenantHeaderInvalidOrMissing (4001): when header is missing/invalid
        TenantMismatchOrNoPermission (403/4003): when member's tenant mismatches
    """
    _log_ignored_member_params_if_any(request)

    tenant_id = get_header_tenant_id(request)
    if tenant_id is None:
        raise TenantHeaderInvalidOrMissing()

    user = getattr(request, "user", None)
    if getattr(user, "is_authenticated", False) and hasattr(user, "tenant") and user.tenant:
        try:
            user_tid = int(user.tenant.id)
        except Exception:
            user_tid = None
        if user_tid is not None and user_tid != tenant_id:
            raise TenantMismatchOrNoPermission()

    # valid when here; no return necessary
