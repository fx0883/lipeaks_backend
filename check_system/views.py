"""
打卡系统视图
"""
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample, OpenApiResponse, OpenApiTypes
import logging

from common.permissions import IsSuperAdminUser, IsAdminUser
from common.utils.user_permissions import is_super_admin, is_admin
from common.pagination import StandardResultsSetPagination
from common.authentication.api_auth import APIJWTAuthentication
from common.viewsets import TenantModelViewSet
from users.models import User
from .models import TaskCategory, Task, CheckRecord, TaskTemplate
from .serializers import (
    TaskCategorySerializer, TaskSerializer, 
    CheckRecordSerializer, TaskTemplateSerializer
)
from .permissions import (
    TaskCategoryPermission, TaskPermission,
    CheckRecordPermission, TaskTemplatePermission
)

logger = logging.getLogger(__name__)


@extend_schema_view(
    list=extend_schema(
        summary="获取打卡类型列表",
        description="获取打卡类型列表，支持分页、过滤和搜索",
        tags=["打卡系统-类型管理"],
        parameters=[
            OpenApiParameter(name="is_system", description="是否为系统预设类型", required=False, type=bool),
            OpenApiParameter(name="search", description="搜索关键词", required=False, type=str),
        ],
        examples=[
            OpenApiExample(
                'List Categories Example',
                summary='获取打卡类型列表示例',
                description='获取打卡类型列表，支持分页、过滤和搜索',
                value={
                    'page': 1,
                    'page_size': 10,
                    'is_system': True,
                    'search': '早起'
                }
            )
        ]
    ),
    retrieve=extend_schema(
        summary="获取打卡类型详情",
        description="获取单个打卡类型的详细信息",
        tags=["打卡系统-类型管理"]
    ),
    create=extend_schema(
        summary="创建打卡类型",
        description="创建新的打卡类型",
        tags=["打卡系统-类型管理"],
        examples=[
            OpenApiExample(
                'Custom Category Example',
                summary='自定义打卡类型示例',
                description='创建一个自定义的打卡类型',
                value={
                    'name': '早起打卡',
                    'description': '每天早上6点前起床打卡',
                    'is_system': False,
                    'icon': 'sunrise',
                    'translations': {
                        'en': {
                            'name': 'Early Rising',
                            'description': 'Check in before 6:00 AM every day'
                        },
                        'zh-hans': {
                            'name': '早起打卡',
                            'description': '每天早上6点前起床打卡'
                        }
                    }
                }
            ),
            OpenApiExample(
                'System Category Example',
                summary='系统预设类型示例',
                description='创建一个系统预设的打卡类型（仅供超级管理员使用）',
                value={
                    'name': '健身打卡',
                    'description': '记录每天的健身情况',
                    'is_system': True,
                    'icon': 'dumbbell',
                    'translations': {
                        'en': {
                            'name': 'Fitness',
                            'description': 'Record daily workout activities'
                        },
                        'zh-hans': {
                            'name': '健身打卡',
                            'description': '记录每天的健身情况'
                        }
                    }
                }
            )
        ]
    ),
    update=extend_schema(
        summary="更新打卡类型",
        description="更新现有打卡类型的所有字段",
        tags=["打卡系统-类型管理"],
        parameters=[

        ],
        examples=[
            OpenApiExample(
                'Update Category Example',
                summary='更新打卡类型示例',
                description='更新现有打卡类型的所有字段',
                value={
                    'name': '早起打卡',
                    'description': '每天早上6点前起床打卡，养成早起好习惯',
                    'is_system': False,
                    'icon': 'sunrise',
                    'translations': {
                        'en': {
                            'name': 'Early Rising',
                            'description': 'Check in before 6:00 AM every day, develop a habit of early rising'
                        },
                        'zh-hans': {
                            'name': '早起打卡',
                            'description': '每天早上6点前起床打卡，养成早起好习惯'
                        }
                    }
                }
            )
        ]
    ),
    partial_update=extend_schema(
        summary="部分更新打卡类型",
        description="更新现有打卡类型的部分字段",
        tags=["打卡系统-类型管理"],
        parameters=[


        ],
        examples=[
            OpenApiExample(
                'Partial Update Category Example',
                summary='部分更新打卡类型示例',
                description='仅更新打卡类型的描述字段',
                value={
                    'description': '每天早上6点前起床打卡，养成早起好习惯，提高效率',
                    'translations': {
                        'en': {
                            'description': 'Check in before 6:00 AM every day, develop a habit of early rising, improve efficiency'
                        },
                        'zh-hans': {
                            'description': '每天早上6点前起床打卡，养成早起好习惯，提高效率'
                        }
                    }
                }
            )
        ]
    ),
    destroy=extend_schema(
        summary="删除打卡类型",
        description="删除现有打卡类型",
        tags=["打卡系统-类型管理"],
        parameters=[


        ],
        examples=[
            OpenApiExample(
                'Delete Category Example',
                summary='删除打卡类型示例',
                description='删除现有打卡类型',
                value={
                    'id': 1
                }
            )
        ]
    ),
)
class TaskCategoryViewSet(TenantModelViewSet):
    """
    打卡类型视图集，提供增删改查API
    
    继承TenantModelViewSet自动处理租户过滤、设置和验证
    
    可以管理系统预设和用户自定义的打卡类型，支持多语言。
    - 普通用户: 可以查看系统预设类型和自己创建的类型
    - 租户管理员: 可以查看系统预设类型和该租户下的所有类型
    - 超级管理员: 可以查看所有类型
    """
    queryset = TaskCategory.objects.all().select_related('user', 'tenant')
    serializer_class = TaskCategorySerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_system']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'name']
    ordering = ['-created_at']
    authentication_classes = [APIJWTAuthentication]
    permission_classes = [TaskCategoryPermission]
    
    def get_queryset(self):
        """
        获取查询集，先调用父类获取租户过滤的queryset
        然后根据用户角色应用额外过滤逻辑
        """
        # 获取租户过滤后的基础queryset
        queryset = super().get_queryset()
            
        user = self.request.user
        
        # 超级管理员已经在父类中处理，返回所有
        if user.is_superuser:
            return queryset
        
        # 租户管理员：系统预设 + 租户数据（租户过滤已在父类处理）
        if is_admin(user):
            return queryset.filter(Q(is_system=True) | Q(tenant=user.tenant))
        
        # 普通用户：系统预设 + 自己创建
        return queryset.filter(Q(is_system=True) | Q(user=user))
        
    def perform_create(self, serializer):
        """
        创建类型时自动关联current用户和租户
        根据角色处理user_id参数
        """
        user = self.request.user
        data = self.request.data
        
        logger.info(f"【开始创建打卡类型】用户ID: {user.id}，用户名: {user.username}，请求数据: {data}")
        
        # 确保用户关联了租户
        if not hasattr(user, 'tenant') or not user.tenant:
            error_msg = "用户未关联租户，无法创建类型"
            logger.error(f"【创建打卡类型失败】{error_msg}，用户ID: {user.id}")
            raise serializers.ValidationError(_(error_msg))
        
        logger.debug(f"【创建打卡类型】用户关联的租户: {user.tenant.name} (ID: {user.tenant.id})")
        
        # 检查是否为系统预设类型
        is_system = data.get('is_system', False)
        if is_system:
            logger.info(f"【创建打卡类型】创建系统预设类型，不关联用户")
            # 系统预设类型不关联用户，只关联租户
            instance = serializer.save(
                user=None,  # 不关联用户
                tenant=user.tenant
            )
            logger.info(f"【创建打卡类型成功】ID: {instance.id}，名称: {instance.name}，系统预设类型，租户: {user.tenant.name}")
            return
        
        # 获取user_id
        user_id = data.get('user_id') or data.get('user')
        logger.debug(f"【创建打卡类型】指定的用户ID: {user_id}")
        
        if is_admin(user):
            logger.debug(f"【创建打卡类型】用户是租户管理员，可以为租户内的任意用户创建")
            # 租户管理员：可以指定用户，但必须属于同一租户
            if user_id:
                try:
                    target_user = User.objects.get(id=user_id)
                    logger.debug(f"【创建打卡类型】找到目标用户: {target_user.username} (ID: {target_user.id})")
                    
                    # 检查目标用户是否属于同一租户
                    if target_user.tenant != user.tenant:
                        error_msg = "无法为其他租户的用户创建类型"
                        logger.error(f"【创建打卡类型失败】{error_msg}，目标用户租户: {target_user.tenant.name if target_user.tenant else 'None'}")
                        raise serializers.ValidationError(_(error_msg))
                    
                    logger.info(f"【创建打卡类型】即将创建打卡类型，关联用户: {target_user.username}，租户: {user.tenant.name}")
                    # 设置用户和租户(始终使用目标用户的租户)
                    instance = serializer.save(
                        user=target_user, 
                        tenant=user.tenant  # 强制使用current租户管理员的租户
                    )
                    logger.info(f"【创建打卡类型成功】ID: {instance.id}，名称: {instance.name}，用户: {target_user.username}，租户: {user.tenant.name}")
                except User.DoesNotExist:
                    error_msg = "Specified user does not exist"
                    logger.error(f"【创建打卡类型失败】{error_msg}，指定的用户ID: {user_id}")
                    raise serializers.ValidationError(_(error_msg))
            else:
                # 未指定用户，使用current用户
                logger.info(f"【创建打卡类型】未指定用户，即将创建打卡类型关联current用户: {user.username}，租户: {user.tenant.name}")
                instance = serializer.save(
                    user=user, 
                    tenant=user.tenant
                )
                logger.info(f"【创建打卡类型成功】ID: {instance.id}，名称: {instance.name}，用户: {user.username}，租户: {user.tenant.name}")
        elif hasattr(user, 'sub_accounts') and user.sub_accounts.exists():
            logger.debug(f"【创建打卡类型】用户是主账号，有子账号权限，可以为子账号创建")
            # 主member：可以为子账号创建
            if user_id:
                try:
                    target_user = User.objects.get(id=user_id)
                    logger.debug(f"【创建打卡类型】找到目标用户: {target_user.username} (ID: {target_user.id})")
                    
                    # 检查目标用户是否为自己的子账号
                    if target_user.parent_id != user.id:
                        error_msg = "只能为自己的子账号创建类型"
                        logger.error(f"【创建打卡类型失败】{error_msg}，目标用户父账号ID: {target_user.parent_id}，current用户ID: {user.id}")
                        raise serializers.ValidationError(_(error_msg))
                    
                    # 检查目标用户是否属于同一租户
                    if target_user.tenant != user.tenant:
                        error_msg = "Sub-accounts must belong to the same tenant"
                        logger.error(f"【创建打卡类型失败】{error_msg}，子账号租户: {target_user.tenant.name if target_user.tenant else 'None'}")
                        raise serializers.ValidationError(_(error_msg))
                    
                    logger.info(f"【创建打卡类型】即将创建打卡类型，关联子账号: {target_user.username}，租户: {user.tenant.name}")
                    # 设置用户和租户
                    instance = serializer.save(
                        user=target_user, 
                        tenant=user.tenant  # 强制使用current用户的租户
                    )
                    logger.info(f"【创建打卡类型成功】ID: {instance.id}，名称: {instance.name}，用户(子账号): {target_user.username}，租户: {user.tenant.name}")
                except User.DoesNotExist:
                    error_msg = "Specified user does not exist"
                    logger.error(f"【创建打卡类型失败】{error_msg}，指定的用户ID: {user_id}")
                    raise serializers.ValidationError(_(error_msg))
            else:
                # 未指定用户，使用current用户
                logger.info(f"【创建打卡类型】未指定用户，即将创建打卡类型关联current用户: {user.username}，租户: {user.tenant.name}")
                instance = serializer.save(
                    user=user, 
                    tenant=user.tenant
                )
                logger.info(f"【创建打卡类型成功】ID: {instance.id}，名称: {instance.name}，用户: {user.username}，租户: {user.tenant.name}")
        else:
            logger.debug(f"【创建打卡类型】普通用户，只能为自己创建")
            # 普通member：只能为自己创建
            instance = serializer.save(
                user=user, 
                tenant=user.tenant
            )
            logger.info(f"【创建打卡类型成功】ID: {instance.id}，名称: {instance.name}，用户: {user.username}，租户: {user.tenant.name}")
    
    def perform_update(self, serializer):
        """
        更新类型时进行权限检查
        根据角色处理user_id参数
        强制使用用户所属的租户ID
        """
        user = self.request.user
        data = self.request.data
        instance = self.get_object()
        
        logger.info(f"【开始更新打卡类型】ID: {instance.id}，名称: {instance.name}，用户ID: {user.id}，用户名: {user.username}，请求数据: {data}")
        
        # 确保用户关联了租户
        if not hasattr(user, 'tenant') or not user.tenant:
            error_msg = "用户未关联租户，无法更新类型"
            logger.error(f"【更新打卡类型失败】{error_msg}，用户ID: {user.id}")
            raise serializers.ValidationError(_(error_msg))
        
        logger.debug(f"【更新打卡类型】用户关联的租户: {user.tenant.name} (ID: {user.tenant.id})")
        
        # 获取user_id
        user_id = data.get('user_id') or data.get('user')
        logger.debug(f"【更新打卡类型】指定的用户ID: {user_id}")
        
        if is_admin(user):
            logger.debug(f"【更新打卡类型】用户是租户管理员，可以修改租户内的任意用户的类型")
            # 租户管理员：可以修改用户，但必须属于同一租户
            if user_id:
                try:
                    target_user = User.objects.get(id=user_id)
                    logger.debug(f"【更新打卡类型】找到目标用户: {target_user.username} (ID: {target_user.id})")
                    
                    # 检查目标用户是否属于同一租户
                    if target_user.tenant != user.tenant:
                        error_msg = "无法为其他租户的用户修改类型"
                        logger.error(f"【更新打卡类型失败】{error_msg}，目标用户租户: {target_user.tenant.name if target_user.tenant else 'None'}")
                        raise serializers.ValidationError(_(error_msg))
                    
                    logger.info(f"【更新打卡类型】即将更新打卡类型，关联用户: {target_user.username}，租户: {user.tenant.name}")
                    # 设置用户和租户(始终使用current租户)
                    updated_instance = serializer.save(
                        user=target_user, 
                        tenant=user.tenant  # 强制使用current租户管理员的租户
                    )
                    logger.info(f"【更新打卡类型成功】ID: {updated_instance.id}，名称: {updated_instance.name}，用户: {target_user.username}，租户: {user.tenant.name}")
                except User.DoesNotExist:
                    error_msg = "Specified user does not exist"
                    logger.error(f"【更新打卡类型失败】{error_msg}，指定的用户ID: {user_id}")
                    raise serializers.ValidationError(_(error_msg))
            else:
                # 未指定用户，保持原样，但确保租户正确
                logger.info(f"【更新打卡类型】未指定用户，保持原有用户: {instance.user.username}，确保租户正确: {user.tenant.name}")
                updated_instance = serializer.save(tenant=user.tenant)
                logger.info(f"【更新打卡类型成功】ID: {updated_instance.id}，名称: {updated_instance.name}，租户: {user.tenant.name}")
        elif hasattr(user, 'sub_accounts') and user.sub_accounts.exists():
            logger.debug(f"【更新打卡类型】用户是主账号，有子账号权限，可以修改子账号的资源")
            # 主member：可以修改子账号的资源
            if user_id:
                try:
                    target_user = User.objects.get(id=user_id)
                    logger.debug(f"【更新打卡类型】找到目标用户: {target_user.username} (ID: {target_user.id})")
                    
                    # 检查目标用户是否为自己的子账号
                    if target_user.parent_id != user.id:
                        error_msg = "只能为自己的子账号修改类型"
                        logger.error(f"【更新打卡类型失败】{error_msg}，目标用户父账号ID: {target_user.parent_id}，current用户ID: {user.id}")
                        raise serializers.ValidationError(_(error_msg))
                    
                    # 检查目标用户是否属于同一租户
                    if target_user.tenant != user.tenant:
                        error_msg = "Sub-accounts must belong to the same tenant"
                        logger.error(f"【更新打卡类型失败】{error_msg}，子账号租户: {target_user.tenant.name if target_user.tenant else 'None'}")
                        raise serializers.ValidationError(_(error_msg))
                    
                    logger.info(f"【更新打卡类型】即将更新打卡类型，关联子账号: {target_user.username}，租户: {user.tenant.name}")
                    # 设置用户和租户
                    updated_instance = serializer.save(
                        user=target_user, 
                        tenant=user.tenant  # 强制使用current用户的租户
                    )
                    logger.info(f"【更新打卡类型成功】ID: {updated_instance.id}，名称: {updated_instance.name}，用户(子账号): {target_user.username}，租户: {user.tenant.name}")
                except User.DoesNotExist:
                    error_msg = "Specified user does not exist"
                    logger.error(f"【更新打卡类型失败】{error_msg}，指定的用户ID: {user_id}")
                    raise serializers.ValidationError(_(error_msg))
            else:
                # 未指定用户，保持原样，但确保租户正确
                logger.info(f"【更新打卡类型】未指定用户，保持原有用户: {instance.user.username}，确保租户正确: {user.tenant.name}")
                updated_instance = serializer.save(tenant=user.tenant)
                logger.info(f"【更新打卡类型成功】ID: {updated_instance.id}，名称: {updated_instance.name}，租户: {user.tenant.name}")
        else:
            logger.debug(f"【更新打卡类型】普通用户，只能修改自己的类型")
            # 普通member：只能修改自己的
            if instance.user != user:
                error_msg = "无法修改其他用户的类型"
                logger.error(f"【更新打卡类型失败】{error_msg}，current用户ID: {user.id}，类型所属用户ID: {instance.user.id}")
                raise serializers.ValidationError(_(error_msg))
            updated_instance = serializer.save(tenant=user.tenant)  # 确保租户正确
            logger.info(f"【更新打卡类型成功】ID: {updated_instance.id}，名称: {updated_instance.name}，用户: {user.username}，租户: {user.tenant.name}")


