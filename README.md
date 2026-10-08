# Decision Lab

[![checks](https://github.com/roshanm20/decision-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/roshanm20/decision-lab/actions/workflows/ci.yml)
![python](https://img.shields.io/badge/python-3.9%2B-blue)
![license](https://img.shields.io/badge/license-MIT-green)

Small, tested tools for the work consultants, BI analysts, marketers and product managers do every week, plus written notes that use them on real questions.

Every tool runs on plain Python with nothing else to install, has tests, and has a page that shows real output and says plainly what it does not do.

```bash
pip install "git+https://github.com/roshanm20/decision-lab"
decisionlab list
decisionlab market-size --example > model.json && decisionlab market-size model.json --simulate 10000
decisionlab ab-test analyze --control 1000 100 --variant 1000 108 --mde 0.01
```

Or without installing, from a clone: `python -m decisionlab list`.

## The tools

<!-- INDEX:START -->

**9 tools across 4 groups, 220 tests, 5 written notes.**

**For consultants**

- [`market-size`](docs/tools/market-size.md) Top-down and bottom-up sizing that checks the two agree, ranks the assumptions that matter, and gives a P10 to P90 range.
- [`unit-economics`](docs/tools/unit-economics.md) CAC, contribution, LTV and payback per customer, with payback that allows for churn and a ranking of which input moves LTV / CAC most.

**For BI and analytics**

- [`cohort`](docs/tools/cohort.md) Monthly cohort retention from a transactions CSV that leaves unreached months blank instead of showing them as zero.
- [`funnel`](docs/tools/funnel.md) Step-by-step conversion with confidence intervals from step counts or an event log, naming the step that leaks most.

**For marketers**

- [`ab-test`](docs/tools/ab-test.md) Sample size before a test, significance after it, and a plain answer on whether a flat result was just underpowered.
- [`srm`](docs/tools/srm.md) Checks whether an experiment's traffic actually landed in the split you configured, before you trust anything else it reports.

**For product managers**

- [`rice`](docs/tools/rice.md) Ranks a backlog by RICE and flags which positions depend on a confidence guess being right.
- [`nps`](docs/tools/nps.md) Scores NPS from raw 0 to 10 replies, puts an interval on it and tests whether two segments really differ.
- [`kano`](docs/tools/kano.md) Turns paired present and absent survey answers into a Kano category per feature, with counts, ties flagged and Better and Worse scores.

**Latest notes**

- `2026-10-03` [Does Unbounce's 336 percent test win survive its own numbers](content/notes/2026-10-03-unbounce-336-percent-test.md)
- `2026-09-26` [Sizing India's electric two-wheeler market and testing the sizing tool](content/notes/2026-09-26-india-electric-two-wheeler-market.md)
- `2026-09-22` [Zaigo's AI due diligence for private equity](content/teardowns/2026-09-22-zaigo-ai-due-diligence.md)
- `2026-09-21` [Why summing daily unique users overstates monthly reach](bi/analyses/2026-09-21-unique-user-double-counting.md)
- `2026-09-19` [Cohort retention table from a transactions CSV](tools/2026-09-19-cohort-retention-table-generator.md)

Everything, including older notes and weekly logs: [docs/INDEX.md](docs/INDEX.md).

<!-- INDEX:END -->

## Why these tools exist

Each one fixes a specific, common mistake rather than wrapping a formula in a script.

- **market-size** makes you build the estimate two ways and tells you when they disagree, which assumption the answer actually rests on, and how wide the honest range is.
- **ab-test** stops the most expensive experiment mistake: reading a flat result from a test that was too small to see the effect you care about as proof that the change does nothing.
- **rice** flags when the order of a backlog depends on one optimistic confidence guess.
- **cohort** leaves the months a cohort has not reached yet blank, instead of printing them as zero and making recent cohorts look like they collapsed.

## Who builds this

I am Muhammed Roshan M. I did a BS-MS in Physics at IISER Bhopal and research at EPFL, and I am moving into product and management. I co-founded [Nayrix](https://nayrix.com) and built [CompEdge](https://compedge.nayrix.com), an AI competitive intelligence product.

Physics taught me to be careful about what a number actually means, and most of these tools come from that habit: an estimate is a range, a flat test might just be a small test, and a cohort that has not reached month six has no month six.

## Notes

Written pieces live beside the code: [BI analyses](bi/analyses), [AI product teardowns](content/teardowns), [metric definitions](bi/metric-library), [decisions from my own work](content/decisions), and [applied notes](content/notes) that run the tools on real, sourced data. Every note has sourced numbers, a stated position, and a section on what would change my mind.

## Reading it critically

Open any tool page and check three things. Does the example show real output. Does the "What it does not do" section admit real limits. Do the tests check numbers worked out independently. If a tool fails those, I would like to know: [open an issue](https://github.com/roshanm20/decision-lab/issues).

## Contact

[LinkedIn](https://www.linkedin.com/in/mroshan1) . [Portfolio](https://roshanm.vercel.app/) . [GitHub](https://github.com/roshanm20)
