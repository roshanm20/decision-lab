"""Market sizing, the way a consulting team should actually do it.

Build the estimate two ways, top-down and bottom-up, as chains of
assumptions that multiply together. The tool then does the three things a
single spreadsheet cell does not:

  1. Reconciles the two approaches and says how far apart they are. Two
     methods that disagree by 3x mean at least one assumption is wrong,
     and that should be fixed before anything is presented.
  2. Runs a sensitivity check. Each assumption is moved to its low and
     high value with the others held still, and the assumptions are ranked
     by how much they swing the answer. Tighten the top one first.
  3. Optionally simulates the whole chain (triangular distributions from
     low, base and high) and reports P10, P50 and P90, so the output is a
     range with a stated spread instead of one falsely precise number.

The model is a small JSON file. Run with --example to print one. Every
number in the example is illustrative, invented to show the format.
Standard library only.
"""

from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from typing import Optional

from decisionlab.common import compact, format_table, markdown_table

TOOL = {
    "name": "market-size",
    "persona": "consulting",
    "title": "Market sizing with reconciliation and sensitivity",
    "summary": "Top-down and bottom-up sizing that checks the two agree, ranks the assumptions that matter, and gives a P10 to P90 range.",
    "doc": "docs/tools/market-size.md",
}

EXAMPLE = {
    "name": "Specialty coffee bean subscriptions, one city of 1 million adults (illustrative numbers)",
    "unit": "INR per year",
    "number_system": "indian",
    "approaches": {
        "top_down": [
            {"label": "Adults in the city", "value": 1000000, "low": 950000, "high": 1050000},
            {"label": "Drink coffee at home at least weekly", "kind": "share", "value": 0.35, "low": 0.25, "high": 0.45},
            {"label": "Of those, buy specialty beans", "kind": "share", "value": 0.10, "low": 0.05, "high": 0.15},
            {"label": "Of those, would subscribe", "kind": "share", "value": 0.20, "low": 0.10, "high": 0.30},
            {"label": "Annual spend per subscriber (INR)", "value": 9600, "low": 7200, "high": 12000},
        ],
        "bottom_up": [
            {"label": "Roasters and cafes selling beans retail", "value": 40, "low": 30, "high": 55},
            {"label": "Subscribers per roaster", "value": 180, "low": 80, "high": 300},
            {"label": "Annual spend per subscriber (INR)", "value": 9600, "low": 7200, "high": 12000},
        ],
    },
}


@dataclass
class Step:
    label: str
    value: float
    low: Optional[float] = None
    high: Optional[float] = None
    kind: str = "count"

    @property
    def has_range(self) -> bool:
        return self.low is not None and self.high is not None


def parse_model(model: dict) -> dict:
    """Validate the JSON model and return {approach_name: [Step, ...]}."""
    if not isinstance(model, dict):
        raise ValueError("the model file must be a JSON object, see --example")
    approaches = model.get("approaches")
    if not isinstance(approaches, dict) or not approaches:
        raise ValueError("the model needs an 'approaches' object with at least one chain of steps")
    parsed = {}
    for name, steps in approaches.items():
        if not isinstance(steps, list) or not steps:
            raise ValueError(f"approach {name!r} has no steps")
        chain = []
        for i, raw in enumerate(steps, start=1):
            if not isinstance(raw, dict) or "label" not in raw or "value" not in raw:
                raise ValueError(f"{name} step {i} needs to be an object with a label and a value")

            def num(key):
                v = raw.get(key)
                if v is None:
                    return None
                if isinstance(v, bool) or not isinstance(v, (int, float)) or v != v or v in (float("inf"), float("-inf")):
                    raise ValueError(f"{name} step {i}: {key} must be a plain number, got {v!r}")
                return float(v)

            value = num("value")
            if value is None:
                raise ValueError(f"{name} step {i}: value cannot be empty")
            st = Step(label=str(raw["label"]), value=value, low=num("low"), high=num("high"),
                      kind=str(raw.get("kind", "count")))
            where = f"{name} step {i} ({st.label})"
            if st.value < 0:
                raise ValueError(f"{where}: value cannot be negative")
            if (st.low is None) != (st.high is None):
                raise ValueError(f"{where}: give both low and high, or neither")
            if st.has_range and not st.low <= st.value <= st.high:
                raise ValueError(f"{where}: needs low <= value <= high, got {st.low}, {st.value}, {st.high}")
            if st.kind == "share":
                for v in (st.value, st.low, st.high):
                    if v is not None and not 0 <= v <= 1:
                        raise ValueError(f"{where}: a share must be between 0 and 1, got {v}")
            chain.append(st)
        parsed[name] = chain
    return parsed


def product(values) -> float:
    total = 1.0
    for v in values:
        total *= v
    return total


