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
                media_type="text/markdown",
                status_codes=[str(status_code)],
            )
        ],
    )


def csv_response(description, example_csv, *, example_name, status_code=200):
    return OpenApiResponse(
        response=OpenApiTypes.STR,
        description=description,
        examples=[
            OpenApiExample(
                name=example_name,
                value=example_csv,
                response_only=True,
                media_type="text/csv",
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
RSS_TAG_ID_PARAMETER = path_int_parameter("tag_id", "Member private tag ID for RSS output.", 1)
TAG_ID_PARAMETER = path_int_parameter("id", "Member private tag ID.", 1)
SEO_KEYWORD_ID_PARAMETER = path_int_parameter("id", "Member SEO keyword ID.", 1)
MEMBER_ID_QUERY_PARAMETER = OpenApiParameter(
    name="member_id",
    type=OpenApiTypes.INT,
    location=OpenApiParameter.QUERY,
    required=True,
    description="Explicit member scope for SEO keyword operations.",
    examples=[OpenApiExample("Member id query example", value=1)],
)
SEO_KEYWORD_SEARCH_PARAMETER = OpenApiParameter(
    name="search",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Case-insensitive keyword text search within one member scope.",
    examples=[OpenApiExample("SEO keyword search example", value="weight")],
)
SEO_KEYWORD_TAG_ID_PARAMETER = OpenApiParameter(
    name="tag_id",
    type=OpenApiTypes.INT,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Filter SEO keywords linked to one member-owned tag.",
    examples=[OpenApiExample("SEO keyword tag filter example", value=1)],
)

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

ARTICLE_PUBLIC_SEARCH_QUERY_PARAMETER = OpenApiParameter(
    name="query",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=True,
    description="Keyword used to search public WeChat articles through the native Sogou Weixin search service.",
    examples=[OpenApiExample("Article search query example", value="AI Agent")],
)

ARTICLE_PUBLIC_SEARCH_LIMIT_PARAMETER = OpenApiParameter(
    name="limit",
    type=OpenApiTypes.INT,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Maximum number of article results to return. Defaults to 10 and cannot exceed 50.",
    examples=[OpenApiExample("Article search limit example", value=10)],
)


ARTICLE_TYPE_PARAMETER = OpenApiParameter(
    name="article_type",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Filter articles by article type. Supported values: `news`, `newspic`.",
    examples=[OpenApiExample("Article type example", value="newspic")],
)

ARTICLE_SEARCH_PARAMETER = OpenApiParameter(
    name="search",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Search article titles using the same splitting rules as we-mp-rss-main.",
    examples=[OpenApiExample("Article search example", value="Alpha|Beta-Gamma")],
)

ARTICLE_FAVORITE_ONLY_PARAMETER = OpenApiParameter(
    name="favorite_only",
    type=OpenApiTypes.BOOL,
    location=OpenApiParameter.QUERY,
    required=False,
    description="When true, return only the current member's favorite articles.",
    examples=[OpenApiExample("Article favorite only example", value=True)],
)

ARTICLE_FEED_ID_PARAMETER = OpenApiParameter(
    name="feed_id",
    type=OpenApiTypes.INT,
    location=OpenApiParameter.QUERY,
    required=False,
    description=(
        "Filter articles by one feed ID. "
        "When provided, the result returns all tenant articles under that feed except the current member's hidden "
        "articles, even when the member is not subscribed to the feed."
    ),
    examples=[OpenApiExample("Article feed id example", value=1)],
)

FEED_SUBSCRIBED_ONLY_PARAMETER = OpenApiParameter(
    name="subscribed_only",
    type=OpenApiTypes.BOOL,
    location=OpenApiParameter.QUERY,
    required=False,
    description="When true, return only the feeds subscribed by the current member.",
    examples=[OpenApiExample("Feed subscribed only example", value=True)],
)

TAG_IDS_PARAMETER = OpenApiParameter(
    name="tag_ids",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Comma-separated member tag IDs. Multiple IDs use AND semantics.",
    examples=[OpenApiExample("Tag ids example", value="1,2,3")],
)

ARTICLE_SORT_BY_PARAMETER = OpenApiParameter(
    name="sort_by",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description=(
        "Sort visible articles by one supported field. Supported values: `read_num`, `publish_time`, "
        "`old_like_num`, `collect_num`, `share_num`, `comment_total_count`."
    ),
    examples=[OpenApiExample("Article sort by example", value="read_num")],
)

ARTICLE_SORT_ORDER_PARAMETER = OpenApiParameter(
    name="sort_order",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description="Article sort direction. Supported values: `asc`, `desc`. Defaults to `desc`.",
    examples=[OpenApiExample("Article sort order example", value="desc")],
)

# Override legacy task parameter docs with the batched feed-sync vocabulary.
TASK_TYPE_PARAMETER = OpenApiParameter(
    name="task_type",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description=(
        "按任务类型过滤，可选值包括 `credential_login`、`feed_sync_run`、"
        "`feed_sync_batch`、`feed_content_refresh`、`article_import`、`article_refresh`、"
        "`article_stats_refresh`。"
    ),
    examples=[OpenApiExample("Task type example", value="feed_sync_run")],
)
TASK_STATUS_PARAMETER = OpenApiParameter(
    name="status",
    type=OpenApiTypes.STR,
    location=OpenApiParameter.QUERY,
    required=False,
    description="按任务状态过滤，可选值包括 `pending`、`running`、`success`、`partial_success`、`timed_out`、`failed`。",
    examples=[OpenApiExample("Task status example", value="failed")],
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
    "is_subscribed": False,
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

FEED_SYNC_REQUEST_FULL_EXAMPLE = {
    "sync_scope": "full",
    "refresh_markdown": False,
}

FEED_SYNC_REQUEST_LATEST_EXAMPLE = {
    "sync_scope": "latest",
    "refresh_markdown": False,
}

FEED_SYNC_REQUEST_WINDOW_EXAMPLE = {
    "sync_scope": "window",
    "window_days": 7,
    "refresh_markdown": False,
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

# Override legacy feed-sync examples with the batched parent-task contract.
FEED_SYNC_TASK_EXAMPLE = {
    "id": 101,
    "task_type": "feed_sync_run",
    "status": "running",
    "task_key": "",
    "target_type": "feed",
    "target_id": 1,
    "message": "A feed sync task is already running.",
    "request_payload": {
        "feed_id": 1,
        "batch_size": 20,
        "poll_after_seconds": 5,
        "sync_scope": "full",
        "window_days": None,
        "refresh_markdown": False,
    },
    "result_payload": {
        "run_status": "running",
        "feed_id": 1,
        "batch_size": 20,
        "poll_after_seconds": 5,
        "sync_scope": "full",
        "window_days": None,
        "refresh_markdown": False,
        "has_more": True,
        "next_begin": 20,
        "batches_completed": 1,
        "batches_failed": 0,
        "articles_synced": 20,
        "articles_failed": 0,
        "article_ids": [11, 12, 13],
        "current_batch_task_id": 202,
        "latest_completed_batch": {
            "batch_no": 1,
            "begin": 0,
            "end": 20,
            "has_more": True,
            "article_count": 20,
            "article_ids": [11, 12, 13],
            "articles": [
                {
                    "id": 11,
                    "source_id": "article-1",
                    "title": "Imported Article 1",
                    "url": "https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc",
                    "publish_time": "2026-03-20T12:00:00Z",
                    "pic_url": "https://example.com/article-cover-1.png",
                    "status": "active",
                }
            ],
            "failed_articles": [],
            "started_at": "2026-03-21T09:20:00Z",
            "finished_at": "2026-03-21T09:20:08Z",
        },
        "last_progress_at": "2026-03-21T09:20:08Z",
        "timeout_reason": "",
        "stop_reason": "",
        "stop_article_url": "",
        "stop_article_source_id": "",
        "stop_publish_time": None,
    },
    "celery_task_id": "",
    "started_at": "2026-03-21T09:20:00Z",
    "finished_at": None,
    "created_at": "2026-03-21T09:20:00Z",
    "updated_at": "2026-03-21T09:20:08Z",
}

FEED_SYNC_TASK_SUCCESS_EXAMPLE = {
    "id": 101,
    "task_type": "feed_sync_run",
    "status": "success",
    "task_key": "",
    "target_type": "feed",
    "target_id": 1,
    "message": "Feed sync complete",
    "request_payload": {
        "feed_id": 1,
        "batch_size": 20,
        "poll_after_seconds": 5,
        "sync_scope": "full",
        "window_days": None,
        "refresh_markdown": False,
    },
    "result_payload": {
        "run_status": "success",
        "feed_id": 1,
        "batch_size": 20,
        "poll_after_seconds": 5,
        "sync_scope": "full",
        "window_days": None,
        "refresh_markdown": False,
        "has_more": False,
        "next_begin": 27,
        "batches_completed": 2,
        "batches_failed": 0,
        "articles_synced": 27,
        "articles_failed": 0,
        "article_ids": [11, 12, 13],
        "current_batch_task_id": None,
        "latest_completed_batch": {
            "batch_no": 2,
            "begin": 20,
            "end": 27,
            "has_more": False,
            "article_count": 7,
            "article_ids": [31, 32, 33],
            "articles": [
                {
                    "id": 31,
                    "source_id": "article-21",
                    "title": "Imported Article 21",
                    "url": "https://mp.weixin.qq.com/s/article-21?__biz=Qkl6&mid=1&idx=21&sn=abc",
                    "publish_time": "2026-03-21T12:00:00Z",
                    "pic_url": "https://example.com/article-cover-21.png",
                    "status": "active",
                }
            ],
            "failed_articles": [],
            "started_at": "2026-03-21T09:20:09Z",
            "finished_at": "2026-03-21T09:20:14Z",
        },
        "last_progress_at": "2026-03-21T09:20:14Z",
        "timeout_reason": "",
        "stop_reason": "",
        "stop_article_url": "",
        "stop_article_source_id": "",
        "stop_publish_time": None,
    },
    "celery_task_id": "",
    "started_at": "2026-03-21T09:20:00Z",
    "finished_at": "2026-03-21T09:20:14Z",
    "created_at": "2026-03-21T09:20:00Z",
    "updated_at": "2026-03-21T09:20:14Z",
}

FEED_SYNC_TASK_PARTIAL_SUCCESS_EXAMPLE = {
    "id": 102,
    "task_type": "feed_sync_run",
    "status": "partial_success",
    "task_key": "",
    "target_type": "feed",
    "target_id": 1,
    "message": "Feed sync partially completed before timing out.",
    "request_payload": {
        "feed_id": 1,
        "batch_size": 20,
        "poll_after_seconds": 5,
        "sync_scope": "full",
        "window_days": None,
        "refresh_markdown": False,
    },
    "result_payload": {
        "run_status": "partial_success",
        "feed_id": 1,
        "batch_size": 20,
        "poll_after_seconds": 5,
        "sync_scope": "full",
        "window_days": None,
        "refresh_markdown": False,
        "has_more": True,
        "next_begin": 20,
        "batches_completed": 1,
        "batches_failed": 1,
        "articles_synced": 20,
        "articles_failed": 0,
        "article_ids": [11, 12, 13],
        "current_batch_task_id": 203,
        "latest_completed_batch": {
            "batch_no": 1,
            "begin": 0,
            "end": 20,
            "has_more": True,
            "article_count": 20,
            "article_ids": [11, 12, 13],
            "articles": [
                {
                    "id": 11,
                    "source_id": "article-1",
                    "title": "Imported Article 1",
                    "url": "https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc",
                    "publish_time": "2026-03-20T12:00:00Z",
                    "pic_url": "https://example.com/article-cover-1.png",
                    "status": "active",
                }
            ],
            "failed_articles": [],
            "started_at": "2026-03-21T09:20:00Z",
            "finished_at": "2026-03-21T09:20:08Z",
        },
        "last_progress_at": "2026-03-21T09:21:38Z",
        "timeout_reason": "batch_timeout",
        "stop_reason": "",
        "stop_article_url": "",
        "stop_article_source_id": "",
        "stop_publish_time": None,
    },
    "celery_task_id": "",
    "started_at": "2026-03-21T09:20:00Z",
    "finished_at": "2026-03-21T09:21:38Z",
    "created_at": "2026-03-21T09:20:00Z",
    "updated_at": "2026-03-21T09:21:38Z",
}

FEED_SYNC_TASK_FAILED_EXAMPLE = {
    "id": 103,
    "task_type": "feed_sync_run",
    "status": "failed",
    "task_key": "",
    "target_type": "feed",
    "target_id": 1,
    "message": "Feed sync failed: WeChat rate limit triggered",
    "request_payload": {
        "feed_id": 1,
        "batch_size": 20,
        "poll_after_seconds": 5,
        "sync_scope": "full",
        "window_days": None,
        "refresh_markdown": False,
    },
    "result_payload": {
        "run_status": "failed",
        "feed_id": 1,
        "batch_size": 20,
        "poll_after_seconds": 5,
        "sync_scope": "full",
        "window_days": None,
        "refresh_markdown": False,
        "has_more": False,
        "next_begin": 0,
        "batches_completed": 0,
        "batches_failed": 1,
        "articles_synced": 0,
        "articles_failed": 0,
        "article_ids": [],
        "current_batch_task_id": 204,
        "latest_completed_batch": None,
        "last_progress_at": "2026-03-21T09:25:02Z",
        "timeout_reason": "",
        "stop_reason": "",
        "stop_article_url": "",
        "stop_article_source_id": "",
        "stop_publish_time": None,
        "error": "WeChat rate limit triggered",
    },
    "celery_task_id": "",
    "started_at": "2026-03-21T09:25:00Z",
    "finished_at": "2026-03-21T09:25:02Z",
    "created_at": "2026-03-21T09:25:00Z",
    "updated_at": "2026-03-21T09:25:02Z",
}

FEED_SYNC_TASK_TIMED_OUT_EXAMPLE = {
    "id": 104,
    "task_type": "feed_sync_run",
    "status": "timed_out",
    "task_key": "",
    "target_type": "feed",
    "target_id": 1,
    "message": "Feed sync timed out before any batch completed.",
    "request_payload": {
        "feed_id": 1,
        "batch_size": 20,
        "poll_after_seconds": 5,
        "sync_scope": "full",
        "window_days": None,
        "refresh_markdown": False,
    },
    "result_payload": {
        "run_status": "timed_out",
        "feed_id": 1,
        "batch_size": 20,
        "poll_after_seconds": 5,
        "sync_scope": "full",
        "window_days": None,
        "refresh_markdown": False,
        "has_more": True,
        "next_begin": 0,
        "batches_completed": 0,
        "batches_failed": 1,
        "articles_synced": 0,
        "articles_failed": 0,
        "article_ids": [],
        "current_batch_task_id": 205,
        "latest_completed_batch": None,
        "last_progress_at": "2026-03-21T09:25:30Z",
        "timeout_reason": "batch_timeout",
        "stop_reason": "",
        "stop_article_url": "",
        "stop_article_source_id": "",
        "stop_publish_time": None,
    },
    "celery_task_id": "",
    "started_at": "2026-03-21T09:25:00Z",
    "finished_at": "2026-03-21T09:25:30Z",
    "created_at": "2026-03-21T09:25:00Z",
    "updated_at": "2026-03-21T09:25:30Z",
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

FEED_CONTENT_REFRESH_TASK_EXAMPLE = {
    "id": 109,
    "task_type": "feed_content_refresh",
    "status": "success",
    "task_key": "feed_content_refresh:2",
    "target_type": "feed",
    "target_id": 2,
    "message": "Feed content refresh complete",
    "request_payload": {
        "feed_id": 2,
        "article_ids": [11, 12, 13],
    },
    "result_payload": {
        "task_type": "feed_content_refresh",
        "feed_id": 2,
        "requested_count": 3,
        "success_count": 2,
        "failed_count": 1,
        "article_ids": [11, 12, 13],
        "failed_articles": [
            {
                "article_id": 13,
                "url": "https://mp.weixin.qq.com/s/article-13",
                "error": "markdown blocked",
            }
        ],
    },
    "celery_task_id": "b8bf05b5-fb7f-43c7-83de-d5f8b4af9658",
    "started_at": "2026-03-21T09:36:00Z",
    "finished_at": "2026-03-21T09:36:08Z",
    "created_at": "2026-03-21T09:36:00Z",
    "updated_at": "2026-03-21T09:36:08Z",
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

ARTICLE_EXPORT_REQUEST_ARTICLE_IDS_EXAMPLE = {
    "article_ids": [11, 12, 13],
}

ARTICLE_BATCH_DELETE_REQUEST_EXAMPLE = {
    "article_ids": [11, 12, 13],
}

ARTICLE_BATCH_DELETE_RESPONSE_EXAMPLE = {
    "deleted_count": 3,
    "article_ids": [11, 12, 13],
}

ARTICLE_EXPORT_REQUEST_MEMBER_EXAMPLE = {
    "member_id": 5,
}

ARTICLE_EXPORT_REQUEST_FEED_EXAMPLE = {
    "feed_id": 2,
}

ARTICLE_STATS_REFRESH_BY_URL_REQUEST_EXAMPLE = {
    "url": "https://mp.weixin.qq.com/s/article-1?token=123456",
}

ARTICLE_STATS_BATCH_REFRESH_REQUEST_ARTICLE_IDS_EXAMPLE = {
    "article_ids": [11, 12, 13],
}

ARTICLE_STATS_BATCH_REFRESH_REQUEST_FEED_EXAMPLE = {
    "feed_id": 2,
}

ARTICLE_STATS_BATCH_REFRESH_REQUEST_MEMBER_EXAMPLE = {
    "member_id": 5,
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

ARTICLE_STATS_REFRESH_TASK_EXAMPLE = {
    "id": 108,
    "task_type": "article_stats_refresh",
    "status": "success",
    "task_key": "article_stats_refresh:feed:2",
    "target_type": "article_stats",
    "target_id": None,
    "message": "Article stats refresh complete",
    "request_payload": {
        "article_ids": [11, 12, 13],
        "feed_id": 2,
        "member_id": None,
    },
    "result_payload": {
        "task_type": "article_stats_refresh",
        "selector_type": "feed_id",
        "requested_count": 3,
        "success_count": 2,
        "failed_count": 1,
        "article_ids": [11, 12, 13],
        "failed_articles": [
            {
                "article_id": 13,
                "url": "https://mp.weixin.qq.com/s/article-13",
                "error": "stats blocked",
            }
        ],
    },
    "celery_task_id": "c7c84d64-5834-4a5a-8334-37d70ad43ca6",
    "started_at": "2026-03-21T10:00:00Z",
    "finished_at": "2026-03-21T10:00:05Z",
    "created_at": "2026-03-21T10:00:00Z",
    "updated_at": "2026-03-21T10:00:05Z",
}

ARTICLE_EXAMPLE = {
    "id": 1,
    "feed_id": 1,
    "source_id": "article-1",
    "article_type": "news",
    "title": "Imported Article",
    "description": "Imported description",
    "content": "# Imported Article\n\nImported content",
    "url": "https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc",
    "pic_url": "https://example.com/article-cover.png",
    "publish_time": "2026-03-20T12:00:00Z",
    "status": "active",
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

WECHAT_ARTICLE_SEARCH_ITEM_EXAMPLE = {
    "title": "AI Agent 实战",
    "url": "https://mp.weixin.qq.com/s/agent-1",
    "summary": "AI Agent related article summary text.",
    "datetime": "2026-04-10 10:00:00",
    "date_text": "2026年04月10日",
    "date_description": "今天",
    "source": "OpenAI",
}

WECHAT_ARTICLE_SEARCH_RESPONSE_EXAMPLE = {
    "query": "AI Agent",
    "total": 1,
    "items": [WECHAT_ARTICLE_SEARCH_ITEM_EXAMPLE],
}

MARKDOWN_FORMAT_REQUEST_EXAMPLE = {
    "content": "# Title\nBody",
    "mode": "gentle",
}

MARKDOWN_FORMAT_RESPONSE_EXAMPLE = {
    "formatted_markdown": "# Title\n\nBody",
    "mode": "gentle",
    "executor": "codex",
}

MEMBER_TAG_EXAMPLE = {
    "id": 1,
    "name": "AI",
    "color": "#008000",
    "description": "Interesting reads",
    "sort_order": 10,
    "is_pinned": True,
    "feed_count": 2,
    "article_count": 3,
    "created_at": "2026-03-20T12:00:00Z",
    "updated_at": "2026-03-21T09:30:00Z",
}

SEO_KEYWORD_EXAMPLE = {
    "id": 1,
    "member_id": 1,
    "keyword": "weight loss recipes",
    "search_index": 6800,
    "tag_ids": [1, 2],
    "tags": [
        {
            "id": 1,
            "name": "Weight Loss",
            "color": "#008000",
            "sort_order": 0,
        },
        {
            "id": 2,
            "name": "Recipes",
            "color": "#FF8800",
            "sort_order": 10,
        },
    ],
    "created_at": "2026-04-05T10:00:00Z",
    "updated_at": "2026-04-05T10:00:00Z",
}

SEO_KEYWORD_WRITE_EXAMPLE = {
    "member_id": 1,
    "keyword": "weight loss recipes",
    "search_index": 6800,
    "tag_ids": [1, 2],
}

SEO_KEYWORD_DELETE_EXAMPLE = {
    "member_id": 1,
}

TAG_RELATION_WRITE_EXAMPLE = {
    "tag_ids": [1, 2, 3],
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

TAG_RSS_XML_EXAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>AI We RSS</title>
    <link>https://example.com/api/v1/we-rss/rss/tags/1/</link>
    <description>RSS feed for one member-private tag.</description>
    <item>
      <title>Imported Article</title>
      <link>https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&amp;mid=1&amp;idx=1&amp;sn=abc</link>
      <description>Imported description</description>
    </item>
  </channel>
</rss>"""

ARTICLE_HTML_EXAMPLE = """# Imported Article

> 公众号: AI Daily

---

Imported content"""

ARTICLE_EXPORT_CSV_EXAMPLE = """article_id,feed_id,feed_name,feed_source_id,source_id,article_type,title,description,content,url,pic_url,publish_time,status,read_num,like_num,old_like_num,share_num,collect_num,comment_count,comment_reply_count,comment_total_count,last_refreshed_at,created_at,updated_at
1,1,AI Daily,gh_abcdef123456,article-1,news,Imported Article,Imported description,# Imported Article,https://mp.weixin.qq.com/s/article-1?__biz=Qkl6&mid=1&idx=1&sn=abc,https://example.com/article-cover.png,2026-03-20T12:00:00Z,active,101,51,21,11,9,7,8,15,2026-03-21T09:30:00Z,2026-03-20T12:00:00Z,2026-03-21T09:30:00Z"""
