#!/usr/bin/env python3
"""
Physical cleanup script for Tenant 1 (admin_cms) in multi_tenant_db_dev.
Deletes:
1. All physical image/resource files exclusive to tenant 1 articles/categories.
2. All business data records for tenant_id = 1 across all database tables.
Preserves:
- The tenant entity itself (tenant id=1, name='admin_cms')
- The admin login user (user id=2, username='admin_cms')
- Tenant quota configuration
"""

import os
import sys
import pymysql

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "123456",
    "database": "multi_tenant_db_dev",
    "charset": "utf8mb4",
}

TENANT_ID = 1
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA_ROOT = os.path.join(PROJECT_ROOT, "media")


def main():
    print("=" * 75)
    print(f"Cleaning up Tenant ID {TENANT_ID} (admin_cms) in database [{DB_CONFIG['database']}]")
    print("Mode: Hard Physical Delete (Database Rows + Disk Image Files)")
    print("Preserving: Tenant 1 record, admin_cms user, Tenant quota")
    print("=" * 75)

    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        # 1. Identify and delete disk files
        print("\n[1] Scanning and removing physical media files...")
        cursor.execute("""
            SELECT DISTINCT cover_image FROM cms_article WHERE tenant_id = %s AND cover_image != '';
        """, (TENANT_ID,))
        cover_images = [row[0] for row in cursor.fetchall()]

        cursor.execute("""
            SELECT DISTINCT cover_image_small FROM cms_article WHERE tenant_id = %s AND cover_image_small != '';
        """, (TENANT_ID,))
        small_images = [row[0] for row in cursor.fetchall()]

        cursor.execute("""
            SELECT DISTINCT cover_image FROM cms_category WHERE tenant_id = %s AND cover_image != '';
        """, (TENANT_ID,))
        cat_images = [row[0] for row in cursor.fetchall()]

        all_rel_paths = set(cover_images + small_images + cat_images)
        deleted_files_count = 0

        for rel in sorted(all_rel_paths):
            cleaned = rel.strip().lstrip('/')
            if cleaned.startswith('media/'):
                sub = cleaned[len('media/'):]
            elif '/media/' in cleaned:
                sub = cleaned.split('/media/', 1)[1]
            else:
                sub = cleaned

            abs_path = os.path.join(MEDIA_ROOT, sub)
            if os.path.exists(abs_path) and os.path.isfile(abs_path):
                os.remove(abs_path)
                deleted_files_count += 1
                print(f"  [-] Deleted disk file: {os.path.relpath(abs_path, PROJECT_ROOT)}")

        print(f"[✓] Physical files cleanup finished: {deleted_files_count} files deleted from disk.")

        # 2. Disable foreign key checks for clean bulk deletion
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        print("\n[2] Disabled foreign key checks (SET FOREIGN_KEY_CHECKS = 0).")

        # 3. Tables to delete from
        delete_tasks = [
            ("cms_access_log", "DELETE FROM `cms_access_log` WHERE `tenant_id` = %s;"),
            ("cms_comment", "DELETE FROM `cms_comment` WHERE `tenant_id` = %s;"),
            ("cms_article_category", "DELETE FROM `cms_article_category` WHERE `tenant_id` = %s;"),
            ("cms_article_application", "DELETE FROM `cms_article_application` WHERE `tenant_id` = %s;"),
            ("cms_article_statistics", "DELETE FROM `cms_article_statistics` WHERE `tenant_id` = %s;"),
            ("cms_article_tag", "DELETE FROM `cms_article_tag` WHERE `tenant_id` = %s;"),
            ("cms_article_version", "DELETE FROM `cms_article_version` WHERE `tenant_id` = %s;"),
            ("cms_article_meta", "DELETE FROM `cms_article_meta` WHERE `tenant_id` = %s;"),
            ("cms_article", "DELETE FROM `cms_article` WHERE `tenant_id` = %s;"),
            (
                "cms_category_translation",
                "DELETE FROM `cms_category_translation` WHERE `master_id` IN (SELECT `id` FROM `cms_category` WHERE `tenant_id` = %s);",
            ),
            ("cms_category", "DELETE FROM `cms_category` WHERE `tenant_id` = %s;"),
            ("cms_tag", "DELETE FROM `cms_tag` WHERE `tenant_id` = %s;"),
            ("cms_operation_log", "DELETE FROM `cms_operation_log` WHERE `tenant_id` = %s;"),
            ("app_application", "DELETE FROM `app_application` WHERE `tenant_id` = %s;"),
            ("common_api_log", "DELETE FROM `common_api_log` WHERE `tenant_id` = %s;"),
            ("customer_tenant_relation", "DELETE FROM `customer_tenant_relation` WHERE `tenant_id` = %s;"),
            ("customer", "DELETE FROM `customer` WHERE `tenant_id` = %s;"),
            ("feedback_reply", "DELETE FROM `feedback_reply` WHERE `tenant_id` = %s;"),
            ("feedback_status_history", "DELETE FROM `feedback_status_history` WHERE `tenant_id` = %s;"),
            ("feedback_vote", "DELETE FROM `feedback_vote` WHERE `tenant_id` = %s;"),
            ("feedback_feedback", "DELETE FROM `feedback_feedback` WHERE `tenant_id` = %s;"),
            ("licenses_machine_binding", "DELETE FROM `licenses_machine_binding` WHERE `tenant_id` = %s;"),
            ("licenses_activation", "DELETE FROM `licenses_activation` WHERE `tenant_id` = %s;"),
            ("licenses_license", "DELETE FROM `licenses_license` WHERE `tenant_id` = %s;"),
            ("licenses_license_plan", "DELETE FROM `licenses_license_plan` WHERE `tenant_id` = %s;"),
            ("licenses_security_audit_log", "DELETE FROM `licenses_security_audit_log` WHERE `tenant_id` = %s;"),
            ("notification", "DELETE FROM `notification` WHERE `tenant_id` = %s;"),
            (
                "task_category_translation",
                "DELETE FROM `task_category_translation` WHERE `master_id` IN (SELECT `id` FROM `task_category` WHERE `tenant_id` = %s);",
            ),
            ("task_template", "DELETE FROM `task_template` WHERE `tenant_id` = %s;"),
            ("task_category", "DELETE FROM `task_category` WHERE `tenant_id` = %s;"),
            ("member", "DELETE FROM `member` WHERE `tenant_id` = %s;"),
            (
                "rbac_user_role",
                "DELETE FROM `rbac_user_role` WHERE `user_id` IN (SELECT `id` FROM `user` WHERE `tenant_id` = %s AND `username` != 'admin_cms');",
            ),
            (
                "user (secondary sub-users)",
                "DELETE FROM `user` WHERE `tenant_id` = %s AND `username` != 'admin_cms';",
            ),
        ]

        print("\n[3] Executing database row physical deletions...")
        deleted_summary = []
        for table_name, sql in delete_tasks:
            cursor.execute(sql, (TENANT_ID,))
            count = cursor.rowcount
            deleted_summary.append((table_name, count))
            print(f"  [-] {table_name:<30}: deleted {count} rows")

        conn.commit()

        # 4. Re-enable foreign key checks
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        print("\n[4] Re-enabled foreign key checks (SET FOREIGN_KEY_CHECKS = 1).")

        # 5. Verification
        print("\n[5] Verifying remaining records for Tenant 1:")
        cursor.execute("SELECT id, name, code FROM `tenant` WHERE id = %s;", (TENANT_ID,))
        tenant_row = cursor.fetchone()
        print(f"  Tenant record: {tenant_row}")

        cursor.execute("SELECT id, username, email, is_active FROM `user` WHERE tenant_id = %s;", (TENANT_ID,))
        user_rows = cursor.fetchall()
        print(f"  User records: {user_rows}")

        cursor.execute("SELECT count(*) FROM `cms_article` WHERE tenant_id = %s;", (TENANT_ID,))
        print(f"  Remaining cms_article: {cursor.fetchone()[0]}")

        cursor.execute("SELECT count(*) FROM `cms_category` WHERE tenant_id = %s;", (TENANT_ID,))
        print(f"  Remaining cms_category: {cursor.fetchone()[0]}")

        cursor.execute("SELECT count(*) FROM `member` WHERE tenant_id = %s;", (TENANT_ID,))
        print(f"  Remaining member: {cursor.fetchone()[0]}")

        cursor.execute("SELECT count(*) FROM `app_application` WHERE tenant_id = %s;", (TENANT_ID,))
        print(f"  Remaining app_application: {cursor.fetchone()[0]}")

        print("\n[✓] Tenant 1 (admin_cms) Data & Media Cleanup Completed Successfully!")

    except Exception as e:
        conn.rollback()
        try:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        except Exception:
            pass
        print(f"\n[!] Error during cleanup: {e}", file=sys.stderr)
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
