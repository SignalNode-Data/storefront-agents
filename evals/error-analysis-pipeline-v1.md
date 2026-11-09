# Error analysis: pipeline-v1 (the "after", first version)

Run: `runs/pipeline-v1/` · model `gemini-3.8-flash` · skills brand-voice 1.1, output-format 1.0, policy-rules 1.0, store-facts 1.0 · 32 products · 2026-11-09 01:22-01:45 PT (3 re-runs after).
Result: **30 publish, 2 held for photo mismatch, 0 needs review.** 5 products needed one revision. 3 products hit a 429 rate limit and were re-run one at a time (same code).
Tokens: 318,538 input · 36,247 output · 213,531 thinking · 80 grounded search queries · 140 model calls.

**Status: first pass by Claude; not the official scores** (those come from the judge and the candidate's blind hand-scores).

## What the agents fixed (compared with baseline-v1)

| Baseline group | Baseline | pipeline-v1 (code checks + reading) |
|---|---|---|
| G1 Brand names in alt-text | 20/32 | **0/32** |
| G2 Size not in the first two sentences | 24/32 | **0/32** (every description opens with type + size) |
| G5 Hype words | 10/32 | **0/32** |
| G6 Photo does not match the listing | 1 would publish | **held** (Bel Canto), plus a second hold (see below) |
| G7 Wrong source tip (matcha "steep 2-4 min") | 1 | **fixed**: researched whisking method, 160-175°F |
| Kettle with no data | invented "ergonomic handle", "durable" | cited capacity, base, switch; Validator removed "ergonomic" from the alt-text |

## New failure groups

| # | Group | Products | Rubric | Example |
|---|---|---|---|---|
| N1 | **General facts stated as this product's facts.** Research returns facts about the *type* of product; Draft writes them as facts about *this* bag. | ~9 | T1 (passes as written: the fact is in the research notes) | Colombia: "These beans grow in the high-altitude San Agustín area of Huila, … 1,400-1,900 m" (the label says only "Colombia Agustino Forest"). Sumatra: "processed using the region's traditional wet-hulling method". Yunnan, 72% chocolate, honey, truffles: flavor or texture notes typical of the type, written as this product's notes. |
| N2 | **Research may describe a similar but different product.** | 1-2 suspected | T1 | Kettle and grinder specs (1 liter, swivel base, 150 W motor) come from web pages that may describe related models. Not verified. |
| N3 | **Pairings with products the store doesn't sell.** | 5 | none (allowed) | "hojicha" suggested in 5 pairings. Harmless, but off-catalog. |
| N4 | **Second photo hold: organic claim not on the package.** | 1 | P6 | Organic Green Matcha Powder: the catalog says organic; the package shows no organic claim. Correctly held for a person to decide. The draft still says "organic" (from the catalog). |

The Validator caught alt-text problems ("ergonomic", "glass jar", "stainless steel") and one weak hook, but **did not catch N1**. Its rule P1 asks "is the claim in a source?", and a general research note is a source.

## Proposed "one change" for Block 5 (candidate decides)

**Make Research label each note as `[THIS PRODUCT]` (a cited source names this exact product) or `[GENERAL]` (true of the product type), and make Draft and Validator treat `[GENERAL]` notes as general:** "Sumatran coffees are often wet-hulled", never "these beans were wet-hulled".

Why this change: N1 is the largest remaining group, it is a real truth risk (the rubric's most important area), and it is a single, testable change in two skills/prompts. Measure: N1 count and T1 pass rate, before vs after the change.
