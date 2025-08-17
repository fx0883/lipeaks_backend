# 维护与更新指南

本文档提供了在cPanel环境中维护和更新Django项目的最佳实践和指南。

## 定期维护任务

### 1. 数据库备份

定期备份数据库是防止数据丢失的关键措施。

#### 自动备份

确保已设置自动备份脚本（如前面文档中的`backup_db.sh`）：

```bash
# 检查备份脚本是否存在
ls -la ~/backup_db.sh

# 如果不存在，创建备份脚本
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

# 设置cron作业
(crontab -l 2>/dev/null; echo "0 2 * * * ~/backup_db.sh >> ~/backup.log 2>&1") | crontab -
```

#### 手动备份

在执行重大更新前，建议手动创建备份：

```bash
# 手动执行备份
~/backup_db.sh
```

#### 验证备份

定期验证备份的有效性：

```bash
# 列出最近的备份
ls -la ~/backups/

# 验证备份文件是否可用
zcat ~/backups/最新备份文件.sql.gz | head -n 20
```

### 2. 日志管理

定期检查和管理日志文件，防止日志文件过大占用磁盘空间。

#### 日志轮转

创建日志轮转脚本：

```bash
# 创建日志轮转脚本
cat > ~/rotate_logs.sh << 'EOL'
#!/bin/bash

# 设置日志目录
LOG_DIR=~/logs

# 轮转日志文件
for LOG_FILE in $LOG_DIR/*.log; do
    if [ -f "$LOG_FILE" ]; then
        # 获取文件大小（字节）
        SIZE=$(stat -c%s "$LOG_FILE")
        
        # 如果文件大于10MB (10485760字节)，进行轮转
        if [ $SIZE -gt 10485760 ]; then
            DATE=$(date +%Y%m%d_%H%M%S)
            mv "$LOG_FILE" "${LOG_FILE}.${DATE}"
            gzip "${LOG_FILE}.${DATE}"
            touch "$LOG_FILE"
            echo "$(date): 轮转日志文件 $LOG_FILE" >> $LOG_DIR/rotate.log
        fi
    fi
done

# 删除30天前的日志
find $LOG_DIR -name "*.gz" -mtime +30 -delete
EOL

# 设置执行权限
chmod +x ~/rotate_logs.sh

# 设置cron作业
(crontab -l 2>/dev/null; echo "0 1 * * * ~/rotate_logs.sh") | crontab -
```

#### 日志分析

定期分析日志文件，查找潜在问题：

```bash
# 创建日志分析脚本
cat > ~/analyze_logs.sh << 'EOL'
#!/bin/bash

# 设置日志目录
LOG_DIR=~/logs
ERROR_LOG=$LOG_DIR/error.log
REPORT_FILE=$LOG_DIR/log_analysis.txt

# 创建报告文件
echo "日志分析报告 - $(date)" > $REPORT_FILE
echo "===============================" >> $REPORT_FILE

# 分析错误日志
if [ -f "$ERROR_LOG" ]; then
    echo -e "\n错误日志分析:" >> $REPORT_FILE
    echo "总错误数: $(grep -c ERROR $ERROR_LOG)" >> $REPORT_FILE
    echo "最近10个错误:" >> $REPORT_FILE
    grep ERROR $ERROR_LOG | tail -10 >> $REPORT_FILE
    
    echo -e "\n最常见的错误类型:" >> $REPORT_FILE
    grep ERROR $ERROR_LOG | awk -F': ' '{print $3}' | sort | uniq -c | sort -nr | head -5 >> $REPORT_FILE
fi

# 分析访问日志（如果存在）
ACCESS_LOG=$LOG_DIR/access.log
if [ -f "$ACCESS_LOG" ]; then
    echo -e "\n访问日志分析:" >> $REPORT_FILE
    echo "总请求数: $(wc -l < $ACCESS_LOG)" >> $REPORT_FILE
    echo "HTTP 500错误数: $(grep -c "HTTP/1\.. 500" $ACCESS_LOG)" >> $REPORT_FILE
    echo "HTTP 404错误数: $(grep -c "HTTP/1\.. 404" $ACCESS_LOG)" >> $REPORT_FILE
    
    echo -e "\n最常访问的URL:" >> $REPORT_FILE
    awk '{print $7}' $ACCESS_LOG | sort | uniq -c | sort -nr | head -10 >> $REPORT_FILE
    
    echo -e "\n访问最多的IP地址:" >> $REPORT_FILE
    awk '{print $1}' $ACCESS_LOG | sort | uniq -c | sort -nr | head -10 >> $REPORT_FILE
fi

echo -e "\n分析完成，报告保存在 $REPORT_FILE"
EOL

# 设置执行权限
chmod +x ~/analyze_logs.sh
```

