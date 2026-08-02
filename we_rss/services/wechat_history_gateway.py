"""
wechat_history_gateway.py
--------------------------
Django 侧网关，封装对微信公众号历史文章接口的调用。

与 WechatFeedGateway 平行，提供对齐的 collect_feed_batch() 接口，
让 FeedService.execute_history_sync_batch_inline() 可以直接复用
_apply_sync_scope_to_batch / _upsert_articles / _apply_feed_sync_updates 等静态方法。

凭证来源：scripts/lipeaks_viral_articles/output/wechat-stats/session.json
"""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Dict, Optional

from rest_framework.exceptions import ValidationError

from scripts.lipeaks_viral_articles.scripts.wechat_fetch_history import (
    DEFAULT_SESSION_FILE,
    fetch_history_batch,
    load_session_file,
)

logger = logging.getLogger(__name__)

# 每批次内的翻页节流（秒），避免请求过于密集触发微信风控
_DEFAULT_SLEEP_SECONDS = 2.0

# profile_ext 接口单页上限
_PAGE_COUNT = 10


class WechatHistoryGateway:
    """
    从微信公众号历史消息接口（profile_ext?action=getmsg）拉取文章。

    提供与 WechatFeedGateway 对齐的 collect_feed_batch() 接口，
    使 FeedService 的批次同步逻辑可以无缝复用。
    """

    def __init__(
        self,
        *,
        session_file: Optional[Path] = None,
        sleep_seconds: float = _DEFAULT_SLEEP_SECONDS,
        sleep_func=None,
        request_timeout: int = 30,
    ):
        self._session_file = session_file or DEFAULT_SESSION_FILE
        self._sleep_seconds = sleep_seconds
        self._sleep_func = sleep_func or time.sleep
        self._request_timeout = request_timeout

    # ------------------------------------------------------------------
    # Runtime 检查
    # ------------------------------------------------------------------

    def ensure_runtime_ready(self) -> None:
        """
        检查 session.json 是否存在且包含有效凭证。
        不满足时抛 ValidationError，与 ArticleStatsRefreshService.ensure_stats_runtime_ready() 保持相同风格。
        """
        if not self._session_file.exists():
            raise ValidationError(
                f"WeChat history sync runtime is not ready. "
                f"Missing: {self._session_file.name}. "
                f"Please open any WeChat article in the WeChat client to refresh the session."
            )
        session = load_session_file(self._session_file)
        if not session.get("key") or not session.get("uin"):
            raise ValidationError(
                f"WeChat history sync runtime is not ready. "
                f"{self._session_file.name} exists but is missing required fields (key, uin). "
                f"Please open any WeChat article in the WeChat client to refresh the session."
            )

    # ------------------------------------------------------------------
    # 公开接口：对齐 WechatFeedGateway.collect_feed_batch() 的签名
    # ------------------------------------------------------------------

    def collect_feed_batch(
        self,
        feed,
        credential=None,  # noqa: 兼容签名，历史接口不使用 credential
        *,
        begin: int = 0,
        batch_size: int = 20,
        deadline_at=None,
    ) -> Dict:
        """
        拉取公众号历史文章的一个 batch（最多 batch_size 篇）。

        :param feed:       WechatFeed 实例，必须有 biz 字段
        :param credential: 兼容参数，历史接口不使用，忽略即可
        :param begin:      翻页偏移量（对应 profile_ext 的 offset 参数）
        :param batch_size: 本批次最多返回的文章数量
        :param deadline_at: 超时截止时间（datetime），超时后提前返回已拉到的数据
        :return: 与 WechatFeedGateway.collect_feed_batch() 完全对齐的字典结构
        """
        from django.utils import timezone  # 延迟导入，避免模块级 Django 初始化问题

        biz = str(getattr(feed, "biz", "") or "").strip()
        if not biz:
            raise ValidationError(
                f"Feed (id={getattr(feed, 'id', '?')}) is missing the `biz` field. "
                f"Cannot fetch history articles without a valid __biz."
            )

        session = load_session_file(self._session_file)
        if not session.get("key") or not session.get("uin"):
            raise ValidationError(
                f"WeChat history sync runtime is not ready. "
                f"{self._session_file.name} is missing required fields (key, uin). "
                f"Please open any WeChat article in the WeChat client to refresh the session."
            )

        articles = []
        current_offset = begin
        has_more = True
        ret = 0
        errmsg = ""
        is_first_page = True

        while has_more and len(articles) < batch_size:
            # 超时检查
            if deadline_at is not None and timezone.now() >= deadline_at:
                logger.warning(
                    "WechatHistoryGateway.collect_feed_batch: deadline exceeded at offset=%d, feed_id=%s",
                    current_offset,
                    getattr(feed, "id", "?"),
                )
                break

            # 节流：第一页不等待
            sleep_fn = self._sleep_func
            page_result = fetch_history_batch(
                biz=biz,
                session=session,
                offset=current_offset,
                count=_PAGE_COUNT,
                timeout=self._request_timeout,
                sleep_seconds=0 if is_first_page else self._sleep_seconds,
                _sleep_func=sleep_fn,
            )
            is_first_page = False

            ret = page_result["ret"]
            errmsg = page_result["errmsg"]

            if ret != 0:
                logger.warning(
                    "WechatHistoryGateway.collect_feed_batch: API returned ret=%d errmsg=%s, feed_id=%s offset=%d",
                    ret, errmsg, getattr(feed, "id", "?"), current_offset,
                )
                # 非 0 ret 时停止本批次，不抛异常（交由上层决策）
                has_more = False
                break

            page_articles = page_result["articles"]
            articles.extend(page_articles)
            has_more = page_result["has_more"]
            current_offset = page_result["next_offset"]

            # 已经凑够 batch_size 条，提前结束本批次
            if len(articles) >= batch_size:
                break

        # 超出 batch_size 的部分截断，next_begin 记录截断点
        # 以便下一批次从正确的 offset 继续
        if len(articles) > batch_size:
            articles = articles[:batch_size]

        # 构建与 WechatFeedGateway.collect_feed_batch() 完全一致的返回结构
        feed_payload = {
            "biz": biz,
            "mp_name": getattr(feed, "mp_name", "") or "",
            "mp_cover": getattr(feed, "mp_cover", "") or "",
        }

        logger.info(
            "WechatHistoryGateway.collect_feed_batch: fetched %d articles, has_more=%s, "
            "begin=%d, next_begin=%d, feed_id=%s, biz=%s",
            len(articles), has_more, begin, current_offset,
            getattr(feed, "id", "?"), biz,
        )

        return {
            "articles": articles,
            "feed_payload": feed_payload,
            "failed_articles": [],
            "has_more": has_more,
            "next_begin": current_offset,
            "detail_success_count": len(articles),
            "detail_failed_count": 0,
            "errors": [],
            # 额外字段：透传接口原始状态码，方便调试
            "_history_ret": ret,
            "_history_errmsg": errmsg,
        }
