"""
将租户 100 下所有的 46 篇文章及分类批量更新为高质量专业英文
"""
import os
import sys
import json
import django

# 设置 Django 运行环境
sys.path.insert(0, "D:/Github/lipeaks_backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.db import transaction
from cms.models import Article, Category

EN_DATA_FILE = "D:/Github/lipeaks_debug/tenant_100_all_en_articles.json"


def update_articles_and_categories():
    print("=" * 60)
    print("开始将租户 ID=100 的所有文章与分类替换为纯英文...")
    print("=" * 60)

    with open(EN_DATA_FILE, "r", encoding="utf-8") as f:
        en_articles = json.load(f)

    with transaction.atomic():
        # 1. 更新 46 篇文章
        updated_count = 0
        for art_id_str, en_data in en_articles.items():
            art_id = int(art_id_str)
            try:
                article = Article.objects.get(id=art_id, tenant_id=100)
                article.title = en_data["title"]
                article.excerpt = en_data["excerpt"]
                article.content = en_data["content"]
                article.save(update_fields=["title", "excerpt", "content", "updated_at"])
                updated_count += 1
                print(f"[{updated_count}/46] 成功更新文章 ID={art_id}: {article.title[:45]}...")
            except Article.DoesNotExist:
                print(f"❌ 警告: 未找到租户 100 下的文章 ID={art_id}")

        # 2. 顺带将租户 100 下的分类名称英文化
        cat_map = {
            "cat-proxyman": "Proxyman",
            "cat-video-compressor": "Video Compressor",
            "cat-steps": "Steps",
            "cat-ponics": "Ponics",
            "news": "News",
        }

        cat_updated = 0
        for slug, en_name in cat_map.items():
            cats = Category.objects.filter(tenant_id=100, slug=slug)
            for c in cats:
                old_name = c.name
                c.name = en_name
                c.save()
                cat_updated += 1
                print(f"更新分类: [{c.id}] {old_name} -> {en_name}")

    print("=" * 60)
    print(f"更新完成！共更新文章: {updated_count} 篇，更新分类: {cat_updated} 个。")
    print("=" * 60)


if __name__ == "__main__":
    update_articles_and_categories()
