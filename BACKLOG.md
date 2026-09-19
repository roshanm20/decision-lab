# Backlog

The daily run picks the first unticked item under today's track. Tick an item with `[x]` when the piece is written.

Add your own items freely. The automation appends a suggestion only when a track runs empty, and it marks its own suggestions with `(auto)` so you can tell them apart and delete the weak ones.

Keep at least five items live under each track. A thin backlog is how the quality drops.

## bi-analysis

Each one needs a real or clearly labelled synthetic dataset, a query or script, and a conclusion a manager could act on.

- [ ] Cohort retention on a public e-commerce transaction dataset, and what the curve shape says about the business
- [ ] RFM segmentation, and where it misleads you when purchase frequency is seasonal
- [ ] Funnel drop-off analysis when events are logged unreliably, and how to still get a defensible number
- [ ] Building a churn early warning list from usage data, with the precision and recall tradeoff written out
- [ ] Pricing elasticity from observational data, and why the naive regression is wrong
- [ ] Marketing attribution, last touch against a simple time decay model, on the same dataset
- [ ] Inventory stockout cost model for a D2C brand, and the reorder point that falls out of it
- [ ] Unit economics of a delivery business at three density levels, built bottom up
- [ ] A/B test that came out flat, and how to work out whether it was underpowered or the idea was wrong
- [ ] Cannibalisation check when a cheaper plan is launched, using a difference in differences setup
- [ ] Support ticket text clustering to find the three product problems worth fixing
- [ ] Sales pipeline conversion by stage, and where the forecast breaks

## teardown

Pick a real AI product. Look at the product, the pricing, the wedge, the moat, and the part that will break. No press release summaries.

- [ ] Cursor, and whether the wrapper moat holds when the model providers ship the same feature
- [ ] Notion AI pricing, seat based against usage based, and what that choice commits them to
- [ ] Perplexity, the shape of the business under the cost of every query
- [ ] Harvey and legal AI, why a narrow vertical with high billing rates is the easiest market to enter
- [ ] Glean and enterprise search, the distribution problem inside a company
- [ ] Zomato and Swiggy AI features, whether any of them change the unit economics or only the interface
- [ ] Jasper, what happened when the underlying capability got commoditised
- [ ] GitHub Copilot, the gross margin question on a fixed price AI product
- [ ] Sarvam and Indic language models, the case for a country specific model company
- [ ] Salesforce Agentforce, whether an incumbent's AI layer is a product or a retention tool
- [ ] Synthesia, why video is a better AI product shape than text
- [ ] An AI product that failed in the last two years, and the decision that killed it

## metric

One metric per file. Definition, the exact formula, the edge cases, how it gets gamed, and what to pair it with.

- [ ] Activation rate for a B2B analytics product, and why the definition decides the roadmap
- [ ] Net revenue retention, what it hides when the customer count is small
- [ ] Contribution margin per order for a quick commerce business
- [ ] DAU over MAU, when the ratio is a real signal and when it is theatre
- [ ] CAC payback, cash based against accrual based, and which one a founder should watch
- [ ] Time to first value, how to instrument it without guessing
- [ ] Gross margin for an AI product where inference is the main cost
- [ ] Feature adoption depth, and why breadth of adoption is the wrong thing to measure
- [ ] Support contact rate per hundred orders, as an operations quality metric
- [ ] Forecast accuracy for a sales team, and the metric that stops sandbagging
- [ ] Employee productivity metrics for a team using AI tools, and the three ways they go wrong
- [ ] North star metric selection, the test a candidate metric has to pass

## case

Write it like a case note. Situation, the decision on the table, the options with numbers, your call, and what would change your mind.

- [ ] A profitable services firm deciding whether to build a product, with the cash flow consequences laid out
- [ ] Pricing a B2B AI tool when the buyer's saving is clear but their budget line does not exist
- [ ] Whether to keep a loss making segment that brings in the customers who buy the profitable one
- [ ] Build against buy for an internal analytics stack at a two hundred person company
- [ ] A founder deciding between a large pilot with one enterprise and ten small paying customers
- [ ] Deciding to sunset a feature that a loud minority of customers depend on
- [ ] Choosing a market entry sequence for an Indian SaaS product going to the US
- [ ] Whether to raise prices when churn is already above plan
- [ ] Hiring a sales team against founder led sales, at what revenue the switch pays for itself
- [ ] A manufacturing firm deciding how much to spend on demand forecasting
- [ ] Responding to a competitor who has cut prices by forty percent
- [ ] Whether to open source the core of a commercial product

## sector-note

Indian sectors mostly. Structure of the sector, who makes money, what is actually changing, and the number that matters.

- [ ] Indian quick commerce, where the margin comes from and whether it survives a funding slowdown
- [ ] UPI and the payments business, how anyone makes money on a zero MDR rail
- [ ] Indian SaaS selling to the US, the gross margin and sales efficiency picture
- [ ] Ed tech after the correction, which parts of the model actually worked
- [ ] Insurance distribution in India, why the broker layer persists
- [ ] Logistics and warehousing, the effect of GST on network design
- [ ] Indian pharma CDMO, the shift in who holds pricing power
- [ ] Electric two wheelers, the unit economics against the subsidy schedule
- [ ] Agri supply chain, the layers between farm gate and retail and what each one earns
- [ ] IT services and AI, whether the pyramid staffing model can hold
- [ ] Consumer lending and the NBFC model, where the risk actually sits
- [ ] Data centres in India, the demand case and the power constraint

## tool

A small thing that works and that someone else could use. Under three hundred lines.

- [x] Cohort retention table generator from a transactions CSV
- [ ] Metric definition linter that checks a YAML metric spec for missing edge cases
- [ ] Unit economics calculator that takes assumptions from a YAML file and prints a sensitivity table
- [ ] A/B test power calculator with a plain language output
- [ ] Competitor pricing page tracker that diffs a saved snapshot
- [ ] SQL query formatter and cost estimate stub for a warehouse dialect
- [ ] Funnel chart generator that handles missing steps
- [ ] Simple forecast baseline that any model has to beat before it is worth using
- [ ] Dataset profiler that prints the five things to check before trusting a table
- [ ] Case study note template generator with the sections prefilled
