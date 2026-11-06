#!/usr/bin/env python
"""
Import data from docs/sql/3 into the active database safely.
Guarantees:
1. Never drops or alters existing table schemas.
2. Uses INSERT IGNORE to prevent overwriting existing tenant data.
3. Cleans schema mismatches (e.g. cms_category fields, removing is_deleted from category translations).
4. Handles foreign key dependencies safely.
"""

import os
import re
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.db import connection

SQL_DIR = os.path.join(BASE_DIR, "docs", "sql", "3")
BACKUP_SQL = os.path.join(BASE_DIR, "docs", "sql", "multi_tenant_db_dev_20261008.sql")


def get_table_counts(cursor, tables):
    counts = {}
    for t in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM `{t}`;")
            counts[t] = cursor.fetchone()[0]
        except Exception:
            counts[t] = -1
    return counts


def main():
    print("=" * 60)
    print("Starting Safe Data Import for docs/sql/3")
    print("=" * 60)

    tables_to_check = [
        "tenant",
        "cms_tag_group",
        "cms_tag",
        "cms_category",
        "cms_category_translation",
        "cms_article_application",
        "cms_article_version",
        "cms_access_log",
    ]

    with connection.cursor() as cursor:
        initial_counts = get_table_counts(cursor, tables_to_check)
        print("Initial Table Counts:")
        for t, c in initial_counts.items():
            print(f"  {t:30}: {c} rows")

        # 1. Disable FK checks for safe batched insertion
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        print("\n[+] SET FOREIGN_KEY_CHECKS = 0;")

        try:
            # 2. Ensure Tenant 20 exists (referenced by cms_access_log & category 70)
            cursor.execute("""
                INSERT IGNORE INTO `tenant` 
                (`id`, `name`, `code`, `status`, `contact_name`, `contact_email`, `contact_phone`, `created_at`, `updated_at`, `is_deleted`)
                VALUES 
                (20, 'Compressor', 'compressor', 'active', 'Compressor', 'Compressor@online.com', '13387649839', NOW(), NOW(), 0);
            """)
            print("[+] Ensured Tenant 20 exists.")

            # 3. Import cms_tag_group.sql (10 rows)
            tag_group_path = os.path.join(SQL_DIR, "cms_tag_group.sql")
            tg_count = 0
            with open(tag_group_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("INSERT INTO `cms_tag_group`"):
                        stmt = line.replace("INSERT INTO `cms_tag_group`", "INSERT IGNORE INTO `cms_tag_group`")
                        cursor.execute(stmt)
                        tg_count += 1
            print(f"[+] Processed cms_tag_group.sql: {tg_count} statements.")

            # 4. Import cms_tag.sql (17 rows)
            tag_path = os.path.join(SQL_DIR, "cms_tag.sql")
            tag_count = 0
            with open(tag_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("INSERT INTO `cms_tag`"):
                        stmt = line.replace("INSERT INTO `cms_tag`", "INSERT IGNORE INTO `cms_tag`")
                        cursor.execute(stmt)
                        tag_count += 1
            print(f"[+] Processed cms_tag.sql: {tag_count} statements.")

            # 5. Import cms_category.sql (7 rows)
            # Old schema: (id, name, slug, description, cover_image, created_at, updated_at, sort_order, is_active, seo_title, seo_description, parent_id, tenant_id)
            # Current schema: (id, slug, cover_image, created_at, updated_at, sort_order, is_active, parent_id, tenant_id, is_pinned, is_deleted, is_admin_only)
            cat_path = os.path.join(SQL_DIR, "cms_category.sql")
            with open(cat_path, "r", encoding="utf-8") as f:
                cat_text = f.read()

            cat_matches = re.findall(r"INSERT INTO `cms_category` VALUES \((.*?)\);", cat_text)
            cat_count = 0
            for m in cat_matches:
                # We need to evaluate the values tuple safely
                # Format: 1, 'Product', 'product-655', '', NULL, '2025-07-08 14:01:50.263836', '2025-07-08 14:01:50.263836', 0, 1, NULL, NULL, NULL, 1
                cursor.execute(f"""
                    INSERT IGNORE INTO `cms_category` 
                    (`id`, `slug`, `cover_image`, `created_at`, `updated_at`, `sort_order`, `is_active`, `parent_id`, `tenant_id`, `is_pinned`, `is_deleted`, `is_admin_only`)
                    SELECT vals.id, vals.slug, vals.cover_image, vals.created_at, vals.updated_at, vals.sort_order, vals.is_active, vals.parent_id, vals.tenant_id, 0, 0, 0
                    FROM (SELECT {m}) as vals(id, name, slug, description, cover_image, created_at, updated_at, sort_order, is_active, seo_title, seo_description, parent_id, tenant_id);
                """)
                # Also insert translation for categories 1, 3, 4
                cursor.execute(f"""
                    INSERT IGNORE INTO `cms_category_translation`
                    (`language_code`, `name`, `description`, `seo_title`, `seo_description`, `master_id`)
                    SELECT 'zh-hans', vals.name, vals.description, vals.seo_title, vals.seo_description, vals.id
                    FROM (SELECT {m}) as vals(id, name, slug, description, cover_image, created_at, updated_at, sort_order, is_active, seo_title, seo_description, parent_id, tenant_id)
                    WHERE vals.id IN (1, 3, 4);
                """)
                cursor.execute(f"""
                    INSERT IGNORE INTO `cms_category_translation`
                    (`language_code`, `name`, `description`, `seo_title`, `seo_description`, `master_id`)
                    SELECT 'en', vals.name, vals.description, vals.seo_title, vals.seo_description, vals.id
                    FROM (SELECT {m}) as vals(id, name, slug, description, cover_image, created_at, updated_at, sort_order, is_active, seo_title, seo_description, parent_id, tenant_id)
                    WHERE vals.id IN (1, 3, 4);
                """)
                cat_count += 1
            print(f"[+] Processed cms_category.sql: {cat_count} records adapted to new schema & translations.")

            # 6. Ensure missing parent categories exist from backup SQL so that cms_category_translation does not point to non-existent categories
            if os.path.exists(BACKUP_SQL):
                missing_cats_count = 0
                with open(BACKUP_SQL, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        if line.startswith("INSERT INTO `cms_category` VALUES"):
                            m = re.match(r"INSERT INTO `cms_category` VALUES \((\d+),", line)
                            if m:
                                cid = int(m.group(1))
                                if cid in list(range(10, 50)) + [70]:
                                    stmt = line.strip().replace("INSERT INTO `cms_category`", "INSERT IGNORE INTO `cms_category`")
                                    cursor.execute(stmt)
                                    missing_cats_count += 1
                print(f"[+] Imported {missing_cats_count} missing parent categories from backup for translation integrity.")

            # 7. Import cms_category_translation.sql (276 rows, removing is_deleted)
            cat_trans_path = os.path.join(SQL_DIR, "cms_category_translation.sql")
            cat_trans_count = 0
            with open(cat_trans_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("INSERT INTO `cms_category_translation`"):
                        cleaned = line.replace(", `is_deleted`", "")
                        cleaned = cleaned.replace("INSERT INTO `cms_category_translation`", "INSERT IGNORE INTO `cms_category_translation`")
                        cleaned = re.sub(r",\s*[01]\s*\);$", ");", cleaned)
                        cursor.execute(cleaned)
                        cat_trans_count += 1
            print(f"[+] Processed cms_category_translation.sql: {cat_trans_count} statements (cleaned is_deleted column).")

            # 8. Import cms_article_application.sql (2 rows)
            art_app_path = os.path.join(SQL_DIR, "cms_article_application.sql")
            art_app_count = 0
            with open(art_app_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("INSERT INTO `cms_article_application`"):
                        stmt = line.replace("INSERT INTO `cms_article_application`", "INSERT IGNORE INTO `cms_article_application`")
                        cursor.execute(stmt)
                        art_app_count += 1
            print(f"[+] Processed cms_article_application.sql: {art_app_count} statements.")

            # 9. Import cms_article_version.sql (41 rows)
            art_ver_path = os.path.join(SQL_DIR, "cms_article_version.sql")
            art_ver_count = 0
            # May span multiple lines or be one statement per line
            with open(art_ver_path, "r", encoding="utf-8") as f:
                ver_sql = f.read()

            ver_stmts = [s.strip() for s in ver_sql.split(";\n") if s.strip()]
            for stmt in ver_stmts:
                if stmt.startswith("INSERT INTO `cms_article_version`"):
                    cleaned = stmt.replace("INSERT INTO `cms_article_version`", "INSERT IGNORE INTO `cms_article_version`")
                    if not cleaned.endswith(";"):
                        cleaned += ";"
                    cursor.execute(cleaned)
                    art_ver_count += 1
            print(f"[+] Processed cms_article_version.sql: {art_ver_count} statements.")

            # 10. Import cms_access_log.sql (15 rows)
            log_path = os.path.join(SQL_DIR, "cms_access_log.sql")
            log_count = 0
            with open(log_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("INSERT INTO `cms_access_log`"):
                        stmt = line.replace("INSERT INTO `cms_access_log`", "INSERT IGNORE INTO `cms_access_log`")
                        cursor.execute(stmt)
                        log_count += 1
            print(f"[+] Processed cms_access_log.sql: {log_count} statements.")

        finally:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
            print("\n[+] Restored SET FOREIGN_KEY_CHECKS = 1;")

        final_counts = get_table_counts(cursor, tables_to_check)
        print("\n" + "=" * 60)
        print("Final Table Counts & Net Changes:")
        print("=" * 60)
        for t in tables_to_check:
            init_c = initial_counts[t]
            fin_c = final_counts[t]
            diff = fin_c - init_c
            print(f"  {t:30}: {fin_c:5} rows (change: +{diff})")


if __name__ == "__main__":
    main()
