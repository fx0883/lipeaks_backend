"""
许可证激活API视图
提供客户端激活、验证、心跳检测等功能
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.cache import cache
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from licenses.serializers import (
    ActivateLicenseSerializer, VerifyActivationSerializer, HeartbeatSerializer
)
from licenses.services.license_service import LicenseActivationService, LicenseManagementService
from licenses.services.security_service import SecurityService
from licenses.models import SecurityAuditLog, LicenseUsageLog, LicenseActivation, MachineBinding
import json
import logging

logger = logging.getLogger('licenses.activation')


class ActivationRateThrottle(AnonRateThrottle):
    """激活请求频率限制"""
    scope = 'activation'
    rate = '10/hour'  # 每小时最多10次激活请求


@extend_schema(
    tags=['许可证激活API'],
    summary='激活许可证',
    description='客户端激活许可证，验证许可证密钥并绑定硬件信息',
    request=ActivateLicenseSerializer,
    responses={
        200: OpenApiResponse(
            description='激活成功',
            examples=[
                OpenApiExample(
                    'Activation Success',
                    value={
                        'success': True,
                        'message': 'License activated successfully',
                        'data': {
                            'activation_code': 'ACT-12345678-ABCD-EFGH',
                            'machine_id': 'MACHINE-ID-12345',
                            'expires_at': '2024-12-31T23:59:59Z',
                            'features': {'feature1': True, 'feature2': False}
                        }
                    }
                )
            ]
        ),
        400: OpenApiResponse(description='激活失败'),
        403: OpenApiResponse(description='可疑活动被阻止'),
        429: OpenApiResponse(description='请求频率限制')
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def activate_license(request):
    """
    激活许可证
    
    POST /api/v1/licenses/activate/
    """
    # 应用频率限制
    throttle = ActivationRateThrottle()
    if not throttle.allow_request(request, None):
        return Response({
            'success': False,
            'error': 'Too many activation attempts. Please try again later.',
            'code': 'RATE_LIMITED'
        }, status=status.HTTP_429_TOO_MANY_REQUESTS)
    
    serializer = ActivateLicenseSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # 提取请求数据
        license_key = serializer.validated_data['license_key']
        hardware_info = serializer.validated_data['hardware_info']
        client_info = serializer.validated_data.get('client_info', {})
        
        # 添加请求IP和User-Agent
        client_info['ip_address'] = get_client_ip(request)
        client_info['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
        
        # 检测可疑活动
        suspicious_check = detect_suspicious_activation(license_key, client_info)
        if suspicious_check['suspicious']:
            # 记录可疑活动
            SecurityAuditLog.objects.create(
                event_type='suspicious_activity',
                severity='HIGH',
                ip_address=client_info.get('ip_address'),
                user_agent=client_info.get('user_agent', ''),
                details={
                    'license_key_hash': SecurityService().hash_manager.hash_data(license_key),
                    'reason': suspicious_check['reason'],
                    'hardware_info_summary': {
                        'os': hardware_info.get('system_info', {}).get('os_version', 'Unknown'),
                        'hostname': hardware_info.get('system_info', {}).get('hostname', 'Unknown')
                    }
                }
            )
            
            return Response({
                'success': False,
                'error': 'Activation request flagged for review',
                'code': 'SUSPICIOUS_ACTIVITY'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # 执行激活
        activation_service = LicenseActivationService()
        result = activation_service.activate_license(
            license_key=license_key,
            hardware_info=hardware_info,
            client_info=client_info
        )
        
        if result['success']:
            logger.info(f"许可证激活成功: {result.get('machine_id')}")
            return Response({
                'success': True,
                'message': 'License activated successfully',
                'data': {
                    'activation_code': result['activation_code'],
                    'machine_id': result['machine_id'],
                    'expires_at': result['expires_at'],
                    'features': result['features']
                }
            })
        else:
            logger.warning(f"许可证激活失败: {result.get('error', 'Unknown error')}")
            return Response({
                'success': False,
                'error': result.get('error', 'Activation failed'),
                'code': result.get('code', 'ACTIVATION_ERROR')
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"激活请求处理异常: {str(e)}")
        return Response({
            'success': False,
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['许可证激活API'],
    summary='验证激活状态',
    description='验证许可证激活状态，检查激活码和机器指纹匹配',
    request=VerifyActivationSerializer,
    responses={
        200: OpenApiResponse(
            description='验证成功',
            examples=[
                OpenApiExample(
                    'Verification Success',
                    value={
                        'valid': True,
                        'license_info': {
                            'product': 'MyProduct 1.0',
                            'plan': 'Standard',
                            'expires_at': '2024-12-31T23:59:59Z',
                            'features': {'feature1': True}
                        },
                        'last_verified': '2024-01-15T10:30:00Z'
                    }
                )
            ]
        ),
        400: OpenApiResponse(description='验证失败')
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def verify_activation(request):
    """
    验证激活状态
    
    POST /api/v1/licenses/verify/
    """
    serializer = VerifyActivationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        activation_code = serializer.validated_data['activation_code']
        machine_fingerprint = serializer.validated_data['machine_fingerprint']
        
        # 检查缓存
        cache_key = f"activation_verify:{activation_code}:{machine_fingerprint[:8]}"
        cached_result = cache.get(cache_key)
        
        if cached_result:
            logger.debug(f"验证缓存命中: {activation_code}")
            return Response(cached_result)
        
        # 执行验证
        activation_service = LicenseActivationService()
        result = activation_service.verify_activation(
            activation_code=activation_code,
            machine_fingerprint=machine_fingerprint
        )
        
        if result['valid']:
            response_data = {
                'valid': True,
                'license_info': {
                    'product': result['product'],
                    'plan': result['plan'],
                    'expires_at': result['expires_at'],
                    'features': result['features']
                },
                'last_verified': result['last_verified']
            }
            
            # 缓存验证结果（5分钟）
            cache.set(cache_key, response_data, 300)
            
            logger.debug(f"激活验证成功: {activation_code}")
            return Response(response_data)
        else:
            logger.warning(f"激活验证失败: {result.get('error', 'Unknown error')}")
            return Response({
                'valid': False,
                'error': result.get('error', 'Verification failed'),
                'code': result.get('code', 'VERIFICATION_ERROR')
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except Exception as e:
        logger.error(f"验证请求处理异常: {str(e)}")
        return Response({
            'valid': False,
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['许可证激活API'],
    summary='许可证心跳',
    description='发送许可证使用心跳，更新最后使用时间和状态信息',
    request=HeartbeatSerializer,
    responses={
        200: OpenApiResponse(
            description='心跳成功',
            examples=[
                OpenApiExample(
                    'Heartbeat Success',
                    value={
                        'success': True,
                        'message': 'Heartbeat received',
                        'server_time': '2024-01-15T10:30:00Z',
                        'license_status': 'active'
                    }
                )
            ]
        ),
        400: OpenApiResponse(description='心跳失败')
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def heartbeat(request):
    """
    发送心跳检测
    
    POST /api/v1/licenses/heartbeat/
    """
    serializer = HeartbeatSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        activation_code = serializer.validated_data['activation_code']
        event_type = serializer.validated_data['event_type']
        event_data = serializer.validated_data.get('event_data', {})
        software_version = serializer.validated_data.get('software_version', '')
        session_id = serializer.validated_data.get('session_id', '')
        system_status = serializer.validated_data.get('system_status', {})
        
        # 查找激活记录
        try:
            activation = LicenseActivation.objects.select_related(
                'license', 'machine_binding'
            ).get(activation_code=activation_code, result='success')
        except LicenseActivation.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Invalid activation code',
                'code': 'INVALID_ACTIVATION'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 检查许可证状态
        if activation.license.status != 'activated':
            return Response({
                'success': False,
                'error': f'License is {activation.license.status}',
                'code': 'LICENSE_INACTIVE'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 创建使用日志
        usage_log = LicenseUsageLog.objects.create(
            license=activation.license,
            machine_binding=activation.machine_binding,
            event_type=event_type,
            event_data=event_data,
            software_version=software_version,
            session_id=session_id,
            cpu_usage=system_status.get('cpu_usage'),
            memory_usage=system_status.get('memory_usage'),
            ip_address=get_client_ip(request)
        )
        
        # 更新机器绑定的最后活跃时间
        activation.machine_binding.last_seen_at = timezone.now()
        activation.machine_binding.save(update_fields=['last_seen_at'])
        
        # 更新许可证的最后验证时间
        activation.license.last_verified_at = timezone.now()
        activation.license.save(update_fields=['last_verified_at'])
        
        # 检查许可证是否即将过期
        days_until_expiry = None
        if activation.license.expires_at:
            delta = activation.license.expires_at - timezone.now()
            days_until_expiry = delta.days
        
        response_data = {
            'success': True,
            'message': 'Heartbeat recorded',
            'license_status': {
                'status': activation.license.status,
                'expires_at': activation.license.expires_at.isoformat() if activation.license.expires_at else None,
                'days_until_expiry': days_until_expiry
            },
            'timestamp': timezone.now().isoformat()
        }
        
        # 如果即将过期，添加警告
        if days_until_expiry is not None and days_until_expiry <= 30:
            response_data['warnings'] = [
                f'License will expire in {days_until_expiry} days'
            ]
        
        logger.debug(f"心跳记录成功: {activation_code} - {event_type}")
        return Response(response_data)
    
    except Exception as e:
        logger.error(f"心跳请求处理异常: {str(e)}")
        return Response({
            'success': False,
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['许可证信息查询'],
    summary='获取许可证信息',
    description='根据许可证密钥获取许可证详细信息（不敏感信息）',
    parameters=[
        OpenApiParameter(
            name='license_key',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.PATH,
            description='许可证密钥',
            required=True
        )
    ],
    responses={
        200: OpenApiResponse(
            description='信息获取成功',
            examples=[
                OpenApiExample(
                    'License Info Success',
                    value={
                        'success': True,
                        'license_info': {
                            'product': {'name': 'MyProduct', 'version': '1.0'},
                            'plan': 'Standard',
                            'expires_at': '2024-12-31T23:59:59Z',
                            'features': {'feature1': True},
                            'status': 'active'
                        }
                    }
                )
            ]
        ),
        404: OpenApiResponse(description='许可证未找到')
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def license_info(request, license_key):
    """
    获取许可证信息
    
    GET /api/v1/licenses/info/<license_key>/
    """
    # 验证许可证密钥格式
    if len(license_key.replace('-', '')) < 10:
        return Response({
            'success': False,
            'error': 'Invalid license key format'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # 查找许可证
    from licenses.models import License
    
    try:
        # 通过许可证密钥直接查找（UUID格式不需要复杂验证）
        license_obj = License.objects.select_related('product', 'plan').get(
            license_key=license_key,
            is_deleted=False
        )
        
        # 返回基本信息
        return Response({
            'success': True,
            'license_info': {
                'product': {
                    'name': license_obj.product.name,
                    'version': license_obj.product.version
                },
                'plan': {
                    'name': license_obj.plan.name,
                    'type': license_obj.plan.plan_type,
                    'default_max_activations': license_obj.plan.default_max_activations
                },
                'status': license_obj.status,
                'issued_at': license_obj.issued_at.isoformat(),
                'expires_at': license_obj.expires_at.isoformat() if license_obj.expires_at else None,
                'max_activations': license_obj.max_activations
            }
        })
        
    except License.DoesNotExist:
        return Response({
            'success': False,
            'error': 'License not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"许可证信息获取异常: {str(e)}")
        return Response({
            'success': False,
            'error': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['许可证服务状态'],
    summary='获取服务器状态',
    description='获取许可证服务器的运行状态和基本信息',
    responses={
        200: OpenApiResponse(
            description='服务器状态信息',
            examples=[
                OpenApiExample(
                    'Server Status',
                    value={
                        'status': 'online',
                        'version': '1.0.0',
                        'server_time': '2024-01-15T10:30:00Z',
                        'uptime': '5 days, 2 hours',
                        'maintenance_mode': False
                    }
                )
            ]
        )
    }
)
@api_view(['GET'])
@permission_classes([AllowAny])
def server_status(request):
    """
    获取服务器状态
    
    GET /api/v1/licenses/status/
    """
    try:
        # 检查数据库连接
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # 检查缓存
        cache_status = 'ok'
        try:
            cache.set('health_check', 'ok', 60)
            cache.get('health_check')
        except Exception:
            cache_status = 'error'
        
        return Response({
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'services': {
                'database': 'ok',
                'cache': cache_status
            },
            'version': '1.0.0'
        })
    
    except Exception as e:
        logger.error(f"服务状态检查异常: {str(e)}")
        return Response({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


def get_client_ip(request):
    """获取客户端IP地址"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def detect_suspicious_activation(license_key: str, client_info: dict) -> dict:
    """
    检测可疑的激活行为
    
    Args:
        license_key: 许可证密钥
        client_info: 客户端信息
        
    Returns:
        dict: 检测结果
    """
    try:
        ip_address = client_info.get('ip_address')
        
        # 检查同一IP的激活频率
        if ip_address:
            recent_activations = LicenseActivation.objects.filter(
                ip_address=ip_address,
                activated_at__gte=timezone.now() - timezone.timedelta(hours=1)
            ).count()
            
            if recent_activations >= 5:
                return {
                    'suspicious': True,
                    'reason': 'High activation frequency from same IP'
                }
        
        # 检查许可证密钥的激活频率
        license_hash = SecurityService().hash_manager.hash_data(license_key)
        try:
            from licenses.models import License
            license_obj = License.objects.get(license_hash=license_hash)
            recent_license_activations = LicenseActivation.objects.filter(
                license=license_obj,
                activated_at__gte=timezone.now() - timezone.timedelta(minutes=30)
            ).count()
            
            if recent_license_activations >= 3:
                return {
                    'suspicious': True,
                    'reason': 'Multiple activation attempts for same license'
                }
        except License.DoesNotExist:
            pass
        
        return {'suspicious': False}
    
    except Exception as e:
        logger.error(f"可疑活动检测异常: {str(e)}")
        return {'suspicious': False}
