import math

import pytest

from decisionlab.marketing.ab_test import analyze, sample_size_per_arm, verdict


def reference_n(p1, p2, alpha=0.05, power=0.8):
    """The same formula written out independently, as a cross-check."""
    from statistics import NormalDist
    z = NormalDist().inv_cdf
    pbar = (p1 + p2) / 2
    a = z(1 - alpha / 2) * math.sqrt(2 * pbar * (1 - pbar))
    b = z(power) * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))
    return math.ceil(((a + b) / (p2 - p1)) ** 2)


def test_sample_size_known_case():
    # 10% to 12%, alpha 0.05 two-sided, power 0.8. Worked by hand: 3840.8, rounds up.
    assert sample_size_per_arm(0.10, 0.02) == 3841


@pytest.mark.parametrize("p1,p2", [(0.05, 0.055), (0.2, 0.25), (0.5, 0.45), (0.01, 0.012)])
def test_sample_size_matches_reference(p1, p2):
    assert sample_size_per_arm(p1, p2 - p1) == reference_n(p1, p2)


def test_relative_and_absolute_agree():
    assert sample_size_per_arm(0.10, 0.2, relative=True) == sample_size_per_arm(0.10, 0.02)


def test_smaller_effect_needs_more_traffic():
    assert sample_size_per_arm(0.10, 0.01) > sample_size_per_arm(0.10, 0.02)


@pytest.mark.parametrize("kwargs", [
    dict(baseline=0, mde=0.01), dict(baseline=1.2, mde=0.01),
    dict(baseline=0.1, mde=0), dict(baseline=0.95, mde=0.1),
])
def test_bad_inputs_raise(kwargs):
    with pytest.raises(ValueError):
        sample_size_per_arm(**kwargs)


def test_analyze_flat_underpowered():
    res = analyze(1000, 100, 1000, 108)
    assert not res.significant
    assert res.p_value == pytest.approx(0.5579, abs=1e-3)
    assert res.ci_low == pytest.approx(-0.01876, abs=1e-4)
    assert res.ci_high == pytest.approx(0.03476, abs=1e-4)
    assert res.detectable_abs == pytest.approx(0.0376, abs=1e-3)
    # Caring about a one point change: this test could never have seen it.
    assert "too small to settle it" in verdict(res, mde=0.01)


def test_analyze_clear_win():
    res = analyze(20000, 2000, 20000, 2240)
    assert res.significant
    assert res.p_value < 0.001
    assert "p < 0.001" in verdict(res)
    assert res.ci_low > 0


def test_analyze_large_flat_test_rules_out_the_effect_you_care_about():
    res = analyze(200000, 20000, 200000, 20050)
    assert not res.significant
    assert res.detectable_abs < 0.01
    assert "change that big is unlikely" in verdict(res, mde=0.01)


def test_flat_result_without_mde_describes_instead_of_judging():
    text = verdict(analyze(1000, 100, 1000, 108))
    assert "not ruled out" in text and "--mde" in text


def test_analyze_flags_few_conversions():
    assert analyze(100, 3, 100, 5).few_conversions


def test_analyze_rejects_impossible_counts():
    with pytest.raises(ValueError):
        analyze(100, 101, 100, 5)


def test_zero_control_rate_uses_pooled_rate_not_nan():
    res = analyze(1000, 0, 1000, 12)
    assert not math.isnan(res.detectable_abs)
    assert math.isnan(res.relative_lift)  # a lift on a zero base has no meaning


def test_no_variation_at_all_cannot_be_judged():
    res = analyze(100, 0, 100, 0)
    text = verdict(res, mde=0.01)
    assert "Cannot judge" in text and "big enough" not in text


def test_cli_rejects_negative_daily_visitors():
    from decisionlab.cli import main
    assert main(["ab-test", "size", "--baseline", "0.1", "--mde", "0.02", "--daily-visitors", "-5"]) == 2


def test_bad_daily_visitors_prints_nothing_before_the_error(capsys):
    from decisionlab.cli import main
    assert main(["ab-test", "size", "--baseline", "0.1", "--mde", "0.02", "--daily-visitors", "0"]) == 2
    assert capsys.readouterr().out == ""
