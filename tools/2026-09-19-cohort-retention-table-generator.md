---
title: Cohort retention table from a transactions CSV
date: 2026-09-19
track: tool
summary: A standard library script that turns a transactions file into a monthly cohort table, and blanks out the months a cohort has not reached yet instead of printing them as zero retention.
sources: 0
---

Most cohort tables I have been shown are wrong in the same way. The recent cohorts have a run of zeros in their later columns, and someone reads that as retention collapsing. It is not collapsing. Those months have not happened yet. A cohort that signed up two months ago cannot have a month six number.

That single mistake is enough to send a team chasing a retention problem that does not exist, or to hide one that does. So this script blanks those cells instead of filling them with zero, and it computes the average row only over the cohorts that have actually reached each month.

`tools/cohort_table.py`. Standard library only, so it runs on any Python 3.9 or later with nothing installed.

## Running it

```bash
python tools/cohort_table.py transactions.csv
python tools/cohort_table.py transactions.csv --metric revenue --periods 12
python tools/cohort_table.py transactions.csv --absolute --out cohorts.csv
python tools/cohort_table.py --demo
```

It expects `customer_id`, `order_date`, and optionally `revenue`. Use `--id-col`, `--date-col` and `--revenue-col` if your columns are named differently. Dates are truncated to the first ten characters, so `2025-04-17T09:31:00Z` reads the same as `2025-04-17`.

## What the output looks like

This is the real output of `--demo`, which generates synthetic data where each cohort retains slightly worse than the one before it. That is the pattern you usually get when acquisition spend is being scaled up.

```
1,944 transactions, 1,340 customers, 12 monthly cohorts, data runs to 2026-02

Metric: customers. Showing percent of the cohort's own first month. Size column is always customers.

 Cohort   Size       M0       M1       M2       M3       M4       M5       M6       M7       M8
-------  -----  -------  -------  -------  -------  -------  -------  -------  -------  -------
2025-01    110     100%      40%      16%       5%       5%       2%       2%       1%       0%
2025-02    106     100%      45%      22%       8%       2%       0%       0%       0%       0%
2025-03    131     100%      41%      13%       4%       3%       0%       0%       0%       0%
2025-04     98     100%      40%      11%       6%       4%       2%       0%       0%       0%
2025-05    122     100%      29%       9%       2%       1%       0%       0%       0%       0%
2025-06     90     100%      27%       6%       3%       1%       0%       0%       0%       0%
2025-07    109     100%      27%       6%       1%       1%       0%       0%       0%
2025-08    113     100%      27%       7%       3%       1%       0%       0%
2025-09    140     100%      22%       6%       1%       0%       0%
2025-10    102     100%      26%       9%       1%       1%
2025-11     97     100%      26%       3%       0%
2025-12    122     100%      25%       3%

Average across cohorts, weighted by cohort size:
    All   1340     100%      31%       9%       3%       2%       0%       0%       0%       0%
```

Look at the staircase on the right. That is the honest shape of a cohort table. Anything that fills those cells with zeroes is lying to you.

## The three decisions inside it

**Blank, not zero.** The script finds the last month present in the data and blanks any cohort and month combination that falls after it. Four lines of code, and it removes the most common way these tables get misread.

**The average row is weighted and it excludes the blanks.** For month three it adds up the month three activity of only those cohorts that have reached month three, and divides by the first month size of those same cohorts. If you average the percentages across all cohorts instead, the recent cohorts drag later columns toward zero and the curve looks worse than it is. If you weight by size but include the blanks, the same thing happens more quietly.

**It reports data problems instead of swallowing them.** Blank customer ids, unparseable dates, revenue that is not a number. It counts them, prints the first five with line numbers, and carries on. A tool that silently drops eight percent of your rows is worse than one that crashes.

## What it does not do

- Monthly buckets only. Weekly cohorts matter for a product with a short usage cycle, and this cannot do them.
- Retention is defined as "made any transaction that month". For a subscription business the right definition is active subscription, which is a different query and a different tool.
- No confidence intervals. A cohort of 40 customers and a cohort of 4,000 print the same way, and the small one is mostly noise. The size column is there so you notice, but the script does not stop you.
- Customers are matched on exact id. If the same person appears under two ids, they will read as two cohorts, and the retention number will be too low.

## What would change my mind

The design choice I am least sure about is the weighted average. Weighting by cohort size means the big cohorts decide the shape, and big cohorts are usually the ones from heavy acquisition months, which retain worse. So the average row may sit below the typical cohort.

If someone showed me that they were making decisions off the average row rather than reading the cohorts individually, I would remove the average row instead of trying to improve it. A single number on a cohort table invites exactly the shortcut the table exists to prevent.

The other thing I would change my mind on is the blanking. If a business genuinely has cohorts that go to zero and stay there, the blanks hide that the data ends rather than the customers leaving. A footer line saying the data window would fix it, and I have not added one yet.
