"""Kano classification of features from paired survey answers.

The mistake it fixes: a team asks "would you like feature X?", hears yes
from nearly everyone and builds it as if it would delight. But a yes tells
you nothing about what happens when the feature is missing. Some features
are expected, so having them earns nothing and lacking them costs a lot.
Others are liked but not missed. The Kano survey asks two questions per
feature, one for "if the product has it" (functional) and one for "if it
does not" (dysfunctional), and the pair of answers puts each respondent's
view of the feature into one category.

Method. Each answer is one of: like, must-be, neutral, live-with, dislike.
The pair goes through the standard 5 by 5 evaluation table (Table 3 in
arxiv.org/abs/1901.05130) to one of six codes:
    A attractive, O one-dimensional, M must-be, I indifferent,
    R reverse (the respondent would rather not have it),
    Q questionable (the two answers contradict each other).
A feature takes the code most respondents gave it. When two codes tie, the
tool says so and does not pick one. The Better and Worse coefficients are
(A + O) / (A + O + M + I) and -(O + M) / (A + O + M + I).

CSV columns (header row required, case-insensitive):
    feature           feature name
    functional        answer when the feature is present
    dysfunctional     answer when the feature is absent
Answers may be written like, must-be, neutral, live-with, dislike (spaces
and underscores also work), or as the numbers 1 to 5 in that order. Lines
starting with # are skipped. Row numbers in errors count the data rows.
Standard library only.
"""

from __future__ import annotations

import argparse
import csv

from decisionlab.common import format_table, markdown_table

TOOL = {
    "name": "kano",
    "persona": "product",
    "title": "Kano classifier for feature surveys",
    "summary": "Turns paired present and absent survey answers into a Kano category per feature, with counts, ties flagged and Better and Worse scores.",
    "doc": "docs/tools/kano.md",
}

ANSWERS = ["like", "must-be", "neutral", "live-with", "dislike"]
CODES = ["A", "O", "M", "I", "R", "Q"]
NAMES = {"A": "attractive", "O": "one-dimensional", "M": "must-be",
         "I": "indifferent", "R": "reverse", "Q": "questionable"}
# Rows: functional answer. Columns: dysfunctional answer. Same order as ANSWERS.
TABLE = [
    ["Q", "A", "A", "A", "O"],
    ["R", "I", "I", "I", "M"],
    ["R", "I", "I", "I", "M"],
    ["R", "I", "I", "I", "M"],
    ["R", "R", "R", "R", "Q"],
]
SMALL_SAMPLE = 30   # my floor for a feature's replies, not a published threshold
CLOSE_GAP = 0.10    # second code within this share of the first is flagged as close


def classify(functional: str, dysfunctional: str) -> str:
    """The Kano code for one respondent's pair of answers."""
    return TABLE[_answer_index(functional)][_answer_index(dysfunctional)]


def _answer_index(text: str) -> int:
    key = str(text).strip().lower().replace("_", "-").replace(" ", "-")
    if key in ANSWERS:
        return ANSWERS.index(key)
    if key in {"1", "2", "3", "4", "5"}:
        return int(key) - 1
    raise ValueError(f"{text!r} is not one of {', '.join(ANSWERS)} or 1 to 5")


def tally(pairs: list) -> dict:
    """{code: count} for a list of (functional, dysfunctional) answers."""
    counts = dict.fromkeys(CODES, 0)
    for f, d in pairs:
        counts[classify(f, d)] += 1
    return counts


def verdict(counts: dict) -> tuple:
    """(codes at the top, share of the top code). More than one code means a tie."""
    n = sum(counts.values())
    if n == 0:
        raise ValueError("no answers to classify")
    top = max(counts.values())
    return [c for c in CODES if counts[c] == top], top / n


def better_worse(counts: dict):
    """(better, worse) or None when A, O, M and I are all zero."""
    base = counts["A"] + counts["O"] + counts["M"] + counts["I"]
    if base == 0:
        return None
    return (counts["A"] + counts["O"]) / base, -(counts["O"] + counts["M"]) / base


def load_answers(path: str) -> dict:
    """{feature: [(functional, dysfunctional)]}, in file order."""
    groups: dict = {}
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(line for line in fh if not line.lstrip().startswith("#"))
        fields = {(f or "").strip().lower(): f for f in (reader.fieldnames or [])}
        for need in ("feature", "functional", "dysfunctional"):
            if need not in fields:
                raise ValueError(f"missing column: {need}")
        for i, raw in enumerate(reader, start=2):
            feature = (raw[fields["feature"]] or "").strip()
            f_text = (raw[fields["functional"]] or "").strip()
            d_text = (raw[fields["dysfunctional"]] or "").strip()
            if not (feature or f_text or d_text):
                continue
            if not feature:
                raise ValueError(f"row {i}: feature is blank")
            for label, text in (("functional", f_text), ("dysfunctional", d_text)):
                try:
                    _answer_index(text)
                except ValueError as err:
                    raise ValueError(f"row {i}: {label} answer {err}") from None
            groups.setdefault(feature, []).append((f_text, d_text))
    if not groups:
        raise ValueError("no answers found in the file")
    return groups


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("csv_path", help="CSV with feature, functional and dysfunctional columns")
    parser.add_argument("--markdown", action="store_true", help="print a markdown table to paste into docs")


def run(args: argparse.Namespace) -> int:
    groups = load_answers(args.csv_path)
    headers = ["Feature", "Replies", *CODES, "Category", "Share", "Better", "Worse"]
    rows, notes = [], []
    for feature, pairs in groups.items():
        counts = tally(pairs)
        n = len(pairs)
        top, share = verdict(counts)
        bw = better_worse(counts)
        label = "/".join(NAMES[c] for c in top) + (" (tie)" if len(top) > 1 else "")
        rows.append([feature, n, *(counts[c] for c in CODES), label, f"{share * 100:.0f}%",
                     f"{bw[0]:.2f}" if bw else "n/a", f"{bw[1]:.2f}" if bw else "n/a"])
        if len(top) > 1:
            notes.append(f"{feature}: {' and '.join(NAMES[c] for c in top)} tie, {counts[top[0]]} each, "
                         "so there is no single category.")
        else:
            rest = sorted((counts[c] for c in CODES if c != top[0]), reverse=True)[0] / n
            if share - rest <= CLOSE_GAP:
                second = max((c for c in CODES if c != top[0]), key=lambda c: counts[c])
                notes.append(f"{feature}: {NAMES[top[0]]} leads {NAMES[second]} by only "
                             f"{(share - rest) * 100:.0f} points, so treat the category as unsettled.")
        if n < SMALL_SAMPLE:
            notes.append(f"{feature}: only {n} {'reply' if n == 1 else 'replies'}, the category can flip with a few answers.")
        if counts["Q"] / n >= 0.10:
            notes.append(f"{feature}: {counts['Q']} of {n} answer pairs contradict each other (Q), "
                         "which usually means the question was misread.")
    print(markdown_table(headers, rows) if args.markdown else format_table(headers, rows, left=(0, 8)))
    print()
    print("A attractive, O one-dimensional, M must-be, I indifferent, R reverse, Q questionable.")
    if notes:
        print()
        print("Notes:")
        for note in notes:
            print(f"  {note}")
    return 0
