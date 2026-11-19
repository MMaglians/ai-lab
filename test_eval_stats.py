import math

import pytest

from eval_stats import (bootstrap_ci, bootstrap_kappa, cohen_kappa, mcnemar_exact,
                        paired_bootstrap_diff, paired_counts, proportion_summary)

def test_bootstrap_contiene_la_stima_ed_e_riproducibile():
    x = [True] * 15 + [False] * 5
    p, low, high = bootstrap_ci(x, seed=0)
    assert p == 0.75
    assert low < p < high
    assert bootstrap_ci(x, seed=0) == (p, low, high)      # stesso seed, stesso risultato


def test_bootstrap_degenera_al_bordo():
    # 20/20: ogni ricampionamento e' tutto 1, l'intervallo collassa (Wilson no)
    assert bootstrap_ci([True] * 20) == (1.0, 1.0, 1.0)
    s = proportion_summary([True] * 20)
    assert s["wilson"][0] < 0.9 and s["bootstrap"] == (1.0, 1.0)


def test_paired_counts_e_mcnemar():
    a = [True, True, False, False, True]
    b = [True, False, True, True, True]
    t = paired_counts(a, b)
    assert t == {"entrambe_giuste": 2, "solo_a": 1, "solo_b": 2, "entrambe_sbagliate": 0}
    assert mcnemar_exact(a, b) == 1.0           # 1 contro 2 discordanti: nessuna prova


def test_mcnemar_ignora_le_coppie_concordanti():
    a = [True] * 90 + [False] * 10
    b = [True] * 90 + [True] * 10                # b migliora 10 domande, ne peggiora 0
    assert mcnemar_exact(a, b) == pytest.approx(2 / 2**10)


def test_paired_bootstrap_diff_segno():
    a = [False] * 10 + [True] * 10
    b = [True] * 20
    d, low, high = paired_bootstrap_diff(a, b)
    assert d == 0.5 and 0 < low <= d <= high


def test_liste_di_lunghezza_diversa():
    with pytest.raises(ValueError):
        paired_counts([True], [True, False])


def test_kappa_esempio_da_manuale():
    # 50 voci: si/si 20, si/no 5, no/si 10, no/no 15 -> p_o=0.70, p_e=0.50, kappa=0.40
    r1 = ["si"] * 25 + ["no"] * 25
    r2 = ["si"] * 20 + ["no"] * 5 + ["si"] * 10 + ["no"] * 15
    assert cohen_kappa(r1, r2) == pytest.approx(0.40)


def test_kappa_accordo_perfetto_e_casuale():
    assert cohen_kappa([1, 0, 1, 0], [1, 0, 1, 0]) == 1.0
    assert cohen_kappa([1, 1, 0, 0], [1, 0, 1, 0]) == 0.0
    assert math.isnan(cohen_kappa([1, 1, 1], [1, 1, 1]))
    


def test_bootstrap_kappa_contiene_la_stima():
    r1 = ["si"] * 25 + ["no"] * 25
    r2 = ["si"] * 20 + ["no"] * 5 + ["si"] * 10 + ["no"] * 15
    k, low, high, undefined = bootstrap_kappa(r1, r2, n_boot=2_000)
    assert k == pytest.approx(0.40) and low < k < high and undefined == 0.0


def test_bootstrap_kappa_segnala_i_casi_non_definiti():
    # 1 solo negativo su 10: molti ricampionamenti non lo contengono e kappa non e' definito
    r = [True] * 9 + [False]
    _, _, _, undefined = bootstrap_kappa(r, r, n_boot=2_000)
    assert 0.2 < undefined < 0.5          # circa (9/10)^10 = 0,35