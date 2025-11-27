"""
许可证报告API视图
提供各类统计报告和数据分析功能
"""

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Count, Q, Sum, Avg
from django.core.cache import cache
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from common.permissions import IsSuperAdminOrTenantAdmin
from common.authentication.jwt_auth import JWTAuthentication
from applications.models import Application
from licenses.models import (
    License, LicenseActivation, LicenseUsageLog, MachineBinding, 
    SecurityAuditLog
)
from licenses.serializers import LicenseReportSerializer
import logging

logger = logging.getLogger('licenses.reports')


@extend_schema(
    tags=['许可证报告'],
    summary='获取许可证报告',
    description='生成许可证使用和统计报告，支持多种报告类型和时间范围',
    parameters=[
        OpenApiParameter(
            name='report_type',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            description='报告类型：overview|usage|activation|security|financial',
            required=True
        ),
        OpenApiParameter(
            name='start_date',
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            description='开始日期 (YYYY-MM-DD)',
            required=False
        ),
        OpenApiParameter(
            name='end_date',
            type=OpenApiTypes.DATE,
            location=OpenApiParameter.QUERY,
            description='结束日期 (YYYY-MM-DD)',
            required=False
        ),
        OpenApiParameter(
            name='product_id',
            type=OpenApiTypes.INT,
            location=OpenApiParameter.QUERY,
            description='产品ID过滤',
            required=False
        )
    ],
    responses={
        200: OpenApiResponse(
            description='报告数据',
            examples=[
                OpenApiExample(
                    'Overview Report',
                    value={
                        'report_type': 'overview',
                        'period': '2024-01-01 to 2024-01-31',
                        'data': {
                            'total_licenses': 150,
                            'active_licenses': 120,
                            'expired_licenses': 30,
                            'total_activations': 450,
                            'unique_machines': 380
                        }
                    }
                )
            ]
        ),
        400: OpenApiResponse(description='参数错误')
    }
)
@api_view(['GET'])
@permission_classes([IsSuperAdminOrTenantAdmin])
def license_reports(request):
    """
    生成许可证报告
    
    GET /api/v1/licenses/reports/
    """
    try:
        # 获取请求参数
        report_type = request.GET.get('report_type')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        product_id = request.GET.get('product_id')
        
        # 设置默认日期范围（最近30天）
        if not end_date:
            end_date = timezone.now().date()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # 根据用户权限过滤数据
        base_filter = {}
        if not request.user.is_super_admin and hasattr(request.user, 'tenant'):
            base_filter['license__tenant'] = request.user.tenant
        
        if product_id:
            base_filter['license__product_id'] = product_id
        
        # 根据报告类型生成数据
        if report_type == 'summary':
            report_data = generate_summary_report(start_date, end_date, base_filter)
        elif report_type == 'usage':
            report_data = generate_usage_report(start_date, end_date, base_filter)
        elif report_type == 'activation':
            report_data = generate_activation_report(start_date, end_date, base_filter)
        elif report_type == 'security':
            report_data = generate_security_report(start_date, end_date, base_filter)
        else:
            return Response({
                'success': False,
                'error': 'Invalid report type'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'report': {
                'type': report_type,
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'generated_at': timezone.now().isoformat(),
                'data': report_data
            }
        })
    
    except Exception as e:
        logger.error(f"报告生成失败: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['许可证报告'],
    summary='生成自定义报表',
    description='根据指定参数生成自定义许可证报表，支持异步生成和导出',
    request=LicenseReportSerializer,
    responses={
        200: OpenApiResponse(
            description='报表生成成功',
            examples=[
                OpenApiExample(
                    'Report Generation Success',
                    value={
                        'success': True,
                        'report_id': 'REPORT-2024-001',
                        'status': 'processing',
                        'estimated_completion': '2024-01-15T10:35:00Z'
                    }
                )
            ]
        ),
        400: OpenApiResponse(description='参数验证失败')
    }
)
@api_view(['POST'])
@permission_classes([IsSuperAdminOrTenantAdmin])
def generate_report(request):
    """
    生成许可证报告
    
    POST /api/v1/licenses/reports/generate/
    """
    serializer = LicenseReportSerializer(data=request.data)
    if not serializer.is_valid():
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # 获取请求参数
        start_date = serializer.validated_data.get('start_date')
        end_date = serializer.validated_data.get('end_date')
        product_id = serializer.validated_data.get('product_id')
        tenant_id = serializer.validated_data.get('tenant_id')
        report_type = serializer.validated_data['report_type']
        
        # 设置默认日期范围（最近30天）
        if not end_date:
            end_date = timezone.now().date()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # 根据用户权限过滤数据
        base_filter = {}
        if not request.user.is_super_admin and hasattr(request.user, 'tenant'):
            base_filter['license__tenant'] = request.user.tenant
        
        if tenant_id:
            base_filter['license__tenant_id'] = tenant_id
        
        if product_id:
            base_filter['license__product_id'] = product_id
        
        # 根据报告类型生成数据
        if report_type == 'summary':
            report_data = generate_summary_report(start_date, end_date, base_filter)
        elif report_type == 'usage':
            report_data = generate_usage_report(start_date, end_date, base_filter)
        elif report_type == 'activation':
            report_data = generate_activation_report(start_date, end_date, base_filter)
        elif report_type == 'security':
            report_data = generate_security_report(start_date, end_date, base_filter)
        else:
            return Response({
                'success': False,
                'error': 'Invalid report type'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'success': True,
            'report': {
                'type': report_type,
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'generated_at': timezone.now().isoformat(),
                'data': report_data
            }
        })
    
    except Exception as e:
        logger.error(f"报告生成失败: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def generate_summary_report(start_date, end_date, base_filter):
    """生成概要报告"""
    
    # 许可证统计
    license_stats = License.objects.filter(
        created_at__date__range=[start_date, end_date],
        **{k.replace('license__', ''): v for k, v in base_filter.items() if k.startswith('license__')}
    ).aggregate(
        total_licenses=Count('id'),
        active_licenses=Count('id', filter=Q(status='activated')),
        expired_licenses=Count('id', filter=Q(expires_at__lt=timezone.now())),
        revoked_licenses=Count('id', filter=Q(status='revoked'))
    )
    
    # 激活统计
    activation_filter = {**base_filter, 'activated_at__date__range': [start_date, end_date]}
    activation_stats = LicenseActivation.objects.filter(**activation_filter).aggregate(
        total_activations=Count('id'),
        successful_activations=Count('id', filter=Q(result='success')),
        failed_activations=Count('id', filter=Q(result='failed'))
    )
    
    # 机器绑定统计
    binding_filter = {**base_filter, 'first_seen_at__date__range': [start_date, end_date]}
    binding_stats = MachineBinding.objects.filter(**binding_filter).aggregate(
        new_machines=Count('id'),
        active_machines=Count('id', filter=Q(status='active')),
        blocked_machines=Count('id', filter=Q(status='blocked'))
    )
    
    # 使用统计
    usage_filter = {**base_filter, 'timestamp__date__range': [start_date, end_date]}
    usage_stats = LicenseUsageLog.objects.filter(**usage_filter).aggregate(
        total_events=Count('id'),
        startup_events=Count('id', filter=Q(event_type='startup')),
        heartbeat_events=Count('id', filter=Q(event_type='heartbeat'))
    )
    
    return {
        'licenses': license_stats,
        'activations': activation_stats,
        'machine_bindings': binding_stats,
        'usage': usage_stats
    }


def generate_usage_report(start_date, end_date, base_filter):
    """生成使用报告"""
    
    # 每日使用统计
    daily_usage = []
    current_date = start_date
    
    while current_date <= end_date:
        daily_filter = {
            **base_filter,
            'timestamp__date': current_date
        }
        
        day_stats = LicenseUsageLog.objects.filter(**daily_filter).aggregate(
            total_events=Count('id'),
            unique_licenses=Count('license', distinct=True),
            unique_machines=Count('machine_binding', distinct=True)
        )
        
        daily_usage.append({
            'date': current_date.isoformat(),
            'stats': day_stats
        })
        
        current_date += timedelta(days=1)
    
    # 事件类型分布
    event_distribution = LicenseUsageLog.objects.filter(
        timestamp__date__range=[start_date, end_date],
        **base_filter
    ).values('event_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # 热门产品
    popular_products = LicenseUsageLog.objects.filter(
        timestamp__date__range=[start_date, end_date],
        **base_filter
    ).values(
        'license__product__name'
    ).annotate(
        usage_count=Count('id')
    ).order_by('-usage_count')[:10]
    
    return {
        'daily_usage': daily_usage,
        'event_distribution': list(event_distribution),
        'popular_products': list(popular_products)
    }


def generate_activation_report(start_date, end_date, base_filter):
    """生成激活报告"""
    
    # 激活成功率趋势
    activation_trend = []
    current_date = start_date
    
    while current_date <= end_date:
        daily_filter = {
            **base_filter,
            'activated_at__date': current_date
        }
        
        day_activations = LicenseActivation.objects.filter(**daily_filter)
        total = day_activations.count()
        successful = day_activations.filter(result='success').count()
        success_rate = (successful / total * 100) if total > 0 else 0
        
        activation_trend.append({
            'date': current_date.isoformat(),
            'total_attempts': total,
            'successful': successful,
            'success_rate': round(success_rate, 2)
        })
        
        current_date += timedelta(days=1)
    
    # 失败原因分析
    failed_activations = LicenseActivation.objects.filter(
        activated_at__date__range=[start_date, end_date],
        result='failed',
        **base_filter
    )
    
    failure_reasons = {}
    for activation in failed_activations:
        reason = activation.error_message or 'Unknown error'
        failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
    
    # IP地址分布
    ip_distribution = LicenseActivation.objects.filter(
        activated_at__date__range=[start_date, end_date],
        **base_filter
    ).exclude(
        ip_address__isnull=True
    ).values('ip_address').annotate(
        count=Count('id')
    ).order_by('-count')[:20]
    
    return {
        'activation_trend': activation_trend,
        'failure_reasons': failure_reasons,
        'ip_distribution': list(ip_distribution)
    }


def generate_security_report(start_date, end_date, base_filter):
    """生成安全报告"""
    
    # 安全事件统计
    security_filter = {'timestamp__date__range': [start_date, end_date]}
    if 'license__tenant' in base_filter:
        security_filter['tenant'] = base_filter['license__tenant']
    
    security_events = SecurityAuditLog.objects.filter(**security_filter).values(
        'event_type', 'severity'
    ).annotate(count=Count('id')).order_by('-count')
    
    # 可疑活动检测
    suspicious_activities = SecurityAuditLog.objects.filter(
        event_type='suspicious_activity',
        **security_filter
    ).values('details').annotate(count=Count('id'))
    
    # 高风险IP地址
    high_risk_ips = SecurityAuditLog.objects.filter(
        severity__in=['HIGH', 'CRITICAL'],
        **security_filter
    ).exclude(
        ip_address__isnull=True
    ).values('ip_address').annotate(
        incident_count=Count('id')
    ).order_by('-incident_count')[:10]
    
    # 异常激活模式
    rapid_activations = LicenseActivation.objects.filter(
        activated_at__date__range=[start_date, end_date],
        **base_filter
    ).values('license').annotate(
        activation_count=Count('id')
    ).filter(activation_count__gt=5).order_by('-activation_count')
    
    return {
        'security_events': list(security_events),
        'suspicious_activities': list(suspicious_activities),
        'high_risk_ips': list(high_risk_ips),
        'rapid_activations': list(rapid_activations)
    }


@extend_schema(
    tags=['许可证仪表板'],
    summary='获取仪表板统计数据',
    description='获取许可证管理仪表板的统计数据和图表信息',
    responses={
        200: OpenApiResponse(
            description='仪表板统计数据',
            examples=[
                OpenApiExample(
                    'Dashboard Stats',
                    value={
                        'total_licenses': 250,
                        'active_licenses': 200,
                        'expired_licenses': 50,
                        'total_activations': 1500,
                        'unique_machines': 800,
                        'recent_activity': {
                            'new_licenses_this_month': 15,
                            'new_activations_today': 25,
                            'suspicious_activities': 3
                        },
                        'charts': {
                            'license_usage_trend': [],
                            'activation_by_product': [],
                            'geographic_distribution': []
                        }
                    }
                )
            ]
        )
    }
)
@api_view(['GET'])
@permission_classes([IsSuperAdminOrTenantAdmin])
def dashboard_stats(request):
    """
    获取仪表板统计数据
    
    GET /api/v1/licenses/reports/dashboard/
    """
    try:
        # 根据用户权限过滤数据
        license_filter = {}
        if not request.user.is_super_admin and hasattr(request.user, 'tenant'):
            license_filter['tenant'] = request.user.tenant
        
        # 基础统计
        total_licenses = License.objects.filter(**license_filter).count()
        active_licenses = License.objects.filter(
            status='activated', **license_filter
        ).count()
        
        # 即将过期的许可证（30天内）
        thirty_days_later = timezone.now() + timedelta(days=30)
        expiring_soon = License.objects.filter(
            expires_at__lte=thirty_days_later,
            expires_at__gte=timezone.now(),
            **license_filter
        ).count()
        
        # 今日激活统计
        today = timezone.now().date()
        today_activations = LicenseActivation.objects.filter(
            activated_at__date=today,
            **{f'license__{k}': v for k, v in license_filter.items()}
        ).count()
        
        # 活跃机器数
        active_machines = MachineBinding.objects.filter(
            status='active',
            **{f'license__{k}': v for k, v in license_filter.items()}
        ).count()
        
        # 最近7天的激活趋势
        activation_trend = []
        for i in range(7):
            date = today - timedelta(days=i)
            count = LicenseActivation.objects.filter(
                activated_at__date=date,
                result='success',
                **{f'license__{k}': v for k, v in license_filter.items()}
            ).count()
            activation_trend.append({
                'date': date.isoformat(),
                'count': count
            })
        
        activation_trend.reverse()  # 按时间正序
        
        return Response({
            'summary': {
                'total_licenses': total_licenses,
                'active_licenses': active_licenses,
                'expiring_soon': expiring_soon,
                'today_activations': today_activations,
                'active_machines': active_machines
            },
            'trends': {
                'activation_trend': activation_trend
            },
            'generated_at': timezone.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"仪表板统计获取失败: {str(e)}")
        return Response({
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=['许可证统计'],
    summary='获取许可证统计数据',
    description='获取许可证系统的综合统计数据，包括许可证状态、激活情况、机器绑定等统计信息',
    responses={
        200: OpenApiResponse(
            description='许可证统计数据',
            examples=[
                OpenApiExample(
                    'License Statistics',
                    value={
                        'success': True,
                        'data': {
                            'overview': {
                                'total_licenses': 250,
                                'active_licenses': 200,
                                'expired_licenses': 30,
                                'revoked_licenses': 20,
                                'activation_rate': 80.0
                            },
                            'products': {
                                'total_products': 5,
                                'active_products': 4
                            },
                            'activations': {
                                'total_activations': 1500,
                                'successful_activations': 1350,
                                'failed_activations': 150,
                                'success_rate': 90.0
                            },
                            'machines': {
                                'total_machines': 800,
                                'active_machines': 750,
                                'blocked_machines': 50
                            },
                            'usage': {
                                'total_events': 50000,
                                'recent_events_24h': 2500
                            }
                        }
                    }
                )
            ]
        )
    }
)
@api_view(['GET'])
@permission_classes([IsSuperAdminOrTenantAdmin])
def license_statistics(request):
    """
    获取许可证统计数据
    
    GET /api/v1/licenses/statistics/
    """
    try:
        # 根据用户权限过滤数据
        license_filter = {}
        activation_filter = {}
        machine_filter = {}
        usage_filter = {}
        
        if not request.user.is_super_admin and hasattr(request.user, 'tenant'):
            license_filter['tenant'] = request.user.tenant
            activation_filter['license__tenant'] = request.user.tenant
            machine_filter['license__tenant'] = request.user.tenant
            usage_filter['license__tenant'] = request.user.tenant
        
        # 许可证概览统计
        license_overview = License.objects.filter(**license_filter).aggregate(
            total_licenses=Count('id'),
            active_licenses=Count('id', filter=Q(status='activated')),
            generated_licenses=Count('id', filter=Q(status='generated')),  
            suspended_licenses=Count('id', filter=Q(status='suspended')),
            revoked_licenses=Count('id', filter=Q(status='revoked')),
            expired_licenses=Count('id', filter=Q(expires_at__lt=timezone.now()))
        )
        
        # 计算激活率
        total = license_overview['total_licenses'] or 0
        active = license_overview['active_licenses'] or 0
        activation_rate = (active / total * 100) if total > 0 else 0
        
        # 产品统计
        product_stats = Application.objects.aggregate(
            total_products=Count('id'),
            active_products=Count('id', filter=Q(status='active')),
            inactive_products=Count('id', filter=Q(status='inactive'))
        )
        
        # 激活统计
        activation_stats = LicenseActivation.objects.filter(**activation_filter).aggregate(
            total_activations=Count('id'),
            successful_activations=Count('id', filter=Q(result='success')),
            failed_activations=Count('id', filter=Q(result='failed')),
            pending_activations=Count('id', filter=Q(result='pending'))
        )
        
        # 计算激活成功率
        total_attempts = activation_stats['total_activations'] or 0
        successful = activation_stats['successful_activations'] or 0
        success_rate = (successful / total_attempts * 100) if total_attempts > 0 else 0
        
        # 机器绑定统计
        machine_stats = MachineBinding.objects.filter(**machine_filter).aggregate(
            total_machines=Count('id'),
            active_machines=Count('id', filter=Q(status='active')),
            inactive_machines=Count('id', filter=Q(status='inactive')),
            blocked_machines=Count('id', filter=Q(status='blocked'))
        )
        
        # 使用统计
        now = timezone.now()
        today = now.date()
        yesterday = today - timedelta(days=1)
        
        usage_stats = LicenseUsageLog.objects.filter(**usage_filter).aggregate(
            total_events=Count('id'),
            recent_events_24h=Count('id', filter=Q(timestamp__gte=now - timedelta(hours=24))),
            heartbeat_events=Count('id', filter=Q(event_type='heartbeat')),
            startup_events=Count('id', filter=Q(event_type='startup'))
        )
        
        # 租户统计（仅超级管理员可见）
        tenant_stats = {}
        if request.user.is_super_admin:
            from tenants.models import Tenant
            tenant_stats = {
                'total_tenants': Tenant.objects.count(),
                'active_tenants': Tenant.objects.filter(status='active').count(),
                'tenants_with_licenses': License.objects.values('tenant').distinct().count()
            }
        
        # 时间范围统计
        this_month_start = today.replace(day=1)
        last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)
        
        time_stats = {
            'licenses_this_month': License.objects.filter(
                created_at__date__gte=this_month_start,
                **license_filter
            ).count(),
            'licenses_last_month': License.objects.filter(
                created_at__date__gte=last_month_start,
                created_at__date__lt=this_month_start,
                **license_filter
            ).count(),
            'activations_today': LicenseActivation.objects.filter(
                activated_at__date=today,
                **activation_filter
            ).count(),
            'activations_yesterday': LicenseActivation.objects.filter(
                activated_at__date=yesterday,
                **activation_filter
            ).count()
        }
        
        response_data = {
            'overview': {
                **license_overview,
                'activation_rate': round(activation_rate, 2)
            },
            'products': product_stats,
            'activations': {
                **activation_stats,
                'success_rate': round(success_rate, 2)
            },
            'machines': machine_stats,
            'usage': usage_stats,
            'time_based': time_stats
        }
        
        # 添加租户统计（仅超级管理员）
        if tenant_stats:
            response_data['tenants'] = tenant_stats
        
        return Response({
            'success': True,
            'data': response_data,
            'generated_at': timezone.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"许可证统计获取失败: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
