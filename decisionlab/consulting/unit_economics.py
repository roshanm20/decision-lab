"""Unit economics that does not hide the assumption doing the work.

Three mistakes show up in most CAC and LTV slides, and this tool stops each.

  1. Payback is worked out as CAC divided by monthly contribution. That
     ignores churn. Customers leave while you are still earning the money
     back, so the real payback is longer, and sometimes it never comes.
     Here payback is worked out on the customers who are still there.
  2. LTV is monthly contribution divided by churn. At 1% churn that is
     100 months, a lifetime nobody has data for. Set a horizon and LTV is
     counted only up to it. Without one, the tool warns when the implied
     lifetime is over 60 months.
  3. One number, no range. Each input can carry a low and a high. The tool
     moves each one alone and ranks them by how much they swing LTV / CAC,
     then moves them all against you at once, because one-at-a-time
     testing misses bad things arriving together.

Everything is per customer, per month. Churn is a constant monthly rate,
so a customer stays for a geometric number of months. The model is a small
JSON file. Run with --example to print one. Every number in the example is
illustrative, invented to show the format. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import math
from typing import Optional

from decisionlab.common import compact, format_table, markdown_table

TOOL = {
    "name": "unit-economics",
    "persona": "consulting",
    "title": "Unit economics with churn-adjusted payback and sensitivity",
    "summary": "CAC, contribution, LTV and payback per customer, with payback that allows for churn and a ranking of which input moves LTV / CAC most.",
    "doc": "docs/tools/unit-economics.md",
}

EXAMPLE = {
    "name": "Billing software for small restaurants, one customer (illustrative numbers)",
    "unit": "INR",
    "number_system": "indian",
    "horizon_months": 36,
    "inputs": {
        "arpu": {"label": "Revenue per customer per month", "value": 1500, "low": 1200, "high": 1800},
        "gross_margin": {"label": "Gross margin", "value": 0.75, "low": 0.65, "high": 0.82},
        "variable_cost": {"label": "Support and payment cost per customer per month", "value": 150, "low": 100, "high": 250},
        "monthly_churn": {"label": "Monthly churn", "value": 0.04, "low": 0.02, "high": 0.07},
        "cac": {"label": "Cost to acquire one customer", "value": 12000, "low": 8000, "high": 20000},
    },
}

# key: (default label, is a share, required, higher is better for the business)
FIELDS = {
    "arpu": ("Revenue per customer per month", False, True, True),
    "gross_margin": ("Gross margin", True, True, True),
    "variable_cost": ("Other variable cost per customer per month", False, False, False),
    "monthly_churn": ("Monthly churn", True, True, False),
    "cac": ("Cost to acquire one customer", False, True, False),
}
LONG_LIFETIME_MONTHS = 60


def _number(raw, where: str) -> float:
    if isinstance(raw, bool) or not isinstance(raw, (int, float)) or raw != raw or raw in (float("inf"), float("-inf")):
        raise ValueError(f"{where} must be a plain number, got {raw!r}")
    return float(raw)


def parse_model(model: dict) -> tuple:
    """Validate the JSON model. Returns (inputs, horizon) where inputs is
    {key: {"label", "value", "low", "high"}} and horizon is months or None."""
    if not isinstance(model, dict):
        raise ValueError("the model file must be a JSON object, see --example")
    raw_inputs = model.get("inputs")
    if not isinstance(raw_inputs, dict):
        raise ValueError("the model needs an 'inputs' object, see --example")
    unknown = sorted(set(raw_inputs) - set(FIELDS))
    if unknown:
        raise ValueError(f"unknown input {unknown[0]!r}, the inputs are: {', '.join(FIELDS)}")
    horizon = model.get("horizon_months")
    if horizon is not None:
        horizon = _number(horizon, "horizon_months")
        if horizon < 1 or horizon != int(horizon):
            raise ValueError(f"horizon_months must be a whole number of months, 1 or more, got {horizon:g}")
        horizon = int(horizon)
    inputs = {}
    for key, (default_label, is_share, required, _) in FIELDS.items():
        if key not in raw_inputs:
            if required:
                raise ValueError(f"missing input {key!r}, it is needed")
            inputs[key] = {"label": default_label, "value": 0.0, "low": 0.0, "high": 0.0}
            continue
        raw = raw_inputs[key]
        if not isinstance(raw, dict) or "value" not in raw:
            raise ValueError(f"input {key!r} needs to be an object with a value")
        value = _number(raw["value"], f"{key}: value")
        low = value if raw.get("low") is None else _number(raw["low"], f"{key}: low")
        high = value if raw.get("high") is None else _number(raw["high"], f"{key}: high")
        if (raw.get("low") is None) != (raw.get("high") is None):
            raise ValueError(f"{key}: give both low and high, or neither")
        if not low <= value <= high:
            raise ValueError(f"{key}: needs low <= value <= high, got {low:g}, {value:g}, {high:g}")
        if low < 0:
            raise ValueError(f"{key}: cannot be negative, got {low:g}")
        if is_share and high > 1:
            raise ValueError(f"{key}: a share must be between 0 and 1, got {high:g}")
        if key in ("arpu", "cac") and low <= 0:
            raise ValueError(f"{key}: must be above zero, got {low:g}")
        inputs[key] = {"label": str(raw.get("label", default_label)), "value": value, "low": low, "high": high}
    if horizon is None and inputs["monthly_churn"]["low"] == 0:
        raise ValueError("monthly_churn of zero means customers never leave and LTV has no end, "
                         "set horizon_months or use a churn above zero")
    return inputs, horizon


def contribution(arpu: float, gross_margin: float, variable_cost: float) -> float:
    """Money left per customer per month after cost of goods and other variable cost."""
    return arpu * gross_margin - variable_cost


def expected_months(churn: float, horizon: Optional[int]) -> float:
    """Expected number of paying months for a new customer. Each month the
    customer stays with probability 1 - churn, so month t (from 0) is paid
    with probability (1 - churn)^t. Without a horizon this is 1 / churn."""
    if churn == 0:
        return float(horizon)
    if horizon is None:
        return 1.0 / churn
    return (1.0 - (1.0 - churn) ** horizon) / churn


def ltv(cm: float, churn: float, horizon: Optional[int]) -> float:
    return cm * expected_months(churn, horizon)


def naive_payback(cm: float, cac: float) -> float:
    """CAC over monthly contribution. Ignores churn. Shown only to compare."""
    return cac / cm if cm > 0 else math.inf


def payback(cm: float, churn: float, cac: float, horizon: Optional[int]) -> float:
    """Months until the expected cumulative contribution of a new customer
    covers CAC, or infinity if it never does (within the horizon, if set).
    Solves cm * (1 - (1 - churn)^n) / churn = cac for n."""
    if cm <= 0:
        return math.inf
    if churn == 0:
        n = cac / cm
    elif churn >= 1:
        n = cac / cm if cac <= cm else math.inf
    else:
        x = 1.0 - cac * churn / cm
        if x <= 0:
            return math.inf
        n = math.log(x) / math.log(1.0 - churn)
    if horizon is not None and n > horizon + 1e-9:
        return math.inf
    return n


def metrics(v: dict, horizon: Optional[int]) -> dict:
    """All results for one set of values {key: number}."""
    cm = contribution(v["arpu"], v["gross_margin"], v["variable_cost"])
    life = expected_months(v["monthly_churn"], horizon)
    value = cm * life
    return {
        "cm": cm, "life": life, "ltv": value, "cac": v["cac"], "ratio": value / v["cac"],
        "payback": payback(cm, v["monthly_churn"], v["cac"], horizon),
        "naive": naive_payback(cm, v["cac"]),
    }


def _values(inputs: dict, which: str) -> dict:
    return {k: d[which] for k, d in inputs.items()}


def sensitivity(inputs: dict, horizon: Optional[int]) -> list:
    """(label, result at low, result at high, swing), largest swing first,
    for each input that has a range. Results are metrics() dicts."""
    base = _values(inputs, "value")
    rows = []
    for key, d in inputs.items():
        if d["low"] == d["high"]:
            continue
        lo = metrics({**base, key: d["low"]}, horizon)
        hi = metrics({**base, key: d["high"]}, horizon)
        rows.append((d["label"], lo, hi, abs(hi["ratio"] - lo["ratio"])))
    return sorted(rows, key=lambda r: -r[3])


def combined_cases(inputs: dict, horizon: Optional[int]) -> tuple:
    """(everything goes wrong, everything goes right): every ranged input
    at its unfavourable, then its favourable, end at the same time."""
    bad, good = {}, {}
    for key, d in inputs.items():
        higher_is_better = FIELDS[key][3]
        bad[key] = d["low"] if higher_is_better else d["high"]
        good[key] = d["high"] if higher_is_better else d["low"]
    return metrics(bad, horizon), metrics(good, horizon)


def _months(x: float) -> str:
    return "never" if math.isinf(x) else f"{x:.1f} months"


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("model", nargs="?", help="path to the JSON model")
    parser.add_argument("--example", action="store_true", help="print an example model and exit")
    parser.add_argument("--markdown", action="store_true", help="print tables as markdown")


def run(args: argparse.Namespace) -> int:
    if args.example:
        print(json.dumps(EXAMPLE, indent=2))
        return 0
    if not args.model:
        raise SystemExit("give a model file, or use --example to see the format")
    with open(args.model, encoding="utf-8") as fh:
        model = json.load(fh)
    inputs, horizon = parse_model(model)
    system = model.get("number_system", "intl")
    fmt = lambda x: compact(x, system)
    table = markdown_table if args.markdown else (lambda h, r: format_table(h, r, left=(0,)))

    def show(key, x):
        return f"{x:.0%}" if FIELDS[key][1] else fmt(x)

    print(model.get("name", "Unit economics"))
    if model.get("unit"):
        print(f"Unit: {model['unit']}, per customer")
    print(f"Horizon: {horizon} months" if horizon else "Horizon: none, customers are counted for their whole lifetime")
    print()
    print(table(["Input", "Low", "Base", "High"],
                [[d["label"], show(k, d["low"]), show(k, d["value"]), show(k, d["high"])]
                 for k, d in inputs.items()]))

    base = metrics(_values(inputs, "value"), horizon)
    print()
    print(f"Contribution per customer per month: {fmt(base['cm'])}")
    print(f"Expected paying months: {base['life']:.1f}")
    print(f"LTV (lifetime contribution): {fmt(base['ltv'])}")
    print(f"CAC: {fmt(base['cac'])}")
    print(f"LTV / CAC: {base['ratio']:.2f}x")
    print(f"Payback allowing for churn: {_months(base['payback'])}")
    print(f"Payback by CAC / contribution, ignoring churn: {_months(base['naive'])}")

    sens = sensitivity(inputs, horizon)
    if sens:
        print()
        print("What moves LTV / CAC most (each input at its low and high, others held):")
        print(table(["Input", "Ratio at low", "Ratio at high", "Swing"],
                    [[l, f"{lo['ratio']:.2f}x", f"{hi['ratio']:.2f}x", f"{sw:.2f}x"] for l, lo, hi, sw in sens]))
        bad, good = combined_cases(inputs, horizon)
        print()
        print("All inputs at once:")
        print(table(["Case", "LTV / CAC", "Payback"],
                    [["Everything goes wrong", f"{bad['ratio']:.2f}x", _months(bad["payback"])],
                     ["Base", f"{base['ratio']:.2f}x", _months(base["payback"])],
                     ["Everything goes right", f"{good['ratio']:.2f}x", _months(good["payback"])]]))

    print()
    if base["cm"] <= 0:
        print("Each customer loses money every month before acquisition cost. Fix the margin before looking at CAC.")
    elif base["ratio"] < 1:
        print("A customer returns less than it cost to win. At these inputs, growing faster loses more money.")
    if base["cm"] > 0 and math.isinf(base["payback"]) and base["ratio"] >= 1 and horizon:
        print(f"CAC is only recovered after the {horizon} month horizon.")
    if base["cm"] > 0 and not math.isinf(base["payback"]) and base["payback"] > base["naive"] * 1.2:
        print(f"Churn stretches payback from {base['naive']:.1f} to {base['payback']:.1f} months. "
              f"The simple CAC / contribution figure is too kind.")
    if horizon is None and base["life"] > LONG_LIFETIME_MONTHS:
        print(f"The implied lifetime is {base['life']:.0f} months. Set horizon_months to count only the "
              f"period you have evidence for.")
    if sens:
        print(f"Verify first: '{sens[0][0]}'.")
    return 0
