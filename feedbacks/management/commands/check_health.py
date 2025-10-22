"""
Management command to check system health
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from feedbacks.utils import RedisHealthChecker
import sys


class Command(BaseCommand):
    help = 'Check system health and Redis connectivity'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed information'
        )
        parser.add_argument(
            '--fail-on-redis',
            action='store_true',
            help='Exit with error code if Redis is unavailable'
        )

    def handle(self, *args, **options):
        verbose = options.get('verbose', False)
        fail_on_redis = options.get('fail_on_redis', False)
        
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('System Health Check'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        # 检查Redis
        self.stdout.write('\n[*] Checking Redis connection...')
        redis_status = RedisHealthChecker.get_redis_status()
        
        if redis_status['available']:
            self.stdout.write(self.style.SUCCESS('[OK] Redis: Available'))
            if verbose:
                self.stdout.write(f"   Version: {redis_status.get('version', 'N/A')}")
                self.stdout.write(f"   Mode: {redis_status.get('mode', 'N/A')}")
                self.stdout.write(f"   Connected Clients: {redis_status.get('connected_clients', 'N/A')}")
                self.stdout.write(f"   Memory Used: {redis_status.get('used_memory_human', 'N/A')}")
                self.stdout.write(f"   Uptime: {redis_status.get('uptime_days', 'N/A')} days")
        else:
            if redis_status['mode'] == 'database':
                self.stdout.write(self.style.WARNING('[WARN] Redis: Not configured (using database)'))
                self.stdout.write(self.style.WARNING('   Message: Using database as broker'))
                self.stdout.write(self.style.WARNING('   Impact: Lower performance, synchronous email sending'))
            else:
                self.stdout.write(self.style.ERROR('[FAIL] Redis: Unavailable'))
                self.stdout.write(self.style.ERROR(f"   Error: {redis_status.get('error', 'Unknown error')}"))
                self.stdout.write(self.style.ERROR('   Impact: Email tasks will run synchronously'))
                
                if fail_on_redis:
                    sys.exit(1)
        
        # 检查Celery配置
        self.stdout.write('\n[*] Checking Celery configuration...')
        broker_url = getattr(settings, 'CELERY_BROKER_URL', None)
        
        if broker_url:
            if broker_url == 'django-db':
                self.stdout.write(self.style.WARNING('[WARN] Celery: Using database broker'))
                self.stdout.write(self.style.WARNING('   Recommendation: Use Redis for better performance'))
            elif redis_status['available']:
                self.stdout.write(self.style.SUCCESS('[OK] Celery: Configured with Redis'))
            else:
                self.stdout.write(self.style.WARNING('[WARN] Celery: Redis configured but unavailable'))
                self.stdout.write(self.style.WARNING('   Status: Will fallback to synchronous execution'))
        else:
            self.stdout.write(self.style.ERROR('[FAIL] Celery: Not configured'))
        
        if verbose and broker_url:
            # 隐藏密码
            safe_url = broker_url
            if '@' in safe_url:
                parts = safe_url.split('@')
                safe_url = '***@' + parts[-1]
            self.stdout.write(f"   Broker URL: {safe_url}")
        
        # 检查数据库
        self.stdout.write('\n[*] Checking database connection...')
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            self.stdout.write(self.style.SUCCESS('[OK] Database: Connected'))
            if verbose:
                self.stdout.write(f"   Type: {connection.vendor}")
        except Exception as e:
            self.stdout.write(self.style.ERROR('[FAIL] Database: Connection failed'))
            self.stdout.write(self.style.ERROR(f"   Error: {str(e)}"))
            sys.exit(1)
        
        # 检查邮件配置
        self.stdout.write('\n[*] Checking email configuration...')
        email_backend = getattr(settings, 'EMAIL_BACKEND', None)
        
        if email_backend:
            if 'console' in email_backend.lower():
                self.stdout.write(self.style.WARNING('[WARN] Email: Console backend (development only)'))
                self.stdout.write(self.style.WARNING('   Recommendation: Configure SMTP for production'))
            else:
                self.stdout.write(self.style.SUCCESS('[OK] Email: SMTP configured'))
            
            if verbose:
                self.stdout.write(f"   Backend: {email_backend}")
                self.stdout.write(f"   Host: {getattr(settings, 'EMAIL_HOST', 'N/A')}")
                self.stdout.write(f"   Port: {getattr(settings, 'EMAIL_PORT', 'N/A')}")
        else:
            self.stdout.write(self.style.ERROR('[FAIL] Email: Not configured'))
        
        # 降级状态检查
        self.stdout.write('\n[*] Fallback mechanism status...')
        if redis_status['available']:
            self.stdout.write(self.style.SUCCESS('[OK] Primary mode: Async (via Redis)'))
        else:
            self.stdout.write(self.style.WARNING('[WARN] Fallback mode: Synchronous'))
            self.stdout.write(self.style.WARNING('   All email tasks will execute synchronously'))
            self.stdout.write(self.style.WARNING('   API responses may be slower'))
        
        # 总结和建议
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('Summary'))
        self.stdout.write('=' * 60)
        
        if redis_status['available']:
            self.stdout.write(self.style.SUCCESS('[OK] System is running optimally'))
        elif redis_status['mode'] == 'database':
            self.stdout.write(self.style.WARNING('[WARN] System is running in database broker mode'))
            self.stdout.write('\n[i] Recommendations:')
            self.stdout.write('   1. Setup external Redis (Upstash) for better performance')
            self.stdout.write('   2. See: temp1022/External_Redis_Services_Guide.md')
        else:
            self.stdout.write(self.style.WARNING('[WARN] System is running in degraded mode'))
            self.stdout.write('\n[i] Recommendations:')
            self.stdout.write('   1. Check Redis connection')
            self.stdout.write('   2. Setup external Redis service (Upstash - Free)')
            self.stdout.write('   3. Or use database broker: CELERY_BROKER_URL = "django-db"')
            self.stdout.write('   4. See: temp1022/Redis_FAQ_ZH.md for solutions')
        
        self.stdout.write('\n' + '=' * 60)
        
        # 退出码
        if not redis_status['available'] and fail_on_redis:
            sys.exit(1)
        else:
            sys.exit(0)
