# feedbacks/management/commands/test_api_performance.py

from django.core.management.base import BaseCommand
import requests
import time
import threading
import statistics


class Command(BaseCommand):
    help = '测试API响应时间，验证线程池优化效果'

    def add_arguments(self, parser):
        parser.add_argument(
            '--url',
            type=str,
            default='http://localhost:8000/api/v1/feedbacks/feedbacks/2/replies/',
            help='要测试的API URL'
        )
        parser.add_argument(
            '--token', 
            type=str,
            required=True,
            help='JWT认证Token'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=5,
            help='测试次数（默认5次）'
        )
        parser.add_argument(
            '--timeout',
            type=int, 
            default=10,
            help='请求超时时间（秒）'
        )

    def handle(self, *args, **options):
        url = options['url']
        token = options['token'] 
        count = options['count']
        timeout = options['timeout']
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting API performance test...')
        )
        self.stdout.write(f'URL: {url}')
        self.stdout.write(f'Test count: {count}')
        self.stdout.write(f'Timeout: {timeout}s\n')
        
        response_times = []
        success_count = 0
        error_count = 0
        timeout_count = 0
        
        for i in range(count):
            data = {
                'content': f'Performance test #{i+1} from {threading.current_thread().name}',
                'is_internal_note': False
            }
            
            try:
                start_time = time.time()
                response = requests.post(
                    url, 
                    headers=headers, 
                    json=data, 
                    timeout=timeout
                )
                end_time = time.time()
                
                response_time = end_time - start_time
                response_times.append(response_time)
                
                if response.status_code in [200, 201]:
                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Test {i+1}: {response_time:.2f}s - Status: {response.status_code}')
                    )
                else:
                    error_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'Test {i+1}: {response_time:.2f}s - Status: {response.status_code}')
                    )
                    
            except requests.exceptions.Timeout:
                timeout_count += 1
                self.stdout.write(
                    self.style.ERROR(f'Test {i+1}: TIMEOUT (>{timeout}s)')
                )
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'Test {i+1}: ERROR - {str(e)}')
                )
                
            # 避免过于频繁的请求
            time.sleep(0.5)
        
        # 计算统计数据
        if response_times:
            avg_time = statistics.mean(response_times)
            min_time = min(response_times)
            max_time = max(response_times) 
            median_time = statistics.median(response_times)
            
            self.stdout.write('\n' + '='*50)
            self.stdout.write(
                self.style.SUCCESS('Performance Test Results:')
            )
            self.stdout.write(f'Total tests: {count}')
            self.stdout.write(f'Successful: {success_count}')
            self.stdout.write(f'Errors: {error_count}')
            self.stdout.write(f'Timeouts: {timeout_count}')
            self.stdout.write('\nResponse Time Statistics:')
            self.stdout.write(f'Average: {avg_time:.2f}s')
            self.stdout.write(f'Minimum: {min_time:.2f}s')
            self.stdout.write(f'Maximum: {max_time:.2f}s')
            self.stdout.write(f'Median: {median_time:.2f}s')
            
            # 性能评估
            self.stdout.write('\nPerformance Assessment:')
            if avg_time < 1.0:
                self.stdout.write(
                    self.style.SUCCESS('[EXCELLENT] Average response time < 1s')
                )
            elif avg_time < 3.0:
                self.stdout.write(
                    self.style.SUCCESS('[GOOD] Average response time < 3s')
                )
            elif avg_time < 5.0:
                self.stdout.write(
                    self.style.WARNING('[FAIR] Average response time < 5s')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('[POOR] Average response time >= 5s')
                )
            
            # 线程池效果评估
            if max_time - min_time < 2.0:
                self.stdout.write(
                    self.style.SUCCESS('[CONSISTENT] Response times are stable (thread pool working well)')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'[VARIABLE] Response time variance is {max_time - min_time:.2f}s')
                )
                
        else:
            self.stdout.write(
                self.style.ERROR('No successful responses to analyze')
            )
