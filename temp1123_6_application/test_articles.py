from applications.models import Application
from cms.models import Article
from cms.serializers import ArticleListSerializer

app = Application.objects.get(id=1)
print(f"Application: {app.name}")
print(f"Tenant: {app.tenant_id}")

try:
    articles = Article.objects.filter(
        tenant_id=app.tenant_id,
        articleapplication__application=app
    ).select_related('user', 'member')
    
    print(f"找到 {articles.count()} 篇文章")
    
    # 测试序列化
    serializer = ArticleListSerializer(articles, many=True)
    print("序列化成功")
    print(f"数据: {serializer.data}")
except Exception as e:
    print(f"错误: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
