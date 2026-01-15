"""
微信小程序相关模型
"""
import logging
from django.db import models
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


class WechatUser(models.Model):
    """
    微信用户模型，存储微信登录相关信息
    
    微信用户与 Member 是一对一关系：
    - 一个微信用户只能绑定一个 Member 账号
    - 通过 openid 作为微信用户的唯一标识
    - unionid 用于跨应用（多个小程序/公众号）用户互通场景
    """
    member = models.OneToOneField(
        'users.Member',
        on_delete=models.CASCADE,
        related_name='wechat_user',
        verbose_name=_("关联会员"),
        help_text=_("绑定的系统会员账号")
    )
    
    # 微信核心标识字段
    openid = models.CharField(
        _("微信OpenID"),
        max_length=64,
        unique=True,
        db_index=True,
        help_text=_("用户在当前小程序的唯一标识")
    )
    unionid = models.CharField(
        _("微信UnionID"),
        max_length=64,
        null=True,
        blank=True,
        db_index=True,
        help_text=_("用户在微信开放平台的唯一标识（跨应用互通时使用）")
    )
    
    # 会话密钥（重要：仅存储在后端，不可返回给前端）
    session_key = models.CharField(
        _("会话密钥"),
        max_length=128,
        null=True,
        blank=True,
        help_text=_("微信会话密钥，用于解密用户数据，仅后端使用")
    )
    
    # 可扩展的用户信息字段（来自用户授权）
    nickname = models.CharField(
        _("微信昵称"),
        max_length=64,
        null=True,
        blank=True
    )
    avatar_url = models.URLField(
        _("微信头像"),
        max_length=500,
        null=True,
        blank=True
    )
    
    # 时间戳
    created_at = models.DateTimeField(_("创建时间"), auto_now_add=True)
    updated_at = models.DateTimeField(_("更新时间"), auto_now=True)
    
    class Meta:
        verbose_name = _("微信用户")
        verbose_name_plural = _("微信用户")
        db_table = 'wechat_user'
        ordering = ['-created_at']
    
    def __str__(self):
        if self.nickname:
            return f"{self.nickname} ({self.openid[:8]}...)"
        return f"微信用户 {self.openid[:8]}..."
    
    def update_session_key(self, session_key):
        """
        更新会话密钥
        每次登录都应该更新 session_key
        """
        self.session_key = session_key
        self.save(update_fields=['session_key', 'updated_at'])
        logger.info(f"更新微信用户 {self.openid[:8]}... 的会话密钥")
