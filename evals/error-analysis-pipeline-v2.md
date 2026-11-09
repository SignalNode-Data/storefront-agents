# Error analysis: pipeline-v2 (Block 5: one change)

Run: `runs/pipeline-v2/` · model `gemini-3.8-flash` · skills brand-voice 1.1, output-format 1.0, **policy-rules 1.1**, store-facts 1.0 · 32 products · started 2026-11-09 10:51 PT · research cache `data/research-v2/` (fresh; the v1 cache in `data/research/` is unchanged, so pipeline-v1 stays reproducible).

## The one change

Research tags every note `[THIS PRODUCT]` (a page it found names this exact product and states the fact) or `[GENERAL]` (true of the type, region, process or style). When unsure, it must use `[GENERAL]`. Draft may state only `[THIS PRODUCT]` notes as facts about this product and must word `[GENERAL]` notes as general ("Sumatran coffees are often wet-hulled"). The Validator fails a `[GENERAL]` note stated as a product fact (rule P1). A code check fails any tag copied into the content.

Files: `storefront_agents/agents.py` (Research, Draft and Validator prompts; per-note source indexes from grounding supports), `storefront_agents/checks.py`, `skills/policy-rules.md` 1.0 → 1.1. Run scripts gained `--research DIR`.

## Results

| Measure | pipeline-v1 | pipeline-v2 |
|---|---|---|
| Status | 30 publish, 2 held | 30 publish, 2 held (same two) |
| Revisions | 4 | 3 |
| Judge (rubric v1.1): products passing | 32/32 | 32/32 |
| Judge: every criterion | 100% | 100% |
| **N1: research-only claims stated as product facts with no `[THIS PRODUCT]` note** | **62 claims in 22 products** | **4 claims in 1 product** |
| Research-only claims worded as general | 4 | 15 |
| Product-worded claims backed by a `[THIS PRODUCT]` note | 0 (v1 has no tags) | 34 |

Research-v2 notes: 161 (31 `[THIS PRODUCT]`, 130 `[GENERAL]`, 0 untagged). 90 grounded searches (87 in the run + 3 in a one-product test before it). Run tokens: 318,734 input, 34,538 output, 272,623 thinking, 133 model calls.

The judge for pipeline-v2 sees the v2 notes, with tags (`run_judge.py pipeline-v2 --research data/research-v2`). The baseline and pipeline-v1 were judged against the v1 notes. The judge was already at its ceiling (32/32), so it cannot show this change. N1 is the measure for it.

## How N1 is measured (Claude's check, not the blind hand-scoring)

`scripts/measure_n1.py RUN --research DIR`, same method for v1 and v2. One model call per product. The model sees the catalog, the label facts, the research notes **with tags removed**, and the content. It lists each origin, process, variety, flavor or spec claim found only in a research note (not in the catalog, not on the label), the note number, and whether the content words it as a product fact or as general. Brewing tips are left out. Code then looks up the note's tag. N1 = worded as a product fact and the note is not `[THIS PRODUCT]`. Output: `runs/<run>/n1.jsonl`, `n1.json`.

Limits: the measurer is the same model family as the pipeline. Some v1 flags are borderline (genmaicha "toasted brown rice" is part of what the tea is). v1 counts are "not checked", not "false": some v1 claims may be true of the product.

## Remaining N1 (v2)

Honey: "delicate floral aromatics" and "unpasteurized" come from `[GENERAL]` notes about raw honey and are stated about this jar. The Validator did not flag them. Low risk ("raw" honey is unheated by definition), but it is still a miss.

## Spot-check of `[THIS PRODUCT]` tags (Claude, by hand, 11:05-11:12 PT)

The change moves the risk: a product fact is now only as good as its `[THIS PRODUCT]` tag. Claude checked the cited pages for 5 products. The grounding links were resolved to page addresses. Three sites refused automated reading (HTTP 403), so for those only the page address was checked, not the page text.

| Product | `[THIS PRODUCT]` claim | Cited page | Result |
|---|---|---|---|
| Organic dark chocolate coconut bar | "imported from Italy" | the retailer's page for this exact product ID | **Confirmed** ("Imported from Italy"). |
| same | "toasted coconut flakes" | a food-data page for this exact product | **Mostly confirmed**: ingredient "organic unsweetened toasted coconut"; the word "flakes" is not on the page. |
| Colombia Agustino Forest | "sourced from the Asoguar Cooperative in San Agustín, Huila" | a reseller page whose address names a **different coffee** (a rainforest blend) | **Tag not supported.** The page address does not match this product. Page text not readable (403). The published description states the cooperative as fact. |
| Sumatra whole bean | "Lake Toba and Lintong region, northern Sumatra" | two pages naming "Sumatra Lake Toba, whole bean, 12 ounce" from the same maker | **Plausible**: page names match the product line and size. Text not readable (403 / timeout). |
| Electric coffee bean grinder | "150-watt motor, 2.1 oz (60 g) capacity" | a user manual whose address carries this exact product ID | **Page identity confirmed**; text not readable (403). |
| Gooseneck kettle | "1 liter, swivel base, cool-touch handle" | a news shopping article and a video | **Not checked**: article text did not load. |

Result: 1 of 5 confirmed from page text, 2 matched by page identity, 1 tag not supported (Colombia), 1 not checked. Small sample; reported as found.

## What this means

- The change did what it was meant to do: general facts are now worded as general (N1 62 → 4) with no loss on the judged rubric.
- It created a new, narrower risk: **a wrong `[THIS PRODUCT]` tag**. The model sets the tag, and Colombia shows it can tag a fact from a page about another product.
- Next change (not built): a code check that a `[THIS PRODUCT]` note cites at least one page whose title or address names the product (or its ID); otherwise downgrade the note to `[GENERAL]`. The per-note source indexes saved in `data/research-v2/*.json` (`note_sources`) make this possible.

## Colombia fix: decided, not run (2026-11-09)

The candidate chose to remove the unsupported cooperative note and re-run Colombia (12:46 PT). The re-run failed: Google Cloud restricted Gemini access on the project (notice received about 12:06 PT; every call returns 403). The cache edit was reverted so the repo matches the recorded runs. **The published pipeline-v2 Colombia description still states the cooperative as fact.** It stays here as a documented example of a wrong `[THIS PRODUCT]` tag.
