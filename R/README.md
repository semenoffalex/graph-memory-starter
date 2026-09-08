# Local graph vs search article

Quarto write-up and plots for a Habr-style article: local models, search RAG vs graph RAG, on the [graph-memory-starter](https://github.com/Glitch-Cat-Club/graph-memory-starter) eval.

## Layout

| Path | What |
|---|---|
| `article.qmd` | Article (knit this) |
| `00_eda.R` / `02_graphs.R` | Exploratory plots |
| `../notebooks/` | LangChain eval notebooks and CSV results |
| `../notebooks/eval_local_V2_results.csv` | Data used by the article |

## Render the article

Open `graph-memory-starter.Rproj` in RStudio (working directory = this folder), then Render `article.qmd`.

Or from this folder:

```bash
quarto render article.qmd
```

Needs R packages `tidyverse` and `gt`, plus [Quarto](https://quarto.org). Plots pull [theme_wong](https://github.com/semenoffalex/MiscR) from GitHub on knit.

## Re-run the eval

See `../notebooks/README.md`. Jupyter writes CSVs next to the notebooks; this folder only reads them.
