-- SQL script to add categories to the CMS system
-- These categories are for tenant_id = 1

-- First, create the parent category
INSERT INTO cms_category (name, slug, description, parent_id, cover_image, created_at, updated_at, sort_order, tenant_id, is_active, seo_title, seo_description)
VALUES 
('Product', 'product', 'Main product category', NULL, NULL, NOW(), NOW(), 0, 1, TRUE, 'Products', 'All products related information');

-- Get the ID of the parent category for reference in child categories
SET @parent_category_id = LAST_INSERT_ID();

-- Then create the child categories
INSERT INTO cms_category (name, slug, description, parent_id, cover_image, created_at, updated_at, sort_order, tenant_id, is_active, seo_title, seo_description)
VALUES 
('ImageDiff', 'imagediff', 'Image difference detection product', @parent_category_id, NULL, NOW(), NOW(), 1, 1, TRUE, 'ImageDiff', 'Image difference detection tools and information'),
('Free tools', 'free-tools', 'Free tools available for users', @parent_category_id, NULL, NOW(), NOW(), 2, 1, TRUE, 'Free Tools', 'Various free tools for users'),
('Affiliate', 'affiliate', 'Affiliate program information', @parent_category_id, NULL, NOW(), NOW(), 3, 1, TRUE, 'Affiliate Program', 'Information about our affiliate programs');

-- Add independent categories (from the image)
INSERT INTO cms_category (name, slug, description, parent_id, cover_image, created_at, updated_at, sort_order, tenant_id, is_active, seo_title, seo_description)
VALUES 
('Blog', 'blog', 'Blog articles and news', NULL, NULL, NOW(), NOW(), 1, 1, TRUE, 'Blog', 'Latest blog posts and news'),
('Case Studies', 'case-studies', 'Customer case studies and success stories', NULL, NULL, NOW(), NOW(), 2, 1, TRUE, 'Case Studies', 'Customer success stories and case studies'),
('Changelog', 'changelog', 'Product updates and version history', NULL, NULL, NOW(), NOW(), 3, 1, TRUE, 'Changelog', 'Product updates and version history information'); 