import pytest

from decisionlab.product.kano import (ANSWERS, better_worse, classify, load_answers,
                                      tally, verdict)


def write(tmp_path, text):
    path = tmp_path / "kano.csv"
    path.write_text(text)
    return str(path)


def test_table_matches_published_cells():
    # Cells as read by hand from Table 3 of arxiv.org/abs/1901.05130, row = functional.
    assert classify("like", "dislike") == "O"
    assert classify("like", "neutral") == "A"
    assert classify("must-be", "dislike") == "M"
    assert classify("neutral", "neutral") == "I"
    assert classify("dislike", "like") == "R"
    assert classify("like", "like") == "Q"
    assert classify("dislike", "dislike") == "Q"


def test_every_cell_of_the_table():
    # A second copy of the table typed from the same reading, so a later edit to TABLE is caught.
    expected = {
        "like": "QAAAO", "must-be": "RIIIM", "neutral": "RIIIM",
        "live-with": "RIIIM", "dislike": "RRRRQ",
    }
    for f, row in expected.items():
        for d, code in zip(ANSWERS, row):
            assert classify(f, d) == code


def test_numbers_and_spelling_variants_accepted():
    assert classify("1", "5") == "O"
    assert classify("Must_Be", "DISLIKE") == "M"


def test_better_worse_match_hand_calculation():
    # A 6, O 3, M 2, I 4 (R and Q ignored): base 15.
    # Better = 9/15 = 0.6. Worse = -5/15 = -0.3333.
    counts = {"A": 6, "O": 3, "M": 2, "I": 4, "R": 5, "Q": 1}
    better, worse = better_worse(counts)
    assert better == pytest.approx(0.6)
    assert worse == pytest.approx(-1 / 3)


def test_better_worse_none_when_only_r_and_q():
    assert better_worse({"A": 0, "O": 0, "M": 0, "I": 0, "R": 3, "Q": 1}) is None


def test_tally_and_verdict():
    pairs = [("like", "neutral")] * 3 + [("like", "dislike")] * 2 + [("neutral", "neutral")]
    counts = tally(pairs)
    assert (counts["A"], counts["O"], counts["I"]) == (3, 2, 1)
    assert verdict(counts) == (["A"], 0.5)


def test_tie_is_reported_not_broken():
    codes, share = verdict({"A": 2, "O": 2, "M": 0, "I": 0, "R": 0, "Q": 0})
    assert codes == ["A", "O"] and share == 0.5


def test_verdict_refuses_empty():
    with pytest.raises(ValueError, match="no answers"):
        verdict(dict.fromkeys("AOMIRQ", 0))


def test_load_groups_by_feature_and_skips_comments(tmp_path):
    path = write(tmp_path, "# note\nFeature,Functional,Dysfunctional\nX,like,dislike\nY,1,3\nX,neutral,neutral\n")
    assert load_answers(path) == {"X": [("like", "dislike"), ("neutral", "neutral")], "Y": [("1", "3")]}


@pytest.mark.parametrize("body,message", [
    ("feature,functional,dysfunctional\nX,love,dislike\n", "row 2.*functional answer.*love"),
    ("feature,functional,dysfunctional\nX,like,9\n", "row 2.*dysfunctional answer"),
    ("feature,functional,dysfunctional\n,like,dislike\n", "row 2.*feature is blank"),
    ("feature,functional,dysfunctional\nX,like,\n", "row 2.*dysfunctional answer"),
    ("feature,functional\nX,like\n", "missing column: dysfunctional"),
    ("feature,functional,dysfunctional\n", "no answers found"),
])
def test_bad_input_refused(tmp_path, body, message):
    with pytest.raises(ValueError, match=message):
        load_answers(write(tmp_path, body))


def test_bad_answer_refused_by_classify():
    with pytest.raises(ValueError, match="not one of"):
        classify("maybe", "like")
