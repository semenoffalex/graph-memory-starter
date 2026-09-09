# graph-memory-starter (fork)

Fork of [Glitch Cat Club / graph-memory-starter](https://github.com/Glitch-Cat-Club/graph-memory-starter). The upstream repo is the design: modelled notes, a SQLite graph, a ~400-token recall dump before the model runs.

This fork is a **reproduction on local 2–20B models**, not another Claude Code setup guide. The published eval uses Haiku as the “small” model. Here “small” means whatever fits a MacBook Air M2 24GB at 8k context.

[Video of the original demo](https://www.youtube.com/watch?v=svvlT-nX6N8). Write-up (Quarto / Habr-style): [`R/article.qmd`](R/article.qmd).

## Question

`A customer wants an £800 refund in March. Who signs it off?`  
Expected: **Marcus Webb**. Three hops (policy → role → holder → delegate) across docs that barely share keywords, plus a superseded 2024 refund policy as bait.

Two conditions, same question:

| Condition | What runs |
|---|---|
| **search** | LangChain agent, Grep/Read over `corpus-before/` |
| **graph** | `src/recall.py` injects facts; the model has **no tools** |

One question, one run per cell. Punchline, not a leaderboard.

## Result (this fork)

MacBook Air M2 24GB, 8k. Models that were already on disk.

| Model | search | graph | tokens | wall time |
|---|---|---|---|---|
| gpt-oss-20b (mxfp4) | wrong | correct | 2315 → 574 | 105s → 23s |
| Hermes-3 Llama 3.1 8B (4bit) | wrong | correct | 2027 → 455 | 53s → 12s |
| gemma-4-e2b (8bit) | wrong | correct | 2100 → 804 | 90s → 36s |
| xLAM-2-8b (8bit) | wrong | correct | 1584 → 475 | 18s → 20s |

None of them answered from search. All of them did from the graph dump (Hermes still names Sarah Chen as a signer — generous `correct`). Pooled tokens ~3.5× lower; pooled wall time ~2.9×. xLAM is the exception on speed: it quit search after one grep and was slower on graph.

Upstream, Fable 5 and Sonnet already succeed on search; only Haiku flips. On 2–20B the graph is what makes the answer possible, not a token-saver for a model that already got it.

The hop walk is code. A stronger model builds the graph once; a 2B model reads ~400 tokens and speaks.

## Layout (what this fork adds)

    notebooks/     LangChain evals + CSV results
    R/             Quarto article and plots
    (the rest)     unchanged from upstream: corpus/, corpus-before/, src/, rag/, …

Details: [`notebooks/README.md`](notebooks/README.md), [`R/README.md`](R/README.md).

## Re-run the eval

Python 3.10+ and a local OpenAI-compatible server (LM Studio or Ollama). Open [`notebooks/eval_local_V2.ipynb`](notebooks/eval_local_V2.ipynb) from `notebooks/` or the repo root, set `MODEL` in Config, run. CSVs land in `notebooks/`.

## Knit the article

Open [`R/graph-memory-starter.Rproj`](R/graph-memory-starter.Rproj), Render `article.qmd`. Needs `tidyverse`, `gt`, [Quarto](https://quarto.org).

## Upstream

To install the memory starter itself (Claude Code hooks, rag/, digest/), use the [original README](https://github.com/Glitch-Cat-Club/graph-memory-starter). Graph build and recall here are the same commands:

```bash
python src/build_graph.py
python src/recall.py "A customer wants an £800 refund in March. Who signs it off?"
```
