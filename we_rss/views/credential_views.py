from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from common.schema.responses import common_error_responses
from we_rss.models import WechatCredential, WechatCredentialLoginSession
from we_rss.schema import (
    CREDENTIAL_CHECK_EXAMPLE,
    CREDENTIAL_EXAMPLE,
    CREDENTIAL_ID_PARAMETER,
    LOGIN_SESSION_EXAMPLE,
    SESSION_ID_PARAMETER,
    WE_RSS_AUTH_DESCRIPTION,
    WE_RSS_TAG,
    json_response,
    request_body,
    request_example,
    with_tenant_header,
)
from we_rss.serializers import (
    CredentialCheckResponseSerializer,
    CredentialLoginSessionCreateSerializer,
    CredentialLoginSessionDetailSerializer,
    CredentialUpdateSerializer,
    WechatCredentialDetailSerializer,
    WechatCredentialListSerializer,
)
from we_rss.services.credential_service import CredentialService, WechatCredentialGateway
from we_rss.views.base import WeRssTenantGenericViewSet, WeRssTenantModelViewSet


class CredentialApiGatewayMixin:
    def get_gateway(self):
        return WechatCredentialGateway()


class CredentialViewSet(CredentialApiGatewayMixin, WeRssTenantModelViewSet):
    queryset = WechatCredential.objects.all()
    serializer_class = WechatCredentialDetailSerializer

    def get_queryset(self):
        return super().get_queryset().order_by("-created_at")

    def get_serializer_class(self):
        if self.action == "list":
            return WechatCredentialListSerializer
        if self.action == "update":
            return CredentialUpdateSerializer
        return WechatCredentialDetailSerializer

    @extend_schema(
        operation_id="we_rss_credentials_list",
        tags=[WE_RSS_TAG],
        summary="列出当前租户的微信凭证",
        description=f"返回当前成员所在 tenant 下可用的全部微信抓取凭证列表。{WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(),
        responses={
            200: json_response(
                WechatCredentialListSerializer(many=True),
                "凭证列表获取成功。",
                [CREDENTIAL_EXAMPLE],
                example_name="Credential list response",
                message="操作成功",
            ),
            **common_error_responses,
        },
    )
    def list(self, request, *args, **kwargs):
        serializer = WechatCredentialListSerializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    @extend_schema(
        operation_id="we_rss_credentials_retrieve",
        tags=[WE_RSS_TAG],
        summary="获取单个微信凭证",
        description=f"按 ID 返回当前 tenant 内的单个微信抓取凭证详情。{WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(CREDENTIAL_ID_PARAMETER),
        responses={
            200: json_response(
                WechatCredentialDetailSerializer,
                "凭证详情获取成功。",
                CREDENTIAL_EXAMPLE,
                example_name="Credential detail response",
                message="操作成功",
            ),
            **common_error_responses,
        },
    )
    def retrieve(self, request, *args, **kwargs):
        serializer = WechatCredentialDetailSerializer(self.get_object())
        return Response(serializer.data)

    @extend_schema(
        operation_id="we_rss_credentials_update",
        tags=[WE_RSS_TAG],
        summary="更新微信凭证元数据",
        description=(
            "仅允许更新凭证显示名称。`token` 与 `cookie` 不支持手动修改，"
            f"登录态仍需通过扫码登录任务生成。{WE_RSS_AUTH_DESCRIPTION}"
        ),
        parameters=with_tenant_header(CREDENTIAL_ID_PARAMETER),
        request=request_body(
            CredentialUpdateSerializer,
            request_example(
                "Credential update request",
                {"name": "Default Credential"},
                description="更新凭证名称。",
            )
        ),
        responses={
            200: json_response(
                WechatCredentialDetailSerializer,
                "凭证更新成功。",
                CREDENTIAL_EXAMPLE,
                example_name="Credential update response",
                message="操作成功",
            ),
            **common_error_responses,
        },
    )
    def update(self, request, *args, **kwargs):
        credential = self.get_object()
        serializer = CredentialUpdateSerializer(credential, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)
        return Response(WechatCredentialDetailSerializer(credential).data)

    @extend_schema(
        operation_id="we_rss_credentials_destroy",
        tags=[WE_RSS_TAG],
        summary="删除微信凭证",
        description=f"删除当前 tenant 内的微信抓取凭证。删除后不可恢复。{WE_RSS_AUTH_DESCRIPTION}",
        parameters=with_tenant_header(CREDENTIAL_ID_PARAMETER),
        responses={204: OpenApiResponse(description="Credential deleted"), **common_error_responses},
    )
    def destroy(self, request, *args, **kwargs):
        credential = self.get_object()
        credential.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        operation_id="we_rss_credentials_check",
        tags=[WE_RSS_TAG],
        summary="校验微信凭证有效性",
        description=(
            "使用当前保存的微信抓取凭证访问微信网关并刷新状态，"
            f"适合在同步前确认登录态是否仍有效。{WE_RSS_AUTH_DESCRIPTION}"
        ),
        parameters=with_tenant_header(CREDENTIAL_ID_PARAMETER),
        request=None,
        responses={
            200: json_response(
                CredentialCheckResponseSerializer,
                "凭证校验完成。",
                CREDENTIAL_CHECK_EXAMPLE,
                example_name="Credential check response",
                message="操作成功",
            ),
            **common_error_responses,
        },
    )
    @action(detail=True, methods=["post"])
    def check(self, request, pk=None):
        credential = self.get_object()
        result = CredentialService.check_credential(credential=credential, gateway=self.get_gateway())
        serializer = CredentialCheckResponseSerializer(result)
        return Response(serializer.data)

    @extend_schema(
        operation_id="we_rss_credentials_set_default",
        tags=[WE_RSS_TAG],
        summary="设置默认微信凭证",
        description=(
            "将指定凭证设置为当前 tenant 的默认微信抓取凭证，并自动取消其他默认项。"
            f"{WE_RSS_AUTH_DESCRIPTION}"
        ),
        parameters=with_tenant_header(CREDENTIAL_ID_PARAMETER),
        request=None,
        responses={
            200: json_response(
                WechatCredentialDetailSerializer,
                "默认凭证设置成功。",
                CREDENTIAL_EXAMPLE,
                example_name="Credential set default response",
                message="操作成功",
            ),
            **common_error_responses,
        },
    )
    @action(detail=True, methods=["post"])
    def set_default(self, request, pk=None):
        credential = self.get_object()
        credential = CredentialService.set_default_credential(credential, updated_by=request.user)
        return Response(WechatCredentialDetailSerializer(credential).data)


