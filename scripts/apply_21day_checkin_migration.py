"""
Apply 21-day check-in database schema changes
Run this script to add new columns without needing Django migrate
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lipeaks_backend.settings')
import django
django.setup()

from django.db import connection

def apply_changes():
    cursor = connection.cursor()
    
    # Check task_category columns
    cursor.execute("SHOW COLUMNS FROM task_category")
    existing_columns = [col[0] for col in cursor.fetchall()]
    print(f"Existing task_category columns: {existing_columns}")
    
    # Add missing columns to task_category
    changes_made = 0
    
    if 'color' not in existing_columns:
        cursor.execute('ALTER TABLE task_category ADD COLUMN color VARCHAR(20) DEFAULT ""')
        print('Added color column')
        changes_made += 1
        
    if 'goal' not in existing_columns:
        cursor.execute('ALTER TABLE task_category ADD COLUMN goal LONGTEXT')
        print('Added goal column')
        changes_made += 1
        
    if 'tip' not in existing_columns:
        cursor.execute('ALTER TABLE task_category ADD COLUMN tip LONGTEXT')
        print('Added tip column')
        changes_made += 1
        
    if 'quote' not in existing_columns:
        cursor.execute('ALTER TABLE task_category ADD COLUMN quote VARCHAR(200) DEFAULT ""')
        print('Added quote column')
        changes_made += 1
        
    if 'form_type' not in existing_columns:
        cursor.execute('ALTER TABLE task_category ADD COLUMN form_type VARCHAR(20) DEFAULT "text"')
        print('Added form_type column')
        changes_made += 1
        
    if 'sort_order' not in existing_columns:
        cursor.execute('ALTER TABLE task_category ADD COLUMN sort_order INT DEFAULT 0')
        print('Added sort_order column')
        changes_made += 1
    
    print(f"task_category: {changes_made} columns added")
    
    # Check check_record columns
    cursor.execute("SHOW COLUMNS FROM check_record")
    existing_columns = [col[0] for col in cursor.fetchall()]
    print(f"Existing check_record columns: {existing_columns}")
    
    changes_made = 0
    
    if 'theme_id' not in existing_columns:
        cursor.execute('ALTER TABLE check_record ADD COLUMN theme_id BIGINT NULL')
        cursor.execute('ALTER TABLE check_record ADD INDEX idx_theme_id (theme_id)')
        print('Added theme_id column')
        changes_made += 1
        
    if 'extra_data' not in existing_columns:
        cursor.execute('ALTER TABLE check_record ADD COLUMN extra_data JSON')
        print('Added extra_data column')
        changes_made += 1
        
    if 'delayed' not in existing_columns:
        cursor.execute('ALTER TABLE check_record ADD COLUMN delayed TINYINT(1) DEFAULT 0')
        print('Added delayed column')
        changes_made += 1
    
    print(f"check_record: {changes_made} columns added")
    
    # Create checkin_cycle table if not exists
    cursor.execute("SHOW TABLES LIKE 'checkin_cycle'")
    if not cursor.fetchone():
        cursor.execute('''
            CREATE TABLE checkin_cycle (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                user_id BIGINT NOT NULL,
                tenant_id BIGINT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                selected_themes JSON NOT NULL,
                is_active TINYINT(1) DEFAULT 1,
                created_at DATETIME(6) NOT NULL,
                updated_at DATETIME(6) NOT NULL,
                INDEX idx_user (user_id),
                INDEX idx_tenant (tenant_id),
                INDEX idx_active (is_active),
                FOREIGN KEY (user_id) REFERENCES user(id),
                FOREIGN KEY (tenant_id) REFERENCES tenant(id)
            )
        ''')
        print('Created checkin_cycle table')
    else:
        print('checkin_cycle table already exists')
    
    # Mark migration as applied
    cursor.execute("""
        INSERT INTO django_migrations (app, name, applied)
        SELECT 'check_system', '0002_add_21day_checkin_fields', NOW()
        WHERE NOT EXISTS (
            SELECT 1 FROM django_migrations 
            WHERE app = 'check_system' AND name = '0002_add_21day_checkin_fields'
        )
    """)
    print('Migration marked as applied')
    
    print('\nDone!')

if __name__ == '__main__':
    apply_changes()
