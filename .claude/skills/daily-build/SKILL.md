---
name: daily-build
description: Produce and commit one day's piece for this repo, on the track the rotation picks, starting from a live web search for what is actually new. Use when the daily scheduled workflow runs, or when Roshan asks for today's piece by hand.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch
---

# Daily build

Produce exactly one piece and commit it. Follow these steps in order.

## 1. Load the rules

Read `STANDARDS.md` in full. Read `CLAUDE.md`. The line that governs everything: every piece has to be defensible by Roshan in an interview, without notes. Write for that reader.

## 2. Get today's brief

```bash
python scripts/pick_track.py
```

Exit codes:

- **0**: carry on.
- **3**: today's piece already exists. Stop. Commit nothing. Say so and finish.
- **4**: a backlog-only track has an empty backlog. Propose three topics that meet the standards, append them under that heading marked `(auto)`, then use the first.

## 3. Discovery, when the brief says `"discovery": true`

Most days start here, not with a topic. The brief's `search_for` field says where to look.

Search properly. Several searches, not one. You are looking for something that moved recently and that a builder would care about, not for a topic to summarise. Good signals:

- Someone describing a problem they have, in public, in the last two weeks.
- A pricing page or changelog that changed.
- A dataset or API that just became available.
- A claim that looks wrong and can be checked.

Bad signals: a funding round with no product detail, a vendor blog post about its own excellence, a paper with no buildable idea in it.

Then append to the discovery log at the path the brief gives, creating the file with a `# Discovery log, <Month YYYY>` heading if it does not exist:

```
## 2026-09-21
- <finding, one line> . <link> . BUILT
- <finding, one line> . <link> . QUEUED, added to BACKLOG under metric
- <finding, one line> . <link> . IGNORED, the claim did not survive a check
```

Log three to five findings every discovery day, including the ones you did not use. The rejected ones are part of the record.

Pick one finding and build the day's piece on it. If the search genuinely turns up nothing worth building on, say so in the log, then fall back to `backlog_fallback_topic` from the brief. Falling back is allowed. Pretending a weak finding is interesting is not.

## 4. Research the thing you picked

- Primary sources. Pricing pages, filings, official statistics, the actual repository, the actual dataset. A news article citing a number is worse than the source it cites, so follow it back.
- Every figure gets its source and the date you checked it.
- If you cannot source what the piece needs, **stop and write nothing.** Say what you could not source. A missing day is acceptable. A day of unsourced assertions is not.

Do not lift sentences from sources. Read, then write in your own words.

Never write about Roshan's own companies or projects from anything except a journal note. Not from the web, not from this repo's README, not from inference. If a piece would benefit from a CompEdge example, leave it out and say so in the commit message.

## 5. Build or write

Write to the directory the brief gives, named `YYYY-MM-DD-slug.md`, with the frontmatter block from `STANDARDS.md`: `title`, `date`, `track`, `summary`, `sources`.

Every piece ends with:

```
## What would change my mind

## Sources
```

Sources numbered, each with a link and the date checked.

Style, and this is checked:

- Plain Indian English. Short sentences. The way a person writes.
- **No em dashes anywhere.** Use a comma, a full stop, "and", or "but".
- No filler opening. Start on the substance.
- No consulting or AI vocabulary. Not "leverage", not "landscape", not "robust framework", not "in an era of".
- Active voice.
- Eight hundred to fifteen hundred words for a note, two hundred to five hundred for a metric. Do not pad.

Then meet the brief's `extra_requirement`. If it says run the tool and paste the output, run it with Bash and paste what it actually printed.

## Build day, Saturdays

The brief carries `existing_tools` and `prefer_extending`.

When `prefer_extending` is true, improving an existing tool is the default and starting a new one needs a reason you state in the commit message. Forty one-off scripts are worth less than six tools that got better.

To extend a tool: read it and its note, pick a limitation the note already admits to under "What it does not do", fix that, run the tool to prove it works, update the note's limitation list, and add a line to `tools/CHANGELOG.md`. The day's markdown file then describes what changed and why, and it can be short.

To write a new tool: under three hundred lines, runs on its own, no dependencies beyond pandas, numpy, matplotlib and the standard library unless you commit a requirements file. Standard library only is better. Add its first entry to `tools/CHANGELOG.md`.

Either way you must actually run it. Never paste an output you did not see.

## Decision record track, Thursdays

The brief will have `"source": "journal"` and a `note_to_use` path. Read that note and build the record from it.

The rule that overrides everything here: **use only what the note says.** You know nothing about CompEdge, Nayrix, Dharti or any of Roshan's projects beyond what is in that file. Do not search for his companies. Do not reason your way to a plausible detail. Do not smooth over a gap.

Where the note is thin, put the question in the record:

```
## Open questions on my own note

- The note says pricing moved but not by how much. What were the two numbers?
- Nothing on what churn did in the three months after. Did it move?
```

That section is a feature. It shows the record came from a real note, and it gives Roshan a list to fill in.

Confidentiality: if the note has a line starting `CONFIDENTIAL:` or a "Cannot go public" section, nothing in there reaches the record. Use a ratio, a range or a description, and say the exact figure is not public.

Structure:

```
## The decision
## What I knew at the time
## Options
## What I picked and why
## What happened
## What I would do differently
## Open questions on my own note
```

Then move the note:

```bash
git mv journal/inbox/<note>.md journal/used/<note>.md
```

If the brief says `"source": "backlog"` instead, the inbox was empty. Write an outside case note into `content/cases` and do not touch the journal folders.

## Weekly review track, Sundays

Do not write opinions. Prepare a draft only:

1. List every piece committed in the last seven days with its track, title and one line summary. `git log --since="7 days ago" --name-only --pretty=format:` gives the files.
2. Write a "Questions for me" section, three to five specific questions about the actual claims made that week. Not generic ones.
3. Leave this block unfilled at the end:

```
## My read

_Not yet written._
```

Roshan writes that by hand. Never fill it, and never edit a weekly file where that section already has content.

## 6. Self check

Every answer must be yes, or fix it, or abandon the piece.

- A real decision or problem at the centre, not a topic summary?
- Every number sourced, or labelled an estimate with the assumption stated?
- A clear position, rather than hedging both ways?
- Is "What would change my mind" specific?
- Does the piece leave behind something reusable?
- Any em dashes? Search the file and remove them.
- Could Roshan defend every sentence in an interview?
- Does this repeat an existing piece? Check the track directory and `grep` titles in `docs/INDEX.md`.
- On a discovery day, is the discovery log updated, including the findings you rejected?

## 7. Tick, rebuild, commit

Tick the backlog item if you used one. Append two or three new topics marked `(auto)` if the track is down to three or fewer.

```bash
python scripts/build_index.py
```

Fix any frontmatter problems it reports in today's file.

**The commit author matters more than anything else in this file.** The action
sets git's user to `claude[bot]` before you run, and a commit authored by the bot
does not appear on Roshan's contribution graph, which makes the whole repo
invisible on his profile. So always pass the author explicitly:

```bash
git add -A
git commit --author="Muhammed Roshan M <muhammedroshanmangat@gmail.com>" \
  -m "<track>: <short description>"
git push
```

The committer stays `claude[bot]`, which is honest and correct, since the bot did
commit it. GitHub counts the author, so this is what makes it count for Roshan.

After pushing, check it worked:

```bash
git log -1 --pretty=format:'%an <%ae>'
```

That must print `Muhammed Roshan M <muhammedroshanmangat@gmail.com>`. If it does
not, fix it with `git commit --amend --author=...` and force push.

One commit. Do not split it to make the history look busier.