@extend_schema_view(
    list=extend_schema(
        summary="获取打卡任务列表",
        description="获取打卡任务列表，支持分页、过滤和搜索",
        tags=["打卡系统-任务管理"],
        parameters=[
            OpenApiParameter(name="category", description="打卡类型ID", required=False, type=int),
            OpenApiParameter(name="status", description="任务状态", required=False, type=str),
            OpenApiParameter(name="search", description="搜索关键词", required=False, type=str),
        ],
        examples=[
            OpenApiExample(
                'List Tasks Example',
                summary='获取打卡任务列表示例',
                description='获取打卡任务列表，支持分页、过滤和搜索',
                value={
                    'page': 1,
                    'page_size': 10,
                    'category': 1,
                    'status': 'active',
                    'search': '早起'
                }
            )
        ]
    ),
    retrieve=extend_schema(
        summary="获取打卡任务详情",
        description="获取单个打卡任务的详细信息",
        tags=["打卡系统-任务管理"],
        parameters=[
            OpenApiParameter(name="id", description="打卡任务ID", required=True, type=OpenApiTypes.INT),
        ],
        examples=[
            OpenApiExample(
                'Retrieve Task Example',
                summary='获取打卡任务详情示例',
                description='获取单个打卡任务的详细信息',
                value={
                    'id': 1
                }
            )
        ]
    ),
    create=extend_schema(
        summary="创建打卡任务",
        description="创建新的打卡任务",
        tags=["打卡系统-任务管理"],
        examples=[
            OpenApiExample(
                'Create Task Example',
                summary='创建打卡任务示例',
                description='创建一个新的打卡任务',
                value={
                    'name': '每日早起',
                    'description': '每天早上6点前起床，培养良好作息习惯',
                    'category': 1,
                    'start_date': '2025-05-01',
                    'end_date': '2025-05-31',
                    'status': 'active',
                    'reminder': True,
                    'reminder_time': '05:30:00'
                }
            ),
            OpenApiExample(
                'Create Long-term Task Example',
                summary='创建长期打卡任务示例',
                description='创建一个没有结束日期的长期打卡任务',
                value={
                    'name': '健身打卡',
                    'description': '每天健身30分钟，保持健康体魄',
                    'category': 2,
                    'start_date': '2025-05-01',
                    'status': 'active',
                    'reminder': False
                }
            )
        ]
    ),
    update=extend_schema(
        summary="更新打卡任务",
        description="更新现有打卡任务的所有字段",
        tags=["打卡系统-任务管理"],
        parameters=[
            OpenApiParameter(name="id", description="打卡任务ID", required=True, type=OpenApiTypes.INT),
        ],
        examples=[
            OpenApiExample(
                'Update Task Example',
                summary='更新打卡任务示例',
                description='更新现有打卡任务的所有字段',
                value={
                    'name': '每日早起',
                    'description': '每天早上6点前起床，培养良好作息习惯，提高工作效率',
                    'category': 1,
                    'start_date': '2025-05-01',
                    'end_date': '2025-06-30',
                    'status': 'active',
                    'reminder': True,
                    'reminder_time': '05:45:00'
                }
            )
        ]
    ),
    partial_update=extend_schema(
        summary="部分更新打卡任务",
        description="更新现有打卡任务的部分字段",
        tags=["打卡系统-任务管理"],
        parameters=[
            OpenApiParameter(name="id", description="打卡任务ID", required=True, type=OpenApiTypes.INT),
        ],
        examples=[
            OpenApiExample(
                'Change Task Status Example',
                summary='更改任务状态示例',
                description='暂停一个正在进行的打卡任务',
                value={
                    'status': 'paused'
                }
            ),
            OpenApiExample(
                'Update Reminder Example',
                summary='更新提醒设置示例',
                description='修改任务提醒时间',
                value={
                    'reminder': True,
                    'reminder_time': '06:00:00'
                }
            )
        ]
    ),
    destroy=extend_schema(
        summary="删除打卡任务",
        description="删除现有打卡任务",
        tags=["打卡系统-任务管理"],
        parameters=[
            OpenApiParameter(name="id", description="打卡任务ID", required=True, type=OpenApiTypes.INT),
        ],
        examples=[
            OpenApiExample(
                'Delete Task Example',
                summary='删除打卡任务示例',
                description='删除现有打卡任务',
                value={
                    'id': 1
                }
            )
        ]
    ),
)
class TaskViewSet(TenantModelViewSet):
    """
    打卡任务视图集，提供增删改查API
    
    继承TenantModelViewSet自动处理租户过滤、设置和验证
    
    可以创建和管理打卡任务，支持任务提醒。
    - 普通用户: 只能查看自己的任务
    - 租户管理员: 可以查看该租户下的所有任务
    - 超级管理员: 可以查看所有任务
    """
    queryset = Task.objects.all().select_related('user', 'tenant', 'category')
    serializer_class = TaskSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'status']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'name', 'start_date', 'end_date']
    ordering = ['-created_at']
    authentication_classes = [APIJWTAuthentication]
    permission_classes = [TaskPermission]
    
    def get_queryset(self):
        """
        获取查询集，先调用父类获取租户过滤的queryset
        然后根据用户角色应用额外过滤逻辑
        """
        # 获取租户过滤后的基础queryset
        queryset = super().get_queryset()
            
        user = self.request.user
        
        # 超级管理员已经在父类中处理
        if user.is_superuser:
            return queryset
        
        # 租户管理员：租户过滤已在父类处理
        if user.is_staff and user.tenant:
            return queryset
        
        # 普通用户：只看自己的
        return queryset.filter(user=user)
    
    def perform_create(self, serializer):
        """
        创建任务时自动关联current用户和租户
        根据角色处理user_id参数
        """
        user = self.request.user
        data = self.request.data
        
        # 确保用户关联了租户
        if not hasattr(user, 'tenant') or not user.tenant:
            raise serializers.ValidationError(_("User has no associated tenant and cannot create task"))
        
        # 获取user_id
        user_id = data.get('user_id') or data.get('user')
        
        # 处理打卡频率数据
        frequency_type = serializer.validated_data.get('frequency_type', 'daily')
        frequency_days = serializer.validated_data.get('frequency_days', [])
        
        # 如果是每天打卡，frequency_days为空列表
        if frequency_type == 'daily':
            frequency_days = []
        
        if is_admin(user):
            # 租户管理员：可以指定用户，但必须属于同一租户
            if user_id:
                try:
                    target_user = User.objects.get(id=user_id)
                    
                    # 检查目标用户是否属于同一租户
                    if target_user.tenant != user.tenant:
                        raise serializers.ValidationError(_("Cannot create task for users of other tenants"))
                    
                    # 设置用户和租户(始终使用current租户)
                    serializer.save(
                        user=target_user, 
                        tenant=user.tenant,  # 强制使用current租户管理员的租户
                        frequency_type=frequency_type,
                        frequency_days=frequency_days
                    )
                except User.DoesNotExist:
                    raise serializers.ValidationError(_("Specified user does not exist"))
            else:
                # 未指定用户，使用current用户
                serializer.save(
                    user=user, 
                    tenant=user.tenant,
                    frequency_type=frequency_type,
                    frequency_days=frequency_days
                )
        elif hasattr(user, 'sub_accounts') and user.sub_accounts.exists():
            # 主member：可以为子账号创建
            if user_id:
                try:
                    target_user = User.objects.get(id=user_id)
                    
                    # 检查目标用户是否为自己的子账号
                    if target_user.parent_id != user.id:
                        raise serializers.ValidationError(_("Can only create tasks for own sub-accounts"))
                    
                    # 检查目标用户是否属于同一租户
                    if target_user.tenant != user.tenant:
                        raise serializers.ValidationError(_("Sub-accounts must belong to the same tenant"))
                    
                    # 设置用户和租户
                    serializer.save(
                        user=target_user, 
                        tenant=user.tenant,  # 强制使用current用户的租户
                        frequency_type=frequency_type,
                        frequency_days=frequency_days
                    )
                except User.DoesNotExist:
                    raise serializers.ValidationError(_("Specified user does not exist"))
            else:
                # 未指定用户，使用current用户
                serializer.save(
                    user=user, 
                    tenant=user.tenant,
                    frequency_type=frequency_type,
                    frequency_days=frequency_days
                )
        else:
            # 普通member：只能为自己创建
            serializer.save(
                user=user, 
                tenant=user.tenant,
                frequency_type=frequency_type,
                frequency_days=frequency_days
            )
        
        logger.info(f"用户 {user.username} 创建了打卡任务: {serializer.validated_data.get('name')}")
    
    def perform_update(self, serializer):
        """
        更新任务时进行权限检查
        根据角色处理user_id参数
        强制使用用户所属的租户ID
        """
        user = self.request.user
        data = self.request.data
        instance = self.get_object()
        
        # 确保用户关联了租户
        if not hasattr(user, 'tenant') or not user.tenant:
            raise serializers.ValidationError(_("User has no associated tenant and cannot update task"))
        
        # 获取user_id
        user_id = data.get('user_id') or data.get('user')
        
        # 处理打卡频率数据
        frequency_type = serializer.validated_data.get('frequency_type', instance.frequency_type)
        frequency_days = serializer.validated_data.get('frequency_days', instance.frequency_days)
        
        # 如果是每天打卡，frequency_days为空列表
        if frequency_type == 'daily':
            frequency_days = []
        
        if is_admin(user):
            # 租户管理员：可以修改用户，但必须属于同一租户
            if user_id:
                try:
                    target_user = User.objects.get(id=user_id)
                    
                    # 检查目标用户是否属于同一租户
                    if target_user.tenant != user.tenant:
                        raise serializers.ValidationError(_("Cannot modify task for users of other tenants"))
                    
                    # 设置用户和租户(始终使用current租户)
                    serializer.save(
                        user=target_user, 
                        tenant=user.tenant,  # 强制使用current租户管理员的租户
                        frequency_type=frequency_type,
                        frequency_days=frequency_days
                    )
                except User.DoesNotExist:
                    raise serializers.ValidationError(_("Specified user does not exist"))
            else:
                # 未指定用户，保持原样，但确保租户正确
                serializer.save(
                    tenant=user.tenant,
                    frequency_type=frequency_type,
                    frequency_days=frequency_days
                )
        elif hasattr(user, 'sub_accounts') and user.sub_accounts.exists():
            # 主member：可以修改子账号的资源
            if user_id:
                try:
                    target_user = User.objects.get(id=user_id)
                    
                    # 检查目标用户是否为自己的子账号
                    if target_user.parent_id != user.id:
                        raise serializers.ValidationError(_("Can only modify tasks for own sub-accounts"))
                    
                    # 检查目标用户是否属于同一租户
                    if target_user.tenant != user.tenant:
                        raise serializers.ValidationError(_("Sub-accounts must belong to the same tenant"))
                    
                    # 设置用户和租户
                    serializer.save(
                        user=target_user, 
                        tenant=user.tenant,  # 强制使用current用户的租户
                        frequency_type=frequency_type,
                        frequency_days=frequency_days
                    )
                except User.DoesNotExist:
                    raise serializers.ValidationError(_("Specified user does not exist"))
            else:
                # 未指定用户，保持原样，但确保租户正确
                serializer.save(
                    tenant=user.tenant,
                    frequency_type=frequency_type,
                    frequency_days=frequency_days
                )
        else:
            # 普通member：只能修改自己的
            if instance.user != user:
                raise serializers.ValidationError(_("Cannot modify other users' tasks"))
            serializer.save(
                tenant=user.tenant,  # 确保租户正确
                frequency_type=frequency_type,
                frequency_days=frequency_days
            )
        
        logger.info(f"用户 {user.username} 更新了打卡任务: {instance.name}")


