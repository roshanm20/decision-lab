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


def test_holm_worked_by_hand():
    # Worked by hand: p = 0.01, 0.04, 0.03, 0.005 with m = 4.
    # Sorted: 0.005*4 = 0.02, 0.01*3 = 0.03, 0.03*2 = 0.06, 0.04*1 = 0.04 -> max so far 0.06.
    from decisionlab.marketing.ab_test import holm_adjust
    got = holm_adjust([0.01, 0.04, 0.03, 0.005])
    assert got == pytest.approx([0.03, 0.06, 0.06, 0.02])


def test_holm_caps_at_one_and_keeps_order():
    from decisionlab.marketing.ab_test import holm_adjust
    assert holm_adjust([0.6, 0.9]) == pytest.approx([1.0, 1.0])
    assert holm_adjust([0.02]) == pytest.approx([0.02])


@pytest.mark.parametrize("bad", [[], [0.1, 1.5], [-0.1]])
def test_holm_bad_input(bad):
    from decisionlab.marketing.ab_test import holm_adjust
    with pytest.raises(ValueError):
        holm_adjust(bad)


def test_analyze_many_correction_removes_a_false_winner():
    from decisionlab.marketing.ab_test import analyze_many, multi_verdict
    # Variant 1 has raw p of about 0.0155. By hand, with 4 variants the smallest
    # p is multiplied by 4, giving about 0.062, which is over 0.05.
    res = analyze_many(5000, 500, [(5000, 575), (5000, 540), (5000, 515), (5000, 495)])
    assert res.analyses[0].significant
    assert res.adjusted_p[0] == pytest.approx(4 * res.analyses[0].p_value)
    assert not any(res.survives)
    assert "does not survive the correction" in multi_verdict(res)


def test_analyze_many_real_winner_survives():
    from decisionlab.marketing.ab_test import analyze_many
    res = analyze_many(5000, 500, [(5000, 650), (5000, 575), (5000, 515)])
    assert res.survives == [True, True, False]


def test_analyze_many_bad_input():
    from decisionlab.marketing.ab_test import analyze_many
    with pytest.raises(ValueError):
        analyze_many(5000, 500, [])
    with pytest.raises(ValueError):
        analyze_many(5000, 500, [(5000, 6000), (5000, 10)])


def test_cli_several_variants(capsys):
    import argparse
    from decisionlab.marketing import ab_test
    parser = argparse.ArgumentParser()
    ab_test.add_arguments(parser)
    args = parser.parse_args(["analyze", "--control", "5000", "500", "--variant", "5000", "575",
                              "--variant", "5000", "540", "--mde", "0.01"])
    assert ab_test.run(args) == 0
    out = capsys.readouterr().out
    assert "2 variants, each against control" in out
    assert "--mde is not used" in out
