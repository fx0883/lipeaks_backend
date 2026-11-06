#!/usr/bin/env python3
"""
Sync CMS tables from muliti_tenant_db (source) to multi_tenant_db_dev (target).
Incremental Merge Strategy:
- Preserves dev-specific records (e.g. dev mock categories 1, 3, 4, dev articles 1..113).
- Resolves unique slug collisions gracefully (e.g. dev article 39 slug renamed to avoid clash with prod article 10342).
- Safely handles schema differences (cms_article_statistics without last_updated_at, cms_category_translation without is_deleted).
- Restores all production tags and category translations cleanly.
- Executes within foreign key checks disabled window.
"""

import sys
import pymysql

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "root",
    "password": "123456",
    "charset": "utf8mb4",
}

SOURCE_DB = "muliti_tenant_db"
TARGET_DB = "multi_tenant_db_dev"

CMS_TABLES = [
    "cms_tag_group",
    "cms_tag",
    "cms_category",
    "cms_category_translation",
    "cms_article",
    "cms_article_application",
    "cms_article_category",
    "cms_article_meta",
    "cms_article_statistics",
    "cms_article_tag",
    "cms_article_version",
    "cms_comment",
    "cms_access_log",
    "cms_operation_log",
    "cms_user_level",
    "cms_user_level_relation",
]


def get_columns(cursor, schema, table):
    cursor.execute("""
        SELECT COLUMN_NAME 
        FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s 
        ORDER BY ORDINAL_POSITION;
    """, (schema, table))
    return [row[0] for row in cursor.fetchall()]


def get_table_counts(cursor, schema, tables):
    counts = {}
    for t in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM `{schema}`.`{t}`;")
            counts[t] = cursor.fetchone()[0]
        except Exception as e:
            counts[t] = f"Error: {e}"
    return counts


