# RICE prioritisation with a fragility check

**For:** product managers, and anyone who has to defend the order of a backlog in a meeting.

**Command:** `python -m decisionlab rice BACKLOG.csv`

## The problem it solves

RICE scoring (Reach x Impact x Confidence / Effort, a method from Intercom's product team) turns a backlog argument into arithmetic. The weak point is Confidence, which is nearly always a guess. A backlog can look well ordered and still rest entirely on two optimistic guesses.

So the tool does one more thing. For each item it asks: if this one confidence guess were 30 percent too high, would the item fall two or more places? Items that would are marked fragile. If your top three are fragile, the useful next step is to firm up those guesses, not to argue about the order.

Reach is a guess too, and often a shakier one than confidence: nobody has run the feature yet, so "6,000 users a month" is as much an estimate as "90% confident". `--check-reach` runs the same test against reach.

## Run it

```bash
python -m decisionlab rice backlog.csv
python -m decisionlab rice backlog.csv --markdown --top 5   # paste into a doc or a ticket
python -m decisionlab rice backlog.csv --check-reach         # also test reach guesses, not just confidence
python -m decisionlab rice backlog.csv --shade 0.5 --drop 1  # stress test: a bigger shade, a lower bar
```

The CSV needs the columns `name, reach, impact, confidence, effort`. Impact uses the scale 3, 2, 1, 0.5, 0.25. Confidence can be written as 80 or 0.8. Effort is in person-months.

`--shade` (default 0.3) is the fraction a guess is shaded down by in the test. `--drop` (default 2) is how many places an item must fall to be marked fragile. Both must make sense: shade between 0 and 1, drop at least 1. The tool refuses anything else with a clear error.

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

Fragile at the top on confidence: Dark mode. If the confidence guess on this item were 30% lower, it would drop 2 or more places. Firm up that guess before committing to the order.

Input warnings:
  SSO for enterprise accounts: confidence of 95% or more is rarely earned
```

## How to read it

Dark mode ranks third, but only because of a 90 percent confidence guess on a low-impact item with very high reach. Shade that guess by 30 percent and it drops two places, below Slack alerts and the onboarding checklist. So the honest statement to the team is: the top two are solid, and third place depends on whether we really believe dark mode will be used by 6,000 people.

## Checking reach too

Confidence is not the only guess in the formula. Reach is one as well, and for a feature nobody has shipped yet, it can be just as shaky. `--check-reach` runs the same shade-and-see test against reach and adds a column for it.

```
$ python -m decisionlab rice examples/rice_backlog.csv --check-reach
Rank  Item                                     Reach  Impact  Confidence  Effort   RICE  Fragile  Fragile (reach)
----  ---------------------------------------  -----  ------  ----------  ------  -----  -------  ---------------
   1  Bulk export to Excel                     1,200       2         90%       1  2,160
   2  Saved filters on the reports page        4,000       1         80%       2  1,600
   3  Dark mode                                6,000    0.25         90%     1.5    900  falls 2  falls 2
   4  Slack alerts when a metric moves         2,500       2         50%       3    833
   5  Onboarding checklist for new workspaces    900       3         60%       2    810
   6  Scheduled PDF reports                    1,500       2         70%       4    525
   7  SSO for enterprise accounts                300       3         95%       5    171

Fragile at the top on confidence: Dark mode. If the confidence guess on this item were 30% lower, it would drop 2 or more places. Firm up that guess before committing to the order.
Fragile at the top on reach: Dark mode. If the reach guess on this item were 30% lower, it would drop 2 or more places. Firm up that guess before committing to the order.

Input warnings:
  SSO for enterprise accounts: confidence of 95% or more is rarely earned
```

Dark mode is fragile both ways here, which is worse than it looks from the confidence check alone. The item is not just a guess about how sure the team is, it is a guess about reach too, and either one being wrong is enough to drop it out of the top three.

## Changing the shade and the drop threshold

The 30 percent shade and the two-place drop are defaults, not the only sensible values. A team that wants a harsher stress test can lower the drop threshold or raise the shade:

```
$ python -m decisionlab rice examples/rice_backlog.csv --shade 0.5 --drop 1
Rank  Item                                     Reach  Impact  Confidence  Effort   RICE  Fragile
----  ---------------------------------------  -----  ------  ----------  ------  -----  -------
   1  Bulk export to Excel                     1,200       2         90%       1  2,160  falls 1
   2  Saved filters on the reports page        4,000       1         80%       2  1,600  falls 3
   3  Dark mode                                6,000    0.25         90%     1.5    900  falls 3
   4  Slack alerts when a metric moves         2,500       2         50%       3    833  falls 2
   5  Onboarding checklist for new workspaces    900       3         60%       2    810  falls 1
   6  Scheduled PDF reports                    1,500       2         70%       4    525
   7  SSO for enterprise accounts                300       3         95%       5    171

Fragile at the top on confidence: Bulk export to Excel, Saved filters on the reports page, Dark mode. If the confidence guess on any of these were 50% lower, it would drop 1 or more places. Firm up those guesses before committing to the order.

Input warnings:
  SSO for enterprise accounts: confidence of 95% or more is rarely earned
```

At a 50 percent shade and a one-place drop, almost everything moves. That is the point: a very harsh stress test should make most items look fragile, so it is only useful for finding the items that hold up even then. Here nothing does, which says the whole ranking is closer together than the RICE scores suggest.

## What it does not do

- The fragility check shades one item at a time. It does not test what happens when several guesses are wrong together.
- No dependencies between items. If item B needs item A first, RICE will not know.
- `--check-reach` shades reach the same way confidence is shaded, as a straight percentage cut. A reach estimate that is wrong by being the wrong order of magnitude, not just 30 percent off, will not show up as merely fragile, it will just produce a wrong ranking with no warning.
