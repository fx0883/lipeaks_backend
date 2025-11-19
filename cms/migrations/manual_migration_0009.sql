-- Manual migration for adding member field to Comment and OperationLog
-- Execute this SQL in your MySQL database

-- Add member field to cms_comment table
ALTER TABLE cms_comment 
ADD COLUMN member_id INT NULL,
ADD INDEX cms_comment_member__139f28_idx (member_id),
ADD INDEX cms_comment_tenant__39f0ee_idx (tenant_id, member_id),
ADD CONSTRAINT cms_comment_member_fk 
  FOREIGN KEY (member_id) REFERENCES member(id) ON DELETE CASCADE;

-- Modify user field to allow NULL
ALTER TABLE cms_comment 
MODIFY COLUMN user_id INT NULL;

-- Add member field to cms_operation_log table
ALTER TABLE cms_operation_log 
ADD COLUMN member_id INT NULL,
ADD INDEX cms_operati_member__fc506b_idx (member_id),
ADD INDEX cms_operati_tenant__ee93cb_idx (tenant_id, member_id),
ADD CONSTRAINT cms_operation_log_member_fk 
  FOREIGN KEY (member_id) REFERENCES member(id) ON DELETE CASCADE;

-- Modify user field to allow NULL
ALTER TABLE cms_operation_log 
MODIFY COLUMN user_id INT NULL;

-- Add check constraints (MySQL 8.0.16+)
-- For cms_comment: ensure one of user_id, member_id, or guest_name is not null
ALTER TABLE cms_comment
ADD CONSTRAINT comment_one_author_type_required 
  CHECK (
    (user_id IS NOT NULL AND member_id IS NULL AND guest_name IS NULL) OR
    (user_id IS NULL AND member_id IS NOT NULL AND guest_name IS NULL) OR
    (user_id IS NULL AND member_id IS NULL AND guest_name IS NOT NULL)
  );

-- For cms_operation_log: ensure one of user_id or member_id is not null
ALTER TABLE cms_operation_log
ADD CONSTRAINT operation_log_one_operator_required 
  CHECK (
    (user_id IS NOT NULL AND member_id IS NULL) OR
    (user_id IS NULL AND member_id IS NOT NULL)
  );
