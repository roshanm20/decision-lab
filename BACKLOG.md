# Backlog

**This is the fallback, not the plan.** Monday, Tuesday, Friday and Saturday start with a web search for what actually moved that week, and build on what they find. The lists here are what the run falls back to on a day when the search turns up nothing worth building on, and they are where it files ideas it found but did not build.

So a healthy backlog grows on its own. Items appear marked `(auto)` when the Friday scan finds something worth queueing. Delete the weak ones, that is the curation.

Wednesday and Thursday still work off fixed input. Wednesday takes the next metric from the list below. Thursday takes the oldest note from `journal/inbox` and writes a decision record about my own work, falling back to the `case` list only in a week where I left no note.

Tick an item with `[x]` when it is written.

## What these topics are for

I am a physics graduate moving into product and management. The honest version of that transition is not that I have ten years of P&L experience, because I do not. It is that I can build the thing, measure it properly, and reason about whether it should exist. So the topics here lean on measurement, unit economics, and product decisions in AI, which is where the physics actually transfers, and they stay close to the markets I have built in.

Where a topic is something I have lived, it goes in the journal instead, and Thursday picks it up.

## bi-build

Monday. Real or clearly labelled synthetic data, a query or script, and a conclusion a manager could act on. Discovery picks the problem where it can, so this list is the fallback.

- [ ] Cohort retention on a public e-commerce transaction dataset, and what the curve shape says about the business
- [ ] Funnel drop-off when events are logged unreliably, and how to still get a defensible number
- [ ] Pricing elasticity from observational data, and why the naive regression is wrong
- [ ] An A/B test that came out flat, and separating underpowered from actually no effect
- [ ] Churn early warning list from usage data, with the precision and recall tradeoff written out
- [ ] Home loan approval funnel analysis, where applications die and which stage is worth fixing
- [ ] Cannibalisation check when a cheaper plan launches, using difference in differences
- [ ] Support ticket clustering to find the three product problems worth fixing
- [ ] Unit economics of a delivery business at three density levels, built bottom up
- [ ] Marketing attribution, last touch against time decay, on the same dataset
- [ ] Measurement error in a product metric, and how much of a reported movement is noise
- [ ] Sales pipeline conversion by stage, and where the forecast breaks

## teardown

Real AI products, and mostly ones in the lane I have built in: competitive intelligence, research and analyst tooling, B2B AI that replaces a chunk of a services engagement. I have shipped one of these, so I have standing to be specific about what is hard.

- [ ] Crayon and Klue in competitive intelligence, what they charge for and what they cannot automate
- [ ] AlphaSense, the moat when the moat is licensed content rather than model quality
- [ ] Harvey and legal AI, why a narrow vertical with high billing rates is the easiest place to start and the hardest to hold
- [ ] Perplexity, the shape of the business under the cost of every query
- [ ] Glean and enterprise search, the distribution problem inside a company
- [ ] Cursor, whether the wrapper moat holds when the model providers ship the same feature
- [ ] An AI product priced per seat against one priced per unit of work, and what each pricing choice commits the company to
- [ ] Sarvam and Indic language models, the case for a country specific model company
- [ ] Salesforce Agentforce, whether an incumbent's AI layer is a product or a retention tool
- [ ] GitHub Copilot, the gross margin question on a fixed price AI product
- [ ] An AI product that failed in the last two years, and the decision that killed it
- [ ] The consulting deliverable as a product, which parts of a research report automate and which do not

## metric

One metric per file. Formula, edge cases, how it gets gamed, what to pair it with.

- [ ] Activation rate for a B2B analytics product, and why the definition decides the roadmap
- [ ] Gross margin for an AI product where inference is the main cost
- [ ] Net revenue retention, what it hides when the customer count is small
- [ ] CAC payback, cash based against accrual based, and which one a founder should watch
- [ ] Time to first value, how to instrument it without guessing
- [ ] Output quality for an AI product, when the output is a document a human has to trust
- [ ] Confidence and calibration as a product metric, not a model metric
- [ ] Contribution margin per order for a quick commerce business
- [ ] DAU over MAU, when the ratio is a real signal and when it is theatre
- [ ] North star metric selection, the test a candidate metric has to pass
- [ ] Forecast accuracy for a sales team, and the metric that stops sandbagging
- [ ] Support contact rate per hundred orders, as an operations quality metric

## case

**Fallback only.** Used on a Thursday when `journal/inbox` is empty. My own decisions are better material, so the aim is for this list to go untouched.

- [ ] A profitable services firm deciding whether to build a product, with the cash flow consequences laid out
- [ ] Pricing a B2B AI tool when the buyer's saving is clear but their budget line does not exist
- [ ] A founder choosing between one large enterprise pilot and ten small paying customers
- [ ] Whether to keep a loss making segment that brings in the customers who buy the profitable one
- [ ] Hiring a sales team against founder led sales, and at what revenue the switch pays for itself
- [ ] Deciding to sunset a feature a loud minority depends on
- [ ] Market entry sequence for an Indian SaaS product going to the US
- [ ] Whether to raise prices when churn is already above plan
- [ ] Responding to a competitor who has cut prices by forty percent
- [ ] Whether to open source the core of a commercial product

## innovation-scan

Friday's track is a scan of what actually shipped that week, so this list is the fallback. When the week is quiet, the run writes one of these as a sector note into `content/sector-notes` instead: how a sector works, the players, where money is made along the chain, and the one number that decides the outcome. Indian sectors mostly.

- [ ] Housing finance in India, where an NBFC actually earns against a bank, and what the spread has to cover
- [ ] Indian quick commerce, where the margin comes from and whether it survives a funding slowdown
- [ ] Market and competitive research as an industry, who buys it and what they pay
- [ ] UPI and the payments business, how anyone makes money on a zero MDR rail
- [ ] Indian SaaS selling to the US, the gross margin and sales efficiency picture
- [ ] IT services and AI, whether the pyramid staffing model can hold
- [ ] Consumer lending and the NBFC model, where the risk actually sits
- [ ] Insurance distribution in India, why the broker layer persists
- [ ] Data centres in India, the demand case and the power constraint
- [ ] Ed tech after the correction, which parts of the model actually worked
- [ ] Indian pharma CDMO, the shift in who holds pricing power
- [ ] Electric two wheelers, the unit economics against the subsidy schedule

## build

Saturday is build day, and once there are three or more tools in `tools/`, improving an existing one beats starting another. These are the new tools worth having. Fixing a limitation a tool already admits to in its "What it does not do" section counts for more than any of them.

- [x] Cohort retention table generator from a transactions CSV
- [ ] Unit economics calculator that takes assumptions from a YAML file and prints a sensitivity table
- [ ] A/B test power calculator with a plain language output and an honest minimum detectable effect
- [ ] Metric definition linter that checks a YAML metric spec for missing edge cases
- [ ] Competitor pricing page tracker that diffs a saved snapshot
- [ ] Dataset profiler that prints the five things to check before trusting a table
- [ ] Simple forecast baseline that any model has to beat before it is worth using
- [ ] Funnel chart generator that handles missing steps
- [ ] Error bar helper that turns a conversion count into a confidence interval, for people who quote percentages off forty users
- [ ] Case note template generator with the sections prefilled
