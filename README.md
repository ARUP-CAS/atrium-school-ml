# atrium-school-ml

[![CC BY-SA 4.0][cc-by-sa-shield]][cc-by-sa]
[![MIT][mit-shield]][mit]

Website for the AIS CR Computer Vision Training School: programme, practical
information, setup guide and slides.

The notebooks and case-study exercises are in a separate repository,
[**atrium-school-ml-lessons**](https://github.com/arubrno/atrium-school-ml-lessons), so participants can clone and run them
without the website's Quarto machinery.

## Layout

```
*.qmd               the website pages
materials/          slides — one folder per session, e.g. intro/ (revealjs slides,
                    images, bibliography and theme)
figs/               figures used by the website
flyer/              the printed flyer
survey/             pre-school survey; raw responses are gitignored, aggregates are not
```

Slides are rendered as part of the site. Notebooks are not here — see the lessons
repository above.

## Environment

Quarto, and R for the chunks in `materials/intro/intro.qmd`. No Python is needed to
build this site.

## Publish

```shell
quarto publish gh-pages
```


## License 

Code in this work is licensed under a [MIT License][mit], all other content is licensed under a
[Creative Commons Attribution-ShareAlike 4.0 International License][cc-by-sa].

[cc-by-sa]: http://creativecommons.org/licenses/by-sa/4.0/
[cc-by-sa-image]: https://licensebuttons.net/l/by-sa/4.0/88x31.png
[cc-by-sa-shield]: https://img.shields.io/badge/License-CC%20BY--SA%204.0-lightgrey.svg
[mit-shield]: https://img.shields.io/badge/License-MIT-yellow.svg
[mit]: https://opensource.org/licenses/MIT