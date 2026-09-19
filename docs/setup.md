# Setup

One time setup. Takes about fifteen minutes. After this the repo runs itself every morning at 07:00 IST.

## 1. Create the repo

It has to be **public**, otherwise none of this shows on your profile.

The git history is already in the folder you unzipped, with two commits authored as you, so there is no `git init` to run. Check it first:

```bash
git log --pretty=format:'%h %an <%ae> %s'
```

Both lines should say `Muhammed Roshan M <muhammedroshanmangat@gmail.com>`. That author email is what decides whether these commits count on your contribution graph.

Then, with the GitHub CLI:

```bash
gh repo create decision-lab --public --source . --remote origin \
  --description "Business intelligence, AI product decisions, and how companies make money. One worked piece a day." \
  --push
```

Or create it in the browser at github.com/new, empty, no README, and then:

```bash
git remote add origin https://github.com/roshanm20/decision-lab.git
git push -u origin main
```

Add repository topics once it is up: `business-intelligence`, `product-management`, `ai-products`, `analytics`, `case-studies`. Topics are how people find it.

## 2. Check the commit email

This is the step that decides whether the daily commits show on your contribution graph. GitHub only counts a commit if the **author email is verified on your account**.

Go to github.com/settings/emails and confirm `muhammedroshanmangat@gmail.com` is listed and verified. If you would rather use a different verified address, change the two lines in `.github/workflows/daily-build.yml` under "Set the commit identity".

If you have "Keep my email addresses private" switched on, use your GitHub noreply address instead. It is shown on that settings page and looks like `163342876+roshanm20@users.noreply.github.com`. That one also counts on the graph.

## 3. Install the Claude GitHub App

Install it on this repository: https://github.com/apps/claude

It needs read and write on Contents, Issues, and Pull requests.

## 4. Add the authentication secret

This uses your Claude subscription. It is not an API key and it does not put anything on pay per use billing. Runs draw on the plan you already pay for.

On your machine, in any terminal:

```bash
claude setup-token
```

It opens a browser, you approve, and it prints a long lived token. Copy it. Then:

```bash
gh secret set CLAUDE_CODE_OAUTH_TOKEN --repo roshanm20/decision-lab
```

Paste the token when it asks. In the browser instead: Settings, Secrets and variables, Actions, New repository secret, named exactly `CLAUDE_CODE_OAUTH_TOKEN`.

That is the only credential the workflow needs. The token is tied to your subscription, so if you ever change plans, regenerate it the same way.

## 5. Test it before trusting it

Do not wait for the cron. Trigger it by hand:

```bash
gh workflow run "Daily build" --repo roshanm20/decision-lab
gh run watch --repo roshanm20/decision-lab
```

Then read what it produced, properly. The first run is the one that tells you whether the standards file is doing its job. If the piece is thin or generic, tighten `STANDARDS.md` and run it again. That file is the control surface for the whole thing.

## 6. Running it by hand, with no setup at all

You do not need any of the above to use this. In the repo folder on your machine:

```bash
claude
```

then type:

```
/daily-build
```

Same skill, same standards, same rotation, running on your subscription through the CLI. It writes the piece and commits it with your own git identity.

This is worth knowing for two reasons. It is how you catch up a day the schedule missed, and it is how you check what a change to `STANDARDS.md` does before letting it run unattended. The Action is only the unattended version of this command.

## 7. Leave notes for the Thursday piece

Thursday is the track that makes this repo yours rather than generic. Drop a rough note in `journal/inbox` whenever a real decision gets made at Nayrix, on CompEdge, or on any project. Bullet points are fine, voice-to-text is fine. `journal/inbox/_template.md` has the prompts.

The run uses only what your note says. If the note has no numbers, the record ends up with a list of questions about your own note instead of invented detail. That is deliberate, and those questions are worth answering while the decision is fresh.

If the inbox is empty on a Thursday, it falls back to an outside case note from the backlog. Nothing breaks, you just get a weaker piece that week.

## 8. Turn the schedule on

The crons are already in the workflow. Nothing to switch on, but four things are worth knowing.

**It lands at a different time every day.** The workflow is scheduled in six windows, at 01:17, 04:17, 07:17, 10:17, 13:17 and 16:17 UTC. A gate step works out which one belongs to today by hashing the date, and the other five exit in seconds. The chosen window then waits a further random-looking interval of up to 45 minutes, drawn from the same hash. See it for yourself:

```bash
python scripts/should_run_now.py --preview 14
```

It is deterministic rather than actually random, on purpose. Real randomness per run would sometimes fire two windows on the same day and sometimes none. This way exactly one runs, and the time still moves around by fifteen hours across the week.

**Scheduled workflows only run from the default branch**, so the workflow file has to be on `main`.

**GitHub disables scheduled workflows in public repos after 60 days with no repository activity.** Committing daily prevents it, but if you pause for two months you will have to re-enable it in the Actions tab.

**Runs can be late** when GitHub's queues are busy. With the random wait on top, the commit time is a range, not a promise.

## 9. The weekly review reaches your inbox

A second workflow, `weekly-review-issue.yml`, opens an issue every Sunday at 21:00 IST listing the week's output with a checklist of what to inspect. GitHub emails you about issues on your own repositories, so that is how the review lands in your inbox without this repo holding any email credential. Closing the issue is the signal that you reviewed the week.

There is also a one-off audit set up on the Claude side for 26 September, which reads the repo, checks it against its own standards, and emails you a verdict on whether the first week was worth it. That one is blunt by design.

## Changing things later

| What you want | Where to change it |
| --- | --- |
| The times it can run | the `WINDOWS` list in `scripts/should_run_now.py`, in UTC hours, plus the matching `cron` lines in the workflow |
| How far the time wanders | `MAX_EXTRA_SLEEP` in `scripts/should_run_now.py` |
| Which track runs on which day | the `TRACKS` dictionary in `scripts/pick_track.py` |
| The quality bar | `STANDARDS.md`. This is the file that matters |
| How a day is run | `.claude/skills/daily-build/SKILL.md` |
| Topics | `BACKLOG.md` |
| The model | add a `--model` line under `claude_args` in the workflow. There is a commented example there |

## Cost control

Runs draw on your Claude plan, not on metered billing. If you want to reduce how much each run does anyway, the levers are `--max-turns` in the workflow, pinning a smaller model, and cutting the cron to weekdays only with `cron: "30 1 * * 1-5"`.

## Pausing it

```bash
gh workflow disable "Daily build" --repo roshanm20/decision-lab
```

Do this when you are heads down on CAT prep or client work. A paused month with a clean history reads better than a month of filler.
