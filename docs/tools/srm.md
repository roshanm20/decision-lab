# Sample ratio mismatch check

**For:** anyone reading the results of an A/B test, before trusting anything else it says.

**Command:** `python -m decisionlab srm --arm NAME WEIGHT COUNT --arm NAME WEIGHT COUNT ...`

## The problem it solves

A test set up as a 50/50 split that actually lands users 52/48 usually is not chance. It means assignment itself is broken: a redirect that fails more often for one variant, a bot filter that catches one variant's tracking pixel more than the other's, a feature flag that changed mid-test, logging that drops events from one arm more than the other. Whatever caused it added or removed users non-randomly, and that breaks the one assumption every other number in the test depends on.

This is called a sample ratio mismatch, or SRM. Statsig's writeup on it and the [Microsoft Research paper on diagnosing SRM](https://www.microsoft.com/en-us/research/articles/diagnosing-sample-ratio-mismatch-in-a-b-testing/) both make the same point: a clean-looking conversion lift from a test with an SRM is not evidence of anything, because the two groups were never actually comparable. This tool runs that check: expected split in, observed counts in, a chi-square test and a plain verdict out.

## Run it

```bash
python -m decisionlab srm --arm control 1 4820 --arm variant 1 5180
```

Weights only need to be in proportion to each other. `1 1` means 50/50. `2 1` means a 2:1 split, for example a treatment arm and a smaller holdout. `--arm` can be repeated for three or more arms.

```bash
python -m decisionlab srm --arm control 1 6667 --arm treatment 1 6650 --arm holdout 1 3350 --alpha 0.0005
```

`--alpha` sets the p-value threshold for flagging a mismatch. It defaults to 0.01, not the usual 0.05, because this check runs on every experiment and a 1-in-20 false alarm rate would mean flagging good experiments constantly.

## Example, real output

A test configured 50/50 that landed 4,820 to 5,180:

```
$ python -m decisionlab srm --arm control 1 4820 --arm variant 1 5180
Arm      Expected split  Expected count  Observed count  Observed split
-------  --------------  --------------  --------------  --------------
control           50.0%         5,000.0           4,820           48.2%
variant           50.0%         5,000.0           5,180           51.8%

Chi-square = 12.960, df = 1, p = 0.0003

Sample ratio mismatch (p = 0.0003, below the 0.01 threshold). 'control' got 4,820 visitors against 5,000 expected. This gap is too large to be chance. Something is skewing who lands in each arm: a redirect or load-time difference between variants, a bot or crawler filter that catches one variant's tag more than the other's, a feature flag that changed mid-test, or logging that drops events from one arm more than the other. Find and fix the cause before reading any result from this test. Every number downstream of a broken split is suspect.
```

The same split configured, landing close to 50/50 instead:

```
$ python -m decisionlab srm --arm control 1 4980 --arm variant 1 5020
Arm      Expected split  Expected count  Observed count  Observed split
-------  --------------  --------------  --------------  --------------
control           50.0%         5,000.0           4,980           49.8%
variant           50.0%         5,000.0           5,020           50.2%

Chi-square = 0.160, df = 1, p = 0.6892

No sample ratio mismatch (p = 0.6892, at or above the 0.01 threshold). The observed split is consistent with the assignment you configured. This does not prove assignment is bug free, only that the counts do not show the kind of skew that would flag it.
```

180 users out of 10,000 either way is a small-looking gap, but it is enough to fail this check. That is the point: SRM is not about how big the gap looks, it is about whether it is bigger than the randomness of assignment alone would produce.

## How to read it

- **Chi-square, df, p-value**: the goodness-of-fit test comparing observed counts to the counts your weights imply.
- **p below alpha**: flagged as a mismatch. Stop and find the cause before reading conversion numbers from this test.
- **p at or above alpha**: no mismatch detected. This does not prove the assignment code has no bugs, only that the counts collected so far do not show the kind of skew this test can catch.
- **The "expected count below 5" warning**: the chi-square approximation gets unreliable with very few visitors. Wait for more traffic before trusting the check either way.

## Method

Standard chi-square goodness-of-fit test. Expected count in each arm is the total observed visitors split according to the weights given. The statistic is `sum((observed - expected)^2 / expected)` across arms, with degrees of freedom one less than the number of arms.

The p-value threshold defaults to 0.01, following the convention Statsig documents for its own SRM checker. The [Microsoft Research paper on the same problem](https://www.microsoft.com/en-us/research/articles/diagnosing-sample-ratio-mismatch-in-a-b-testing/) (Fabijan et al., KDD 2019) uses an even stricter 0.0005, arguing that real mismatches produce p-values far below any reasonable cutoff, so a strict threshold costs little power against genuine SRM while cutting false alarms further. Pass `--alpha 0.0005` for that stricter check.

`tests/test_srm.py` checks the chi-square p-value function against published textbook critical values (the standard chi-square distribution table), and separately checks the two-arm case against an independently written two-proportion z-test formula, not against this module's own code.

## What it does not do

- Says only whether the split is off. It does not diagnose the cause. The verdict lists the usual suspects, but finding which one applies means checking the test's own logs.
- Checked once, on the final counts. If you want to catch an SRM early, before running it out to the end of the test, you need to run this check periodically during the test, not just at the end. This tool does not do that monitoring itself, you rerun it with the day's counts.
- No time dimension. Two arms that individually match 50/50 in total can still have had a broken week in the middle if one bad day offset another. Splitting the observed counts by day and running this per day would catch that. This version takes one set of totals.
- Assumes independent visitors, same as `ab-test`. Assignment randomised by account or by shared device needs a different variance calculation than the simple chi-square here.
