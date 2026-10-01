"""Net Promoter Score with a confidence interval, and a test between two segments.

The mistake it fixes: an NPS that moves from 31 to 36 gets reported as an
improvement, when the interval around each number is plus or minus ten and
the move is noise. NPS looks like one number, but it is a difference
between two shares, and it is noisy. A survey of 100 people can give an
interval more than 30 points wide.

Method. Each reply is a promoter (9 or 10), a passive (7 or 8) or a
detractor (0 to 6). With p the promoter share, d the detractor share and n
replies, NPS = (p - d) x 100. The variance of p - d, treating the three
groups as one multinomial draw, is (p + d - (p - d)^2) / n. The interval is
NPS plus or minus z x 100 x sqrt(variance). Two segments are compared with
a z-test on the difference, using the sum of the two variances.

This is the plain Wald interval. It is a poor fit for small samples and for
scores near the ends of the scale, which the tool warns about.

CSV columns (header row required, case-insensitive):
    score             0 to 10, whole numbers
    segment           optional, any label (plan, region, survey month)
Lines starting with # are skipped, so a file can label itself. Row numbers in
errors count the data rows, not the comment lines.
Standard library only.
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from statistics import NormalDist

from decisionlab.common import format_table, markdown_table

TOOL = {
    "name": "nps",
    "persona": "product",
    "title": "NPS with a confidence interval and segment comparison",
    "summary": "Scores NPS from raw 0 to 10 replies, puts an interval on it and tests whether two segments really differ.",
    "doc": "docs/tools/nps.md",
}

_N = NormalDist()
SMALL_SAMPLE = 30   # below this the normal interval is unreliable, so the tool warns


@dataclass
class Result:
    label: str
    promoters: int
    passives: int
    detractors: int

    @property
    def n(self) -> int:
        return self.promoters + self.passives + self.detractors

    @property
    def nps(self) -> float:
        return 100 * (self.promoters - self.detractors) / self.n

    @property
    def variance(self) -> float:
        """Variance of (p - d), as a fraction squared (not in points)."""
        p = self.promoters / self.n
        d = self.detractors / self.n
        return (p + d - (p - d) ** 2) / self.n


def tally(label: str, scores: list) -> Result:
    if not scores:
        raise ValueError(f"no scores for {label!r}")
    return Result(
        label,
        promoters=sum(1 for s in scores if s >= 9),
        passives=sum(1 for s in scores if 7 <= s <= 8),
        detractors=sum(1 for s in scores if s <= 6),
    )


def interval(result: Result, confidence: float = 0.95) -> tuple:
    """(low, high) for the NPS, in points, clipped to the -100 to 100 range."""
    _check_confidence(confidence)
    half = _N.inv_cdf(1 - (1 - confidence) / 2) * 100 * result.variance ** 0.5
    return max(-100.0, result.nps - half), min(100.0, result.nps + half)


def compare(a: Result, b: Result, confidence: float = 0.95) -> dict:
    """Difference a minus b in points, its interval and a two-sided p-value."""
    _check_confidence(confidence)
    diff = a.nps - b.nps
    se = 100 * (a.variance + b.variance) ** 0.5
    if se == 0:
        # Every reply in both segments falls in one group, so there is no spread to test with.
        return {"diff": diff, "low": diff, "high": diff, "p": 0.0 if diff else 1.0}
    z = diff / se
    crit = _N.inv_cdf(1 - (1 - confidence) / 2)
    return {"diff": diff, "low": diff - crit * se, "high": diff + crit * se,
            "p": 2 * (1 - _N.cdf(abs(z)))}


def _check_confidence(confidence: float) -> None:
    if not 0 < confidence < 1:
        raise ValueError(f"confidence must be between 0 and 1, got {confidence!r}")


def load_scores(path: str) -> dict:
    """{segment: [scores]}. Rows without a segment column go under 'all'."""
    groups: dict = {}
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(line for line in fh if not line.lstrip().startswith("#"))
        fields = {(f or "").strip().lower(): f for f in (reader.fieldnames or [])}
        if "score" not in fields:
            raise ValueError("missing column: score")
        seg_col = fields.get("segment")
        for i, raw in enumerate(reader, start=2):
            text = (raw[fields["score"]] or "").strip()
            seg = (raw[seg_col] or "").strip() if seg_col else ""
            if not text and not seg:
                continue
            try:
                score = float(text)
            except ValueError:
                raise ValueError(f"row {i}: score is {text!r}, which is not a number") from None
            if score != int(score) or not 0 <= score <= 10:
                raise ValueError(f"row {i}: score {text!r} must be a whole number from 0 to 10")
            if seg_col and not seg:
                raise ValueError(f"row {i}: segment is blank")
            groups.setdefault(seg or "all", []).append(int(score))
    if not groups:
        raise ValueError("no scores found in the file")
    return groups


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("csv_path", help="CSV with a score column (0 to 10) and an optional segment column")
    parser.add_argument("--compare", nargs=2, metavar=("A", "B"),
                        help="test whether segment A and segment B differ (needed if there are more than two segments)")
    parser.add_argument("--confidence", type=float, default=0.95,
                        help="confidence level for the intervals (default 0.95)")
    parser.add_argument("--markdown", action="store_true", help="print a markdown table to paste into docs")


def run(args: argparse.Namespace) -> int:
    groups = load_scores(args.csv_path)
    results = {name: tally(name, scores) for name, scores in groups.items()}
    pair = args.compare
    if pair:
        for name in pair:
            if name not in results:
                raise ValueError(f"segment {name!r} is not in the file, found: {', '.join(results)}")
        if pair[0] == pair[1]:
            raise ValueError("--compare needs two different segments")
    elif len(results) == 2:
        pair = list(results)
    level = f"{args.confidence * 100:g}%"
    headers = ["Segment", "Replies", "Promoters", "Passives", "Detractors", "NPS", f"{level} interval"]
    rows = []
    for r in results.values():
        low, high = interval(r, args.confidence)
        rows.append([r.label, r.n, f"{r.promoters / r.n * 100:.0f}%", f"{r.passives / r.n * 100:.0f}%",
                     f"{r.detractors / r.n * 100:.0f}%", f"{r.nps:.0f}", f"{low:.0f} to {high:.0f}"])
    print(markdown_table(headers, rows) if args.markdown else format_table(headers, rows, left=(0,)))
    if pair:
        a, b = results[pair[0]], results[pair[1]]
        c = compare(a, b, args.confidence)
        print()
        if min(a.n, b.n) < SMALL_SAMPLE:
            verdict = "With so few replies this test cannot be trusted either way."
        else:
            verdict = ("The interval on the difference excludes zero, so the gap is unlikely to be noise."
                       if c["low"] > 0 or c["high"] < 0 else
                       "The interval on the difference includes zero, so this survey cannot tell the two apart.")
        print(f"{a.label} minus {b.label}: {c['diff']:+.0f} points, {level} interval "
              f"{c['low']:+.0f} to {c['high']:+.0f}, p = {c['p']:.3f}. {verdict}")
    if len(results) > 2 and not args.compare:
        print()
        print(f"{len(results)} segments found. Pass --compare A B to test two of them.")
    warnings = [f"{r.label}: only {r.n} {'reply' if r.n == 1 else 'replies'}, the interval is unreliable below {SMALL_SAMPLE}"
                for r in results.values() if r.n < SMALL_SAMPLE]
    warnings += [f"{r.label}: every reply is in one group, so the interval has zero width and means nothing"
                 for r in results.values() if r.n >= 1 and r.variance == 0]
    if warnings:
        print()
        print("Warnings:")
        for w in warnings:
            print(f"  {w}")
    return 0
