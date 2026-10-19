"""HNSW contro ricerca esatta: velocita' e recall (nessuna API, vettori sintetici).
Non uso API. Genero 50.000 vettori sintetici raggruppati in cluster e confronto.
"""

import time

import numpy as np

import faiss
from vector_math import normalize

N, D, N_QUERIES, K = 50_000, 128, 200, 10

def clustered_vectors(n: int, d: int, n_clusters: int=100, seed: int=0) -> np.ndarray:
    """Vettori raggruppati in cluster, un po' piu' simili ai dati reali di rumore puro."""
    rng = np.random.default_rng(seed)
    centers = rng.normal(size=(n_clusters, d))
    labels = rng.integers(0, n_clusters, size=n)
    data = centers[labels] + 0.6 * rng.normal(size=(n,d))
    return normalize(data).astype(np.float32)

def main() -> None:
    data = clustered_vectors(N, D)
    queries = clustered_vectors(N_QUERIES, D, seed = 1)
    
    #ricerca esatta
    flat = faiss.IndexFlatIP(D) 
    flat.add(data)
    t0 = time.perf_counter()
    _, truth = flat.search(queries, K)
    t_flat = time.perf_counter()-t0
    print(f"Flat (esatto): {t_flat * 1000 / N_QUERIES:.2f} ms per query")
    
    #ANN:
    hnsw = faiss.IndexHNSWFlat(D, 32, faiss.METRIC_INNER_PRODUCT) # M=32 vicini per nodo
    hnsw.hnsw.efConstruction = 100 #ampiezza di ricerca durante la costruzione
    t0 = time.perf_counter()
    hnsw.add(data)
    print(f"HNSW: costruzione in {time.perf_counter() - t0:.1f} s")
    
    for ef in (8, 16, 64, 256):
        hnsw.hnsw.efSearch = ef #ampiezza di ricerca durante query
        t0 = time.perf_counter()
        _, found = hnsw.search(queries, K)
        t = time.perf_counter() - t0
        recall = np.mean([len(set(f) & set(tr)) / K for f, tr in zip(found, truth)])
        print(f"  efSearch={ef:<4} recall@{K}={recall:.3f}  {t * 1000 / N_QUERIES:.2f} ms per query")
    
if __name__ == "__main__":
    main()