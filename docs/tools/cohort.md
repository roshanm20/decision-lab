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
python -m decisionlab cohort --demo          # synthetic data, written to a temp folder
```

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

The full write-up, including why the average row is weighted the way it is, is in [the original note](../../tools/2026-09-19-cohort-retention-table-generator.md).

## What it does not do

- Monthly cohorts only. Weekly cohorts matter for products used on a short cycle.
- Retention means "made any transaction that month". Subscription businesses need active-subscription retention instead.
- No guard against small cohorts. A cohort of 40 customers gets its own row that looks as solid as one of 4,000, even though its percentages are mostly noise. Queued in `ROADMAP.md`.
- Customers are matched on exact id, so one person under two ids counts as two customers.
