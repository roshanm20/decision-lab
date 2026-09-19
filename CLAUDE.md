# Repo instructions

This repo is a working notebook on business intelligence, AI product decisions, and management problems. It is maintained by Muhammed Roshan M and is meant to be read by people who are evaluating how he thinks: recruiters, PGP admission interviewers, and potential collaborators.

A daily GitHub Action runs the `daily-build` skill, which adds one piece and commits it. The same skill can be run by hand with `/daily-build` in Claude Code.

Roshan is a physics graduate moving into product and management. The repo's job is to show that he can build, measure, and decide, not to claim experience he does not have. Overclaiming on his behalf damages it more than a thin week does.

## Read before writing anything

`STANDARDS.md` is binding. Read it in full at the start of every run. If a piece you are about to write cannot meet those standards, stop and commit nothing rather than lowering the bar.

## How a day runs

1. Run `python scripts/pick_track.py`. It prints today's track, the target directory, and where the day's subject comes from.
2. On a day where the brief says `"discovery": true`, search the web first for something that actually moved, log three to five findings in `discovery/<month>.md` including the ones you reject, and build on one of them. The backlog is only the fallback when the search comes up empty. On Thursdays the subject is the oldest note in `journal/inbox` instead. The skill covers both.
3. Do the work for that track. Research properly. Real sources, real numbers.
4. Write the file into the directory the script gave you, named `YYYY-MM-DD-slug.md`.
5. Tick the backlog item if you used one, and file any unbuilt findings into `BACKLOG.md` marked `(auto)`.
6. Run `python scripts/build_index.py` to refresh `docs/INDEX.md` and the index block in `README.md`.
7. Commit and push.

## Commit rules

The commit author must be Muhammed Roshan M <muhammedroshanmangat@gmail.com>. The action overrides git's configured user with `claude[bot]` before the skill runs, so setting git config is not enough. Pass `--author` on the commit itself, every time. A commit authored by the bot does not show on Roshan's contribution graph, which defeats the point of the repo.

Commit message format: `track: short description of the piece`

Examples:
- `teardown: Notion AI pricing and why the seat model holds`
- `metric: define activation rate for a B2B analytics product`

One commit per day covering the new piece and the index refresh. Do not split into several cosmetic commits to inflate the count. The point is the content, not the graph.

## Hard limits

- Never write more than one content piece in a run.
- Never skip the discovery log on a discovery day. A day with no log entry looks like the search never happened, and that is the part of this repo that shows judgement rather than output.
- On build day, once `tools/` holds three or more tools, improving one is the default. Starting another needs a reason stated in the commit message.
- Never edit or rewrite a piece from a previous day, except to fix a factual error. If you fix one, say so in the commit message.
- Never invent a source, a URL, a filing, or a figure.
- Never state anything about Roshan's own companies or projects that is not written in a journal note. CompEdge, Nayrix, Dharti, the Mercor eval work. No web research about them, no inference, no plausible filler. A gap becomes an open question, not a guess.
- Never commit if the day's piece already exists. Check the target directory first and exit quietly.
- Never touch `weekly/` review files that already have content under the "My read" heading. Those are written by hand.
- If research fails and you cannot source the claims, write nothing and exit. A missing day is fine.

## Tone

Plain Indian English. Short sentences. No em dashes. No AI or consulting filler. Write like a person explaining something to a colleague who is smart but busy.
