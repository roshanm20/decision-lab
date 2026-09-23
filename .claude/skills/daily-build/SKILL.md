---
name: daily-build
description: Build and commit one day's work for this repo from ROADMAP.md, with tests, docs, an independent review and a guaranteed commit. Use when the daily scheduled workflow runs, or when Roshan asks for today's build by hand.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch, Task
---

# Daily build

One day, one commit, and it must be work Roshan could defend in an interview. Follow the steps in order.

## 1. Load the rules

Read `CLAUDE.md` and `STANDARDS.md` in full. They are binding. Keep the goal in mind the whole time: tools practitioners would actually use, done properly, over anything that just adds volume.

## 2. Get the brief

```bash
python scripts/pick_track.py
```

- Exit **3**: today already landed. Stop. Commit nothing.
- Exit **4**: today's roadmap section has no ready item. Add three good items to that section of `ROADMAP.md` in the exact item format, each grounded in something you found and can link, then build the first.
- Exit **0**: carry on with the brief. It gives `day_type`, the roadmap `item`, the persona's existing tools with the limitations their docs admit, and the `commit_trailer`.

## 3. Do the day's work

### build, Monday to Friday

The brief's `item` is either `extend` (improve an existing tool) or `new` (add a tool).

First, spend a few minutes on discovery for the persona. Search for what practitioners in that role are actually struggling with this week: forum threads, practitioner blogs, product changelogs, questions on analytics and marketing communities. Append three findings to `discovery/<YYYY-MM>.md` under a `## <date>` heading, each one line with a link and a verdict: `BUILT`, `QUEUED` or `IGNORED, <reason>`. Rejected findings stay in the log. If a finding sharpens today's item, use it. Anything worth building later becomes a `QUEUED` finding, and Sunday turns those into roadmap items.

**For an `extend` item:**
1. Read the tool's module, its tests, and its docs page.
2. Make the change. Keep the tool's interface and its existing behaviour unless the item says otherwise.
3. Add tests for the new behaviour, including at least one checked against a number you worked out independently, and one for a bad input.
4. Update the docs page: new usage, a fresh example with real output, and remove the fixed limitation from `## What it does not do`. Add any new limitation you now know about.
5. Add a dated entry to `tools/CHANGELOG.md`.

**For a `new` item:**
1. Copy the structure of an existing tool in the same persona or the closest one: a module docstring that names the mistake the tool fixes, a `TOOL` dict, `add_arguments(parser)`, `run(args)`, and pure functions that the tests can call directly.
2. Standard library only unless there is a real reason. Say the reason in the docs if so.
3. Register it in `decisionlab/registry.py`.
4. Write `tests/test_<module>.py`: the core calculation checked against an independently worked value, edge cases, and bad inputs refused with clear messages.
5. If it needs example input, add it to `examples/` and label it illustrative in the file and on the docs page.
6. Write `docs/tools/<name>.md` in the same shape as the existing pages. Paste real output from a real run. End with `## What it does not do`.
7. Add a dated entry to `tools/CHANGELOG.md`.

Then run the tool the way a user would, from the command line, on the example and on at least one awkward input. Fix anything that reads badly.

Every `$ python -m decisionlab ...` block on a docs page must be a plain command, no pipes or redirects, whose output is the same on every run. After any change to a tool or its docs page, run `python scripts/refresh_docs.py` so every pasted output on the docs pages is regenerated from a real run, then read the diff. If an output changed in a way you did not intend, that is a bug to fix, not a docs update. `scripts/check.py` fails if any pasted output is stale.

### note, Saturday

Take the brief's item from the `notes` section. The best note runs one of this repo's tools on real, sourced public data.

- Research primary sources: filings, official statistics, company pricing pages, the actual dataset. Follow a news article back to what it cites.
- Every number gets its source and the date checked. If you cannot source what the note needs, switch to the next notes item. If none can be sourced, fall back as in step 6.
- If a tool is used, commit its input file next to the note and paste the real output.
- Frontmatter as in `STANDARDS.md`. End with `## What would change my mind` and `## Sources`.

### decision-record, Thursday when journal/inbox has a note

Build the record from the note in the brief, using **only what the note says**. You know nothing about Roshan's companies beyond that file. No web searching them, no filling gaps by inference.

