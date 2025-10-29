"""
用户互动模型
包括文章收藏、点赞等用户与内容的交互行为
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone


class ArticleFavorite(models.Model):
    """
    文章收藏模型
    
    记录用户收藏的文章，支持租户隔离
    """
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='article_favorites',
        verbose_name=_("用户")
    )
    article = models.ForeignKey(
        'cms.Article',
        on_delete=models.CASCADE,
        related_name='favorited_by',
        verbose_name=_("文章")
    )
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='article_favorites',
        verbose_name=_("所属租户")
    )
    created_at = models.DateTimeField(_("收藏时间"), default=timezone.now, db_index=True)
    
    class Meta:
        verbose_name = _('文章收藏')
        verbose_name_plural = _('文章收藏')
        db_table = 'interactions_article_favorite'
        ordering = ['-created_at']
        unique_together = [['user', 'article']]  # 同一用户不能重复收藏同一文章
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['article']),
            models.Index(fields=['tenant', 'user']),
            models.Index(fields=['tenant', 'article']),
        ]
    
    def __str__(self):
        return f"{self.user.username} favorited {self.article.title}"
