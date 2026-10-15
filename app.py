"""Servizio FastAPI: /health e /chat (risposta in streaming SSE)."""
import logging
from collections.abc import Iterable
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.sse import EventSourceResponse, ServerSentEvent
from google import genai
from pydantic import BaseModel, Field

from llm_client import MODEL, get_client, status_of, stream_events

logger = logging.getLogger("ai_lab.chat")

SYSTEM = "Sei un tutor di AI. Rispondi in italiano, in modo chiaro e conciso."

app = FastAPI(title="ai-lab chat", version="0.1.0")

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)

@lru_cache
def client_dep() -> genai.Client:
    """Un solo client per tutto il processo (e sostituibile nei test)."""
    return get_client()

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model": MODEL}
 
@app.post("/chat", response_class=EventSourceResponse)
def chat(
    req: ChatRequest,
    client: Annotated[genai.Client, Depends(client_dep)],
) -> Iterable[ServerSentEvent]:
    try:
        for kind, payload in stream_events(client, req.message, SYSTEM, req.temperature):
            if kind == "text":
                yield ServerSentEvent(data={"text": payload}, event="token")
            else:
                yield ServerSentEvent(data=payload, event="usage")
    except Exception as exc:
        # lo stato HTTP e' gia' 200: l'errore va comunicato dentro il flusso
        logger.exception("errore durante lo streaming")
        yield ServerSentEvent(
            data={"error": type(exc).__name__, "status": status_of(exc)},
            event="error",
        )
        return
    yield ServerSentEvent(raw_data="[DONE]", event="done")