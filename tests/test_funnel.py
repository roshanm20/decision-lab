import argparse

import pytest

from decisionlab.bi.funnel import Step, analyse, biggest_leak, load, load_counts, load_events, run, wilson


def write(tmp_path, text, name="f.csv"):
    path = tmp_path / name
    path.write_text(text)
    return str(path)


def test_wilson_matches_hand_calculation():
    # 50 of 100 at 95%: centre 0.5, half width 1.959964 x sqrt(0.0025 + 0.00009604) / 1.038416 = 0.09617.
    low, high = wilson(50, 100)
    assert low == pytest.approx(0.40383, abs=1e-4)
    assert high == pytest.approx(0.59617, abs=1e-4)


def test_wilson_zero_successes_has_closed_form_upper_bound():
    # With no successes the upper bound is z^2 / (n + z^2) = 3.841459 / 13.841459.
    low, high = wilson(0, 10)
    assert low == pytest.approx(0.0, abs=1e-12)
    assert high == pytest.approx(0.27753, abs=1e-4)


def test_wilson_rejects_bad_input():
    with pytest.raises(ValueError, match="positive"):
        wilson(0, 0)
    with pytest.raises(ValueError, match="between 0 and n"):
        wilson(11, 10)
    with pytest.raises(ValueError, match="confidence"):
        wilson(5, 10, 1.5)


def test_step_rates_and_loss():
    rows = analyse([Step("a", 1000), Step("b", 400), Step("c", 100)])
    assert rows[0]["rate"] == pytest.approx(0.4)
    assert rows[0]["lost"] == 600
    assert rows[1]["rate"] == pytest.approx(0.25)
    assert rows[1]["from_top"] == pytest.approx(0.1)


def test_rising_count_is_refused():
    with pytest.raises(ValueError, match="cannot reach a step"):
        analyse([Step("a", 100), Step("b", 120)])


def test_one_step_is_refused():
    with pytest.raises(ValueError, match="at least two"):
        analyse([Step("a", 100)])


def test_zero_users_step_gives_no_rate():
    rows = analyse([Step("a", 100), Step("b", 0), Step("c", 0)])
    assert rows[1]["rate"] is None
    assert biggest_leak(rows)["worst"]["step"] == "b"


def test_biggest_leak_is_lowest_rate_and_overlap_is_checked():
    far = biggest_leak(analyse([Step("a", 10000), Step("b", 8000), Step("c", 2000)]))
    assert far["worst"]["step"] == "c"
    assert far["separable"] is True
    close = biggest_leak(analyse([Step("a", 50), Step("b", 25), Step("c", 12)]))
    assert close["separable"] is False


def test_counts_file_skips_blank_step_and_reports_it(tmp_path):
    path = write(tmp_path, "# note\nstep,users\na,1000\nb,\nc,500\n")
    steps, problems = load_counts(path)
    assert [s.name for s in steps] == ["a", "c"]
    assert "row 3" in problems[0] and "'b'" in problems[0]


@pytest.mark.parametrize("text, message", [
    ("step,users\na,10\nb,x\n", "row 3.*not a number"),
    ("step,users\na,10\nb,2.5\n", "row 3.*whole number"),
    ("step,users\na,10\nb,-1\n", "row 3.*whole number"),
    ("step,users\na,10\na,5\n", "row 3.*twice"),
    ("step,users\n,10\n", "row 2.*blank"),
    ("step,users\n", "no steps"),
])
def test_counts_file_bad_rows_have_line_numbers(tmp_path, text, message):
    with pytest.raises(ValueError, match=message):
        load_counts(write(tmp_path, text))


def test_events_counted_by_hand(tmp_path):
    # u1: a b c. u2: a b. u3: a. u4: a c (skips b). u5: a b a (duplicate). x row is not a step.
    path = write(tmp_path, "user_id,event\nu1,a\nu1,b\nu1,c\nu2,a\nu2,b\nu3,a\nu4,a\nu4,c\nu5,a\nu5,b\nu5,a\nu1,x\n")
    steps, problems = load_events(path, ["a", "b", "c"])
    assert [s.users for s in steps] == [5, 3, 1]
    assert any("1 users did a later step" in p for p in problems)
    assert any("1 event rows are not in --steps" in p for p in problems)


def test_event_log_needs_steps_and_valid_columns(tmp_path):
    path = write(tmp_path, "user_id,event\nu1,a\n")
    with pytest.raises(ValueError, match="--steps"):
        load(path)
    with pytest.raises(ValueError, match="twice"):
        load(path, ["a", "a"])
    with pytest.raises(ValueError, match="no events"):
        load(path, ["p", "q"])
    with pytest.raises(ValueError, match="needs columns"):
        load(write(tmp_path, "foo,bar\n1,2\n", "g.csv"))


def test_run_prints_leak(tmp_path, capsys):
    path = write(tmp_path, "step,users\na,1000\nb,300\nc,200\n")
    args = argparse.Namespace(csv_path=path, steps=None, confidence=0.95, markdown=False)
    assert run(args) == 0
    out = capsys.readouterr().out
    assert "Biggest leak: a to b" in out
    assert "30.0%" in out


def test_run_rejects_bad_confidence(tmp_path):
    path = write(tmp_path, "step,users\na,10\nb,5\n")
    with pytest.raises(ValueError, match="confidence"):
        run(argparse.Namespace(csv_path=path, steps=None, confidence=2, markdown=False))


def test_small_and_empty_steps_warn_and_markdown_prints(tmp_path, capsys):
    path = write(tmp_path, "step,users\na,20\nb,10\nc,0\nd,0\n")
    run(argparse.Namespace(csv_path=path, steps=None, confidence=0.95, markdown=True))
    out = capsys.readouterr().out
    assert "only 20 users entered" in out
    assert "nobody entered this step" in out
    assert "| Step |" in out
