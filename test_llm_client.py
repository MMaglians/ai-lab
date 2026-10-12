from llm_client import backoff_delay, status_of

def test_backoff_cresce_esponenzialmente():
    assert backoff_delay(1, base=1.0, jitter=0) == 1.0
    assert backoff_delay(2, base=1.0, jitter=0) == 2.0
    assert backoff_delay(4, base=1.0, jitter=0) == 8.0


def test_jitter_resta_nei_limiti():
    for _ in range(100):
        d = backoff_delay(1, base=1.0, jitter=0.5)
        assert 1.0 <= d <= 1.5


def test_status_of_legge_il_codice():
    class FintoErrore(Exception):
        code = 429
    assert status_of(FintoErrore()) == 429
    assert status_of(ValueError("niente codice")) is None