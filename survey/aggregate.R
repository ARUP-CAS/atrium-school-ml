#!/usr/bin/env Rscript
# Aggregate the raw pre-school survey export into the committed summary tables.
#
#   Rscript survey/aggregate.R [raw.csv]      # run from the project root
#
# The raw export contains names and e-mail addresses and is gitignored.
# Only the aggregate counts written to survey/summary/ ever enter the repo,
# and only those are read by the slides.

suppressPackageStartupMessages({
  library(dplyr); library(tidyr); library(readr); library(stringr)
})

args <- commandArgs(trailingOnly = TRUE)
raw_path <- if (length(args)) args[1] else {
  f <- sort(list.files("survey", "^results_.*\\.csv$", full.names = TRUE),
            decreasing = TRUE)
  if (!length(f)) stop("No survey/results_*.csv found. Run from the project root.")
  f[1]
}
message("Reading ", raw_path)

raw <- read_csv(raw_path, show_col_types = FALSE, name_repair = "minimal")
n <- nrow(raw)
dir.create("survey/summary", showWarnings = FALSE, recursive = TRUE)

# Column positions rather than names — the question wording is long and may be
# re-edited between rounds. Check these if the form changes.
col <- function(i) raw[[i]]

# Free-text answers that don't match a fixed option are folded into the nearest
# category. Recodes are listed explicitly so they can be audited.
ml_recode <- function(x) {
  case_when(
    str_detect(x, "^None")                  ~ "None",
    str_detect(x, "^Some")                  ~ "Some — a course or self-study",
    str_detect(x, "trained a model")        ~ "Trained a model before",
    str_detect(x, "work with ML regularly") ~ "Work with ML regularly",
    # "member of a project training models ... doing image preparation":
    # exposure through a project, but not modelling work -> Some
    TRUE                                    ~ "Some — a course or self-study"
  )
}

ml_levels <- c("None", "Some — a course or self-study",
               "Trained a model before", "Work with ML regularly")

tibble(category = factor(ml_recode(col(11)), levels = ml_levels)) |>
  count(category, .drop = FALSE) |>
  mutate(pct = round(100 * n / .env$n)) |>
  write_csv("survey/summary/ml_exposure.csv")

# Multi-select questions: comma-separated, so `n` sums above the respondent count.
multi <- function(x, drop = character()) {
  tibble(v = x) |>
    separate_rows(v, sep = ",") |>
    mutate(v = str_squish(v)) |>
    filter(v != "", !v %in% drop) |>
    count(v, name = "n", sort = TRUE) |>
    rename(category = v) |>
    mutate(pct = round(100 * n / .env$n))
}

multi(col(12)) |> write_csv("survey/summary/cv_concepts.csv")

# Fold the two one-off answers (3D scans; Japanese woodblock prints) into "Other".
multi(col(4)) |>
  mutate(category = if_else(n == 1 & !str_detect(category, "Coins"),
                            "Other", category)) |>
  group_by(category) |>
  summarise(n = sum(n), .groups = "drop") |>
  mutate(pct = round(100 * n / .env$n)) |>
  arrange(desc(n)) |>
  write_csv("survey/summary/dataset_interest.csv")

# Single headline figures used as text on the slides.
pct <- function(x) round(100 * sum(x, na.rm = TRUE) / n)
tibble::tribble(
  ~key,                  ~pct,
  "assistant_regularly", pct(str_detect(col(15), "regularly")),
  "python_confident",    pct(suppressWarnings(as.numeric(col(7))) >= 4),
  "never_annotated",     pct(col(13) == "No"),
  "any_ml_exposure",     pct(!str_detect(col(11), "^None")),
  "no_own_dataset",      pct(col(18) == "No"),
  "windows",             pct(str_detect(col(24), "Windows"))
) |>
  mutate(n_respondents = n) |>
  write_csv("survey/summary/headline.csv")

message("Wrote survey/summary/*.csv for n = ", n, " respondents.")
