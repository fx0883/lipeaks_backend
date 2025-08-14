-- 修改数据库字符集为utf8mb4
ALTER DATABASE `espresso_multi_tenant_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 修改auth_permission表的字符集
ALTER TABLE `auth_permission` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 特别修改name字段的字符集
ALTER TABLE `auth_permission` MODIFY `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci; 