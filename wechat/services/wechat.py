import json
import logging
import mimetypes
from pathlib import Path

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

WECHAT_TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/token"
WECHAT_ADD_MATERIAL_URL = "https://api.weixin.qq.com/cgi-bin/material/add_material"
WECHAT_UPLOAD_ARTICLE_IMAGE_URL = "https://api.weixin.qq.com/cgi-bin/media/uploadimg"
WECHAT_ADD_DRAFT_URL = "https://api.weixin.qq.com/cgi-bin/draft/add"
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
ALLOWED_THUMB_EXTENSIONS = {".jpg", ".jpeg"}


class WechatServiceError(Exception):
    default_code = 5000
    default_status_code = 500

    def __init__(
        self,
        message,
        *,
        code=None,
        status_code=None,
        data=None,
        errcode=None,
        errmsg=None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code or self.default_code
        self.status_code = status_code or self.default_status_code
        self.data = data
        self.errcode = errcode
        self.errmsg = errmsg

    def to_response(self):
        payload = self.data
        if payload is None and (self.errcode is not None or self.errmsg):
            payload = {
                "errcode": self.errcode,
                "errmsg": self.errmsg,
            }
        return {
            "success": False,
            "code": self.code,
            "message": self.message,
            "data": payload,
        }


class WechatConfigError(WechatServiceError):
    default_code = 4000
    default_status_code = 500


class WechatValidationError(WechatServiceError):
    default_code = 4000
    default_status_code = 400


class WechatAPIError(WechatServiceError):
    default_code = 5002
    default_status_code = 502


def _mask_value(value, *, head=4, tail=4):
    if not value:
        return ""
    if len(value) <= head + tail:
        return "*" * len(value)
    return f"{value[:head]}***{value[-tail:]}"


def _get_config_path():
    config_path = getattr(settings, "WECHAT_CONFIG_PATH", "")
    if not config_path:
        raise WechatConfigError("WECHAT_CONFIG_PATH is not configured")
    return Path(config_path)


def _get_api_timeout():
    return int(getattr(settings, "WECHAT_API_TIMEOUT", 15))


def _get_image_max_bytes():
    return int(getattr(settings, "WECHAT_DRAFT_IMAGE_MAX_BYTES", 10 * 1024 * 1024))


def _get_thumb_max_bytes():
    return int(getattr(settings, "WECHAT_DRAFT_THUMB_MAX_BYTES", 64 * 1024))


def _raise_for_wechat_error(data, operation):
    errcode = data.get("errcode")
    if errcode in (None, 0):
        return

    errmsg = data.get("errmsg", "unknown error")
    raise WechatAPIError(
        f"{operation} failed with errcode={errcode}, errmsg={errmsg}",
        errcode=errcode,
        errmsg=errmsg,
    )


def _parse_wechat_response(response, operation):
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        status_code = getattr(response, "status_code", None)
        raise WechatAPIError(
            f"{operation} failed with HTTP status {status_code}",
            data={"status_code": status_code, "body": response.text[:500]},
        ) from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise WechatAPIError(
            f"{operation} returned a non-JSON response",
            data={"body": response.text[:500]},
        ) from exc

    if not isinstance(data, dict):
        raise WechatAPIError(
            f"{operation} returned an unexpected response payload",
            data={"response": data},
        )

    _raise_for_wechat_error(data, operation)
    return data


def load_wechat_accounts():
    config_path = _get_config_path()
    if not config_path.exists():
        raise WechatConfigError(f"WeChat config file does not exist: {config_path}")
    if not config_path.is_file():
        raise WechatConfigError(f"WeChat config path is not a file: {config_path}")

    try:
        content = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise WechatConfigError(f"WeChat config file is not valid JSON: {config_path}") from exc

    raw_accounts = content.get("account")
    if not isinstance(raw_accounts, list):
        raise WechatConfigError('WeChat config must contain an "account" list')

    accounts = []
    for index, item in enumerate(raw_accounts):
        if not isinstance(item, dict):
            raise WechatConfigError(f"WeChat account config at index {index} must be an object")

        name = str(item.get("name", "")).strip()
        author = str(item.get("author", "")).strip()
        appid = str(item.get("WECHAT_APPID", "")).strip()
        secret = str(item.get("WECHAT_SECRET", "")).strip()

        if not name or not appid or not secret:
            raise WechatConfigError(
                f"WeChat account config at index {index} must include name, WECHAT_APPID, and WECHAT_SECRET"
            )

        accounts.append(
            {
                "name": name,
                "author": author,
                "WECHAT_APPID": appid,
                "WECHAT_SECRET": secret,
            }
        )

    return accounts


def get_wechat_account_by_appid(appid):
    normalized_appid = str(appid or "").strip()
    if not normalized_appid:
        raise WechatValidationError("account_appid is required")

    for account in load_wechat_accounts():
        if account["WECHAT_APPID"] == normalized_appid:
            return account

    raise WechatValidationError(f"WeChat account not found for appid: {normalized_appid}")


def get_access_token(appid, secret):
    cache_key = f"wechat:access_token:{appid}"
    cached_token = cache.get(cache_key)
    if cached_token:
        logger.info("Using cached WeChat access token for appid=%s", _mask_value(appid))
        return cached_token

    response = requests.get(
        WECHAT_TOKEN_URL,
        params={
            "grant_type": "client_credential",
            "appid": appid,
            "secret": secret,
        },
        timeout=_get_api_timeout(),
    )
    data = _parse_wechat_response(response, "get access_token")
    access_token = data.get("access_token")
    if not access_token:
        raise WechatAPIError(
            "get access_token succeeded but access_token is missing",
            data=data,
        )

    expires_in = int(data.get("expires_in", 7200))
    cache_timeout = min(int(getattr(settings, "WECHAT_ACCESS_TOKEN_CACHE_TIMEOUT", 7000)), expires_in)
    cache.set(cache_key, access_token, cache_timeout)
    logger.info(
        "Fetched WeChat access token for appid=%s and cached for %s seconds",
        _mask_value(appid),
        cache_timeout,
    )
    return access_token


def _validate_media_path(image_path, *, allowed_extensions, max_bytes, media_label):
    if not image_path:
        raise WechatValidationError(f"{media_label} path is required")

    path = Path(image_path)
    if not path.is_absolute():
        raise WechatValidationError(f"{media_label} path must be an absolute path: {image_path}")
    if not path.exists():
        raise WechatValidationError(f"{media_label} file does not exist: {image_path}")
    if not path.is_file():
        raise WechatValidationError(f"{media_label} path is not a file: {image_path}")
    if path.suffix.lower() not in allowed_extensions:
        allowed = ", ".join(sorted(allowed_extensions))
        raise WechatValidationError(
            f"Unsupported {media_label} extension for {image_path}. Supported extensions: {allowed}"
        )

    file_size = path.stat().st_size
    if file_size <= 0:
        raise WechatValidationError(f"{media_label} file is empty: {image_path}")
    if file_size > max_bytes:
        raise WechatValidationError(
            f"{media_label} file is too large: {image_path}. Size={file_size} bytes, limit={max_bytes} bytes"
        )

    return path


def _validate_uploaded_media_file(uploaded_file, *, allowed_extensions, max_bytes, media_label):
    if uploaded_file is None:
        raise WechatValidationError(f"{media_label} file is required")

    file_name = Path(str(getattr(uploaded_file, "name", "")).strip()).name
    if not file_name:
        raise WechatValidationError(f"{media_label} file name is required")

    extension = Path(file_name).suffix.lower()
    if extension not in allowed_extensions:
        allowed = ", ".join(sorted(allowed_extensions))
        raise WechatValidationError(
            f"Unsupported {media_label} extension for {file_name}. Supported extensions: {allowed}"
        )

    file_size = getattr(uploaded_file, "size", None)
    if file_size is None:
        raise WechatValidationError(f"Unable to determine {media_label} file size for {file_name}")
    if file_size <= 0:
        raise WechatValidationError(f"{media_label} file is empty: {file_name}")
    if file_size > max_bytes:
        raise WechatValidationError(
            f"{media_label} file is too large: {file_name}. Size={file_size} bytes, limit={max_bytes} bytes"
        )

    return file_name


def add_permanent_material(access_token, image_path, media_type):
    if media_type == "image":
        path = _validate_media_path(
            image_path,
            allowed_extensions=ALLOWED_IMAGE_EXTENSIONS,
            max_bytes=_get_image_max_bytes(),
            media_label="image",
        )
    elif media_type == "thumb":
        path = _validate_media_path(
            image_path,
            allowed_extensions=ALLOWED_THUMB_EXTENSIONS,
            max_bytes=_get_thumb_max_bytes(),
            media_label="thumb",
        )
    else:
        raise WechatValidationError(f"Unsupported permanent media type: {media_type}")

    content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    url = f"{WECHAT_ADD_MATERIAL_URL}?access_token={access_token}&type={media_type}"

    with path.open("rb") as file_obj:
        response = requests.post(
            url,
            files={"media": (path.name, file_obj, content_type)},
            timeout=_get_api_timeout(),
        )

    data = _parse_wechat_response(response, f"add permanent {media_type}")
    media_id = data.get("media_id")
    if not media_id:
        raise WechatAPIError(
            f"add permanent {media_type} succeeded but media_id is missing",
            data=data,
        )

    logger.info("Added permanent %s for file=%s", media_type, path.name)
    return {
        "media_id": media_id,
        "url": data.get("url"),
    }


def add_permanent_material_file(access_token, uploaded_file, media_type):
    if media_type == "image":
        file_name = _validate_uploaded_media_file(
            uploaded_file,
            allowed_extensions=ALLOWED_IMAGE_EXTENSIONS,
            max_bytes=_get_image_max_bytes(),
            media_label="image",
        )
    elif media_type == "thumb":
        file_name = _validate_uploaded_media_file(
            uploaded_file,
            allowed_extensions=ALLOWED_THUMB_EXTENSIONS,
            max_bytes=_get_thumb_max_bytes(),
            media_label="thumb",
        )
    else:
        raise WechatValidationError(f"Unsupported permanent media type: {media_type}")

    content_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
    url = f"{WECHAT_ADD_MATERIAL_URL}?access_token={access_token}&type={media_type}"

    if hasattr(uploaded_file, "seek"):
        uploaded_file.seek(0)
    file_obj = getattr(uploaded_file, "file", uploaded_file)
    if hasattr(file_obj, "seek"):
        file_obj.seek(0)

    response = requests.post(
        url,
        files={"media": (file_name, file_obj, content_type)},
        timeout=_get_api_timeout(),
    )

    data = _parse_wechat_response(response, f"add permanent {media_type}")
    media_id = data.get("media_id")
    if not media_id:
        raise WechatAPIError(
            f"add permanent {media_type} succeeded but media_id is missing",
            data=data,
        )

    logger.info("Added permanent %s for uploaded file=%s", media_type, file_name)
    return {
        "media_id": media_id,
        "url": data.get("url"),
    }


def upload_permanent_media(access_token, image_path, media_type):
    return add_permanent_material(access_token, image_path, media_type)["media_id"]


def upload_permanent_media_file(access_token, uploaded_file, media_type):
    return add_permanent_material_file(access_token, uploaded_file, media_type)["media_id"]


def upload_permanent_image(access_token, image_path):
    return upload_permanent_media(access_token, image_path, "image")


def upload_permanent_thumb(access_token, image_path):
    return upload_permanent_media(access_token, image_path, "thumb")


def upload_permanent_image_file(access_token, uploaded_file):
    return upload_permanent_media_file(access_token, uploaded_file, "image")


def upload_permanent_thumb_file(access_token, uploaded_file):
    return upload_permanent_media_file(access_token, uploaded_file, "thumb")


def upload_article_image_file(access_token, uploaded_file):
    file_name = _validate_uploaded_media_file(
        uploaded_file,
        allowed_extensions=ALLOWED_IMAGE_EXTENSIONS,
        max_bytes=_get_image_max_bytes(),
        media_label="image",
    )

    content_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
    url = f"{WECHAT_UPLOAD_ARTICLE_IMAGE_URL}?access_token={access_token}"

    if hasattr(uploaded_file, "seek"):
        uploaded_file.seek(0)
    file_obj = getattr(uploaded_file, "file", uploaded_file)
    if hasattr(file_obj, "seek"):
        file_obj.seek(0)

    response = requests.post(
        url,
        files={"media": (file_name, file_obj, content_type)},
        timeout=_get_api_timeout(),
    )
    data = _parse_wechat_response(response, "upload article image")
    image_url = data.get("url")
    if not image_url:
        raise WechatAPIError(
            "upload article image succeeded but url is missing",
            data=data,
        )

    logger.info("Uploaded article image for uploaded file=%s", file_name)
    return image_url


def add_draft(access_token, articles):
    if not isinstance(articles, list) or not articles:
        raise WechatValidationError("articles must contain at least one item")

    payload = {
        "articles": articles,
    }
    payload_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    response = requests.post(
        f"{WECHAT_ADD_DRAFT_URL}?access_token={access_token}",
        data=payload_bytes,
        headers={"Content-Type": "application/json; charset=utf-8"},
        timeout=_get_api_timeout(),
    )
    data = _parse_wechat_response(response, "add draft")
    if "media_id" not in data:
        raise WechatAPIError(
            "add draft succeeded but media_id is missing",
            data=data,
        )

    logger.info(
        "Added draft with %s articles, media_id=%s",
        len(articles),
        _mask_value(data.get("media_id")),
    )
    return data
