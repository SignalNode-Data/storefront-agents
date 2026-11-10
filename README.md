# storefront-agents

Four AI agents that write product pages for a small coffee, tea and matcha shop, plus a rubric, a judge and a hand-scored check that measure whether the pages are safe to publish.

The shop, **Half Tempo Café**, is fictional. Product data is a 32-product sample from [Amazon Berkeley Objects](https://amazon-berkeley-objects.s3.amazonaws.com/index.html) (CC BY 4.0, credit Amazon.com), adapted with brand names removed. See `data/abo/ATTRIBUTION.md`.

Demo (recorded runs): https://storefront-demo-377532661967.us-central1.run.app

## Results

| | One plain prompt (`runs/baseline-v1`) | Agents (`runs/pipeline-v2`) |
|---|---|---|
| Products passing the rubric (all 4 Truth criteria + 5 of 7 quality) | 11 / 32 | 32 / 32 |
| Brand names on the page (T2) | 21 / 32 | 0 / 32 |
| General facts stated as this product's facts (`scripts/measure_n1.py`) | — | 62 claims (pipeline-v1) → 4 (pipeline-v2) |

- Judge: Gemini, scoring against `evals/rubric.md` (locked before any output). Blind hand-scores of 10 products agree with the judge on 106 of 110 criterion scores (`evals/hand-scoring/agreement.json`).
- 32 / 32 is the rubric's ceiling, not proof of zero errors. `evals/error-analysis-pipeline-v2.md` lists what the score misses, including a hand spot-check that found one wrong `[THIS PRODUCT]` tag.
- The judge and the Validator are the same model family, so they can share blind spots.

## How it works

```
Research (Google Search grounding, cached) ─┐
                                            ├─> Draft ─> Validator ─> publish | revise once | hold for a person
Vision (alt-text, label facts, photo check) ┘
```

- **Research** looks up facts with cited sources and tags each one `[THIS PRODUCT]` or `[GENERAL]`. Results are cached in `data/research-v2/` (v1 cache kept in `data/research/`).
- **Vision** writes alt-text from the photo, lists label facts, and flags a photo that shows a different product.
- **Draft** writes the description and launch brief and lists a source for every claim.
- **Validator** runs code checks first (brand names, hype words, lengths, size placement), then a model check of facts, health claims, promises and tips. One revision; a photo mismatch is always held.
- Each agent loads only the skills it needs from `skills/` (brand voice, output format, policy rules, store facts). Skills are versioned; every run records the versions.

## Layout

| Path | What |
|---|---|
| `storefront_agents/` | Agents, pipeline, code checks, judge, catalog loader |
| `skills/` | Versioned rule files the agents load |
| `evals/` | Rubric, error analyses, blind hand-scoring and agreement |
| `runs/` | Every run's outputs, judge scores and usage |
| `scripts/` | Run the baseline, the pipeline, the judge, the N1 measure |
| `app/` | Demo (FastAPI): preset products, cached research, per-visitor limits |
| `prompts/baseline_v1.md` | The one plain prompt used for the "before" |

## Run it

Needs Python 3.12 and a Google Cloud project with Vertex AI (Application Default Credentials; no API keys).

```
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/run_baseline.py   # writes runs/baseline-v1
.venv/bin/python scripts/run_pipeline.py pipeline-v2 --research data/research-v2
.venv/bin/python scripts/run_judge.py pipeline-v2 --research data/research-v2
.venv/bin/python scripts/measure_n1.py pipeline-v2 --research data/research-v2
.venv/bin/python -m pytest -q tests
```

The project ID is set in `storefront_agents/llm.py`. The demo runs with `LIVE_RUNS=off` to serve recorded runs only.

## Built with

Built with Claude Code as a coding partner, with Gemini (`gemini-3.8-flash` on Vertex AI) running the agents and the judge. Claude wrote most of the code under the author's direction; the author chose the problem, wrote the rubric, hand-scored the samples and made the trade-offs.
