-- CMS分类多语言迁移SQL脚本
-- 执行前请确保已备份数据库！

-- 步骤1: 创建翻译表
CREATE TABLE `cms_category_translation` (
    `id` bigint(20) NOT NULL AUTO_INCREMENT,
    `language_code` varchar(15) NOT NULL,
    `name` varchar(100) NOT NULL,
    `description` longtext,
    `seo_title` varchar(255),
    `seo_description` longtext,
    `master_id` bigint(20) NOT NULL,
    PRIMARY KEY (`id`),
    UNIQUE KEY `cms_category_translat_language_code_master__37d9b6c5_uniq` (`language_code`, `master_id`),
    KEY `cms_category_translation_master_id_2ca0b49d_fk_cms_category_id` (`master_id`),
    KEY `cms_category_translation_language_code_c7ec18e8` (`language_code`),
    CONSTRAINT `cms_category_translation_master_id_2ca0b49d_fk_cms_category_id` 
        FOREIGN KEY (`master_id`) REFERENCES `cms_category` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 步骤2: 将现有分类数据迁移到翻译表（使用简体中文作为默认语言）
INSERT INTO `cms_category_translation` 
    (`language_code`, `name`, `description`, `seo_title`, `seo_description`, `master_id`)
SELECT 
    'zh-hans' as language_code,
    `name`,
    `description`,
    `seo_title`,
    `seo_description`,
    `id`
FROM `cms_category`
WHERE `name` IS NOT NULL;  -- 只迁移有名称的分类

-- 步骤3: 删除原有字段（可选，建议先测试确认数据迁移成功后再执行）
-- 注意：执行此步骤后将无法回退！请确认数据迁移正确后再执行！
-- ALTER TABLE `cms_category` DROP COLUMN `name`;
-- ALTER TABLE `cms_category` DROP COLUMN `description`;
-- ALTER TABLE `cms_category` DROP COLUMN `seo_title`;
-- ALTER TABLE `cms_category` DROP COLUMN `seo_description`;

-- 验证迁移结果的SQL查询
-- 执行下面的查询检查翻译数据是否正确：
SELECT 
    c.id as category_id,
    c.slug,
    t.language_code,
    t.name,
    t.description
FROM cms_category c
LEFT JOIN cms_category_translation t ON c.id = t.master_id
ORDER BY c.id, t.language_code;

