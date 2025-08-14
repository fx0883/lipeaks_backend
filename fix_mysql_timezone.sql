-- 修复MySQL时区问题的SQL脚本

-- 显示当前时区设置
SELECT @@global.time_zone, @@session.time_zone;

-- 设置全局时区为+08:00（中国标准时间）
SET GLOBAL time_zone = '+08:00';

-- 设置会话时区为+08:00
SET time_zone = '+08:00';

-- 验证设置是否生效
SELECT @@global.time_zone, @@session.time_zone;

-- 注意：此设置在MySQL重启后会恢复为默认值
-- 设置MySQL全局时区为UTC
SET GLOBAL time_zone = 'UTC';

-- 设置当前会话时区为Asia/Shanghai
SET time_zone = 'Asia/Shanghai';

-- 检查时区设置
SELECT @@global.time_zone AS 'Global Time Zone', 
       @@session.time_zone AS 'Session Time Zone',
       NOW() AS 'Current Server Time';

-- 测试时区转换功能
SELECT 
    '2025-07-03 10:00:00' AS 'Original Time',
    CONVERT_TZ('2025-07-03 10:00:00', 'UTC', 'Asia/Shanghai') AS 'UTC to Asia/Shanghai';

-- 验证时区表是否已安装 (结果应该大于0)
SELECT COUNT(*) AS 'Time Zone Tables Count'
FROM information_schema.tables 
WHERE table_name LIKE 'time_zone%' 
AND table_schema = 'mysql';

-- 如果上述查询结果为0，则需要安装时区表
-- 在Linux/Unix系统上，使用以下命令:
-- mysql_tzinfo_to_sql /usr/share/zoneinfo | mysql -u root mysql
--
-- 在Windows系统上，可能需要从MySQL安装目录导入时区SQL文件:
-- source C:\path\to\mysql\share\mysql\timezone_posix.sql 