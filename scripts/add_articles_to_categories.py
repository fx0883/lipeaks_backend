#!/usr/bin/env python
"""
向租户ID为17的所有叶子分类添加13篇文章
"""
import os
import django
import sys
from datetime import datetime
import random
from faker import Faker

# 设置Django环境
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from cms.models import Category, Article, ArticleCategory
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.db import transaction

User = get_user_model()

# 初始化Faker生成假数据
fake = Faker()


def get_leaf_categories(tenant_id):
    """获取所有叶子分类（没有子分类的分类）"""
    all_categories = Category.objects.filter(tenant_id=tenant_id)
    leaf_categories = []
    
    for category in all_categories:
        if not all_categories.filter(parent=category).exists():
            leaf_categories.append(category)
    
    return leaf_categories


def create_article(author, tenant_id, category, index):
    """创建一篇文章"""
    title = f"{category.name} - {fake.catch_phrase()} ({index})"
    slug = slugify(f"{category.name}-{fake.word()}-{random.randint(1000, 9999)}")
    
    # 生成文章内容
    paragraphs = [fake.paragraph(nb_sentences=10) for _ in range(5)]
    content = "\n\n".join([f"## {fake.catch_phrase()}\n\n{p}" for p in paragraphs])
    
    # 创建文章
    article = Article(
        title=title,
        slug=slug,
        content=content,
        content_type='markdown',
        excerpt=fake.text(max_nb_chars=200),
        author=author,
        status='published',
        is_featured=random.choice([True, False]),
        is_pinned=False,
        allow_comment=True,
        visibility='public',
        published_at=datetime.now(),
        sort_order=0,
        tenant_id=tenant_id
    )
    article.save()
    
    # 创建文章分类关系
    ArticleCategory.objects.create(
        article=article,
        category=category,
        tenant_id=tenant_id
    )
    
    return article


def add_articles_to_leaf_categories(tenant_id=17, articles_per_category=13):
    """向所有叶子分类添加指定数量的文章"""
    # 获取叶子分类
    leaf_categories = get_leaf_categories(tenant_id)
    print(f"找到 {len(leaf_categories)} 个叶子分类")
    
    # 获取作者 (使用已有文章的作者)
    try:
        author = User.objects.get(pk=34)  # 根据已有文章的作者ID
    except User.DoesNotExist:
        print("找不到作者ID=34，脚本终止")
        return
    
    # 为每个叶子分类添加文章
    with transaction.atomic():
        for category in leaf_categories:
            # 检查当前分类中已有的文章数量
            existing_articles = ArticleCategory.objects.filter(
                category=category, 
                tenant_id=tenant_id
            ).count()
            
            print(f"分类 '{category.name}' (ID: {category.id}) 已有 {existing_articles} 篇文章")
            
            # 计算需要添加的文章数量
            articles_to_add = max(0, articles_per_category - existing_articles)
            print(f"需要添加 {articles_to_add} 篇文章到分类 '{category.name}'")
            
            # 添加文章
            for i in range(1, articles_to_add + 1):
                article = create_article(author, tenant_id, category, i)
                print(f"创建文章: {article.title}")
    
    print("完成！所有叶子分类都已添加足够的文章")


if __name__ == "__main__":
    # 默认参数：租户ID=17，每个分类13篇文章
    tenant_id = 17
    articles_per_category = 13
    
    # 从命令行参数获取
    if len(sys.argv) > 1:
        tenant_id = int(sys.argv[1])
    if len(sys.argv) > 2:
        articles_per_category = int(sys.argv[2])
    
    print(f"开始为租户 {tenant_id} 的所有叶子分类添加 {articles_per_category} 篇文章...")
    add_articles_to_leaf_categories(tenant_id, articles_per_category) 