@extend_schema_view(
    list=extend_schema(
        summary="获取打卡记录列表",
        description="获取打卡记录列表，支持分页、过滤和搜索",
        tags=["打卡系统-记录管理"],
    ),
    retrieve=extend_schema(
        summary="获取打卡记录详情",
        description="获取单个打卡记录的详细信息",
        tags=["打卡系统-记录管理"],
        parameters=[
            OpenApiParameter(name="id", description="打卡记录ID", required=True, type=OpenApiTypes.INT),
        ],
    ),
    create=extend_schema(
        summary="创建打卡记录",
        description="创建新的打卡记录",
        tags=["打卡系统-记录管理"],
    ),
    update=extend_schema(
        summary="更新打卡记录",
        description="更新现有的打卡记录",
        tags=["打卡系统-记录管理"],
        parameters=[
            OpenApiParameter(name="id", description="打卡记录ID", required=True, type=OpenApiTypes.INT),
        ],
    ),
    partial_update=extend_schema(
        summary="部分更新打卡记录",
        description="部分更新现有的打卡记录",
        tags=["打卡系统-记录管理"],
        parameters=[
            OpenApiParameter(name="id", description="打卡记录ID", required=True, type=OpenApiTypes.INT),
        ],
    ),
    destroy=extend_schema(
        summary="删除打卡记录",
        description="删除现有的打卡记录",
        tags=["打卡系统-记录管理"],
        parameters=[
            OpenApiParameter(name="id", description="打卡记录ID", required=True, type=OpenApiTypes.INT),
        ],
    )
)
class CheckRecordViewSet(TenantModelViewSet):
    """
    打卡记录视图集，提供增删改查API
    
    继承TenantModelViewSet自动处理租户过滤、设置和验证
    
    记录用户的打卡情况，支持添加备注。
    - 普通用户: 只能查看自己的打卡记录
    - 租户管理员: 可以查看该租户下的所有打卡记录
    - 超级管理员: 可以查看所有打卡记录
    """
    queryset = CheckRecord.objects.all().select_related('user', 'task', 'task__category', 'task__tenant')
    serializer_class = CheckRecordSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['task', 'check_date']
    search_fields = ['remarks']
    ordering_fields = ['check_date', 'check_time', 'created_at']
    ordering = ['-check_date', '-check_time']
    authentication_classes = [APIJWTAuthentication]
    permission_classes = [CheckRecordPermission]
    
    def get_queryset(self):
        """
        获取查询集，先调用父类获取租户过滤的queryset
        然后根据用户角色应用额外过滤逻辑
        
        注意：CheckRecord没有tenant字段，通过task关联租户
        """
        # CheckRecord没有tenant字段，直接使用基础queryset
        queryset = CheckRecord.objects.all().select_related('user', 'task', 'task__category', 'task__tenant')
            
        user = self.request.user
        
        # 超级管理员
        if user.is_superuser:
            return queryset
        
        # 租户管理员：通过task和user过滤
        if user.is_staff and user.tenant:
            return queryset.filter(
                Q(user__tenant=user.tenant) | Q(task__tenant=user.tenant)
            )
        
        # 普通用户：只看自己的
        return queryset.filter(user=user)
    
    def perform_create(self, serializer):
        """
        创建打卡记录时自动关联current用户
        根据角色处理user_id参数
        检查任务和用户所属租户是否一致
        """
        user = self.request.user
        data = self.request.data
        
        # 确保用户关联了租户
        if not hasattr(user, 'tenant') or not user.tenant:
            raise serializers.ValidationError(_("User has no associated tenant and cannot create check-in record"))
        
        # 获取user_id和task_id
        user_id = data.get('user_id') or data.get('user')
        task_id = data.get('task_id') or data.get('task')
        
        # 检查任务所属租户与用户租户是否一致
        if task_id:
            try:
                task = Task.objects.get(id=task_id)
                if task.tenant != user.tenant:
                    raise serializers.ValidationError(_("Cannot create check-in record for tasks of other tenants"))
            except Task.DoesNotExist:
                raise serializers.ValidationError(_("Specified task does not exist"))
        
        if is_admin(user):
            # 租户管理员：可以指定用户，但必须属于同一租户
            if user_id:
                try:
                    target_user = User.objects.get(id=user_id)
                    
                    # 检查目标用户是否属于同一租户
                    if target_user.tenant != user.tenant:
                        raise serializers.ValidationError(_("Cannot create check-in record for users of other tenants"))
                    
                    # 设置用户
                    serializer.save(user=target_user)
                except User.DoesNotExist:
                    raise serializers.ValidationError(_("Specified user does not exist"))
            else:
                # 未指定用户，使用current用户
                serializer.save(user=user)
        elif hasattr(user, 'sub_accounts') and user.sub_accounts.exists():
            # 主member：可以为子账号创建
            if user_id:
                try:
                    target_user = User.objects.get(id=user_id)
                    
                    # 检查目标用户是否为自己的子账号
                    if target_user.parent_id != user.id:
                        raise serializers.ValidationError(_("Can only create check-in records for own sub-accounts"))
                    
                    # 检查目标用户是否属于同一租户
                    if target_user.tenant != user.tenant:
                        raise serializers.ValidationError(_("Sub-accounts must belong to the same tenant"))
                    
                    # 设置用户
                    serializer.save(user=target_user)
                except User.DoesNotExist:
                    raise serializers.ValidationError(_("Specified user does not exist"))
            else:
                # 未指定用户，使用current用户
                serializer.save(user=user)
        else:
            # 普通member：只能为自己创建
            serializer.save(user=user)
    
    def perform_update(self, serializer):
        """
        更新打卡记录时进行权限检查
        根据角色处理user_id参数
        检查任务和用户所属租户是否一致
        """
        user = self.request.user
        data = self.request.data
        instance = self.get_object()
        
        # 确保用户关联了租户
        if not hasattr(user, 'tenant') or not user.tenant:
            raise serializers.ValidationError(_("User has no associated tenant and cannot update check-in record"))
        
        # 获取user_id和task_id
        user_id = data.get('user_id') or data.get('user')
        task_id = data.get('task_id') or data.get('task')
        
        # 检查任务所属租户与用户租户是否一致
        if task_id:
            try:
                task = Task.objects.get(id=task_id)
                if task.tenant != user.tenant:
                    raise serializers.ValidationError(_("Cannot update check-in record for tasks of other tenants"))
            except Task.DoesNotExist:
                raise serializers.ValidationError(_("Specified task does not exist"))
        
        if is_admin(user):
            # 租户管理员：可以修改用户，但必须属于同一租户
            if user_id:
                try:
                    target_user = User.objects.get(id=user_id)
                    
                    # 检查目标用户是否属于同一租户
                    if target_user.tenant != user.tenant:
                        raise serializers.ValidationError(_("无法为其他租户的用户修改打卡记录"))
                    
                    # 设置用户
                    serializer.save(user=target_user)
                except User.DoesNotExist:
                    raise serializers.ValidationError(_("Specified user does not exist"))
            else:
                # 未指定用户，保持原样
                serializer.save()
        elif hasattr(user, 'sub_accounts') and user.sub_accounts.exists():
            # 主member：可以修改子账号的资源
            if user_id:
                try:
                    target_user = User.objects.get(id=user_id)
                    
                    # 检查目标用户是否为自己的子账号
                    if target_user.parent_id != user.id:
                        raise serializers.ValidationError(_("Can only modify check-in records for own sub-accounts"))
                    
                    # 检查目标用户是否属于同一租户
                    if target_user.tenant != user.tenant:
                        raise serializers.ValidationError(_("Sub-accounts must belong to the same tenant"))
                    
                    # 设置用户
                    serializer.save(user=target_user)
                except User.DoesNotExist:
                    raise serializers.ValidationError(_("Specified user does not exist"))
            else:
                # 未指定用户，保持原样
                serializer.save()
        else:
            # 普通member：只能修改自己的
            if instance.user != user:
                raise serializers.ValidationError(_("Cannot modify other users' check-in records"))
            serializer.save()


