"""Prima chiamata con l'SDK ufficiale e la Interactions API."""
import time

from llm_client import MODEL, get_client, with_retry

client = get_client()

#client.interactions.create() è la chiamata vera all'API
def ask(prompt: str, temperature: float = 0.7) -> str:
    start = time.perf_counter() #restituisce orologio in secondi 
    interaction = with_retry(lambda: client.interactions.create(
        model=MODEL,
        input=prompt,
        system_instruction="Sei un tutor di AI. Rispondi in italiano, in massimo 3 frasi.",
        generation_config={"temperature": temperature},
        store=False,   # non salvare la conversazione sui server Google
    ))
    print(f"[{time.perf_counter() - start:.2f}s, temperature={temperature}]")
    #decommenta la riga sotto se vuoi cercare i conteggi dei token
    #print(interaction)
    return interaction.output_text


if __name__ == "__main__":
    domanda = "Cos'è il rate limit di un'API?"
    for t in (0.0, 1.0): #variamo la temperatura
        print(ask(domanda, temperature=t), "\n")