# RICE prioritisation with a fragility check

**For:** product managers, and anyone who has to defend the order of a backlog in a meeting.

**Command:** `python -m decisionlab rice BACKLOG.csv`

## The problem it solves

RICE scoring (Reach x Impact x Confidence / Effort, a method from Intercom's product team) turns a backlog argument into arithmetic. The weak point is Confidence, which is nearly always a guess. A backlog can look well ordered and still rest entirely on two optimistic guesses.

So the tool does one more thing. For each item it asks: if this one confidence guess were 30 percent too high, would the item fall two or more places? Items that would are marked fragile. If your top three are fragile, the useful next step is to firm up those guesses, not to argue about the order.

## Run it

```bash
python -m decisionlab rice backlog.csv
python -m decisionlab rice backlog.csv --markdown --top 5   # paste into a doc or a ticket
```

The CSV needs the columns `name, reach, impact, confidence, effort`. Impact uses the scale 3, 2, 1, 0.5, 0.25. Confidence can be written as 80 or 0.8. Effort is in person-months.

## Example, real output

The backlog in [`examples/rice_backlog.csv`](../../examples/rice_backlog.csv) is invented, for a made-up analytics product.

```
$ python -m decisionlab rice examples/rice_backlog.csv
Rank  Item                                     Reach  Impact  Confidence  Effort   RICE  Fragile
----  ---------------------------------------  -----  ------  ----------  ------  -----  -------
   1  Bulk export to Excel                     1,200       2         90%       1  2,160
   2  Saved filters on the reports page        4,000       1         80%       2  1,600
   3  Dark mode                                6,000    0.25         90%     1.5    900  falls 2
   4  Slack alerts when a metric moves         2,500       2         50%       3    833
   5  Onboarding checklist for new workspaces    900       3         60%       2    810
   6  Scheduled PDF reports                    1,500       2         70%       4    525
   7  SSO for enterprise accounts                300       3         95%       5    171

Fragile at the top: Dark mode. If the confidence guess on this item were 30% lower, it would drop 2 or more places. Firm up that guess before committing to the order.

Input warnings:
  SSO for enterprise accounts: confidence of 95% or more is rarely earned
```

## How to read it

Dark mode ranks third, but only because of a 90 percent confidence guess on a low-impact item with very high reach. Shade that guess by 30 percent and it drops two places, below Slack alerts and the onboarding checklist. So the honest statement to the team is: the top two are solid, and third place depends on whether we really believe dark mode will be used by 6,000 people.

## What it does not do

- The fragility check shades one item at a time. It does not test what happens when several guesses are wrong together.
- It checks Confidence only. Reach estimates are often just as shaky.
- No dependencies between items. If item B needs item A first, RICE will not know.
- The 30 percent shade and the two-place threshold are fixed. They should become flags.
