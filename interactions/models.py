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


class MemberLike(models.Model):
    """
    用户点赞模型
    
    记录Member用户之间的点赞行为，支持租户隔离
    """
    from_member = models.ForeignKey(
        'users.Member',
        on_delete=models.CASCADE,
        related_name='given_likes',
        verbose_name=_("点赞发起者")
    )
    to_member = models.ForeignKey(
        'users.Member',
        on_delete=models.CASCADE,
        related_name='received_likes',
        verbose_name=_("被点赞用户")
    )
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='member_likes',
        verbose_name=_("所属租户")
    )
    created_at = models.DateTimeField(_("点赞时间"), default=timezone.now, db_index=True)
    
    class Meta:
        verbose_name = _('用户点赞')
        verbose_name_plural = _('用户点赞')
        db_table = 'interactions_member_like'
        ordering = ['-created_at']
        unique_together = [['from_member', 'to_member']]  # 同一用户不能重复点赞同一用户
        indexes = [
            models.Index(fields=['from_member', 'created_at']),
            models.Index(fields=['to_member', 'created_at']),
            models.Index(fields=['tenant', 'from_member']),
            models.Index(fields=['tenant', 'to_member']),
        ]
    
    def __str__(self):
        return f"{self.from_member.username} liked {self.to_member.username}"


class MemberFollow(models.Model):
    """
    用户关注模型
    
    记录Member用户之间的关注关系，支持租户隔离
    """
    follower = models.ForeignKey(
        'users.Member',
        on_delete=models.CASCADE,
        related_name='following_set',
        verbose_name=_("关注者")
    )
    following = models.ForeignKey(
        'users.Member',
        on_delete=models.CASCADE,
        related_name='followers_set',
        verbose_name=_("被关注者")
    )
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='member_follows',
        verbose_name=_("所属租户")
    )
    created_at = models.DateTimeField(_("关注时间"), default=timezone.now, db_index=True)
    
    class Meta:
        verbose_name = _('用户关注')
        verbose_name_plural = _('用户关注')
        db_table = 'interactions_member_follow'
        ordering = ['-created_at']
        unique_together = [['follower', 'following']]  # 同一用户不能重复关注同一用户
        indexes = [
            models.Index(fields=['follower', 'created_at']),
            models.Index(fields=['following', 'created_at']),
            models.Index(fields=['tenant', 'follower']),
            models.Index(fields=['tenant', 'following']),
        ]
    
    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"
    
    def is_mutual(self):
        """检查是否互相关注"""
        return MemberFollow.objects.filter(
            follower=self.following,
            following=self.follower
        ).exists()
