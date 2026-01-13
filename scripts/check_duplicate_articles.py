"""
检查租户ID=1中的重复文章
"""
import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db.models import Count
from cms.models import Article

def check_duplicate_articles(tenant_id=1):
    """检查指定租户的重复文章"""
    
    # 查找title相同的文章组
    duplicate_groups = (
        Article.objects
        .filter(tenant_id=tenant_id, is_deleted=False)
        .values('title')
        .annotate(count=Count('id'))
        .filter(count__gt=1)
        .order_by('-count')
    )
    
    print(f"\n租户ID={tenant_id}的重复文章统计:")
    print(f"{'='*80}")
    print(f"发现 {duplicate_groups.count()} 组重复的文章标题")
    print(f"{'='*80}\n")
    
    total_duplicates = 0
    
    for group in duplicate_groups:
        title = group['title']
        count = group['count']
        
        # 获取该标题的所有文章
        articles = Article.objects.filter(
            tenant_id=tenant_id,
            title=title,
            is_deleted=False
        ).order_by('created_at')
        
        print(f"\n标题: {title}")
        print(f"重复数量: {count} 篇")
        print(f"{'-'*80}")
        
        for idx, article in enumerate(articles, 1):
            print(f"  [{idx}] ID: {article.id}")
            print(f"      Slug: {article.slug}")
            print(f"      状态: {article.status}")
            print(f"      创建时间: {article.created_at}")
            print(f"      发布时间: {article.published_at}")
            print(f"      作者: {article.author_display_name or 'N/A'}")
            print(f"      浏览量: {article.statistics.views_count if hasattr(article, 'statistics') else 0}")
            print()
        
        total_duplicates += count - 1
    
    print(f"\n{'='*80}")
    print(f"总结:")
    print(f"  - 重复标题组数: {duplicate_groups.count()}")
    print(f"  - 需要删除的文章数: {total_duplicates} (保留每组中的1篇)")
    print(f"{'='*80}\n")
    
    return duplicate_groups

if __name__ == '__main__':
    check_duplicate_articles(tenant_id=1)
