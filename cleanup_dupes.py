import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lipeaks_backend.settings')
django.setup()

from we_rss.models import WechatArticle
from django.db.models import Count

biz = 'Mzg5MTYwMzk0Ng=='
dupes = WechatArticle.objects.filter(feed__biz=biz).values('title').annotate(c=Count('id')).filter(c__gt=1)
print(f"Found {len(dupes)} titles with duplicates for biz {biz}.")

deleted_count = 0
for dupe in dupes:
    title = dupe['title']
    # Keep the oldest one (first imported), delete newer ones
    articles = list(WechatArticle.objects.filter(feed__biz=biz, title=title).order_by('id'))
    if len(articles) > 1:
        to_delete = articles[1:]
        for a in to_delete:
            a.delete()
            deleted_count += 1

print(f"Successfully deleted {deleted_count} duplicate articles.")
