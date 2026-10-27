import os
import sys
import django

sys.path.insert(0, "D:/Github/lipeaks_backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from rest_framework.test import APIRequestFactory
from cms.views import ArticleViewSet

factory = APIRequestFactory()
request = factory.get("/api/v1/cms/articles/?page=1&page_size=6&status=published", HTTP_X_TENANT_ID="100", HTTP_HOST="localhost")
view = ArticleViewSet.as_view({"get": "list"})
response = view(request)

print(f"API HTTP Status: {response.status_code}")
data = response.data.get("data", response.data)
results = data.get("results", [])
print(f"Total returned in page 1: {len(results)}")
for a in results:
    print(f"ID: {a['id']} | Title: {a['title']}")

detail_request = factory.get(f"/api/v1/cms/articles/{results[0]['id']}/", HTTP_X_TENANT_ID="100", HTTP_HOST="localhost")
detail_view = ArticleViewSet.as_view({"get": "retrieve"})
detail_response = detail_view(detail_request, pk=results[0]['id'])
print(f"Detail API HTTP Status: {detail_response.status_code}")
detail_data = detail_response.data.get("data", detail_response.data)
print(f"Detail Title: {detail_data['title']}")
print(f"Detail Excerpt: {detail_data['excerpt']}")
print(f"Detail Content Preview: {detail_data['content'][:120]}...")
