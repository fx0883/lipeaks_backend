import re

from drf_spectacular.helpers import forced_singular_serializer
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiRequest, OpenApiResponse
from rest_framework import serializers


WE_RSS_TAG = "we-rss"
WE_RSS_AUTH_DESCRIPTION = (
    "需要使用当前项目的 Member JWT 访问。所有数据按 `request.user.tenant` 共享隔离，"
    "Member 未绑定 tenant 时会被拒绝访问。"
)
X_TENANT_ID_PARAMETER = OpenApiParameter(
    name="X-Tenant-ID",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.HEADER,
    required=True,
    description=(
        "Member JWT 接口必填的租户头。值必须等于当前 member 绑定的 tenant ID，"
        "用于触发 `common` 模块里的租户隔离和权限校验。"
    ),
    examples=[OpenApiExample("Tenant header example", value="1")],
)


def with_tenant_header(*parameters):
    return [X_TENANT_ID_PARAMETER, *parameters]


def _build_success_envelope_serializer(name, data_serializer):
    if isinstance(data_serializer, type) and issubclass(data_serializer, serializers.BaseSerializer):
        data_serializer = data_serializer()

    serializer_class = type(
        name,
        (serializers.Serializer,),
        {
            "success": serializers.BooleanField(),
            "code": serializers.IntegerField(),
            "message": serializers.CharField(),
            "data": data_serializer,
        },
    )
    return forced_singular_serializer(serializer_class)


def wrapped_success_response(data, message="操作成功", code=2000):
    return {
        "success": True,
        "code": code,
        "message": message,
        "data": data,
    }


def success_example(name, data, *, message="操作成功", status_code=200, description=""):
    return OpenApiExample(
        name=name,
        value=wrapped_success_response(data=data, message=message),
        response_only=True,
        status_codes=[str(status_code)],
        description=description,
    )


def request_example(name, value, *, description=""):
    return OpenApiExample(
        name=name,
        value=value,
        request_only=True,
        description=description,
    )


def request_body(request, *examples):
    return OpenApiRequest(
        request=request,
        examples=list(examples),
    )


def json_response(response, description, example_data=None, *, example_name=None, message=None, status_code=200, examples=None):
    schema_name = re.sub(r"[^0-9A-Za-z]+", "", f"{example_name}{status_code}Envelope")
    resolved_examples = examples
    if resolved_examples is None:
        resolved_examples = [
            success_example(
                example_name,
                example_data,
                message=message,
                status_code=status_code,
            )
        ]
    return OpenApiResponse(
        response=_build_success_envelope_serializer(schema_name, response),
        description=description,
        examples=resolved_examples,
    )


def xml_response(description, example_xml, *, example_name, status_code=200):
    return OpenApiResponse(
        response=OpenApiTypes.STR,
        description=description,
        examples=[
            OpenApiExample(
                name=example_name,
                value=example_xml,
                response_only=True,
                media_type="application/xml",
                status_codes=[str(status_code)],
            )
        ],
    )


def html_response(description, example_html, *, example_name, status_code=200):
    return OpenApiResponse(
        response=OpenApiTypes.STR,
        description=description,
        examples=[
            OpenApiExample(
                name=example_name,
                value=example_html,
                response_only=True,
                media_type="text/html",
                status_codes=[str(status_code)],
            )
        ],
    )


def path_int_parameter(name, description, example):
    return OpenApiParameter(
        name=name,
        type=OpenApiTypes.INT,
        location=OpenApiParameter.PATH,
        required=True,
        description=description,
        examples=[OpenApiExample(f"{name} example", value=example)],
    )


def path_str_parameter(name, description, example):
    return OpenApiParameter(
        name=name,
        type=OpenApiTypes.STR,
        location=OpenApiParameter.PATH,
        required=True,
        description=description,
        examples=[OpenApiExample(f"{name} example", value=example)],
    )


