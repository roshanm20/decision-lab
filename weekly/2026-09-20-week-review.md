---
title: Week one review, repo setup plus one tool
date: 2026-09-20
track: weekly-review
summary: Not yet written. This is a draft, the read is mine to add.
sources: 0
---

## This week's pieces

The repo was set up this week (2026-09-19), so most commits are scaffolding rather than content: the standards file, the daily rotation script, the skill, the workflows, the backlog, the journal inbox. One actual piece went out under the rotation.

- **tool**: [Cohort retention table from a transactions CSV](../tools/2026-09-19-cohort-retention-table-generator.md). A standard library script that turns a transactions file into a monthly cohort table, and blanks the months a cohort has not reached yet instead of printing them as zero retention.

## Questions for me

- The piece says weighting the average row by cohort size pulls it below the typical cohort, because big cohorts usually come from heavy acquisition months that retain worse. Did you check that against the actual `--demo` output, or is that reasoning without a number behind it?
- "It reports data problems instead of swallowing them" is stated as a design decision. Was this run against a CSV with actual blank ids, bad dates or non-numeric revenue, or only against the clean synthetic demo data?
- The demo data is generated so each cohort retains slightly worse than the one before it, described as "the pattern you usually get when acquisition spend is being scaled up." Is that a claim you can back with a real dataset, or is it just the shape you picked for the demo to make the blanking problem visible?
- The piece lists "no confidence intervals" as an open limitation and says the size column is there so you notice small cohorts. Would you actually catch a 40-customer cohort being read as meaningful, or does that limitation need a harder guard than a visible column?
- This is the only content piece from a week that was mostly infrastructure. Is one tool enough to judge whether the daily rotation is producing pieces that meet STANDARDS.md, or should next week's review wait for a full week of the rotation actually running before drawing conclusions on pace?

## My read

_Not yet written._
