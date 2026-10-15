"""Metriche di valutazione dell'estrazione: funzioni pure, testabili senza rete."""
import math

SCALAR_FIELDS = [
    "invoice_number", "issue_date", "due_date", "supplier_name",
    "supplier_vat", "currency", "net_total", "vat_amount", "total_amount",
]
MONEY_FIELDS = {"net_total", "vat_amount", "total_amount"}


def norm_text(value: str | None) -> str | None:
    """Minuscolo e spazi normalizzati; None resta None."""
    if value is None:
        return None
    return " ".join(str(value).split()).casefold()


def norm_vat(value: str | None) -> str | None:
    if value is None:
        return None
    return str(value).replace(" ", "").replace(".", "").upper()


def field_correct(field: str, expected, got) -> bool:
    """Exact match dopo normalizzazione; gli importi con tolleranza di mezzo centesimo."""
    if expected is None or got is None:
        return expected is None and got is None      # null e' una risposta valida: va azzeccata
    if field in MONEY_FIELDS:
        return abs(float(expected) - float(got)) < 0.005
    if field == "supplier_vat":
        return norm_vat(expected) == norm_vat(got)
    return norm_text(expected) == norm_text(got)


def compare_scalars(expected: dict, got: dict | None) -> dict[str, bool]:
    """Per ogni campo scalare: giusto o sbagliato. Se non c'e' un'estrazione valida, tutto sbagliato."""
    if got is None:
        return {f: False for f in SCALAR_FIELDS}
    return {f: field_correct(f, expected.get(f), got.get(f)) for f in SCALAR_FIELDS}


def item_key(item: dict) -> tuple:
    return (norm_text(item["description"]), int(item["quantity"]), round(float(item["unit_price"]), 2))


def item_counts(expected_items: list[dict], got_items: list[dict] | None) -> tuple[int, int, int]:
    """(veri positivi, falsi positivi, falsi negativi) sulle righe, come insiemi."""
    exp = {item_key(i) for i in expected_items}
    got = {item_key(i) for i in (got_items or [])}
    return len(exp & got), len(got - exp), len(exp - got)


def precision_recall_f1(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    if tp + fp + fn == 0:
        return 1.0, 1.0, 1.0
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def standard_error(p: float, n: int) -> float:
    """Errore standard di una proporzione stimata su n casi."""
    return math.sqrt(p * (1 - p) / n) if n > 0 else float("nan")