### 3. 系统健康检查

定期执行系统健康检查，确保应用程序正常运行。

#### 创建健康检查脚本

```bash
# 创建健康检查脚本
cat > ~/system_health_check.sh << 'EOL'
#!/bin/bash

# 设置日志文件
LOG_FILE=~/logs/health_check.log
echo "系统健康检查 - $(date)" >> $LOG_FILE
echo "===============================" >> $LOG_FILE

# 检查磁盘空间
echo -e "\n磁盘空间使用情况:" >> $LOG_FILE
df -h >> $LOG_FILE

# 检查内存使用情况
echo -e "\n内存使用情况:" >> $LOG_FILE
free -m >> $LOG_FILE

# 检查CPU负载
echo -e "\nCPU负载:" >> $LOG_FILE
uptime >> $LOG_FILE

# 检查进程数
echo -e "\n进程数:" >> $LOG_FILE
ps aux | wc -l >> $LOG_FILE

# 检查数据库连接
echo -e "\n数据库连接:" >> $LOG_FILE
source ~/virtualenv/lipeaks_backend/3.12/bin/activate
cd ~/lipeaks_backend
python -c "from django.db import connection; cursor = connection.cursor(); cursor.execute('SELECT COUNT(*) FROM information_schema.processlist'); print(cursor.fetchone()[0])" >> $LOG_FILE 2>&1

# 检查网站可访问性
echo -e "\n网站可访问性:" >> $LOG_FILE
SITE_URL="https://yourdomain.com"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" $SITE_URL)
echo "HTTP状态码: $HTTP_CODE" >> $LOG_FILE

# 检查SSL证书过期时间
echo -e "\nSSL证书信息:" >> $LOG_FILE
echo | openssl s_client -servername yourdomain.com -connect yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates >> $LOG_FILE

echo -e "\n健康检查完成" >> $LOG_FILE
echo "===============================" >> $LOG_FILE
EOL

# 设置执行权限
chmod +x ~/system_health_check.sh

# 设置cron作业
(crontab -l 2>/dev/null; echo "0 7 * * * ~/system_health_check.sh") | crontab -
```

### 4. 文件系统维护

定期清理临时文件和缓存，防止磁盘空间不足。

#### 创建清理脚本

```bash
# 创建清理脚本
cat > ~/clean_filesystem.sh << 'EOL'
#!/bin/bash

# 设置日志文件
LOG_FILE=~/logs/clean_filesystem.log
echo "文件系统清理 - $(date)" >> $LOG_FILE

# 清理Python缓存文件
echo "清理Python缓存文件..." >> $LOG_FILE
find ~/lipeaks_backend -name "*.pyc" -delete
find ~/lipeaks_backend -name "__pycache__" -type d -exec rm -rf {} +
find ~/lipeaks_backend -name "*.pyo" -delete

# 清理会话文件（如果使用文件会话存储）
echo "清理过期会话文件..." >> $LOG_FILE
find ~/lipeaks_backend -path "*/django_sessions/*" -type f -mtime +30 -delete

# 清理临时上传文件
echo "清理临时上传文件..." >> $LOG_FILE
find ~/lipeaks_backend/media/temp -type f -mtime +7 -delete

# 清理日志备份
echo "清理旧日志备份..." >> $LOG_FILE
find ~/logs -name "*.gz" -mtime +60 -delete

echo "文件系统清理完成" >> $LOG_FILE
EOL

# 设置执行权限
chmod +x ~/clean_filesystem.sh

# 设置cron作业
(crontab -l 2>/dev/null; echo "0 3 * * 0 ~/clean_filesystem.sh") | crontab -
```