def main():
    print("=" * 75)
    print(f"Syncing CMS data: [{SOURCE_DB}] -> [{TARGET_DB}]")
    print("Strategy: Incremental Merge / UPSERT (dev specific preserved, conflicts updated)")
    print("=" * 75)

    conn = pymysql.connect(**DB_CONFIG)
    cursor = conn.cursor()

    try:
        # 1. Initial counts
        source_counts = get_table_counts(cursor, SOURCE_DB, CMS_TABLES)
        target_counts_before = get_table_counts(cursor, TARGET_DB, CMS_TABLES)

        print("\n[1] Initial Row Counts:")
        print(f"{'Table':<28} | {'Source (' + SOURCE_DB + ')':<22} | {'Target Before':<15}")
        print("-" * 75)
        for t in CMS_TABLES:
            print(f"{t:<28} | {str(source_counts[t]):<22} | {str(target_counts_before[t]):<15}")

        # 2. Disable foreign key checks
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        print("\n[2] Disabled foreign key checks (SET FOREIGN_KEY_CHECKS = 0).")

        # 3. Ensure foreign key dependencies exist in target
        cursor.execute(f"SELECT COUNT(*) FROM `{TARGET_DB}`.`member` WHERE id = 40;")
        if cursor.fetchone()[0] == 0:
            print("[+] Inserting missing member 40 into target member table...")
            member_cols = get_columns(cursor, TARGET_DB, "member")
            source_member_cols = set(get_columns(cursor, SOURCE_DB, "member"))
            common_m_cols = [c for c in member_cols if c in source_member_cols]
            cols_str = ", ".join(f"`{c}`" for c in common_m_cols)
            cursor.execute(f"""
                INSERT INTO `{TARGET_DB}`.`member` ({cols_str})
                SELECT {cols_str} FROM `{SOURCE_DB}`.`member` WHERE id = 40;
            """)
            conn.commit()
            print("    -> Member 40 inserted.")
        else:
            print("[+] Member 40 already exists in target member table.")

        # 4. Resolve slug collision in cms_article (dev article 39 slug='article' vs prod article 10342 slug='article')
        cursor.execute(f"""
            UPDATE `{TARGET_DB}`.`cms_article` 
            SET slug = 'article-dev-39' 
            WHERE id = 39 AND slug = 'article';
        """)
        if cursor.rowcount > 0:
            print("[+] Renamed dev article 39 slug from 'article' to 'article-dev-39' to prevent unique slug conflict with prod article 10342.")
            conn.commit()

        # 5. Table Migration Step-by-Step
        print("\n[3] Starting table migration...")

        # 5.1 cms_tag_group
        t = "cms_tag_group"
        dev_cols = get_columns(cursor, TARGET_DB, t)
        src_cols = set(get_columns(cursor, SOURCE_DB, t))
        common_cols = [c for c in dev_cols if c in src_cols]
        cols_str = ", ".join(f"`{c}`" for c in common_cols)
        update_str = ", ".join(f"`{c}` = VALUES(`{c}`)" for c in common_cols if c != "id")
        cursor.execute(f"""
            INSERT INTO `{TARGET_DB}`.`{t}` ({cols_str})
            SELECT {cols_str} FROM `{SOURCE_DB}`.`{t}`
            ON DUPLICATE KEY UPDATE {update_str};
        """)
        conn.commit()
        print(f"[+] `{t}`: Synced {source_counts[t]} source rows.")

        # 5.2 cms_tag
        # Replace target tags with prod tags so slugs/IDs align exactly with prod canonical data
        t = "cms_tag"
        cursor.execute(f"DELETE FROM `{TARGET_DB}`.`{t}`;")
        dev_cols = get_columns(cursor, TARGET_DB, t)
        src_cols = set(get_columns(cursor, SOURCE_DB, t))
        common_cols = [c for c in dev_cols if c in src_cols]
        cols_str = ", ".join(f"`{c}`" for c in common_cols)
        cursor.execute(f"""
            INSERT INTO `{TARGET_DB}`.`{t}` ({cols_str})
            SELECT {cols_str} FROM `{SOURCE_DB}`.`{t}`;
        """)
        conn.commit()
        print(f"[+] `{t}`: Synced all {source_counts[t]} production tags cleanly.")

        # 5.3 cms_category
        # Preserve dev mock categories (IDs 1, 3, 4), delete other categories in dev, insert all prod categories (5..70)
        t = "cms_category"
        cursor.execute(f"DELETE FROM `{TARGET_DB}`.`{t}` WHERE id NOT IN (1, 3, 4);")
        del_count = cursor.rowcount
        print(f"[+] `{t}`: Kept dev mock categories (1, 3, 4), removed {del_count} overlapping dev categories.")
        dev_cols = get_columns(cursor, TARGET_DB, t)
        src_cols = set(get_columns(cursor, SOURCE_DB, t))
        common_cols = [c for c in dev_cols if c in src_cols]
        cols_str = ", ".join(f"`{c}`" for c in common_cols)
        cursor.execute(f"""
            INSERT INTO `{TARGET_DB}`.`{t}` ({cols_str})
            SELECT {cols_str} FROM `{SOURCE_DB}`.`{t}`;
        """)
        conn.commit()
        print(f"[+] `{t}`: Inserted all {source_counts[t]} production categories.")

        # 5.4 cms_category_translation
        # Preserve translations for categories 1, 3, 4, insert all prod translations
        t = "cms_category_translation"
        cursor.execute(f"DELETE FROM `{TARGET_DB}`.`{t}` WHERE master_id NOT IN (1, 3, 4);")
        del_count = cursor.rowcount
        print(f"[+] `{t}`: Kept dev mock translations for (1, 3, 4), removed {del_count} overlapping dev translations.")
        dev_cols = get_columns(cursor, TARGET_DB, t)
        src_cols = set(get_columns(cursor, SOURCE_DB, t))
        common_cols = [c for c in dev_cols if c in src_cols]
        cols_str = ", ".join(f"`{c}`" for c in common_cols)
        cursor.execute(f"""
            INSERT INTO `{TARGET_DB}`.`{t}` ({cols_str})
            SELECT {cols_str} FROM `{SOURCE_DB}`.`{t}`;
        """)
        conn.commit()
        print(f"[+] `{t}`: Inserted all {source_counts[t]} production category translations.")

        # 5.5 Remaining tables
        remaining_tables = [
            "cms_article",
            "cms_article_application",
            "cms_article_category",
            "cms_article_meta",
            "cms_article_statistics",
            "cms_article_tag",
            "cms_article_version",
            "cms_comment",
            "cms_access_log",
            "cms_operation_log",
            "cms_user_level",
            "cms_user_level_relation",
        ]

        for t in remaining_tables:
            src_count = source_counts[t]
            if src_count == 0:
                print(f"[-] `{t}`: Source has 0 rows, skipping.")
                continue

            dev_cols = get_columns(cursor, TARGET_DB, t)
            src_cols = set(get_columns(cursor, SOURCE_DB, t))
            common_cols = [c for c in dev_cols if c in src_cols]

            cols_str = ", ".join(f"`{c}`" for c in common_cols)
            update_str = ", ".join(f"`{c}` = VALUES(`{c}`)" for c in common_cols if c != "id")

            sql = f"""
                INSERT INTO `{TARGET_DB}`.`{t}` ({cols_str})
                SELECT {cols_str} FROM `{SOURCE_DB}`.`{t}`
                ON DUPLICATE KEY UPDATE {update_str};
            """

            cursor.execute(sql)
            conn.commit()
            print(f"[+] `{t}`: Synced {src_count} source rows (affected rows: {cursor.rowcount}).")

        # 6. Re-enable foreign key checks
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        print("\n[4] Re-enabled foreign key checks (SET FOREIGN_KEY_CHECKS = 1).")

        # 7. Final row counts
        target_counts_after = get_table_counts(cursor, TARGET_DB, CMS_TABLES)
        print("\n[5] Final Row Counts Comparison:")
        print(f"{'Table':<28} | {'Source (' + SOURCE_DB + ')':<18} | {'Target Before':<14} | {'Target After':<14}")
        print("-" * 80)
        for t in CMS_TABLES:
            print(f"{t:<28} | {str(source_counts[t]):<18} | {str(target_counts_before[t]):<14} | {str(target_counts_after[t]):<14}")

        print("\n[✓] CMS Data Migration Completed Successfully!")

    except Exception as e:
        conn.rollback()
        try:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        except Exception:
            pass
        print(f"\n[!] Error during migration: {e}", file=sys.stderr)
        raise
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()
