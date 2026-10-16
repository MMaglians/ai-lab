import json

import pytest

from extractor import extract
from fakes import FakeClient, usage
from types import SimpleNamespace as NS

GOOD = {
    "invoice_number": "1/2026", "issue_date": "2026-01-10", "due_date": None,
    "supplier_name": "Foo Srl", "supplier_vat": None, "currency": "EUR",
    "line_items": [{"description": "X", "quantity": 2, "unit_price": 10.0}],
    "net_total": 20.0, "vat_amount": 4.4, "total_amount": 24.4,
}


def reply(payload):
    text = payload if isinstance(payload, str) else json.dumps(payload)
    return lambda **kw: NS(output_text=text, usage=usage())


def test_ok():
    r = extract("testo", client=FakeClient(reply(GOOD)))
    assert r.ok and r.invoice.total_amount == 24.4 and r.input_tokens == 10


def test_sends_schema_and_zero_temperature():
    client = FakeClient(reply(GOOD))
    extract("testo", version="v1", client=client)
    call = client.interactions.calls[0]
    assert call["generation_config"] == {"temperature": 0.0}
    assert call["response_format"]["mime_type"] == "application/json"
    assert "properties" in call["response_format"]["schema"]


def test_inconsistent_totals_are_validation_errors():
    bad = {**GOOD, "total_amount": 99.0}
    r = extract("testo", client=FakeClient(reply(bad)))
    assert not r.ok and r.error_kind == "validation"


def test_malformed_json_is_validation_error():
    r = extract("testo", client=FakeClient(reply("{non json")))
    assert r.error_kind == "validation"


def test_api_error_is_kept_separate(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)

    class Boom(Exception):
        status_code = 429

    def handler(**kw):
        raise Boom()

    client = FakeClient(handler)
    r = extract("testo", client=client, max_attempts=3)
    assert r.error_kind == "api" and "429" in r.error_detail
    assert len(client.interactions.calls) == 3


def test_transient_error_then_success(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    state = {"n": 0}

    class Boom(Exception):
        status_code = 503

    def handler(**kw):
        state["n"] += 1
        if state["n"] < 3:
            raise Boom()
        return NS(output_text=json.dumps(GOOD), usage=usage())

    assert extract("testo", client=FakeClient(handler)).ok

def test_strip_descriptions_keeps_field_named_description():
    from extractor import strip_descriptions
    from schemas import Invoice
    schema = Invoice.model_json_schema()
    stripped = strip_descriptions(schema)
    assert "description" in stripped["$defs"]["LineItem"]["properties"]   # il CAMPO resta
    assert '"description": "' not in json.dumps(stripped)                # le descrizioni testuali no


def test_no_descriptions_sends_stripped_schema():
    client = FakeClient(reply(GOOD))
    extract("testo", client=client, schema_descriptions=False)
    sent = client.interactions.calls[0]["response_format"]["schema"]
    assert '"description": "' not in json.dumps(sent)