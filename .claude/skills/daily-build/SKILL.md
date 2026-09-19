---
name: daily-build
description: Produce and commit one day's piece for this repo, on the track the rotation picks. Use when the daily scheduled workflow runs, or when Roshan asks for today's piece by hand.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, WebSearch, WebFetch
---

# Daily build

Produce exactly one piece and commit it. Follow these steps in order. Do not skip step 1 or step 2.

## 1. Load the rules

Read `STANDARDS.md` in full. Read `CLAUDE.md`. These are binding. The most important line in them is this one: every piece has to be defensible by Roshan in an interview, without notes. Write for that reader.

## 2. Get today's brief

```bash
python scripts/pick_track.py
```

Handle the exit code:

- **0**: carry on with the brief it printed.
- **3**: today's piece already exists. Stop now. Commit nothing. Say so and finish.
- **4**: the backlog for this track is empty. Propose three topics that meet the standards, append them under that track's heading in `BACKLOG.md` each marked `(auto)` at the end, then use the first one.

## 3. Research

This is where the piece is won or lost. Budget most of the run here.

- Search for primary sources. Company pricing pages, annual reports, regulatory filings, industry body data, official statistics. A news article citing a number is worse than the source it cites, so follow it back.
- Get real figures. For each one note the source and the date you checked it.
- Look for the number that decides the answer, not a collection of context numbers.
- If after honest effort you cannot source the claims the piece needs, **stop and write nothing**. Say what you could not source. A missing day is acceptable. A day of unsourced assertions is not.

Do not lift sentences from sources. Read, then write in your own words.

## 4. Write the piece

Write to the directory the brief gave you, using the suggested filename.

Start with the frontmatter block exactly as `STANDARDS.md` specifies: `title`, `date`, `track`, `summary`, `sources`.

Then the body. Structure depends on the track, but every piece ends with these two headings:

```
## What would change my mind

## Sources
```

The sources list is numbered, each with a link and the date you checked it.

Style rules, and they are checked:

- Plain Indian English. Short sentences. The way a person writes, not the way a report is written.
- **No em dashes anywhere.** Use a comma, a full stop, "and", or "but".
- No filler openings. Start on the substance in the first sentence.
- No consulting or AI vocabulary. Not "leverage", not "landscape", not "robust framework", not "in an era of".
- Active voice. Say "I compared", not "a comparison was made".
- Eight hundred to fifteen hundred words for a note. A metric definition can be two hundred to five hundred. Do not pad to hit a number.

Then meet the track's extra requirement from the brief. If it says commit the SQL alongside, commit the SQL. If it says run the tool and paste the output, run it for real with Bash and paste the actual output.

## 5. Self check before committing

Go through this list honestly. If any answer is no, fix it or abandon the piece.

- Is there a real decision or question at the centre, not a summary of a topic?
- Does every number have a source next to it, or is it labelled as an estimate with the assumption stated?
- Is there a clear position, or did I hedge both ways?
- Is the "What would change my mind" section specific, or is it three generic lines?
- Does the piece leave behind something reusable?
- Are there any em dashes? Search the file and remove them.
- Would Roshan be able to defend every sentence of this in an interview?
- Does this repeat a piece that already exists? Check with `ls` on the track directory and `grep` the titles in `docs/INDEX.md`.

## 6. Tick the backlog and rebuild the index

Edit `BACKLOG.md` and change the topic's `- [ ]` to `- [x]`. If the track is down to three or fewer pending topics, append two or three more, marked `(auto)`.

```bash
python scripts/build_index.py
```

Fix any frontmatter problems it reports in today's file.

## 7. Commit and push

Git identity is already set by the workflow. Do not change it.

```bash
git add -A
git commit -m "<track>: <short description of the piece>"
git push
```

One commit. Do not split it up to make the history look busier.

## Decision record track, Thursdays

This is the most important track in the repo and the easiest one to ruin.

The brief will have `"source": "journal"` and a `note_to_use` path. Read that note. Build the decision record from it.

The rule that overrides everything else here: **use only what the note says.** You know nothing about CompEdge, Nayrix, Dharti, or any of Roshan's projects beyond what is in that file. Do not search the web for his companies and weave in what you find. Do not reason your way to a plausible detail. Do not smooth over a gap.

Where the note is thin, put the question in the record itself:

```
## Open questions on my own note

- The note says pricing moved but not by how much. What were the two numbers?
- No mention of what churn did in the three months after. Did it move?
```

That section is a feature. It shows the record was built from a real note rather than made up, and it gives Roshan a list of things to fill in.

Handle confidentiality. If the note has a line starting `CONFIDENTIAL:` or a "Cannot go public" section, nothing in there reaches the published record. Use a ratio, a range, or a description instead of the figure, and say in the record that the exact number is not public.

Structure for a decision record:

```
## The decision
## What I knew at the time
## Options
## What I picked and why
## What happened
## What I would do differently
## Open questions on my own note
```

When the record is written, move the note:

```bash
git mv journal/inbox/<note>.md journal/used/<note>.md
```

If the brief instead says `"source": "backlog"`, the inbox was empty. Write an outside case note into `content/cases` from the backlog topic, and do not touch the journal folders.

## Weekly review track

Sunday is different. Do not write opinions. Prepare a draft only:

1. List every piece committed in the last seven days with its track, title, and one line summary. Get the list with `git log --since="7 days ago" --name-only --pretty=format:` or by reading the file dates.
2. Write a "Questions for me" section with three to five specific questions about the week's output. Not generic ones. Ask about the actual claims made, for example "the Blinkit note assumed a 12 percent contribution margin, does that hold at current AOV".
3. Leave this exact block at the end, unfilled:

```
## My read

_Not yet written._
```

Roshan writes that part by hand. Never fill it, and never edit a weekly file where that section already has content.
