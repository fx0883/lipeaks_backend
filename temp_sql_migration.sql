-- ====================================================================
-- 多租户积分系统数据库迁移脚本
-- 创建时间: 2025-09-25
-- 说明: 手动执行此脚本来同步数据库，支持现有系统零修改升级
-- ====================================================================

-- 开始事务
START TRANSACTION;

-- ====================================================================
-- 1. 创建用户等级配置表
-- ====================================================================
CREATE TABLE IF NOT EXISTS `user_level` (
    `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `level_name` varchar(50) NOT NULL COMMENT '等级名称',
    `level_code` varchar(20) NOT NULL UNIQUE COMMENT '等级代码',
    `level_order` int UNSIGNED NOT NULL UNIQUE COMMENT '等级序号',
    `min_points` int UNSIGNED NOT NULL DEFAULT 0 COMMENT '最低积分要求',
    `max_points` int UNSIGNED NULL COMMENT '最高积分上限',
    `permissions` JSON NOT NULL DEFAULT ('{}') COMMENT '权限配置',
    `quota_config` JSON NOT NULL DEFAULT ('{}') COMMENT '配额配置',
    `level_color` varchar(7) NOT NULL DEFAULT '#999999' COMMENT '等级颜色',
    `level_icon` varchar(100) NOT NULL DEFAULT '' COMMENT '等级图标',
    `level_description` longtext NOT NULL DEFAULT '' COMMENT '等级描述',
    `is_active` bool NOT NULL DEFAULT true COMMENT '是否启用',
    `is_default` bool NOT NULL DEFAULT false COMMENT '是否默认等级',
    `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
    `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '更新时间',
    
    CONSTRAINT `valid_min_points` CHECK (`min_points` >= 0),
    CONSTRAINT `valid_max_points` CHECK (`max_points` IS NULL OR `max_points` > `min_points`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户等级配置表';

-- 创建索引
CREATE INDEX `idx_user_level_active_order` ON `user_level` (`is_active`, `level_order`);
CREATE INDEX `idx_user_level_min_points` ON `user_level` (`min_points`);

-- ====================================================================
-- 2. 创建用户标签定义表
-- ====================================================================
CREATE TABLE IF NOT EXISTS `user_type_tag` (
    `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `tag_name` varchar(50) NOT NULL COMMENT '标签名称',
    `tag_code` varchar(20) NOT NULL UNIQUE COMMENT '标签代码',
    `tag_type` varchar(20) NOT NULL COMMENT '标签类型',
    `tag_color` varchar(7) NOT NULL DEFAULT '#007bff' COMMENT '标签颜色',
    `tag_icon` varchar(100) NOT NULL DEFAULT '' COMMENT '标签图标',
    `tag_description` longtext NOT NULL DEFAULT '' COMMENT '标签描述',
    `permission_modifiers` JSON NOT NULL DEFAULT ('{}') COMMENT '权限修改器',
    `quota_modifiers` JSON NOT NULL DEFAULT ('{}') COMMENT '配额修改器',
    `price_config` JSON NOT NULL DEFAULT ('{}') COMMENT '价格配置',
    `default_duration_days` int UNSIGNED NULL COMMENT '默认有效期天数',
    `max_duration_days` int UNSIGNED NULL COMMENT '最大有效期天数',
    `tag_level` int UNSIGNED NOT NULL DEFAULT 1 COMMENT '标签等级',
    `is_active` bool NOT NULL DEFAULT true COMMENT '是否启用',
    `is_assignable` bool NOT NULL DEFAULT true COMMENT '是否可分配',
    `requires_payment` bool NOT NULL DEFAULT false COMMENT '是否需要付费',
    `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
    `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户标签定义表';

-- 创建索引
CREATE INDEX `idx_user_type_tag_type_active` ON `user_type_tag` (`tag_type`, `is_active`);
CREATE INDEX `idx_user_type_tag_assignable` ON `user_type_tag` (`is_active`, `is_assignable`);

-- ====================================================================
-- 3. 创建租户用户档案表
-- ====================================================================
CREATE TABLE IF NOT EXISTS `tenant_user_profile` (
    `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `member_id` bigint NOT NULL COMMENT '关联成员ID',
    `tenant_id` bigint NOT NULL COMMENT '关联租户ID',
    `current_level_id` bigint NULL COMMENT '当前等级ID',
    
    -- 积分信息
    `total_points` int UNSIGNED NOT NULL DEFAULT 0 COMMENT '总积分',
    `available_points` int UNSIGNED NOT NULL DEFAULT 0 COMMENT '可用积分',
    `level_updated_at` datetime(6) NULL COMMENT '等级更新时间',
    
    -- 统计信息
    `points_earned_total` int UNSIGNED NOT NULL DEFAULT 0 COMMENT '历史总获得积分',
    `points_spent_total` int UNSIGNED NOT NULL DEFAULT 0 COMMENT '历史总消费积分',
    `points_expired_total` int UNSIGNED NOT NULL DEFAULT 0 COMMENT '历史总过期积分',
    
    -- 活跃度信息
    `last_points_update` datetime(6) NULL COMMENT '最后积分变动时间',
    `last_level_check` datetime(6) NULL COMMENT '最后等级检查时间',
    `consecutive_login_days` int UNSIGNED NOT NULL DEFAULT 0 COMMENT '连续登录天数',
    `last_login_date` date NULL COMMENT '最后登录日期',
    
    -- 配置信息
    `points_multiplier` decimal(3, 2) NOT NULL DEFAULT 1.00 COMMENT '积分倍数',
    `is_points_enabled` bool NOT NULL DEFAULT true COMMENT '是否启用积分功能',
    
    -- 审计字段
    `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
    `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '更新时间',
    
    CONSTRAINT `unique_member_tenant` UNIQUE (`member_id`, `tenant_id`),
    CONSTRAINT `valid_points` CHECK (`total_points` >= 0 AND `available_points` >= 0),
    CONSTRAINT `available_points_check` CHECK (`available_points` <= `total_points`),
    
    FOREIGN KEY (`member_id`) REFERENCES `users_member` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`tenant_id`) REFERENCES `tenants_tenant` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`current_level_id`) REFERENCES `user_level` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='租户用户档案表';

-- 创建索引
CREATE INDEX `idx_tenant_user_profile_member` ON `tenant_user_profile` (`member_id`);
CREATE INDEX `idx_tenant_user_profile_tenant` ON `tenant_user_profile` (`tenant_id`);
CREATE INDEX `idx_tenant_user_profile_points` ON `tenant_user_profile` (`tenant_id`, `total_points`);
CREATE INDEX `idx_tenant_user_profile_level` ON `tenant_user_profile` (`current_level_id`);
CREATE INDEX `idx_tenant_user_profile_active` ON `tenant_user_profile` (`tenant_id`, `last_points_update`);

-- ====================================================================
-- 4. 创建租户用户积分记录表
-- ====================================================================
CREATE TABLE IF NOT EXISTS `tenant_user_points` (
    `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `tenant_user_profile_id` bigint NOT NULL COMMENT '租户用户档案ID',
    `tenant_id` bigint NOT NULL COMMENT '租户ID(冗余字段)',
    `member_id` bigint NOT NULL COMMENT '成员ID(冗余字段)',
    
    -- 积分类型分类
    `point_type` varchar(10) NOT NULL COMMENT '积分类型(earn/spend/expire/adjust)',
    `category` varchar(20) NOT NULL COMMENT '业务分类',
    `subcategory` varchar(50) NOT NULL DEFAULT '' COMMENT '子分类',
    
    -- 积分数值
    `points` int NOT NULL COMMENT '积分变动数量(正数为获得，负数为消费)',
    `balance_before` int UNSIGNED NOT NULL COMMENT '操作前积分余额',
    `balance_after` int UNSIGNED NOT NULL COMMENT '操作后积分余额',
    
    -- 租户特定信息
    `tenant_multiplier` decimal(3, 2) NOT NULL DEFAULT 1.00 COMMENT '租户积分倍数',
    `original_points` int UNSIGNED NULL COMMENT '倍数调整前的原始积分',
    
    -- 关联信息
    `source_type` varchar(20) NOT NULL DEFAULT 'system' COMMENT '来源类型',
    `source_id` bigint UNSIGNED NULL COMMENT '关联的源记录ID',
    `source_description` longtext NOT NULL DEFAULT '' COMMENT '来源描述',
    
    -- 积分生命周期
    `earned_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '积分获得时间',
    `expires_at` datetime(6) NULL COMMENT '积分过期时间',
    `expired_at` datetime(6) NULL COMMENT '实际过期时间',
    
    -- 操作信息
    `operation_reason` longtext NOT NULL DEFAULT '' COMMENT '操作原因说明',
    `operator_id` bigint UNSIGNED NULL COMMENT '操作人员ID',
    `batch_id` varchar(100) NOT NULL DEFAULT '' COMMENT '批量操作标识',
    
    -- 状态管理
    `status` varchar(20) NOT NULL DEFAULT 'active' COMMENT '状态',
    `is_manual` bool NOT NULL DEFAULT false COMMENT '是否手动调整',
    
    -- 审计字段
    `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
    `created_by_id` bigint UNSIGNED NULL COMMENT '创建人ID',
    
    CONSTRAINT `points_not_zero` CHECK (`points` > 0 OR `points` < 0),
    CONSTRAINT `valid_balance` CHECK (`balance_after` = `balance_before` + `points`),
    CONSTRAINT `valid_balance_positive` CHECK (`balance_after` >= 0),
    CONSTRAINT `valid_tenant_multiplier` CHECK (`tenant_multiplier` > 0),
    
    FOREIGN KEY (`tenant_user_profile_id`) REFERENCES `tenant_user_profile` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`tenant_id`) REFERENCES `tenants_tenant` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`member_id`) REFERENCES `users_member` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='租户用户积分记录表';

