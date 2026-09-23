# Repo instructions

This repo is a toolkit for consultants, BI analysts, marketers and product managers, plus written notes that use the tools on real questions. It is maintained by Muhammed Roshan M, a physics graduate moving into product and management, and it is read by people deciding whether to hire or admit him: recruiters, IIM interview panels, and potential collaborators.

A daily GitHub Action runs the `daily-build` skill. The same skill runs by hand with `/daily-build` in Claude Code.

## The goal, so every decision can be checked against it

Make Roshan a standout candidate in IIM interviews and in placements, through a body of genuinely useful, tested code that practitioners in consulting, BI, marketing and product management could pick up and use, and notes that show he can reason about business with numbers.

That means: working tools over essays, depth over count, and nothing that would embarrass him if an interviewer opened it at random. Overclaiming on his behalf does more damage than a small day.

## Read before doing anything

1. `STANDARDS.md`, in full. It is binding.
2. `ROADMAP.md`, the section for today.
3. The docs page of any tool you are about to touch.

## How a day runs

The skill has the detail. In short:

1. `python scripts/pick_track.py` prints today's brief. Exit 3 means today already landed: stop.
2. Build the item, with tests, a docs page, and real output pasted from a real run.
3. Have a reviewer agent that did not write the change read it against `STANDARDS.md`, and fix what it finds.
4. `python scripts/commit_day.py --item <ID> -m "<day type>: <what this does>"` ticks the roadmap item, rebuilds the index, runs every check, and commits with the right author and trailers. `git push` is blocked. The workflow pushes after checking again with its own copy of the checks.

## A day is never skipped

The workflow runs at up to eight windows a day until the day's commit lands. If the planned item cannot meet the bar, do a smaller item that can: fix a documented limitation, add missing edge case tests, improve an example. Filler is never acceptable. A smaller honest commit always is.

## Commit rules

- Always commit through `scripts/commit_day.py`. It sets the author to Muhammed Roshan M with his verified email, which is what makes the commit count on his GitHub graph. The action sets git's user to `claude[bot]`, so a plain `git commit` would be invisible on his profile.
- One commit per day. Never split work into several commits to look busier.
- Pass `--item` with the one roadmap item the commit finishes, for example `--item BI-02 -m "build: funnel tool with step intervals"`. No `--item` for a commit that finishes no item.
- Commit messages are public and must never name Roshan's companies. The script refuses if they do.

## Hard limits

- Never write about Roshan's own companies or projects (Nayrix, CompEdge, the analytics and evaluation work) from anything except a note in `journal/inbox`. No web research on them, no inference. `scripts/check.py` fails the commit otherwise.
- Never invent a source, URL, filing, quote or figure. Never present invented example data as real.
- Never edit a past note except to fix an error, and say so in the commit message.
- Never change Roshan's control files: `STANDARDS.md`, this file, `docs/setup.md`, anything in `.github/` or `.claude/`, the check scripts (`check.py`, `commit_day.py`, `daylog.py`, `should_run_now.py`, `refresh_docs.py`, `build_index.py`, `profile_section.py`), or the README outside its generated block. The workflow refuses to push a run that touches them. Propose changes in the weekly log instead.
- Never commit with failing tests or a failing check.

## Tone

Plain Indian English. Short sentences. No em dashes or en dashes. No AI or consulting filler. Write like a person explaining something to a smart, busy colleague.
