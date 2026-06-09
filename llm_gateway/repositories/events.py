from llm_gateway.models import LLMRunEvent


class EventRepository:
    @staticmethod
    def append(run, event_type, payload=None):
        last_event = run.events.order_by("-sequence").first()
        next_sequence = 1 if last_event is None else last_event.sequence + 1
        return LLMRunEvent.objects.create(
            run=run,
            sequence=next_sequence,
            event_type=event_type,
            payload=payload,
        )

    @staticmethod
    def list_by_run(run):
        return run.events.order_by("sequence", "id")
