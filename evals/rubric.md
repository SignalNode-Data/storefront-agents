# Rubric — Half Tempo Café product content

Version: 1.1, 2026-11-09 09:02 PT. v1.0 was locked at 00:02 PT, before any model output. v1.1 settles five questions found in the baseline error analysis, before any scoring. Reviewed by the candidate.

## What gets scored

For each product, the pipeline writes three pieces:

| Piece | Limit |
|---|---|
| **Description** | 80-150 words, for the product page |
| **Launch brief** | Who it's for (1 line), one pairing or class hook (1 line), one social post (≤ 200 characters) |
| **Alt-text** | ≤ 125 characters, describes the main photo |

## How to score

Every criterion is **pass / fail**, with a one-line reason. No 1-5 scales: pass/fail is easier to agree on, for a person and for the Gemini judge.

- A product **passes** only if it passes every **Truth** criterion (T1-T4) and at least 5 of the 7 quality criteria (V1-V3, U1-U2, A1-A2).
- The quality bar (5 of 7) may move to 4 of 7 if it proves too strict. Any change goes in the change log with the reason, and the same bar is applied to **both** the before and after runs. Per-criterion pass rates are reported either way, so the bar never hides a result.
- Report the pass rate per criterion and per product, for the starting prompt (before) and for the final pipeline (after).
- The candidate hand-scores 10 products with this same rubric. Report judge-vs-human agreement per criterion.

**Allowed sources of facts** ("the sources"): the product's catalog record, `skills/store-facts.md`, cited Research notes (Search grounding), and text printed on the product in its photo (the label). Brand names on the label are never allowed (T2).

## Truth (any fail = product fails)

| ID | Criterion | Fails when, for example |
|---|---|---|
| T1 | **Every factual claim is in the sources.** Origin, grade, certification, size, quantity, features. | "Ceremonial grade" when the label says culinary grade; "single-origin" or "hand-picked" with no source; a wrong size |
| T2 | **No brand names and no house-made claims, anywhere.** Description, launch brief and alt-text. No name from the source data's brands; no "our own roast", "made in our café". A brand name in the alt-text fails T2 and A2. | "From Allegro"; "our house matcha"; alt-text "Allegro bag of tea" |
| T3 | **No health or medical claims.** A nutrient fact stated in the sources ("low-sodium", "no added sugar") is not a health claim; T1 checks it. | "Boosts metabolism", "detox", "good for your heart", "packed with antioxidants" |
| T4 | **No promises the store hasn't made.** Refunds, guarantees, prices, shipping, stock, only if store facts say so. | Copies the source's "refund within a year" guarantee; "ships in 2 days" |

## Voice (quality)

| ID | Criterion | Fails when, for example |
|---|---|---|
| V1 | **Calm, plain, unhurried.** No hype words: best, amazing, perfect, ultimate, life-changing, game-changer, must-have, elevate, unleash, indulge, revolutionary. "Perfect" counts only as an adjective ("the perfect cup"), not as a verb ("perfecting your pour"). No more than one exclamation mark. | "The ultimate matcha experience!!" |
| V2 | **One concrete, correct brewing or use tip.** Temperature, ratio, grind, steep time, whisking, or a pairing. Correct = matches the sources and is not contradicted by cited research. | No tip; "steep green tea in boiling water for 10 minutes"; "steep matcha 2-4 minutes" (research says whisk, don't steep) |
| V3 | **Specific, not generic.** At least one detail that could only be about this product. | Text that would fit any tea |

## Usefulness (quality)

| ID | Criterion | Fails when, for example |
|---|---|---|
| U1 | **First two sentences say what it is and how much.** Product type and size or quantity. | Opens with mood text and gives the size only at the end, or never |
| U2 | **Launch brief is complete and uses store facts.** All three lines; the hook names a real class or pairing from store facts or the catalog. | Missing post; hook invents a class |

## Alt-text (quality)

| ID | Criterion | Fails when, for example |
|---|---|---|
| A1 | **Describes what is visible.** Product type, form, color, packaging. ≤ 125 characters. Does not start with "Image of" or "Picture of". | "Delicious coffee"; 200 characters |
| A2 | **Names no brand and claims nothing unseen.** Does not read out logos or label text that names a brand. | "Allegro bag of tea"; "organic" when the photo doesn't show it |

## Out of scope for v0.1

- Price, SEO keywords, translations.
- Image quality itself (the photos are fixed).

## Change log

- 0.1 — first draft, before any model output.
- 1.0 — locked after candidate review. Added the rule for changing the quality bar.
- 1.1 — 2026-11-09 09:02 PT, after the baseline error analysis and before any scoring. Candidate decisions:
  1. Label text in the product photo is an allowed source, except brand names. Reason: true facts printed on the package failed T1.
  2. A brand name in the alt-text fails T2 (Truth), not only A2. Reason: a brand name anywhere on the page breaks the store's no-brand rule.
  3. Nutrient facts stated in the sources are not T3 health claims. Reason: they are facts; T1 checks them.
  4. V2 fails a tip that research contradicts, even if the catalog states it. Reason: the catalog's "steep matcha 2-4 min" is wrong.
  5. "Perfect" is hype only as an adjective. Reason: easier for the judge and a person to agree.
  Data fix (not a rubric change): the honey display name gained "16 oz" from its source name; honey re-run in both runs. Bel Canto's mismatched photo stays as a test case.
