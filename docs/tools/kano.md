# Kano classifier for feature surveys

**For:** product managers who survey customers about features and have to decide which ones to build first.

**Command:** `python -m decisionlab kano SURVEY.csv`

## The problem it solves

A team asks "would you like feature X?", hears yes from almost everyone, and builds it as if it would delight. But a yes does not say what happens when the feature is missing. Some features are expected, so having them earns little and lacking them costs a lot. Others are liked but not missed.

The Kano survey asks two questions per feature. The functional question is "if the product has this, how do you feel?". The dysfunctional question is "if it does not, how do you feel?". The pair of answers puts each respondent's view into one category. This tool does the classifying and counting, and says when the result is a tie or too close to call.

## Run it

```bash
python -m decisionlab kano survey.csv
python -m decisionlab kano survey.csv --markdown
```

The CSV needs three columns: `feature`, `functional` and `dysfunctional`. One row is one respondent's answers for one feature. Answers are `like`, `must-be`, `neutral`, `live-with` or `dislike`, or the numbers 1 to 5 in that order. Lines starting with `#` are skipped.

## Example, real output

[`examples/kano_survey.csv`](../../examples/kano_survey.csv) is invented answers for a made-up product. It is illustrative, not survey data.

```
$ python -m decisionlab kano examples/kano_survey.csv
Feature              Replies   A   O   M   I  R  Q  Category                          Share  Better  Worse
-------------------  -------  --  --  --  --  -  -  --------------------------------  -----  ------  -----
Dark mode                 80  44  10   4  22  0  0  attractive                          55%    0.68  -0.17
Two-factor login          90   6  12  60  10  0  2  must-be                             67%    0.20  -0.82
Bulk export              100  16  44  20  18  2  0  one-dimensional                     44%    0.61  -0.65
Weekly digest email       95  12  10  10  55  8  0  indifferent                         58%    0.25  -0.23
Offline sync              48  20  20   0   8  0  0  attractive/one-dimensional (tie)    42%    0.83  -0.42

A attractive, O one-dimensional, M must-be, I indifferent, R reverse, Q questionable.

Notes:
  Offline sync: attractive and one-dimensional tie, 20 each, so there is no single category.
```

## How to read it

The columns A to Q count respondents by code. The category is the code most respondents gave. Share is that code's share of replies.

- **Two-factor login** is must-be. Having it adds little (Better 0.20) but lacking it hurts a lot (Worse -0.82). Build it, but do not expect it to sell.
- **Dark mode** is attractive. Few would mind its absence (Worse -0.17), and many would be pleased by it.
- **Bulk export** is one-dimensional. More of it means more satisfaction, and lacking it hurts. Note that its leading share is only 44 percent.
- **Weekly digest email** is indifferent. Most respondents do not care either way.
- **Offline sync** has two codes tied. The tool does not pick one. It needs more replies, or a decision made knowing it sits between delighter and performance feature.

Better is (A + O) / (A + O + M + I). It is how much satisfaction rises if the feature is added. Worse is -(O + M) / (A + O + M + I). It is how much satisfaction falls if the feature is missing. Reverse and questionable answers are left out of both.

## The method

Each pair of answers goes through the standard 5 by 5 evaluation table. Rows are the functional answer and columns are the dysfunctional one:

| Functional \ Dysfunctional | like | must-be | neutral | live-with | dislike |
| --- | --- | --- | --- | --- | --- |
| like | Q | A | A | A | O |
| must-be | R | I | I | I | M |
| neutral | R | I | I | I | M |
| live-with | R | I | I | I | M |
| dislike | R | R | R | R | Q |

The table is Table 3 of Kano-based release planning work on arXiv ([arxiv.org/abs/1901.05130](https://arxiv.org/abs/1901.05130), checked 2026-10-08). The Better and Worse formulas are as given on [metricgate.com](https://metricgate.com/calculator/kano-model-feature-categorization), checked 2026-10-08. I read the cell letters by hand from the text of the paper's PDF, and the tests compare the code with a copy of the table typed from that reading, so they catch a later slip but do not re-read the paper. Metricgate and Conjointly, which I also opened, do not print the table, so it has one source only.

A feature takes the code with the most respondents. If two or more codes share the top count, the tool reports a tie and picks none. It also notes a feature when the leader is within 10 points of the next code, when a feature has fewer than 30 replies (a floor I chose, not a published rule), and when 10 percent or more of answer pairs are Q.

## What it does not do

- It does not give an interval on the category. A leader at 44 percent of 100 replies could easily be second with another sample. The close-gap note is a rough flag, not a test.
- Critics of the method, as listed by [Conjointly](https://conjointly.com/blog/criticism-of-kano-model) (checked 2026-10-08, and Conjointly disputes some of them), say category assignment is unstable below about 200 respondents, and that the five answer options overlap, since a person can both expect and love a feature. I read the Conjointly page, not the original paper. The tool follows the standard method and does not fix either point.
- The 30-reply warning and the 10-point close-gap flag are my own thresholds.
- It ignores which respondent is which, so it cannot split results by segment. Run it on a file per segment.
- It does not turn categories into a priority order. Combine it with `rice` or your own judgement.
- It handles the five standard answers only. Surveys that use other scales need recoding first.
