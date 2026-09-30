"""Sample ratio mismatch (SRM) check for experiments.

A 50/50 test that actually lands users 52/48 usually means the random
assignment itself is broken: a redirect that fails more often for one
arm, a bot filter that catches one variant's tracking pixel more than
the other's, a feature flag rollout that raced the experiment's own
flag. When assignment is broken, every downstream number from the test
is suspect, no matter how clean the conversion lift looks, because the
two groups were never actually comparable to start with.

This is the first check to run on any experiment's results, before
looking at conversion rates at all. It compares the split you
configured against the split you observed, using a chi-square
goodness-of-fit test, and says whether the gap is bigger than chance
would produce.

Method: standard chi-square goodness-of-fit test. The p-value threshold
defaults to 0.01, not the usual 0.05, following the convention used by
SRM checkers at Statsig and others, because SRM is checked on every
single experiment and a 1-in-20 false alarm rate would mean flagging
good experiments constantly. Microsoft's research on the same problem
(Fabijan et al., "Diagnosing Sample Ratio Mismatch in Online Controlled
Experiments", KDD 2019) uses an even stricter 0.0005, reasoning that
real SRMs produce p-values far below any reasonable threshold, so a
strict cutoff costs little power against genuine mismatches while
cutting false alarms further. Both are available here through --alpha.
Standard library only.
"""

from __future__ import annotations

import argparse
import csv
import math
from dataclasses import dataclass, field

from decisionlab.common import format_table, pct

TOOL = {
    "name": "srm",
    "persona": "marketing",
    "title": "Sample ratio mismatch check",
    "summary": "Checks whether an experiment's traffic actually landed in the split you configured, before you trust anything else it reports.",
    "doc": "docs/tools/srm.md",
}

MIN_EXPECTED = 5  # below this, the chi-square approximation is unreliable, same rule of thumb as a two-way contingency table


@dataclass
class Arm:
    name: str
    weight: float
    observed: int


@dataclass
class Result:
    arms: list
    expected: list
    chi2: float
    df: int
    p_value: float
    alpha: float
    mismatched: bool
    few_expected: bool
    warnings: list = field(default_factory=list)


def _log_gamma(x: float) -> float:
    """Lanczos approximation to ln(Gamma(x)), the standard coefficients (g=5, n=6)."""
    cof = [76.18009172947146, -86.50532032941677, 24.01409824083091,
           -1.231739572450155, 0.1208650973866179e-2, -0.5395239384953e-5]
    y = x
    tmp = x + 5.5
    tmp -= (x + 0.5) * math.log(tmp)
    series = 1.000000000190015
    for c in cof:
        y += 1
        series += c / y
    return -tmp + math.log(2.5066282746310005 * series / x)


def _gamma_series(a: float, x: float) -> float:
    """Regularized lower incomplete gamma P(a, x) by its series expansion. Valid for x < a + 1."""
    if x <= 0:
        return 0.0
    term = 1.0 / a
    total = term
    ap = a
    for _ in range(200):
        ap += 1
        term *= x / ap
        total += term
        if abs(term) < abs(total) * 1e-12:
            break
    return total * math.exp(-x + a * math.log(x) - _log_gamma(a))


def _gamma_continued_fraction(a: float, x: float) -> float:
    """Regularized upper incomplete gamma Q(a, x) by a continued fraction. Valid for x >= a + 1."""
    tiny = 1e-300
    b = x + 1.0 - a
    c = 1.0 / tiny
    d = 1.0 / b
    h = d
    for i in range(1, 201):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < tiny:
            d = tiny
        c = b + an / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-12:
            break
    return math.exp(-x + a * math.log(x) - _log_gamma(a)) * h


