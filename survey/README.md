# Surveys

The participant **pre-school survey**, whose results feed the "Who is in the
room?" slides in [`materials/intro/intro.qmd`](../materials/intro/intro.qmd),
and the **post-school survey** that collects feedback at the end of the week.

## Rule

**Raw responses never enter this repository.** The pre-school export contains
names and e-mail addresses, and post-school responses may carry a name too. Only
the aggregate counts in `summary/`, `aggregate.R` and `post_school_survey.gs` are
committed; everything else under `survey/` is gitignored.

## Layout

```
survey/
  results_<date>.csv       # the raw export — gitignored, keep it local
  aggregate.R              # raw  ->  summary/*.csv
  post_school_survey.gs    # Apps Script that builds the post-school form
  summary/                 # committed; the only thing the slides read
    ml_exposure.csv
    cv_concepts.csv
    dataset_interest.csv
    headline.csv
```

## Refreshing the numbers

Drop a new export in as `survey/results_<date>.csv` and, from the project root:

```sh
Rscript survey/aggregate.R          # picks up the newest results_*.csv
quarto render materials/intro/intro.qmd
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

## The post-school survey

`post_school_survey.gs` is a Google Apps Script that builds the feedback form
("CV in Archaeology — Post-School Survey"). Paste it into a new project at
[script.google.com](https://script.google.com), run `createFeedbackForm`, and
take the edit and share URLs from the execution log. It creates the form only —
link a response sheet from the form's *Responses* tab. Running it a second time
creates a second form, so edit the existing form for small fixes and keep the
script in step.

Two items are required (what I learned; help was there when I needed it);
everything else, including the name field, is optional, and no e-mail addresses
are collected. The per-lecturer grids and comment boxes are there to give each
person something to act on for their next workshop, not to rank them — keep the
wording forward-looking if you edit it.

## Quotations

The three quotations on "What you want from the week" are pasted into the slide
source, anonymised and lightly trimmed. They are **not** stored here — re-pick
them by hand from the raw export each round, and keep them free of anything that
identifies a respondent, an institution, or a site.

> The survey form has no consent question. If quotations are to be shown again,
> add one.
