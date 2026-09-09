# atrium-school-ml

[![CC BY-SA 4.0][cc-by-sa-shield]][cc-by-sa]
[![MIT][mit-shield]][mit]

Repository contains an AIS CR Computer Vision Training School website and materials.

## Layout

```
*.qmd               the website
materials/          slides (intro.qmd) and the Monday CLIP demo notebook
case-studies/       one folder per case study
  datasets.yml      where every dataset lives — the only file to edit when one moves
  atrium_data.py    get_dataset(name) -> a local folder, cached in the persistent home
requirements.txt    Python packages for the notebooks
survey/             pre-school survey; raw responses are gitignored, aggregates are not
```

**Datasets are never committed.** They are too large, and some are not
redistributable. Notebooks call `get_dataset("name")`, which resolves the manifest
entry — a folder in this repo, a directory mounted on the JupyterHub, or a download
cached under `~/.cache/atrium-school`. Moving a dataset, or giving it a Zenodo DOI
later, means editing one entry in `case-studies/datasets.yml` and no notebook.

## Environment

```shell
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt \
    --index-url https://download.pytorch.org/whl/cpu \
    --extra-index-url https://pypi.org/simple
```

The PyTorch CPU index avoids pulling ~2.5 GB of CUDA runtime onto machines with no
NVIDIA card.

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