## 更新流程

### 1. 代码更新

#### 使用Git更新（推荐）

如果您使用Git管理代码，可以按照以下步骤更新：

```bash
# 切换到项目目录
cd ~/lipeaks_backend

# 创建备份分支
git checkout -b backup_$(date +%Y%m%d)

# 切换回主分支
git checkout main

# 拉取最新代码
git pull origin main
```

#### 使用文件上传更新

如果不使用Git，可以通过文件上传更新：

1. 在本地备份当前代码
2. 将新代码打包成ZIP文件
3. 上传到服务器
4. 解压并替换旧文件

### 2. 依赖更新

定期更新依赖项，特别是安全相关的更新：

```bash
# 激活虚拟环境
source ~/virtualenv/lipeaks_backend/3.12/bin/activate

# 备份当前requirements.txt
cp ~/lipeaks_backend/requirements.txt ~/lipeaks_backend/requirements.txt.bak

# 更新依赖
pip install --upgrade -r ~/lipeaks_backend/requirements.txt
```

### 3. 数据库迁移

在代码更新后，执行数据库迁移：

```bash
# 激活虚拟环境
source ~/virtualenv/lipeaks_backend/3.12/bin/activate

# 切换到项目目录
cd ~/lipeaks_backend

# 创建迁移
python manage.py makemigrations

# 应用迁移
python manage.py migrate
```

### 4. 静态文件收集

更新静态文件：

```bash
# 激活虚拟环境
source ~/virtualenv/lipeaks_backend/3.12/bin/activate

# 切换到项目目录
cd ~/lipeaks_backend

# 收集静态文件
python manage.py collectstatic --noinput
```

### 5. 重启应用程序

更新完成后，重启应用程序：

```bash
# 触摸passenger_wsgi.py文件以重启应用程序
touch ~/lipeaks_backend/passenger_wsgi.py
```

## 自动化更新流程

创建一个脚本来自动化整个更新流程：

```bash
# 创建更新脚本
cat > ~/update_app.sh << 'EOL'
#!/bin/bash

# 设置日志文件
LOG_FILE=~/logs/update_app.log
echo "应用程序更新 - $(date)" > $LOG_FILE

# 设置变量
APP_DIR=~/lipeaks_backend
BACKUP_DIR=~/backups/app_backup_$(date +%Y%m%d_%H%M%S)

# 创建应用程序备份
echo "创建应用程序备份..." >> $LOG_FILE
mkdir -p $BACKUP_DIR
cp -r $APP_DIR/* $BACKUP_DIR/

# 创建数据库备份
echo "创建数据库备份..." >> $LOG_FILE
~/backup_db.sh >> $LOG_FILE

# 更新代码（使用Git）
if [ -d "$APP_DIR/.git" ]; then
    echo "使用Git更新代码..." >> $LOG_FILE
    cd $APP_DIR
    git checkout -b backup_$(date +%Y%m%d) >> $LOG_FILE 2>&1
    git checkout main >> $LOG_FILE 2>&1
    git pull origin main >> $LOG_FILE 2>&1
else
    echo "未使用Git，跳过代码更新" >> $LOG_FILE
fi

# 激活虚拟环境
source ~/virtualenv/lipeaks_backend/3.12/bin/activate

# 更新依赖
echo "更新依赖..." >> $LOG_FILE
pip install --upgrade -r $APP_DIR/requirements.txt >> $LOG_FILE 2>&1

# 执行数据库迁移
echo "执行数据库迁移..." >> $LOG_FILE
cd $APP_DIR
python manage.py makemigrations >> $LOG_FILE 2>&1
python manage.py migrate >> $LOG_FILE 2>&1

# 收集静态文件
echo "收集静态文件..." >> $LOG_FILE
python manage.py collectstatic --noinput >> $LOG_FILE 2>&1

# 重启应用程序
echo "重启应用程序..." >> $LOG_FILE
touch $APP_DIR/passenger_wsgi.py

# 验证应用程序
echo "验证应用程序..." >> $LOG_FILE
sleep 5  # 等待应用程序重启
SITE_URL="https://yourdomain.com"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" $SITE_URL)
echo "HTTP状态码: $HTTP_CODE" >> $LOG_FILE

if [ $HTTP_CODE -eq 200 ]; then
    echo "更新成功！" >> $LOG_FILE
else
    echo "更新可能失败，HTTP状态码: $HTTP_CODE" >> $LOG_FILE
    echo "请检查日志文件并手动验证应用程序" >> $LOG_FILE
fi

echo "更新完成 - $(date)" >> $LOG_FILE
EOL

# 设置执行权限
chmod +x ~/update_app.sh
```

