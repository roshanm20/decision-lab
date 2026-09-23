# Standards

Everything committed to this repo has to pass these. `scripts/check.py` enforces the parts a script can check. The rest is on whoever writes the change, and on the reviewer agent that reads it before it is committed.

## The rule that matters most

I have to be able to defend every file in this repo in an interview, without notes.

That rules out any claim I have not checked, any number I cannot source, and any conclusion I do not actually hold. If someone opens a random file and asks "why did you say this", there has to be an answer.

## Tools

A tool is a module in `decisionlab/` registered in `decisionlab/registry.py`. Every tool must:

1. **Fix a named mistake.** Not "computes X", but "people get X wrong in this way, and this stops it". The docs page says what the mistake is.
2. **Run on the standard library.** If a tool truly needs numpy or pandas, it goes in an optional extra in `pyproject.toml` and the docs say so. Most do not need it.
3. **Have tests that check numbers, not just that code runs.** At least one test compares against a value worked out independently, by hand, from a textbook example, or by a separately written copy of the formula. Every bad input a user might plausibly give has a test that it is refused with a clear message.
4. **Have a docs page** in `docs/tools/` with who it is for, the problem, how to run it, an example with **real output pasted from a real run**, how to read that output, the method, and a section headed exactly `## What it does not do`. Example commands are plain commands with output that is the same every run, because `scripts/check.py` reruns them and fails if the pasted output has gone stale.
5. **Say what it does not do honestly.** That section is the most read part of a tool page for anyone who knows the field. It is also the list future work is picked from.
6. **Never present invented data as real.** Example files are labelled as illustrative in the file itself and on the docs page.
7. **Keep going when input is messy.** Report bad rows with line numbers rather than crashing, and rather than silently dropping them.

Extending a tool that exists usually beats starting another one. Six tools that clearly got better are worth more than twenty that were each touched once. `tools/CHANGELOG.md` and `CHANGELOG.md` are where that shows.

## Notes

A note is a written piece in one of the note folders. Every note must have:

1. **A real decision or question at the centre.** "Should Zomato have kept Blinkit separate" is a question. "An overview of quick commerce" is not.
2. **Numbers with sources next to them.** Every figure gets a link and the date it was checked. An estimate is labelled as an estimate with its assumption stated.
3. **A position.** Say what you think and why.
4. **A section headed "What would change my mind"**, specific, not three generic lines.
5. **Something reusable.** Best of all, one of the repo's tools run on the question, with the inputs committed.

The strongest notes are applied notes: a tool from this repo run on real, sourced data, showing both the tool and the thinking.

## Things that are never allowed

- An invented source, URL, filing, quote or figure.
- Anything about my own companies or projects (Nayrix, CompEdge, the analytics and evaluation work) that is not taken from a note I wrote in `journal/inbox`. A gap in my note becomes a question in the piece, not a guess. `scripts/check.py` fails any commit that mentions them elsewhere.
- Padding, filler openings, and consulting or AI vocabulary.
- Fake precision. Do not write 23.7 percent when the source says roughly a quarter.
- A placeholder published as if it were finished. "Not yet written" is not a summary.
- Commits made only to fill the graph: whitespace, reformatting, timestamps, reshuffled files.

## Every day lands a real commit

The daily run commits every day. When the day's planned item cannot meet this bar, because a source could not be verified or a test cannot be made to pass, the run does a smaller item that does meet it instead. Legitimate smaller items:

- Fixing a limitation listed in a tool's "What it does not do" section.
- Adding tests for an edge case a tool does not yet cover.
- Improving a docs page example with a clearer real run.
- Grooming `ROADMAP.md` with findings from the discovery log, each with its source.

Filler is never the fallback. A smaller honest commit always is.

## Writing style

- Plain Indian English, the way a person actually writes. Short sentences.
- No em dashes or en dashes anywhere. Use a comma, a full stop, "and" or "but". The check fails on them.
- Active voice. "I compared three pricing models", not "three pricing models were compared".
- Define a term the first time it appears, then use it.
- Tables for comparisons, prose for reasoning.

## Frontmatter for notes

```
---
title: Short and specific, no colon subtitle
date: YYYY-MM-DD
track: note, decision-record, bi-build, teardown, metric, case, sector-note or innovation-scan
summary: One sentence saying what the piece concludes, not what it covers.
sources: 3
---
```

Weekly logs use `track: weekly-log` and are listed separately. They record what happened, and they are not counted as pieces.

## Review

Every change is read by a second agent that did not write it, against this file, before it is committed. Then `scripts/check.py` runs. Then the workflow runs it again before pushing. I read the weekly log, and the weekly issue lands in my inbox with questions for my journal.
