import importlib

import pytest
from django.apps import apps

from applications.models import Application
from cms.models import Article, ArticleMeta, Category
from tenants.models import Tenant
from users.models import User


migration_mod = importlib.import_module("cms.migrations.0017_update_viscase_cases_copy")


@pytest.mark.django_db
def test_viscase_copy_migration_noop_on_empty_db():
    summary = migration_mod.apply_viscase_copy(apps, db_alias="default", clear_cache=False)

    assert summary["application_updated"] is False
    assert summary["category_updated"] is False
    assert summary["articles_updated"] == 0


@pytest.mark.django_db
def test_viscase_copy_migration_updates_all_records_idempotently():
    tenant, _ = Tenant.objects.update_or_create(
        id=100,
        defaults={"name": "EspressoX CMS", "code": "espressox_cms_t100"},
    )
    author = User.objects.create_user(
        username="viscase_test_admin",
        email="viscase_test_admin@example.com",
        password="Password123!",
        tenant=tenant,
        is_admin=True,
        admin_type="tenant_owner",
    )
    app = Application.original_objects.create(
        tenant=tenant,
        name="VisCase Old",
        code="viscase",
        description="placeholder description",
    )
    cat = Category.objects.create(
        tenant=tenant,
        slug="visshow",
        application=app,
        name="VisShow",
        description="VisCase è§†è§‰å±•ç¤ºç²¾é€‰æ¡ˆä¾‹",
        seo_title="Old SEO Title",
        seo_description="Old SEO Description",
    )

    articles = []
    for idx, item in enumerate(migration_mod.VISCASE_DB_CASES, start=1):
        art = Article.original_objects.create(
            tenant=tenant,
            user=author,
            title=f"VisCase 案例 P-{idx}",
            slug=item["slug"],
            content=f"# VisCase 案例 P-{idx}\n\nplaceholder",
            content_type="markdown",
            excerpt=f"placeholder {idx}",
            cover_image=f"https://api.lipeaks.cloud/media/uploads/100/article_covers/P-{idx}.jpg",
            status="published",
        )
        articles.append(art)

    # First run
    first_summary = migration_mod.apply_viscase_copy(apps, db_alias="default", clear_cache=False)
    assert first_summary["application_updated"] is True
    assert first_summary["category_updated"] is True
    assert first_summary["articles_updated"] == 12

    app.refresh_from_db()
    assert app.name == "VisCase"
    assert "实体视觉案例展厅" in app.description

    cat_zh = Category.objects.language("zh-hans").get(pk=cat.pk)
    assert cat_zh.name == "VisShow"
    assert "12 组完整案例" in cat_zh.description
    assert "VisCase Studio" in cat_zh.seo_title

    cat_en = Category.objects.language("en").get(pk=cat.pk)
    assert cat_en.name == "VisShow"
    assert "Curated VisCase brand identity" in cat_en.description

    first_article = Article.original_objects.get(slug="viscase-case-p-1")
    assert first_article.title == "丹江口 · 南水北调源头城市形象标识"
    assert "山水太极" in first_article.excerpt
    assert "## 城市气质与双意象太极构图" in first_article.content
    meta = ArticleMeta.original_objects.get(article=first_article)
    assert meta.tenant_id == tenant.id
    assert meta.og_image == first_article.cover_image
    assert "丹江口" in meta.seo_keywords

    # Second run must be 100% idempotent with no duplicate rows
    second_summary = migration_mod.apply_viscase_copy(apps, db_alias="default", clear_cache=False)
    assert second_summary["application_updated"] is True
    assert second_summary["category_updated"] is True
    assert second_summary["articles_updated"] == 12
    assert ArticleMeta.original_objects.filter(article__slug__startswith="viscase-case-p-").count() == 12
