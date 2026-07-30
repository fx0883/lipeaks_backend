"""
WeChat-related views.
"""

import logging
import uuid

from django.db import transaction
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.authentication.jwt_auth import generate_jwt_token
from common.utils.image_url import add_domain_to_image_url
from tenants.models import Tenant
from users.models import Member
from wechat.models import WechatUser
from wechat.serializers import (
    WechatAccountsResponseSerializer,
    WechatAddMaterialRequestSerializer,
    WechatAddMaterialResponseSerializer,
    WechatDraftAddRequestSerializer,
    WechatDraftAddResponseSerializer,
    WechatErrorResponseSerializer,
    WechatLoginSerializer,
    WechatUploadImageRequestSerializer,
    WechatUploadImageResponseSerializer,
)
from wechat.services import (
    WechatServiceError,
    add_draft,
    add_permanent_material_file,
    get_access_token,
    get_wechat_account_by_appid,
    load_wechat_accounts,
    upload_article_image_file,
)

logger = logging.getLogger(__name__)


def _validation_error_response(errors):
    return Response(
        {
            "success": False,
            "code": 4000,
            "message": "请求参数校验失败",
            "data": errors,
        },
        status=status.HTTP_400_BAD_REQUEST,
    )


def _unexpected_error_response(message):
    return Response(
        {
            "success": False,
            "code": 5000,
            "message": message,
            "data": None,
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def _apply_default_author(articles, default_author):
    normalized_articles = []
    for article in articles:
        normalized_article = dict(article)
        article_type = str(normalized_article.get("article_type", "news")).strip() or "news"
        normalized_article["article_type"] = article_type
        if article_type == "news" and not str(normalized_article.get("author", "")).strip():
            normalized_article["author"] = default_author
        normalized_articles.append(normalized_article)
    return normalized_articles


@extend_schema(
    summary="获取公众号账号列表",
    description=(
        "读取 `WECHAT_CONFIG_PATH` 配置文件，返回前端下拉框需要的公众号账号列表。"
        "响应只暴露 `name`、`author` 和 `appid`。"
    ),
    responses={
        200: WechatAccountsResponseSerializer,
        500: WechatErrorResponseSerializer,
    },
    examples=[
        OpenApiExample(
            name="公众号账号列表示例",
            value={
                "success": True,
                "code": 2000,
                "message": "获取公众号账号列表成功",
                "data": [
                    {"name": "公众号A", "author": "作者甲", "appid": "wx123"},
                    {"name": "公众号B", "author": "作者乙", "appid": "wx456"},
                ],
            },
            response_only=True,
        )
    ],
    tags=["微信公众号草稿接口"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def wechat_accounts(request):
    try:
        accounts = load_wechat_accounts()
        data = [
            {
                "name": account["name"],
                "author": account.get("author", ""),
                "appid": account["WECHAT_APPID"],
            }
            for account in accounts
        ]
        return Response(
            {
                "success": True,
                "code": 2000,
                "message": "获取公众号账号列表成功",
                "data": data,
            },
            status=status.HTTP_200_OK,
        )
    except WechatServiceError as exc:
        return Response(exc.to_response(), status=exc.status_code)
    except Exception:
        logger.exception("Failed to load WeChat accounts")
        return _unexpected_error_response("获取公众号账号列表失败")


@extend_schema(
    summary="上传图文正文图片",
    description=(
        "对应微信官方 `/cgi-bin/media/uploadimg` 接口。前端每次上传一张正文图片，"
        "后端返回微信可用的图片 URL。"
    ),
    request=WechatUploadImageRequestSerializer,
    responses={
        200: WechatUploadImageResponseSerializer,
        400: WechatErrorResponseSerializer,
        401: WechatErrorResponseSerializer,
        500: WechatErrorResponseSerializer,
        502: WechatErrorResponseSerializer,
    },
    examples=[
        OpenApiExample(
            name="上传正文图片成功",
            value={
                "success": True,
                "code": 2000,
                "message": "正文图片上传成功",
                "data": {
                    "account_appid": "wx123",
                    "account_name": "公众号A",
                    "url": "https://mmbiz.qpic.cn/example-image",
                },
            },
            response_only=True,
        )
    ],
    tags=["微信公众号草稿接口"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def wechat_media_uploadimg(request):
    serializer = WechatUploadImageRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return _validation_error_response(serializer.errors)

    validated_data = serializer.validated_data

    try:
        account = get_wechat_account_by_appid(validated_data["account_appid"])
        access_token = get_access_token(account["WECHAT_APPID"], account["WECHAT_SECRET"])
        image_url = upload_article_image_file(access_token, validated_data["media"])
        return Response(
            {
                "success": True,
                "code": 2000,
                "message": "正文图片上传成功",
                "data": {
                    "account_appid": account["WECHAT_APPID"],
                    "account_name": account["name"],
                    "url": image_url,
                },
            },
            status=status.HTTP_200_OK,
        )
    except WechatServiceError as exc:
        return Response(exc.to_response(), status=exc.status_code)
    except Exception:
        logger.exception(
            "Failed to upload WeChat article image for appid=%s",
            validated_data["account_appid"],
        )
        return _unexpected_error_response("正文图片上传失败")


@extend_schema(
    summary="上传永久素材",
    description=(
        "对应微信官方 `/cgi-bin/material/add_material` 接口。前端每次上传一个永久素材。"
        "当前支持 `image` 和 `thumb`。不传 `type` 时默认按 `image` 处理。"
    ),
    request=WechatAddMaterialRequestSerializer,
    responses={
        200: WechatAddMaterialResponseSerializer,
        400: WechatErrorResponseSerializer,
        401: WechatErrorResponseSerializer,
        500: WechatErrorResponseSerializer,
        502: WechatErrorResponseSerializer,
    },
    examples=[
        OpenApiExample(
            name="上传永久素材成功",
            value={
                "success": True,
                "code": 2000,
                "message": "永久素材上传成功",
                "data": {
                    "account_appid": "wx123",
                    "account_name": "公众号A",
                    "type": "image",
                    "media_id": "MEDIA_ID_123",
                    "url": "https://mmbiz.qpic.cn/example-material",
                },
            },
            response_only=True,
        )
    ],
    tags=["微信公众号草稿接口"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def wechat_material_add_material(request):
    serializer = WechatAddMaterialRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return _validation_error_response(serializer.errors)

    validated_data = serializer.validated_data

    try:
        account = get_wechat_account_by_appid(validated_data["account_appid"])
        access_token = get_access_token(account["WECHAT_APPID"], account["WECHAT_SECRET"])
        material_result = add_permanent_material_file(
            access_token,
            validated_data["media"],
            validated_data["type"],
        )
        return Response(
            {
                "success": True,
                "code": 2000,
                "message": "永久素材上传成功",
                "data": {
                    "account_appid": account["WECHAT_APPID"],
                    "account_name": account["name"],
                    "type": validated_data["type"],
                    "media_id": material_result["media_id"],
                    "url": material_result.get("url"),
                },
            },
            status=status.HTTP_200_OK,
        )
    except WechatServiceError as exc:
        return Response(exc.to_response(), status=exc.status_code)
    except Exception:
        logger.exception(
            "Failed to add WeChat permanent material for appid=%s type=%s",
            validated_data["account_appid"],
            validated_data["type"],
        )
        return _unexpected_error_response("永久素材上传失败")


@extend_schema(
    summary="新增草稿",
    description=(
        "对应微信官方 `/cgi-bin/draft/add` 接口。前端先自行上传正文图片和永久素材，"
        "再通过本接口提交 `articles` JSON。"
    ),
    request=WechatDraftAddRequestSerializer,
    responses={
        200: WechatDraftAddResponseSerializer,
        400: WechatErrorResponseSerializer,
        401: WechatErrorResponseSerializer,
        500: WechatErrorResponseSerializer,
        502: WechatErrorResponseSerializer,
    },
    examples=[
        OpenApiExample(
            name="新增草稿请求示例",
            value={
                "account_appid": "wx123",
                "articles": [
                    {
                        "article_type": "news",
                        "title": "文章标题",
                        "author": "作者甲",
                        "digest": "文章摘要",
                        "content": "<p>正文内容</p>",
                        "content_source_url": "https://example.com/source-article",
                        "thumb_media_id": "thumb-media-id",
                        "need_open_comment": 0,
                        "only_fans_can_comment": 0,
                    }
                ],
            },
            request_only=True,
        ),
        OpenApiExample(
            name="新增草稿成功",
            value={
                "success": True,
                "code": 2000,
                "message": "草稿创建成功",
                "data": {
                    "account_appid": "wx123",
                    "account_name": "公众号A",
                    "draft_media_id": "draft-media-id",
                },
            },
            response_only=True,
        ),
    ],
    tags=["微信公众号草稿接口"],
)
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def wechat_draft_add(request):
    serializer = WechatDraftAddRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return _validation_error_response(serializer.errors)

    validated_data = serializer.validated_data

    try:
        account = get_wechat_account_by_appid(validated_data["account_appid"])
        access_token = get_access_token(account["WECHAT_APPID"], account["WECHAT_SECRET"])
        normalized_articles = _apply_default_author(
            validated_data["articles"],
            account.get("author", ""),
        )
        draft_result = add_draft(access_token, normalized_articles)
        return Response(
            {
                "success": True,
                "code": 2000,
                "message": "草稿创建成功",
                "data": {
                    "account_appid": account["WECHAT_APPID"],
                    "account_name": account["name"],
                    "draft_media_id": draft_result["media_id"],
                },
            },
            status=status.HTTP_200_OK,
        )
    except WechatServiceError as exc:
        return Response(exc.to_response(), status=exc.status_code)
    except Exception:
        logger.exception(
            "Failed to add WeChat draft for appid=%s",
            validated_data["account_appid"],
        )
        return _unexpected_error_response("草稿创建失败")


class WechatLoginView(APIView):
    """
    微信小程序登录视图

    处理微信登录流程：
    1. 接收小程序前端传来的 code
    2. 调用微信 code2Session API 获取 openid/session_key/unionid
    3. 查找或创建 WechatUser 和 Member
    4. 生成并返回 JWT token
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="微信小程序登录",
        description=(
            "微信小程序登录接口。\n\n"
            "**流程说明：**\n"
            "1. 小程序端调用 wx.login() 获取 code\n"
            "2. 将 code 发送到此接口\n"
            "3. 后端调用微信 code2Session API 验证并获取用户标识\n"
            "4. 首次登录自动创建 Member 账号并绑定微信\n"
            "5. 返回 JWT token 用于后续 API 认证\n\n"
            "**注意：** code 只能使用一次，有效期 5 分钟"
        ),
        request=WechatLoginSerializer,
        parameters=[
            OpenApiParameter(
                name="X-Tenant-ID",
                location=OpenApiParameter.HEADER,
                required=False,
                description="租户 ID（首次登录时用于指定新用户所属租户）",
                type=int,
            ),
        ],
        responses={
            200: {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean", "example": True},
                    "code": {"type": "integer", "example": 2000},
                    "message": {"type": "string", "example": "登录成功"},
                    "data": {
                        "type": "object",
                        "properties": {
                            "token": {"type": "string"},
                            "refresh_token": {"type": "string"},
                            "user": {"type": "object"},
                            "is_new_user": {"type": "boolean"},
                        },
                    },
                },
            },
            400: {"description": "请求参数错误或微信登录失败"},
        },
        examples=[
            OpenApiExample(
                name="登录请求示例",
                value={"code": "wx_login_code_from_miniprogram"},
                request_only=True,
            ),
        ],
        tags=["微信登录"],
    )
    def post(self, request):
        """
        处理微信登录请求
        """

        serializer = WechatLoginSerializer(data=request.data)

        if not serializer.is_valid():
            logger.warning("微信登录参数校验失败: %s", serializer.errors)
            return Response(
                {
                    "success": False,
                    "code": 4000,
                    "message": "登录失败",
                    "data": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        openid = serializer.validated_data["openid"]
        session_key = serializer.validated_data.get("session_key")
        unionid = serializer.validated_data.get("unionid")

        tenant_id = serializer.validated_data.get("tenant_id")
        if not tenant_id:
            tenant_id = request.headers.get("X-Tenant-ID")
            if tenant_id:
                try:
                    tenant_id = int(tenant_id)
                except ValueError:
                    tenant_id = None

        try:
            with transaction.atomic():
                wechat_user = WechatUser.objects.filter(openid=openid).first()
                is_new_user = False

                if wechat_user:
                    member = wechat_user.member
                    if session_key:
                        wechat_user.update_session_key(session_key)
                    logger.info(
                        "微信用户 %s 登录，已绑定 Member: %s",
                        openid[:8],
                        member.username,
                    )
                else:
                    is_new_user = True

                    tenant = None
                    if tenant_id:
                        tenant = Tenant.objects.filter(id=tenant_id).first()
                        if not tenant:
                            logger.warning("指定的租户 %s 不存在", tenant_id)

                    username = f"wx_{openid[:16]}_{uuid.uuid4().hex[:6]}"

                    member = Member.objects.create(
                        username=username,
                        email=f"{username}@wechat.placeholder",
                        tenant=tenant,
                        is_active=True,
                    )
                    member.set_password(uuid.uuid4().hex)
                    member.save()

                    wechat_user = WechatUser.objects.create(
                        member=member,
                        openid=openid,
                        unionid=unionid,
                        session_key=session_key,
                    )

                    logger.info(
                        "新微信用户 %s 首次登录，创建 Member: %s",
                        openid[:8],
                        member.username,
                    )

                ip = self.get_client_ip(request)
                member.last_login_ip = ip
                member.save(update_fields=["last_login_ip", "last_login"])

                tokens = generate_jwt_token(member)

                avatar_url = add_domain_to_image_url(request, member.avatar) if member.avatar else ""
                user_data = {
                    "id": member.id,
                    "username": member.username,
                    "email": member.email,
                    "nick_name": member.nick_name or wechat_user.nickname or "",
                    "avatar": avatar_url or wechat_user.avatar_url or "",
                    "is_admin": False,
                    "is_super_admin": False,
                    "is_member": True,
                    "is_sub_account": getattr(member, "is_sub_account", False),
                    "wechat_bindded": True,
                }

                if member.tenant:
                    user_data["tenant_id"] = member.tenant.id
                    user_data["tenant_name"] = member.tenant.name

                return Response(
                    {
                        "success": True,
                        "code": 2000,
                        "message": "登录成功",
                        "data": {
                            "token": tokens["access_token"],
                            "refresh_token": tokens["refresh_token"],
                            "user": user_data,
                            "is_new_user": is_new_user,
                        },
                    }
                )

        except Exception as exc:
            logger.exception("微信登录处理异常: %s", str(exc))
            return Response(
                {
                    "success": False,
                    "code": 5000,
                    "message": "登录处理失败，请稍后再试",
                    "data": None,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def get_client_ip(self, request):
        """
        获取客户端 IP 地址
        """

        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip
