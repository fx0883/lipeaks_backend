"""
认证相关视图
"""
import logging
import jwt
from django.conf import settings

from rest_framework.views import APIView
from rest_framework import status, permissions, generics, serializers
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample, OpenApiParameter

from common.authentication.jwt_auth import generate_jwt_token
from users.serializers import (
    LoginSerializer, TokenRefreshSerializer, RegisterSerializer,
    ChangePasswordSerializer, PasswordResetRequestSerializer, PasswordResetVerifySerializer,
    PasswordResetConfirmSerializer, MemberSelfRegisterSerializer
)
from users.schema import (
    login_responses, login_request_examples, login_response_examples,
    token_refresh_responses, token_refresh_request_examples, token_refresh_response_examples,
    token_verify_responses, token_verify_response_examples,
    register_responses, register_request_examples, register_response_examples,
    password_reset_request_responses, password_reset_request_examples, password_reset_response_examples,
    password_reset_verify_responses, password_reset_verify_examples, password_reset_verify_response_examples,
    password_reset_confirm_responses, password_reset_confirm_examples, password_reset_confirm_response_examples
)

logger = logging.getLogger(__name__)

class RegisterView(APIView):
    """
    用户注册视图
    """
    permission_classes = [AllowAny]
    @extend_schema(
        summary="用户注册",
        description="新用户注册接口，可选关联到指定租户",
        request=RegisterSerializer,
        responses=register_responses,
        examples=register_request_examples + register_response_examples,
        tags=["认证"]
    )
    def post(self, request):
        """
        处理用户注册请求
        """
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            # 创建用户
            user = serializer.save()
            
            # 生成JWT令牌
            tokens = generate_jwt_token(user)
            token = tokens['access_token']
            refresh_token = tokens['refresh_token']
            
            # 记录IP
            ip = self.get_client_ip(request)
            user.last_login_ip = ip
            user.save(update_fields=['last_login_ip', 'last_login'])
            
            # 构建用户信息
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'nick_name': user.nick_name or '',
                'is_admin': user.is_admin,
                'is_member': user.is_member,
                'avatar': user.avatar or '',
            }
            
            # 添加租户信息
            if user.tenant:
                user_data['tenant_id'] = user.tenant.id
                user_data['tenant_name'] = user.tenant.name
            
            # 记录注册成功
            logger.info(f"新用户 {user.username} 注册成功, IP: {ip}")
            
            return Response({
                'success': True,
                'code': 2000,
                'message': '注册成功',
                'data': {
                    'token': token,
                    'refresh_token': refresh_token,
                    'user': user_data
                }
            }, status=status.HTTP_201_CREATED)
        
        # 记录注册失败
        logger.warning(f"用户注册失败: {serializer.errors}, IP: {self.get_client_ip(request)}")
        
        return Response({
            'success': False,
            'code': 4000,
            'message': '注册失败',
            'data': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
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


class MemberRegisterView(APIView):
    """
    成员自助注册视图
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="成员自助注册",
        description="成员自助注册接口，tenant_id可从请求体或请求头X-Tenant-ID获取",
        request=MemberSelfRegisterSerializer,
        responses=register_responses,
        examples=register_request_examples + register_response_examples,
        tags=["认证"]
    )
    def post(self, request):
        serializer = MemberSelfRegisterSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            # 创建成员
            member = serializer.save()

            # 生成JWT令牌
            tokens = generate_jwt_token(member)
            token = tokens['access_token']
            refresh_token = tokens['refresh_token']

            # 记录IP
            ip = self.get_client_ip(request)
            member.last_login_ip = ip
            member.save(update_fields=['last_login_ip', 'last_login'])

            # 构建成员信息
            user_data = {
                'id': member.id,
                'username': member.username,
                'email': member.email,
                'nick_name': member.nick_name or '',
                'avatar': member.avatar or '',
                'is_admin': False,
                'is_super_admin': False,
                'is_member': True,
                'is_sub_account': getattr(member, 'is_sub_account', False),
            }

            if member.tenant:
                user_data['tenant_id'] = member.tenant.id
                user_data['tenant_name'] = member.tenant.name

            logger.info(f"新成员 {member.username} 自助注册成功, IP: {ip}")

            return Response({
                'success': True,
                'code': 2000,
                'message': '注册成功',
                'data': {
                    'token': token,
                    'refresh_token': refresh_token,
                    'user': user_data
                }
            }, status=status.HTTP_201_CREATED)

        logger.warning(f"成员自助注册失败: {serializer.errors}, IP: {self.get_client_ip(request)}")
        return Response({
            'success': False,
            'code': 4000,
            'message': '注册失败',
            'data': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class LoginView(APIView):
    """
    用户登录视图
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="用户登录",
        description=(
            "用户登录接口，验证用户名/邮箱和密码，返回JWT令牌。\n"
            "成员可通过请求体的 tenant_id 或请求头 X-Tenant-ID 指定租户；当标识在多个租户中存在时需提供租户ID进行消歧。"
        ),
        request=LoginSerializer,
        responses=login_responses,
        examples=login_request_examples + login_response_examples,
        parameters=[
            OpenApiParameter(
                name="X-Tenant-ID",
                location=OpenApiParameter.HEADER,
                required=False,
                description="租户ID。用于成员登录的租户定位（与请求体 tenant_id 等价；优先级：请求体 > 请求头）",
                type=int,
            ),
        ],
        tags=["认证"]
    )
    def post(self, request):
        """
        处理用户登录请求
        """
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # 生成JWT令牌
            tokens = generate_jwt_token(user)
            token = tokens['access_token']
            refresh_token = tokens['refresh_token']
            
            # 记录IP和更新登录时间
            ip = self.get_client_ip(request)
            user.last_login_ip = ip
            user.save(update_fields=['last_login_ip', 'last_login'])
            
            # 构建用户信息，区分User和Member模型
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'nick_name': user.nick_name or '',
                'avatar': user.avatar or '',
            }
            
            # 根据用户类型添加对应字段
            from users.models import User as AdminUser
            if isinstance(user, AdminUser):
                user_data['is_admin'] = user.is_admin
                user_data['is_super_admin'] = user.is_super_admin
                user_data['is_member'] = False
            else:  # Member类型
                user_data['is_admin'] = False
                user_data['is_super_admin'] = False
                user_data['is_member'] = True
                user_data['is_sub_account'] = user.is_sub_account if hasattr(user, 'is_sub_account') else False
            
            # 添加租户信息
            if user.tenant:
                user_data['tenant_id'] = user.tenant.id
                user_data['tenant_name'] = user.tenant.name
            
            # 记录登录成功
            logger.info(f"用户 {user.username} 登录成功, IP: {ip}")
            
            return Response({
                'success': True,
                'code': 2000,
                'message': '登录成功',
                'data': {
                    'token': token,
                    'refresh_token': refresh_token,
                    'user': user_data
                }
            })
        
        # 记录登录失败
        logger.warning(f"登录失败: {serializer.errors}, IP: {self.get_client_ip(request)}")
        
        return Response({
            'success': False,
            'code': 4002,
            'message': '用户名/邮箱或密码错误',
            'data': None
        }, status=status.HTTP_401_UNAUTHORIZED)
    
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


class TokenRefreshView(APIView):
    """
    刷新Token视图
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="刷新访问令牌",
        description="使用刷新令牌获取新的访问令牌和刷新令牌",
        request=TokenRefreshSerializer,
        responses=token_refresh_responses,
        examples=token_refresh_request_examples + token_refresh_response_examples,
        tags=["认证"]
    )
    def post(self, request):
        """
        处理刷新Token请求
        """
        serializer = TokenRefreshSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'code': 4000,
                'message': '无效的刷新令牌',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)
        
        refresh_token = serializer.validated_data['refresh_token']
        
        try:
            # 解析刷新令牌
            payload = jwt.decode(
                refresh_token,
                settings.JWT_AUTH['JWT_SECRET_KEY'],
                algorithms=[settings.JWT_AUTH['JWT_ALGORITHM']]
            )
            
            # 确认是刷新令牌
            if payload.get('token_type') != 'refresh':
                raise jwt.InvalidTokenError('令牌类型错误')
            
            # 获取用户
            user_id = payload.get('user_id')
            if not user_id:
                raise jwt.InvalidTokenError('令牌中缺少用户ID')
            
            # 根据model_type确定用户模型
            model_type = payload.get('model_type', 'user')
            
            # 导入模型
            from users.models import User, Member
            
            # 根据模型类型查询用户
            if model_type == 'member':
                user = Member.objects.get(id=user_id, is_active=True, is_deleted=False)
            else:
                user = User.objects.get(id=user_id, is_active=True, is_deleted=False)
            
            # 检查用户状态
            if user.status != 'active':
                logger.warning(f"刷新令牌时发现用户状态异常: {user.username} ({user.status})")
                raise jwt.InvalidTokenError('用户状态异常')
                
            # 检查是否为子账号
            if hasattr(user, 'parent') and user.parent:
                logger.warning(f"子账号尝试刷新令牌: {user.username}")
                raise jwt.InvalidTokenError('子账号不允许登录')
            
            # 检查用户的租户状态
            if user.tenant and not getattr(user, 'is_super_admin', False):
                if user.tenant.status != 'active' or user.tenant.is_deleted:
                    logger.warning(f"用户 {user.username} 的租户状态异常")
                    raise jwt.InvalidTokenError('所属租户已被禁用或删除')
            
            # 生成新的令牌
            tokens = generate_jwt_token(user)
            
            # 记录刷新成功
            logger.info(f"用户 {user.username} 刷新令牌成功")
            
            return Response({
                'success': True,
                'code': 2000,
                'message': '刷新令牌成功',
                'data': {
                    'token': tokens['access_token'],
                    'refresh_token': tokens['refresh_token']
                }
            })
            
        except (jwt.InvalidTokenError, jwt.DecodeError) as e:
            logger.warning(f"刷新令牌失败: {str(e)}")
            return Response({
                'success': False,
                'code': 4001,
                'message': '无效的刷新令牌',
                'data': None
            }, status=status.HTTP_401_UNAUTHORIZED)
        except (User.DoesNotExist, Member.DoesNotExist) as e:
            logger.warning(f"刷新令牌对应的用户不存在或已被禁用: {str(e)}")
            return Response({
                'success': False,
                'code': 4001,
                'message': '用户不存在或已被禁用',
                'data': None
            }, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            logger.error(f"刷新令牌时发生未知错误: {str(e)}")
            return Response({
                'success': False,
                'code': 5000,
                'message': '刷新令牌失败',
                'data': None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TokenVerifyView(APIView):
    """
    验证Token视图
    """
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="验证访问令牌",
        description="验证当前令牌是否有效，返回用户信息",
        responses=token_verify_responses,
        examples=token_verify_response_examples,
        tags=["认证"]
    )
    def get(self, request):
        """
        验证当前用户令牌
        """
        user = request.user
        
        # 构建用户信息，区分User和Member模型
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'nick_name': user.nick_name or '',
            'avatar': user.avatar or '',
        }
        
        # 根据用户类型添加对应字段
        from users.models import User as AdminUser
        if isinstance(user, AdminUser):
            user_data['is_admin'] = user.is_admin
            user_data['is_super_admin'] = user.is_super_admin
            user_data['is_member'] = False
        else:  # Member类型
            user_data['is_admin'] = False
            user_data['is_super_admin'] = False
            user_data['is_member'] = True
            user_data['is_sub_account'] = user.is_sub_account if hasattr(user, 'is_sub_account') else False
        
        # 添加租户信息
        if user.tenant:
            user_data['tenant_id'] = user.tenant.id
            user_data['tenant_name'] = user.tenant.name
        
        logger.info(f"用户 {user.username} 验证令牌成功")
        
        return Response({
            'success': True,
            'code': 2000,
            'message': '令牌有效',
            'data': {
                'user': user_data
            }
        })


class ChangePasswordView(generics.UpdateAPIView):
    """
    修改密码视图
    """
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    @extend_schema(
        summary="修改用户密码",
        description="允许已认证用户修改自己的密码，需要提供旧密码和新密码",
        responses={
            200: OpenApiResponse(
                description="密码修改成功",
                examples=[
                    OpenApiExample(
                        name="密码修改成功示例",
                        value={
                            "success": True,
                            "code": 2000,
                            "message": "密码修改成功",
                            "data": {
                                "detail": "密码修改成功"
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="请求数据无效或旧密码不正确",
                examples=[
                    OpenApiExample(
                        name="密码修改成功示例",
                        value={
                            "success": True,
                            "code": 2000,
                            "message": "密码修改成功",
                            "data": {
                                "detail": "密码修改成功"
                            }
                        }
                    )
                ]
            ),
        },
        tags=["认证"]
    )
    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            # 设置新密码
            user.set_password(serializer.validated_data.get('new_password'))
            user.save()
            logger.info(f"用户 {user.username} 修改了密码")
            
            return Response(
                {"detail": "密码修改成功"},
                status=status.HTTP_200_OK
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    # 去掉 put 方法的 DRF 注解
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
    
    # 去掉 patch 方法的 DRF 注解
    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)
    
    # 去掉 post 方法的 DRF 注解
    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

# 管理员修改用户密码的序列化器
class AdminChangePasswordSerializer(serializers.Serializer):
    """
    管理员修改用户密码的序列化器
    """
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, data):
        """
        验证两次输入的密码是否一致
        """
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "两次输入的密码不一致"})
        
        # 验证新密码强度
        from django.contrib.auth.password_validation import validate_password
        validate_password(data['new_password'])
        
        return data

# 管理员修改用户密码视图
class AdminChangePasswordView(generics.UpdateAPIView):
    """
    管理员修改用户密码视图
    """
    serializer_class = AdminChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        user_id = self.kwargs.get('user_id')
        user = get_object_or_404(User, id=user_id)
        return user
    
    def check_permissions(self, request):
        """
        检查当前用户是否有权限修改指定用户密码
        """
        super().check_permissions(request)
        if not (request.user.is_admin or request.user.is_super_admin):
            raise PermissionDenied("只有管理员才能修改其他用户的密码")
    
    @extend_schema(
        summary="管理员修改用户密码",
        description="允许租户管理员或超级管理员修改其他用户的密码",
        responses={
            200: OpenApiResponse(
                description="密码修改成功",
                examples=[
                    OpenApiExample(
                        name="管理员修改密码成功示例",
                        value={
                            "success": True,
                            "code": 2000,
                            "message": "密码修改成功",
                            "data": {
                                "detail": "密码修改成功"
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="请求数据无效",
                examples=[
                    OpenApiExample(
                        name="数据验证失败示例",
                        value={
                            "success": False,
                            "code": 4000,
                            "message": "请求数据无效",
                            "data": {
                                "confirm_password": ["两次输入的密码不一致"]
                            }
                        }
                    )
                ]
            ),
            403: OpenApiResponse(
                description="权限不足",
                examples=[
                    OpenApiExample(
                        name="权限不足示例",
                        value={
                            "success": False,
                            "code": 4003,
                            "message": "权限不足",
                            "data": {
                                "detail": "只有管理员才能修改其他用户的密码"
                            }
                        }
                    )
                ]
            ),
            404: OpenApiResponse(
                description="用户不存在",
                examples=[
                    OpenApiExample(
                        name="用户不存在示例",
                        value={
                            "success": False,
                            "code": 4004,
                            "message": "用户不存在",
                            "data": {
                                "detail": "未找到指定用户"
                            }
                        }
                    )
                ]
            )
        },
        tags=["认证"]
    )
    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(data=request.data)
        
        if serializer.is_valid():
            # 设置新密码
            user.set_password(serializer.validated_data.get('new_password'))
            user.save()
            logger.info(f"管理员 {request.user.username} 修改了用户 {user.username} 的密码")
            
            return Response({
                'success': True,
                'code': 2000,
                'message': '密码修改成功',
                'data': {
                    "detail": "密码修改成功"
                }
            }, status=status.HTTP_200_OK)
        
        return Response({
            'success': False,
            'code': 4000,
            'message': '请求数据无效',
            'data': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
    
    def patch(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

class PasswordResetRequestView(APIView):
    """
    请求密码重置视图
    """
    permission_classes = [AllowAny]
    
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
    
    @extend_schema(
        summary="请求密码重置",
        description="通过邮箱请求密码重置，系统将发送重置链接至邮箱",
        request=PasswordResetRequestSerializer,
        responses=password_reset_request_responses,
        examples=password_reset_request_examples + password_reset_response_examples,
        tags=["认证"]
    )
    def post(self, request):
        """
        处理密码重置请求
        """
        # 获取客户端IP
        ip = self.get_client_ip(request)
        
        # 检查请求限制（同一IP每10分钟最多3次请求）
        from django.core.cache import cache
        from rest_framework.exceptions import Throttled
        
        cache_key = f"password_reset_request:{ip}"
        request_count = cache.get(cache_key, 0)
        
        if request_count >= 3:
            logger.warning(f"IP {ip} 请求密码重置过于频繁")
            raise Throttled(detail="请求过于频繁，请稍后再试")
        
        # 增加请求计数并设置过期时间
        cache.set(cache_key, request_count + 1, 600)  # 10分钟 = 600秒
        
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            # 延迟导入以避免循环依赖
            from users.models import User, Member, PasswordResetToken
            from django.utils import timezone
            import secrets
            import string
            from django.core.mail import send_mail
            from django.template.loader import render_to_string
            from django.conf import settings

            email = serializer.validated_data['email']
            account_type = serializer.validated_data.get('account_type')
            tenant_id = serializer.validated_data.get('tenant_id')

            target_user = None  # 可为 User 或 Member

            try:
                if account_type == 'user':
                    target_user = User.objects.filter(email=email, is_active=True, is_deleted=False).first()
                elif account_type == 'member':
                    qs = Member.objects.filter(email=email, is_active=True, is_deleted=False, status='active')
                    # 子账号不允许找回
                    qs = qs.filter(parent__isnull=True)
                    if tenant_id:
                        qs = qs.filter(tenant_id=tenant_id)
                    # 若出现多租户歧义，返回通用成功（不发送邮件）
                    if qs.count() == 1:
                        target_user = qs.first()
                else:
                    # 未指定类型：优先匹配 User；否则匹配唯一 Member
                    target_user = User.objects.filter(email=email, is_active=True, is_deleted=False).first()
                    if not target_user:
                        qs = Member.objects.filter(email=email, is_active=True, is_deleted=False, status='active').filter(parent__isnull=True)
                        if tenant_id:
                            qs = qs.filter(tenant_id=tenant_id)
                        if qs.count() == 1:
                            target_user = qs.first()
            except Exception as e:
                # 出现异常也不暴露细节
                logger.error(f"查找重置主体异常: {str(e)}")

            if target_user:
                # 生成安全令牌与过期时间
                token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(64))
                expires_at = timezone.now() + timezone.timedelta(hours=1)

                # 创建统一令牌，关联到 user 或 member
                kwargs = {'token': token, 'expires_at': expires_at}
                if hasattr(target_user, '_meta') and target_user._meta.model_name == 'user':
                    kwargs['user'] = target_user
                else:
                    kwargs['member'] = target_user
                reset_token = PasswordResetToken.objects.create(**kwargs)

                # 重置链接
                frontend_url = settings.FRONTEND_URL
                reset_link = f"{frontend_url}/reset-password?token={token}"

                # 邮件内容
                context = {
                    'user': target_user,
                    'reset_link': reset_link,
                    'expires_at': expires_at.strftime('%Y-%m-%d %H:%M:%S')
                }
                subject = '密码重置 - 多租户用户管理系统'
                html_message = render_to_string('email/password_reset.html', context)
                plain_message = f"""
                尊敬的 {getattr(target_user, 'display_name', getattr(target_user, 'username', '用户'))}，

                您收到此邮件是因为您请求重置您在多租户用户管理系统的密码。

                请点击以下链接重置密码：
                {reset_link}

                此链接将在 {expires_at.strftime('%Y-%m-%d %H:%M:%S')} 过期。

                如果您没有请求重置密码，请忽略此邮件。

                多租户用户管理系统团队
                """

                try:
                    send_mail(
                        subject=subject,
                        message=plain_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[target_user.email],
                        html_message=html_message,
                        fail_silently=False
                    )
                    logger.info(f"已发送密码重置邮件至 {target_user.email}")
                except Exception as e:
                    logger.error(f"发送密码重置邮件失败: {str(e)}")
                    # 删除已创建的令牌，避免脏数据
                    reset_token.delete()
                    return Response({
                        'success': False,
                        'code': 5000,
                        'message': '发送邮件失败，请稍后再试',
                        'data': {
                            'detail': '发送邮件失败，请稍后再试'
                        }
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # 无论是否找到主体，都返回通用成功，避免用户枚举
            if not target_user:
                logger.info(f"密码重置请求提交（可能存在租户歧义/不存在）：{email}")
            return Response({
                'success': True,
                'code': 2000,
                'message': '如果该邮箱存在，密码重置链接已发送',
                'data': {
                    'detail': '如果该邮箱存在，密码重置链接已发送'
                }
            })
        
        logger.warning(f"用户请求密码重置失败，数据验证未通过: {serializer.errors}")
        return Response({
            'success': False,
            'code': 4000,
            'message': '请求数据无效',
            'data': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetVerifyView(APIView):
    """
    验证密码重置令牌视图
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="验证密码重置令牌",
        description="验证密码重置令牌是否有效",
        request=PasswordResetVerifySerializer,
        responses=password_reset_verify_responses,
        examples=password_reset_verify_examples + password_reset_verify_response_examples,
        tags=["认证"]
    )
    def post(self, request):
        """
        验证密码重置令牌
        """
        serializer = PasswordResetVerifySerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            from users.models import PasswordResetToken
            token_obj = PasswordResetToken.objects.filter(token=token, is_used=False).first()
            
            if token_obj and not token_obj.is_expired():
                # 兼容 user/member
                owner = token_obj.user or token_obj.member
                email = getattr(owner, 'email', None)
                name = getattr(owner, 'username', '用户')
                logger.info(f"密码重置令牌验证成功，账号: {name}")
                return Response({
                    'success': True,
                    'code': 2000,
                    'message': '重置令牌有效',
                    'data': {
                        'detail': '重置令牌有效',
                        'user_email': email
                    }
                })
            
            if token_obj and token_obj.is_expired():
                owner = token_obj.user or token_obj.member
                logger.warning(f"密码重置令牌已过期，账号: {getattr(owner, 'username', '未知')}")
                return Response({
                    'success': False,
                    'code': 4000,
                    'message': '重置令牌已过期',
                    'data': {
                        'token': ['重置令牌已过期']
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
            logger.warning("验证了无效的密码重置令牌")
            return Response({
                'success': False,
                'code': 4000,
                'message': '无效的重置令牌',
                'data': {
                    'token': ['无效的重置令牌']
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.warning(f"密码重置令牌验证失败，数据验证未通过: {serializer.errors}")
        return Response({
            'success': False,
            'code': 4000,
            'message': '请求数据无效',
            'data': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """
    确认密码重置视图
    """
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="确认密码重置",
        description="使用有效的重置令牌重置用户密码",
        request=PasswordResetConfirmSerializer,
        responses=password_reset_confirm_responses,
        examples=password_reset_confirm_examples + password_reset_confirm_response_examples,
        tags=["认证"]
    )
    def post(self, request):
        """
        确认密码重置
        """
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            token_obj = serializer.validated_data['token_obj']
            new_password = serializer.validated_data['new_password']
            
            # 获取目标账号（User 或 Member）
            owner = token_obj.user or token_obj.member

            # 校验密码强度
            from django.contrib.auth.password_validation import validate_password
            validate_password(new_password)

            # 设置新密码
            owner.set_password(new_password)
            owner.save(update_fields=['password'])
            
            # 标记令牌为已使用
            token_obj.mark_as_used()
            
            # 记录密码重置
            logger.info(f"账号 {getattr(owner, 'username', '用户')} 的密码已重置")
            
            return Response({
                'success': True,
                'code': 2000,
                'message': '密码重置成功',
                'data': {
                    'detail': '密码重置成功，请使用新密码登录'
                }
            })
        
        logger.warning(f"密码重置确认失败，数据验证未通过: {serializer.errors}")
        return Response({
            'success': False,
            'code': 4000,
            'message': '请求数据无效',
            'data': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST) 