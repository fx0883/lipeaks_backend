# 数据库配置与迁移

本文档将指导您在cPanel环境中配置数据库连接，执行数据库迁移，以及解决可能遇到的字符集和编码问题。

## 配置数据库连接

首先，确保您已经在cPanel中创建了数据库和数据库用户，并且已经在`.env`文件中配置了正确的数据库连接信息。

### 验证数据库连接

在执行迁移之前，先验证数据库连接是否正常：

```bash
# 激活虚拟环境
source ~/virtualenv/lipeaks_backend/3.12/bin/activate

# 切换到项目目录
cd ~/lipeaks_backend

# 使用Django shell测试数据库连接
python manage.py shell -c "from django.db import connection; cursor = connection.cursor(); print('数据库连接成功！')"
```

如果连接成功，您将看到"数据库连接成功！"的消息。如果连接失败，请检查数据库配置和凭据。

## 解决字符集和编码问题

MySQL数据库默认可能不使用UTF-8编码，这会导致中文等非ASCII字符存储和显示问题。以下是解决方法：

### 1. 创建数据库字符集修复脚本

创建一个Python脚本来修复数据库和表的字符集：

```bash
# 创建脚本文件
cat > ~/lipeaks_backend/fix_charset.py << 'EOL'
#!/usr/bin/env python
import os
import pymysql
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 获取数据库连接参数
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
DB_PORT = int(os.getenv('DB_PORT', '3306'))

def fix_charset():
    """修复数据库和表的字符集为utf8mb4"""
    try:
        # 连接到MySQL服务器（不指定数据库）
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        
        with connection.cursor() as cursor:
            print(f"修改数据库 {DB_NAME} 的字符集...")
            cursor.execute(f"ALTER DATABASE `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        
        # 重新连接，指定数据库
        connection.close()
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT
        )
        
        with connection.cursor() as cursor:
            # 查询所有表
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            
            # 对每个表设置字符集
            for table in tables:
                table_name = table[0]
                print(f"修改表 {table_name} 的字符集...")
                cursor.execute(f"ALTER TABLE `{table_name}` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        
        connection.commit()
        print("所有表的字符集已成功修改为utf8mb4_unicode_ci")
        
    except Exception as e:
        print(f"错误: {e}")
    finally:
        if 'connection' in locals() and connection:
            connection.close()

if __name__ == "__main__":
    fix_charset()
EOL

# 设置执行权限
chmod +x ~/lipeaks_backend/fix_charset.py
```

### 2. 执行字符集修复脚本

```bash
# 激活虚拟环境
source ~/virtualenv/lipeaks_backend/3.12/bin/activate

# 切换到项目目录
cd ~/lipeaks_backend

# 执行修复脚本
python fix_charset.py
```

## 执行数据库迁移

现在，您可以执行Django的数据库迁移：

```bash
# 检查迁移状态
python manage.py showmigrations

# 执行所有迁移
python manage.py migrate
```

### 处理迁移错误

如果遇到迁移错误，以下是一些常见问题的解决方法：

#### 1. 表已存在错误

如果遇到"表已存在"错误，可以尝试：

```bash
# 标记特定应用的迁移为已应用（不实际执行）
python manage.py migrate app_name --fake

# 或标记所有迁移为已应用
python manage.py migrate --fake
```

#### 2. 字段类型不兼容错误

如果遇到字段类型不兼容的错误，可能需要手动修改数据库架构：

```bash
# 使用MySQL客户端连接数据库
mysql -u username -p

# 在MySQL中执行必要的ALTER TABLE语句
# 例如：ALTER TABLE table_name MODIFY COLUMN column_name VARCHAR(255);
```

#### 3. 外键约束错误

如果遇到外键约束错误，可以尝试：

```bash
# 临时禁用外键检查
python manage.py shell -c "from django.db import connection; cursor = connection.cursor(); cursor.execute('SET FOREIGN_KEY_CHECKS=0;')"

# 执行迁移
python manage.py migrate

# 重新启用外键检查
python manage.py shell -c "from django.db import connection; cursor = connection.cursor(); cursor.execute('SET FOREIGN_KEY_CHECKS=1;')"
```

## 创建超级用户

执行迁移后，创建一个超级用户以便访问Django管理界面：

```bash
# 创建超级用户
python manage.py createsuperuser
```

按照提示输入用户名、电子邮件和密码。

## 加载初始数据（如果需要）

如果您的项目需要初始数据，可以使用Django的fixtures功能：

```bash
# 加载初始数据
python manage.py loaddata fixtures/initial_data.json
```

## 创建数据库备份脚本

为了定期备份数据库，创建一个备份脚本：

```bash
# 创建备份脚本
cat > ~/backup_db.sh << 'EOL'
#!/bin/bash

# 加载环境变量
source ~/lipeaks_backend/.env

# 设置备份目录
BACKUP_DIR=~/backups
mkdir -p $BACKUP_DIR

# 设置备份文件名（使用日期）
BACKUP_FILE="$BACKUP_DIR/db_backup_$(date +%Y%m%d_%H%M%S).sql"

# 执行备份
mysqldump -h $DB_HOST -u $DB_USER -p$DB_PASSWORD $DB_NAME > $BACKUP_FILE

# 压缩备份文件
gzip $BACKUP_FILE

# 删除30天前的备份
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +30 -delete

echo "数据库备份完成：${BACKUP_FILE}.gz"
EOL

# 设置执行权限
chmod +x ~/backup_db.sh
```

### 设置定期备份（如果cPanel支持cron）

```bash
# 在cPanel中设置cron作业，每天凌晨2点执行备份
(crontab -l 2>/dev/null; echo "0 2 * * * ~/backup_db.sh >> ~/backup.log 2>&1") | crontab -
```

或者，您可以在cPanel界面中设置cron作业：

1. 在cPanel主界面，找到并点击**"Cron Jobs"**或**"定时任务"**
2. 选择适当的执行频率（例如每天）
3. 在命令字段中输入 `~/backup_db.sh >> ~/backup.log 2>&1`
4. 点击**"添加新的Cron作业"**按钮

## 监控数据库性能

为了监控数据库性能，您可以创建一个简单的脚本：

```bash
# 创建监控脚本
cat > ~/monitor_db.py << 'EOL'
#!/usr/bin/env python
import os
import pymysql
import time
from dotenv import load_dotenv

# 加载环境变量
load_dotenv(os.path.join(os.path.expanduser('~'), 'lipeaks_backend', '.env'))

# 获取数据库连接参数
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
DB_PORT = int(os.getenv('DB_PORT', '3306'))

def check_db_status():
    """检查数据库状态和性能"""
    try:
        # 记录开始时间
        start_time = time.time()
        
        # 连接到数据库
        connection = pymysql.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            port=DB_PORT
        )
        
        # 计算连接时间
        connect_time = time.time() - start_time
        
        with connection.cursor() as cursor:
            # 测试简单查询
            query_start = time.time()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            query_time = time.time() - query_start
            
            # 获取数据库状态
            cursor.execute("SHOW STATUS")
            status = dict(cursor.fetchall())
            
            # 获取表信息
            cursor.execute("SELECT TABLE_NAME, TABLE_ROWS, DATA_LENGTH, INDEX_LENGTH FROM information_schema.TABLES WHERE TABLE_SCHEMA = %s", (DB_NAME,))
            tables = cursor.fetchall()
        
        print(f"数据库连接时间: {connect_time:.4f}秒")
        print(f"查询响应时间: {query_time:.4f}秒")
        print(f"活跃连接数: {status.get('Threads_connected', 'N/A')}")
        print(f"慢查询数: {status.get('Slow_queries', 'N/A')}")
        print("\n表信息:")
        for table in tables:
            name, rows, data_size, index_size = table
            print(f"  {name}: {rows or 0}行, 数据大小: {data_size/1024/1024:.2f}MB, 索引大小: {index_size/1024/1024:.2f}MB")
        
    except Exception as e:
        print(f"错误: {e}")
    finally:
        if 'connection' in locals() and connection:
            connection.close()

if __name__ == "__main__":
    check_db_status()
EOL

# 设置执行权限
chmod +x ~/monitor_db.py
```

## 下一步

完成数据库配置与迁移后，您可以继续[静态文件与媒体文件配置](06_static_media_files.md)。 