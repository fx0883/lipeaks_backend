# feedbacks/management/commands/monitor_email_threads.py

from django.core.management.base import BaseCommand
import threading
import time


class Command(BaseCommand):
    help = '监控邮件发送线程池状态'

    def add_arguments(self, parser):
        parser.add_argument(
            '--duration',
            type=int,
            default=30,
            help='监控持续时间（秒，默认30秒）'
        )
        parser.add_argument(
            '--interval',
            type=float,
            default=2.0,
            help='检查间隔（秒，默认2秒）'
        )

    def handle(self, *args, **options):
        duration = options['duration']
        interval = options['interval']
        
        from ...services import _email_thread_pool
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting email thread pool monitoring...')
        )
        self.stdout.write(f'Duration: {duration}s')
        self.stdout.write(f'Check interval: {interval}s')
        self.stdout.write(f'Thread pool max workers: {_email_thread_pool.max_workers}\n')
        
        start_time = time.time()
        check_count = 0
        
        try:
            while time.time() - start_time < duration:
                check_count += 1
                current_time = time.strftime("%H:%M:%S")
                
                # 获取当前活跃线程信息
                active_threads = threading.active_count()
                current_thread = threading.current_thread().name
                
                # 获取所有线程名称
                all_threads = [t.name for t in threading.enumerate()]
                email_threads = [name for name in all_threads if 'email-sender' in name]
                
                self.stdout.write(f'[{current_time}] Check #{check_count}:')
                self.stdout.write(f'  Total threads: {active_threads}')
                self.stdout.write(f'  Email sender threads: {len(email_threads)}')
                self.stdout.write(f'  Current thread: {current_thread}')
                
                if email_threads:
                    self.stdout.write('  Active email threads:')
                    for thread_name in email_threads[:5]:  # 显示前5个
                        self.stdout.write(f'    - {thread_name}')
                    if len(email_threads) > 5:
                        self.stdout.write(f'    ... and {len(email_threads) - 5} more')
                
                # 尝试获取线程池状态（如果可能）
                if hasattr(_email_thread_pool.executor, '_threads'):
                    pool_threads = len(_email_thread_pool.executor._threads)
                    self.stdout.write(f'  Thread pool size: {pool_threads}')
                
                self.stdout.write('')  # 空行
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('\nMonitoring interrupted by user')
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Monitoring completed. Total checks: {check_count}')
        )
        
        # 显示最终线程状态
        final_active = threading.active_count()
        final_email_threads = [t.name for t in threading.enumerate() if 'email-sender' in t.name]
        
        self.stdout.write('\nFinal thread status:')
        self.stdout.write(f'Total threads: {final_active}')
        self.stdout.write(f'Email threads: {len(final_email_threads)}')
        
        if final_email_threads:
            self.stdout.write('Active email threads:')
            for thread_name in final_email_threads:
                self.stdout.write(f'  - {thread_name}')
