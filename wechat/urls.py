"""
微信公众号相关 URL 配置
"""
from django.urls import path

from wechat.views import (
    WechatLoginView,
    wechat_accounts,
    wechat_draft_add,
    wechat_material_add_material,
    wechat_media_uploadimg,
)

app_name = "wechat"

urlpatterns = [
    path("login/", WechatLoginView.as_view(), name="wechat-login"),
    path("accounts/", wechat_accounts, name="wechat-accounts"),
    path("media/uploadimg/", wechat_media_uploadimg, name="wechat-media-uploadimg"),
    path("material/add-material/", wechat_material_add_material, name="wechat-material-add-material"),
    path("draft/add/", wechat_draft_add, name="wechat-draft-add"),
]
