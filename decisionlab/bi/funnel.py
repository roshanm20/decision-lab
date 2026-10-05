"""Funnel step conversion with confidence intervals, and the step that leaks most.

The mistake it fixes: a funnel chart shows 100%, 62%, 31%, 9% and everyone
points at the last bar because it is the smallest. But the percentages are
from the top of the funnel, so they hide how each step does against the one
before it. And every step rate is measured on a sample, so a step that looks
worst may not be distinguishable from the next worst. This tool shows each
step against the step before it, puts an interval on that rate, names the
step with the lowest rate, and says whether the sample of users can really
tell it apart from the second lowest.

Two input shapes, picked from the header row:
    step counts   columns: step, users. One row per step, in funnel order.
    event log     columns: user_id, event. Pass the funnel order with --steps.
Lines starting with # are skipped, so a file can label itself.

Missing steps. In a step-count file, a step with a blank count is skipped and
reported, and the next step is measured against the last step that has a
count. A count that rises from one step to the next is refused, since a user
cannot reach a step without the one before it. In an event log, a user counts
at step k only if they have every step up to k. Users who did a later step
but skipped an earlier one (often broken tracking) are counted and reported,
not hidden.

Method. Step conversion is users at the step over users at the previous step.
The interval is the Wilson score interval, which behaves at small counts and
at rates near 0 or 100 where the plain normal interval does not. Standard
library only.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from statistics import NormalDist

from decisionlab.common import format_table, markdown_table

TOOL = {
    "name": "funnel",
    "persona": "bi",
    "title": "Funnel step conversion and biggest leak",
    "summary": "Step-by-step conversion with confidence intervals from step counts or an event log, naming the step that leaks most.",
    "doc": "docs/tools/funnel.md",
}

_N = NormalDist()
SMALL_SAMPLE = 30   # below this many users entering a step, the interval is wide and the tool warns


@dataclass
class Step:
    name: str
    users: int


def wilson(successes: int, n: int, confidence: float = 0.95) -> tuple:
    """Wilson score interval for a proportion, as fractions."""
    _check_confidence(confidence)
    if n <= 0:
        raise ValueError("n must be positive")
    if not 0 <= successes <= n:
        raise ValueError(f"successes ({successes}) must be between 0 and n ({n})")
    z = _N.inv_cdf(1 - (1 - confidence) / 2)
    p = successes / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * (p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5 / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def _check_confidence(confidence: float) -> None:
    if not 0 < confidence < 1:
        raise ValueError(f"confidence must be between 0 and 1, got {confidence!r}")


def analyse(steps: list, confidence: float = 0.95) -> list:
    """One dict per step after the first: its rate against the previous step."""
    if len(steps) < 2:
        raise ValueError("a funnel needs at least two steps")
    for prev, cur in zip(steps, steps[1:]):
        if cur.users > prev.users:
            raise ValueError(
                f"{cur.name!r} has {cur.users:,} users, more than {prev.users:,} at {prev.name!r}. "
                "A user cannot reach a step without the one before it. Check the counts or the step order."
            )
    top = steps[0].users
    out = []
    for prev, cur in zip(steps, steps[1:]):
        row = {"step": cur.name, "from": prev.name, "entered": prev.users, "users": cur.users,
               "lost": prev.users - cur.users, "rate": None, "low": None, "high": None,
               "from_top": cur.users / top if top else None}
        if prev.users > 0:
            row["rate"] = cur.users / prev.users
            row["low"], row["high"] = wilson(cur.users, prev.users, confidence)
        out.append(row)
    return out


def biggest_leak(rows: list) -> dict:
    """The step with the lowest rate, and whether it can be told from the next lowest.

    `separable` is True when the two Wilson intervals do not overlap. The
    steps are nested groups of the same users, not independent samples, so
    this is a rough guide and not a formal test."""
    scored = [r for r in rows if r["rate"] is not None]
    if not scored:
        return {}
    ranked = sorted(scored, key=lambda r: r["rate"])
    worst = ranked[0]
    result = {"worst": worst, "next": None, "separable": None}
    if len(ranked) > 1:
        nxt = ranked[1]
        result["next"] = nxt
        result["separable"] = worst["high"] < nxt["low"]
    return result


def _open_rows(path: str):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(line for line in fh if not line.lstrip().startswith("#"))
        fields = {(f or "").strip().lower(): f for f in (reader.fieldnames or [])}
        rows = list(reader)
    return fields, rows


def load_counts(path: str) -> tuple:
    """(steps, problems) from a step,users file. Blank counts are skipped and reported."""
    fields, rows = _open_rows(path)
    steps, problems = [], []
    for i, raw in enumerate(rows, start=2):
        name = (raw[fields["step"]] or "").strip()
        text = (raw[fields["users"]] or "").strip().replace(",", "")
        if not name and not text:
            continue
        if not name:
            raise ValueError(f"row {i}: step name is blank")
        if not text:
            problems.append(f"row {i}: no count for {name!r}, step skipped. The next step is measured against the last step that has a count.")
            continue
        try:
            value = float(text)
        except ValueError:
            raise ValueError(f"row {i}: users for {name!r} is {text!r}, which is not a number") from None
        if value != int(value) or value < 0:
            raise ValueError(f"row {i}: users for {name!r} must be a whole number of zero or more, got {text!r}")
        if any(s.name == name for s in steps):
            raise ValueError(f"row {i}: step {name!r} appears twice")
        steps.append(Step(name, int(value)))
    if not steps:
        raise ValueError("no steps found in the file")
    return steps, problems


def load_events(path: str, order: list) -> tuple:
    """(steps, problems) from a user_id,event log, using the given step order."""
    if len(set(order)) != len(order):
        raise ValueError("--steps lists the same step twice")
    fields, rows = _open_rows(path)
    seen: dict = {}
    unknown = 0
    for i, raw in enumerate(rows, start=2):
        user = (raw[fields["user_id"]] or "").strip()
        event = (raw[fields["event"]] or "").strip()
        if not user and not event:
            continue
        if not user or not event:
            raise ValueError(f"row {i}: user_id or event is blank")
        if event not in order:
            unknown += 1
            continue
        seen.setdefault(user, set()).add(event)
    if not seen:
        raise ValueError("no events for the steps in --steps were found in the file")
    counts = [0] * len(order)
    skippers = 0
    for events in seen.values():
        depth = 0
        while depth < len(order) and order[depth] in events:
            depth += 1
        for k in range(depth):
            counts[k] += 1
        if any(order[k] in events for k in range(depth + 1, len(order))):
            skippers += 1
    problems = []
    if unknown:
        problems.append(f"{unknown:,} event rows are not in --steps and were ignored")
    if skippers:
        problems.append(
            f"{skippers:,} users did a later step without an earlier one. They are counted only up to "
            "the step before the gap. If tracking is broken at that step, fix that before trusting this funnel"
        )
    return [Step(name, n) for name, n in zip(order, counts)], problems


def load(path: str, order: list = None) -> tuple:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        header = next(csv.reader(line for line in fh if not line.lstrip().startswith("#")), [])
    names = {h.strip().lower() for h in header}
    if {"step", "users"} <= names:
        return load_counts(path)
    if {"user_id", "event"} <= names:
        if not order:
            raise ValueError("this looks like an event log (user_id, event). Pass the funnel order with --steps a,b,c")
        return load_events(path, order)
    raise ValueError("the file needs columns step and users, or user_id and event. "
                     f"Found: {', '.join(h.strip() for h in header) or 'nothing'}")


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("csv_path", help="step counts (step, users) or an event log (user_id, event)")
    parser.add_argument("--steps", help="funnel order for an event log, comma separated, for example visit,signup,paid")
    parser.add_argument("--confidence", type=float, default=0.95,
                        help="confidence level for the intervals (default 0.95)")
    parser.add_argument("--markdown", action="store_true", help="print a markdown table to paste into docs")


def run(args: argparse.Namespace) -> int:
    _check_confidence(args.confidence)
    order = [s.strip() for s in args.steps.split(",") if s.strip()] if args.steps else None
    steps, problems = load(args.csv_path, order)
    rows = analyse(steps, args.confidence)
    level = f"{args.confidence * 100:g}%"

    print(f"{steps[0].users:,} users at the top, {steps[-1].users:,} at the end, across {len(steps)} steps")
    if problems:
        print("Data problems:")
        for p in problems:
            print(f"  {p}")
    print()
    headers = ["Step", "Users", "Step rate", f"{level} interval", "Lost", "Of top"]
    table = [[steps[0].name, f"{steps[0].users:,}", "", "", "", "100%" if steps[0].users else "n/a"]]
    for r in rows:
        if r["rate"] is None:
            table.append([r["step"], f"{r['users']:,}", "n/a", "", f"{r['lost']:,}", "n/a"])
        else:
            table.append([r["step"], f"{r['users']:,}", f"{r['rate'] * 100:.1f}%",
                          f"{r['low'] * 100:.1f}% to {r['high'] * 100:.1f}%", f"{r['lost']:,}",
                          f"{r['from_top'] * 100:.1f}%"])
    print(markdown_table(headers, table) if args.markdown else format_table(headers, table, left=(0,)))

    top = steps[0].users
    if top > 0:
        low, high = wilson(steps[-1].users, top, args.confidence)
        print()
        print(f"End to end: {steps[-1].users / top * 100:.1f}% of users reach {steps[-1].name}, "
              f"{level} interval {low * 100:.1f}% to {high * 100:.1f}%.")

    leak = biggest_leak(rows)
    if leak:
        w, n = leak["worst"], leak["next"]
        print()
        print(f"Biggest leak: {w['from']} to {w['step']}, where only {w['rate'] * 100:.1f}% carry on "
              f"({w['lost']:,} of {w['entered']:,} lost).")
        if n is not None:
            verdict = ("The intervals do not overlap, so this step is probably the weakest."
                       if leak["separable"] else
                       "The intervals overlap, so this data cannot say it is worse than the next one.")
            print(f"Next lowest: {n['from']} to {n['step']} at {n['rate'] * 100:.1f}%. {verdict}")
    warnings = [f"{r['from']} to {r['step']}: only {r['entered']:,} users entered, the interval is wide"
                for r in rows if 0 < r["entered"] < SMALL_SAMPLE]
    warnings += [f"{r['from']} to {r['step']}: nobody entered this step, so there is no rate"
                 for r in rows if r["entered"] == 0]
    if warnings:
        print()
        print("Warnings:")
        for w in warnings:
            print(f"  {w}")
    return 0
