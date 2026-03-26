from django.urls import path

from we_rss.views.article_views import ArticleViewSet, SyncTaskViewSet
from we_rss.views.credential_views import (
    CredentialLoginSessionViewSet,
    CredentialViewSet,
)
from we_rss.views.feed_views import FeedViewSet
from we_rss.views.rss_views import ArticleContentView, FeedRssView, TenantRssView
from we_rss.views.tag_views import MemberTagViewSet

app_name = "we-rss"


urlpatterns = [
    path("credentials/", CredentialViewSet.as_view({"get": "list"}), name="credential-list"),
    path("credentials/<int:pk>/", CredentialViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"}), name="credential-detail"),
    path("credentials/<int:pk>/check/", CredentialViewSet.as_view({"post": "check"}), name="credential-check"),
    path("credentials/<int:pk>/set-default/", CredentialViewSet.as_view({"post": "set_default"}), name="credential-set-default"),
    path("credentials/login-sessions/", CredentialLoginSessionViewSet.as_view({"post": "create"}), name="credential-login-session-create"),
    path(
        "credentials/login-sessions/<str:session_id>/",
        CredentialLoginSessionViewSet.as_view({"get": "retrieve"}),
        name="credential-login-session-detail",
    ),
    path("feeds/", FeedViewSet.as_view({"get": "list", "post": "create"}), name="feed-list"),
    path("tags/", MemberTagViewSet.as_view({"get": "list", "post": "create"}), name="tag-list"),
    path("tags/<int:pk>/", MemberTagViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"}), name="tag-detail"),
    path("feeds/search/", FeedViewSet.as_view({"get": "search"}), name="feed-search"),
    path("feeds/subscribe/", FeedViewSet.as_view({"post": "subscribe"}), name="feed-subscribe"),
    path("feeds/<int:pk>/", FeedViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"}), name="feed-detail"),
    path("feeds/<int:pk>/articles/", FeedViewSet.as_view({"delete": "clear_articles"}), name="feed-clear-articles"),
    path("feeds/<int:pk>/subscribe/", FeedViewSet.as_view({"delete": "unsubscribe"}), name="feed-unsubscribe"),
    path("feeds/<int:pk>/tags/", FeedViewSet.as_view({"get": "list_tags"}), name="feed-tag-list"),
    path("feeds/<int:pk>/tags/attach/", FeedViewSet.as_view({"post": "attach_tags"}), name="feed-tag-attach"),
    path("feeds/<int:pk>/tags/detach/", FeedViewSet.as_view({"post": "detach_tags"}), name="feed-tag-detach"),
    path("feeds/<int:pk>/sync/", FeedViewSet.as_view({"post": "sync"}), name="feed-sync"),
    path("articles/", ArticleViewSet.as_view({"get": "list"}), name="article-list"),
    path("articles/import-by-url/", ArticleViewSet.as_view({"post": "import_by_url"}), name="article-import-by-url"),
    path("articles/<int:pk>/", ArticleViewSet.as_view({"get": "retrieve", "delete": "destroy"}), name="article-detail"),
    path("articles/<int:pk>/refresh/", ArticleViewSet.as_view({"post": "refresh"}), name="article-refresh"),
    path("articles/<int:pk>/favorite/", ArticleViewSet.as_view({"put": "update_favorite"}), name="article-favorite"),
    path("articles/<int:pk>/tags/", ArticleViewSet.as_view({"get": "list_tags"}), name="article-tag-list"),
    path("articles/<int:pk>/tags/attach/", ArticleViewSet.as_view({"post": "attach_tags"}), name="article-tag-attach"),
    path("articles/<int:pk>/tags/detach/", ArticleViewSet.as_view({"post": "detach_tags"}), name="article-tag-detach"),
    path("tasks/", SyncTaskViewSet.as_view({"get": "list"}), name="task-list"),
    path("tasks/<int:task_id>/", SyncTaskViewSet.as_view({"get": "retrieve"}), name="task-detail"),
    path("rss/", TenantRssView.as_view(), name="rss"),
    path("rss/<int:feed_id>/", FeedRssView.as_view(), name="rss-feed"),
    path("rss/content/<int:article_id>/", ArticleContentView.as_view(), name="rss-content"),
]
