# Tool changelog

Tool-level history, newest first. Release-level history is in the top-level `CHANGELOG.md`. Format:

```
## YYYY-MM-DD  tool_name.py
What changed, and the problem it fixes. One or two lines.
```

The point of this file is to make improvement visible. A repo of forty one-off scripts is worth less than six tools that got better, but only if the getting better is legible from the outside.

## 2026-10-05  funnel
First version. Step conversion against the previous step with Wilson intervals, from a step-count CSV or an event log. Names the step with the lowest rate and says whether its interval overlaps the next lowest. Blank step counts are skipped and reported, rising counts are refused, and users who skip a step in an event log are counted and flagged. Standard library only.

## 2026-10-02  cohort
`--min-size N` marks cohorts under N customers with `*`, leaves them out of the average row, and says how many customers were left out. A 40-customer cohort used to get a row that looked as solid as one of 4,000. Default 0 keeps the old output. The CSV gets a `small` column when it is used.

## 2026-10-01  nps
First version. NPS from raw 0 to 10 replies with a confidence interval, and a z-test between two segments, so a few points of movement is not reported as a trend when it is noise. Warns under 30 replies and when every reply sits in one group. Plain Wald interval, and the docs say it is not the adjusted-Wald method. Standard library only.

## 2026-09-30  srm
`--daily FILE.csv` checks the running total after every day and each day alone, and names the first day the split goes wrong, so a broken split is caught mid-test. `--weight` sets unequal splits. Bad rows are reported by line number. Repeated daily looks raise the false alarm rate, which the docs say plainly. Optimizely uses a sequential test for this and this tool does not.

## 2026-09-29  unit-economics
First version. CAC, contribution, LTV and payback per customer from a JSON model with low and high values. Payback allows for churn instead of dividing CAC by contribution, LTV can be capped at a horizon, and a sensitivity table ranks inputs by swing in LTV / CAC. An "everything goes wrong at once" row covers the combined case that one-at-a-time testing misses. Standard library only.

## 2026-09-24  rice
`--shade` and `--drop` flags replace the fixed 30 percent shade and two-place threshold, both validated (shade between 0 and 1, drop at least 1). `--check-reach` runs the same fragility test against reach, since reach is often as much a guess as confidence. New column and message when it is used.

## 2026-09-23  srm
First version. Chi-square sample ratio mismatch check for experiments: expected split and observed counts in, a plain verdict on whether the assignment itself looks broken out. Defaults to a 0.01 p-value threshold rather than 0.05, since this check runs on every experiment. Standard library only, including the chi-square p-value itself.

## 2026-09-23  cohort
Moved into the package as `python -m decisionlab cohort`, logic unchanged. The old `tools/cohort_table.py` path still works. The demo now writes its CSV to a temp folder, because running it from the repo root once left a stray file that got committed. Messy-input handling is now a permanent test.

## 2026-09-19  cohort_table.py
First version. Monthly cohort retention from a transactions CSV, standard library only. Blanks the months a cohort has not reached yet instead of printing them as zero retention, and the average row only uses cohorts that have reached each month.
