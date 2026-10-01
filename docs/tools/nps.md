# NPS with a confidence interval and segment comparison

**For:** product managers and CX analysts who report Net Promoter Score and have to say whether a move is real.

**Command:** `python -m decisionlab nps SURVEY.csv`

## The problem it solves

NPS is reported as one number, and a move from 31 to 36 gets called an improvement. But NPS is the promoter share minus the detractor share, each measured on a sample, so it is noisy. With a few hundred replies the interval around it is often ten points either side or more. Many of the "gains" and "drops" on a dashboard are inside that noise.

This tool takes raw 0 to 10 replies, scores NPS, puts an interval on it, and tests whether two segments (two plans, two regions, this quarter and last) really differ.

## Run it

```bash
python -m decisionlab nps survey.csv
python -m decisionlab nps survey.csv --compare Starter Pro   # needed when there are three or more segments
python -m decisionlab nps survey.csv --confidence 0.9
python -m decisionlab nps survey.csv --markdown
```

The CSV needs a `score` column with whole numbers from 0 to 10. An optional `segment` column splits the replies into groups. Lines starting with `#` are skipped. With exactly two segments the comparison runs by itself.

## Example, real output

[`examples/nps_survey.csv`](../../examples/nps_survey.csv) is invented replies for a made-up product. It is illustrative, not survey data.

```
$ python -m decisionlab nps examples/nps_survey.csv
Segment  Replies  Promoters  Passives  Detractors  NPS  95% interval
-------  -------  ---------  --------  ----------  ---  ------------
Starter      120        32%       38%         30%    2     -12 to 16
Pro           90        46%       37%         18%   28      12 to 43

Starter minus Pro: -26 points, 95% interval -47 to -5, p = 0.014. The interval on the difference excludes zero, so the gap is unlikely to be noise.
```

## How to read it

Starter scores 2 and Pro scores 28. Each has an interval of about 30 points wide, even with 120 and 90 replies. Starter could really be anywhere from -12 to 16. The gap of 26 points is large enough that its own interval, -47 to -5, stays below zero, so these two segments probably do differ.

Now take a change of 5 points between two quarters of 120 replies each. The interval on that change would be roughly plus or minus 20, so the survey could not tell it apart from no change at all. The tool says so in that case.

A 90 percent interval is narrower:

```
$ python -m decisionlab nps examples/nps_survey.csv --confidence 0.9
Segment  Replies  Promoters  Passives  Detractors  NPS  90% interval
-------  -------  ---------  --------  ----------  ---  ------------
Starter      120        32%       38%         30%    2     -10 to 13
Pro           90        46%       37%         18%   28      15 to 41

Starter minus Pro: -26 points, 90% interval -44 to -9, p = 0.014. The interval on the difference excludes zero, so the gap is unlikely to be noise.
```

## The method

Promoters score 9 or 10, passives 7 or 8, detractors 0 to 6. With p the promoter share, d the detractor share and n replies:

- NPS = (p - d) x 100
- variance of (p - d) = (p + d - (p - d)^2) / n, treating the three groups as one multinomial draw
- interval = NPS plus or minus z x 100 x sqrt(variance)
- difference between two segments: z-test with the two variances added

Check by hand: 50 promoters, 30 passives and 20 detractors out of 100 give NPS 30, variance 0.0061, and a 95 percent interval of 14.7 to 45.3. The tests check exactly this.

MeasuringU's write-up of NPS statistics recommends an adjusted-Wald interval for better coverage ([measuringu.com/statistical-analysis-nps](https://measuringu.com/statistical-analysis-nps/), checked 2026-10-01). That page does not give the adjustment constants, so this tool uses the plain Wald interval and does not claim to match theirs.

## What it does not do

- It uses the plain Wald interval, which is unreliable for small samples and for scores near -100 or 100. The tool warns under 30 replies in a segment. It does not use the adjusted-Wald method that MeasuringU recommends.
- It treats the replies as a simple random sample. A survey that only the happiest or angriest users answer is biased, and no interval fixes that.
- It compares two independent groups. The same people surveyed in two waves are paired, and this test ignores that.
- It tests one pair at a time. Comparing many segments and picking the one that stands out will find false differences, and there is no correction for that.
- The scale cut-offs (9 and 10, 7 and 8, 0 to 6) are the standard ones and are fixed.
