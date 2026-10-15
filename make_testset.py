"""Genera un test set SINTETICO di fatture: testo + risposta attesa.

Tutti i dati sono inventati (nessun documento reale, nessun problema di privacy o di licenza).
Con SEED fisso il test set e' riproducibile. Uso:  uv run python make_testset.py
"""
import json
import random
from datetime import date, timedelta
from pathlib import Path

from schemas import Invoice

SEED = 42
N_CASES = 20
OUT_DIR = Path("data")

MESI_IT = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio",
           "agosto", "settembre", "ottobre", "novembre", "dicembre"]
MESI_EN = ["January", "February", "March", "April", "May", "June", "July",
           "August", "September", "October", "November", "December"]

SUPPLIERS = [
    "Bianchi Forniture S.r.l.", "Eliografica Nord S.p.A.", "Colombo & Figli S.n.c.",
    "TecnoUfficio Srl", "Marino Logistica S.r.l.", "Ferrari Arredi S.p.A.",
    "Greco Informatica S.r.l.", "Conti Packaging S.r.l.", "Lombardi Servizi S.n.c.",
    "Barbieri Ricambi S.r.l.", "Costa Stampa S.p.A.", "Fontana Edilizia S.r.l.",
]

# (descrizione italiana, descrizione inglese, prezzo unitario in centesimi)
CATALOG = [
    ("Carta A4 (risma)", "A4 paper (ream)", 390),
    ("Toner nero", "Black toner", 5450),
    ("Cavo HDMI 2 m", "HDMI cable 2 m", 899),
    ("Tastiera wireless", "Wireless keyboard", 3490),
    ("Monitor 24 pollici", "24-inch monitor", 15900),
    ("Scatola di cartone 40x30", "Cardboard box 40x30", 120),
    ("Nastro adesivo (confezione)", "Packing tape (pack)", 650),
    ("Consulenza tecnica (ora)", "Technical consulting (hour)", 6500),
    ("Licenza software annuale", "Annual software licence", 12000),
    ("Sedia ergonomica", "Ergonomic chair", 18900),
]


# --- formattazione di date e importi ---

def fmt_date(d: date, style: str) -> str:
    if style == "slash":
        return f"{d.day:02d}/{d.month:02d}/{d.year}"
    if style == "dots":
        return f"{d.day:02d}.{d.month:02d}.{d.year}"
    if style == "iso":
        return d.isoformat()
    if style == "text_it":
        return f"{d.day} {MESI_IT[d.month - 1]} {d.year}"
    if style == "text_en":
        return f"{d.day} {MESI_EN[d.month - 1]} {d.year}"
    raise ValueError(style)


def fmt_money(cents: int, style: str) -> str:
    euros, rest = divmod(cents, 100)
    if style == "it":      # 1.234,56
        return f"{euros:,}".replace(",", ".") + f",{rest:02d}"
    return f"{euros}.{rest:02d}"   # 1234.56


# --- i quattro layout ---

def layout_formal(c: dict) -> str:
    rows = "\n".join(
        f"{i['it']:<30} {i['qty']:>4} {fmt_money(i['cents'], 'it'):>12} {fmt_money(i['qty'] * i['cents'], 'it'):>12}"
        for i in c["items"]
    )
    vat_line = f"P.IVA {c['vat']}" if c["vat"] else "P.IVA: non indicata"
    due_line = f"Scadenza pagamento: {fmt_date(c['due'], c['dstyle'])}" if c["due"] else "Pagamento alla consegna."
    return (
        f"FATTURA N. {c['number']}\n"
        f"Data emissione: {fmt_date(c['issue'], c['dstyle'])}\n"
        f"Data ordine: {fmt_date(c['order_date'], c['dstyle'])} - Rif. ordine n. {c['order_no']}\n\n"
        f"Fornitore: {c['name']}\n{vat_line}\n\n"
        f"{'Descrizione':<30} {'Q.ta':>4} {'Prezzo unit.':>12} {'Importo':>12}\n{rows}\n\n"
        f"Imponibile: {fmt_money(c['net'], 'it')} {c['cur']}\n"
        f"IVA {c['rate']}%: {fmt_money(c['vat_c'], 'it')} {c['cur']}\n"
        f"TOTALE DOCUMENTO: {fmt_money(c['total'], 'it')} {c['cur']}\n"
        f"{due_line}\n"
    )


