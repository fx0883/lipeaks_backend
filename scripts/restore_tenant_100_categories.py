"""
Restore Tenant 100 Categories and re-link Tenant 100 articles.
This script:
1. Renames category 70 slug from 'news' to 'compressor-news' (tenant 20)
2. Creates categories 122-127 for Tenant 100:
   - 122: cat-proxyman (app 12)
   - 123: cat-video-compressor (app 13)
   - 124: cat-steps (app 14)
   - 125: cat-ponics (app 15)
   - 126: news (app None)
   - 127: visshow (app 18)
3. Inserts translations in zh-hans and en
4. Updates cms_article_category for Tenant 100 articles (56-113)
"""
import os
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection
from django.utils import timezone

def run():
    now = timezone.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    with connection.cursor() as cursor:
        print("1. Updating Category 70 slug...")
        cursor.execute("UPDATE cms_category SET slug = 'compressor-news' WHERE id = 70 AND slug = 'news'")
        print(f"   Rows affected: {cursor.rowcount}")

        categories = [
            (122, 'cat-proxyman', 1, 100, 12),
            (123, 'cat-video-compressor', 2, 100, 13),
            (124, 'cat-steps', 3, 100, 14),
            (125, 'cat-ponics', 4, 100, 15),
            (126, 'news', 0, 100, None),
            (127, 'visshow', 1, 100, 18),
        ]

        print("2. Inserting Tenant 100 Categories...")
        for cat_id, slug, sort_order, tenant_id, app_id in categories:
            cursor.execute("""
                INSERT INTO cms_category (
                    id, slug, cover_image, created_at, updated_at,
                    sort_order, is_active, parent_id, tenant_id,
                    is_pinned, application_id, is_deleted, is_admin_only
                ) VALUES (
                    %s, %s, NULL, %s, %s,
                    %s, 1, NULL, %s,
                    0, %s, 0, 0
                ) ON DUPLICATE KEY UPDATE
                    slug = VALUES(slug),
                    sort_order = VALUES(sort_order),
                    tenant_id = VALUES(tenant_id),
                    application_id = VALUES(application_id),
                    is_active = 1,
                    is_deleted = 0
            """, [cat_id, slug, now, now, sort_order, tenant_id, app_id])
            print(f"   Category {cat_id} ({slug}): OK")

        translations = [
            # 122: cat-proxyman
            ('zh-hans', 'Proxyman 调试工具', '高性能原生 HTTP/HTTPS 抓包调试与 Mock 工具技术指南与更新', 'Proxyman 调试工具 - EspressoX', '高性能原生 HTTP/HTTPS 抓包调试与 Mock 工具技术指南与更新', 122),
            ('en', 'Proxyman DevTools', 'High performance native HTTP/HTTPS proxy and mocking tutorials.', 'Proxyman DevTools - EspressoX', 'High performance native HTTP/HTTPS proxy and mocking tutorials.', 122),
            # 123: cat-video-compressor
            ('zh-hans', 'Video Compressor 视频工具', '高能效离线视频压缩与 GIF 转换器最佳实践与更新', 'Video Compressor 视频工具 - EspressoX', '高能效离线视频压缩与 GIF 转换器最佳实践与更新', 123),
            ('en', 'Video Compressor', 'High efficiency local video compressor & GIF converter practice.', 'Video Compressor - EspressoX', 'High efficiency local video compressor & GIF converter practice.', 123),
            # 124: cat-steps
            ('zh-hans', 'Steps 计步与健身', 'Apple Health 原生计步、3D 轨迹回放与健康生活方式指引', 'Steps 计步与健身 - EspressoX', 'Apple Health 原生计步、3D 轨迹回放与健康生活方式指引', 124),
            ('en', 'Steps Pedometer', 'Apple Health pedometer, 3D route replay and fitness guidance.', 'Steps Pedometer - EspressoX', 'Apple Health pedometer, 3D route replay and fitness guidance.', 124),
            # 125: cat-ponics
            ('zh-hans', '自然拼读 Ponics', '44个核心音素、艾宾浩斯抗遗忘记忆曲线与儿童启蒙方法论', '自然拼读 Ponics - EspressoX', '44个核心音素、艾宾浩斯抗遗忘记忆曲线与儿童启蒙方法论', 125),
            ('en', 'Ponics Phonics', '44 phonemes, Ebbinghaus forgetting curve and English phonics.', 'Ponics Phonics - EspressoX', '44 phonemes, Ebbinghaus forgetting curve and English phonics.', 125),
            # 126: news
            ('zh-hans', 'News', 'LiPeaks Studio 品牌资讯、官方公告与生态动态', 'News - LiPeaks Studio', 'LiPeaks Studio 官方动态与新闻发布', 126),
            ('en', 'News', 'Official news, announcements and product updates from LiPeaks Studio.', 'News - LiPeaks Studio', 'LiPeaks Studio Official News and Announcements', 126),
            # 127: visshow
            ('zh-hans', 'VisShow', 'VisCase 视觉展示精选案例', 'VisShow - LiPeaks Studio', 'VisCase 视觉展示精选案例', 127),
            ('en', 'VisShow', 'VisCase Visual Showcase', 'VisShow - LiPeaks Studio', 'VisCase Visual Showcase', 127),
        ]

        print("3. Inserting Category Translations...")
        for lang, name, desc, seo_title, seo_desc, master_id in translations:
            cursor.execute("""
                INSERT INTO cms_category_translation (
                    language_code, name, description, seo_title, seo_description, master_id
                ) VALUES (
                    %s, %s, %s, %s, %s, %s
                ) ON DUPLICATE KEY UPDATE
                    name = VALUES(name),
                    description = VALUES(description),
                    seo_title = VALUES(seo_title),
                    seo_description = VALUES(seo_description)
            """, [lang, name, desc, seo_title, seo_desc, master_id])
            print(f"   Translation ({lang}) for master_id {master_id}: OK")

        article_mappings = [
            (56, 65, 122),
            (66, 75, 123),
            (76, 85, 124),
            (86, 95, 125),
            (96, 101, 126),
            (102, 113, 127),
        ]

        print("4. Updating cms_article_category mapping for Tenant 100...")
        for start_id, end_id, target_cat_id in article_mappings:
            cursor.execute("""
                UPDATE cms_article_category
                SET category_id = %s, tenant_id = 100
                WHERE article_id BETWEEN %s AND %s
            """, [target_cat_id, start_id, end_id])
            print(f"   Articles {start_id}-{end_id} -> category {target_cat_id}: {cursor.rowcount} rows updated")

    print("\nRestore finished successfully!")

if __name__ == '__main__':
    run()