@extend_schema_view(
    list=extend_schema(
        summary="获取任务模板列表",
        description="获取任务模板列表，支持分页、过滤和搜索",
        tags=["打卡系统-模板管理"],
    ),
    retrieve=extend_schema(
        summary="获取任务模板详情",
        description="获取单个任务模板的详细信息",
        tags=["打卡系统-模板管理"],
        parameters=[

        ],
    ),
    create=extend_schema(
        summary="创建任务模板",
        description="创建新的任务模板，需要提供模板名称、描述和所属类型等信息",
        tags=["打卡系统-模板管理"],
        request=TaskTemplateSerializer,
        responses={
            201: TaskTemplateSerializer,
            400: OpenApiResponse(description="请求参数错误"),
            403: OpenApiResponse(description="权限不足"),
        },
        examples=[
            OpenApiExample(
                "创建模板示例",
                value={
                    "name": "每日阅读",
                    "description": "每天阅读30分钟",
                    "category": 1,
                    "is_system": False,
                    "reminder": True,
                    "reminder_time": "20:00:00",
                    "translations": {"en": {"name": "Daily Reading"}}
                },
                request_only=True,
            )
        ],
    ),
    update=extend_schema(
        summary="更新任务模板",
        description="更新现有任务模板",
        tags=["打卡系统-模板管理"],
        parameters=[

        ],
    ),
    partial_update=extend_schema(
        summary="部分更新任务模板",
        description="部分更新现有任务模板",
        tags=["打卡系统-模板管理"],
        parameters=[

        ],
    ),
    destroy=extend_schema(
        summary="删除任务模板",
        description="删除现有任务模板",
        tags=["打卡系统-模板管理"],
        parameters=[

        ],
    )
)
class TaskTemplateViewSet(TenantModelViewSet):
    """
    任务模板视图集，提供增删改查API
    
    继承TenantModelViewSet自动处理租户过滤、设置和验证
    
    可以管理系统预设和用户自定义的任务模板，支持多语言和基于模板创建任务。
    - 普通用户: 只能查看系统预设模板和自己创建的模板
    - 租户管理员: 可以查看系统预设模板和该租户下的所有模板
    - 超级管理员: 可以查看所有模板
    """
    queryset = TaskTemplate.objects.all().select_related('user', 'tenant', 'category')
    serializer_class = TaskTemplateSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'is_system']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'name']
    ordering = ['-created_at']
    authentication_classes = [APIJWTAuthentication]
    permission_classes = [TaskTemplatePermission]
    
    def get_queryset(self):
        """
        获取查询集，先调用父类获取租户过滤的queryset
        然后根据用户角色应用额外过滤逻辑
        """
        # 获取租户过滤后的基础queryset
        queryset = super().get_queryset()
            
        user = self.request.user
        
        # 超级管理员已经在父类中处理
        if user.is_superuser:
            return queryset
        
        # 租户管理员：系统预设 + 租户数据
        if user.is_staff and user.tenant:
            return queryset.filter(Q(is_system=True) | Q(tenant=user.tenant))
        
        # 普通用户：系统预设 + 自己创建
        return queryset.filter(Q(is_system=True) | Q(user=user))
    
    def perform_create(self, serializer):
        """
        创建模板时自动关联current用户和租户
        根据角色处理user_id参数
        """
        user = self.request.user
        data = self.request.data
        
        logger.info(f"【开始创建任务模板】用户ID: {user.id}，用户名: {user.username}，请求数据: {data}")
        
        # 确保用户关联了租户
        if not hasattr(user, 'tenant') or not user.tenant:
            error_msg = "用户未关联租户，无法创建模板"
            logger.error(f"【创建任务模板失败】{error_msg}，用户ID: {user.id}")
            raise serializers.ValidationError(_(error_msg))
        
        logger.debug(f"【创建任务模板】用户关联的租户: {user.tenant.name} (ID: {user.tenant.id})")
        
        # 检查是否为系统预设类型
        is_system = data.get('is_system', False)
        if is_system:
            logger.info(f"【创建任务模板】创建系统预设类型，不关联用户")
            # 系统预设类型不关联用户，只关联租户
            instance = serializer.save(
                user=None,  # 不关联用户
                tenant=user.tenant
            )
            logger.info(f"【创建任务模板成功】ID: {instance.id}，名称: {instance.name}，系统预设类型，租户: {user.tenant.name}")
            return
        
        # 获取user_id
        user_id = data.get('user_id') or data.get('user')
        logger.debug(f"【创建任务模板】指定的用户ID: {user_id}")
        
        if is_admin(user):
            logger.debug(f"【创建任务模板】用户是租户管理员，可以为租户内的任意用户创建")
            # 租户管理员：可以指定用户，但必须属于同一租户
            if user_id:
                try:
                    target_user = User.objects.get(id=user_id)
                    logger.debug(f"【创建任务模板】找到目标用户: {target_user.username} (ID: {target_user.id})")
                    
                    # 检查目标用户是否属于同一租户
                    if target_user.tenant != user.tenant:
                        error_msg = "无法为其他租户的用户创建模板"
                        logger.error(f"【创建任务模板失败】{error_msg}，目标用户租户: {target_user.tenant.name if target_user.tenant else 'None'}")
                        raise serializers.ValidationError(_(error_msg))
                    
                    logger.info(f"【创建任务模板】即将创建任务模板，关联用户: {target_user.username}，租户: {user.tenant.name}")
                    # 设置用户和租户(始终使用current租户)
                    instance = serializer.save(
                        user=target_user, 
                        tenant=user.tenant  # 强制使用current租户管理员的租户
                    )
                    logger.info(f"【创建任务模板成功】ID: {instance.id}，名称: {instance.name}，用户: {target_user.username}，租户: {user.tenant.name}")
                except User.DoesNotExist:
                    error_msg = "Specified user does not exist"
                    logger.error(f"【创建任务模板失败】{error_msg}，指定的用户ID: {user_id}")
                    raise serializers.ValidationError(_(error_msg))
            else:
                # 未指定用户，使用current用户
                logger.info(f"【创建任务模板】未指定用户，即将创建任务模板关联current用户: {user.username}，租户: {user.tenant.name}")
                instance = serializer.save(
                    user=user, 
                    tenant=user.tenant
                )
                logger.info(f"【创建任务模板成功】ID: {instance.id}，名称: {instance.name}，用户: {user.username}，租户: {user.tenant.name}")
        elif hasattr(user, 'sub_accounts') and user.sub_accounts.exists():
            logger.debug(f"【创建任务模板】用户是主账号，有子账号权限，可以为子账号创建")
            # 主member：可以为子账号创建
            if user_id:
                try:
                    target_user = User.objects.get(id=user_id)
                    logger.debug(f"【创建任务模板】找到目标用户: {target_user.username} (ID: {target_user.id})")
                    
                    # 检查目标用户是否为自己的子账号
                    if target_user.parent_id != user.id:
                        error_msg = "只能为自己的子账号创建模板"
                        logger.error(f"【创建任务模板失败】{error_msg}，目标用户父账号ID: {target_user.parent_id}，current用户ID: {user.id}")
                        raise serializers.ValidationError(_(error_msg))
                    
                    # 检查目标用户是否属于同一租户
                    if target_user.tenant != user.tenant:
                        error_msg = "Sub-accounts must belong to the same tenant"
                        logger.error(f"【创建任务模板失败】{error_msg}，子账号租户: {target_user.tenant.name if target_user.tenant else 'None'}")
                        raise serializers.ValidationError(_(error_msg))
                    
                    logger.info(f"【创建任务模板】即将创建任务模板，关联子账号: {target_user.username}，租户: {user.tenant.name}")
                    # 设置用户和租户
                    instance = serializer.save(
                        user=target_user, 
                        tenant=user.tenant  # 强制使用current用户的租户
                    )
                    logger.info(f"【创建任务模板成功】ID: {instance.id}，名称: {instance.name}，用户(子账号): {target_user.username}，租户: {user.tenant.name}")
                except User.DoesNotExist:
                    error_msg = "Specified user does not exist"
                    logger.error(f"【创建任务模板失败】{error_msg}，指定的用户ID: {user_id}")
                    raise serializers.ValidationError(_(error_msg))
            else:
                # 未指定用户，使用current用户
                logger.info(f"【创建任务模板】未指定用户，即将创建任务模板关联current用户: {user.username}，租户: {user.tenant.name}")
                instance = serializer.save(
                    user=user, 
                    tenant=user.tenant
                )
                logger.info(f"【创建任务模板成功】ID: {instance.id}，名称: {instance.name}，用户: {user.username}，租户: {user.tenant.name}")
        else:
            logger.debug(f"【创建任务模板】普通用户，只能为自己创建")
            # 普通member：只能为自己创建
            instance = serializer.save(
                user=user, 
                tenant=user.tenant
            )
            logger.info(f"【创建任务模板成功】ID: {instance.id}，名称: {instance.name}，用户: {user.username}，租户: {user.tenant.name}")
    
    def perform_update(self, serializer):
        """
        更新模板时进行权限检查
        根据角色处理user_id参数
        强制使用用户所属的租户ID
        """
        user = self.request.user
        data = self.request.data
        instance = self.get_object()
        
        logger.info(f"【开始更新任务模板】ID: {instance.id}，名称: {instance.name}，用户ID: {user.id}，用户名: {user.username}，请求数据: {data}")
        
        # 确保用户关联了租户
        if not hasattr(user, 'tenant') or not user.tenant:
            error_msg = "用户未关联租户，无法更新模板"
            logger.error(f"【更新任务模板失败】{error_msg}，用户ID: {user.id}")
            raise serializers.ValidationError(_(error_msg))
        
        logger.debug(f"【更新任务模板】用户关联的租户: {user.tenant.name} (ID: {user.tenant.id})")
        
        # 获取user_id
        user_id = data.get('user_id') or data.get('user')
        logger.debug(f"【更新任务模板】指定的用户ID: {user_id}")
        
        if is_admin(user):
            logger.debug(f"【更新任务模板】用户是租户管理员，可以修改租户内的任意用户的模板")
            # 租户管理员：可以修改用户，但必须属于同一租户
            if user_id:
                try:
                    target_user = User.objects.get(id=user_id)
                    logger.debug(f"【更新任务模板】找到目标用户: {target_user.username} (ID: {target_user.id})")
                    
                    # 检查目标用户是否属于同一租户
                    if target_user.tenant != user.tenant:
                        error_msg = "无法为其他租户的用户修改模板"
                        logger.error(f"【更新任务模板失败】{error_msg}，目标用户租户: {target_user.tenant.name if target_user.tenant else 'None'}")
                        raise serializers.ValidationError(_(error_msg))
                    
                    logger.info(f"【更新任务模板】即将更新任务模板，关联用户: {target_user.username}，租户: {user.tenant.name}")
                    # 设置用户和租户(始终使用current租户)
                    updated_instance = serializer.save(
                        user=target_user, 
                        tenant=user.tenant  # 强制使用current租户管理员的租户
                    )
                    logger.info(f"【更新任务模板成功】ID: {updated_instance.id}，名称: {updated_instance.name}，用户: {target_user.username}，租户: {user.tenant.name}")
                except User.DoesNotExist:
                    error_msg = "Specified user does not exist"
                    logger.error(f"【更新任务模板失败】{error_msg}，指定的用户ID: {user_id}")
                    raise serializers.ValidationError(_(error_msg))
            else:
                # 未指定用户，保持原样，但确保租户正确
                logger.info(f"【更新任务模板】未指定用户，保持原有用户: {instance.user.username}，确保租户正确: {user.tenant.name}")
                updated_instance = serializer.save(tenant=user.tenant)
                logger.info(f"【更新任务模板成功】ID: {updated_instance.id}，名称: {updated_instance.name}，租户: {user.tenant.name}")
        elif hasattr(user, 'sub_accounts') and user.sub_accounts.exists():
            logger.debug(f"【更新任务模板】用户是主账号，有子账号权限，可以修改子账号的模板")
            # 主member：可以修改子账号的资源
            if user_id:
                try:
                    target_user = User.objects.get(id=user_id)
                    logger.debug(f"【更新任务模板】找到目标用户: {target_user.username} (ID: {target_user.id})")
                    
                    # 检查目标用户是否为自己的子账号
                    if target_user.parent_id != user.id:
                        error_msg = "只能为自己的子账号修改模板"
                        logger.error(f"【更新任务模板失败】{error_msg}，目标用户父账号ID: {target_user.parent_id}，current用户ID: {user.id}")
                        raise serializers.ValidationError(_(error_msg))
                    
                    # 检查目标用户是否属于同一租户
                    if target_user.tenant != user.tenant:
                        error_msg = "Sub-accounts must belong to the same tenant"
                        logger.error(f"【更新任务模板失败】{error_msg}，子账号租户: {target_user.tenant.name if target_user.tenant else 'None'}")
                        raise serializers.ValidationError(_(error_msg))
                    
                    logger.info(f"【更新任务模板】即将更新任务模板，关联子账号: {target_user.username}，租户: {user.tenant.name}")
                    # 设置用户和租户
                    updated_instance = serializer.save(
                        user=target_user, 
                        tenant=user.tenant  # 强制使用current用户的租户
                    )
                    logger.info(f"【更新任务模板成功】ID: {updated_instance.id}，名称: {updated_instance.name}，用户(子账号): {target_user.username}，租户: {user.tenant.name}")
                except User.DoesNotExist:
                    error_msg = "Specified user does not exist"
                    logger.error(f"【更新任务模板失败】{error_msg}，指定的用户ID: {user_id}")
                    raise serializers.ValidationError(_(error_msg))
            else:
                # 未指定用户，保持原样，但确保租户正确
                logger.info(f"【更新任务模板】未指定用户，保持原有用户: {instance.user.username}，确保租户正确: {user.tenant.name}")
                updated_instance = serializer.save(tenant=user.tenant)
                logger.info(f"【更新任务模板成功】ID: {updated_instance.id}，名称: {updated_instance.name}，租户: {user.tenant.name}")
        else:
            logger.debug(f"【更新任务模板】普通用户，只能修改自己的模板")
            # 普通member：只能修改自己的
            if instance.user != user:
                error_msg = "无法修改其他用户的模板"
                logger.error(f"【更新任务模板失败】{error_msg}，current用户ID: {user.id}，模板所属用户ID: {instance.user.id}")
                raise serializers.ValidationError(_(error_msg))
            updated_instance = serializer.save(tenant=user.tenant)  # 确保租户正确
            logger.info(f"【更新任务模板成功】ID: {updated_instance.id}，名称: {updated_instance.name}，用户: {user.username}，租户: {user.tenant.name}")
