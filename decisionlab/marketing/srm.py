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


def add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--arm", nargs=3, action="append", required=True,
        metavar=("NAME", "EXPECTED_WEIGHT", "OBSERVED_COUNT"),
        help="repeat once per arm, for example --arm control 1 4820 --arm variant 1 5180. "
             "Weights only need to be in proportion: 1 1 means 50/50, 2 1 means a 2:1 split.",
    )
    parser.add_argument("--alpha", type=float, default=0.01,
                        help="p-value threshold for flagging a mismatch (default 0.01)")


def run(args: argparse.Namespace) -> int:
    if len(args.arm) < 2:
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