def layout_email(c: dict) -> str:
    lines = "\n".join(
        f"- {i['it']}: {i['qty']} x {fmt_money(i['cents'], 'it')} {c['cur']} = {fmt_money(i['qty'] * i['cents'], 'it')} {c['cur']}"
        for i in c["items"]
    )
    vat_part = f" (P.IVA {c['vat']})" if c["vat"] else ""
    due_part = f", da saldare entro il {fmt_date(c['due'], c['dstyle'])}" if c["due"] else ", pagamento alla consegna"
    return (
        f"Oggetto: Fattura {c['number']}\n\n"
        f"Gentile cliente,\n"
        f"in allegato la fattura {c['number']} emessa il {fmt_date(c['issue'], c['dstyle'])} da {c['name']}{vat_part}.\n"
        f"Il materiale e' stato ordinato il {fmt_date(c['order_date'], c['dstyle'])} (ordine {c['order_no']}).\n\n"
        f"Dettaglio:\n{lines}\n\n"
        f"Importo netto {fmt_money(c['net'], 'it')} {c['cur']}, IVA ({c['rate']}%) {fmt_money(c['vat_c'], 'it')} {c['cur']}, "
        f"totale {fmt_money(c['total'], 'it')} {c['cur']}{due_part}.\n\n"
        f"Cordiali saluti,\n{c['name']}\n"
    )


def layout_compact(c: dict) -> str:
    rows = "\n".join(
        f"{i['it']} ; {i['qty']} ; {fmt_money(i['cents'], 'plain')} ; {fmt_money(i['qty'] * i['cents'], 'plain')}"
        for i in c["items"]
    )
    head = f"{c['name']} | {c['vat']}" if c["vat"] else c["name"]
    due = f"SCAD. {fmt_date(c['due'], c['dstyle'])}" if c["due"] else "Scad.: a vista"
    return (
        f"{head}\n"
        f"INV {c['number']} | {fmt_date(c['issue'], c['dstyle'])}\n"
        f"----\n{rows}\n----\n"
        f"NETTO {fmt_money(c['net'], 'plain')}  IVA {fmt_money(c['vat_c'], 'plain')} ({c['rate']}%)  "
        f"TOT {fmt_money(c['total'], 'plain')} {c['cur']}\n{due}\n"
    )


def layout_english(c: dict) -> str:
    rows = "\n".join(
        f"  {i['qty']} x {i['en']} @ {fmt_money(i['cents'], 'plain')} {c['cur']} -> {fmt_money(i['qty'] * i['cents'], 'plain')}"
        for i in c["items"]
    )
    due = f"Due date: {fmt_date(c['due'], c['dstyle'])}" if c["due"] else "Payment due: on receipt"
    vat = f"VAT no.: {c['vat']}\n" if c["vat"] else ""
    return (
        f"INVOICE\nInvoice no.: {c['number']}\n"
        f"Issue date: {fmt_date(c['issue'], c['dstyle'])}\n{due}\n"
        f"Order date: {fmt_date(c['order_date'], c['dstyle'])}\n"
        f"Seller: {c['name']}\n{vat}"
        f"Items:\n{rows}\n"
        f"Subtotal: {fmt_money(c['net'], 'plain')} {c['cur']}\n"
        f"VAT {c['rate']}%: {fmt_money(c['vat_c'], 'plain')} {c['cur']}\n"
        f"Total due: {fmt_money(c['total'], 'plain')} {c['cur']}\n"
    )


