"""
微信小程序相关URL配置
"""
from django.urls import path
from wechat.views import WechatLoginView

app_name = 'wechat'

urlpatterns = [
    # 微信小程序登录
    path('login/', WechatLoginView.as_view(), name='wechat-login'),
]
