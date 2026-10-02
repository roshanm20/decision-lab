# Cohort retention table

**For:** BI analysts, growth teams, and founders reading their own retention.

**Command:** `python -m decisionlab cohort TRANSACTIONS.csv`

## The problem it solves

Most cohort tables print months that have not happened yet as zero. A cohort that signed up two months ago cannot have a month six figure, but the table shows 0%, and the recent cohorts look like they collapsed. Teams chase retention problems that do not exist this way, or miss ones that do.

This tool leaves those months blank. The average row only uses cohorts that have reached each month, so its columns can be compared fairly.

## Run it

```bash
python -m decisionlab cohort transactions.csv
python -m decisionlab cohort transactions.csv --metric revenue --periods 12
python -m decisionlab cohort transactions.csv --min-size 100
python -m decisionlab cohort --demo          # synthetic data, written to a temp folder
```

`--min-size N` marks cohorts with fewer than N customers with a `*` after the size, leaves them out of the average row, and says how many were left out. The cohort rows stay in the table so nothing is hidden. With `--out`, the CSV gets a `small` column. The default is 0, which changes nothing. The right N depends on how big a difference you need to see. One source puts a floor at about 30 customers for spotting a gap of 3 to 5 points (see the source in `discovery/2026-10.md`). The 100 used in the examples is only an example value. The note under the table says how many points one customer moves the smallest left-out cohort.

The CSV needs `customer_id` and `order_date`, and optionally `revenue`. Other column names can be passed with `--id-col`, `--date-col` and `--revenue-col`.

## Example, real output

The demo data is synthetic, and each cohort retains slightly worse than the one before. That shape was picked so the blank cells are easy to see. It is not a claim about real businesses.

The first line of output, the path of the temp file, is left out below.

```
$ python -m decisionlab cohort --demo --periods 6
1,944 transactions, 1,340 customers, 12 monthly cohorts, data runs to 2026-02

Metric: customers. Showing percent of the cohort's own first month. Size column is always customers.

 Cohort   Size       M0       M1       M2       M3       M4       M5       M6
-------  -----  -------  -------  -------  -------  -------  -------  -------
2025-01    110     100%      40%      16%       5%       5%       2%       2%
2025-02    106     100%      45%      22%       8%       2%       0%       0%
2025-03    131     100%      41%      13%       4%       3%       0%       0%
2025-04     98     100%      40%      11%       6%       4%       2%       0%
2025-05    122     100%      29%       9%       2%       1%       0%       0%
2025-06     90     100%      27%       6%       3%       1%       0%       0%
2025-07    109     100%      27%       6%       1%       1%       0%       0%
2025-08    113     100%      27%       7%       3%       1%       0%       0%
2025-09    140     100%      22%       6%       1%       0%       0%         
2025-10    102     100%      26%       9%       1%       1%                  
2025-11     97     100%      26%       3%       0%                           
2025-12    122     100%      25%       3%                                    

Average across cohorts, weighted by cohort size:
    All   1340     100%      31%       9%       3%       2%       0%       0%

Blank cells are months that have not happened yet for that cohort, not zero retention. The average row only uses cohorts that have reached the month in question, so it is comparable across columns.
```

Same data with `--min-size 100`. Three cohorts fall under 100 customers, so the average row now uses the other nine.

```
$ python -m decisionlab cohort --demo --periods 6 --min-size 100
1,944 transactions, 1,340 customers, 12 monthly cohorts, data runs to 2026-02

Metric: customers. Showing percent of the cohort's own first month. Size column is always customers.

 Cohort   Size       M0       M1       M2       M3       M4       M5       M6
-------  -----  -------  -------  -------  -------  -------  -------  -------
2025-01    110     100%      40%      16%       5%       5%       2%       2%
2025-02    106     100%      45%      22%       8%       2%       0%       0%
2025-03    131     100%      41%      13%       4%       3%       0%       0%
2025-04    98*     100%      40%      11%       6%       4%       2%       0%
2025-05    122     100%      29%       9%       2%       1%       0%       0%
2025-06    90*     100%      27%       6%       3%       1%       0%       0%
2025-07    109     100%      27%       6%       1%       1%       0%       0%
2025-08    113     100%      27%       7%       3%       1%       0%       0%
2025-09    140     100%      22%       6%       1%       0%       0%         
2025-10    102     100%      26%       9%       1%       1%                  
2025-11    97*     100%      26%       3%       0%                           
2025-12    122     100%      25%       3%                                    

Average across cohorts, weighted by cohort size:
    All   1055     100%      31%      10%       3%       2%       0%       0%

* 3 of 12 cohorts have fewer than 100 customers and are left out of the average row (285 customers). Their own percentages are mostly noise: in the smallest, one customer moves the percentage by 1.1 points.

Blank cells are months that have not happened yet for that cohort, not zero retention. The average row only uses cohorts that have reached the month in question, so it is comparable across columns.
```

The full write-up, including why the average row is weighted the way it is, is in [the original note](../../tools/2026-09-19-cohort-retention-table-generator.md).

## What it does not do

- Monthly cohorts only. Weekly cohorts matter for products used on a short cycle.
- Retention means "made any transaction that month". Subscription businesses need active-subscription retention instead.
- `--min-size` is a plain cut-off you choose. The tool does not work out a safe size for you, and it does not draw confidence intervals on each cell.
- Customers are matched on exact id, so one person under two ids counts as two customers.
