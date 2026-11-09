# Error analysis: baseline-v1 (the "before")

Run: `runs/baseline-v1/` · model `gemini-3.8-flash` · prompt `prompts/baseline_v1.md` · 32 products · 0 errors · 2026-11-09 00:21 PT.
Tokens: 61,201 input, 8,937 output, 57,714 thinking.

**Status: first pass by Claude (open coding); awaiting the candidate's review.** These are not the official scores. The official "before" scores come from the Gemini judge and the candidate's hand-scores, using rubric v1.x.

Method (after Husain's error analysis): read every output, write down each failure in plain words, then group the failures and count them. Claims were checked against the catalog record; two photos were opened to check claims that the text data did not explain.

## What the plain prompt did well

- **No brand names in any description, launch brief or social post** (0/32). The loader removes brands from the text, and the model kept them out.
- **No copied refund guarantee** (0/5 coffees that carry it). The model used the store's 30-day return rule instead.
- **Store facts used correctly.** Class names, days and times, free pickup, the return rule and the free class seat for gear were all stated as written.
- **All length limits met.** Descriptions 92-133 words; alt-text ≤ 113 characters; posts ≤ 179 characters.

## Failure groups (most common first)

| # | Group | Products | Rubric | Root cause |
|---|---|---|---|---|
| G1 | **Brand names read off the photo into the alt-text** | 20/32 | A2 (and T2 as written) | The model reads logos on the packaging. The prompt never said not to. The text was clean; the photo is the leak path. |
| G2 | **Size buried or missing** in the first two sentences | 24/32 | U1 | Descriptions open with mood ("Slow down with…", "Start your morning…"). Size comes late or not at all (e.g. masala chai, 4 coffees, scones). 3 of the 24 have no size in the data (kettle, frother) or in our display name (honey: our error). |
| G3 | **True facts taken from the photo**, outside the allowed sources | ≥ 4 | T1 as written | E.g. Sumatra "Lake Toba", "cocoa nibs"; matcha "USDA Organic"; honey "US Grade A". All printed on the package, but rubric v1.0 lists only the record, store facts and research notes as sources. |
| G4 | **Invented or stretched claims** | ~6 | T1 | Sumatra "fertile volcanic soils" (nowhere); Nicaragua "medium roast" and "juicy" (data: medium-light, "subtly complex"); kettle "ergonomic handle", "durable", "complete control" (no data at all); matcha "dissolves smoothly"; chai "packed with caffeine" (data: "contains caffeine"); honey "unpasteurized" (inferred from "raw"). |
| G5 | **Hype words** | 10/32 | V1 | "perfect" and its forms in 8 products ("Perfect for iced lattes", "your perfect cup", "the perfect companion"); "indulgence" (72% chocolate); "elevates" (coconut bar). |
| G6 | **Photo does not match the listing** | 1/32 | T1, A1 | Bel Canto: the photo shows "Organic Espresso Sierra, medium dark roast". The description follows the listing (berries, cocoa) and the alt-text follows the photo, so the page contradicts itself. A data error in ABO. |
| G7 | **Wrong source data copied faithfully** | 1/32 | passes V2 as written | Organic green matcha: "steep for two to four minutes" is in the source data, so it "matches the sources". But matcha is whisked, not steeped. |

Observations (not failures under v1.0):

- **Tips are often handed off to the bar.** Many descriptions say "bring your bag to the bar for help with water temperature" instead of giving a temperature. V2 still passes, because a pairing counts as a tip.
- **Nutrient claims** from the source ("naturally sodium-free", "low-sodium") appear in 2 pairings. They are in the sources; whether T3 covers them is open (Q3).

## What each group asks of the pipeline

| Group | Fix in the agent design |
|---|---|
| G1 | Alt-text agent rule: never name a brand or read out logo text. Validator: run `BRAND_PATTERN` on every piece (a code check, not a model guess). |
| G2 | Output-format skill: sentence 1 = product type + size or quantity. Validator checks it. |
| G3, G4 | Research agent: grounded, cited facts for thin products (kettle). Validator: every claim must trace to a source; flag anything it cannot trace. |
| G5 | Brand-voice skill with the banned-word list; Validator code check. |
| G6 | Validator compares photo and listing; on mismatch, hold the product for human review instead of publishing. |
| G7 | Research agent checks brewing tips against grounded sources; the Validator flags a tip that research contradicts. |

## Open questions for the candidate (decide before any scoring; log as rubric v1.1)

1. **Is label text on the product photo an allowed source?** (G3) Recommendation: yes, for everything except brand names. The facts are real and printed on the product. Without this change, true claims fail T1.
2. **Does a brand name in the alt-text fail Truth (T2) as well as A2?** As written, yes, so 20 products fail outright. Recommendation: keep it strict. A brand name anywhere on the page is a real publishing error, given the store's no-brand rule.
3. **Are nutrient claims from the sources ("low-sodium") health claims under T3?** Recommendation: no. Allow them when the source states them (T1 covers accuracy).
4. **Should V2 fail a tip that matches the source but is wrong?** (G7) Recommendation: yes. Change "correct = matches the sources" to "matches the sources and is not contradicted by cited research".
5. **Do word forms count as hype?** ("perfecting your drink") Recommendation: count "perfect" as an adjective only ("perfect cup"), not the verb ("perfecting"). That makes it easier for the judge and a person to agree.

## Data fixes to decide before scoring

- **Honey display name has no size** (our error in `data/selection.csv`): add "16 oz" from the source name. Recommendation: fix it and re-run the baseline (≈ 4 minutes, a few cents) so the scored "before" uses the same data as the "after".
- **Bel Canto photo mismatch:** keep it as a deliberate test case for G6 (recommended), or swap the product.

## Decisions (2026-11-09 09:02 PT, candidate)

The candidate accepted all five recommendations and both data fixes. They are recorded in `evals/rubric.md` v1.1. Honey re-ran in both runs with "16 oz" in its name (logged in each `run.json` under `reruns`). In pipeline-v1, honey published with no revision this time, so "revised" changed from 5 to 4.