def chi2_sf(x: float, df: int) -> float:
    """P(a chi-square variable with `df` degrees of freedom exceeds `x`). This is the p-value
    for a goodness-of-fit test. Numerical Recipes' gammp/gammq algorithm, standard library only."""
    if df <= 0:
        raise ValueError("degrees of freedom must be at least 1")
    if x <= 0:
        return 1.0
    a = df / 2.0
    half_x = x / 2.0
    if half_x < a + 1.0:
        return max(0.0, 1.0 - _gamma_series(a, half_x))
    return max(0.0, _gamma_continued_fraction(a, half_x))


def check(arms: list, alpha: float = 0.01) -> Result:
    """Compare observed counts against the split the weights imply."""
    if len(arms) < 2:
        raise ValueError("need at least two arms to check a split")
    names = [a.name for a in arms]
    if len(set(names)) != len(names):
        raise ValueError("arm names must be unique")
    for a in arms:
        if a.weight <= 0:
            raise ValueError(f"{a.name!r}: expected weight must be more than zero")
        if a.observed < 0:
            raise ValueError(f"{a.name!r}: observed count cannot be negative")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")
    total_weight = sum(a.weight for a in arms)
    total_observed = sum(a.observed for a in arms)
    if total_observed == 0:
        raise ValueError("no visitors observed in any arm")
    expected = [total_observed * a.weight / total_weight for a in arms]
    chi2 = sum((a.observed - e) ** 2 / e for a, e in zip(arms, expected))
    df = len(arms) - 1
    p_value = chi2_sf(chi2, df)
    return Result(
        arms=arms, expected=expected, chi2=chi2, df=df, p_value=p_value, alpha=alpha,
        mismatched=p_value < alpha,
        few_expected=any(e < MIN_EXPECTED for e in expected),
    )


def _p(p: float) -> str:
    return "p < 0.0001" if p < 0.0001 else f"p = {p:.4f}"


def _pcell(p: float) -> str:
    return "<0.0001" if p < 0.0001 else f"{p:.4f}"


def verdict(r: Result) -> str:
    if r.mismatched:
        worst = max(range(len(r.arms)), key=lambda i: abs(r.arms[i].observed - r.expected[i]))
        arm = r.arms[worst]
        return (
            f"Sample ratio mismatch ({_p(r.p_value)}, below the {r.alpha} threshold). "
            f"{arm.name!r} got {arm.observed:,} visitors against {r.expected[worst]:,.0f} expected. "
            "This gap is too large to be chance. Something is skewing who lands in each arm: a redirect "
            "or load-time difference between variants, a bot or crawler filter that catches one variant's "
            "tag more than the other's, a feature flag that changed mid-test, or logging that drops events "
            "from one arm more than the other. Find and fix the cause before reading any result from this "
            "test. Every number downstream of a broken split is suspect."
        )
    return (
        f"No sample ratio mismatch ({_p(r.p_value)}, at or above the {r.alpha} threshold). "
        "The observed split is consistent with the assignment you configured. This does not prove "
        "assignment is bug free, only that the counts do not show the kind of skew that would flag it."
    )


@dataclass
class DayResult:
    day: str
    day_total: int
    cumulative: Result
    day_only: Result


@dataclass
class DailyReport:
    arm_names: list
    days: list
    first_cumulative_day: str | None
    first_day_only_day: str | None
    problems: list = field(default_factory=list)