Structure: `## The decision`, `## What I knew at the time`, `## Options`, `## What I picked and why`, `## What happened`, `## What I would do differently`, `## Open questions on my own note`. The last section lists every gap in the note as a question. The journal folder is public, so the note itself is already visible. If it still contains something that looks like it should not be public, such as a client name or exact revenue, leave that out of the record and say so in the commit message so Roshan can remove it from the note too.

Write it to `content/decisions/<date>-<slug>.md` with `track: decision-record`, then:

```bash
git mv journal/inbox/<note>.md journal/used/<note>.md
```

### release, Sunday

1. Run `python scripts/check.py`. If anything fails, fixing it is today's work.
2. Write `weekly/<date>-week-log.md` with `track: weekly-log`. List any decision record by linking to its file in `content/decisions/`, not by retyping its title. Then a factual list of the week's commits (`git log --since="7 days ago" --format="%ad %s" --date=short`), which tools were added or extended, the test count now against a week ago, and how many discovery findings were logged. Facts only, no opinions and no placeholders.
3. Groom `ROADMAP.md`: tick anything finished, turn this week's `QUEUED` discovery findings into items (each with a why and a done-when), split anything too big for one day, and keep at least five ready items in every section. Order each section by value to a practitioner.
4. If a tool was added or extended this week, bump the version in both `pyproject.toml` and `decisionlab/__init__.py` (new tool or option: minor, fix only: patch) and add a section to `CHANGELOG.md` in the same style as the ones already there. The workflow turns that section into a GitHub release.

## 4. Independent review, before any commit

Use the Task tool to start a reviewer agent that did not see you write the change. Give it this brief, filled in:

> You are reviewing a change to a public repo that will be read by recruiters and interview panels. Read STANDARDS.md in full. Then review every file listed in `git status --porcelain` and `git diff`. Check: (1) run `python scripts/check.py` and report its result; (2) for any tool changed, run the command shown on its docs page and confirm the pasted output matches what it prints now; (3) confirm at least one test checks a number worked out independently rather than copied from the code's own output; (4) for any note, open at least two cited sources with WebFetch and confirm they say what the note claims; (5) look for claims stated as fact without a source, invented example data presented as real, placeholders, filler, and any mention of Roshan's own companies outside journal-derived files. Reply with PASS, or with a numbered list of specific problems and the file and line for each.

Fix everything it lists and review once more. If it still does not pass after two rounds, drop down the ladder in step 6 instead of committing weak work.

## 5. Commit

```bash
python scripts/commit_day.py --item <ID> -m "<day type>: <what this does>"
```

For example `--item BI-02 -m "build: funnel tool with step intervals"`. Pass `--item` with the ID of the one roadmap item this commit actually finishes, nothing else. The script ticks it in `ROADMAP.md` in the same commit and records it in a `Roadmap-Item` trailer, which is how the picker knows never to build it again. A commit that finishes no roadmap item, such as Sunday's release or a fallback-ladder fix, has no `--item`.

Commit messages are public. Never name Roshan's companies in one, and the script refuses if you do. A decision record's message describes it instead, for example `decision-record: pricing tiers, from a journal note`.

The script rebuilds the index, runs every check, commits as Muhammed Roshan M with the day's `Daily-Build` trailer, and confirms the author. If it refuses, fix what it reports and run it again.

**Do not push.** `git push` is blocked for you. The workflow checks again with its own copy of the checks and pushes.

**Do not edit Roshan's control files**: `CLAUDE.md`, `STANDARDS.md`, `docs/setup.md`, anything in `.github/` or `.claude/`, `scripts/check.py`, `scripts/commit_day.py`, `scripts/daylog.py`, `scripts/should_run_now.py`, `scripts/profile_section.py`, `scripts/refresh_docs.py`, `scripts/build_index.py`, and the README outside its generated block. The workflow refuses to push a run that touches any of them, and the whole day is lost. If one of them seems wrong, say so in the weekly log instead.

## 6. If the planned work cannot meet the bar

A day always ends with a commit, and it is never filler. Go down this ladder until something passes review and the checks:

1. The next ready item in the same roadmap section.
2. A small `extend` on any tool: fix one limitation listed in its docs page, with tests.
3. Tests for an edge case some tool does not cover yet, plus a fix if the test finds a bug.
4. Grooming `ROADMAP.md` with this week's discovery findings, every new item carrying its source link.

Whichever rung you land on, the commit message says what was actually done.

## Style, checked by scripts/check.py

Plain Indian English, short sentences, active voice. No em dashes or en dashes anywhere, in code comments too. No filler openings, no consulting or AI vocabulary.
