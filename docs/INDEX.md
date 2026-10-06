# Index

8 tools, 195 tests, 5 notes.

## Tools

**For consultants**

- [`market-size`](../docs/tools/market-size.md) Top-down and bottom-up sizing that checks the two agree, ranks the assumptions that matter, and gives a P10 to P90 range.
- [`unit-economics`](../docs/tools/unit-economics.md) CAC, contribution, LTV and payback per customer, with payback that allows for churn and a ranking of which input moves LTV / CAC most.

**For BI and analytics**

- [`cohort`](../docs/tools/cohort.md) Monthly cohort retention from a transactions CSV that leaves unreached months blank instead of showing them as zero.
- [`funnel`](../docs/tools/funnel.md) Step-by-step conversion with confidence intervals from step counts or an event log, naming the step that leaks most.

**For marketers**

- [`ab-test`](../docs/tools/ab-test.md) Sample size before a test, significance after it, and a plain answer on whether a flat result was just underpowered.
- [`srm`](../docs/tools/srm.md) Checks whether an experiment's traffic actually landed in the split you configured, before you trust anything else it reports.

**For product managers**

- [`rice`](../docs/tools/rice.md) Ranks a backlog by RICE and flags which positions depend on a confidence guess being right.
- [`nps`](../docs/tools/nps.md) Scores NPS from raw 0 to 10 replies, puts an interval on it and tests whether two segments really differ.

## Notes

### Applied notes, the tools used on real data

- **[Does Unbounce's 336 percent test win survive its own numbers](../content/notes/2026-10-03-unbounce-336-percent-test.md)** (2026-10-03)  
  The published 336 percent lift rests on one conversion in the control arm, and re-run with this repo's ab-test tool it is not significant at the 95 percent level, so the page's conclusion is not proven by its own data.
- **[Sizing India's electric two-wheeler market and testing the sizing tool](../content/notes/2026-09-26-india-electric-two-wheeler-market.md)** (2026-09-26)  
  India's electric two-wheeler market was worth roughly 13,700 to 17,800 crore rupees at ex-showroom prices in FY2024-25, but the bigger finding is that this tool's top-down versus bottom-up check only catches a real error when the two chains do not share an input, and here they shared both the units and the price.

### BI analyses

- **[Why summing daily unique users overstates monthly reach](../bi/analyses/2026-09-21-unique-user-double-counting.md)** (2026-09-21)  
  Summing daily or per-channel unique-user counts overstates true reach, and the overstatement gets worse as a product gets stickier, so period-level reach needs a direct distinct count, not a rollup of daily numbers.

### AI product teardowns

- **[Zaigo's AI due diligence for private equity](../content/teardowns/2026-09-22-zaigo-ai-due-diligence.md)** (2026-09-22)  
  Zaigo's technical AI due diligence for PE buyers is a real wedge with a genuine information asymmetry behind it, but it has no defensible moat and its own post-deal upsell puts it on the wrong side of an independence question that PE firms already worry about.

### Tool write-ups

- **[Cohort retention table from a transactions CSV](../tools/2026-09-19-cohort-retention-table-generator.md)** (2026-09-19)  
  A standard library script that turns a transactions file into a monthly cohort table, and blanks out the months a cohort has not reached yet instead of printing them as zero retention.

## Weekly logs

- [Week three log, two new tools, two extended, tests from 98 to 161](../weekly/2026-10-04-week-log.md) (2026-10-04)
- [Week two log, srm shipped, rice extended, tests from zero to 98](../weekly/2026-09-27-week-log.md) (2026-09-27)
- [Week one log, repo setup plus one tool](../weekly/2026-09-20-week-review.md) (2026-09-20)
