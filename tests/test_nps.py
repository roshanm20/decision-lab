import pytest

from decisionlab.product.nps import Result, compare, interval, load_scores, tally


def write(tmp_path, text):
    path = tmp_path / "nps.csv"
    path.write_text(text)
    return str(path)


def test_tally_uses_standard_bands():
    r = tally("x", [0, 6, 7, 8, 9, 10])
    assert (r.promoters, r.passives, r.detractors) == (2, 2, 2)
    assert r.nps == 0


def test_interval_matches_hand_calculation():
    # 50 promoters, 30 passives, 20 detractors out of 100.
    # NPS 30. Variance of p - d = (0.7 - 0.3^2) / 100 = 0.0061, se = 7.8102 points.
    # 95% half width = 1.96 x 7.8102 = 15.31.
    low, high = interval(Result("x", 50, 30, 20))
    assert low == pytest.approx(14.69, abs=0.02)
    assert high == pytest.approx(45.31, abs=0.02)


def test_compare_matches_hand_calculation():
    # A: 50/30/20 of 100, variance 0.0061. B: 40/30/30 of 100, NPS 10,
    # variance (0.7 - 0.01) / 100 = 0.0069. Diff 20, se = 100 x sqrt(0.013) = 11.402,
    # z = 1.754, two-sided p = 0.0795.
    c = compare(Result("A", 50, 30, 20), Result("B", 40, 30, 30))
    assert c["diff"] == 20
    assert c["p"] == pytest.approx(0.0795, abs=0.001)
    assert c["low"] < 0 < c["high"]


def test_interval_clipped_to_scale():
    low, high = interval(Result("x", 49, 0, 1))
    assert high <= 100 and low >= -100


def test_wider_confidence_gives_wider_interval():
    r = Result("x", 50, 30, 20)
    lo90, hi90 = interval(r, 0.90)
    lo99, hi99 = interval(r, 0.99)
    assert hi99 - lo99 > hi90 - lo90


def test_bad_confidence_refused():
    with pytest.raises(ValueError, match="confidence"):
        interval(Result("x", 5, 3, 2), 1.5)


def test_load_groups_by_segment_and_skips_comments(tmp_path):
    path = write(tmp_path, "# note\nscore,segment\n9,A\n3,B\n10,A\n")
    assert load_scores(path) == {"A": [9, 10], "B": [3]}


def test_no_segment_column_goes_under_all(tmp_path):
    assert load_scores(write(tmp_path, "Score\n9\n7\n")) == {"all": [9, 7]}


@pytest.mark.parametrize("body,message", [
    ("score\n11\n", "row 2.*0 to 10"),
    ("score\n7.5\n", "row 2.*whole number"),
    ("score\nabc\n", "row 2.*not a number"),
    ("score,segment\n9,\n", "row 2.*segment is blank"),
    ("rating\n9\n", "missing column: score"),
    ("score\n", "no scores found"),
])
def test_bad_input_refused(tmp_path, body, message):
    with pytest.raises(ValueError, match=message):
        load_scores(write(tmp_path, body))


def test_all_one_group_does_not_crash():
    c = compare(Result("A", 10, 0, 0), Result("B", 0, 0, 10))
    assert c["diff"] == 200 and c["p"] == 0.0