## 安全更新

### 1. 定期更新安全相关依赖

创建一个脚本来定期更新安全相关依赖：

```bash
# 创建安全更新脚本
cat > ~/security_updates.sh << 'EOL'
#!/bin/bash

# 设置日志文件
LOG_FILE=~/logs/security_updates.log
echo "安全更新 - $(date)" > $LOG_FILE

# 激活虚拟环境
source ~/virtualenv/lipeaks_backend/3.12/bin/activate

# 检查安全漏洞
echo "检查安全漏洞..." >> $LOG_FILE
pip list --outdated | grep -i "django\|pillow\|requests\|cryptography\|pyjwt" >> $LOG_FILE

# 更新关键安全依赖
echo "更新关键安全依赖..." >> $LOG_FILE
pip install --upgrade django pillow requests cryptography pyjwt >> $LOG_FILE 2>&1

# 重启应用程序
echo "重启应用程序..." >> $LOG_FILE
touch ~/lipeaks_backend/passenger_wsgi.py

echo "安全更新完成 - $(date)" >> $LOG_FILE
EOL

# 设置执行权限
chmod +x ~/security_updates.sh

# 设置cron作业
(crontab -l 2>/dev/null; echo "0 4 1,15 * * ~/security_updates.sh") | crontab -
```

### 2. 定期安全扫描

创建一个脚本来定期进行安全扫描：

```bash
# 创建安全扫描脚本
cat > ~/security_scan.sh << 'EOL'
#!/bin/bash

# 设置日志文件
LOG_FILE=~/logs/security_scan.log
echo "安全扫描 - $(date)" > $LOG_FILE

# 激活虚拟环境
source ~/virtualenv/lipeaks_backend/3.12/bin/activate

# 安装安全扫描工具（如果需要）
pip install safety >> $LOG_FILE 2>&1

# 扫描依赖项安全漏洞
echo "扫描依赖项安全漏洞..." >> $LOG_FILE
safety check -r ~/lipeaks_backend/requirements.txt >> $LOG_FILE 2>&1

# 检查文件权限
echo "检查文件权限..." >> $LOG_FILE
~/security_check.sh >> $LOG_FILE 2>&1

# 检查敏感信息泄露
echo "检查敏感信息泄露..." >> $LOG_FILE
grep -r "password\|secret\|key\|token" --include="*.py" ~/lipeaks_backend/ >> $LOG_FILE 2>&1

echo "安全扫描完成 - $(date)" >> $LOG_FILE
EOL

# 设置执行权限
chmod +x ~/security_scan.sh

# 设置cron作业
(crontab -l 2>/dev/null; echo "0 5 * * 1 ~/security_scan.sh") | crontab -
```

## 性能监控与优化

### 1. 性能监控

