"""
删除租户ID=1中的重复文章（硬删除）
策略：保留最新创建的文章（ID最大），删除其他重复的
"""
import os
import json
import django
from datetime import datetime

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db.models import Count
from cms.models import Article, ArticleCategory, ArticleTag, Comment, ArticleStatistics

def export_articles_to_delete(tenant_id=1):
    """导出要删除的文章列表作为备份"""
    
    # 查找title相同的文章组
    duplicate_groups = (
        Article.objects
        .filter(tenant_id=tenant_id, is_deleted=False)
        .values('title')
        .annotate(count=Count('id'))
        .filter(count__gt=1)
        .order_by('-count')
    )
    
    articles_to_delete = []
    articles_to_keep = []
    
    for group in duplicate_groups:
        title = group['title']
        
        # 获取该标题的所有文章，按ID排序
        articles = Article.objects.filter(
            tenant_id=tenant_id,
            title=title,
            is_deleted=False
        ).order_by('id')
        
        # 保留ID最大的（最新的），删除其他的
        articles_list = list(articles)
        keep_article = articles_list[-1]  # ID最大的
        delete_articles = articles_list[:-1]  # 其他的
        
        # 记录要保留的文章
        articles_to_keep.append({
            'id': keep_article.id,
            'title': keep_article.title,
            'slug': keep_article.slug,
            'created_at': keep_article.created_at.isoformat(),
            'author': keep_article.author_display_name or 'N/A',
            'status': keep_article.status,
        })
        
        # 记录要删除的文章
        for article in delete_articles:
            article_data = {
                'id': article.id,
                'title': article.title,
                'slug': article.slug,
                'content': article.content[:500] + '...' if len(article.content) > 500 else article.content,
                'excerpt': article.excerpt,
                'status': article.status,
                'created_at': article.created_at.isoformat(),
                'published_at': article.published_at.isoformat() if article.published_at else None,
                'author': article.author_display_name or 'N/A',
                'author_type': article.author_type,
                'views_count': article.statistics.views_count if hasattr(article, 'statistics') else 0,
            }
            articles_to_delete.append(article_data)
    
    # 保存备份文件
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f'backup_deleted_articles_{timestamp}.json'
    keep_file = f'backup_kept_articles_{timestamp}.json'
    
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(articles_to_delete, f, ensure_ascii=False, indent=2)
    
    with open(keep_file, 'w', encoding='utf-8') as f:
        json.dump(articles_to_keep, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 备份文件已创建:")
    print(f"   - 要删除的文章: {backup_file}")
    print(f"   - 要保留的文章: {keep_file}")
    print(f"   - 要删除的文章数: {len(articles_to_delete)}")
    print(f"   - 要保留的文章数: {len(articles_to_keep)}")
    
    return articles_to_delete, articles_to_keep


def delete_duplicate_articles(tenant_id=1, dry_run=False):
    """删除重复文章（硬删除）"""
    
    print(f"\n{'='*80}")
    print(f"开始{'模拟' if dry_run else '执行'}删除操作")
    print(f"租户ID: {tenant_id}")
    print(f"策略: 保留ID最大的文章，硬删除其他重复文章")
    print(f"{'='*80}\n")
    
    # 查找title相同的文章组
    duplicate_groups = (
        Article.objects
        .filter(tenant_id=tenant_id, is_deleted=False)
        .values('title')
        .annotate(count=Count('id'))
        .filter(count__gt=1)
        .order_by('-count')
    )
    
    total_deleted = 0
    deleted_ids = []
    
    for idx, group in enumerate(duplicate_groups, 1):
        title = group['title']
        count = group['count']
        
        print(f"\n[{idx}] 处理标题: {title[:60]}...")
        print(f"    重复数量: {count}")
        
        # 获取该标题的所有文章，按ID排序
        articles = Article.objects.filter(
            tenant_id=tenant_id,
            title=title,
            is_deleted=False
        ).order_by('id')
        
        articles_list = list(articles)
        keep_article = articles_list[-1]  # ID最大的
        delete_articles = articles_list[:-1]  # 其他的
        
        print(f"    保留文章ID: {keep_article.id} (最新)")
        print(f"    删除文章ID: {[a.id for a in delete_articles]}")
        
        if not dry_run:
            # 硬删除
            for article in delete_articles:
                try:
                    article_id = article.id
                    article.delete()  # 硬删除，会级联删除关联数据
                    deleted_ids.append(article_id)
                    total_deleted += 1
                    print(f"      ✅ 已删除文章ID: {article_id}")
                except Exception as e:
                    print(f"      ❌ 删除文章ID {article.id} 失败: {str(e)}")
        else:
            total_deleted += len(delete_articles)
    
    print(f"\n{'='*80}")
    if dry_run:
        print(f"模拟完成 - 将删除 {total_deleted} 篇文章")
    else:
        print(f"✅ 删除完成 - 已删除 {total_deleted} 篇文章")
        print(f"   删除的文章ID: {deleted_ids}")
    print(f"{'='*80}\n")
    
    return total_deleted, deleted_ids


def verify_deletion(tenant_id=1):
    """验证删除结果"""
    
    print(f"\n{'='*80}")
    print(f"验证删除结果")
    print(f"{'='*80}\n")
    
    # 重新检查重复文章
    duplicate_groups = (
        Article.objects
        .filter(tenant_id=tenant_id, is_deleted=False)
        .values('title')
        .annotate(count=Count('id'))
        .filter(count__gt=1)
    )
    
    remaining_duplicates = duplicate_groups.count()
    
    if remaining_duplicates == 0:
        print("✅ 验证成功：租户ID=1没有重复文章了！")
    else:
        print(f"⚠️  警告：仍有 {remaining_duplicates} 组重复文章")
        for group in duplicate_groups:
            print(f"   - {group['title']}: {group['count']} 篇")
    
    print(f"\n{'='*80}\n")
    
    return remaining_duplicates == 0


if __name__ == '__main__':
    import sys
    
    # 检查是否有 --dry-run 参数
    dry_run = '--dry-run' in sys.argv
    
    if dry_run:
        print("\n⚠️  模拟模式 - 不会真正删除数据\n")
    else:
        print("\n⚠️  警告：即将执行硬删除操作，此操作不可恢复！\n")
        response = input("确认要继续吗？(输入 'yes' 继续): ")
        if response.lower() != 'yes':
            print("操作已取消")
            sys.exit(0)
    
    # 1. 导出备份
    if not dry_run:
        print("\n步骤 1: 导出备份...")
        articles_to_delete, articles_to_keep = export_articles_to_delete(tenant_id=1)
    
    # 2. 执行删除
    print("\n步骤 2: 执行删除...")
    total_deleted, deleted_ids = delete_duplicate_articles(tenant_id=1, dry_run=dry_run)
    
    # 3. 验证结果
    if not dry_run:
        print("\n步骤 3: 验证结果...")
        verify_deletion(tenant_id=1)
    
    print("\n🎉 操作完成！")