def load_daily(path: str):
    """Read a long format CSV with columns day, arm, count. Returns
    ({day: {arm: count}}, arm names in first seen order, problems). Bad rows are
    reported with their line number and skipped. Repeated day and arm rows add up."""
    counts: dict = {}
    arm_names: list = []
    problems: list = []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        # Lines starting with # are comments, so an example file can label itself.
        lines = [(n, ln) for n, ln in enumerate(fh, start=1)
                 if ln.strip() and not ln.startswith("#")]
        if not lines:
            raise ValueError(f"{path}: the file is empty")
        header = [h.strip() for h in next(csv.reader([lines[0][1]]))]
        missing = {"day", "arm", "count"} - set(header)
        if missing:
            raise ValueError(f"{path}: missing column(s) {', '.join(sorted(missing))}. "
                             "Expected the header day,arm,count")
        for line_no, raw in lines[1:]:
            fields = next(csv.reader([raw]))
            if len(fields) != len(header):
                problems.append(f"line {line_no}: expected {len(header)} fields, got {len(fields)}, skipped")
                continue
            row = dict(zip(header, fields))
            day = (row["day"] or "").strip()
            arm = (row["arm"] or "").strip()
            if not day or not arm:
                problems.append(f"line {line_no}: blank day or arm, skipped")
                continue
            try:
                n = int((row["count"] or "").strip().replace(",", ""))
            except ValueError:
                problems.append(f"line {line_no}: count {row['count']!r} is not a whole number, skipped")
                continue
            if n < 0:
                problems.append(f"line {line_no}: negative count, skipped")
                continue
            if arm not in arm_names:
                arm_names.append(arm)
            counts.setdefault(day, {})
            counts[day][arm] = counts[day].get(arm, 0) + n
    return counts, arm_names, problems


def check_daily(counts: dict, arm_names: list, weights: dict | None = None,
                alpha: float = 0.01) -> DailyReport:
    """Run the SRM check on the running total after each day, and on each day alone.
    Days are taken in sorted order, so use ISO dates (YYYY-MM-DD)."""
    if len(arm_names) < 2:
        raise ValueError("need at least two arms in the daily file")
    if not counts:
        raise ValueError("the daily file has no usable rows")
    weights = weights or {}
    unknown = set(weights) - set(arm_names)
    if unknown:
        raise ValueError(f"weight given for arm(s) not in the file: {', '.join(sorted(unknown))}")
    problems: list = []
    running = {a: 0 for a in arm_names}
    days = []
    first_cum = first_day = None
    for day in sorted(counts):
        for a in arm_names:
            if a not in counts[day]:
                problems.append(f"{day}: no row for arm {a!r}, counted as 0")
        today = {a: counts[day].get(a, 0) for a in arm_names}
        for a in arm_names:
            running[a] += today[a]
        total = sum(today.values())
        if total == 0:
            problems.append(f"{day}: no visitors in any arm, day skipped")
            continue
        cum = check([Arm(a, weights.get(a, 1.0), running[a]) for a in arm_names], alpha)
        one = check([Arm(a, weights.get(a, 1.0), today[a]) for a in arm_names], alpha)
        # A flag on a tiny sample is not trusted, see MIN_EXPECTED.
        cum.mismatched = cum.mismatched and not cum.few_expected
        one.mismatched = one.mismatched and not one.few_expected
        if cum.mismatched and first_cum is None:
            first_cum = day
        if one.mismatched and first_day is None:
            first_day = day
        days.append(DayResult(day, total, cum, one))
    if not days:
        raise ValueError("no day in the file has any visitors")
    return DailyReport(arm_names, days, first_cum, first_day, problems)


def daily_verdict(rep: DailyReport, alpha: float) -> str:
    n = len(rep.days)
    if rep.first_cumulative_day:
        return (
            f"The running total first shows a sample ratio mismatch on {rep.first_cumulative_day} "
            f"(p below {alpha}). Look at what changed in assignment, logging or filters on or just "
            "before that day. Do not read conversion results from this test until the cause is found."
        )
    if rep.first_day_only_day:
        return (
            f"The running total never crosses the {alpha} threshold, but {rep.first_day_only_day} "
            "alone does. A bad day can be hidden by good days around it. Check what happened on that day."
        )
    return (
        f"No sample ratio mismatch on any of {n} daily checks at the {alpha} threshold. "
        "This does not prove assignment is bug free. Note that checking every day gives the "
        "test many chances to raise a false alarm, so a lone flag near the threshold deserves a "
        "second look rather than instant panic."
    )


