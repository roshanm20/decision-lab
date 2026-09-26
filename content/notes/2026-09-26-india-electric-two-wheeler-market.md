---
title: Sizing India's electric two-wheeler market and testing the sizing tool
date: 2026-09-26
track: note
summary: India's electric two-wheeler market was worth roughly 13,700 to 17,800 crore rupees at ex-showroom prices in FY2024-25, but the bigger finding is that this tool's top-down versus bottom-up check only catches a real error when the two chains do not share an input, and here they shared both the units and the price.
sources: 7
---

Two questions, not one. First, what was India's electric two-wheeler (e2W) market worth in FY2024-25, at ex-showroom prices. Second, when I ran [`market-size`](../../docs/tools/market-size.md) on it, the tool said the top-down and bottom-up chains agreed almost exactly. Does that agreement mean the estimate is trustworthy, the way the tool's own docs suggest it should.

## The units, which are well measured

Two numbers are not in dispute, because they come from the two bodies that actually count vehicles.

SIAM, the industry association, reported that 1,96,07,332 two-wheelers were sold in India in FY2024-25, up 9.1 percent, and that "share of EVs in overall two-wheelers have crossed 6% in 2024-25" with e-two-wheeler registrations up 21.2 percent to 11.5 lakh units (SIAM press release, 15 April 2025). Autocar Professional's own analysis of Vahan registration data puts the exact e2W figure at 11,49,307 units for FY2025, against 9,48,508 in FY2024, a match with SIAM's rounder numbers (Autocar Professional, 3 April 2025). The same article breaks the figure down by maker:

| OEM | FY2025 e2W units (Vahan) | Share |
| --- | --- | --- |
| Ola Electric | 3,44,009 | 30% |
| TVS Motor | 2,37,576 | 21% |
| Bajaj Auto | 2,30,808 | 20% |
| Ather Energy | 1,30,945 | 11.4% |
| Hero MotoCorp | 48,673 | 4% |
| Greaves Electric Mobility | 40,162 | 3.5% |
| Bgauss | 17,343 | 1.5% |
| Revolt Motors | 11,564 | 1% |

Source: Autocar Professional, "Two-wheeler share of EV sales grows to 58% in FY2025", 3 April 2025, citing Vahan.

Adding the top four myself gives 9,43,338 units, which is 82.1 percent of the 11,49,307 total, close enough to the article's own "82%" that I trust the arithmetic. That 82.1 percent is the gross-up factor the bottom-up chain needs to go from "the four OEMs anyone naming this market would name" to the whole segment: multiply by 1 divided by 0.821, or 1.2183.

## The price, which nobody publishes directly

Nobody publishes "the e2W market was worth X crore" the way SIAM publishes units. Getting from units to value means picking a price, and this is where the two chains stopped being independent of each other, which matters for what comes next.

I started from list prices, checked on 2026-09-26. For each of the four leading OEMs I took the cheapest and the costliest currently listed variant:

| OEM | Low (INR) | High (INR) | Source |
| --- | --- | --- | --- |
| Ola Electric | 79,999 (S1 Z) | 1,70,499 (S1 Pro+ 5.2 kWh) | olaelectric.com/s1, official price page |
| TVS Motor | 1,19,565 (iQube 2.3 kWh) | 1,75,760 (iQube ST 5.3 kWh) | bikewale.com/tvs-bikes/iqube, "Avg. Ex-Showroom price" |
| Bajaj Auto | 1,19,056 (Chetak 3001) | 1,56,874 (Chetak C3501) | bikewale.com/bajaj-bikes/chetak, "Avg. Ex-Showroom price" |
| Ather Energy | 1,30,283 (450S onwards) | 1,96,273 (450 Apex onwards) | bikewale.com/ather-bikes/450x, "Avg. Ex-Showroom price" |

Weighting each OEM's low and high by its FY2025 unit share gives a blended band of 1,06,500 to 1,72,068 rupees. That band is genuine: it is built from four different companies' price lists.

But a single point estimate inside that band still had to come from somewhere, and picking the middle of a list-price band would have been a guess dressed up as a number. Ola Electric is listed, and its results are filed, not modelled. Its Q4 and FY25 press release states FY25 revenue of 4,645 crore rupees against 3,59,221 units delivered (Ola Electric Mobility Limited, "Q4 & FY25 Press Release", 29 May 2025). Revenue divided by units is 1,29,308 rupees per unit, an actual realised average, not a list price. It sits inside the 1,06,500 to 1,72,068 band, nearer the low end, which makes sense: list prices are for the top variant a showroom pushes, while a revenue-weighted average reflects what people actually bought, discounts included.

I used 1,29,308 as the value in the model and the list-price band as its low and high, in both chains.

## Running the tool

The model is committed at [`2026-09-26-india-electric-two-wheeler-market.json`](2026-09-26-india-electric-two-wheeler-market.json). Real run, unedited:

