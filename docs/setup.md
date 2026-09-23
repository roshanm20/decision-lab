# How this repo runs, and the switches that are yours

The repo is already set up and running. This page is for when something needs attention, or when you want to turn on one of the optional parts.

## What happens without you

| When | What | Where to see it |
| --- | --- | --- |
| Every day, at a different time | One commit: a new or improved tool, or a note. Monday BI, Tuesday consulting, Wednesday marketing, Thursday a decision record if you left a journal note, else a product tool, Friday whichever group has the fewest tools, Saturday a note, Sunday a release and a weekly log | Commits on `main` |
| After every daily run | Tests on Python 3.9 and 3.12, and the installed command is tried | The checks badge on the README |
| When the version goes up | A GitHub release with notes from `CHANGELOG.md` | Releases, on the right of the repo page |
| Monday 08:00 IST | An issue with the week's commits, a two minute checklist, and journal prompts. GitHub emails it to you | Your inbox |
| If a whole day passes with nothing | An issue titled "No daily commit landed on ..." | Your inbox |

The daily workflow fires at eight windows a day. One of the first six is chosen from the date, so the time moves around. If that run is dropped by GitHub, delayed, or fails, every later window tries again until the day lands. A day that has landed is never built twice.

## If you get a "No daily commit landed" issue

Almost always the Claude token has expired or the plan hit a usage limit. To refresh the token, in any terminal on your laptop:

```bash
claude setup-token
```

Then paste what it prints into GitHub: repo Settings, Secrets and variables, Actions, `CLAUDE_CODE_OAUTH_TOKEN`, Update. The next window picks the day up.

## Running a day by hand

In Claude Code, inside a clone of this repo, type `/daily-build`. Same rules, same checks. It commits but does not push, so push afterwards.

## Pausing

Actions tab, Daily build, the three dots, Disable workflow. Turn it back on the same way. A paused stretch leaves a gap in the history, which is fine.

## Optional switch 1: a live website

Turns the README and the tool pages into a small website at `roshanm20.github.io/decision-lab`, which is nicer to send a recruiter than a code page.

1. Repo Settings, Pages, Source: **GitHub Actions**.
2. Repo Settings, Secrets and variables, Actions, **Variables** tab, New repository variable: name `PAGES_ENABLED`, value `true`.

The site workflow then publishes after every daily run.

## Optional switch 2: keep your profile page current

Your profile page is the first thing anyone sees, and it can carry a small section about this repo that updates itself every Monday.

1. Create a fine-grained token: GitHub Settings, Developer settings, Personal access tokens, **Fine-grained tokens**, Generate new token. Repository access: **Only select repositories**, pick `roshanm20/roshanm20`. Repository permissions: **Contents, Read and write**. Nothing else.
2. In this repo: Settings, Secrets and variables, Actions, New repository secret, name `PROFILE_TOKEN`, paste the token.
3. In your profile README, add these two lines wherever you want the section to appear:

```
<!-- DECISION-LAB:START -->
<!-- DECISION-LAB:END -->
```

The Monday workflow fills in the space between them. It never touches anything outside those two lines, and it does nothing if they are missing.

## Journal notes

Drop a rough note in `journal/inbox` whenever a real decision happens at Nayrix or on CompEdge. Bullet points are fine. `journal/inbox/_template.md` has prompts. Thursday turns the oldest note into a decision record, using only what the note says.

**The journal folder is public.** A note can be read by anyone as soon as it is pushed, before any record is made from it. Never put a client name or an exact confidential figure in it. Use a range or a ratio instead.

## Changing direction

| What you want | Where |
| --- | --- |
| What gets built next | `ROADMAP.md`, move items up or add new ones |
| The quality bar | `STANDARDS.md` |
| What a commit has to pass | `scripts/check.py` |
| Which group gets which day | `scripts/pick_track.py` |
| The possible run times | `WINDOWS` in `scripts/should_run_now.py`, and the matching crons in the workflow |
