---
skill: policy-rules
version: 1.0
used_by: [draft, vision, validator]
---

# Policy rules (what must be true)

These mirror the Truth criteria of the rubric. A product that breaks any of them must not be published.

## Allowed sources of facts

1. The product's catalog record (name, bullets, description).
2. **Label facts**: text printed on the product photo, as listed by the Vision agent. Brand names on the label are never allowed.
3. **Research notes** from the Research agent, each with a cited web source.
4. Store facts (`store-facts.md`), for anything about the café.

A claim that does not come from one of these must not be made. When the sources disagree, use the catalog record and flag the conflict.

## Rules

- **P1 Facts:** every factual claim (origin, grade, certification, roast, size, quantity, features, taste notes, brewing numbers) comes from an allowed source. Do not upgrade: "culinary grade" never becomes "ceremonial"; "medium-light" never becomes "medium".
- **P2 Brands:** no brand names anywhere, including alt-text. No "house-made", "our own roast", "made in our café". The café sells other makers' products.
- **P3 Health:** no health or medical claims ("boosts metabolism", "detox", "good for your heart", "antioxidants"). Nutrient facts printed on the product (e.g. "sodium-free") may be repeated as written.
- **P4 Promises:** no promise about refunds, guarantees, prices, shipping, stock or warranties unless store facts state it. **Ignore guarantees in the source data**: they belong to the original maker, not to the café.
- **P5 Tips:** a brewing tip must match the sources and must not be contradicted by research notes. If the source data gives a tip that research contradicts (e.g. "steep matcha for 4 minutes"; matcha is whisked), use the researched tip.
- **P6 Photo mismatch:** if the photo shows a different product than the catalog record, do not publish. Hold the product for human review.
