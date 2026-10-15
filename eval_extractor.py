"""Valuta le versioni del prompt sul test set.

Uso:
    uv run python eval_extractor.py                    # v1 e v2, tutti i casi
    uv run python eval_extractor.py --prompt v2 --limit 5
    uv run python eval_extractor.py --rpm 5            # se ricevi molti errori 429
"""
import argparse
import json
import time
from pathlib import Path

from extractor import PROMPTS, extract
from llm_client import get_client
from metrics import SCALAR_FIELDS, compare_scalars, item_counts, precision_recall_f1, standard_error


def load_cases(path: Path, limit: int | None) -> list[dict]:
    lines = path.read_text(encoding="utf-8").splitlines()
    cases = [json.loads(line) for line in lines if line.strip()]
    return cases[:limit] if limit else cases


def evaluate(version: str, cases: list[dict], client, rpm: int) -> dict:
    min_interval = 60 / rpm
    details = []
    for case in cases:
        t0 = time.perf_counter()
        result = extract(case["text"], version=version, client=client, max_attempts=6)
        got = result.invoice.model_dump(mode="json") if result.ok else None

        scalars = compare_scalars(case["expected"], got)
        tp, fp, fn = item_counts(case["expected"]["line_items"], got["line_items"] if got else None)
        details.append({
            "id": case["id"], "tags": case["tags"], "ok": result.ok,
            "error_kind": result.error_kind, "error_detail": result.error_detail,
            "scalars": scalars, "items": [tp, fp, fn],
            "wrong": {f: [case["expected"][f], got[f] if got else None] for f, ok in scalars.items() if not ok},
            "input_tokens": result.input_tokens, "output_tokens": result.output_tokens,
            "seconds": result.seconds, "raw": result.raw,
        })
        print(f"  {case['id']}: {'ok ' if result.ok else 'NO '} {result.error_kind or ''} {result.error_detail or ''}")
        time.sleep(max(0.0, min_interval - (time.perf_counter() - t0)))   # rispetta il rate limit
    return summarize(version, details)


def summarize(version: str, details: list[dict]) -> dict:
    api_errors = [d for d in details if d["error_kind"] == "api"]
    evaluated = [d for d in details if d["error_kind"] != "api"]   # gli errori API non sono colpa del modello
    n = len(evaluated)
    if n == 0:
        return {"version": version, "n": 0, "api_errors": len(api_errors), "details": details}

    field_acc = {f: sum(d["scalars"][f] for d in evaluated) / n for f in SCALAR_FIELDS}
    tp = sum(d["items"][0] for d in evaluated)
    fp = sum(d["items"][1] for d in evaluated)
    fn = sum(d["items"][2] for d in evaluated)
    precision, recall, f1 = precision_recall_f1(tp, fp, fn)
    record_exact = sum(all(d["scalars"].values()) and d["items"][1] == 0 and d["items"][2] == 0 for d in evaluated) / n
    valid_rate = sum(d["ok"] for d in evaluated) / n
    toks_in = [d["input_tokens"] for d in evaluated if d["input_tokens"] is not None]
    toks_out = [d["output_tokens"] for d in evaluated if d["output_tokens"] is not None]

    return {
        "version": version, "n": n, "api_errors": len(api_errors),
        "valid_rate": valid_rate, "field_accuracy": field_acc,
        "items_precision": precision, "items_recall": recall, "items_f1": f1,
        "record_exact": record_exact, "record_exact_se": standard_error(record_exact, n),
        "mean_input_tokens": sum(toks_in) / len(toks_in) if toks_in else None,
        "mean_output_tokens": sum(toks_out) / len(toks_out) if toks_out else None,
        "mean_seconds": sum(d["seconds"] for d in evaluated) / n,
        "details": details,
    }


def print_report(summaries: list[dict]) -> None:
    print("\n" + "=" * 64)
    for s in summaries:
        print(f"\nPrompt {s['version']}: {s['n']} casi valutati, {s['api_errors']} errori API (esclusi)")
        if s["n"] == 0:
            print("  nessun caso valutabile: riprova o abbassa --rpm")
            continue
        print(f"  JSON valido e coerente : {s['valid_rate']:.2f}")
        print("  Accuratezza per campo (un caso non valido conta come sbagliato):")
        for f, acc in s["field_accuracy"].items():
            print(f"    {f:<16} {acc:.2f}")
        print(f"  Righe: precision {s['items_precision']:.2f} | recall {s['items_recall']:.2f} | F1 {s['items_f1']:.2f}")
        print(f"  Record perfetti        : {s['record_exact']:.2f}  (errore standard +/- {s['record_exact_se']:.2f})")
        tin, tout = s["mean_input_tokens"], s["mean_output_tokens"]
        if tin is not None and tout is not None:
            print(f"  Token medi per caso    : {tin:.0f} in, {tout:.0f} out | {s['mean_seconds']:.1f}s")
    print("\nCasi sbagliati (primi 8 per versione):")
    for s in summaries:
        shown = 0
        for d in s["details"]:
            if d["error_kind"] == "api" or (d["ok"] and not d["wrong"] and d["items"][1] == d["items"][2] == 0):
                continue
            what = d["error_detail"] if not d["ok"] else "; ".join(f"{f}: atteso {e!r}, ottenuto {g!r}" for f, (e, g) in d["wrong"].items())
            print(f"  [{s['version']}] {d['id']} {d['tags']}: {what or 'righe diverse'}")
            shown += 1
            if shown == 8:
                break


def main() -> None:
    parser = argparse.ArgumentParser(description="Valuta le versioni del prompt sul test set.")
    parser.add_argument("--prompt", nargs="+", default=["v1", "v2"], choices=sorted(PROMPTS))
    parser.add_argument("--testset", type=Path, default=Path("data/testset.jsonl"))
    parser.add_argument("--limit", type=int, default=None, help="usa solo i primi N casi (prove veloci)")
    parser.add_argument("--rpm", type=int, default=10, help="richieste al minuto da non superare")
    args = parser.parse_args()

    cases = load_cases(args.testset, args.limit)
    client = get_client()
    summaries = []
    for version in args.prompt:
        print(f"\nValuto il prompt {version} su {len(cases)} casi...")
        summaries.append(evaluate(version, cases, client, args.rpm))

    Path("results").mkdir(exist_ok=True)
    for s in summaries:
        Path("results", f"eval_{s['version']}.json").write_text(
            json.dumps(s, ensure_ascii=False, indent=2), encoding="utf-8")
    print_report(summaries)
    print("\nDettagli completi in results/eval_<versione>.json")


if __name__ == "__main__":
    main()