"""
更新租户 100 下 VisCase (VisShow 分类 ID=127, 文章 ID=102~113) 的数据库实案文案。

依据每张作品实图 (P-1.jpg ~ P-12.jpg) 撰写图片驱动的真实中文案例标题、摘要、Markdown 正文剖析、
ArticleMeta SEO 元数据，以及 VisShow 分类描述与 VisCase 应用描述，并自动清理 Redis 接口缓存。
与 `cms/migrations/0017_update_viscase_cases_copy.py` 共用同一份幂等数据源，可安全重复执行。
"""
import importlib
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.chdir(BASE_DIR)

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.apps import apps
from django.db import transaction


def run():
    migration_mod = importlib.import_module("cms.migrations.0017_update_viscase_cases_copy")
    with transaction.atomic():
        summary = migration_mod.apply_viscase_copy(apps, db_alias="default", clear_cache=False)
    cache_cleared = migration_mod.clear_api_cache_safely()
    summary["cache_cleared"] = cache_cleared
    print(f"VisCase DB copy sync completed: {summary}")


if __name__ == "__main__":
    run()
