"""CLI: estrae i dati di una fattura da un file di testo e stampa JSON validato.

Uso:
    uv run python extract_cli.py data/examples/case_00.txt
    uv run python extract_cli.py data/examples/case_00.txt --prompt v1
    type fattura.txt | uv run python extract_cli.py -
Codice di uscita: 0 = ok, 1 = estrazione fallita.
"""
import argparse
import sys
from pathlib import Path

from extractor import PROMPTS, extract


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Estrae i dati di una fattura da testo libero.")
    parser.add_argument("path", help="file di testo da leggere, oppure - per leggere da stdin")
    parser.add_argument("--prompt", choices=sorted(PROMPTS), default="v2", help="versione del prompt")
    args = parser.parse_args(argv)

    text = sys.stdin.read() if args.path == "-" else Path(args.path).read_text(encoding="utf-8")

    result = extract(text, version=args.prompt)
    if not result.ok:
        print(f"Estrazione fallita ({result.error_kind}): {result.error_detail}", file=sys.stderr)
        return 1
    print(result.invoice.model_dump_json(indent=2))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")   # evita errori di codifica sul terminale Windows
    sys.stdin.reconfigure(encoding="utf-8")
    sys.exit(main())