```
$ python -m decisionlab market-size content/notes/2026-09-26-india-electric-two-wheeler-market.json --simulate 10000
India's electric two-wheeler market, ex-showroom value, FY2024-25
Unit: INR, ex-showroom value

== top down ==
Step                                                          Value  Running total
-------------------------------------------------------  ----------  -------------
Two-wheelers sold in India, FY2024-25                    1.96 crore     1.96 crore
Share of two-wheelers that were electric, FY2024-25              6%      11.5 lakh
Average ex-showroom realisation per e2W unit, FY2024-25   1.29 lakh   14,861 crore
Estimate: 14,861 crore

What moves this estimate most (each assumption at its low and high, others held):
Assumption                                                     At low       At high        Swing
-------------------------------------------------------  ------------  ------------  -----------
Average ex-showroom realisation per e2W unit, FY2024-25  12,240 crore  19,776 crore  7,536 crore
Simulated range (10,000 runs): P10 13,656 crore, P50 15,458 crore, P90 17,847 crore

== bottom up ==
Step                                                                Value  Running total
--------------------------------------------------------------  ---------  -------------
Top 4 OEMs' e2W units sold, FY2024-25 (Ola, TVS, Bajaj, Ather)  9.43 lakh      9.43 lakh
Average ex-showroom realisation per e2W unit, FY2024-25         1.29 lakh   12,198 crore
Gross-up for OEMs outside the top 4 (18% of e2W units)                  1   14,861 crore
Estimate: 14,861 crore

What moves this estimate most (each assumption at its low and high, others held):
Assumption                                                     At low       At high        Swing
-------------------------------------------------------  ------------  ------------  -----------
Average ex-showroom realisation per e2W unit, FY2024-25  12,240 crore  19,775 crore  7,536 crore
Simulated range (10,000 runs): P10 13,655 crore, P50 15,457 crore, P90 17,846 crore

The approaches agree within 0%. Present the simulated range, not a single number.
```

## Why the agreement proves less than it looks like

The tool's own docs say the reconciliation step exists to catch a wrong assumption before it gets presented. Here the two chains landed on the exact same 14,861 crore, and the sensible reaction is to feel reassured. I do not think that reaction is earned.

Look at what is actually independent between the two chains. The top-down chain's units come from SIAM's total two-wheeler count times a penetration rate that Vahan itself supplied. The bottom-up chain's units come from the same Vahan registrations, just for four OEMs instead of the whole market, then grossed back up using a share that Vahan also supplied. Both chains use the identical price, 1,29,308 rupees, because I only had one revenue-based price to trust. So the "two methods" are one units source and one price source, arranged into two different-looking multiplications. A wrong price would move both chains by exactly the same amount, in the same direction, and they would still agree with each other, and both would still be wrong.

A reconciliation that means something needs the two chains to fail independently when an input is wrong. The nearest I have to that here is the price cross-check against the list-price band, which is a genuinely separate source from Ola's filed revenue, and that one did move: the filed number (1,29,308) landed near the bottom of the list-price band (1,06,500 to 1,72,068), not at its centre, which is itself informative about how much showroom list prices overstate what buyers actually pay.

One more gap worth naming. Ola's own press release says it delivered 3,59,221 units in FY25, 4.4 percent more than the 3,44,009 Vahan-registered units Autocar's OEM table uses for the same company. Deliveries and registrations are not the same event, and there is a lag between them. Every OEM-level number in the bottom-up chain likely understates true deliveries by a similar few percent, which the model does not correct for.

## What I think

India's e2W market was worth somewhere around 13,700 to 17,800 crore rupees at ex-showroom prices in FY2024-25 (the simulated P10 to P90), with 14,861 crore as the single number if one is required. The tighter claim I would actually defend in an interview is the methodological one: an agreement between top-down and bottom-up is only evidence of a correct estimate when the two chains do not share an input, and a consultant should say out loud, on the slide, when they do.

## What would change my mind

- If TVS Motor or Bajaj Auto ever disclosed a segment-level e2W revenue number the way Ola does (both are diversified two-wheeler makers and do not currently break out EV revenue separately), and it implied a per-unit realisation far from 1,29,308, I would trust the bottom-up chain's price far less, since it is currently one company's number applied to three others.
- If Vahan published delivery-adjusted rather than registration-based counts, I would redo the bottom-up chain with the higher, corrected unit counts, which would raise the estimate by roughly the 4 to 5 percent gap seen in Ola's own numbers.
- If a second listed e2W maker's revenue-per-unit came in far outside the 1,06,500 to 1,72,068 list-price band, that would be the real, independent reconciliation failure this note is missing, and it would mean the single 1,29,308 price should not be reused across both chains.
- This note has no way to check whether Ola's FY2024-25 discount and financing mix, the thing that pulls its realised price below list, was typical of the market or specific to Ola's own push for volume that year. A second filed revenue number would settle it either way.

## Sources

- Society of Indian Automobile Manufacturers, two-wheeler domestic sales press release, FY2024-25, 15 April 2025. https://www.siam.in/pressrelease-details.aspx?mpgid=48&pgidtrail=50&pid=579
- Autocar Professional, "Two-wheeler share of EV sales grows to 58% in FY2025", 3 April 2025, citing Vahan registration data. https://www.autocarpro.in/analysis-sales/two-wheeler-share-of-ev-sales-grows-to-58-in-fy2025-125714
- Ola Electric Mobility Limited, "Q4 & FY25 Press Release", 29 May 2025. https://cdn.olaelectric.com/sites/evdp/pages/investor/financials/q4/Ola_Electric_Mobility_Limited_Press_Release_Q4_FY25.pdf
- Ola Electric, S1 scooter price page, checked 2026-09-26. https://www.olaelectric.com/s1
- BikeWale, TVS iQube price page, checked 2026-09-26. https://www.bikewale.com/tvs-bikes/iqube/
- BikeWale, Bajaj Chetak price page, checked 2026-09-26. https://www.bikewale.com/bajaj-bikes/chetak/
- BikeWale, Ather 450 price page, checked 2026-09-26. https://www.bikewale.com/ather-bikes/450x/
