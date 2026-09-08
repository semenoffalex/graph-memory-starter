library(tidyverse)

df <- read_csv(file.path("..", "notebooks", "eval_local_V2_results.csv"))

View(df)

df %>% ggplot() +
  geom_histogram(aes(x=result, y=total_tokens))
