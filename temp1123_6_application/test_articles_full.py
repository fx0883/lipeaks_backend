from django.test import RequestFactory
from applications.models import Application
from cms.models import Article
from cms.serializers import ArticleListSerializer

factory = RequestFactory()
request = factory.get('/api/v1/applications/1/articles/')

app = Application.objects.get(id=1)
print(f"Application: {app.name}")
print(f"Tenant: {app.tenant_id}")

try:
    articles = Article.objects.filter(
        tenant_id=app.tenant_id,
        articleapplication__application=app
    ).select_related('user', 'member')
    
    print(f"找到 {articles.count()} 篇文章")
    
    # 测试序列化 - 带request context
    serializer = ArticleListSerializer(articles, many=True, context={'request': request})
    print("序列化成功")
    data = serializer.data
    print(f"数据长度: {len(data)}")
    if data:
        print(f"第一条: {data[0]}")
except Exception as e:
    print(f"错误: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
