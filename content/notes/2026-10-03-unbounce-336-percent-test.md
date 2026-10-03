---
title: Does Unbounce's 336 percent test win survive its own numbers
date: 2026-10-03
track: note
summary: The published 336 percent lift rests on one conversion in the control arm, and re-run with this repo's ab-test tool it is not significant at the 95 percent level, so the page's conclusion is not proven by its own data.
sources: 1
---

One question. A well-known Unbounce case study says a single A/B test lifted conversions by 336 percent at 95.2 percent confidence. Does that conclusion hold when I redo the arithmetic with [`ab-test`](../../docs/tools/ab-test.md)?

## What the page says

The case study is by Dustin Sparks, published 11 November 2013 (Unbounce, checked 2026-10-03). It reports:

| Item | Published value |
| --- | --- |
| Traffic | "exactly 120 experiments", described as pure PPC visits |
| Duration | 23 days |
| Control conversion rate | 3.12% |
| Challenger conversion rate | 13.64% |
| Improvement | 336% |
| Confidence | 95.2% |

The challenger removed the main navigation, changed the theme and used a larger human figure. The page's hypothesis also mentions moving the form above the fold. I read "experiments" as visits, so 120 visits in total across both versions. That is my reading. The page does not say how the 120 visits split between the two versions, and it does not print conversion counts.

## Recovering the counts

I looked for whole numbers that fit every published figure. I tried every split of 120 visits into a control size and a challenger size, and every conversion count in each arm, and kept the ones that round to 3.12% and 13.64%. Exactly one fits: control 1 conversion from 32 visits (3.125%), challenger 12 from 88 (13.636%). The relative lift then comes to 336.4%, which matches the page's 336%.

This is my reconstruction, not a published fact. It is unusual to split traffic 32 to 88, and the author may have counted differently. But the fit is exact on three published numbers at once, and no other split in my search worked. The inputs are in [the JSON file next to this note](2026-10-03-unbounce-336-percent-test.json).

## Re-running it

```
$ python -m decisionlab ab-test analyze --control 32 1 --variant 88 12 --mde 0.05
Control : 1 / 32 = 3.12%
Variant : 12 / 88 = 13.64%
Difference : +10.51 points (+336.4% relative)
95% interval on the difference : +1.14 to +19.88 points
p-value : 0.1014
Warning: fewer than 10 conversions in an arm. The approximation behind these numbers is shaky here.

No reliable difference, and the test was too small to settle it. You care about changes of 5.00 points, but this sample could only reliably detect about 12.19. This is 'we could not tell', not 'there is no effect'. Run longer or test a bolder change.
```

The tool's two-sided p-value is 0.10, so not significant at 0.05. The tool also warns that the approximation is shaky with so few conversions. So I checked with Fisher's exact test, which does not need the approximation. I computed it separately with a short script using the hypergeometric distribution. It gives a two-sided p of 0.181 and a one-sided p of 0.089.

## Where 95.2 percent might come from

The pooled z-test gives z = 1.64. A one-sided reading of that is 94.9 percent confidence, close to the page's 95.2. I do not know what calculator Unbounce used, so I only say the figure looks like a one-sided confidence. A one-sided test asks "is the challenger better", and it is only fair if you committed to ignoring the case where it is worse. With 12 conversions against 1, calling that confidence "95 percent" and treating it like a normal significance level overstates the evidence.

## How fragile the lift is

The whole 336 percent depends on one visitor converting in the control. I changed only the control count:

| Control conversions | Control rate | Difference | p-value |
| --- | --- | --- | --- |
| 0 | 0.00% | +13.64 points | 0.0277 |
| 1 | 3.12% | +10.51 points | 0.1014 |
| 2 | 6.25% | +7.39 points | 0.2650 |
| 3 | 9.38% | +4.26 points | 0.5325 |

One more converting visitor in the control cuts the lift from 336 percent to about 118 percent and moves p from 0.10 to 0.27. The 95 percent interval on the difference runs from +1.14 to +19.88 points, which is too wide to plan anything on. The challenger may well be better. The data cannot show it.

## What I think

The conclusion "the challenger won" does not hold on this evidence. The direction may be right, and removing navigation on a paid landing page is a plausible idea. But 13 conversions in total cannot support a headline of 336 percent. The honest reading of the page is "promising, run it longer". The page also says the original rate was under 2 percent before earlier best-practice fixes took it to 3.12 percent. That is the baseline the 336 percent is measured against, and with one conversion in 32 visits it is a very soft number.

This is a 2013 post and one case. I am not saying Unbounce's later work has the same problem, or that the author acted in bad faith. Case studies are written to be read quickly, and counts are often left out. The lesson is for the reader: before quoting a lift, ask for the counts.

## What would change my mind

- If the full test export shows a different split and more conversions than my reconstruction, for example 120 visits per arm, then the 336 percent claim would be a different test from the one I re-ran, and I would redo it.
- If the author followed a stated one-sided plan before the test began, and committed to a fixed 120-visit stopping point, then 94.9 to 95.2 percent one-sided confidence would be a fair claim, though still weak.
- If the same change was tested again on this landing page and held at a similar size with several hundred visits per arm, I would accept the direction as real.
- If another search finds a different set of whole numbers that matches the published rates, I would drop my reconstruction. I only searched splits of exactly 120 visits. If the 120 is not the total across both arms, the reconstruction fails.

## Sources

- Dustin Sparks, "How a Single A/B Test Increased Conversion by 336%", Unbounce, 11 November 2013, checked 2026-10-03. https://unbounce.com/a-b-testing/how-a-single-a-b-test-increased-conversions/
