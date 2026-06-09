import json


def encode_sse_event(event_name, payload) -> bytes:
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return f"event: {event_name}\ndata: {body}\n\n".encode("utf-8")