LAYOUTS = [
    ("formale", layout_formal, ["slash", "dots", "text_it"]),
    ("email", layout_email, ["text_it", "slash"]),
    ("compatto", layout_compact, ["dots", "iso", "slash"]),
    ("inglese", layout_english, ["iso", "text_en"]),
]


def make_case(i: int, rng: random.Random) -> dict:
    layout_name, layout_fn, date_styles = LAYOUTS[i % len(LAYOUTS)]
    issue = date(2026, 1, 1) + timedelta(days=rng.randint(0, 270))
    foreign = rng.random() < 0.15
    cur = rng.choice(["USD", "CHF"]) if foreign else "EUR"
    rate = 0 if foreign else rng.choice([22, 22, 22, 10])

    chosen = rng.sample(CATALOG, k=rng.randint(1, 4))
    items = [{"it": it, "en": en, "cents": cents, "qty": rng.randint(1, 10)} for it, en, cents in chosen]
    net = sum(x["qty"] * x["cents"] for x in items)
    vat_c = round(net * rate / 100)
    total = net + vat_c

    c = {
        "number": rng.choice([f"{rng.randint(1, 999)}/2026", f"FT-{rng.randint(100, 999):04d}",
                              f"INV-2026{rng.randint(1, 12):02d}{rng.randint(1, 28):02d}-{rng.randint(1, 9):02d}",
                              f"{rng.randint(10, 99)}/E"]),
        "name": rng.choice(SUPPLIERS),
        "vat": None if rng.random() < 0.25 else "IT" + "".join(str(rng.randint(0, 9)) for _ in range(11)),
        "issue": issue,
        "due": None if rng.random() < 0.2 else issue + timedelta(days=rng.choice([15, 30, 60])),
        "order_date": issue - timedelta(days=rng.randint(5, 20)),
        "order_no": str(rng.randint(10000, 99999)),
        "dstyle": rng.choice(date_styles),
        "cur": cur, "rate": rate, "items": items, "net": net, "vat_c": vat_c, "total": total,
    }
    text = layout_fn(c)

    descr_key = "en" if layout_name == "inglese" else "it"
    expected = {
        "invoice_number": c["number"],
        "issue_date": issue.isoformat(),
        "due_date": c["due"].isoformat() if c["due"] else None,
        "supplier_name": c["name"],
        "supplier_vat": c["vat"],
        "currency": cur,
        "line_items": [{"description": x[descr_key], "quantity": x["qty"], "unit_price": x["cents"] / 100} for x in items],
        "net_total": net / 100,
        "vat_amount": vat_c / 100,
        "total_amount": total / 100,
    }
    Invoice.model_validate(expected)   # la risposta attesa deve rispettare lo schema e i conti

    tags = [layout_name, c["dstyle"]]
    if c["vat"] is None:
        tags.append("senza_piva")
    if c["due"] is None:
        tags.append("senza_scadenza")
    if foreign:
        tags.append("valuta_estera")
    if len(items) >= 3:
        tags.append("molte_righe")
    return {"id": f"case_{i:02d}", "tags": tags, "text": text, "expected": expected}


def main() -> None:
    rng = random.Random(SEED)
    cases = [make_case(i, rng) for i in range(N_CASES)]

    OUT_DIR.mkdir(exist_ok=True)
    with (OUT_DIR / "testset.jsonl").open("w", encoding="utf-8") as f:
        for case in cases:
            f.write(json.dumps(case, ensure_ascii=False) + "\n")

    examples = OUT_DIR / "examples"
    examples.mkdir(exist_ok=True)
    for case in cases[:4]:   # i primi quattro, uno per layout, per provare la CLI
        (examples / f"{case['id']}.txt").write_text(case["text"], encoding="utf-8")

    print(f"Scritti {len(cases)} casi in {OUT_DIR / 'testset.jsonl'}")
    print(f"Quattro esempi per la CLI in {examples}")


if __name__ == "__main__":
    main()