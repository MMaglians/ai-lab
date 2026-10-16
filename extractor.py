"""Estrazione di una fattura da testo libero -> Invoice validata."""
import time
from dataclasses import dataclass

from pydantic import ValidationError

from llm_client import MODEL, get_client, status_of, with_retry
from schemas import Invoice

# --- Le versioni del prompt sono DATI: cosi' si confrontano con l'eval ---

SYSTEM_V1 = "Sei un assistente che estrae dati da documenti."
PREAMBLE_V1 = "Estrai i dati della fattura dal testo seguente."

SYSTEM_V2 = """Sei un assistente che estrae dati strutturati da fatture.
Regole:
- Le date vanno in formato YYYY-MM-DD.
- Gli importi sono numeri con il punto decimale, senza separatori delle migliaia e senza simbolo di valuta (esempio: 1234.56).
- La valuta e' il codice ISO a 3 lettere (EUR, USD, CHF...).
- issue_date e' la data di EMISSIONE della fattura: non confonderla con data ordine, data consegna o scadenza.
- invoice_number e' il numero della fattura, non il numero d'ordine.
- unit_price e' il prezzo unitario al netto di IVA.
- Se un'informazione non e' presente nel testo usa null. Non inventare mai valori."""

PREAMBLE_V2 = """Estrai i dati della fattura dal testo, seguendo le regole.

ESEMPIO 1
TESTO:
Fattura 14/2026 del 3 febbraio 2026. Emessa da Rossi Impianti S.n.c. (P.IVA IT09876543210).
2 x Interruttore differenziale a 45,00 EUR. Imponibile 90,00, IVA 22% 19,80, totale 109,80 EUR.
Pagamento entro il 5/3/2026.
RISULTATO:
{"invoice_number": "14/2026", "issue_date": "2026-02-03", "due_date": "2026-03-05", "supplier_name": "Rossi Impianti S.n.c.", "supplier_vat": "IT09876543210", "currency": "EUR", "line_items": [{"description": "Interruttore differenziale", "quantity": 2, "unit_price": 45.0}], "net_total": 90.0, "vat_amount": 19.8, "total_amount": 109.8}

ESEMPIO 2
TESTO:
Verdi Servizi - Fattura n. A-77 - 10.04.2026. 1 x Consulenza tecnica 300,00 CHF. Netto 300,00 CHF, IVA 0,00, totale 300,00 CHF. Pagamento alla consegna.
RISULTATO:
{"invoice_number": "A-77", "issue_date": "2026-04-10", "due_date": null, "supplier_name": "Verdi Servizi", "supplier_vat": null, "currency": "CHF", "line_items": [{"description": "Consulenza tecnica", "quantity": 1, "unit_price": 300.0}], "net_total": 300.0, "vat_amount": 0.0, "total_amount": 300.0}"""

PROMPTS = {
    "v1": (SYSTEM_V1, PREAMBLE_V1),
    "v2": (SYSTEM_V2, PREAMBLE_V2),
}

@dataclass
class Extraction:
    ok: bool
    invoice: Invoice | None = None
    error_kind: str | None = None        # "api" (non e' colpa del modello) o "validation"
    error_detail: str | None = None
    raw: str = ""
    input_tokens: int | None = None
    output_tokens: int | None = None
    seconds: float = 0.0


def strip_descriptions(node):
    """Rimuove le descrizioni (stringhe) dallo schema JSON, in modo ricorsivo."""
    if isinstance(node, dict):
        return {
            k: strip_descriptions(v)
            for k, v in node.items()
            if not (k== "description" and isinstance(v, str))
        } #si tolgono solo descrizioni testuali
    if isinstance(node, list):
        return [strip_descriptions(x) for x in node]
    return node

def extract(text: str, version: str = "v2", client=None, max_attempts: int = 4, 
            schema_descriptions: bool=True) -> Extraction:
    system, preamble = PROMPTS[version]
    client = client or get_client()
    schema = Invoice.model_json_schema()
    if not schema_descriptions:
        schema = strip_descriptions(schema)
    start = time.perf_counter()

    try:
        interaction = with_retry(
            lambda: client.interactions.create(
                model=MODEL,
                input=f"{preamble}\n\nTESTO:\n{text}",
                system_instruction=system,
                generation_config={"temperature": 0.0},
                response_format={
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": schema,
                },
                store=False,
            ),
            max_attempts=max_attempts,
        )
    except Exception as exc:
        # errore di infrastruttura (rete, quota, chiave): va tenuto separato dagli errori del modello
        return Extraction(
            ok=False,
            error_kind="api",
            error_detail=f"{type(exc).__name__} (status {status_of(exc)})",
            seconds=time.perf_counter() - start,
        )

    seconds = time.perf_counter() - start
    raw = interaction.output_text or ""
    usage = interaction.usage
    tokens = {
        "input_tokens": usage.total_input_tokens if usage else None,
        "output_tokens": usage.total_output_tokens if usage else None,
    }

    try:
        invoice = Invoice.model_validate_json(raw)
    except ValidationError as exc:
        first = exc.errors()[0]
        where = ".".join(str(p) for p in first["loc"]) or "documento"
        return Extraction(
            ok=False, error_kind="validation", raw=raw, seconds=seconds, **tokens,
            error_detail=f"{where}: {first['msg']}",
        )
    return Extraction(ok=True, invoice=invoice, raw=raw, seconds=seconds, **tokens)
            
        