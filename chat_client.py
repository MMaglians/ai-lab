"""Client di prova per /chat: legge gli eventi SSE e misura il TTFT lato client.

Uso:  uv run python chat_client.py "Cos'e' un tokenizer?"
"""
import json
import sys
import time

import httpx

URL = "http://127.0.0.1:8000/chat"


def main(message: str) -> None:
    start = time.perf_counter()
    first_token = None
    event = None
    usage = None

    with httpx.stream("POST", URL, json={"message": message}, timeout=60) as response:
        print(f"[HTTP {response.status_code}]")
        if response.status_code != 200:
            print(response.read().decode())
            return
        for line in response.iter_lines():
            if line.startswith("event:"):
                event = line.split(":", 1)[1].strip()
            elif line.startswith("data:"):
                data = line.split(":", 1)[1].strip()
                if event == "token":
                    if first_token is None:
                        first_token = time.perf_counter() - start
                    print(json.loads(data)["text"], end="", flush=True)
                elif event == "usage":
                    usage = json.loads(data)
                elif event == "error":
                    print(f"\n[ERRORE NEL FLUSSO] {data}")
                elif event == "done":
                    break

    total = time.perf_counter() - start
    ttft = f"{first_token:.2f}s" if first_token is not None else "n/d"
    print(f"\n\nTTFT lato client: {ttft} | totale: {total:.2f}s | token: {usage}")


if __name__ == "__main__":
    main(" ".join(sys.argv[1:]) or "Spiega in 5 righe cos'e' un tokenizer.")