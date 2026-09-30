import pytest

from decisionlab.cli import main
from decisionlab.marketing.srm import check_daily, load_daily

# A clean series: 14 days, two arms, gaps of at most 30 visitors on about 2,000 a day.
CLEAN = {
    f"2026-04-{d:02d}": {"control": 1000 + off, "variant": 1000 - off}
    for d, off in zip(range(1, 15), [5, -12, 8, -3, 15, -9, 2, 11, -14, 6, -7, 13, -4, 9])
}


def test_cumulative_chi_square_matches_hand_calculation():
    # Day 1: 520 v 480. Expected 500 each. chi2 = 2 * 20^2 / 500 = 1.6.
    # Day 2 adds 490 v 510. Running total 1,010 v 990, expected 1,000,
    # chi2 = 2 * 10^2 / 1000 = 0.2. That day alone: 2 * 10^2 / 500 = 0.4.
    counts = {"d1": {"a": 520, "b": 480}, "d2": {"a": 490, "b": 510}}
    rep = check_daily(counts, ["a", "b"])
    assert rep.days[0].cumulative.chi2 == pytest.approx(1.6, abs=1e-9)
    assert rep.days[1].cumulative.chi2 == pytest.approx(0.2, abs=1e-9)
    assert rep.days[1].day_only.chi2 == pytest.approx(0.4, abs=1e-9)


def test_clean_series_raises_no_alarm():
    rep = check_daily(CLEAN, ["control", "variant"])
    assert rep.first_cumulative_day is None
    assert rep.first_day_only_day is None


def test_names_first_day_the_running_total_breaks():
    counts = dict(CLEAN)
    for d in range(8, 15):
        counts[f"2026-04-{d:02d}"] = {"control": 900, "variant": 1100}
    rep = check_daily(counts, ["control", "variant"])
    day = rep.first_cumulative_day
    assert day is not None and day >= "2026-04-08"
    # The day before the flagged day must be clean on the running total.
    earlier = [d for d in rep.days if d.day < day]
    assert all(not d.cumulative.mismatched for d in earlier)


def test_one_bad_day_hidden_in_the_total_is_still_caught():
    counts = {f"2026-05-{d:02d}": {"a": 5000, "b": 5000} for d in range(1, 10)}
    counts["2026-05-10"] = {"a": 4700, "b": 5300}
    rep = check_daily(counts, ["a", "b"])
    assert rep.first_cumulative_day is None
    assert rep.first_day_only_day == "2026-05-10"


def test_unequal_weights_are_used():
    counts = {"d1": {"t": 6700, "h": 3300}, "d2": {"t": 6600, "h": 3400}}
    rep = check_daily(counts, ["t", "h"], {"t": 2, "h": 1})
    assert rep.first_cumulative_day is None


def test_tiny_first_day_is_not_flagged():
    rep = check_daily({"d1": {"a": 0, "b": 4}, "d2": {"a": 500, "b": 500}}, ["a", "b"])
    assert rep.first_day_only_day is None


def test_missing_arm_on_a_day_is_reported():
    rep = check_daily({"d1": {"a": 100, "b": 100}, "d2": {"a": 100}}, ["a", "b"])
    assert any("d2" in p and "'b'" in p for p in rep.problems)


def test_messy_file_reports_line_numbers(tmp_path):
    f = tmp_path / "m.csv"
    f.write_text("# comment\nday,arm,count\n2026-01-01,a,100\n2026-01-01,b,abc\n,b,5\n"
                 "2026-01-01,b,-3\n2026-01-01,b,1,000\n2026-01-01,b,\"1,000\"\n")
    counts, arms, problems = load_daily(str(f))
    assert counts == {"2026-01-01": {"a": 100, "b": 1000}}
    assert any(p.startswith("line 4") for p in problems)
    assert any(p.startswith("line 5") for p in problems)
    assert any(p.startswith("line 6") for p in problems)
    assert any(p.startswith("line 7") for p in problems)


def test_missing_header_refused(tmp_path):
    f = tmp_path / "h.csv"
    f.write_text("date,arm,n\n2026-01-01,a,1\n")
    with pytest.raises(ValueError, match="missing column"):
        load_daily(str(f))


def test_single_arm_refused():
    with pytest.raises(ValueError, match="two arms"):
        check_daily({"d1": {"a": 10}}, ["a"])


def test_weight_for_unknown_arm_refused():
    with pytest.raises(ValueError, match="not in the file"):
        check_daily({"d1": {"a": 10, "b": 10}}, ["a", "b"], {"z": 2})


def test_cli_daily_runs_on_example(capsys):
    assert main(["srm", "--daily", "examples/srm_daily.csv"]) == 0
    assert "2026-03-09" in capsys.readouterr().out


def test_cli_daily_and_arm_together_refused(capsys):
    assert main(["srm", "--daily", "examples/srm_daily.csv", "--arm", "a", "1", "5", "--arm", "b", "1", "5"]) == 2


def test_cli_weight_without_daily_refused():
    assert main(["srm", "--weight", "a", "2", "--arm", "a", "1", "5", "--arm", "b", "1", "5"]) == 2


def test_cli_no_input_refused():
    assert main(["srm"]) == 2
