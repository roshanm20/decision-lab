import json

import pytest

from decisionlab.consulting.market_sizing import (
    EXAMPLE, estimate, parse_model, reconcile, sensitivity, simulate,
)


def test_example_estimates():
    chains = parse_model(EXAMPLE)
    assert estimate(chains["top_down"]) == pytest.approx(67_200_000)
    assert estimate(chains["bottom_up"]) == pytest.approx(69_120_000)


def test_example_file_matches_embedded_example():
    with open("examples/market_size_coffee.json", encoding="utf-8") as fh:
        assert json.load(fh) == EXAMPLE


def test_sensitivity_ranks_widest_swing_first():
    rows = sensitivity(parse_model(EXAMPLE)["bottom_up"])
    assert rows[0][0] == "Subscribers per roaster"
    assert [r[3] for r in rows] == sorted((r[3] for r in rows), reverse=True)


def test_simulation_is_reproducible_and_ordered():
    chain = parse_model(EXAMPLE)["top_down"]
    first = simulate(chain, 2000, seed=1)
    assert first == simulate(chain, 2000, seed=1)
    p10, p50, p90 = first
    assert p10 < p50 < p90


def test_reconcile():
    assert reconcile({"a": 100, "b": 110}, 0.3) == (pytest.approx(1.1), True)
    ratio, ok = reconcile({"a": 100, "b": 300}, 0.3)
    assert ratio == pytest.approx(3.0) and not ok


@pytest.mark.parametrize("bad_step", [
    {"label": "x", "value": 5, "low": 6, "high": 9},
    {"label": "x", "value": 1.5, "kind": "share"},
    {"label": "x", "value": 5, "low": 1},
    {"label": "x", "value": -1},
    {"value": 5},
])
def test_bad_models_raise(bad_step):
    with pytest.raises(ValueError):
        parse_model({"approaches": {"a": [bad_step]}})


def test_reconcile_treats_a_zero_estimate_as_disagreement():
    ratio, ok = reconcile({"a": 0, "b": 5e9}, 0.3)
    assert ratio == float("inf") and not ok


@pytest.mark.parametrize("model", [
    [],
    {"approaches": {"a": ["not a step"]}},
    {"approaches": {"a": [{"label": "x", "value": None}]}},
    {"approaches": {"a": [{"label": "x", "value": True}]}},
    {"approaches": {"a": [{"label": "x", "value": "12"}]}},
])
def test_malformed_models_raise_clear_errors(model):
    with pytest.raises(ValueError):
        parse_model(model)


def test_cli_rejects_negative_simulation_runs():
    from decisionlab.cli import main
    assert main(["market-size", "examples/market_size_coffee.json", "--simulate", "-5"]) == 2


def test_zero_disagreement_without_ranges_prints_a_clean_sentence(tmp_path, capsys):
    import json as _json
    from decisionlab.cli import main
    model = {"approaches": {"a": [{"label": "x", "value": 0}], "b": [{"label": "y", "value": 5e9}]}}
    path = tmp_path / "m.json"
    path.write_text(_json.dumps(model))
    assert main(["market-size", str(path)]) == 0
    last = capsys.readouterr().out.strip().splitlines()[-1]
    assert last == "The approaches disagree completely, one of them is zero. Do not present either number yet."
