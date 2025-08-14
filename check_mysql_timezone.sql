-- 检查MySQL的时区设置
SELECT @@global.time_zone AS 'Global Time Zone', 
       @@session.time_zone AS 'Session Time Zone',
       NOW() AS 'Current Server Time';

-- 检查时区表是否已安装
SELECT COUNT(*) AS 'Time Zone Tables Count'
FROM information_schema.tables 
WHERE table_name LIKE 'time_zone%' 
AND table_schema = 'mysql';

-- 检查时区转换功能是否正常
SELECT CONVERT_TZ('2025-07-03 10:00:00', 'UTC', 'Asia/Shanghai') AS 'UTC to Asia/Shanghai'; 