"""
微信小程序相关序列化器
"""
import logging
from pathlib import Path

import requests
from django.conf import settings
from rest_framework import serializers

logger = logging.getLogger(__name__)


class WechatLoginSerializer(serializers.Serializer):
    """
    微信登录序列化器
    
    接收小程序前端传来的 code，调用微信 code2Session API 获取用户信息
    """
    code = serializers.CharField(
        required=True,
        help_text="小程序 wx.login() 获取的临时登录凭证"
    )
    tenant_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        help_text="可选的租户ID，用于首次登录时指定新用户所属租户"
    )
    
    def validate_code(self, value):
        """
        验证 code 基本格式
        """
        if not value or len(value) < 10:
            raise serializers.ValidationError("无效的登录凭证")
        return value
    
    def call_code2session(self, code):
        """
        调用微信 code2Session API
        
        接口文档: https://developers.weixin.qq.com/miniprogram/dev/OpenApiDoc/user-login/code2Session.html
        
        返回示例:
        成功: {"openid": "xxx", "session_key": "xxx", "unionid": "xxx"}
        失败: {"errcode": 40029, "errmsg": "invalid code"}
        
        常见错误码:
        - 40029: code无效
        - 40163: code已使用
        - 40013: appid无效
        """
        appid = getattr(settings, 'WECHAT_APPID', '')
        secret = getattr(settings, 'WECHAT_SECRET', '')
        
        if not appid or not secret:
            logger.error("微信小程序配置缺失：WECHAT_APPID 或 WECHAT_SECRET 未设置")
            raise serializers.ValidationError("微信登录服务配置错误")
        
        url = "https://api.weixin.qq.com/sns/jscode2session"
        params = {
            'appid': appid,
            'secret': secret,
            'js_code': code,
            'grant_type': 'authorization_code'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # 检查微信返回的错误码
            if 'errcode' in data and data['errcode'] != 0:
                error_msg = data.get('errmsg', '未知错误')
                errcode = data['errcode']
                
                # 映射常见错误码到友好提示
                error_messages = {
                    40029: "登录凭证无效，请重新获取",
                    40163: "登录凭证已使用，请重新获取",
                    40013: "小程序配置错误",
                    45011: "请求过于频繁，请稍后再试",
                }
                
                friendly_msg = error_messages.get(errcode, f"微信登录失败：{error_msg}")
                logger.warning(f"微信 code2Session 失败: errcode={errcode}, errmsg={error_msg}")
                raise serializers.ValidationError(friendly_msg)
            
            # 验证必需字段
            if 'openid' not in data:
                logger.error(f"微信 code2Session 返回数据缺少 openid: {data}")
                raise serializers.ValidationError("微信登录失败：未获取到用户标识")
            
            logger.info(f"微信 code2Session 成功，openid: {data['openid'][:8]}...")
            return data
            
        except requests.RequestException as e:
            logger.error(f"请求微信 API 失败: {str(e)}")
            raise serializers.ValidationError("微信服务暂时不可用，请稍后再试")
    
    def validate(self, attrs):
        """
        验证并调用微信 API
        """
        code = attrs['code']
        
        # 调用微信 API 获取用户信息
        wechat_data = self.call_code2session(code)
        
        # 将微信返回的数据添加到验证后的数据中
        attrs['openid'] = wechat_data['openid']
        attrs['session_key'] = wechat_data.get('session_key')
        attrs['unionid'] = wechat_data.get('unionid')
        
        return attrs


class WechatUserSerializer(serializers.Serializer):
    """
    微信用户信息序列化器（只读，用于响应）
    """
    openid = serializers.CharField(read_only=True)
    unionid = serializers.CharField(read_only=True, allow_null=True)
    nickname = serializers.CharField(read_only=True, allow_null=True)
    avatar_url = serializers.URLField(read_only=True, allow_null=True)
    created_at = serializers.DateTimeField(read_only=True)


class WechatAccountOptionSerializer(serializers.Serializer):
    name = serializers.CharField(read_only=True)
    author = serializers.CharField(read_only=True, allow_blank=True)
    appid = serializers.CharField(read_only=True)


class WechatAccountsResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = WechatAccountOptionSerializer(many=True)


class WechatUploadImageRequestSerializer(serializers.Serializer):
    account_appid = serializers.CharField(required=True, max_length=64)
    media = serializers.FileField(required=True, write_only=True)

    def validate_media(self, value):
        file_name = Path(str(getattr(value, "name", "")).strip()).name
        extension = Path(file_name).suffix.lower()
        if extension not in {".jpg", ".jpeg", ".png"}:
            raise serializers.ValidationError(
                f"Unsupported image extension for {file_name}. Supported extensions: .jpg, .jpeg, .png."
            )

        file_size = getattr(value, "size", None)
        max_bytes = int(getattr(settings, "WECHAT_DRAFT_IMAGE_MAX_BYTES", 10 * 1024 * 1024))
        if file_size is None:
            raise serializers.ValidationError(f"Unable to determine image size for {file_name}.")
        if file_size <= 0:
            raise serializers.ValidationError(f"Image file is empty: {file_name}.")
        if file_size > max_bytes:
            raise serializers.ValidationError(
                f"Image file is too large: {file_name}. Size={file_size} bytes, limit={max_bytes} bytes."
            )
        return value


class WechatUploadImageResultSerializer(serializers.Serializer):
    account_appid = serializers.CharField(read_only=True)
    account_name = serializers.CharField(read_only=True)
    url = serializers.URLField(read_only=True)


class WechatUploadImageResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = WechatUploadImageResultSerializer()


class WechatAddMaterialRequestSerializer(serializers.Serializer):
    account_appid = serializers.CharField(required=True, max_length=64)
    type = serializers.ChoiceField(
        choices=["image", "thumb"],
        required=False,
        default="image",
    )
    media = serializers.FileField(required=True, write_only=True)

    def validate(self, attrs):
        attrs = super().validate(attrs)
        uploaded_file = attrs["media"]
        file_name = Path(str(getattr(uploaded_file, "name", "")).strip()).name
        extension = Path(file_name).suffix.lower()

        allowed_extensions = {".jpg", ".jpeg", ".png"}
        if attrs["type"] == "thumb":
            allowed_extensions = {".jpg", ".jpeg"}

        if extension not in allowed_extensions:
            allowed = ", ".join(sorted(allowed_extensions))
            raise serializers.ValidationError(
                {"media": [f"Unsupported file extension for {file_name}. Supported extensions: {allowed}."]}
            )

        file_size = getattr(uploaded_file, "size", None)
        max_bytes = int(getattr(settings, "WECHAT_DRAFT_IMAGE_MAX_BYTES", 10 * 1024 * 1024))
        if attrs["type"] == "thumb":
            max_bytes = int(getattr(settings, "WECHAT_DRAFT_THUMB_MAX_BYTES", 64 * 1024))

        if file_size is None:
            raise serializers.ValidationError({"media": [f"Unable to determine file size for {file_name}."]})
        if file_size <= 0:
            raise serializers.ValidationError({"media": [f"File is empty: {file_name}."]})
        if file_size > max_bytes:
            raise serializers.ValidationError(
                {"media": [f"File is too large: {file_name}. Size={file_size} bytes, limit={max_bytes} bytes."]}
            )
        return attrs


class WechatAddMaterialResultSerializer(serializers.Serializer):
    account_appid = serializers.CharField(read_only=True)
    account_name = serializers.CharField(read_only=True)
    type = serializers.CharField(read_only=True)
    media_id = serializers.CharField(read_only=True)
    url = serializers.URLField(read_only=True, required=False, allow_null=True)


class WechatAddMaterialResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = WechatAddMaterialResultSerializer()


class WechatDraftAddRequestSerializer(serializers.Serializer):
    account_appid = serializers.CharField(required=True, max_length=64)
    articles = serializers.ListField(
        child=serializers.JSONField(),
        required=True,
        allow_empty=False,
        min_length=1,
        help_text="Official WeChat draft/add articles payload.",
    )

    def validate_articles(self, value):
        for index, article in enumerate(value):
            if not isinstance(article, dict):
                raise serializers.ValidationError(f"Article at index {index} must be an object.")

            article_type = str(article.get("article_type", "news")).strip() or "news"
            title = str(article.get("title", "")).strip()
            content = str(article.get("content", "")).strip()
            if not title:
                raise serializers.ValidationError(f"Article at index {index} is missing title.")
            if not content:
                raise serializers.ValidationError(f"Article at index {index} is missing content.")

            if article_type == "news":
                thumb_media_id = str(article.get("thumb_media_id", "")).strip()
                if not thumb_media_id:
                    raise serializers.ValidationError(
                        f"Article at index {index} must include thumb_media_id for news drafts."
                    )
            elif article_type == "newspic":
                image_info = article.get("image_info") or {}
                image_list = image_info.get("image_list") or []
                if not image_list:
                    raise serializers.ValidationError(
                        f"Article at index {index} must include image_info.image_list for newspic drafts."
                    )
                if len(image_list) > 20:
                    raise serializers.ValidationError(
                        f"Article at index {index} exceeds the 20 image limit for newspic drafts."
                    )
            else:
                raise serializers.ValidationError(
                    f"Article at index {index} has unsupported article_type: {article_type}."
                )
        return value


class WechatDraftAddResultSerializer(serializers.Serializer):
    account_appid = serializers.CharField(read_only=True)
    account_name = serializers.CharField(read_only=True)
    draft_media_id = serializers.CharField(read_only=True)


class WechatDraftAddResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = WechatDraftAddResultSerializer()


class WechatErrorResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField()
    code = serializers.IntegerField()
    message = serializers.CharField()
    data = serializers.JSONField(required=False, allow_null=True)
