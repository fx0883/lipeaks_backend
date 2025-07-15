import os
import time
import datetime
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = '清理超过指定天数的日志文件'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=settings.LOG_RETENTION_DAYS,
            help=f'要保留的日志天数，默认为{settings.LOG_RETENTION_DAYS}天'
        )

    def handle(self, *args, **options):
        days = options['days']
        logs_dir = settings.LOGS_DIR
        self.stdout.write(f'开始清理{days}天前的日志文件...')
        
        # 计算截止日期的时间戳
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        
        # 获取日志目录中的所有文件
        log_files = []
        for root, dirs, files in os.walk(logs_dir):
            for file in files:
                # 处理新的日志文件命名格式 (base_name.YYYY-MM-DD.log)
                if file.endswith('.log'):
                    file_path = os.path.join(root, file)
                    log_files.append(file_path)
                    
                    # 尝试从文件名中提取日期
                    try:
                        # 假设文件名格式为 base_name.YYYY-MM-DD.log
                        parts = file.split('.')
                        if len(parts) >= 3:  # 至少有base_name、日期和.log三部分
                            date_str = parts[-2]  # 日期应该是倒数第二部分
                            # 尝试解析日期
                            try:
                                file_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').timestamp()
                                # 如果日期早于截止日期，标记为删除
                                if file_date < cutoff_time:
                                    self.stdout.write(f'根据文件名日期删除: {file_path}')
                                    try:
                                        os.remove(file_path)
                                    except Exception as e:
                                        self.stderr.write(f'删除文件失败: {file_path}, 错误: {str(e)}')
                                continue  # 已处理此文件，继续下一个
                            except ValueError:
                                # 日期格式不正确，回退到使用文件修改时间
                                pass
                    except Exception:
                        # 任何解析错误，回退到使用文件修改时间
                        pass
                    
                    # 如果无法从文件名解析日期，使用文件修改时间
                    file_mtime = os.path.getmtime(file_path)
                    if file_mtime < cutoff_time:
                        try:
                            self.stdout.write(f'根据修改时间删除: {file_path}')
                            os.remove(file_path)
                        except Exception as e:
                            self.stderr.write(f'删除文件失败: {file_path}, 错误: {str(e)}')
        
        self.stdout.write(self.style.SUCCESS(f'日志清理完成')) 