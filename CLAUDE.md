# Repo instructions

This repo is a working notebook on business intelligence, AI product decisions, and management problems. It is maintained by Muhammed Roshan M and is meant to be read by people who are evaluating how he thinks: recruiters, PGP admission interviewers, and potential collaborators.

A daily GitHub Action runs the `daily-build` skill, which adds one piece and commits it.

## Read before writing anything

`STANDARDS.md` is binding. Read it in full at the start of every run. If a piece you are about to write cannot meet those standards, stop and commit nothing rather than lowering the bar.

## How a day runs

1. Run `python scripts/pick_track.py`. It prints today's track, target directory, and the next topic from `BACKLOG.md`.
2. Do the work for that track. Research properly with web search. Real sources, real numbers.
3. Write the file into the directory the script gave you, named `YYYY-MM-DD-slug.md`.
4. Tick the backlog item off in `BACKLOG.md`.
5. Run `python scripts/build_index.py` to refresh `docs/INDEX.md` and the index block in `README.md`.
6. Commit and push.

## Commit rules

The commit author must be Muhammed Roshan M. The workflow sets this before the skill runs, so do not change git config yourself.

Commit message format: `track: short description of the piece`

Examples:
- `teardown: Notion AI pricing and why the seat model holds`
- `metric: define activation rate for a B2B analytics product`

One commit per day covering the new piece and the index refresh. Do not split into several cosmetic commits to inflate the count. The point is the content, not the graph.

## Hard limits

- Never write more than one content piece in a run.
- Never edit or rewrite a piece from a previous day, except to fix a factual error. If you fix one, say so in the commit message.
- Never invent a source, a URL, a filing, or a figure.
- Never commit if the day's piece already exists. Check the target directory first and exit quietly.
- Never touch `weekly/` review files that already have content under the "My read" heading. Those are written by hand.
- If research fails and you cannot source the claims, write nothing and exit. A missing day is fine.

## Tone

Plain Indian English. Short sentences. No em dashes. No AI or consulting filler. Write like a person explaining something to a colleague who is smart but busy.
