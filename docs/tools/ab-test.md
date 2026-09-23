# A/B test calculator

**For:** marketers, growth teams and product managers running experiments on conversion rates.

**Command:** `python -m decisionlab ab-test size ...` before the test, `python -m decisionlab ab-test analyze ...` after it.

## The problem it solves

Two mistakes cost the most in experiments. Stopping a test before it had enough traffic, and reading a flat result as proof that a change does nothing. The second one kills good ideas quietly. A test that could only ever have seen a 4 point change says nothing about a 1 point change, but the dashboard shows the same grey "not significant" either way.

`size` tells you how much traffic you need before you start. `analyze` tells you whether the result is real, and when it is flat, whether the test was big enough to have seen the effect you care about.

## Run it

```bash
python -m decisionlab ab-test size --baseline 0.10 --mde 0.02 --daily-visitors 2000
python -m decisionlab ab-test analyze --control 1000 100 --variant 1000 108 --mde 0.01
```

`--mde` is absolute by default (0.02 means 10% to 12%). Add `--relative` to `size` to give it as a lift instead (0.2 means +20%).

## Example, real output

Planning a test to move a 10 percent conversion rate to 12 percent:

```
$ python -m decisionlab ab-test size --baseline 0.10 --mde 0.02 --daily-visitors 2000
Baseline 10.00% to 12.00%, alpha 0.05, power 0.8, two-sided
Visitors needed per variant : 3,841
Visitors needed in total    : 7,682
Days at 2,000 visitors a day : 4
Run it for at least a full week anyway, so weekday and weekend behaviour both count.
```

A small test that came out flat, when the team cares about a 1 point change:

```
$ python -m decisionlab ab-test analyze --control 1000 100 --variant 1000 108 --mde 0.01
Control : 100 / 1,000 = 10.00%
Variant : 108 / 1,000 = 10.80%
Difference : +0.80 points (+8.0% relative)
95% interval on the difference : -1.88 to +3.48 points
p-value : 0.5579

No reliable difference, and the test was too small to settle it. You care about changes of 1.00 points, but this sample could only reliably detect about 3.76. This is 'we could not tell', not 'there is no effect'. Run longer or test a bolder change.
```

A large test that came out flat, same threshold:

```
$ python -m decisionlab ab-test analyze --control 200000 20000 --variant 200000 20050 --mde 0.01
Control : 20,000 / 200,000 = 10.00%
Variant : 20,050 / 200,000 = 10.03%
Difference : +0.03 points (+0.3% relative)
95% interval on the difference : -0.16 to +0.21 points
p-value : 0.7923

No reliable difference (p = 0.792), and the test was big enough to see a change of 1.00 points if one existed. So a change that big is unlikely. A smaller one is still possible, but by your own threshold it would not matter.
```

Both results are "not significant". Only the second one tells you anything about whether the change works.

## Method

- Sample size: the standard normal-approximation formula for comparing two proportions, two-sided.
- Significance: pooled two-proportion z-test.
- Interval on the difference: unpooled Wald interval.
- Detectable effect after the fact: `(z for alpha + z for power) x sqrt(2 p (1 - p) / n)`, using the control rate for both arms. This is an approximation and the output says so by calling it "about".

The tests in `tests/test_ab_test.py` check the sample size formula against a separately written copy of the same formula, and check the analysis against numbers worked out by hand.

## What it does not do

- Conversion rates only. No revenue per visitor, average order value or other continuous metrics.
- One variant against control. With several variants, you need a correction for multiple comparisons, and this tool does not apply one.
- No sequential testing. If you check results every day and stop the moment p drops under 0.05, the p-values here are wrong. Decide the sample size first and look once.
- Assumes every visitor is counted once and independently. Tests randomised by account or by city need a different calculation.