创建一个脚本来监控应用程序性能：

```bash
# 创建性能监控脚本
cat > ~/monitor_performance.sh << 'EOL'
#!/bin/bash

# 设置日志文件
LOG_FILE=~/logs/performance_monitor.log
echo "性能监控 - $(date)" > $LOG_FILE

# 监控系统资源
echo "系统资源使用情况:" >> $LOG_FILE
echo "CPU使用率:" >> $LOG_FILE
top -b -n 1 | head -n 5 >> $LOG_FILE
echo "内存使用情况:" >> $LOG_FILE
free -m >> $LOG_FILE
echo "磁盘使用情况:" >> $LOG_FILE
df -h >> $LOG_FILE

# 监控数据库性能
echo "数据库性能:" >> $LOG_FILE
source ~/virtualenv/lipeaks_backend/3.12/bin/activate
cd ~/lipeaks_backend
python ~/lipeaks_backend/monitor_db.py >> $LOG_FILE 2>&1

# 监控网站响应时间
echo "网站响应时间:" >> $LOG_FILE
SITE_URL="https://yourdomain.com"
RESPONSE_TIME=$(curl -s -w "%{time_total}\n" -o /dev/null $SITE_URL)
echo "响应时间: ${RESPONSE_TIME}秒" >> $LOG_FILE

echo "性能监控完成 - $(date)" >> $LOG_FILE
EOL

# 设置执行权限
chmod +x ~/monitor_performance.sh

# 设置cron作业
(crontab -l 2>/dev/null; echo "*/30 * * * * ~/monitor_performance.sh") | crontab -
```

### 2. 定期优化

创建一个脚本来定期优化应用程序：

```bash
# 创建优化脚本
cat > ~/optimize_app.sh << 'EOL'
#!/bin/bash

# 设置日志文件
LOG_FILE=~/logs/optimize_app.log
echo "应用程序优化 - $(date)" > $LOG_FILE

# 优化数据库
echo "优化数据库..." >> $LOG_FILE
source ~/virtualenv/lipeaks_backend/3.12/bin/activate
cd ~/lipeaks_backend
python -c "from django.db import connection; cursor = connection.cursor(); cursor.execute('ANALYZE TABLE auth_user'); cursor.execute('OPTIMIZE TABLE auth_user')" >> $LOG_FILE 2>&1

# 优化静态文件
echo "优化静态文件..." >> $LOG_FILE
python ~/lipeaks_backend/optimize_images.py >> $LOG_FILE 2>&1

# 清理缓存
echo "清理缓存..." >> $LOG_FILE
python manage.py clearcache >> $LOG_FILE 2>&1

echo "应用程序优化完成 - $(date)" >> $LOG_FILE
EOL

# 设置执行权限
chmod +x ~/optimize_app.sh

# 设置cron作业
(crontab -l 2>/dev/null; echo "0 3 * * 0 ~/optimize_app.sh") | crontab -
```

## 灾难恢复计划

### 1. 创建完整备份

创建一个脚本来创建完整备份：

