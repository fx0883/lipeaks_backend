-- 手动迁移SQL脚本：将GenericForeignKey替换为双外键
-- 执行前请备份数据库！

-- 步骤1: 添加新字段user_id和member_id
ALTER TABLE cms_article 
ADD COLUMN user_id INT NULL,
ADD COLUMN member_id INT NULL;

-- 步骤2: 添加外键约束
ALTER TABLE cms_article
ADD CONSTRAINT cms_article_user_fk 
    FOREIGN KEY (user_id) REFERENCES users_user(id) ON DELETE CASCADE;

ALTER TABLE cms_article
ADD CONSTRAINT cms_article_member_fk 
    FOREIGN KEY (member_id) REFERENCES users_member(id) ON DELETE CASCADE;

-- 步骤3: 迁移数据（从author_content_type_id和author_object_id到user_id或member_id）

-- 迁移User作者
UPDATE cms_article 
SET user_id = author_object_id 
WHERE author_content_type_id = (
    SELECT id FROM django_content_type 
    WHERE app_label='users' AND model='user'
) AND author_object_id IS NOT NULL;

-- 迁移Member作者
UPDATE cms_article 
SET member_id = author_object_id 
WHERE author_content_type_id = (
    SELECT id FROM django_content_type 
    WHERE app_label='users' AND model='member'
) AND author_object_id IS NOT NULL;

-- 步骤4: 验证数据迁移
SELECT 
    COUNT(*) as total_articles,
    SUM(CASE WHEN user_id IS NOT NULL THEN 1 ELSE 0 END) as user_articles,
    SUM(CASE WHEN member_id IS NOT NULL THEN 1 ELSE 0 END) as member_articles,
    SUM(CASE WHEN user_id IS NULL AND member_id IS NULL THEN 1 ELSE 0 END) as no_author
FROM cms_article;

-- 步骤5: 删除旧字段
ALTER TABLE cms_article
DROP FOREIGN KEY cms_article_author_content_type_fk;

ALTER TABLE cms_article
DROP COLUMN author_content_type_id,
DROP COLUMN author_object_id;

-- 步骤6: 添加索引
CREATE INDEX cms_article_user_idx ON cms_article(user_id);
CREATE INDEX cms_article_member_idx ON cms_article(member_id);
CREATE INDEX cms_article_tenant_user_idx ON cms_article(tenant_id, user_id);
CREATE INDEX cms_article_tenant_member_idx ON cms_article(tenant_id, member_id);

-- 步骤7: 添加约束（确保user和member有且仅有一个非空）
-- 注意：MySQL 8.0.16+才支持CHECK约束
ALTER TABLE cms_article
ADD CONSTRAINT article_one_author_required 
CHECK (
    (user_id IS NOT NULL AND member_id IS NULL) OR 
    (user_id IS NULL AND member_id IS NOT NULL)
);

-- 完成！验证结果
SELECT 
    'Migration Completed!' as status,
    COUNT(*) as total_articles,
    SUM(CASE WHEN user_id IS NOT NULL THEN 1 ELSE 0 END) as user_articles,
    SUM(CASE WHEN member_id IS NOT NULL THEN 1 ELSE 0 END) as member_articles
FROM cms_article;

