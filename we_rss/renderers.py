import json

from rest_framework.renderers import BaseRenderer


class EventStreamRenderer(BaseRenderer):
    media_type = "text/event-stream"
    format = "event-stream"
    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if data is None:
            return b""
        return f"event: error\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n".encode("utf-8")
