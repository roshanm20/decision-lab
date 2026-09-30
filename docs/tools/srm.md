# Sample ratio mismatch check

**For:** anyone reading the results of an A/B test, before trusting anything else it says.

**Command:** `python -m decisionlab srm --arm NAME WEIGHT COUNT --arm NAME WEIGHT COUNT ...` or `python -m decisionlab srm --daily FILE.csv`

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

## Check it day by day

A split that breaks on day 6 of a two week test is best caught on day 6, not day 14. Optimizely's [support page on its automatic SRM detection](https://support.optimizely.com/hc/en-us/articles/13409080412173-Optimizely-s-automatic-sample-ratio-mismatch-detection) says it checks daily and not only at the end (page updated 2026-03-06, checked 2026-09-30). Give the tool a CSV with the columns `day,arm,count`, one row per arm per day:

```bash
python -m decisionlab srm --daily examples/srm_daily.csv
```

`examples/srm_daily.csv` is illustrative, made up for this page. Lines starting with `#` are comments. Use ISO dates (`2026-03-09`), because days are sorted as text. For a split that is not equal, add `--weight NAME WEIGHT` for each arm, for example `--weight treatment 2 --weight holdout 1`.

```
$ python -m decisionlab srm --daily examples/srm_daily.csv
Arms, in split order: control / variant
Day         Visitors  Total so far  Split so far   p so far  p that day  Flag
----------  --------  ------------  -------------  --------  ----------  --------
2026-03-01     2,010         2,010  50.3% / 49.7%    0.7548      0.7548
2026-03-02     1,997         4,007  49.9% / 50.1%    0.8869      0.6068
2026-03-03     1,996         6,003  50.0% / 50.0%    0.9485      0.7540
2026-03-04     2,003         8,006  50.0% / 50.0%    0.9465      0.8059
2026-03-05     2,006        10,012  50.1% / 49.9%    0.7643      0.4215
2026-03-06     1,992        12,004  49.7% / 50.3%    0.4542      0.0121
2026-03-07     1,991        13,995  49.2% / 50.8%    0.0745      0.0038  bad day
2026-03-08     1,989        15,984  49.0% / 51.0%    0.0162      0.0370
2026-03-09     1,991        17,975  48.8% / 51.2%    0.0009      0.0016  MISMATCH
2026-03-10     1,988        19,963  48.6% / 51.4%   <0.0001      0.0136  MISMATCH

The running total first shows a sample ratio mismatch on 2026-03-09 (p below 0.01). Look at what changed in assignment, logging or filters on or just before that day. Do not read conversion results from this test until the cause is found.
```

How to read it. "p so far" is the chi-square test on all visitors up to and including that day. "p that day" tests that day alone. `MISMATCH` means the running total is below the threshold. `bad day` means only that day alone is, which catches a bad day that the earlier good days dilute in the running total. A day with fewer than 5 expected visitors in an arm is never flagged. The first flagged day is where to start looking in the test's logs. The break here began on 2026-03-06, three days before the running total gave it away, so the flagged day is when the tool was sure, not when the fault started.

Rows that cannot be read are listed by line number under "Problems in the file" and skipped. A day with no row for an arm counts that arm as 0 and says so.

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
- The daily check repeats an ordinary chi-square test every day, so it gets many chances at a false alarm. If the looks were independent, the chance of at least one flag in k days at threshold a would be 1 - (1 - a)^k. The running totals overlap, so the real figure is lower, but this tool does not compute it. Optimizely says it uses a sequential SRM test, not a chi-square, which is built for repeated looks. This tool does not. For a long test, use `--alpha 0.001` and treat a lone flag close to the threshold as a reason to look, not proof.
- The daily file is long format, one row per day and arm, and the tool does not run itself on a live feed. You export the counts and run it.
- Assumes independent visitors, same as `ab-test`. Assignment randomised by account or by shared device needs a different variance calculation than the simple chi-square here.
