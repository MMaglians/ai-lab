"""Streaming: stampa i pezzi appena arrivano e misura TTFT e tempo totale."""
import time

from llm_client import MODEL, get_client

client = get_client()
prompt = "Spiega in 8 righe come funziona un tokenizer, con un esempio."

start = time.perf_counter()
first_token_at = None

stream = client.interactions.create(model=MODEL, input=prompt, stream=True, store=False)
for event in stream:
    if event.event_type == "step.delta" and event.delta.type == "text":
        text = getattr(event.delta, "text", None)
        if text:
            if first_token_at is None:
                first_token_at = time.perf_counter() - start
            print(text, end="", flush=True)

total = time.perf_counter() - start
print(f"\n\nTTFT: {first_token_at:.2f}s | totale: {total:.2f}s")