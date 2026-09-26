# Roadmap

This file decides what the daily run builds. The run takes the first ready item under the day's section, builds it, ticks it, and commits. The Sunday run grooms this file: it adds items from the discovery log, splits anything too big for one day, and reorders.

Item format, which `scripts/pick_track.py` parses, so keep it exact:

```
- [ ] ID | new or extend or note or fix | short title | S or M
  - why: who asks for this and what goes wrong without it
  - done when: the test for finished
```

`[ ]` is ready, `[x]` is done, `[~]` is blocked or waiting on Roshan. S is a few hours of careful work, M is a full day. Anything bigger gets split before it is picked.

The order inside a section is the priority. Extending a tool that people already use usually beats starting a new one, so extend items sit near the top.

## bi

- [ ] BI-01 | extend | cohort: flag and leave out small cohorts | S
  - why: a 40-customer cohort gets its own row that looks as solid as a cohort of 4,000, even though its percentages are mostly noise. Raised on the first Sunday check.
  - done when: `--min-size N` marks small cohorts, leaves them out of the average row, says how many were left out, and has tests.
- [ ] BI-02 | new | funnel: step conversion, drop-off and the biggest leak | M
  - why: funnel charts show percentages without saying which drop is actually unusual or how sure we are about it.
  - done when: takes a step-count CSV or an event log, handles missing steps, gives step conversion with confidence intervals, names the biggest leak, has tests and a docs page.
- [ ] BI-03 | new | metric-sql: metric definitions in YAML turned into SQL | M
  - why: the same metric gets computed three different ways by three analysts. A definition file that generates the SQL settles it.
  - done when: a YAML spec (name, table, numerator, denominator, filters, grain) produces SQL for Postgres and BigQuery, a lint step flags missing edge cases like null handling and time zone, tests pass.
- [ ] BI-04 | new | profile: the five checks before trusting a table | M
  - why: analysts build dashboards on tables with duplicate keys, silent nulls and date gaps, and find out after the numbers are presented.
  - done when: prints row count, null rate by column, duplicate keys, date gaps, and extreme values for a CSV, with a clear pass or warn per check, and tests.
- [ ] BI-05 | new | anomaly: flag unusual days in a KPI series | M
  - why: dashboards show every wiggle, and teams either chase noise or miss the real break.
  - done when: robust z-score (median and MAD) with day-of-week adjustment on a date,value CSV, flags and explains each anomaly, tests on a synthetic series with planted anomalies.
- [ ] BI-06 | new | stickiness: DAU, WAU, MAU and DAU over MAU counted correctly | S
  - why: the 21 September note showed that summing daily uniques overstates reach. This makes the correct count a one-line command.
  - done when: takes an events CSV (user, date), counts distinct users per window correctly, reports the ratios, has tests, links to the note.
- [ ] BI-07 | new | baseline-forecast: the forecast any model has to beat | M
  - why: teams adopt forecasting models without checking they beat a seasonal naive guess.
  - done when: naive, seasonal naive and moving average forecasts with holdout MAPE on a date,value CSV, picks the best baseline, tests.
- [ ] BI-08 | extend | cohort: weekly cohorts | S
  - why: products used on a short cycle need weekly, not monthly, retention.
  - done when: `--grain week` works with ISO weeks and the blanking logic still holds, tests.
- [ ] BI-09 | new | rfm: RFM segments from transactions, with a seasonality warning | M
  - why: RFM is standard for CRM teams but misleads when buying is seasonal.
  - done when: quintile scores, named segments, a warning when purchase gaps are seasonal, tests and docs.
- [ ] BI-10 | new | report-table: turn a CSV into a clean summary table for a report | S
  - why: analysts spend time formatting numbers for decks and docs by hand.
  - done when: group-by with sum, mean or count, sensible number formatting, markdown or HTML output, tests.

## consulting

- [ ] CO-01 | new | unit-economics: CAC, contribution margin, payback and LTV with sensitivity | M
  - why: every consulting case and every founder deck needs this, and most versions hide the assumption doing the work.
  - done when: JSON inputs, prints the unit economics and a sensitivity table ranked by swing, like market-size, tests and docs.
- [ ] CO-02 | extend | market-size: add segments that sum, and label SAM and SOM | M
  - why: real markets are several segments added together, and the tool only multiplies.
  - done when: a model can hold segments whose totals add, TAM, SAM and SOM are labelled in the output, the example still reconciles, tests.
- [ ] CO-03 | new | case-math: mental maths drills for case interviews | S
  - why: case interviews for consulting and IIM panels test fast estimation, and practice material is scattered.
  - done when: generates timed drills (percentages, growth rates, break-even, market sizing steps) with answers and a seed for repeatable sets, tests.
- [ ] CO-04 | new | breakeven: break-even volume with price and cost sensitivity | S
  - why: "how many do we need to sell" is the first question in half of all cases.
  - done when: fixed cost, price and variable cost in, break-even volume and a price by cost grid out, tests.
