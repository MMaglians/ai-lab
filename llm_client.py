"""Client Gemini condiviso: creazione del client e retry con backoff."""
import os
import random
import time
from collections.abc import Callable, Iterator
from typing import TypeVar

from dotenv import load_dotenv
from google import genai #SDK di Google

load_dotenv()

MODEL = "gemini-3.5-flash-lite"
RETRYABLE_STATUS = {429, 500, 503} #rate limit e problemi lato server

T = TypeVar("T") # è un generico

def get_client() -> genai.Client:
    """Crea il client leggendo la chiave dal .env"""
    return genai.Client(api_key= os.environ["GEMINI_API_KEY"])

#---Funzioni pure easy to test---

def backoff_delay(attempt: int, base: float = 1.0, jitter = 0.5) -> float:
    """Attesa prima del tentativo successivo: base * 2^(attempt-1) + rumore casuale."""
    return base * 2**(attempt - 1) + random.uniform(0, jitter)

def status_of(exc: Exception) -> int | None:
    """Prova a estrarre il codice HTTP da un'eccezione dell'SDK."""
    for attr in ("code", "status_code", "status"):
        value = getattr(exc, attr, None)
        if isinstance(value, int):
            return value
    return None

#--- Funzione di I/O---

def with_retry(fn: Callable[[], T], max_attempts: int = 4) -> T:
    """Esegue fn; se fallisce con 429/5xx riprova con exponential backoff."""
    for attempt in range(1, max_attempts+1):
        try:
            return fn()
        except Exception as exc:
            status = status_of(exc)
            if status not in RETRYABLE_STATUS or attempt == max_attempts:
                raise
            delay = backoff_delay(attempt)
            print(f"[retry] errore {status}, tentativo {attempt}/{max_attempts}, attendo {delay:.1f}s")
            time.sleep(delay)
    raise RuntimeError("non raggiungibile")

def stream_events(
    client: genai.Client,
    prompt: str,
    system_instruction: str | None = None,
    temperature: float=0.7,
) -> Iterator[tuple[str, object]]:
    """Genera tuple (tipo, contenuto).

    ("text", "pezzo di testo")                  per ogni frammento di risposta
    ("usage", {"input": n, "output": m})        una volta, a fine flusso
    Un errore comunicato dentro il flusso solleva RuntimeError.
    """
    kwargs = {
        "model": MODEL,
        "input": prompt,
        "generation_config": {"temperature": temperature},
        "stream": True,
        "store": False,
    }
    if system_instruction:
        kwargs["system_instruction"] = system_instruction
    
    # il retry copre solo l'apertura del flusso: a meta' flusso non si ritenta
    stream = with_retry(lambda: client.interactions.create(**kwargs))

    for event in stream:
        kind = event.event_type
        if kind == "step.delta" and event.delta.type == "text":
            text = getattr(event.delta, "text", None)
            if text:
                yield ("text", text)
        elif kind == "interaction.completed":
            usage = event.interaction.usage
            yield ("usage", {
                "input": usage.total_input_tokens if usage else None,
                "output": usage.total_output_tokens if usage else None,
            })
        elif kind == "error":
            message = event.error.message if event.error else "errore sconosciuto"
            raise RuntimeError(message)
            