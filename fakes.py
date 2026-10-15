"""Client finti per i test: nessuna rete, nessuna chiave."""
from types import SimpleNamespace as NS


def usage(i=10, o=5):
    return NS(total_input_tokens=i, total_output_tokens=o)


class FakeInteractions:
    def __init__(self, handler):
        self.handler = handler
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return self.handler(**kwargs)


class FakeClient:
    def __init__(self, handler):
        self.interactions = FakeInteractions(handler)


def stream_of(*pieces, error=None):
    events = [NS(event_type="step.delta", delta=NS(type="text", text=p)) for p in pieces]
    if error:
        events.append(NS(event_type="error", error=NS(message=error)))
    else:
        events.append(NS(event_type="interaction.completed", interaction=NS(usage=usage())))
    return iter(events)
