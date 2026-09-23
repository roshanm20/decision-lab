"""A/B test calculator for conversion rates.

Two questions, one tool:

  size     How many visitors per variant do I need before I start?
  analyze  I have results. Is the difference real, and if it is flat,
           was the test big enough to have seen an effect at all?

The second half of `analyze` is the part most calculators leave out. A
flat result from an underpowered test does not mean "no effect". It means
the test could not have seen one. The tool says which case you are in.

Method: two-sided test on two proportions. Sample size uses the standard
normal approximation formula. Significance uses a pooled z-test. The
confidence interval on the difference is the unpooled Wald interval. All
of these assume each visitor is independent and counted once, and they get
unreliable when conversions are very few (the tool warns below 10).
Standard library only.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from statistics import NormalDist

from decisionlab.common import pct

TOOL = {
    "name": "ab-test",
    "persona": "marketing",
    "title": "A/B test calculator",
    "summary": "Sample size before a test, significance after it, and a plain answer on whether a flat result was just underpowered.",
    "doc": "docs/tools/ab-test.md",
}

_N = NormalDist()


def _z(q: float) -> float:
    return _N.inv_cdf(q)


def sample_size_per_arm(baseline: float, mde: float, alpha: float = 0.05,
                        power: float = 0.8, relative: bool = False) -> int:
    """Visitors needed in EACH variant to detect a change of `mde` from `baseline`.

    `mde` is absolute (0.02 means 10% to 12%) unless relative=True
    (0.2 means 10% to 12% as well, a 20% relative lift).
    """
    if not 0 < baseline < 1:
        raise ValueError("baseline must be a rate between 0 and 1, for example 0.10")
    if not 0 < alpha < 1 or not 0 < power < 1:
        raise ValueError("alpha and power must be between 0 and 1")
    p1 = baseline
    p2 = baseline * (1 + mde) if relative else baseline + mde
    if not 0 < p2 < 1:
        raise ValueError(f"baseline plus the effect gives {p2:.4f}, which is not a valid rate")
    if p2 == p1:
        raise ValueError("the minimum detectable effect cannot be zero")
    p_bar = (p1 + p2) / 2
    numerator = (_z(1 - alpha / 2) * math.sqrt(2 * p_bar * (1 - p_bar))
                 + _z(power) * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
    return math.ceil(numerator / (p2 - p1) ** 2)


@dataclass
class Analysis:
    rate_a: float
    rate_b: float
    diff: float
    relative_lift: float
    ci_low: float
    ci_high: float
    p_value: float
    significant: bool
    detectable_abs: float
    few_conversions: bool


def analyze(n_a: int, x_a: int, n_b: int, x_b: int, alpha: float = 0.05,
            power: float = 0.8) -> Analysis:
    """Compare control (a) with variant (b). n is visitors, x is conversions."""
    for n, x, label in ((n_a, x_a, "control"), (n_b, x_b, "variant")):
        if n <= 0:
            raise ValueError(f"{label} visitors must be more than zero")
        if not 0 <= x <= n:
            raise ValueError(f"{label} conversions must be between 0 and its visitors")
    p_a, p_b = x_a / n_a, x_b / n_b
    diff = p_b - p_a
    pooled = (x_a + x_b) / (n_a + n_b)
    se_pooled = math.sqrt(pooled * (1 - pooled) * (1 / n_a + 1 / n_b))
    if se_pooled == 0:
        p_value = 1.0
    else:
        p_value = 2 * (1 - _N.cdf(abs(diff) / se_pooled))
    se = math.sqrt(p_a * (1 - p_a) / n_a + p_b * (1 - p_b) / n_b)
    z = _z(1 - alpha / 2)
    # Smallest absolute difference this sample could reliably detect, using
    # the control rate for both arms, or the pooled rate when the control rate
    # is 0 or 100 percent. An approximation, stated as such. NaN when both arms
    # are all 0 or all 1, because then there is no variation to judge from.
    n_small = min(n_a, n_b)
    base = p_a if 0 < p_a < 1 else pooled
    detectable = (z + _z(power)) * math.sqrt(2 * base * (1 - base) / n_small) if 0 < base < 1 else float("nan")
    return Analysis(
        rate_a=p_a, rate_b=p_b, diff=diff,
        relative_lift=(diff / p_a) if p_a else float("nan"),
        ci_low=diff - z * se, ci_high=diff + z * se,
        p_value=p_value, significant=p_value < alpha,
        detectable_abs=detectable,
        few_conversions=min(x_a, x_b) < 10,
    )


def _p(p: float) -> str:
    return "p < 0.001" if p < 0.001 else f"p = {p:.3f}"


def verdict(a: Analysis, mde: float = None) -> str:
    """One paragraph a marketer can paste into a decision thread.

    `mde` is the smallest absolute change that would matter to the business.
    Without it, a flat result can only be described, not judged, because
    "underpowered" only means something relative to an effect you care about.
    """
    if a.significant:
        direction = "better" if a.diff > 0 else "worse"
        return (f"The variant converts {direction} than control, and the difference is unlikely to be "
                f"noise ({_p(a.p_value)}). The true difference is probably between "
                f"{a.ci_low * 100:+.2f} and {a.ci_high * 100:+.2f} percentage points.")
    if math.isnan(a.detectable_abs):
        return ("Cannot judge this test. Both arms converted at 0 percent or both at 100 percent, so "
                "there is no variation to measure a difference against. Check the tracking before "
                "anything else.")
    reach = f"{a.detectable_abs * 100:.2f}"
    if mde is None:
        return (f"No reliable difference ({_p(a.p_value)}). At this sample size the test could reliably "
                f"detect a change of about {reach} percentage points or more. Anything smaller is not "
                f"ruled out. Pass --mde with the smallest change that matters to you for a firmer answer.")
    if a.detectable_abs > mde:
        return (f"No reliable difference, and the test was too small to settle it. You care about "
                f"changes of {mde * 100:.2f} points, but this sample could only reliably detect about "
                f"{reach}. This is 'we could not tell', not 'there is no effect'. Run longer or test a "
                f"bolder change.")
    return (f"No reliable difference ({_p(a.p_value)}), and the test was big enough to see a change of "
            f"{mde * 100:.2f} points if one existed. So a change that big is unlikely. A smaller one is "
            f"still possible, but by your own threshold it would not matter.")


def add_arguments(parser: argparse.ArgumentParser) -> None:
    sub = parser.add_subparsers(dest="mode", required=True)
    s = sub.add_parser("size", help="visitors needed per variant before you start")
    s.add_argument("--baseline", type=float, required=True, help="current conversion rate, e.g. 0.10")
    s.add_argument("--mde", type=float, required=True,
                   help="smallest change worth detecting, absolute (0.02) unless --relative")
    s.add_argument("--relative", action="store_true", help="read --mde as a relative lift (0.2 = +20%%)")
    s.add_argument("--alpha", type=float, default=0.05)
    s.add_argument("--power", type=float, default=0.8)
    s.add_argument("--daily-visitors", type=int, help="total daily traffic into the test, to estimate days")
    a = sub.add_parser("analyze", help="is the observed difference real")
    a.add_argument("--control", nargs=2, type=int, metavar=("VISITORS", "CONVERSIONS"), required=True)
    a.add_argument("--variant", nargs=2, type=int, metavar=("VISITORS", "CONVERSIONS"), required=True)
    a.add_argument("--alpha", type=float, default=0.05)
    a.add_argument("--power", type=float, default=0.8)
    a.add_argument("--mde", type=float,
                   help="smallest absolute change that matters to you, e.g. 0.01 for one point")


def run(args: argparse.Namespace) -> int:
    if args.mode == "size":
        if args.daily_visitors is not None and args.daily_visitors <= 0:
            raise ValueError("--daily-visitors must be more than zero")
        n = sample_size_per_arm(args.baseline, args.mde, args.alpha, args.power, args.relative)
        target = args.baseline * (1 + args.mde) if args.relative else args.baseline + args.mde
        print(f"Baseline {pct(args.baseline, 2)} to {pct(target, 2)}, "
              f"alpha {args.alpha}, power {args.power}, two-sided")
        print(f"Visitors needed per variant : {n:,}")
        print(f"Visitors needed in total    : {2 * n:,}")
        if args.daily_visitors:
            days = math.ceil(2 * n / args.daily_visitors)
            print(f"Days at {args.daily_visitors:,} visitors a day : {days}")
            if days < 7:
                print("Run it for at least a full week anyway, so weekday and weekend behaviour both count.")
        return 0

    n_a, x_a = args.control
    n_b, x_b = args.variant
    res = analyze(n_a, x_a, n_b, x_b, args.alpha, args.power)
    print(f"Control : {x_a:,} / {n_a:,} = {pct(res.rate_a, 2)}")
    print(f"Variant : {x_b:,} / {n_b:,} = {pct(res.rate_b, 2)}")
    rel = "n/a" if math.isnan(res.relative_lift) else f"{res.relative_lift * 100:+.1f}%"
    print(f"Difference : {res.diff * 100:+.2f} points ({rel} relative)")
    print(f"{int((1 - args.alpha) * 100)}% interval on the difference : "
          f"{res.ci_low * 100:+.2f} to {res.ci_high * 100:+.2f} points")
    print(f"p-value : {res.p_value:.4f}")
    if res.few_conversions:
        print("Warning: fewer than 10 conversions in an arm. The approximation behind these numbers is shaky here.")
    print()
    print(verdict(res, args.mde))
    return 0
