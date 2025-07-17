from django.core.management.base import BaseCommand
from django.conf import settings
import os
import pymysql

class Command(BaseCommand):
    help = '执行 common_config.sql 脚本'

    def handle(self, *args, **options):
        sql_path = 'docs/init_sql/common_config.sql'
        
        if not os.path.exists(sql_path):
            self.stdout.write(self.style.ERROR(f'SQL文件不存在: {sql_path}'))
            return
            
        self.stdout.write(self.style.SUCCESS(f'开始执行SQL脚本: {sql_path}'))
        
        # 读取SQL文件内容
        with open(sql_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 使用pymysql直接连接数据库
        try:
            # 从Django设置中获取数据库连接信息
            db_settings = settings.DATABASES['default']
            conn = pymysql.connect(
                host=db_settings['HOST'],
                user=db_settings['USER'],
                password=db_settings['PASSWORD'],
                database=db_settings['NAME'],
                port=int(db_settings.get('PORT', 3306)),
                charset='utf8mb4',
                # 关键参数：允许执行多条SQL语句
                client_flag=pymysql.constants.CLIENT.MULTI_STATEMENTS
            )
            
            with conn.cursor() as cursor:
                # 执行整个SQL脚本
                cursor.execute(sql_content)
                
                # 处理所有结果集
                while cursor.nextset():
                    pass
                
            # 提交事务
            conn.commit()
            self.stdout.write(self.style.SUCCESS('SQL脚本执行成功'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'SQL脚本执行失败: {str(e)}'))
        finally:
            if 'conn' in locals():
                conn.close() 