- [ ] CO-05 | new | npv: NPV, IRR and payback for a cash flow with scenarios | S
  - why: investment cases need these three numbers side by side, with the discount rate sensitivity shown.
  - done when: CSV of period cash flows, NPV at several rates, IRR by bisection, payback period, tests against known answers.
- [ ] CO-06 | new | survey-crosstab: cross-tabs with significance flags | M
  - why: consulting surveys get cut ten ways and every difference gets reported as a finding.
  - done when: cross-tab of two columns with counts and percentages, chi-square test, cells flagged when they differ reliably, a small-base warning, tests.
- [ ] CO-07 | new | issue-tree: check an issue tree for overlap and gaps | M
  - why: MECE is easy to claim and hard to check.
  - done when: reads an indented text tree, flags branches that share key words, flags a level with a single child, prints markdown and a Mermaid diagram, tests.
- [ ] CO-08 | new | waterfall: a bridge chart as SVG | M
  - why: every EBITDA or revenue bridge in a deck is hand drawn in PowerPoint.
  - done when: CSV of start, steps and end produces a clean SVG waterfall with labels, standard library only, tests on the geometry.
- [ ] CO-09 | new | benchmark: peer benchmarking with quartiles | S
  - why: "how do we compare" slides need quartiles and percentile rank, not a bar per company.
  - done when: CSV of peers and one or more metrics, quartiles and the focal company's percentile rank per metric, tests.
- [ ] CO-10 | new | two-by-two: a prioritisation matrix as SVG | M
  - why: effort-impact and similar 2x2s are the most common consulting chart.
  - done when: CSV with name, x and y produces an SVG with quadrant labels and no overlapping text for up to 20 points, tests.

## marketing

- [x] MK-01 | new | srm: sample ratio mismatch check for experiments | S
  - why: a 50/50 test that lands 52/48 usually means the split is broken, and every result from it is suspect.
  - done when: expected split and observed counts in, chi-square SRM check out, with a plain verdict, tests.
- [ ] MK-02 | extend | ab-test: several variants with a Holm correction | S
  - why: testing four variants at p under 0.05 each gives a false winner far too often.
  - done when: `analyze` accepts several variants, applies Holm, and says which survive, tests.
- [ ] MK-03 | new | attribution: first touch, last touch, linear and time decay compared | M
  - why: channel budgets move on attribution choices nobody looked at side by side.
  - done when: a touchpoint CSV (user, time, channel, converted) gives credit per channel under four models and shows where the models disagree most, tests.
- [ ] MK-04 | extend | ab-test: revenue per visitor with a Welch test | M
  - why: many tests care about revenue, not conversion, and revenue is heavily skewed.
  - done when: per-visitor values in, Welch t-test and a bootstrap interval out, with a skew warning, tests.
- [ ] MK-05 | new | utm-audit: find the mess in UTM tags | S
  - why: inconsistent UTM tags split one campaign into five rows in every report.
  - done when: a list of URLs in, flags for inconsistent casing, missing medium or source, near duplicate campaign names, and a cleaned mapping out, tests.
- [ ] MK-06 | new | ltv-cac: LTV to CAC and payback by channel | S
  - why: blended CAC hides channels that lose money.
  - done when: channel CSV in, LTV, CAC, ratio and payback months per channel out, with the 3 to 1 benchmark labelled as a rule of thumb, tests.
- [ ] MK-07 | new | price-sensitivity: Van Westendorp from survey answers | M
  - why: early stage pricing is usually a guess when a cheap survey method exists.
  - done when: the four price questions in, the acceptable price range and optimal point out, tests on a known worked example.
- [ ] MK-08 | new | holdout-roi: incremental ROI against a holdout group | S
  - why: campaign ROI without a holdout counts sales that would have happened anyway.
  - done when: treated and holdout results in, incremental conversions, incremental ROI and an interval out, tests.
- [ ] MK-09 | new | keyword-groups: group search keywords by shared terms | M
  - why: SEO plans start from thousands of keywords that need grouping into pages.
  - done when: keyword CSV with volume in, groups by shared stemmed terms out, with total volume per group, standard library only, tests.
- [ ] MK-10 | new | email-health: list health from email campaign results | S
  - why: open rates stopped being reliable, and teams miss rising unsubscribe and bounce rates.
  - done when: campaign CSV in, click, unsubscribe and bounce trends with flags out, tests.

## product

- [x] PM-01 | extend | rice: make the fragility shade and threshold flags, and test reach too | S
  - why: the 30 percent shade and two-place threshold are fixed, and reach guesses are as shaky as confidence.
  - done when: `--shade` and `--drop` flags, an optional reach check, tests.
- [ ] PM-02 | new | nps: NPS with a confidence interval and segment comparison | S
  - why: NPS moves of a few points get celebrated when the interval is plus or minus ten.
  - done when: scores CSV in, NPS, its interval and a comparison between two segments out, tests.
