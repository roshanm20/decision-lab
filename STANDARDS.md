# Standards

Every file in this repo has to pass these checks before it gets committed. If a piece cannot pass, it does not go in. An empty day is better than a filler day.

## The one rule that matters

I have to be able to defend every file in this repo in an interview, without notes.

That means no piece can contain a claim I have not checked, a number I cannot source, or a conclusion I do not actually hold. If an interviewer opens a random file and asks "why did you say this", I should have an answer.

## What every piece must have

1. A real decision or a real question at the centre. Not a topic summary. "Should Zomato have kept Blinkit separate" is a decision. "An overview of quick commerce" is not.
2. Numbers with sources. Every figure gets a link or a named filing, right next to it. If the number cannot be sourced, write the estimate and say it is an estimate, with the assumption stated.
3. A position. Say what you think and why. Hedging on both sides is the easiest way to look like you have not thought about it.
4. What would change my mind. One short section at the end. This is the part that shows actual thinking, and it is the part interviewers pick up on.
5. Something reusable. A query, a metric definition, a small script, a checklist. A piece that is only prose is worth less than a piece that leaves behind a tool.

## What is banned

- Padding. No "in today's fast moving landscape". No section that exists only to make the file longer.
- Fake precision. Do not write 23.7% when the source says roughly a quarter.
- Invented data. If a dataset is needed and none is public, say so and use a clearly labelled synthetic one with the generator script committed.
- Repeating a piece that already exists in the repo under a different title.
- Marketing language about myself. No "cutting edge", no "leveraging". Describe what was done.
- Long files for the sake of length. Eight hundred to fifteen hundred words is the useful range for a note. A metric definition can be two hundred.

## Writing style

- Plain Indian English, the way a person actually writes. Short sentences.
- No em dashes anywhere. Use a comma, a full stop, "and" or "but".
- Active voice. "I compared three pricing models", not "three pricing models were compared".
- Define a term the first time it appears, in one line, then use it.
- Tables for comparisons. Prose for reasoning.

## Code standards

- Every SQL file states the dialect at the top and the schema it assumes.
- Every Python file runs on its own with `python file.py` and prints something useful. No hidden dependencies beyond pandas, numpy, matplotlib and the standard library, unless a requirements file is committed alongside.
- Comment the business logic, not the syntax.
- If a query is slow or wrong in an obvious case, say so in a note at the bottom rather than leaving it silently broken.

## Frontmatter

Every markdown piece starts with this block. The index script reads it, so the keys must match exactly.

```
---
title: Short and specific, no colon-subtitle pattern
date: YYYY-MM-DD
track: one of bi-analysis, teardown, metric, case, sector-note, tool, weekly-review
summary: One sentence saying what the piece concludes, not what it covers.
sources: 3
---
```

`sources` is the count of external sources cited in the piece. A note with zero sources is not publishable, with two exceptions: the `tool` track, where the tool and its tested output are the evidence, and `weekly-review`, which is about this repo.

That exception exists for a reason. A rule that demands a citation for something that does not need one is how invented citations get written. If there is nothing real to cite, cite nothing and say why.

## The weekly check

On Sunday the repo gets a review. That review is mine to write, not the automation's. The automation only prepares the draft with the week's files listed and the questions to answer. If I have not reviewed a week's output, the automation should stop adding to that track until I have.
