# Tool changelog

Tool-level history, newest first. Release-level history is in the top-level `CHANGELOG.md`. Format:

```
## YYYY-MM-DD  tool_name.py
What changed, and the problem it fixes. One or two lines.
```

The point of this file is to make improvement visible. A repo of forty one-off scripts is worth less than six tools that got better, but only if the getting better is legible from the outside.

## 2026-09-23  cohort
Moved into the package as `python -m decisionlab cohort`, logic unchanged. The old `tools/cohort_table.py` path still works. The demo now writes its CSV to a temp folder, because running it from the repo root once left a stray file that got committed. Messy-input handling is now a permanent test.

## 2026-09-19  cohort_table.py
First version. Monthly cohort retention from a transactions CSV, standard library only. Blanks the months a cohort has not reached yet instead of printing them as zero retention, and the average row only uses cohorts that have reached each month.
