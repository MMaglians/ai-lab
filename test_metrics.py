from metrics import (compare_scalars, field_correct, item_counts, precision_recall_f1,
                     sign_test_pvalue, standard_error, wilson_interval)


def test_money_tolerance():
    assert field_correct("net_total", 100.0, 100.004)
    assert not field_correct("net_total", 100.0, 100.01)


def test_null_must_be_matched():
    assert field_correct("due_date", None, None)
    assert not field_correct("due_date", None, "2026-01-01")
    assert not field_correct("due_date", "2026-01-01", None)


def test_vat_normalization():
    assert field_correct("supplier_vat", "IT 123.45", "it12345")


def test_text_normalization():
    assert field_correct("supplier_name", "Foo  Srl", "foo srl")


def test_no_extraction_means_all_wrong():
    assert not any(compare_scalars({"currency": "EUR"}, None).values())


def test_item_counts_and_f1():
    exp = [{"description": "A", "quantity": 1, "unit_price": 1.0}, {"description": "B", "quantity": 2, "unit_price": 2.0}]
    got = [{"description": "a", "quantity": 1, "unit_price": 1.0}, {"description": "C", "quantity": 1, "unit_price": 3.0}]
    assert item_counts(exp, got) == (1, 1, 1)
    assert precision_recall_f1(1, 1, 1) == (0.5, 0.5, 0.5)
    assert item_counts(exp, None) == (0, 0, 2)


def test_standard_error():
    assert abs(standard_error(0.5, 100) - 0.05) < 1e-9

def test_wilson_interval_handles_extremes():
    lo, hi = wilson_interval(20, 20)
    assert 0.83 < lo < 0.85 and hi == 1.0
    lo, hi = wilson_interval(0, 20)
    assert lo == 0.0 and 0.15 < hi < 0.17
    assert wilson_interval(10, 20)[0] < 0.5 < wilson_interval(10, 20)[1]


def test_sign_test():
    assert sign_test_pvalue(0, 0) == 1.0
    assert sign_test_pvalue(5, 5) == 1.0
    assert abs(sign_test_pvalue(0, 8) - 2 / 256) < 1e-12