# Local graph vs search evals

LangChain notebooks that replay the starter’s 3-hop refund question under two conditions:

- **search** — the model drives Grep/Read over `corpus-before/`
- **graph** — `src/recall.py` injects facts; the model has no tools

`eval_local_V2.ipynb` is the run behind the article (adds wall time). `eval_local.ipynb` is the earlier table without timing.

Open from `notebooks/` or the repo root. Config resolves `src/` and writes CSVs in this folder.

Needs Python 3.10+ and a local OpenAI-compatible server (LM Studio or Ollama). Change `MODEL` in the Config cell between runs.
