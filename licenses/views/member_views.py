"""
Member用户许可证申请API视图
提供试用许可证申请、可申请产品列表、用户许可证查看等功能
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.core.cache import cache
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

from licenses.serializers import (
    AvailableProductSerializer, LicenseApplicationSerializer,
    MemberLicenseSerializer, MemberLicenseListSerializer,
    MemberMachineBindingSerializer, UnbindDeviceRequestSerializer
)
from licenses.services.member_license_service import (
    MemberLicenseApplicationService, MemberLicenseManagementService
)
from licenses.models import SoftwareProduct
from common.permissions import IsMemberUser, CanApplyTrialLicense
import logging

logger = logging.getLogger('licenses.member')


class MemberTrialApplicationThrottle(UserRateThrottle):
    """Member试用申请频率限制"""
    scope = 'member_trial_application'
    
    @property
    def rate(self):
        """从配置文件动态获取频率限制"""
        from licenses.config import APPLICATION_RATE_LIMITS
        daily_limit = APPLICATION_RATE_LIMITS.get('daily_limit', 5)
        return f'{daily_limit}/day'


class MemberAPIThrottle(UserRateThrottle):
    """Member API通用频率限制"""
    scope = 'member_api'
    rate = '100/hour'  # 每小时最多100次请求


@extend_schema(
    tags=['Member许可证API'],
    summary='获取可申请的试用产品列表',
    description='''
    获取currentMember用户可以申请试用许可证的产品列表

    ## 业务规则

    1. **产品筛选** - 只显示有试用方案且状态为活跃的产品
    2. **租户隔离** - 仅显示current用户租户下的产品
    3. **申请状态** - 标记用户是否已申请过该产品
    4. **方案信息** - 包含试用方案的详细配置信息

    ## 权限要求

    - 需要JWT认证
    - 必须是Member用户身份
    - 用户和租户状态必须为活跃

    ## 响应说明

    返回产品列表，每个产品包含：
    - 产品基本信息（名称、描述、版本等）
    - 试用方案配置（有效期、激活数、功能等）
    - 用户申请状态（是否已申请）

    ## 使用场景

    - 用户浏览可申请的试用产品
    - 前端展示产品选择界面
    - 检查申请资格和状态
    ''',
    responses={
        200: OpenApiResponse(
            description='获取成功',
            examples=[
                OpenApiExample(
                    'Success Response',
                    value={
                        'success': True,
                        'data': {
                            'count': 3,
                            'products': [
                                {
                                    'id': 1,
                                    'name': 'PDF压缩工具',
                                    'code': 'pdf_compress',
                                    'description': '高效的PDF文件压缩工具',
                                    'version': '1.2.0',
                                    'trial_plan': {
                                        'id': 10,
                                        'name': '试用版',
                                        'default_validity_days': 30,
                                        'default_max_activations': 1,
                                        'features': {'compression_level': 'basic'},
                                        'price': 0.0,
                                        'currency': 'CNY'
                                    },
                                    'already_applied': False
                                }
                            ]
                        }
                    }
                )
            ]
        ),
        401: OpenApiResponse(
            description='未认证',
            examples=[
                OpenApiExample(
                    'Unauthorized',
                    value={'detail': 'Authentication credentials were not provided.'}
                )
            ]
        ),
        403: OpenApiResponse(
            description='权限不足',
            examples=[
                OpenApiExample(
                    'Permission Denied',
                    value={'detail': 'You do not have permission to perform this action.'}
                )
            ]
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsMemberUser])
@throttle_classes([MemberAPIThrottle])
def available_products(request):
    """
    获取可申请的试用产品列表
    
    GET /api/v1/licenses/member/available-products/
    """
    try:
        # 获取Member用户可申请的产品
        application_service = MemberLicenseApplicationService()
        products = application_service.get_available_products(request.user)
        
        # 序列化产品数据
        serializer = AvailableProductSerializer(
            products, 
            many=True,
            context={'request': request}
        )
        
        logger.info(f"Member {request.user.username} 获取可申请产品列表，共 {len(products)} 个产品")
        
        return Response({
            'success': True,
            'data': {
                'count': len(products),
                'products': serializer.data
            }
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"获取可申请产品列表失败: {str(e)}")
        return Response({
            'success': False,
            'error': '获取产品列表失败，请稍后重试',
            'code': 'FETCH_PRODUCTS_FAILED'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['Member许可证API'],
    summary='申请试用许可证',
    description='''
    Member用户申请指定产品的试用许可证

    ## 业务流程

    1. **参数验证** - 验证产品ID和申请信息
    2. **资格检查** - 检查用户是否有申请资格
    3. **重复检查** - 确保用户未重复申请该产品
    4. **配额验证** - 检查用户和租户配额限制
    5. **频率控制** - 防止频繁申请（24小时内最多3次）
    6. **许可证生成** - 自动生成试用许可证
    7. **分配关系** - 创建用户与许可证的分配关系
    8. **通知发送** - 发送申请成功通知（可选）

    ## 权限要求

    - 需要JWT认证
    - 必须是Member用户身份  
    - 具有试用许可证申请权限
    - 用户和租户状态必须为活跃

    ## 业务限制

    - 每个产品只能申请一次试用许可证
    - 24小时内最多申请3次
    - 用户最多持有1个试用许可证（可配置）
    - 产品必须有可用的试用方案

    ## 自动化处理

    - 试用版申请自动通过，无需人工审批
    - 许可证自动生成，立即可用
    - 有效期根据方案配置自动设置

    ## 使用场景

    - 用户申请产品试用
    - 自动化试用流程
    - 快速体验产品功能
    ''',
    request=LicenseApplicationSerializer,
    responses={
        201: OpenApiResponse(
            description='申请成功',
            examples=[
                OpenApiExample(
                    'Application Success',
                    value={
                        'success': True,
                        'message': '试用许可证申请成功',
                        'data': {
                            'license_id': 123,
                            'assignment_id': 456,
                            'license_key': 'ABCDE-FGHIJ-KLMNO-PQRST-UVWXY',
                            'expires_at': '2024-02-15T10:30:00Z',
                            'product_name': 'PDF压缩工具',
                            'plan_name': '试用版',
                            'max_activations': 1
                        }
                    }
                )
            ]
        ),
        400: OpenApiResponse(
            description='申请失败 - 参数错误或业务规则限制',
            examples=[
                OpenApiExample(
                    'Already Applied',
                    value={
                        'success': False,
                        'error': 'You have already applied for a license for this product',
                        'code': 'APPLICATION_FAILED'
                    }
                ),
                OpenApiExample(
                    'Quota Exceeded',
                    value={
                        'success': False,
                        'error': 'Your trial license quota has been reached（1个）',
                        'code': 'APPLICATION_FAILED'
                    }
                ),
                OpenApiExample(
                    'Rate Limited',
                    value={
                        'success': False,
                        'error': '24hours. Too many applications, please try again later',
                        'code': 'APPLICATION_FAILED'
                    }
                )
            ]
        ),
        401: OpenApiResponse(
            description='未认证',
            examples=[
                OpenApiExample(
                    'Unauthorized',
                    value={'detail': 'Authentication credentials were not provided.'}
                )
            ]
        ),
        403: OpenApiResponse(
            description='权限不足',
            examples=[
                OpenApiExample(
                    'Permission Denied',
                    value={'detail': 'You do not have permission to perform this action.'}
                )
            ]
        ),
        429: OpenApiResponse(
            description='请求频率限制',
            examples=[
                OpenApiExample(
                    'Throttled',
                    value={'detail': 'Request was throttled. Expected available in 3600 seconds.'}
                )
            ]
        ),
        500: OpenApiResponse(
            description='服务器内部错误',
            examples=[
                OpenApiExample(
                    'Internal Error',
                    value={
                        'success': False,
                        'error': '系统内部错误，请稍后重试',
                        'code': 'INTERNAL_ERROR'
                    }
                )
            ]
        )
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsMemberUser, CanApplyTrialLicense])
@throttle_classes([MemberTrialApplicationThrottle])
@csrf_exempt
def apply_trial_license(request):
    """
    申请试用许可证
    
    POST /api/v1/licenses/member/apply/
    """
    # 验证请求数据
    serializer = LicenseApplicationSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if not serializer.is_valid():
        logger.warning(f"Member {request.user.username} 试用许可证申请数据验证失败: {serializer.errors}")
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # 处理申请
        application_service = MemberLicenseApplicationService()
        result = application_service.apply_trial_license(
            member=request.user,
            product_id=serializer.validated_data['product_id'],
            plan_id=serializer.validated_data.get('plan_id'),  # 新增：支持指定方案ID
            reason=serializer.validated_data.get('reason', '试用版申请'),
            user_info=serializer.validated_data.get('user_info')
        )
        
        if result['success']:
            logger.info(f"Member {request.user.username} 试用许可证申请成功: {result['data']['license_id']}")
            return Response(result, status=status.HTTP_201_CREATED)
        else:
            logger.warning(f"Member {request.user.username} 试用许可证申请失败: {result['error']}")
            return Response(result, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"试用许可证申请异常: {str(e)}")
        return Response({
            'success': False,
            'error': '申请处理失败，请稍后重试',
            'code': 'APPLICATION_ERROR'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['Member许可证API'],
    summary='查看我的许可证',
    description='''
    获取currentMember用户的所有许可证列表及统计信息

    ## 返回信息

    1. **许可证列表** - 按创建时间倒序排列
    2. **统计信息** - 总数、有效数、试用数、即将过期数
    3. **详细状态** - 每个许可证的状态和激活信息
    4. **有效期信息** - 距离过期天数和时间

    ## 许可证信息包含

    - **基本信息**: 产品名称、版本、方案类型
    - **许可证密钥**: 仅显示部分密钥，保护隐私
    - **状态信息**: current状态、分配时间、过期时间
    - **激活信息**: current激活数、最大激活数、可用配额
    - **使用权限**: 激活权限、停用权限、共享权限

    ## 权限要求

    - 需要JWT认证
    - 必须是Member用户身份
    - 只能查看自己的许可证

    ## 租户隔离

    - 自动按用户租户过滤数据
    - 确保跨租户数据安全

    ## 使用场景

    - 用户查看个人许可证
    - 管理激活设备
    - 监控有效期状态
    - 许可证使用统计
    ''',
    parameters=[
        OpenApiParameter(
            name='status',
            description='过滤许可证状态 (active/expired/revoked/pending)',
            required=False,
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY
        ),
        OpenApiParameter(
            name='plan_type',
            description='过滤方案类型 (trial/basic/professional/enterprise)',
            required=False,
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY
        )
    ],
    responses={
        200: OpenApiResponse(
            description='获取成功',
            examples=[
                OpenApiExample(
                    'Success Response',
                    value={
                        'success': True,
                        'data': {
                            'count': 2,
                            'active_count': 1,
                            'trial_count': 1,
                            'expiring_soon_count': 0,
                            'licenses': [
                                {
                                    'id': 456,
                                    'product_name': 'PDF压缩工具',
                                    'product_code': 'pdf_compress',
                                    'product_version': '1.2.0',
                                    'plan_name': '试用版',
                                    'plan_type': 'trial',
                                    'license_key_preview': 'ABCDE...VWXYZ',
                                    'status': 'active',
                                    'status_display': '有效',
                                    'assignment_type': 'direct',
                                    'assigned_at': '2024-01-15T10:30:00Z',
                                    'activated_at': '2024-01-15T10:30:00Z',
                                    'expires_at': '2024-02-15T10:30:00Z',
                                    'days_until_expiry': 25,
                                    'assignment_reason': '试用版申请',
                                    'can_activate_license': True,
                                    'activation_info': {
                                        'current_activations': 0,
                                        'max_activations': 1,
                                        'available_slots': 1
                                    },
                                    'usage_count': 5,
                                    'last_used_at': '2024-01-20T14:25:30Z',
                                    'last_heartbeat': '2024-01-20T14:25:30Z',
                                    'can_activate': True,
                                    'can_deactivate': False,
                                    'can_share': False,
                                    'max_devices_per_user': 1
                                }
                            ]
                        }
                    }
                )
            ]
        ),
        401: OpenApiResponse(
            description='未认证',
            examples=[
                OpenApiExample(
                    'Unauthorized',
                    value={'detail': 'Authentication credentials were not provided.'}
                )
            ]
        ),
        403: OpenApiResponse(
            description='权限不足',
            examples=[
                OpenApiExample(
                    'Permission Denied',
                    value={'detail': 'You do not have permission to perform this action.'}
                )
            ]
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsMemberUser])
@throttle_classes([MemberAPIThrottle])
def my_licenses(request):
    """
    查看我的许可证
    
    GET /api/v1/licenses/member/my-licenses/
    """
    try:
        # 获取查询参数
        status_filter = request.query_params.get('status')
        plan_type_filter = request.query_params.get('plan_type')
        
        # 获取用户许可证数据
        application_service = MemberLicenseApplicationService()
        license_data = application_service.get_member_licenses(request.user)
        
        # 应用过滤器
        licenses = license_data['licenses']
        if status_filter:
            licenses = [l for l in licenses if l.status == status_filter]
        if plan_type_filter:
            licenses = [l for l in licenses if l.license.plan.plan_type == plan_type_filter]
        
        # 重新计算统计信息（如果有过滤）
        if status_filter or plan_type_filter:
            filtered_count = len(licenses)
            filtered_active_count = sum(1 for l in licenses if l.status == 'active')
            filtered_trial_count = sum(1 for l in licenses if l.license.plan.plan_type == 'trial')
            
            # 计算即将过期数量
            seven_days_later = timezone.now() + timezone.timedelta(days=7)
            filtered_expiring_soon_count = sum(
                1 for l in licenses 
                if l.status == 'active' and l.expires_at and 
                l.expires_at <= seven_days_later and l.expires_at >= timezone.now()
            )
            
            license_data.update({
                'count': filtered_count,
                'active_count': filtered_active_count,
                'trial_count': filtered_trial_count,
                'expiring_soon_count': filtered_expiring_soon_count,
                'licenses': licenses
            })
        
        # 序列化许可证数据
        serializer = MemberLicenseSerializer(
            license_data['licenses'], 
            many=True,
            context={'request': request}
        )
        
        response_data = {
            'count': license_data['count'],
            'active_count': license_data['active_count'],
            'trial_count': license_data['trial_count'],
            'expiring_soon_count': license_data['expiring_soon_count'],
            'licenses': serializer.data
        }
        
        logger.info(f"Member {request.user.username} 查看许可证列表，共 {license_data['count']} 个许可证")
        
        return Response({
            'success': True,
            'data': response_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"获取用户许可证列表失败: {str(e)}")
        return Response({
            'success': False,
            'error': '获取许可证列表失败，请稍后重试',
            'code': 'FETCH_LICENSES_FAILED'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['Member许可证API'],
    summary='查看许可证的设备列表',
    description='''
    获取Member用户指定许可证的所有设备绑定列表及统计信息
    
    ## 业务说明
    
    1. **权限验证** - 仅能查看自己拥有的许可证设备
    2. **设备信息** - 返回所有绑定设备的详细信息
    3. **状态统计** - 活跃、非活跃、已阻止设备的数量统计
    4. **许可证信息** - 包含激活配额和有效期信息
    
    ## 权限要求
    
    - 需要JWT认证
    - 必须是Member用户身份
    - 只能查看自己被分配的许可证
    
    ## 租户隔离
    
    - 自动按用户租户过滤数据
    - 确保跨租户数据安全
    
    ## 使用场景
    
    - 用户查看已激活的设备列表
    - 管理设备激活配额
    - 准备解绑不使用的设备
    ''',
    parameters=[
        OpenApiParameter(
            name='license_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.PATH,
            description='许可证分配ID（从 my-licenses 接口返回的 id 字段）',
            required=True
        )
    ],
    responses={
        200: OpenApiResponse(
            description='获取成功',
            examples=[
                OpenApiExample(
                    'Success Response',
                    value={
                        'success': True,
                        'data': {
                            'license_info': {
                                'id': 123,
                                'product_name': 'PDF压缩工具',
                                'plan_name': '试用版',
                                'max_activations': 3,
                                'current_activations': 2,
                                'available_slots': 1,
                                'expires_at': '2024-02-15T10:30:00Z'
                            },
                            'statistics': {
                                'total': 3,
                                'active': 2,
                                'inactive': 1,
                                'blocked': 0
                            },
                            'devices': [
                                {
                                    'id': 456,
                                    'machine_id': 'MACHINE-ABC123',
                                    'machine_fingerprint': 'fp-hash-12345',
                                    'os_name': 'Windows 11',
                                    'os_info': {'os_name': 'Windows', 'os_version': '11'},
                                    'hardware_summary': {'cpu': 'Intel i7', 'ram': '16GB'},
                                    'last_ip_address': '192.168.1.100',
                                    'status': 'active',
                                    'status_display': '活跃',
                                    'first_seen_at': '2024-01-15T10:30:00Z',
                                    'last_seen_at': '2024-01-20T14:25:30Z',
                                    'days_since_last_seen': 0
                                }
                            ],
                            'permissions': {
                                'can_unbind': True
                            }
                        }
                    }
                )
            ]
        ),
        400: OpenApiResponse(
            description='请求错误',
            examples=[
                OpenApiExample(
                    'License Not Found',
                    value={
                        'success': False,
                        'error': '许可证不存在或您无权访问',
                        'code': 'LICENSE_NOT_FOUND'
                    }
                )
            ]
        ),
        401: OpenApiResponse(
            description='未认证',
            examples=[
                OpenApiExample(
                    'Unauthorized',
                    value={'detail': 'Authentication credentials were not provided.'}
                )
            ]
        ),
        403: OpenApiResponse(
            description='权限不足',
            examples=[
                OpenApiExample(
                    'Permission Denied',
                    value={'detail': 'You do not have permission to perform this action.'}
                )
            ]
        ),
        500: OpenApiResponse(
            description='服务器内部错误',
            examples=[
                OpenApiExample(
                    'Internal Error',
                    value={
                        'success': False,
                        'error': '获取设备列表失败，请稍后重试',
                        'code': 'FETCH_DEVICES_FAILED'
                    }
                )
            ]
        )
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsMemberUser])
@throttle_classes([MemberAPIThrottle])
def my_license_devices(request, license_id):
    """
    查看许可证的设备列表
    
    GET /api/v1/licenses/member/my-licenses/<license_id>/devices/
    """
    try:
        # 调用服务获取设备列表
        management_service = MemberLicenseManagementService()
        result = management_service.get_license_devices(request.user, license_id)
        
        # 序列化设备数据
        devices_serializer = MemberMachineBindingSerializer(
            result['devices'],
            many=True,
            context={'request': request}
        )
        
        response_data = {
            'license_info': result['license_info'],
            'statistics': result['statistics'],
            'devices': devices_serializer.data,
            'permissions': result['permissions']
        }
        
        logger.info(
            f"Member {request.user.username} 查看许可证 {license_id} 的设备列表，"
            f"共 {result['statistics']['total']} 台设备"
        )
        
        return Response({
            'success': True,
            'data': response_data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        from common.exceptions import LicenseException
        
        if isinstance(e, LicenseException):
            logger.warning(f"查看设备列表失败: {e.detail}")
            return Response({
                'success': False,
                'error': e.detail,
                'code': e.error_code
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.error(f"查看设备列表失败: {str(e)}")
        return Response({
            'success': False,
            'error': '获取设备列表失败，请稍后重试',
            'code': 'FETCH_DEVICES_FAILED'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['Member许可证API'],
    summary='解绑设备',
    description='''
    Member用户解绑自己许可证下的指定设备，释放激活配额
    
    ## 业务流程
    
    1. **权限验证** - 验证许可证归属和用户权限
    2. **设备验证** - 确认设备属于该许可证且状态为活跃
    3. **执行解绑** - 将设备状态设为非活跃
    4. **更新配额** - 减少许可证的当前激活数
    5. **审计记录** - 记录解绑操作到安全审计日志
    
    ## 权限要求
    
    - 需要JWT认证
    - 必须是Member用户身份
    - 只能解绑自己拥有的许可证设备
    
    ## 业务规则
    
    - 只能解绑状态为"活跃"的设备
    - 解绑后设备状态变为"非活跃"
    - 自动更新许可证的可用激活配额
    - 保留设备绑定记录用于审计
    
    ## 安全机制
    
    - 记录详细的审计日志
    - 频率限制防止滥用
    - 租户隔离自动校验
    
    ## 使用场景
    
    - 用户更换设备前解绑旧设备
    - 释放激活配额给新设备使用
    - 清理不再使用的设备绑定
    ''',
    request=UnbindDeviceRequestSerializer,
    responses={
        200: OpenApiResponse(
            description='解绑成功',
            examples=[
                OpenApiExample(
                    'Unbind Success',
                    value={
                        'success': True,
                        'message': '设备解绑成功',
                        'data': {
                            'license_id': 123,
                            'machine_binding_id': 456,
                            'machine_id': 'MACHINE-ABC123',
                            'unbound_at': '2024-01-20T15:30:00Z',
                            'reason': '用户主动解绑',
                            'remaining_activations': 1,
                            'max_activations': 3,
                            'available_slots': 2
                        }
                    }
                )
            ]
        ),
        400: OpenApiResponse(
            description='解绑失败 - 参数错误或业务规则限制',
            examples=[
                OpenApiExample(
                    'License Not Found',
                    value={
                        'success': False,
                        'error': '许可证不存在或您无权访问',
                        'code': 'LICENSE_NOT_FOUND'
                    }
                ),
                OpenApiExample(
                    'Device Not Found',
                    value={
                        'success': False,
                        'error': '设备不存在或不属于该许可证',
                        'code': 'DEVICE_NOT_FOUND'
                    }
                ),
                OpenApiExample(
                    'Device Not Active',
                    value={
                        'success': False,
                        'error': '设备当前状态为非活跃，无法解绑',
                        'code': 'DEVICE_NOT_ACTIVE'
                    }
                )
            ]
        ),
        401: OpenApiResponse(
            description='未认证',
            examples=[
                OpenApiExample(
                    'Unauthorized',
                    value={'detail': 'Authentication credentials were not provided.'}
                )
            ]
        ),
        403: OpenApiResponse(
            description='权限不足',
            examples=[
                OpenApiExample(
                    'Permission Denied',
                    value={'detail': 'You do not have permission to perform this action.'}
                )
            ]
        ),
        429: OpenApiResponse(
            description='请求频率限制',
            examples=[
                OpenApiExample(
                    'Throttled',
                    value={'detail': 'Request was throttled. Expected available in 3600 seconds.'}
                )
            ]
        ),
        500: OpenApiResponse(
            description='服务器内部错误',
            examples=[
                OpenApiExample(
                    'Internal Error',
                    value={
                        'success': False,
                        'error': '设备解绑失败，请稍后重试',
                        'code': 'UNBIND_FAILED'
                    }
                )
            ]
        )
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsMemberUser])
@throttle_classes([MemberAPIThrottle])
@csrf_exempt
def unbind_device(request):
    """
    解绑设备
    
    POST /api/v1/licenses/member/unbind-device/
    """
    # 验证请求数据
    serializer = UnbindDeviceRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        logger.warning(f"Member {request.user.username} 解绑设备数据验证失败: {serializer.errors}")
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # 提取请求数据
        license_id = serializer.validated_data['license_id']
        machine_binding_id = serializer.validated_data['machine_binding_id']
        reason = serializer.validated_data.get('reason', '用户主动解绑')
        
        # 构建客户端信息
        client_info = {
            'ip_address': get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', '')
        }
        
        # 调用服务执行解绑
        management_service = MemberLicenseManagementService()
        result = management_service.unbind_device(
            member=request.user,
            license_id=license_id,
            machine_binding_id=machine_binding_id,
            reason=reason,
            client_info=client_info
        )
        
        logger.info(
            f"Member {request.user.username} 成功解绑设备: "
            f"许可证 {license_id}, 设备 {machine_binding_id}"
        )
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        from common.exceptions import LicenseException
        
        if isinstance(e, LicenseException):
            logger.warning(f"解绑设备失败: {e.detail}")
            return Response({
                'success': False,
                'error': e.detail,
                'code': e.error_code
            }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.error(f"解绑设备失败: {str(e)}")
        return Response({
            'success': False,
            'error': '设备解绑失败，请稍后重试',
            'code': 'UNBIND_FAILED'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def get_client_ip(request):
    """获取客户端IP地址"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
