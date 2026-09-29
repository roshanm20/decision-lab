import copy
import json
import math

import pytest

from decisionlab.consulting.unit_economics import (
    EXAMPLE, combined_cases, contribution, expected_months, ltv, metrics, parse_model, payback,
    sensitivity,
)

BASE = {"arpu": 2000, "gross_margin": 0.6, "variable_cost": 200, "monthly_churn": 0.1, "cac": 5000}


def brute_force_payback_month(cm, churn, cac, limit=1000):
    """First whole month by which expected cumulative contribution covers CAC,
    found by adding up month by month. Written separately from the formula."""
    total, alive = 0.0, 1.0
    for month in range(1, limit + 1):
        total += cm * alive
        alive *= 1 - churn
        if total >= cac:
            return month
    return None


def test_worked_example_by_hand():
    # contribution = 2000 x 0.6 - 200 = 1000. LTV = 1000 / 0.1 = 10,000. CAC 5000 gives 2x.
    m = metrics(BASE, None)
    assert m["cm"] == pytest.approx(1000)
    assert m["ltv"] == pytest.approx(10_000)
    assert m["ratio"] == pytest.approx(2.0)
    assert m["naive"] == pytest.approx(5.0)


def test_payback_allows_for_churn_and_matches_brute_force():
    # n = ln(1 - 5000 x 0.1 / 1000) / ln(0.9) = ln(0.5) / ln(0.9) = 6.579
    n = payback(1000, 0.1, 5000, None)
    assert n == pytest.approx(6.579, abs=0.001)
    assert math.ceil(n) == brute_force_payback_month(1000, 0.1, 5000) == 7


def test_payback_never_when_churn_eats_the_margin():
    # Lifetime contribution is capped at 1000 / 0.1 = 10,000, below a CAC of 20,000.
    assert math.isinf(payback(1000, 0.1, 20_000, None))
    assert brute_force_payback_month(1000, 0.1, 20_000, limit=2000) is None


def test_horizon_truncates_ltv():
    # 1000 x (1 - 0.9^12) / 0.1 = 7175.7, worked by hand from 0.9^12 = 0.28243
    assert ltv(1000, 0.1, 12) == pytest.approx(7175.7, abs=0.1)
    # month by month, a separate route to the same number
    assert sum(1000 * 0.9 ** t for t in range(12)) == pytest.approx(ltv(1000, 0.1, 12))


def test_horizon_can_make_payback_never():
    assert payback(1000, 0.1, 5000, 12) == pytest.approx(6.579, abs=0.001)
    assert math.isinf(payback(1000, 0.1, 5000, 6))


def test_zero_churn_with_horizon():
    assert expected_months(0, 24) == 24
    assert payback(500, 0, 6000, 24) == pytest.approx(12)


def test_total_churn_means_one_month():
    assert expected_months(1.0, None) == pytest.approx(1.0)
    assert payback(1000, 1.0, 800, None) == pytest.approx(0.8)
    assert math.isinf(payback(1000, 1.0, 1500, None))


def test_negative_contribution_never_pays_back():
    assert contribution(100, 0.5, 80) == pytest.approx(-30)
    assert math.isinf(payback(-30, 0.05, 1000, None))


def test_example_parses_and_reconciles_with_hand_values():
    inputs, horizon = parse_model(EXAMPLE)
    assert horizon == 36
    m = metrics({k: d["value"] for k, d in inputs.items()}, horizon)
    assert m["cm"] == pytest.approx(975)  # 1500 x 0.75 - 150
    assert m["life"] == pytest.approx((1 - 0.96 ** 36) / 0.04)
    assert m["ratio"] == pytest.approx(1.564, abs=0.001)
    assert m["payback"] == pytest.approx(16.6, abs=0.05)


def test_example_file_matches_embedded_example():
    with open("examples/unit_economics_restaurant_saas.json", encoding="utf-8") as fh:
        assert json.load(fh) == EXAMPLE


def test_sensitivity_is_ranked_and_cac_leads_in_example():
    inputs, horizon = parse_model(EXAMPLE)
    rows = sensitivity(inputs, horizon)
    assert rows[0][0] == "Cost to acquire one customer"
    assert [r[3] for r in rows] == sorted((r[3] for r in rows), reverse=True)


def test_combined_cases_move_every_input_against_and_for_you():
    inputs, horizon = parse_model(EXAMPLE)
    bad, good = combined_cases(inputs, horizon)
    assert bad["cm"] == pytest.approx(1200 * 0.65 - 250)
    assert bad["cac"] == 20_000 and good["cac"] == 8_000
    assert bad["ratio"] < metrics({k: d["value"] for k, d in inputs.items()}, horizon)["ratio"] < good["ratio"]


def model(**changes):
    m = copy.deepcopy(EXAMPLE)
    for key, patch in changes.items():
        if patch is None:
            del m["inputs"][key]
        else:
            m["inputs"][key].update(patch)
    return m


@pytest.mark.parametrize("bad, message", [
    ([1, 2], "JSON object"),
    ({"name": "x"}, "'inputs'"),
    (model(cac=None), "missing input 'cac'"),
    (model(cac={"value": "12000"}), "plain number"),
    (model(cac={"value": True}), "plain number"),
    (model(cac={"value": 0, "low": 0, "high": 0}), "above zero"),
    (model(arpu={"low": 2000}), "low <= value <= high"),
    (model(arpu={"low": None}), "both low and high"),
    (model(gross_margin={"high": 1.4}), "between 0 and 1"),
    (model(monthly_churn={"low": -0.01}), "cannot be negative"),
])
def test_bad_models_are_refused_clearly(bad, message):
    with pytest.raises(ValueError, match=message):
        parse_model(bad)


def test_unknown_input_is_refused():
    m = copy.deepcopy(EXAMPLE)
    m["inputs"]["ltv"] = {"value": 1}
    with pytest.raises(ValueError, match="unknown input 'ltv'"):
        parse_model(m)


@pytest.mark.parametrize("horizon", [0, 2.5, "36", True])
def test_bad_horizon_is_refused(horizon):
    m = copy.deepcopy(EXAMPLE)
    m["horizon_months"] = horizon
    with pytest.raises(ValueError, match="horizon_months"):
        parse_model(m)


def test_zero_churn_without_horizon_is_refused():
    m = model(monthly_churn={"value": 0.03, "low": 0.0})
    del m["horizon_months"]
    with pytest.raises(ValueError, match="never leave"):
        parse_model(m)


def test_variable_cost_is_optional():
    inputs, _ = parse_model(model(variable_cost=None))
    assert inputs["variable_cost"]["value"] == 0.0
