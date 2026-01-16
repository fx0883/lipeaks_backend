"""
微信小程序相关视图
"""
import logging
import uuid
from django.db import transaction
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample

from wechat.models import WechatUser
from wechat.serializers import WechatLoginSerializer
from users.models import Member
from tenants.models import Tenant
from common.authentication.jwt_auth import generate_jwt_token
from common.utils.image_url import add_domain_to_image_url

logger = logging.getLogger(__name__)


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
                description="租户ID（首次登录时用于指定新用户所属租户）",
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
                            "is_new_user": {"type": "boolean"}
                        }
                    }
                }
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
        tags=["微信登录"]
    )
    def post(self, request):
        """
        处理微信登录请求
        """
        serializer = WechatLoginSerializer(data=request.data)
        
        if not serializer.is_valid():
            logger.warning(f"微信登录参数校验失败: {serializer.errors}")
            return Response({
                'success': False,
                'code': 4000,
                'message': '登录失败',
                'data': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 从验证后的数据中获取微信信息
        openid = serializer.validated_data['openid']
        session_key = serializer.validated_data.get('session_key')
        unionid = serializer.validated_data.get('unionid')
        
        # 获取租户ID（优先从请求体获取，其次从请求头获取）
        tenant_id = serializer.validated_data.get('tenant_id')
        if not tenant_id:
            tenant_id = request.headers.get('X-Tenant-ID')
            if tenant_id:
                try:
                    tenant_id = int(tenant_id)
                except ValueError:
                    tenant_id = None
        
        try:
            with transaction.atomic():
                # 查找已存在的微信用户
                wechat_user = WechatUser.objects.filter(openid=openid).first()
                is_new_user = False
                
                if wechat_user:
                    # 已绑定用户，更新 session_key
                    member = wechat_user.member
                    if session_key:
                        wechat_user.update_session_key(session_key)
                    logger.info(f"微信用户 {openid[:8]}... 登录，已绑定 Member: {member.username}")
                else:
                    # 首次登录，创建新用户
                    is_new_user = True
                    
                    # 获取租户
                    tenant = None
                    if tenant_id:
                        tenant = Tenant.objects.filter(id=tenant_id).first()
                        if not tenant:
                            logger.warning(f"指定的租户 {tenant_id} 不存在")
                    
                    # 生成唯一用户名
                    username = f"wx_{openid[:16]}_{uuid.uuid4().hex[:6]}"
                    
                    # 创建 Member 账号
                    member = Member.objects.create(
                        username=username,
                        email=f"{username}@wechat.placeholder",  # 占位邮箱
                        tenant=tenant,
                        is_active=True,
                    )
                    # 设置一个随机密码（微信用户不需要密码登录）
                    member.set_password(uuid.uuid4().hex)
                    member.save()
                    
                    # 创建微信用户记录
                    wechat_user = WechatUser.objects.create(
                        member=member,
                        openid=openid,
                        unionid=unionid,
                        session_key=session_key,
                    )
                    
                    logger.info(f"新微信用户 {openid[:8]}... 首次登录，创建 Member: {member.username}")
                
                # 更新登录信息
                ip = self.get_client_ip(request)
                member.last_login_ip = ip
                member.save(update_fields=['last_login_ip', 'last_login'])
                
                # 生成 JWT token
                tokens = generate_jwt_token(member)
                
                # 构建用户信息
                avatar_url = add_domain_to_image_url(request, member.avatar) if member.avatar else ''
                user_data = {
                    'id': member.id,
                    'username': member.username,
                    'email': member.email,
                    'nick_name': member.nick_name or wechat_user.nickname or '',
                    'avatar': avatar_url or wechat_user.avatar_url or '',
                    'is_admin': False,
                    'is_super_admin': False,
                    'is_member': True,
                    'is_sub_account': getattr(member, 'is_sub_account', False),
                    'wechat_bindded': True,
                }
                
                if member.tenant:
                    user_data['tenant_id'] = member.tenant.id
                    user_data['tenant_name'] = member.tenant.name
                
                return Response({
                    'success': True,
                    'code': 2000,
                    'message': '登录成功',
                    'data': {
                        'token': tokens['access_token'],
                        'refresh_token': tokens['refresh_token'],
                        'user': user_data,
                        'is_new_user': is_new_user,
                    }
                })
                
        except Exception as e:
            logger.exception(f"微信登录处理异常: {str(e)}")
            return Response({
                'success': False,
                'code': 5000,
                'message': '登录处理失败，请稍后再试',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get_client_ip(self, request):
        """
        获取客户端IP地址
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
