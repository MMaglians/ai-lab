"""Genera un test set PIU' DIFFICILE: stesse fatture sintetiche, ma con 'rumore' realistico.

Il rumore NON cambia la risposta attesa: aggiunge solo distrattori (dati del cliente, IBAN,
data di consegna, note a piede di pagina) e spezza il documento con un'interruzione di pagina.
Uso:  uv run python make_hard_testset.py
"""
import json
import random
from datetime import date, timedelta
from pathlib import Path

from make_testset import fmt_date, make_case

SEED = 7
N_CASES = 40
OUT = Path("data/testset_hard.jsonl")

CUSTOMERS = ["Alfa Costruzioni S.r.l.", "Delta Moda S.p.A.", "Omega Servizi S.n.c.", "Sigma Trasporti Srl"]

def fake_vat(rng: random.Random) -> str:
    return "IT" + "".join(str(rng.randint(0, 9)) for _ in range(11))

def fake_iban(rng: random.Random) -> str:
    return "IT" + str(rng.randint(10, 99)) + "X" + "".join(str(rng.randint(0, 9)) for _ in range(22))

def add_noise(case: dict, rng: random.Random) -> dict:
    lines = case["text"].split("\n")
    expected = case["expected"]
    # 1) blocco cliente con P.IVA e codice fiscale: due numeri che NON vanno estratti come fornitore
    delivery = fmt_date(
        date.fromisoformat(expected["issue_date"]) + timedelta(days=rng.randint(1, 9)),
        "slash",
    )
    customer_block = [
        f"Cliente: {rng.choice(CUSTOMERS)}",
        f"P.IVA cliente: {fake_vat(rng)}  Codice fiscale: {''.join(str(rng.randint(0, 9)) for _ in range(11))}",
        f"Data consegna: {delivery}  Rif. DDT n. {rng.randint(1000, 9999)}",
        "",
    ]
    lines[1:1] = customer_block

    # 2) interruzione di pagina a meta' documento
    middle = len(lines) // 2
    lines.insert(middle, f"--- segue a pagina 2 --- Pag. 1/2 --- (protocollo interno n. {rng.randint(100, 999)})")

    # 3) piede di pagina con IBAN, PEC e note
    lines += [
        "",
        f"Coordinate bancarie: IBAN {fake_iban(rng)}",
        f"PEC: amministrazione{rng.randint(1, 99)}@pec.example.it - Tel. 0{rng.randint(10, 99)} {rng.randint(100000, 999999)}",
        f"Pag. 2/2 - Documento generato il {fmt_date(date(2026, 10, 1), 'slash')}",
    ]

    return {**case, "text": "\n".join(lines), "tags": case["tags"] + ["rumore"]}

def main() -> None:
    rng = random.Random(SEED)
    cases = []
    for i in range(N_CASES):
        case = make_case(i, rng)
        case = add_noise(case, rng)
        case["id"] = f"hard_{i:02d}"
        cases.append(case)
        
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        for case in cases:
            f.write(json.dumps(case, ensure_ascii=False) + "\n")
    print(f"Scritti {len(cases)} casi difficili in {OUT}")
 

if __name__ == "__main__":
    main() 