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
| Qwen3-0.6B | Colab (T4) | [10.41] | 35 | [70] | nessuna licenza (si paga la GPU) |
| Qwen3-1.7B | Colab (T4) | [14.40] | 35 | [71] | nessuna licenza (si paga la GPU) |
| gemini-3.5-flash-lite | API | [2.02] | 20 | [93] | circa $[0.00024] |

Prezzi Gemini: $0,30 input e $2,50 output per milione di token (listino ufficiale, 8 ottobre 2026; con il tier gratuito la spesa effettiva è zero).

### Cosa ho imparato
- **Il modello non sceglie il token.** La rete produce una distribuzione di probabilità; temperatura e top-p decidono come estrarre da essa.
- **Con T = 0 il testo è identico a ogni esecuzione; con T > 0 no.** Un token diverso cambia tutto il seguito perché rientra nell'input.
- **La lingua cambia il costo.** A parità di significato, l'italiano richiede il 50% di token in più dell'inglese (57 contro 38 token sulla frase di prova).
- **Un token improbabile estratto per caso si propaga:** per questo si taglia la coda con top-p.

### Limiti
Confronto su un solo prompt, con valutazione soggettiva e tempi variabili tra esecuzioni: è un assaggio, non un benchmark. Il conteggio dei token di Qwen è solo una stima di quello di Gemini (tokenizer diversi).

## Come riprodurre
1. Apri il notebook su Colab con il pulsante sopra e scegli **Runtime → Change runtime type → T4 GPU**.
2. Per le parti con Gemini, crea un secret `GEMINI_API_KEY` (icona a chiave) e attiva **Notebook access**.
3. **Runtime → Run all**.

Gli script locali (`api_demo.py`, `gemini_demo.py`) usano un file `.env` con la chiave: copia `.env.example` in `.env` e compilalo. Il file `.env` non viene mai caricato su Git.

## Struttura
Controlla con `dir` e scrivi solo cartelle e file che esistono davvero (`notebooks/`, `docs/`, `src/ai_lab/`, gli script, i test).

## Licenza
MIT