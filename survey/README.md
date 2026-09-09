# Pre-school survey

Results of the participant pre-school survey, used on the "Who is in the room?"
slides in [`materials/intro.qmd`](../materials/intro.qmd).

## Rule

**Raw responses never enter this repository.** The export contains names and
e-mail addresses. Only the aggregate counts in `summary/` are committed, and
only those are read by the slides. Everything else under `survey/` is gitignored.

## Layout

```
survey/
  results_<date>.csv   # the raw export — gitignored, keep it local
  aggregate.R          # raw  ->  summary/*.csv
  summary/             # committed; the only thing the slides read
    ml_exposure.csv
    cv_concepts.csv
    dataset_interest.csv
    headline.csv
```

## Refreshing the numbers

Drop a new export in as `survey/results_<date>.csv` and, from the project root:

```sh
Rscript survey/aggregate.R          # picks up the newest results_*.csv
quarto render materials/intro.qmd
```

The script reads the questions **by column position**, not by name — the wording
is long and gets edited between rounds. If the form changes, check the indices at
the top of `aggregate.R`. Free-text answers that don't match a fixed option are
folded into the nearest category by an explicit, commented recode.

## The summary tables

`ml_exposure.csv`, `cv_concepts.csv`, `dataset_interest.csv` all carry
`category, n, pct`. `pct` is always a percentage of respondents, so for the
multi-select questions (`cv_concepts`, `dataset_interest`) the column sums above
100 — say "multiple answers allowed" wherever they are shown.

`headline.csv` carries `key, pct, n_respondents` for the single figures quoted as
text on the slides: `assistant_regularly`, `python_confident`, `never_annotated`,
`any_ml_exposure`, `no_own_dataset`, `windows`.

## Quotations

The three quotations on "What you want from the week" are pasted into the slide
source, anonymised and lightly trimmed. They are **not** stored here — re-pick
them by hand from the raw export each round, and keep them free of anything that
identifies a respondent, an institution, or a site.

> The survey form has no consent question. If quotations are to be shown again,
> add one.
