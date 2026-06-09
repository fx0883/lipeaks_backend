MOJIBAKE_MARKERS = {
    "\ufffd",
    "馃",
    "锛",
    "銆",
    "鈥",
    "浠",
    "瀹",
    "鏄",
    "鐨",
    "鍦",
    "鍥",
    "鎴",
    "鏂",
    "绗",
    "褰",
    "璇",
    "鍙",
    "鎵",
    "閮",
    "闂",
    "鎺",
    "鏃",
    "骞",
    "鏈",
    "甯",
    "浣",
    "娆",
    "鍏",
    "灏",
    "鍒",
    "鍚",
    "鍝",
    "鏀",
}


def looks_like_utf8_as_gbk_mojibake(value):
    text = str(value or "")
    if not text:
        return False
    return any(marker in text for marker in MOJIBAKE_MARKERS)


def repair_utf8_as_gbk_mojibake(value):
    text = str(value or "")
    if not looks_like_utf8_as_gbk_mojibake(text):
        return text

    for encoding in ("gb18030", "gbk"):
        try:
            repaired = text.encode(encoding).decode("utf-8")
        except UnicodeError:
            continue
        if repaired != text:
            return repaired

    return text