def estimate(chain: list) -> float:
    return product(s.value for s in chain)


def sensitivity(chain: list) -> list:
    """(label, result at low, result at high, swing), largest swing first."""
    base = [s.value for s in chain]
    rows = []
    for i, st in enumerate(chain):
        if not st.has_range:
            continue
        lo = product(base[:i] + [st.low] + base[i + 1:])
        hi = product(base[:i] + [st.high] + base[i + 1:])
        rows.append((st.label, lo, hi, hi - lo))
    return sorted(rows, key=lambda r: -r[3])


def simulate(chain: list, runs: int, seed: int) -> tuple:
    """P10, P50, P90 of the chain, drawing each ranged step from a triangular
    distribution. Assumes the steps are independent of each other."""
    rng = random.Random(seed)
    results = []
    for _ in range(runs):
        results.append(product(
            rng.triangular(s.low, s.high, s.value) if s.has_range else s.value for s in chain))
    results.sort()
    pick = lambda q: results[min(len(results) - 1, int(q * len(results)))]
    return pick(0.10), pick(0.50), pick(0.90)


def reconcile(estimates: dict, tolerance: float) -> tuple:
    """(ratio of largest to smallest estimate, whether that is within tolerance).
    One estimate at zero while another is not is infinite disagreement."""
    values = list(estimates.values())
    if len(values) < 2 or all(v == 0 for v in values):
        return 1.0, True
    if min(values) == 0:
        return float("inf"), False
    ratio = max(values) / min(values)
    return ratio, ratio <= 1 + tolerance


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("model", nargs="?", help="path to the JSON model")
    parser.add_argument("--example", action="store_true", help="print an example model and exit")
    parser.add_argument("--simulate", type=int, default=0, metavar="RUNS",
                        help="also simulate the chains, e.g. 10000, and report P10/P50/P90")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--tolerance", type=float, default=0.3,
                        help="how far apart approaches may be before flagging, default 0.3 (30%%)")
    parser.add_argument("--markdown", action="store_true", help="print tables as markdown")


def run(args: argparse.Namespace) -> int:
    if args.example:
        print(json.dumps(EXAMPLE, indent=2))
        return 0
    if not args.model:
        raise SystemExit("give a model file, or use --example to see the format")
    if args.simulate < 0:
        raise ValueError("--simulate must be zero or a positive number of runs")
    with open(args.model, encoding="utf-8") as fh:
        model = json.load(fh)
    chains = parse_model(model)
    system = model.get("number_system", "intl")
    unit = model.get("unit", "")
    fmt = lambda x: compact(x, system)
    table = markdown_table if args.markdown else (lambda h, r: format_table(h, r, left=(0,)))

    print(model.get("name", "Market size"))
    print(f"Unit: {unit}" if unit else "")
    estimates = {}
    for name, chain in chains.items():
        estimates[name] = estimate(chain)
        print()
        print(f"== {name.replace('_', ' ')} ==")
        running, rows = 1.0, []
        for st in chain:
            running *= st.value
            shown = f"{st.value:.0%}" if st.kind == "share" else fmt(st.value)
            rows.append([st.label, shown, fmt(running)])
        print(table(["Step", "Value", "Running total"], rows))
        print(f"Estimate: {fmt(estimates[name])}")
        sens = sensitivity(chain)
        if sens:
            print()
            print("What moves this estimate most (each assumption at its low and high, others held):")
            print(table(["Assumption", "At low", "At high", "Swing"],
                        [[l, fmt(lo), fmt(hi), fmt(sw)] for l, lo, hi, sw in sens]))
        if args.simulate:
            p10, p50, p90 = simulate(chain, args.simulate, args.seed)
            print(f"Simulated range ({args.simulate:,} runs): P10 {fmt(p10)}, P50 {fmt(p50)}, P90 {fmt(p90)}")

    ratio, ok = reconcile(estimates, args.tolerance)
    print()
    if len(estimates) > 1:
        if ok and args.simulate:
            print(f"The approaches agree within {ratio - 1:.0%}. Present the simulated range, "
                  f"not a single number.")
        elif ok:
            print(f"The approaches agree within {ratio - 1:.0%}. Run again with --simulate 10000 "
                  f"to get the range to present, rather than a single number.")
        else:
            biggest = {n: sensitivity(c)[0][0] for n, c in chains.items() if sensitivity(c)}
            fixes = "; ".join(f"{n.replace('_', ' ')}: '{lbl}'" for n, lbl in biggest.items())
            gap = "completely, one of them is zero" if ratio == float("inf") else f"by {ratio:.1f}x"
            advice = f" Start with the assumption that swings each estimate most. {fixes}." if fixes else ""
            print(f"The approaches disagree {gap}. Do not present either number yet.{advice}")
    return 0
