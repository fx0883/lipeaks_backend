"""
文章媒体资源清理工具
用于物理删除文章时，安全清理关联的封面图、缩略图及正文中引用的本地媒体文件
支持事务提交后回调（transaction.on_commit），保障 ACID 一致性与防误删安全
"""
import os
import re
import logging
from urllib.parse import urlparse
from django.conf import settings
from django.db import models, transaction

logger = logging.getLogger(__name__)


def get_media_absolute_path(url_or_path: str) -> str | None:
    """
    将图片 URL 或相对路径解析为服务器磁盘上的绝对路径，并进行安全验证。
    """
    if not url_or_path or not isinstance(url_or_path, str):
        return None

    # 解析 URL 路径部分，去除 query 参数或 hash
    if url_or_path.startswith(('http://', 'https://')):
        parsed = urlparse(url_or_path)
        path = parsed.path
    else:
        path = url_or_path.split('?')[0].split('#')[0]

    path = path.strip().lstrip('/')

    # 提取相对子路径
    if path.startswith('media/'):
        rel_sub = path[len('media/'):]
    elif '/media/' in path:
        rel_sub = path.split('/media/', 1)[1]
    elif path.startswith('uploads/'):
        rel_sub = path
    else:
        return None

    media_root = os.path.abspath(settings.MEDIA_ROOT)
    full_path = os.path.abspath(os.path.join(media_root, rel_sub))

    # 安全检查：必须在 MEDIA_ROOT 目录内，且不能是 MEDIA_ROOT 本身
    if full_path.startswith(media_root) and full_path != media_root:
        return full_path

    return None


def extract_media_urls_from_content(content: str) -> list[str]:
    """
    从文章正文内容中提取所有可能引用的本地媒体资源 URL/路径
    支持 Markdown 图片语法与 HTML img 标签
    """
    if not content or not isinstance(content, str):
        return []

    urls = set()

    # 1. Markdown 图片语法: ![alt](url)
    md_matches = re.findall(r'!\[.*?\]\(([^)\s]+)', content)
    for u in md_matches:
        if '/media/' in u or u.startswith('media/') or u.startswith('uploads/'):
            urls.add(u.strip())

    # 2. HTML img 标签: <img ... src="url" ...>
    html_matches = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', content, re.IGNORECASE)
    for u in html_matches:
        if '/media/' in u or u.startswith('media/') or u.startswith('uploads/'):
            urls.add(u.strip())

    # 3. 文本中直接引用的 media/uploads 路径
    text_matches = re.findall(r'(?:https?://[^\s/]+)?/(?:media/uploads/[^\s\'"<>\)]+)', content)
    for u in text_matches:
        urls.add(u.strip())

    return list(urls)


def get_article_media_files_to_cleanup(article) -> list[str]:
    """
    分析文章关联的图片资源，并执行安全引用检查，返回可安全物理删除的磁盘文件绝对路径列表。
    （纯分析与收集，不直接执行磁盘删除）
    """
    from cms.models import Article, Category

    files_to_delete = []
    candidates = set()

    if getattr(article, 'cover_image', None):
        candidates.add(article.cover_image)
    if getattr(article, 'cover_image_small', None):
        candidates.add(article.cover_image_small)

    content = getattr(article, 'content', None)
    if content:
        content_urls = extract_media_urls_from_content(content)
        candidates.update(content_urls)

    for item in candidates:
        abs_path = get_media_absolute_path(item)
        if not abs_path or not os.path.isfile(abs_path):
            continue

        filename = os.path.basename(abs_path)

        # 安全检查：排除当前文章自身后，跨租户检查是否有其他文章或分类仍在引用此文件名
        try:
            # 1. 文章引用检查（使用 original_objects 跨所有租户检查未软删除的文章）
            other_article_ref = (
                Article.original_objects.exclude(id=article.id)
                .filter(is_deleted=False)
                .filter(
                    models.Q(cover_image__icontains=filename) |
                    models.Q(cover_image_small__icontains=filename) |
                    models.Q(content__icontains=filename)
                )
                .exists()
            )
            # 2. 分类封面引用检查
            other_category_ref = (
                Category.objects.filter(is_deleted=False)
                .filter(cover_image__icontains=filename)
                .exists()
            )

            if other_article_ref or other_category_ref:
                logger.info(f"[物理删除资源] 文件 {abs_path} 仍被其他文章或分类引用，保留文件")
                continue
        except Exception as e:
            logger.warning(f"[物理删除资源] 检查文件引用异常: {e}，谨慎起见保留文件: {abs_path}")
            continue

        files_to_delete.append(abs_path)

    return files_to_delete


def delete_physical_files(file_paths: list[str]) -> list[str]:
    """
    从磁盘实际删除指定的文件列表
    """
    deleted = []
    for abs_path in file_paths:
        try:
            if os.path.isfile(abs_path):
                os.remove(abs_path)
                deleted.append(abs_path)
                logger.info(f"[物理删除资源] 成功清理物理文件: {abs_path}")
        except Exception as e:
            logger.warning(f"[物理删除资源] 删除磁盘文件失败: {abs_path}, 错误: {e}")
    return deleted


def cleanup_article_media_files(article) -> list[str]:
    """
    同步清理文章关联的本地物理媒体资源（兼容旧调用）
    """
    files = get_article_media_files_to_cleanup(article)
    return delete_physical_files(files)


def schedule_media_cleanup_on_commit(article) -> list[str]:
    """
    在数据库事务提交后再执行磁盘文件清理，确保事务回滚时物理文件毫发无损！
    返回待清理的文件列表
    """
    files = get_article_media_files_to_cleanup(article)
    if not files:
        return []

    # 注册事务提交后回调
    def do_cleanup():
        delete_physical_files(files)

    transaction.on_commit(do_cleanup)
    return files
