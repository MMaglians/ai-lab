# ai-lab

Laboratorio personale per imparare LLM, API, RAG e agenti AI, con esperimenti riproducibili e numeri misurati.

## Settimana 1: LLM sotto il cofano

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/MMaglians/ai-lab/blob/main/notebooks/01_llm_sotto_il_cofano.ipynb)

Notebook che apre la scatola di un modello linguistico: dal testo ai token, dai logit alle probabilità, fino alla generazione scritta a mano.

**Cosa contiene**
- Tokenizer e logit di `Qwen3-0.6B` e `Qwen3-1.7B` con `transformers`.
- Temperatura e top-p implementati da zero e confrontati con i parametri dell'API Gemini.
- Tre esercizi applicati: stima dei costi per lingua, classificatore con soglia di confidenza, punteggio di qualità del testo (perplessità).

### Risultati
Stesso prompt ("Spiega in tre frasi a un cliente non tecnico cos'è un modello linguistico"), generazione deterministica, GPU T4 di Colab, mediana di 3 esecuzioni.

| Modello | Dove gira | Secondi | Token in | Token out | Costo per richiesta |
|---|---|---|---|---|---|
| Qwen3-0.6B | Colab (T4) | 10.51 | 35 | 70 | nessuna licenza (si paga la GPU) |
| Qwen3-1.7B | Colab (T4) | 14.40 | 35 | 71 | nessuna licenza (si paga la GPU) |
| gemini-3.5-flash-lite | API | 2.02 | 20 | 93 | circa $0.00024 |

Prezzi Gemini: $0,30 input e $2,50 output per milione di token (listino ufficiale, 8 ottobre 2026; con il tier gratuito la spesa effettiva è zero).

### Cosa ho imparato
- **Il modello non sceglie il token.** La rete produce una distribuzione di probabilità; temperatura e top-p decidono come estrarre da essa.
- **Con T = 0 il testo è identico a ogni esecuzione; con T > 0 no.** Un token diverso cambia tutto il seguito perché rientra nell'input.
- **La lingua cambia il costo.** A parità di significato, l'italiano richiede il 50% di token in più dell'inglese (57 contro 38 token sulla frase di prova).
- **Un token improbabile estratto per caso si propaga:** per questo si taglia la coda con top-p.

### Limiti
Confronto su un solo prompt, con valutazione soggettiva e tempi variabili tra esecuzioni: è un assaggio, non un benchmark. Il conteggio dei token di Qwen è solo una stima di quello di Gemini (tokenizer diversi).

## Settimana 2: API, prompt e output strutturati

Dalla prima chiamata con l'SDK di Gemini a un estrattore di fatture con output validato. Il progetto completo, con valutazione e README in inglese, è nel repository [invoice-extractor](https://github.com/MMaglians/invoice-extractor).

**Cosa contiene**
- Client condiviso con retry e backoff esponenziale su 429, 500 e 503 (`llm_client.py`).
- Streaming con misura del tempo al primo token (`stream_demo.py`).
- Zero-shot contro few-shot su una classificazione a etichette fisse (`fewshot_demo.py`).
- Primo output strutturato validato con Pydantic (`structured_demo.py`).
- Servizio FastAPI con `/health` e `/chat` in streaming SSE, più un client che misura il TTFT (`app.py`, `chat_client.py`).
- Estrattore di fatture, test set sintetici e valutazione (`extractor.py`, `make_hard_testset.py`, `eval_extractor.py`).

**Come provarlo**
```
uv run fastapi dev app.py
uv run python chat_client.py "Cos'e' un tokenizer?"
uv run python extract_cli.py data/examples/case_00.txt
```

**Cosa ho imparato**
- Una chiamata a un LLM è una chiamata di rete: si ritenta solo sugli errori transitori, con attese crescenti e casuali.
- "Rispondi in JSON" non basta: servono uno schema, la validazione e controlli di coerenza sui numeri.
- Un errore di rete e un errore del modello vanno tenuti separati, anche nella valutazione.

