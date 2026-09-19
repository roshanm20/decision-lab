# Tool changelog

Every change to an existing tool gets a line here, newest first. Format:

```
## YYYY-MM-DD  tool_name.py
What changed, and the problem it fixes. One or two lines.
```

The point of this file is to make improvement visible. A repo of forty one-off scripts is worth less than six tools that got better, but only if the getting better is legible from the outside.

## 2026-09-19  cohort_table.py
First version. Monthly cohort retention from a transactions CSV, standard library only. Blanks the months a cohort has not reached yet instead of printing them as zero retention, and the average row only uses cohorts that have reached each month.
