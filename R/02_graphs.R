library(tidyverse)

# TODO: make a categorical color scale for a fixed number of cathegories (see Wong for the recomendation of the maximum number)

source("https://raw.githubusercontent.com/semenoffalex/MiscR/main/theme_wong.R")
wong_set_style("sf")

d <- read_csv(file.path("..", "notebooks", "eval_local_V2_results.csv")) |>
  mutate(
    model = recode(
      model,
      "hermes-3-llama-3.1-8b" = "llama-3.1-8b",
      "google/gemma-4-e2b" = "gemma-4-e2b",
      "llama-xlam-2-8b-fc-r-mlx" = "xLAM-2-8b"
    ),
    model = factor(
      model,
      levels = c("gpt-oss-20b", "llama-3.1-8b", "gemma-4-e2b", "xLAM-2-8b")
    ),
    condition = factor(condition, levels = c("search", "graph"))
  )

## Graph: Total tokens by Model
ggplot(d, aes(model, total_tokens, fill = condition)) +
  geom_col(position = position_dodge(width = 0.78), width = 0.72) +
  scale_fill_manual(
    values = setNames(wong_pal(2), c("search", "graph"))) +
  geom_text(
    aes(label = total_tokens),
    position = position_dodge(width = 0.78),
    vjust = -0.35,
    size = 3.2
  ) +
  scale_y_continuous(
    breaks = seq(0, 3000, 1000),
    labels = function(x) {
      ifelse(x == 0, "0", paste0(x / 1000, "K"))
    },
    limits = c(0, 3000),
    expand = expansion(mult = c(0, 0.04))
  ) +
  labs(title = "Total tokens by model", 
       subtitle = "Search sums every agent LLM call. Graph is one call.",
       x = NULL, 
       y = NULL) +
  theme_wong(style = "sf", 
             scales = FALSE) +
  theme(
    axis.text.y = element_blank(),
    axis.line.y = element_blank(),
    axis.ticks.y = element_blank(),
    panel.grid.major.y = element_blank(),
    legend.justification = "center", # TODO: make this default in theme_wong()
    legend.title = element_blank())

## Graph: Elapsed wall time by model
ggplot(d, aes(model, elapsed_s, fill = condition)) +
  geom_col(position = position_dodge(width = 0.78), width = 0.72) +
  scale_y_continuous(
    expand = expansion(mult = c(0, 0.04))
  ) +
  scale_fill_manual(
    values = setNames(wong_pal(2), c("search", "graph"))) +
  geom_text(
    aes(label = elapsed_s),
    position = position_dodge(width = 0.78),
    vjust = -0.35,
    size = 3.2
  ) +
  labs(title = "Elapsed wall time by model",
       subtitle = "Rounded to nearest second. Search includes grep/read.",
       x = NULL, 
       y = NULL) +
  theme_wong(style = "sf", 
             scales = FALSE) +
  theme(
    axis.text.y = element_blank(),
    axis.line.y = element_blank(),
    axis.ticks.y = element_blank(),
    panel.grid.major.y = element_blank(),
    legend.justification = "center", # TODO: make this default in theme_wong()
    legend.title = element_blank())


# Graph ideas from LLM ------------------------------------------------------------------

d <- read_csv(file.path("..", "notebooks", "eval_local_V2_results.csv")) |>
  mutate(
    model = str_trunc(model, 28),
    elapsed_seconds = elapsed_s,
    condition = factor(condition, levels = c("search", "graph"))
  )

paired <- d |>
  select(run_at, model, condition, total_tokens, elapsed_seconds) |>
  pivot_longer(
    c(total_tokens, elapsed_seconds),
    names_to = "metric",
    values_to = "value"
  ) |>
  mutate(
    metric = recode(
      metric,
      total_tokens = "total tokens",
      elapsed_seconds = "elapsed seconds"
    )
  )

ggplot(paired, aes(condition, value, group = interaction(model, run_at), colour = model)) +
  geom_line(alpha = 0.9, linewidth = 0.7) +
  geom_point(size = 2.4) +
  facet_wrap(~metric, scales = "free_y") +
  labs(
    x = NULL,
    y = NULL,
    colour = NULL,
    title = "Search vs graph"
  ) +
  theme_wong()   # style = "sf" для charcoal/orange

deltas <- d |>
  select(run_at, model, condition, total_tokens, elapsed_seconds) |>
  pivot_wider(
    names_from = condition,
    values_from = c(total_tokens, elapsed_seconds)
  ) |>
  mutate(
    `total tokens` = total_tokens_search - total_tokens_graph,
    `elapsed seconds` = elapsed_seconds_search - elapsed_seconds_graph
  ) |>
  select(run_at, model, `total tokens`, `elapsed seconds`) |>
  pivot_longer(
    c(`total tokens`, `elapsed seconds`),
    names_to = "metric",
    values_to = "search_minus_graph"
  )

ggplot(deltas, aes(search_minus_graph, fct_reorder(model, search_minus_graph), fill = metric)) +
  geom_vline(xintercept = 0, colour = wong_colors$axis, linewidth = 0.4) +
  geom_col(width = 0.65, show.legend = FALSE) +
  facet_wrap(~metric, scales = "free_x") +
  labs(
    x = "search − graph",
    y = NULL,
    title = "How much extra search spends"
  ) +
  theme_wong(grid = FALSE) +
  theme(
    panel.grid.major.x = element_line(colour = wong_colors$grid, linewidth = 0.3),
    panel.grid.major.y = element_blank()
  )

