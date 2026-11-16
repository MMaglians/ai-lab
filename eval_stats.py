"""Statistica per i report di valutazione: funzioni pure, testabili senza rete.

Bootstrap, confronto appaiato tra due configurazioni e accordo tra due valutatori.
Riusa Wilson e il test dei segni gia' scritti in metrics.py (settimana 2).
"""
import numpy as np

from metrics import sign_test_pvalue, wilson_interval


def to_array(values) -> np.ndarray:
    """Lista di bool o numeri -> array di float (True = 1.0)."""
    return np.asarray(values, dtype=float)


def bootstrap_ci(values, stat=np.mean, n_boot: int = 10_000,
                 level: float = 0.95, seed: int = 0) -> tuple[float, float, float]:
    """Stima puntuale e intervallo bootstrap percentile.

    Ricampiona n valori CON reinserimento, n_boot volte, calcola la statistica su
    ogni ricampionamento e prende i quantili (1-level)/2 e (1+level)/2.
    """
    x = to_array(values)
    n = len(x)
    if n == 0:
        raise ValueError("servono dei valori")
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, n, size=(n_boot, n))          # n_boot righe di indici
    boot = np.array([stat(x[row]) for row in idx])
    alpha = (1 - level) / 2
    low, high = np.quantile(boot, [alpha, 1 - alpha])
    return float(stat(x)), float(low), float(high)


def proportion_summary(successes_list) -> dict:
    """Per una metrica si/no: k/n, Wilson e bootstrap a confronto."""
    x = to_array(successes_list)
    k, n = int(x.sum()), len(x)
    w_low, w_high = wilson_interval(k, n)
    _, b_low, b_high = bootstrap_ci(x)
    return {"k": k, "n": n, "p": k / n,
            "wilson": (round(w_low, 3), round(w_high, 3)),
            "bootstrap": (round(b_low, 3), round(b_high, 3))}
    
def paired_counts(a, b) -> dict:
    """Tabella 2x2 di due configurazioni sulle STESSE domande (a e b: liste di bool)."""
    a, b = to_array(a).astype(bool), to_array(b).astype(bool)
    if len(a) != len(b):
        raise ValueError("le due liste devono riferirsi alle stesse domande")
    return {"entrambe_giuste": int((a & b).sum()),
            "solo_a": int((a & ~b).sum()),       # a giusta, b sbagliata
            "solo_b": int((~a & b).sum()),       # b giusta, a sbagliata
            "entrambe_sbagliate": int((~a & ~b).sum())}


def mcnemar_exact(a, b) -> float:
    """McNemar esatto = test dei segni sulle sole coppie discordanti."""
    t = paired_counts(a, b)
    return sign_test_pvalue(t["solo_a"], t["solo_b"])


def paired_bootstrap_diff(a, b, n_boot: int = 10_000, level: float = 0.95,
                          seed: int = 0) -> tuple[float, float, float]:
    """Differenza media (b - a) con IC bootstrap, ricampionando le DOMANDE (le coppie)."""
    a, b = to_array(a), to_array(b)
    if len(a) != len(b):
        raise ValueError("le due liste devono riferirsi alle stesse domande")
    return bootstrap_ci(b - a, n_boot=n_boot, level=level, seed=seed)


def cohen_kappa(r1, r2) -> float:
    """Kappa di Cohen tra due valutatori sulle stesse voci (etichette qualsiasi)."""
    r1, r2 = list(r1), list(r2)
    if len(r1) != len(r2) or not r1:
        raise ValueError("servono due liste della stessa lunghezza, non vuote")
    n = len(r1)
    labels = sorted(set(r1) | set(r2), key=str)
    p_o = sum(x == y for x, y in zip(r1, r2)) / n                    # accordo osservato
    p_e = sum((r1.count(c) / n) * (r2.count(c) / n) for c in labels)  # accordo atteso per caso
    if p_e == 1.0:
        return float("nan")    # entrambi usano una sola etichetta: kappa non e' definito
    return (p_o - p_e) / (1 - p_e)