```bash
# 创建完整备份脚本
cat > ~/full_backup.sh << 'EOL'
#!/bin/bash

# 设置变量
BACKUP_DIR=~/full_backups/backup_$(date +%Y%m%d_%H%M%S)
LOG_FILE=~/logs/full_backup.log
APP_DIR=~/lipeaks_backend

# 创建备份目录
mkdir -p $BACKUP_DIR

# 记录开始时间
echo "完整备份开始 - $(date)" > $LOG_FILE

# 备份应用程序文件
echo "备份应用程序文件..." >> $LOG_FILE
cp -r $APP_DIR $BACKUP_DIR/app

# 备份数据库
echo "备份数据库..." >> $LOG_FILE
source $APP_DIR/.env
DB_BACKUP_FILE=$BACKUP_DIR/database.sql
mysqldump -h $DB_HOST -u $DB_USER -p$DB_PASSWORD $DB_NAME > $DB_BACKUP_FILE
gzip $DB_BACKUP_FILE

# 备份虚拟环境
echo "备份虚拟环境..." >> $LOG_FILE
pip freeze > $BACKUP_DIR/requirements_freeze.txt

# 备份配置文件
echo "备份配置文件..." >> $LOG_FILE
cp $APP_DIR/.env $BACKUP_DIR/env_backup
cp ~/public_html/.htaccess $BACKUP_DIR/htaccess_backup

# 备份cron作业
echo "备份cron作业..." >> $LOG_FILE
crontab -l > $BACKUP_DIR/crontab_backup

# 压缩备份
echo "压缩备份..." >> $LOG_FILE
cd ~/full_backups
tar -czf backup_$(date +%Y%m%d_%H%M%S).tar.gz $(basename $BACKUP_DIR)

# 删除30天前的备份
echo "删除旧备份..." >> $LOG_FILE
find ~/full_backups -name "backup_*.tar.gz" -mtime +30 -delete

echo "完整备份完成 - $(date)" >> $LOG_FILE
EOL

# 设置执行权限
chmod +x ~/full_backup.sh

# 设置cron作业
(crontab -l 2>/dev/null; echo "0 1 * * 0 ~/full_backup.sh") | crontab -
```

### 2. 创建恢复脚本

创建一个脚本来恢复备份：

```bash
# 创建恢复脚本
cat > ~/restore_backup.sh << 'EOL'
#!/bin/bash

# 检查参数
if [ -z "$1" ]; then
    echo "使用方法: $0 备份文件路径"
    echo "例如: $0 ~/full_backups/backup_20230101_120000.tar.gz"
    exit 1
fi

BACKUP_FILE=$1
RESTORE_DIR=~/restore_$(date +%Y%m%d_%H%M%S)
LOG_FILE=~/logs/restore.log

# 记录开始时间
echo "开始恢复备份 - $(date)" > $LOG_FILE
echo "备份文件: $BACKUP_FILE" >> $LOG_FILE

# 创建恢复目录
mkdir -p $RESTORE_DIR

# 解压备份
echo "解压备份..." >> $LOG_FILE
tar -xzf $BACKUP_FILE -C $RESTORE_DIR

# 找到备份目录
BACKUP_DIR=$(find $RESTORE_DIR -type d -name "backup_*" | head -1)
if [ -z "$BACKUP_DIR" ]; then
    echo "错误: 无法找到备份目录" >> $LOG_FILE
    exit 1
fi

# 恢复应用程序文件
echo "恢复应用程序文件..." >> $LOG_FILE
cp -r $BACKUP_DIR/app/* ~/lipeaks_backend/

# 恢复数据库
echo "恢复数据库..." >> $LOG_FILE
source ~/lipeaks_backend/.env
gunzip -c $BACKUP_DIR/database.sql.gz | mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD $DB_NAME

# 恢复配置文件
echo "恢复配置文件..." >> $LOG_FILE
cp $BACKUP_DIR/env_backup ~/lipeaks_backend/.env
cp $BACKUP_DIR/htaccess_backup ~/public_html/.htaccess

# 重启应用程序
echo "重启应用程序..." >> $LOG_FILE
touch ~/lipeaks_backend/passenger_wsgi.py

echo "恢复完成 - $(date)" >> $LOG_FILE
EOL

# 设置执行权限
chmod +x ~/restore_backup.sh
```

## 总结

本文档提供了在cPanel环境中维护和更新Django项目的全面指南。通过定期执行这些维护任务，您可以确保应用程序的稳定性、安全性和性能。

关键维护任务包括：
1. 定期数据库备份
2. 日志管理和分析
3. 系统健康检查
4. 文件系统维护
5. 代码和依赖更新
6. 安全扫描和更新
7. 性能监控和优化
8. 灾难恢复计划

建议将这些脚本添加到cron作业中，实现自动化维护。同时，定期检查日志文件，及时发现和解决潜在问题。 