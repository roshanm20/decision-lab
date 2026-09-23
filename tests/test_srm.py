import math
from statistics import NormalDist

import pytest

from decisionlab.marketing.srm import Arm, chi2_sf, check, verdict

# Textbook chi-square critical values (any statistics table, e.g. a standard
# chi-square distribution table): the x where P(chi2 > x) equals the given
# p, for a given degrees of freedom. Independent of this module's own gamma
# function code, since these numbers come from published tables, not from
# running our chi2_sf and reading back its answer.
CRITICAL_VALUES = [
    (3.841, 1, 0.05),
    (6.635, 1, 0.01),
    (10.828, 1, 0.001),
    (5.991, 2, 0.05),
    (9.210, 2, 0.01),
    (7.815, 3, 0.05),
    (11.345, 3, 0.01),
    (9.488, 4, 0.05),
]


@pytest.mark.parametrize("x,df,expected_p", CRITICAL_VALUES)
def test_chi2_sf_matches_textbook_critical_values(x, df, expected_p):
    assert chi2_sf(x, df) == pytest.approx(expected_p, abs=2e-4)


def test_chi2_sf_at_zero_is_one():
    assert chi2_sf(0, 1) == 1.0
    assert chi2_sf(-5, 3) == 1.0


def test_two_arm_p_value_matches_independent_normal_formula():
    # 10,000 visitors, 50/50 expected, 4,820 / 5,180 observed. Chi-square by
    # hand: expected 5,000 each, (180^2/5000)*2 = 12.96.
    r = check([Arm("control", 1, 4820), Arm("variant", 1, 5180)])
    assert r.chi2 == pytest.approx(12.96, abs=1e-9)
    # A 2-category chi-square test is exactly a two-sided z-test on the
    # proportion, z = (O - E) / sqrt(N p (1-p)). Written out separately here,
    # not called from the module, as the independent check.
    n, p0 = 10000, 0.5
    z = (4820 - 5000) / math.sqrt(n * p0 * (1 - p0))
    p_ref = 2 * (1 - NormalDist().cdf(abs(z)))
    assert r.p_value == pytest.approx(p_ref, abs=1e-9)


def test_flags_mismatch_below_alpha():
    r = check([Arm("control", 1, 4820), Arm("variant", 1, 5180)])
    assert r.mismatched
    assert "Sample ratio mismatch" in verdict(r)


def test_balanced_split_is_not_flagged():
    r = check([Arm("control", 1, 4980), Arm("variant", 1, 5020)])
    assert not r.mismatched
    assert "No sample ratio mismatch" in verdict(r)


def test_unequal_weights_respected():
    # 2:1 holdout design, observed split matches 2:1 almost exactly.
    r = check([Arm("treatment", 2, 6667), Arm("holdout", 1, 3333)])
    assert r.expected[0] == pytest.approx(6666.67, abs=0.5)
    assert not r.mismatched


def test_three_arms_uses_two_degrees_of_freedom():
    r = check([Arm("a", 1, 3300), Arm("b", 1, 3300), Arm("c", 1, 3400)])
    assert r.df == 2


def test_stricter_alpha_can_flip_the_verdict():
    # Microsoft Research's recommended 0.0005 threshold is stricter than the
    # 0.01 default, so a mismatch flagged at 0.01 can pass at 0.0005.
    lenient = check([Arm("control", 1, 4850), Arm("variant", 1, 5150)], alpha=0.01)
    strict = check([Arm("control", 1, 4850), Arm("variant", 1, 5150)], alpha=0.0005)
    assert lenient.mismatched
    assert not strict.mismatched


def test_flags_few_expected():
    r = check([Arm("control", 1, 3), Arm("variant", 1, 3)])
    assert r.few_expected


def test_needs_at_least_two_arms():
    with pytest.raises(ValueError):
        check([Arm("control", 1, 100)])


def test_rejects_zero_weight():
    with pytest.raises(ValueError):
        check([Arm("control", 0, 100), Arm("variant", 1, 100)])


def test_rejects_negative_observed():
    with pytest.raises(ValueError):
        check([Arm("control", 1, -5), Arm("variant", 1, 100)])


def test_rejects_duplicate_names():
    with pytest.raises(ValueError):
        check([Arm("control", 1, 100), Arm("control", 1, 100)])


def test_rejects_all_zero_observed():
    with pytest.raises(ValueError):
        check([Arm("control", 1, 0), Arm("variant", 1, 0)])


def test_rejects_bad_alpha():
    with pytest.raises(ValueError):
        check([Arm("control", 1, 100), Arm("variant", 1, 100)], alpha=1.5)


def test_cli_needs_two_arms():
    from decisionlab.cli import main
    assert main(["srm", "--arm", "control", "1", "100"]) == 2


def test_cli_rejects_non_numeric_count():
    from decisionlab.cli import main
    assert main(["srm", "--arm", "control", "1", "abc", "--arm", "variant", "1", "100"]) == 2


def test_cli_runs_clean_split(capsys):
    from decisionlab.cli import main
    assert main(["srm", "--arm", "control", "1", "4980", "--arm", "variant", "1", "5020"]) == 0
    out = capsys.readouterr().out
    assert "No sample ratio mismatch" in out
