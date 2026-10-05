# Funnel step conversion and biggest leak

**For:** BI analysts, growth and product teams who read funnel charts and have to say which step to fix.

**Command:** `python -m decisionlab funnel FILE.csv`

## The problem it solves

A funnel chart shows 100%, 24%, 15%, 6% and everyone points at the smallest bar. But those percentages are measured from the top, so they only say how many users are left, not how well each step did against the step before it. And each step rate comes from a sample of users, so the step that looks worst may be no different from the second worst.

This tool shows each step against the one before it, puts an interval on that rate, names the step with the lowest rate, and says whether the data can really tell it apart from the next lowest.

## Run it

```bash
python -m decisionlab funnel counts.csv
python -m decisionlab funnel events.csv --steps visit,signup,paid
python -m decisionlab funnel counts.csv --confidence 0.9
python -m decisionlab funnel counts.csv --markdown
```

Two input shapes, picked from the header row. Lines starting with `#` are skipped.

- Step counts: columns `step` and `users`, one row per step in funnel order.
- Event log: columns `user_id` and `event`. Pass the funnel order with `--steps`. A user counts at a step only if they have done every step up to it. Repeat events are counted once.

## Example, real output

[`examples/funnel_steps.csv`](../../examples/funnel_steps.csv) holds invented counts for a made-up checkout. It is illustrative, not real data. One step has a blank count on purpose.

```
$ python -m decisionlab funnel examples/funnel_steps.csv
10,000 users at the top, 610 at the end, across 5 steps
Data problems:
  row 6: no count for 'Enter payment', step skipped. The next step is measured against the last step that has a count.

Step             Users  Step rate    95% interval   Lost  Of top
--------------  ------  ---------  --------------  -----  ------
Product page    10,000                                      100%
Add to cart      2,400      24.0%  23.2% to 24.8%  7,600   24.0%
Start checkout   1,500      62.5%  60.5% to 64.4%    900   15.0%
Enter address    1,260      84.0%  82.1% to 85.8%    240   12.6%
Pay                610      48.4%  45.7% to 51.2%    650    6.1%

End to end: 6.1% of users reach Pay, 95% interval 5.6% to 6.6%.

Biggest leak: Product page to Add to cart, where only 24.0% carry on (7,600 of 10,000 lost).
Next lowest: Enter address to Pay at 48.4%. The intervals do not overlap, so this step is probably the weakest.
```

The same idea from an event log. [`examples/funnel_events.csv`](../../examples/funnel_events.csv) is also invented. It has a few users with a missing `activate` event and some `page_view` rows that are not part of the funnel.

```
$ python -m decisionlab funnel examples/funnel_events.csv --steps visit,signup,activate,add_payment,paid
1,200 users at the top, 133 at the end, across 5 steps
Data problems:
  12 event rows are not in --steps and were ignored
  3 users did a later step without an earlier one. They are counted only up to the step before the gap. If tracking is broken at that step, fix that before trusting this funnel

Step         Users  Step rate    95% interval  Lost  Of top
-----------  -----  ---------  --------------  ----  ------
visit        1,200                                     100%
signup         571      47.6%  44.8% to 50.4%   629   47.6%
activate       399      69.9%  66.0% to 73.5%   172   33.2%
add_payment    216      54.1%  49.2% to 59.0%   183   18.0%
paid           133      61.6%  54.9% to 67.8%    83   11.1%

End to end: 11.1% of users reach paid, 95% interval 9.4% to 13.0%.

Biggest leak: visit to signup, where only 47.6% carry on (629 of 1,200 lost).
Next lowest: activate to add_payment at 54.1%. The intervals overlap, so this data cannot say it is worse than the next one.
```

## How to read it

Step rate is users at the step divided by users who entered it. Lost is how many dropped there. Of top is the usual funnel chart number.

In the first run, the skipped `Enter payment` step means the last row compares Pay with Enter address, so 48.4% is the rate over both steps together. The biggest leak is the first step, and its interval is far from the next lowest, so that call is safe on this data.

In the second run, the lowest rate is the first step at 47.6%, but add payment at 54.1% has an interval that overlaps with it. Fixing the second may be as worth doing as the first. The tool says so rather than naming a winner.

The three users with a missing `activate` event matter too. They are cut off at that step, so they are missing from `activate` and every step after it. The warning is there so someone checks the tracking.

## The method

- Step rate = users at the step / users at the previous step.
- Interval: Wilson score interval, which stays inside 0 to 100% and works at small counts, unlike the plain normal interval.
- The biggest leak is the step with the lowest rate. It is separable from the next lowest if their two intervals do not overlap.
- Counts that rise from one step to the next are refused, because a user cannot reach a step without the one before it.

Check by hand: 50 of 100 at 95% gives centre 0.5 and half width 0.0962, so 40.4% to 59.6%. And 0 of 10 gives an upper bound of z squared / (n + z squared) = 27.8%. The tests check both.

## What it does not do

- It names the step with the lowest rate. A step with a modest rate but a huge number of users lost can matter more to the business, and the table shows Lost so you can judge that.
- The overlap check is a rough guide. The steps are nested groups of the same users, so they are not independent samples, so treat the overlap check as a guide, not a test.
- It does not check the time order of events. A user who paid before signing up counts as having done both.
- Steps are matched by exact name, with no time window. A user who does the steps a month apart counts the same as one who does them in a minute.
- No segments yet, so it cannot say where two groups of users differ.
- Event names with commas cannot be passed to `--steps`.
- It warns when fewer than 30 users enter a step, and when no one does, since the interval is wide or missing there. Those are warnings only, nothing is dropped.
- The interval treats users as a simple random sample. Counts of sessions instead of users, or users who can enter twice, break that.