## Settimana 3: embedding e ricerca

Ricerca per significato scritta a mano, poi con FAISS, e confronto tra ricerca esatta e approssimata. Il progetto completo (RAG sull'EU AI Act con citazioni e valutazione) è nel repository [AI-act-QA](https://github.com/MMaglians/AI-act-QA).

**Cosa contiene**
- Similarità coseno e ricerca top-k in NumPy (`vector_math.py`).
- Embedding con Gemini, formati diversi per documenti e domande, cache su disco (`embed_texts.py`).
- Chunking a parole con sovrapposizione (`chunking.py`) e metriche hit@k e recall@k (`retrieval_metrics.py`).
- Ricerca semantica su un mini corpus originale di 12 testi (pallavolo, chitarra, giapponese) con 12 domande (`toy_corpus.py`, `search_demo.py`).
- FAISS esatto confrontato con la ricerca in NumPy (`faiss_demo.py`).
- HNSW contro ricerca esatta su 50.000 vettori sintetici (`hnsw_demo.py`).

### Risultati
- Mini corpus, 12 domande: hit@1 = 1.0, hit@3 = 1.0.
- FAISS `IndexFlatIP` restituisce gli stessi risultati della ricerca in NumPy.
- HNSW (M = 32, efConstruction = 100), 200 query, k = 10; ricerca esatta 0.29 ms per query:

| efSearch | recall@10 | ms per query |
|---|---|---|
| 8 | 0.223 | 0.01 |
| 16 | 0.297 | 0.02 |
| 64 | 0.604 | 0.05 |
| 256 | 0.872 | 0.11 |

**Cosa ho imparato**
- Con vettori normalizzati il prodotto scalare è il coseno: si normalizza una volta e si usa un indice a prodotto scalare.
- HNSW scambia un po' di recall con la velocità; `efSearch` regola il compromesso. Con poche migliaia di vettori la ricerca esatta basta.

### Limiti
Mini corpus di 12 testi scritti da me e 12 domande: un test didattico, non un benchmark. I tempi dipendono dalla macchina.


## Come riprodurre
1. Apri il notebook su Colab con il pulsante sopra e scegli **Runtime → Change runtime type → T4 GPU**.
2. Per le parti con Gemini, crea un secret `GEMINI_API_KEY` (icona a chiave) e attiva **Notebook access**.
3. **Runtime → Run all**.

Gli script locali (`api_demo.py`, `gemini_demo.py`) usano un file `.env` con la chiave: copia `.env.example` in `.env` e compilalo. Il file `.env` non viene mai caricato su Git.

## Struttura
- `notebooks/`: notebook della settimana 1 (`01_llm_sotto_il_cofano.ipynb`).
- `docs/`: note in linguaggio non tecnico (`llm_per_non_tecnici.md`).
- `data/`: test set sintetici di fatture (`testset.jsonl`, `testset_hard.jsonl`) ed esempi in `data/examples/`.
- Settimana 0: `api_demo.py`, `gemini_demo.py`, `gemini_demo_locale.py`.
- Settimana 2: `llm_client.py`, `sdk_demo.py`, `stream_demo.py`, `fewshot_demo.py`, `structured_demo.py`, `app.py`, `chat_client.py`, `schemas.py`, `extractor.py`, `extract_cli.py`, `make_testset.py`, `make_hard_testset.py`, `metrics.py`, `eval_extractor.py`, `fakes.py`.
- Settimana 3: `vector_math.py`, `embed_texts.py`, `chunking.py`, `retrieval_metrics.py`, `toy_corpus.py`, `search_demo.py`, `faiss_demo.py`, `hnsw_demo.py`.
- `test_*.py`: test unitari, eseguibili con `uv run pytest`; nessuno chiama la rete.

## Licenza
MIT