CREDENTIAL_ID_PARAMETER = path_int_parameter("id", "微信抓取凭证 ID。", 1)
FEED_ID_PARAMETER = path_int_parameter("id", "公众号记录 ID。", 1)
ARTICLE_ID_PARAMETER = path_int_parameter("id", "公众号文章记录 ID。", 1)
TASK_ID_PARAMETER = path_int_parameter("task_id", "异步同步任务 ID。", 101)
RSS_FEED_ID_PARAMETER = path_int_parameter("feed_id", "要生成 RSS 的公众号 ID。", 1)
RSS_ARTICLE_ID_PARAMETER = path_int_parameter("article_id", "要渲染正文 HTML 的文章 ID。", 1)
SESSION_ID_PARAMETER = path_str_parameter("session_id", "扫码登录会话 ID。", "session-123")
TASK_TYPE_PARAMETER = OpenApiParameter(
    name="task_type",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description="按任务类型过滤，可选值包括 `credential_login`、`feed_sync`、`article_import`、`article_refresh`。",
    examples=[OpenApiExample("Task type example", value="feed_sync")],
)
TASK_STATUS_PARAMETER = OpenApiParameter(
    name="status",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description="按任务状态过滤，可选值包括 `pending`、`running`、`success`、`failed`。",
    examples=[OpenApiExample("Task status example", value="failed")],
)
TASK_TARGET_TYPE_PARAMETER = OpenApiParameter(
    name="target_type",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description="按任务目标类型过滤，例如 `feed`、`article`、`login_session`。",
    examples=[OpenApiExample("Task target type example", value="feed")],
)
TASK_TARGET_ID_PARAMETER = OpenApiParameter(
    name="target_id",
    type=OpenApiTypes.INT,
    location=OpenApiParameter.QUERY,
    required=False,
    description="按任务目标记录 ID 过滤。",
    examples=[OpenApiExample("Task target id example", value=1)],
)
KEYWORD_PARAMETER = OpenApiParameter(
    name="keyword",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=True,
    description="用于微信公众平台搜索公众号的关键字，支持公众号名称或相关词。",
    examples=[OpenApiExample("Keyword example", value="AI")],
)


ARTICLE_TYPE_PARAMETER = OpenApiParameter(
    name="article_type",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Filter articles by article type. Supported values: `news`, `newspic`.",
    examples=[OpenApiExample("Article type example", value="newspic")],
)


CREDENTIAL_EXAMPLE = {
    "id": 1,
    "name": "Default Credential",
    "status": "active",
    "expires_at": "2026-03-31T12:00:00Z",
    "last_login_at": "2026-03-21T08:30:00Z",
    "last_check_at": "2026-03-21T08:35:00Z",
    "last_error": "",
    "is_default": True,
    "created_at": "2026-03-20T10:00:00Z",
    "updated_at": "2026-03-21T08:35:00Z",
}

LOGIN_SESSION_EXAMPLE = {
    "session_id": "session-123",
    "status": "pending",
    "qr_code_url": "https://mp.weixin.qq.com/cgi-bin/scanloginqrcode?action=getqrcode&uuid=session-123",
    "qr_code_image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
    "scan_status": "waiting",
    "error_message": "",
    "expired_at": "2026-03-21T09:00:00Z",
    "credential_id": None,
    "task_id": 301,
    "created_at": "2026-03-21T08:40:00Z",
    "updated_at": "2026-03-21T08:40:00Z",
}

CREDENTIAL_CHECK_EXAMPLE = {
    "valid": True,
    "status": "active",
    "message": "",
}

FEED_EXAMPLE = {
    "id": 1,
    "credential_id": 1,
    "source_id": "gh_abcdef123456",
    "faker_id": "MzA5NzQ1Mjg2NA==",
    "biz": "MzA5NzQ1Mjg2NA==",
    "mp_name": "AI Daily",
    "mp_cover": "https://example.com/feed-cover.png",
    "mp_intro": "Daily updates from the AI team.",
    "status": "active",
    "sync_time": "2026-03-21T09:20:00Z",
    "update_time": "2026-03-21T09:20:00Z",
    "last_synced_at": "2026-03-21T09:20:00Z",
    "is_featured": False,
    "created_at": "2026-03-20T11:00:00Z",
    "updated_at": "2026-03-21T09:20:00Z",
}

FEED_SEARCH_EXAMPLE = {
    "source_id": "gh_search_1",
    "faker_id": "MzI3NjQ4NTY=",
    "biz": "MzI3NjQ4NTY=",
    "mp_name": "AI Weekly",
    "mp_cover": "https://example.com/search-cover.png",
    "mp_intro": "Weekly insights about AI products.",
}

