"""FAISS: indice esatto (Flat) e confronto con la ricerca a mano in NumPy."""

import numpy as np

import faiss
from vector_math import normalize, top_k


def build_flat_ip_index(vectors: np.ndarray) -> faiss.IndexFlatIP:
    """Indice esatto a prodotto scalare. Con vettori normalizzati: prodotto scalare == coseno."""
    data = np.ascontiguousarray(normalize(vectors), dtype=np.float32)
    index = faiss.IndexFlatIP(data.shape[1])
    index.add(data)
    return index


def search(index: faiss.Index, query: np.ndarray, k: int = 3):
    q = np.ascontiguousarray(normalize(query).reshape(1, -1), dtype=np.float32)
    scores, ids = index.search(q, min(k, index.ntotal))
    return ids[0], scores[0]


def main() -> None:
    rng = np.random.default_rng(0)
    vectors = rng.normal(size=(1000, 64)).astype(np.float32)
    query = rng.normal(size=64).astype(np.float32)

    index = build_flat_ip_index(vectors)
    print("vettori nell'indice:", index.ntotal, "| dimensione:", index.d)

    ids_faiss, scores_faiss = search(index, query, k=5)
    ids_numpy, scores_numpy = top_k(query, vectors, k=5)
    print("FAISS :", list(ids_faiss), np.round(scores_faiss, 4))
    print("NumPy :", list(ids_numpy), np.round(scores_numpy, 4))
    print("stessi indici?", list(ids_faiss) == list(ids_numpy))


if __name__ == "__main__":
    main()