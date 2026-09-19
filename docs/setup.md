# Setup

One time setup. Takes about fifteen minutes. After this the repo runs itself every morning at 07:00 IST.

## 1. Create the repo

It has to be **public**, otherwise none of this shows on your profile.

With the GitHub CLI, from inside this folder:

```bash
git init
git add -A
git commit -m "Set up the repo, standards, rotation, and daily workflow"
gh repo create decision-lab --public --source . --remote origin \
  --description "Business intelligence, AI product decisions, and how companies make money. One worked piece a day." \
  --push
```

Or create it in the browser at github.com/new and then:

```bash
git init
git add -A
git commit -m "Set up the repo, standards, rotation, and daily workflow"
git branch -M main
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

Two options. The first one uses your Claude subscription and costs nothing extra, so start there.

**Option A, subscription token.** On your machine, with Claude Code installed:

```bash
claude setup-token
```

Copy the token it prints. Then:

```bash
gh secret set CLAUDE_CODE_OAUTH_TOKEN --repo roshanm20/decision-lab
```

Paste the token when it asks. Or add it in the browser under Settings, Secrets and variables, Actions, New repository secret, named exactly `CLAUDE_CODE_OAUTH_TOKEN`.

**Option B, API key.** Get a key from platform.claude.com, set it as `ANTHROPIC_API_KEY`, and in the workflow file change

```yaml
claude_code_oauth_token: ${{ secrets.CLAUDE_CODE_OAUTH_TOKEN }}
```

to

```yaml
anthropic_api_key: ${{ secrets.ANTHROPIC_API_KEY }}
```

This one bills per run.

## 5. Test it before trusting it

Do not wait for the cron. Trigger it by hand:

```bash
gh workflow run "Daily build" --repo roshanm20/decision-lab
gh run watch --repo roshanm20/decision-lab
```

Then read what it produced, properly. The first run is the one that tells you whether the standards file is doing its job. If the piece is thin or generic, tighten `STANDARDS.md` and run it again. That file is the control surface for the whole thing.

## 6. Turn the schedule on

The cron is already in the workflow. Two things to know about GitHub's scheduler:

- Scheduled workflows only run from the default branch, so the workflow file has to be on `main`.
- GitHub disables scheduled workflows in public repos after 60 days with no repository activity. Since this commits daily, that will not trigger, but if you pause it for two months you will have to re-enable it in the Actions tab.

Runs can be a few minutes late when GitHub's queues are busy. That is normal.

## Changing things later

| What you want | Where to change it |
| --- | --- |
| The time it runs | the `cron` line in `.github/workflows/daily-build.yml`. It is in UTC, so subtract 5:30 from the IST time you want |
| Which track runs on which day | the `TRACKS` dictionary in `scripts/pick_track.py` |
| The quality bar | `STANDARDS.md`. This is the file that matters |
| How a day is run | `.claude/skills/daily-build/SKILL.md` |
| Topics | `BACKLOG.md` |
| The model | add a `--model` line under `claude_args` in the workflow. There is a commented example there |

## Cost control

If you are on the subscription token, runs draw on your existing plan. If you move to an API key, the levers are `--max-turns` in the workflow, a smaller model, and cutting the cron to weekdays only with `cron: "30 1 * * 1-5"`.

## Pausing it

```bash
gh workflow disable "Daily build" --repo roshanm20/decision-lab
```

Do this when you are heads down on CAT prep or client work. A paused month with a clean history reads better than a month of filler.