-- 创建索引
CREATE INDEX `idx_tenant_user_points_profile` ON `tenant_user_points` (`tenant_user_profile_id`, `created_at`);
CREATE INDEX `idx_tenant_user_points_tenant_member` ON `tenant_user_points` (`tenant_id`, `member_id`, `created_at`);
CREATE INDEX `idx_tenant_user_points_type` ON `tenant_user_points` (`tenant_id`, `point_type`, `category`);
CREATE INDEX `idx_tenant_user_points_expires` ON `tenant_user_points` (`tenant_id`, `expires_at`) 
    WHERE `expires_at` IS NOT NULL AND `status` = 'active';
CREATE INDEX `idx_tenant_user_points_source` ON `tenant_user_points` (`tenant_id`, `source_type`, `source_id`) 
    WHERE `source_id` IS NOT NULL;

-- ====================================================================
-- 5. 创建租户用户标签关联表
-- ====================================================================
CREATE TABLE IF NOT EXISTS `tenant_user_type_tag` (
    `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `tenant_user_profile_id` bigint NOT NULL COMMENT '租户用户档案ID',
    `tag_id` bigint NOT NULL COMMENT '用户标签ID',
    `tenant_id` bigint NOT NULL COMMENT '租户ID(冗余字段)',
    `member_id` bigint NOT NULL COMMENT '成员ID(冗余字段)',
    
    -- 授予信息
    `granted_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '授予时间',
    `granted_by_id` bigint UNSIGNED NULL COMMENT '授予人ID',
    `grant_reason` longtext NOT NULL DEFAULT '' COMMENT '授予原因',
    `grant_method` varchar(20) NOT NULL COMMENT '授予方式',
    
    -- VIP期限管理
    `expires_at` datetime(6) NULL COMMENT '过期时间',
    `original_duration_days` int UNSIGNED NULL COMMENT '原始有效期天数',
    `extended_days` int UNSIGNED NOT NULL DEFAULT 0 COMMENT '延期天数',
    `auto_renewal` bool NOT NULL DEFAULT false COMMENT '是否自动续期',
    `renewal_count` int UNSIGNED NOT NULL DEFAULT 0 COMMENT '续期次数',
    
    -- 期限计算辅助字段
    `grace_period_days` int UNSIGNED NOT NULL DEFAULT 0 COMMENT '宽限期天数',
    `reminder_sent_at` datetime(6) NULL COMMENT '过期提醒发送时间',
    `renewal_reminder_sent` bool NOT NULL DEFAULT false COMMENT '是否已发送续期提醒',
    
    -- 使用统计
    `last_used_at` datetime(6) NULL COMMENT '最后使用时间',
    `usage_count` int UNSIGNED NOT NULL DEFAULT 0 COMMENT '使用次数',
    `benefits_used` JSON NOT NULL DEFAULT ('{}') COMMENT '已使用的福利记录',
    
    -- 支付信息
    `payment_id` bigint UNSIGNED NULL COMMENT '关联的支付记录ID',
    `payment_amount` decimal(10, 2) NULL COMMENT '支付金额',
    `payment_currency` varchar(3) NOT NULL DEFAULT 'CNY' COMMENT '支付货币',
    
    -- 状态管理
    `is_active` bool NOT NULL DEFAULT true COMMENT '是否有效',
    `status` varchar(20) NOT NULL DEFAULT 'active' COMMENT '状态',
    
    -- 备注信息
    `notes` longtext NOT NULL DEFAULT '' COMMENT '备注信息',
    `metadata` JSON NOT NULL DEFAULT ('{}') COMMENT '扩展元数据',
    
    -- 审计字段
    `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
    `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '更新时间',
    
    CONSTRAINT `unique_tenant_member_tag` UNIQUE (`tenant_id`, `member_id`, `tag_id`),
    CONSTRAINT `valid_expiry` CHECK (`expires_at` IS NULL OR `expires_at` > `granted_at`),
    CONSTRAINT `valid_duration` CHECK (`original_duration_days` IS NULL OR `original_duration_days` > 0),
    CONSTRAINT `valid_payment_amount` CHECK (`payment_amount` IS NULL OR `payment_amount` >= 0),
    
    FOREIGN KEY (`tenant_user_profile_id`) REFERENCES `tenant_user_profile` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`tag_id`) REFERENCES `user_type_tag` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`tenant_id`) REFERENCES `tenants_tenant` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`member_id`) REFERENCES `users_member` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='租户用户标签关联表';