- [ ] PM-03 | new | kano: Kano model classifier for feature surveys | M
  - why: teams build features customers expect as if they were delighters.
  - done when: paired functional and dysfunctional answers in, Kano category per feature with counts out, tests on a worked example.
- [ ] PM-04 | new | metric-tree: a north star metric tree from YAML | M
  - why: north star metrics get picked without checking that the input metrics actually add up to them.
  - done when: YAML tree in, markdown and Mermaid out, with checks for inputs that cannot move the parent, tests.
- [ ] PM-05 | new | okr-lint: catch key results that are really tasks | S
  - why: "launch feature X" gets written as a key result all the time.
  - done when: an OKR file in, flags for key results with no number, no baseline, or task verbs, tests.
- [ ] PM-06 | new | sus: System Usability Scale scoring | S
  - why: SUS is the standard usability survey and its scoring is easy to get wrong.
  - done when: ten answers per respondent in, scores, mean, interval and the usual grade bands out, tests on known answers.
- [ ] PM-07 | new | adoption: feature adoption breadth and depth | M
  - why: "30 percent of users tried it" says nothing about whether anyone kept using it.
  - done when: events CSV in, tried, repeated and habitual users per feature out, tests.
- [ ] PM-08 | new | experiment-log: what the last year of experiments actually taught | S
  - why: teams run tests but never look at their win rate or average lift across them.
  - done when: an experiment log CSV in, win rate, median lift, and the list of untested areas out, tests.
- [ ] PM-09 | new | capacity: MoSCoW against real team capacity | S
  - why: must-haves routinely add up to more than the team can build in the period.
  - done when: backlog with priority and estimates plus team capacity in, what fits and what does not out, tests.
- [ ] PM-10 | new | prd: a PRD skeleton from a short problem statement | S
  - why: specs skip non-goals and success metrics more than anything else.
  - done when: a short YAML brief in, a markdown PRD with goals, non-goals, metrics and open questions out, and a check that non-goals and metrics are not empty, tests.

## notes

Saturday is a writing day. The best notes use one of the tools above on real, sourced public data, because that shows the tool and the thinking at the same time.

- [x] NT-01 | note | Size a real Indian market with market-size, every number sourced | M
  - why: the tool's only example is invented. A sourced one shows it works on a real question.
  - done when: a note in `content/notes` with the JSON model committed, every input cited with a date checked, and a stated position.
- [ ] NT-02 | note | Re-check a published A/B test case study with ab-test | M
  - why: many published test wins do not survive their own numbers.
  - done when: a public case with visitor and conversion counts, re-analysed, with a clear verdict on whether its conclusion holds.
- [ ] NT-03 | note | Teardown of an AI research or competitive intelligence product | M
  - why: consulting and strategy teams buy these tools, and the category is crowded enough that pricing and moat questions are sharp. Work only from public sources.
  - done when: a teardown in `content/teardowns` meeting STANDARDS.md, with a dated pricing table.
- [ ] NT-04 | note | Metric definition: activation rate for a B2B analytics product | S
  - why: the definition decides the roadmap, and teams rarely write it down.
  - done when: a note in `bi/metric-library` with the formula, edge cases, how it gets gamed, and SQL.
- [ ] NT-05 | note | Housing finance in India, where an NBFC earns against a bank | M
  - why: a sector note on a sector with public filings to work from.
  - done when: a sector note in `content/sector-notes` with at least four primary sources.
- [ ] NT-06 | note | Pricing a B2B AI tool when the buyer has no budget line for it | M
  - why: a common and unsolved question for AI products sold to services firms.
  - done when: a case note in `content/cases` with options priced in numbers, a call, and what would change it.
- [ ] NT-07 | note | One case worked end to end with three of the tools | M
  - why: shows the tools as a workflow, the way a consultant would actually use them.
  - done when: a note that runs at least three tools on one question, with commands and real output.

## needs-roshan

The daily run never picks these. They need a click or a note from Roshan.

- [~] NR-01 | fix | Turn on GitHub Pages so the docs become a live site | S
  - why: a live site with working tool pages is the strongest thing a recruiter can open.
  - done when: Settings, Pages, Source set to GitHub Actions, and a repo variable PAGES_ENABLED set to true. The site workflow is ready. See docs/setup.md.
- [~] NR-02 | fix | Let the automation keep the profile README current | S
  - why: the profile page is the first thing anyone sees, and it still says astrophysics only.
  - done when: a fine-grained PROFILE_TOKEN secret exists and the profile README has the two marker lines. The Monday workflow is ready. See docs/setup.md.
- [~] NR-03 | note | Journal notes on real decisions in Roshan's own companies | S
  - why: decision records are the pieces no other applicant can write. The automation cannot write them without notes.
  - done when: at least one note in journal/inbox each week.
