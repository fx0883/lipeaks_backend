# feedbacks/management/commands/retry_failed_emails.py

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta
import logging

from ...models import FeedbackEmailLog
from ...tasks import send_feedback_reply_email, send_status_change_email, send_verification_email
from ...utils import TaskExecutor

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '重试失败的邮件发送任务'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='重试最近多少小时内失败的邮件（默认24小时）'
        )
        parser.add_argument(
            '--email-type',
            type=str,
            choices=['reply', 'status_change', 'verification', 'all'],
            default='all',
            help='要重试的邮件类型'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='只显示统计信息，不实际重试'
        )
        parser.add_argument(
            '--force-async',
            action='store_true',
            help='强制异步执行（需要Redis/Celery可用）'
        )

    def handle(self, *args, **options):
        hours = options['hours']
        email_type = options['email_type']
        dry_run = options['dry_run']
        force_async = options['force_async']
        
        # 查询失败的邮件
        since = timezone.now() - timedelta(hours=hours)
        queryset = FeedbackEmailLog.objects.filter(
            status='failed',
            created_at__gte=since
        )
        
        if email_type != 'all':
            queryset = queryset.filter(email_type=email_type)
        
        failed_emails = queryset.order_by('-created_at')
        
        self.stdout.write(
            self.style.SUCCESS(f'找到 {failed_emails.count()} 个失败的邮件任务')
        )
        
        if dry_run:
            self.show_statistics(failed_emails)
            return
        
        if failed_emails.count() == 0:
            self.stdout.write(
                self.style.WARNING('没有需要重试的邮件任务')
            )
            return
        
        # 重试邮件
        success_count = 0
        failed_count = 0
        
        for email_log in failed_emails:
            try:
                task_func = self.get_task_function(email_log.email_type)
                target_id = self.get_target_id(email_log)
                
                if force_async:
                    # 强制异步执行
                    result = TaskExecutor.execute_task(
                        task_func,
                        target_id,
                        fallback_to_sync=False
                    )
                else:
                    # 允许降级到同步
                    result = TaskExecutor.execute_task(
                        task_func,
                        target_id,
                        fallback_to_sync=True
                    )
                
                if result.get('mode') in ['async', 'sync']:
                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'重试成功: {email_log.email_type} #{email_log.id} (模式: {result.get("mode")})')
                    )
                else:
                    failed_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'重试失败: {email_log.email_type} #{email_log.id}')
                    )
                    
            except Exception as e:
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(f'重试异常: {email_log.email_type} #{email_log.id} - {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n重试完成: 成功 {success_count}，失败 {failed_count}')
        )
    
    def show_statistics(self, failed_emails):
        """显示失败邮件的统计信息"""
        from django.db.models import Count
        
        # 按类型统计
        type_stats = failed_emails.values('email_type').annotate(
            count=Count('id')
        ).order_by('-count')
        
        self.stdout.write('\n按类型统计:')
        for stat in type_stats:
            self.stdout.write(f'  {stat["email_type"]}: {stat["count"]} 个')
        
        # 按时间统计
        self.stdout.write('\n最近的失败邮件:')
        for email_log in failed_emails[:10]:
            self.stdout.write(
                f'  #{email_log.id} - {email_log.email_type} - {email_log.recipient} - {email_log.created_at}'
            )
        
        if failed_emails.count() > 10:
            self.stdout.write(f'  ... 还有 {failed_emails.count() - 10} 个')
    
    def get_task_function(self, email_type):
        """根据邮件类型获取对应的任务函数"""
        task_map = {
            'reply': send_feedback_reply_email,
            'status_change': send_status_change_email,
            'verification': send_verification_email,
        }
        
        task_func = task_map.get(email_type)
        if not task_func:
            raise CommandError(f'未知的邮件类型: {email_type}')
        
        return task_func
    
    def get_target_id(self, email_log):
        """根据邮件类型获取目标ID"""
        if email_log.email_type == 'reply':
            # 需要通过feedback找到相关的reply
            # 这里简化处理，实际可能需要更复杂的逻辑
            reply = email_log.feedback.replies.filter(
                created_at__gte=email_log.created_at - timedelta(minutes=5)
            ).first()
            if reply:
                return reply.id
            else:
                raise CommandError(f'无法找到邮件日志 #{email_log.id} 对应的回复')
        
        elif email_log.email_type == 'status_change':
            # 需要找到状态历史记录
            history = email_log.feedback.status_history.filter(
                created_at__gte=email_log.created_at - timedelta(minutes=5)
            ).first()
            if history:
                return history.id
            else:
                raise CommandError(f'无法找到邮件日志 #{email_log.id} 对应的状态历史')
        
        elif email_log.email_type == 'verification':
            return email_log.feedback.id
        
        else:
            raise CommandError(f'未知的邮件类型: {email_log.email_type}')
