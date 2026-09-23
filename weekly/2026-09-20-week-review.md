---
title: Week one log, repo setup plus one tool
date: 2026-09-20
track: weekly-log
summary: Setup week. One tool shipped. The Sunday check raised five questions about it, three are now fixed in the repo and one is queued as work.
sources: 0
---

This is a log of what happened in the week, not an argument. It is kept so anyone reading the repo can see how the work was checked, and what changed because of the checks.

## What shipped

The repo was set up on 19 September, so most commits this week were scaffolding: the standards file, the daily rotation, the skill, the workflows, the backlog and the journal inbox. One actual piece went out.

- **tool**: [Cohort retention table from a transactions CSV](../tools/2026-09-19-cohort-retention-table-generator.md). A standard library script that turns a transactions file into a monthly cohort table, and blanks the months a cohort has not reached yet instead of printing them as zero retention.

## Questions raised on the Sunday check, and what happened to each

1. **Is the claim about the weighted average row backed by a number?** It was not, and the demo did not support it. The note said big cohorts retain worse, which would drag the size-weighted average row down. In the demo, month one's size-weighted average is about 31 percent and the plain average of the twelve cohorts is 31.25 percent, so cohort size makes almost no difference there. The note now says this and explains when the concern would apply. Fixed on 23 September.

2. **Was the "reports data problems" behaviour tested on messy data?** It was tested by hand on 19 September against a file with a blank date, an unreadable date and a revenue value with a comma in it, but that test was not saved anywhere. It is now a permanent test in `tests/test_cohort.py`. Fixed on 23 September.

3. **Is "the pattern you usually get when acquisition spend is scaled up" backed by anything?** No. It described the shape chosen for the synthetic demo as if it were a real-world pattern. Reworded to say plainly that it is a choice made for the demo. Fixed on 23 September. An outside review of the repo on 22 September flagged it too.

4. **Would a 40-customer cohort get read as meaningful?** Probably, because the only guard is a visible size column. Queued in `ROADMAP.md` as a small-cohort flag for the tool.

5. **Is one tool enough to judge the pace of the rotation?** No. Judge it after two full weeks of the rotation running.
