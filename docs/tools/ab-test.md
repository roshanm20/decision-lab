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

### Several variants

Repeat `--variant` for each one. Every variant is compared with control, and the p-values are adjusted with the Holm method. Test four variants at 0.05 each and the chance of at least one false winner is about 1 - 0.95^4, roughly 19 percent if the tests were independent, even if nothing works.

```
$ python -m decisionlab ab-test analyze --control 5000 500 --variant 5000 575 --variant 5000 540 --variant 5000 515 --variant 5000 495
Control : 500 / 5,000 = 10.00%
4 variants, each against control. Holm correction at alpha 0.05.
              rate  diff (pts)    raw p   Holm p  result
variant 1   11.50%       +1.50   0.0155   0.0619  not significant
variant 2   10.80%       +0.80   0.1901   0.5702  not significant
variant 3   10.30%       +0.30   0.6194   1.0000  not significant
variant 4    9.90%       -0.10   0.8673   1.0000  not significant

No variant beats control once the correction for 4 comparisons is applied. variant 1 looked significant on its own but does not survive the correction, so treat it as likely noise. A flat variant here is not proof of no effect. Check the sample size with `size`.
```

Variant 1 passes a plain test at 0.0155 and fails after correction. The counts above are made up to show this case. They are not data from a real test.

```
$ python -m decisionlab ab-test analyze --control 5000 500 --variant 5000 650 --variant 5000 575 --variant 5000 515
Control : 500 / 5,000 = 10.00%
3 variants, each against control. Holm correction at alpha 0.05.
              rate  diff (pts)    raw p   Holm p  result
variant 1   13.00%       +3.00   0.0000   0.0000  survives, better
variant 2   11.50%       +1.50   0.0155   0.0309  survives, better
variant 3   10.30%       +0.30   0.6194   0.6194  not significant

variant 1, variant 2 still differ from control after the correction for 3 comparisons. A flat variant here is not proof of no effect. Check the sample size with `size`.
```

Here a real-sized gap survives. Also illustrative counts.

## Method

- Sample size: the standard normal-approximation formula for comparing two proportions, two-sided.
- Several variants: Holm step-down. Sort the p-values from smallest, multiply the smallest by the number of variants, the next by one less, and so on. Keep a running maximum so adjusted values never fall. A variant survives when its adjusted p is under alpha. It controls the chance of any false winner at alpha, and is never weaker than Bonferroni.
- Significance: pooled two-proportion z-test.
- Interval on the difference: unpooled Wald interval.
- Detectable effect after the fact: `(z for alpha + z for power) x sqrt(2 p (1 - p) / n)`, using the control rate for both arms. This is an approximation and the output says so by calling it "about".

The tests in `tests/test_ab_test.py` check the sample size formula against a separately written copy of the same formula, and check the analysis against numbers worked out by hand.

## What it does not do

- Conversion rates only. No revenue per visitor, average order value or other continuous metrics.
- Several variants get a Holm correction on the p-values only. The intervals shown for one variant are not widened, and in the several-variant table only p-values are given. `--mde` and the "was it big enough" judgement are not applied then.
- Variants are each tested against control, not against each other. If you want to rank variants, that is a different set of comparisons.
- No sequential testing. If you check results every day and stop the moment p drops under 0.05, the p-values here are wrong. Decide the sample size first and look once.
- Assumes every visitor is counted once and independently. Tests randomised by account or by city need a different calculation.