-- 创建索引
CREATE INDEX `idx_tenant_user_type_tag_profile` ON `tenant_user_type_tag` (`tenant_user_profile_id`, `is_active`);
CREATE INDEX `idx_tenant_user_type_tag_tenant_member` ON `tenant_user_type_tag` (`tenant_id`, `member_id`, `is_active`);
CREATE INDEX `idx_tenant_user_type_tag_expires` ON `tenant_user_type_tag` (`tenant_id`, `expires_at`) 
    WHERE `expires_at` IS NOT NULL AND `is_active` = true;
CREATE INDEX `idx_tenant_user_type_tag_payment` ON `tenant_user_type_tag` (`payment_id`) 
    WHERE `payment_id` IS NOT NULL;
CREATE INDEX `idx_tenant_user_type_tag_renewal` ON `tenant_user_type_tag` (`tenant_id`, `auto_renewal`, `expires_at`) 
    WHERE `auto_renewal` = true AND `is_active` = true;

-- ====================================================================
-- 6. 创建许可证分配关联表
-- ====================================================================
CREATE TABLE IF NOT EXISTS `licenses_license_assignment` (
    `id` bigint AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `member_id` bigint NOT NULL COMMENT '分配成员ID',
    `license_id` bigint NOT NULL COMMENT '分配许可证ID',
    `tenant_id` bigint NOT NULL COMMENT '关联租户ID',
    
    -- 分配配置
    `assignment_type` varchar(20) NOT NULL DEFAULT 'direct' COMMENT '分配类型',
    `assignment_reason` longtext NOT NULL DEFAULT '' COMMENT '分配原因',
    `priority` varchar(10) NOT NULL DEFAULT 'normal' COMMENT '优先级',
    
    -- 权限级别设置
    `can_activate` bool NOT NULL DEFAULT true COMMENT '允许激活',
    `can_deactivate` bool NOT NULL DEFAULT false COMMENT '允许停用',
    `can_share` bool NOT NULL DEFAULT false COMMENT '允许共享',
    `max_devices_per_user` int UNSIGNED NOT NULL DEFAULT 1 COMMENT '用户最大设备数',
    
    -- 时间控制
    `assigned_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '分配时间',
    `activated_at` datetime(6) NULL COMMENT '激活时间',
    `expires_at` datetime(6) NULL COMMENT '分配过期时间',
    `last_used_at` datetime(6) NULL COMMENT '最后使用时间',
    
    -- 状态管理
    `status` varchar(20) NOT NULL DEFAULT 'active' COMMENT '分配状态',
    `is_primary` bool NOT NULL DEFAULT false COMMENT '是否主要分配',
    
    -- 使用统计
    `usage_count` int UNSIGNED NOT NULL DEFAULT 0 COMMENT '使用次数',
    `last_heartbeat` datetime(6) NULL COMMENT '最后心跳时间',
    
    -- 操作审计
    `assigned_by_id` bigint NULL COMMENT '分配操作员ID',
    `revoked_by_id` bigint NULL COMMENT '撤销操作员ID',
    `revoked_at` datetime(6) NULL COMMENT '撤销时间',
    `revoke_reason` longtext NOT NULL DEFAULT '' COMMENT '撤销原因',
    
    -- 扩展配置
    `assignment_metadata` JSON NOT NULL DEFAULT ('{}') COMMENT '分配元数据',
    
    -- 审计字段
    `created_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) COMMENT '创建时间',
    `updated_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6) COMMENT '更新时间',
    
    CONSTRAINT `unique_member_license_assignment` UNIQUE (`member_id`, `license_id`),
    CONSTRAINT `valid_max_devices` CHECK (`max_devices_per_user` >= 1),
    CONSTRAINT `valid_usage_count` CHECK (`usage_count` >= 0),
    CONSTRAINT `valid_assignment_expiry` CHECK (`expires_at` IS NULL OR `expires_at` > `assigned_at`),
    
    FOREIGN KEY (`member_id`) REFERENCES `users_member` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`license_id`) REFERENCES `licenses_license` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`tenant_id`) REFERENCES `tenants_tenant` (`id`) ON DELETE CASCADE,
    FOREIGN KEY (`assigned_by_id`) REFERENCES `users_user` (`id`) ON DELETE SET NULL,
    FOREIGN KEY (`revoked_by_id`) REFERENCES `users_user` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='许可证分配关联表';

-- 创建索引
CREATE INDEX `idx_license_assignment_member_status` ON `licenses_license_assignment` (`member_id`, `status`);
CREATE INDEX `idx_license_assignment_license_status` ON `licenses_license_assignment` (`license_id`, `status`);
CREATE INDEX `idx_license_assignment_tenant_status` ON `licenses_license_assignment` (`tenant_id`, `status`);
CREATE INDEX `idx_license_assignment_tenant_member` ON `licenses_license_assignment` (`tenant_id`, `member_id`, `status`);
CREATE INDEX `idx_license_assignment_assigned_at` ON `licenses_license_assignment` (`assigned_at`);
CREATE INDEX `idx_license_assignment_expires_at` ON `licenses_license_assignment` (`expires_at`) 
    WHERE `expires_at` IS NOT NULL;
CREATE INDEX `idx_license_assignment_primary` ON `licenses_license_assignment` (`is_primary`, `license_id`);
CREATE INDEX `idx_license_assignment_last_used` ON `licenses_license_assignment` (`last_used_at`) 
    WHERE `last_used_at` IS NOT NULL;

-- ====================================================================
-- 7. 插入基础数据
-- ====================================================================

-- 插入默认用户等级
INSERT IGNORE INTO `user_level` (`level_name`, `level_code`, `level_order`, `min_points`, `max_points`, `level_color`, `is_active`, `is_default`) VALUES
('新手', 'BRONZE', 1, 0, 999, '#CD7F32', true, true),
('铜牌', 'SILVER', 2, 1000, 4999, '#C0C0C0', true, false),
('银牌', 'GOLD', 3, 5000, 19999, '#FFD700', true, false),
('金牌', 'PLATINUM', 4, 20000, 49999, '#E5E4E2', true, false),
('钻石', 'DIAMOND', 5, 50000, NULL, '#B9F2FF', true, false);

-- 插入默认用户标签
INSERT IGNORE INTO `user_type_tag` (`tag_name`, `tag_code`, `tag_type`, `tag_color`, `requires_payment`, `default_duration_days`, `is_active`) VALUES
('VIP用户', 'VIP', 'vip', '#FF6B6B', true, 30, true),
('超级VIP', 'SUPER_VIP', 'vip', '#FF4757', true, 365, true),
('企业用户', 'ENTERPRISE', 'enterprise', '#5352ED', true, 365, true),
('教育用户', 'EDUCATION', 'education', '#2ED573', false, 180, true),
('开发者', 'DEVELOPER', 'developer', '#FFA726', false, 90, true);

-- 提交事务
COMMIT;

-- ====================================================================
-- 执行完成提示
-- ====================================================================
SELECT '多租户积分系统数据库迁移完成！' as message,
       '已创建6个核心表和基础数据' as details,
       NOW() as completed_at;

-- 验证表创建
SELECT 
    TABLE_NAME as '已创建的表',
    TABLE_COMMENT as '表描述'
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA = DATABASE() 
AND TABLE_NAME IN (
    'user_level', 
    'user_type_tag', 
    'tenant_user_profile', 
    'tenant_user_points', 
    'tenant_user_type_tag', 
    'licenses_license_assignment'
)
ORDER BY TABLE_NAME;
