SUSPICIOUS_MOJIBAKE_MARKERS = (
    "\ufffd",
    "\u7009",
    "\u9983",
    "\u7039",
    "\u6f79",
    "\u6fb6",
    "\u6d60",
    "\u9ab6",
    "\u93c8",
    "\u95c2",
    "\u934f",
    "\u5a13",
    "\u704f",
    "\u934f",
    "\u9aca",
    "\u741b",
    "\u93b4",
    "\u93c2",
    "\u93ba",
    "\u95c4",
    "\u9420",
    "\u95ba",
)


def _mojibake_score(value):
    text = str(value or "")
    if not text:
        return 0
    return sum(text.count(marker) for marker in SUSPICIOUS_MOJIBAKE_MARKERS)


def looks_like_utf8_as_gbk_mojibake(value):
    return _mojibake_score(value) > 0


def repair_utf8_as_gbk_mojibake(value):
    text = str(value or "")
    if not text:
        return text

    best_text = text
    best_score = _mojibake_score(text)

    for encoding in ("gb18030", "gbk"):
        try:
            repaired = text.encode(encoding).decode("utf-8")
        except UnicodeError:
            continue
        repaired_score = _mojibake_score(repaired)
        if repaired_score < best_score:
            best_text = repaired
            best_score = repaired_score

    return best_text
