"""
Health Check Views

This module contains views for system health monitoring.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from ..utils import RedisHealthChecker


class SystemHealthView(APIView):
    """系统健康检查视图"""
    permission_classes = [IsAdminUser]
    
    @extend_schema(
        tags=['Feedback System'],
        summary='Check system health',
        description='Check the health status of critical system components including Redis, database, and email service.',
        responses={
            200: OpenApiResponse(
                description='System health status',
                examples=[
                    OpenApiExample(
                        'Healthy System',
                        value={
                            'status': 'healthy',
                            'components': {
                                'redis': {
                                    'available': True,
                                    'mode': 'redis',
                                    'version': '7.0.0'
                                },
                                'database': {
                                    'available': True,
                                    'type': 'MySQL'
                                },
                                'celery': {
                                    'available': True,
                                    'mode': 'async',
                                    'fallback_enabled': True
                                }
                            },
                            'recommendations': []
                        }
                    ),
                    OpenApiExample(
                        'Redis Unavailable',
                        value={
                            'status': 'degraded',
                            'components': {
                                'redis': {
                                    'available': False,
                                    'error': 'Connection refused'
                                },
                                'database': {
                                    'available': True
                                },
                                'celery': {
                                    'available': True,
                                    'mode': 'sync',
                                    'fallback_enabled': True
                                }
                            },
                            'recommendations': [
                                'Redis is not available. Email tasks will run synchronously.',
                                'Consider setting up Redis for better performance.'
                            ]
                        }
                    )
                ]
            ),
            403: OpenApiResponse(description='Permission denied')
        }
    )
    def get(self, request):
        """
        Get system health status
        
        检查所有关键组件的健康状况
        """
        health_data = {
            'status': 'healthy',
            'components': {},
            'recommendations': []
        }
        
        # 检查Redis
        redis_status = RedisHealthChecker.get_redis_status()
        health_data['components']['redis'] = redis_status
        
        if not redis_status['available']:
            health_data['status'] = 'degraded'
            if redis_status['mode'] == 'redis':
                health_data['recommendations'].append(
                    'Redis is not available. Email tasks will run synchronously.'
                )
                health_data['recommendations'].append(
                    'Consider setting up Redis or using external Redis service (Upstash).'
                )
        
        # 检查数据库
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            health_data['components']['database'] = {
                'available': True,
                'type': connection.vendor
            }
        except Exception as e:
            health_data['components']['database'] = {
                'available': False,
                'error': str(e)
            }
            health_data['status'] = 'unhealthy'
            health_data['recommendations'].append('Database connection failed!')
        
        # 检查Celery配置
        from django.conf import settings
        broker_url = getattr(settings, 'CELERY_BROKER_URL', None)
        
        if broker_url == 'django-db':
            celery_mode = 'database'
            health_data['recommendations'].append(
                'Using database as Celery broker. Performance may be limited.'
            )
        elif redis_status['available']:
            celery_mode = 'async'
        else:
            celery_mode = 'sync'
        
        health_data['components']['celery'] = {
            'available': True,
            'mode': celery_mode,
            'fallback_enabled': True,
            'broker': broker_url
        }
        
        # 检查邮件配置
        email_backend = getattr(settings, 'EMAIL_BACKEND', None)
        if email_backend == 'django.core.mail.backends.console.EmailBackend':
            health_data['components']['email'] = {
                'available': True,
                'mode': 'console',
                'warning': 'Emails are being sent to console only'
            }
            health_data['recommendations'].append(
                'Email backend is set to console. Configure SMTP for production.'
            )
        else:
            health_data['components']['email'] = {
                'available': True,
                'mode': 'smtp',
                'backend': email_backend
            }
        
        return Response(health_data)


class RedisStatusView(APIView):
    """Redis状态检查视图"""
    permission_classes = [IsAdminUser]
    
    @extend_schema(
        tags=['Feedback System'],
        summary='Check Redis status',
        description='Get detailed Redis connection status and information.',
        responses={
            200: OpenApiResponse(
                description='Redis status information'
            )
        }
    )
    def get(self, request):
        """Get Redis detailed status"""
        status = RedisHealthChecker.get_redis_status()
        
        # 添加建议
        if not status['available']:
            status['suggestions'] = [
                {
                    'priority': 'high',
                    'title': 'Setup External Redis',
                    'description': 'Use Upstash for free Redis hosting',
                    'link': '/api/v1/feedbacks/docs/#section/External-Redis-Services'
                },
                {
                    'priority': 'medium',
                    'title': 'Use Database Broker',
                    'description': 'Temporary solution with lower performance',
                    'config': 'CELERY_BROKER_URL = "django-db"'
                }
            ]
        
        return Response(status)
