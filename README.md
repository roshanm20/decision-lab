# Decision Lab

A working notebook on business intelligence, AI product decisions, and how companies actually make money.

I am Muhammed Roshan M. I did a BS-MS in Physics at IISER Bhopal and research at EPFL, and I am now building products and moving into product management. I co-founded [Nayrix](https://nayrix.com) and built [CompEdge](https://compedge.nayrix.com), an AI competitive intelligence product that takes a research brief and returns a client ready report.

The honest version of that transition is not that I have years of P&L experience, because I do not. It is that I can build the thing, measure it properly, and reason about whether it should exist. Physics taught me to be careful about what a number actually means, which turns out to matter more in product work than I expected. This repo is where I do that reasoning in public, one piece a day.

The reason it is public is simple. Anyone can say they think about business problems. This is the version you can check.

## What is in here

| Folder | What it holds |
| --- | --- |
| [`content/decisions`](content/decisions) | Decisions from my own work, written up properly. The pieces I can speak to in most detail |
| [`bi/analyses`](bi/analyses) | Analyses on real or clearly labelled synthetic data, with the query or script committed |
| [`bi/metric-library`](bi/metric-library) | One metric per file. Formula, edge cases, how it gets gamed |
| [`content/teardowns`](content/teardowns) | AI products taken apart: the wedge, the pricing, the moat, the thing that breaks |
| [`content/sector-notes`](content/sector-notes) | How a sector works, who earns what along the chain |
| [`content/cases`](content/cases) | Outside case notes. A decision, the options with numbers, my call |
| [`tools`](tools) | Small things that run: calculators, generators, checkers |
| [`weekly`](weekly) | What I got wrong that week and what I changed |
| [`journal`](journal/inbox) | My rough notes, which become the decision records |

## How it works

One piece a day, on a fixed rotation, so the week has a shape.

| Day | Track |
| --- | --- |
| Monday | Business intelligence analysis |
| Tuesday | AI product teardown |
| Wednesday | Metric definition |
| Thursday | A decision from my own work |
| Friday | Sector note |
| Saturday | A small tool |
| Sunday | Weekly review |

A GitHub Action runs Claude Code every morning against the rules in [`CLAUDE.md`](CLAUDE.md) and the quality bar in [`STANDARDS.md`](STANDARDS.md). It picks the next topic from [`BACKLOG.md`](BACKLOG.md), does the research, writes the piece, and commits it. I curate the backlog, review every week, and rewrite whatever does not hold up.

Thursday works differently, and it is the part I care most about. I drop rough notes about real decisions into [`journal/inbox`](journal/inbox), and the run turns the oldest one into a proper decision record using only what my note says. Where my note is thin, the record ends with a question about my own note rather than a guess. The automation knows nothing about my companies, and it is not allowed to fill that in from the web or from inference. Those open questions are the honest seam in this repo, and I would rather show it than hide it.

Being open about the automation is deliberate. Using a tool well and holding a standard it has to meet is the skill worth showing. The standards file is the interesting file, not the commit count.

## The bar every piece has to clear

1. A real decision at the centre, not a topic summary.
2. Numbers with sources next to them.
3. A position, stated plainly.
4. A section on what would change my mind.
5. Something reusable left behind: a query, a definition, a script.

Anything that cannot clear it does not get committed. Gaps in the history are on purpose.

## Index

<!-- INDEX:START -->

**1 piece so far.** 1 tool

Most recent:

- `2026-09-19` [Cohort retention table from a transactions CSV](tools/2026-09-19-cohort-retention-table-generator.md) . A standard library script that turns a transactions file into a monthly cohort table, and blanks out the months a cohort has not reached yet instead of printing them as zero retention.

Full list in [docs/INDEX.md](docs/INDEX.md).

<!-- INDEX:END -->

## Reading it critically

If you are evaluating this repo, the fastest way is to open the most recent piece in any track and check three things. Are the numbers sourced. Is there an actual position. Is there a section saying what would change it. If a piece fails those, it should not be here, and I would like to know: open an issue.

## Contact

[LinkedIn](https://www.linkedin.com/in/mroshan1) . [Portfolio](https://roshanm.vercel.app/) . [GitHub](https://github.com/roshanm20)
