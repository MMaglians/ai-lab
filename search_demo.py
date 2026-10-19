"""Ricerca semantica a mano sul mini corpus: embedding, coseno, hit@k."""

import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

from embed_texts import GeminiEmbedder, embed_cached, format_document, format_query
from retrieval_metrics import hit_at_k, mean
from toy_corpus import DOCS, QUERIES
from vector_math import top_k

CACHE = Path(".cache") / "toy_embeddings.json"

def run(embedder: GeminiEmbedder, cache_path: Path=CACHE, k: int = 3) -> dict:
    doc_ids = [d["id"] for d in DOCS]
    doc_vectors = embed_cached(
        [format_document(d["text"], d["title"]) for d in DOCS], embedder, cache_path
    )
    query_vectors = embed_cached(
        [format_query(q) for q, _ in QUERIES],  embedder, cache_path
    )
    hits1, hitsk = [], []
    for (question, expected), qv in zip(QUERIES, query_vectors):
        idx, scores = top_k(qv, doc_vectors, k=k)
        ranked = [doc_ids[i] for i in idx]
        hits1.append(hit_at_k(ranked, {expected}, 1))
        hitsk.append(hit_at_k(ranked, {expected}, k))
        mark = "OK " if ranked[0] == expected else "--"
        print(f"{mark}{question}")
        print(f"     atteso: {expected}")
        for rank, (i, s) in enumerate(zip(idx, scores), start=1):
            print(f"     {rank}. {doc_ids[i]:<22} {s:.3f}")
    return {"hit@1": mean(hits1), f"hit@{k}": mean(hitsk), "n": len(QUERIES)}

def main() -> None:
    load_dotenv()
    if not os.getenv("GEMINI_API_KEY"):
        raise SystemExit("GEMINI_API_KEY non trovata: controlla il file .env")
    client = genai.Client()
    results = run(GeminiEmbedder(client))
    print(results)
    
if __name__ == "__main__":
    main()
        