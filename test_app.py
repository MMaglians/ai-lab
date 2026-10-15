import pytest
from fastapi.testclient import TestClient

from app import app, client_dep
from fakes import FakeClient, stream_of


def make_client(handler):
    app.dependency_overrides[client_dep] = lambda: FakeClient(handler)
    return TestClient(app)


@pytest.fixture(autouse=True)
def cleanup():
    yield
    app.dependency_overrides.clear()


def parse_sse(text: str) -> list[tuple[str, str]]:
    events = []
    for block in text.strip().split("\n\n"):
        ev, data = None, None
        for line in block.splitlines():
            if line.startswith("event:"):
                ev = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                data = line.split(":", 1)[1].strip()
        events.append((ev, data))
    return events


def test_health():
    assert make_client(lambda **kw: None).get("/health").json()["status"] == "ok"


def test_chat_streams_tokens_usage_done():
    c = make_client(lambda **kw: stream_of("Ciao ", "mondo"))
    r = c.post("/chat", json={"message": "hi"})
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")
    names = [e for e, _ in parse_sse(r.text)]
    assert names == ["token", "token", "usage", "done"]


def test_validation_422():
    c = make_client(lambda **kw: stream_of("x"))
    assert c.post("/chat", json={"message": ""}).status_code == 422
    assert c.post("/chat", json={"message": "a", "temperature": 5}).status_code == 422


def test_error_inside_stream_is_in_band_and_not_leaked():
    c = make_client(lambda **kw: stream_of("a", error="SEGRETO interno"))
    r = c.post("/chat", json={"message": "hi"})
    assert r.status_code == 200
    names = [e for e, _ in parse_sse(r.text)]
    assert names[-1] == "error" and "done" not in names
    assert "SEGRETO" not in r.text