FEED_ARTICLE_CLEAR_EXAMPLE = {
    "feed_id": 1,
    "deleted_count": 12,
}

FEED_SYNC_TASK_EXAMPLE = {
    "id": 101,
    "task_type": "feed_sync",
    "status": "success",
    "task_key": "feed_sync:1",
    "target_type": "feed",
    "target_id": 1,
    "message": "Feed sync complete",
    "request_payload": {"feed_id": 1},
    "result_payload": {
        "fetched_count": 3,
        "detail_success_count": 2,
        "detail_failed_count": 1,
        "errors": [
            {
                "source_id": "article-3",
                "url": "https://mp.weixin.qq.com/s/article-3?__biz=Qkl6&mid=1&idx=3&sn=ghi",
                "error": "WeChat article detail fetch failed.",
            }
        ],
    },
    "feed_id": 1,
    "article_ids": [11, 12, 13],
    "article_count": 3,
    "detail_success_count": 2,
    "detail_failed_count": 1,
    "failed_articles": [
        {
            "source_id": "article-3",
            "url": "https://mp.weixin.qq.com/s/article-3?__biz=Qkl6&mid=1&idx=3&sn=ghi",
            "error": "WeChat article detail fetch failed.",
        }
    ],
    "celery_task_id": "6ec3c8a2-e570-4bd8-9031-53d5976fb415",
    "started_at": "2026-03-21T09:20:00Z",
    "finished_at": "2026-03-21T09:20:08Z",
    "created_at": "2026-03-21T09:20:00Z",
    "updated_at": "2026-03-21T09:20:08Z",
}

FEED_SYNC_TASK_FAILED_EXAMPLE = {
    "id": 102,
    "task_type": "feed_sync",
    "status": "failed",
    "task_key": "feed_sync:1",
    "target_type": "feed",
    "target_id": 1,
    "message": "Feed sync failed: WeChat rate limit triggered",
    "request_payload": {"feed_id": 1},
    "result_payload": {
        "feed_id": 1,
        "task_type": "feed_sync",
        "error": "WeChat rate limit triggered",
    },
    "celery_task_id": "34e4eb4f-505c-4e8a-86ae-24f614e9f5c1",
    "started_at": "2026-03-21T09:25:00Z",
    "finished_at": "2026-03-21T09:25:02Z",
    "created_at": "2026-03-21T09:25:00Z",
    "updated_at": "2026-03-21T09:25:02Z",
}

ARTICLE_IMPORT_TASK_EXAMPLE = {
    "id": 103,
    "task_type": "article_import",
    "status": "success",
    "task_key": "article_import:https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc",
    "target_type": "article",
    "target_id": 1,
    "message": "Article import complete",
    "request_payload": {
        "url": "https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc",
    },
    "result_payload": {
        "article_id": 1,
        "feed_id": 1,
        "message": "Article import complete",
    },
    "celery_task_id": "52f577bc-1be3-423f-a79f-f48db2d938df",
    "started_at": "2026-03-21T09:30:00Z",
    "finished_at": "2026-03-21T09:30:03Z",
    "created_at": "2026-03-21T09:30:00Z",
    "updated_at": "2026-03-21T09:30:03Z",
}

ARTICLE_REFRESH_TASK_EXAMPLE = {
    "id": 104,
    "task_type": "article_refresh",
    "status": "success",
    "task_key": "article_refresh:1",
    "target_type": "article",
    "target_id": 1,
    "message": "Article refresh complete",
    "request_payload": {"article_id": 1},
    "result_payload": {
        "article_id": 1,
        "message": "Article refresh complete",
        "read_num": 101,
        "comment_total_count": 15,
    },
    "celery_task_id": "23173654-7d9a-4b62-a916-251c17f7ff7b",
    "started_at": "2026-03-21T09:35:00Z",
    "finished_at": "2026-03-21T09:35:04Z",
    "created_at": "2026-03-21T09:35:00Z",
    "updated_at": "2026-03-21T09:35:04Z",
}