def _print_daily(rep: DailyReport, alpha: float) -> None:
    headers = ["Day", "Visitors", "Total so far", "Split so far", "p so far", "p that day", "Flag"]
    rows = []
    running = 0
    for d in rep.days:
        running += d.day_total
        tot = sum(a.observed for a in d.cumulative.arms) or 1
        split = " / ".join(pct(a.observed / tot, 1) for a in d.cumulative.arms)
        flag = ("MISMATCH" if d.cumulative.mismatched
                else "bad day" if d.day_only.mismatched else "")
        rows.append([d.day, f"{d.day_total:,}", f"{running:,}", split,
                     _pcell(d.cumulative.p_value), _pcell(d.day_only.p_value), flag])
    print("Arms, in split order: " + " / ".join(rep.arm_names))
    print(format_table(headers, rows, left=(0, 3, 6)))
    print()
    print(daily_verdict(rep, alpha))


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--daily", metavar="CSV",
        help="a CSV with columns day,arm,count. Checks the running total after every day "
             "and each day alone, and names the first day the split goes wrong. Use instead of --arm.",
    )
    parser.add_argument("--weight", nargs=2, action="append", metavar=("NAME", "WEIGHT"),
                        help="with --daily, expected weight for an arm (default 1 for every arm)")
    parser.add_argument(
        "--arm", nargs=3, action="append",
        metavar=("NAME", "EXPECTED_WEIGHT", "OBSERVED_COUNT"),
        help="repeat once per arm, for example --arm control 1 4820 --arm variant 1 5180. "
             "Weights only need to be in proportion: 1 1 means 50/50, 2 1 means a 2:1 split.",
    )
    parser.add_argument("--alpha", type=float, default=0.01,
                        help="p-value threshold for flagging a mismatch (default 0.01)")


def run_daily(args: argparse.Namespace) -> int:
    if args.arm:
        raise ValueError("use either --daily or --arm, not both")
    weights = {}
    for name, w in args.weight or []:
        try:
            weights[name] = float(w)
        except ValueError:
            raise ValueError(f"{name!r}: expected weight {w!r} is not a number") from None
    counts, arm_names, problems = load_daily(args.daily)
    try:
        rep = check_daily(counts, arm_names, weights, args.alpha)
    except ValueError as exc:
        if problems:
            raise ValueError(f"{exc}. Rows skipped: " + "; ".join(problems)) from None
        raise
    _print_daily(rep, args.alpha)
    problems += rep.problems
    if problems:
        print()
        print("Problems in the file:")
        for line in problems:
            print(f"  {line}")
    return 0


def run(args: argparse.Namespace) -> int:
    if args.daily:
        return run_daily(args)
    if args.weight:
        raise ValueError("--weight only works with --daily. With --arm, give the weight in the arm")
    if not args.arm or len(args.arm) < 2:
        raise ValueError("need at least two --arm entries to check a split")
    arms = []
    for name, weight_s, count_s in args.arm:
        try:
            weight = float(weight_s)
        except ValueError:
            raise ValueError(f"{name!r}: expected weight {weight_s!r} is not a number") from None
        try:
            count = int(count_s)
        except ValueError:
            raise ValueError(f"{name!r}: observed count {count_s!r} is not a whole number") from None
        arms.append(Arm(name=name, weight=weight, observed=count))
    res = check(arms, args.alpha)
    total_weight = sum(a.weight for a in res.arms)
    headers = ["Arm", "Expected split", "Expected count", "Observed count", "Observed split"]
    rows = [
        [a.name, pct(a.weight / total_weight, 1), f"{e:,.1f}", f"{a.observed:,}",
         pct(a.observed / sum(x.observed for x in res.arms), 1)]
        for a, e in zip(res.arms, res.expected)
    ]
    print(format_table(headers, rows, left=(0,)))
    print()
    print(f"Chi-square = {res.chi2:.3f}, df = {res.df}, {_p(res.p_value)}")
    if res.few_expected:
        print(f"Warning: an arm's expected count is below {MIN_EXPECTED}. "
              "The chi-square approximation is unreliable this low; collect more traffic first.")
    print()
    print(verdict(res))
    return 0