class CredentialLoginSessionViewSet(CredentialApiGatewayMixin, WeRssTenantGenericViewSet):
    queryset = WechatCredentialLoginSession.objects.all()
    lookup_field = "session_id"
    lookup_url_kwarg = "session_id"

    def get_queryset(self):
        return WechatCredentialLoginSession.objects.filter(tenant_id=self.get_tenant_id()).order_by("-created_at")

    @extend_schema(
        operation_id="we_rss_credentials_login_sessions_create",
        tags=[WE_RSS_TAG],
        summary="创建扫码登录会话",
        description=(
            "创建一个新的微信扫码登录会话，返回二维码地址、二维码图片和绑定的后台任务。"
            f"{WE_RSS_AUTH_DESCRIPTION}"
        ),
        parameters=with_tenant_header(),
        request=request_body(
            CredentialLoginSessionCreateSerializer,
            request_example(
                "Login session create request",
                {},
                description="当前接口不需要请求字段，提交空 JSON 对象即可。",
            )
        ),
        responses={
            201: json_response(
                CredentialLoginSessionDetailSerializer,
                "扫码登录会话创建成功。",
                LOGIN_SESSION_EXAMPLE,
                example_name="Login session create response",
                message="操作成功",
                status_code=201,
            ),
            **common_error_responses,
        },
    )
    def create(self, request, *args, **kwargs):
        serializer = CredentialLoginSessionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = CredentialService.create_login_session(
            tenant=request.user.tenant,
            created_by=request.user,
            gateway=self.get_gateway(),
        )
        return Response(CredentialLoginSessionDetailSerializer(session).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        operation_id="we_rss_credentials_login_sessions_retrieve",
        tags=[WE_RSS_TAG],
        summary="查询扫码登录会话",
        description=(
            "根据 `session_id` 查询扫码登录状态、二维码信息以及最终关联的凭证 ID。"
            f"{WE_RSS_AUTH_DESCRIPTION}"
        ),
        parameters=with_tenant_header(SESSION_ID_PARAMETER),
        responses={
            200: json_response(
                CredentialLoginSessionDetailSerializer,
                "扫码登录会话详情获取成功。",
                LOGIN_SESSION_EXAMPLE,
                example_name="Login session detail response",
                message="操作成功",
            ),
            **common_error_responses,
        },
    )
    def retrieve(self, request, *args, **kwargs):
        session = get_object_or_404(self.get_queryset(), session_id=kwargs["session_id"])
        return Response(CredentialLoginSessionDetailSerializer(session).data)