CREDENTIAL_LOGIN_TASK_FAILED_EXAMPLE = {
    "id": 105,
    "task_type": "credential_login",
    "status": "failed",
    "task_key": "",
    "target_type": "login_session",
    "target_id": 301,
    "message": "Credential login failed: WeChat rejected the QR login.",
    "request_payload": {"session_id": "session-fail-1"},
    "result_payload": {
        "session_id": "session-fail-1",
        "task_type": "credential_login",
        "status": "failed",
        "error": "WeChat rejected the QR login.",
    },
    "celery_task_id": "9cfcb5c4-91f8-4144-94a1-bdb401330091",
    "started_at": "2026-03-21T09:40:00Z",
    "finished_at": "2026-03-21T09:40:03Z",
    "created_at": "2026-03-21T09:40:00Z",
    "updated_at": "2026-03-21T09:40:03Z",
}

ARTICLE_IMPORT_TASK_FAILED_EXAMPLE = {
    "id": 106,
    "task_type": "article_import",
    "status": "failed",
    "task_key": "article_import:https://mp.weixin.qq.com/s/import-fail",
    "target_type": "article",
    "target_id": None,
    "message": "Article import failed: WeChat import blocked by anti-bot",
    "request_payload": {"url": "https://mp.weixin.qq.com/s/import-fail"},
    "result_payload": {
        "task_type": "article_import",
        "url": "https://mp.weixin.qq.com/s/import-fail",
        "error": "WeChat import blocked by anti-bot",
    },
    "celery_task_id": "8617396d-8d65-4fe9-94ef-0d7f1803e688",
    "started_at": "2026-03-21T09:45:00Z",
    "finished_at": "2026-03-21T09:45:01Z",
    "created_at": "2026-03-21T09:45:00Z",
    "updated_at": "2026-03-21T09:45:01Z",
}

ARTICLE_REFRESH_TASK_FAILED_EXAMPLE = {
    "id": 107,
    "task_type": "article_refresh",
    "status": "failed",
    "task_key": "",
    "target_type": "article",
    "target_id": 1,
    "message": "Article refresh failed: WeChat refresh blocked by anti-bot",
    "request_payload": {"article_id": 1},
    "result_payload": {
        "task_type": "article_refresh",
        "article_id": 1,
        "error": "WeChat refresh blocked by anti-bot",
    },
    "celery_task_id": "bf7ad15d-a7df-4ffa-b89c-78ca6a5d9806",
    "started_at": "2026-03-21T09:50:00Z",
    "finished_at": "2026-03-21T09:50:02Z",
    "created_at": "2026-03-21T09:50:00Z",
    "updated_at": "2026-03-21T09:50:02Z",
}

ARTICLE_EXAMPLE = {
    "id": 1,
    "feed_id": 1,
    "source_id": "article-1",
    "article_type": "news",
    "title": "Imported Article",
    "description": "Imported description",
    "content": "<p>Imported content</p>",
    "url": "https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc",
    "pic_url": "https://example.com/article-cover.png",
    "publish_time": "2026-03-20T12:00:00Z",
    "status": "active",
    "is_read": False,
    "is_favorite": False,
    "last_refreshed_at": "2026-03-21T09:30:00Z",
    "read_num": 101,
    "like_num": 51,
    "old_like_num": 21,
    "share_num": 11,
    "collect_num": 9,
    "comment_count": 7,
    "comment_reply_count": 8,
    "comment_total_count": 15,
    "created_at": "2026-03-20T12:00:00Z",
    "updated_at": "2026-03-21T09:30:00Z",
}

TENANT_RSS_XML_EXAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Tenant A We RSS</title>
    <link>https://example.com/api/v1/we-rss/rss/</link>
    <description>Tenant scoped WeChat article feed.</description>
    <item>
      <title>Imported Article</title>
      <link>https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&amp;mid=1&amp;idx=1&amp;sn=abc</link>
      <description>Imported description</description>
    </item>
  </channel>
</rss>"""

FEED_RSS_XML_EXAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>AI Daily</title>
    <link>https://example.com/api/v1/we-rss/rss/1/</link>
    <description>RSS feed for a single WeChat public account.</description>
    <item>
      <title>Imported Article</title>
      <link>https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&amp;mid=1&amp;idx=1&amp;sn=abc</link>
      <description>Imported description</description>
    </item>
  </channel>
</rss>"""

ARTICLE_HTML_EXAMPLE = """<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <title>Imported Article</title>
  </head>
  <body>
    <article>
      <h1>Imported Article</h1>
      <p>Imported description</p>
      <div><p>Imported content</p></div>
    </article>
  </body>
</html>"""
