from we_rss.models import WechatArticle
from django.db.models import Count
dupes = WechatArticle.objects.filter(feed__biz='Mzg5MTYwMzk0Ng==').values('title').annotate(c=Count('id')).filter(c__gt=1)
print('DUPLICATES COUNT:', len(dupes))
if dupes:
    title = dupes[0]['title']
    articles = WechatArticle.objects.filter(title=title).order_by('id')
    print(f'Title: {title}')
    for a in articles:
        print(f"ID: {a.id}")
        print(f"URL: {a.url}")
