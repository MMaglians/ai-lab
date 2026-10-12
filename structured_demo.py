"""Primo output strutturato: abstract di un paper -> JSON validato con Pydantic."""
from pydantic import BaseModel, Field, ValidationError

from llm_client import MODEL, get_client, with_retry

class PaperInfo(BaseModel):
    title: str = Field(description="Titolo del paper")
    authors: list[str] = Field(description="Cognomi degli autori, nell'ordine del testo")
    year: int | None = Field(description="Anno di pubblicazione, null se assente")
    keywords: list[str] = Field(description="Da 3 a 5 parole chiave, in inglese")
    
TESTO = """Neural ODEs for meteoroid entry. Rossi, Bianchi and Verdi propose a
physics-informed neural ordinary differential equation to model atmospheric entry
of meteoroids, trained on 12,000 synthetic trajectories."""

client = get_client()
interaction = with_retry(lambda: client.interactions.create(
    model = MODEL,
    input=f"Estrai i metadati dal testo seguente.\n\n{TESTO}",
    response_format={
        "type": "text",
        "mime_type": "application/json",
        "schema_": PaperInfo.model_json_schema(),
    },
    store=False,
))

try:
    info = PaperInfo.model_validate_json(interaction.output_text)
    print(info.model_dump_json(indent=2))
except ValidationError as e:
    print("JSON non valido rispetto allo schema:\n", e)