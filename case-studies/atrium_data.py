"""Dataset access for the ATRIUM computer-vision training school.

Every notebook gets its data the same way, whatever the data actually is::

    from atrium_data import get_dataset
    path = get_dataset("coins")

Where a dataset lives is described once, in ``datasets.yml``. Moving a dataset —
into the repository, onto the hub, up to Zenodo — edits that file and no notebook.

Downloads are cached under ``~/.cache/atrium-school``, or wherever ``$ATRIUM_CACHE``
points — ``atrium_bootstrap.setup()`` sets it per platform. On the CERIT-SC
JupyterHub and on your own machine that is a persistent home directory, so a
dataset is fetched once and survives every later respawn of the notebook server.
On Colab it lives in ``/content`` unless you asked for Google Drive.

A dataset may list several sources under ``sources:`` instead of one ``source:``.
They are tried in order, so a folder mounted on the hub can name a public mirror
as its fallback, and the same notebook then works in Colab.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path

import yaml

__all__ = ["get_dataset", "list_datasets", "describe", "cache_dir"]

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent
MANIFEST = _HERE / "datasets.yml"

def cache_dir() -> Path:
    """Where downloads land. Override with $ATRIUM_CACHE.

    Read on every call, not once at import: ``atrium_bootstrap.setup()`` chooses
    a cache per platform, and a notebook may import this module either side of it.
    """
    return Path(os.environ.get("ATRIUM_CACHE", Path.home() / ".cache" / "atrium-school"))


class DatasetUnavailable(RuntimeError):
    """The dataset exists in the manifest but is not reachable from here."""


def _manifest() -> dict:
    with open(MANIFEST, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _entry(name: str) -> dict:
    manifest = _manifest()
    if name not in manifest:
        raise KeyError(
            f"No dataset {name!r} in {MANIFEST.name}. "
            f"Available: {', '.join(sorted(manifest))}"
        )
    return manifest[name]


def list_datasets() -> None:
    """Print the datasets in the manifest, with their day and access status."""
    for name, e in _manifest().items():
        print(f"  {name:<11} {e.get('day', '—'):<10} {e.get('access', '?'):<11} {e.get('title', '')}")


def describe(name: str) -> dict:
    """Return the manifest entry for one dataset."""
    return _entry(name)


def _unavailable(name: str, entry: dict, detail: str) -> DatasetUnavailable:
    note = (entry.get("note") or "").strip()
    where = os.environ.get("ATRIUM_ENV", "")
    msg = [f"Dataset {name!r} ({entry.get('title', '')}) is not available here.", detail]
    if note:
        msg += ["", note]
    if entry.get("access") == "restricted":
        msg += ["", "This dataset is restricted and is not in the repository by design."]
        if where in {"colab", "local"}:
            msg += ["Run this notebook on the school JupyterHub, where the folder is mounted."]
    return DatasetUnavailable("\n".join(msg))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _extract(archive: Path, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    if zipfile.is_zipfile(archive):
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(dest)
    elif tarfile.is_tarfile(archive):
        with tarfile.open(archive) as tf:
            # filter="data" refuses absolute paths and traversal outside dest.
            tf.extractall(dest, filter="data")
    else:
        raise DatasetUnavailable(f"{archive.name} is neither a zip nor a tar archive.")


def _collapse_single_dir(path: Path) -> Path:
    """An archive that unpacks to one wrapper folder shouldn't add a path segment."""
    children = [c for c in path.iterdir() if not c.name.startswith(".")]
    if len(children) == 1 and children[0].is_dir():
        return children[0]
    return path


def _zenodo_files(doi: str) -> list[tuple[str, str]]:
    """Resolve a Zenodo DOI to [(filename, download_url), ...]."""
    record_id = doi.rstrip("/").split(".")[-1]
    url = f"https://zenodo.org/api/records/{record_id}"
    with urllib.request.urlopen(url, timeout=60) as resp:
        record = json.load(resp)
    return [(f["key"], f["links"]["self"]) for f in record.get("files", [])]


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    print(f"  downloading {url}")
    with urllib.request.urlopen(url, timeout=300) as resp, open(dest, "wb") as out:
        shutil.copyfileobj(resp, out)


def _sources(entry: dict) -> list[dict]:
    """Every source for a dataset, in the order they should be tried."""
    if entry.get("sources"):
        return list(entry["sources"])
    return [entry.get("source") or {}]


def get_dataset(name: str, *, refresh: bool = False) -> Path:
    """Return a local directory holding the dataset's files.

    Downloads and unpacks on first use, then reads from the cache. Pass
    ``refresh=True`` to discard the cached copy and fetch again.

    A dataset with several sources tries them in order, so a folder that is only
    mounted on the hub can fall back to a public download elsewhere.
    """
    entry = _entry(name)
    failures = []
    for source in _sources(entry):
        try:
            return _from_source(name, entry, source, refresh=refresh)
        except DatasetUnavailable as exc:
            failures.append(str(exc))
    raise DatasetUnavailable("\n\n".join(failures) if failures else
                             f"Dataset {name!r} lists no usable source.")


def _from_source(name: str, entry: dict, source: dict, *, refresh: bool) -> Path:
    kind = source.get("kind")

    # --- already in the repository -------------------------------------
    if kind == "repo":
        path = _REPO_ROOT / source["path"]
        if not path.is_dir() or not any(path.iterdir()):
            raise _unavailable(
                name, entry,
                f"Expected files in {path}, but the folder is missing or empty.",
            )
        print(f"{name}: {path}  (in the repository)")
        return path

    # --- already mounted on the hub ------------------------------------
    if kind == "hub":
        path = Path(source["path"])
        if not path.is_dir():
            raise _unavailable(
                name, entry, f"Expected the mounted folder {path}, which is not there.",
            )
        print(f"{name}: {path}  (mounted on the hub)")
        return path

    # --- fetched and cached --------------------------------------------
    if kind not in {"url", "zenodo"}:
        raise _unavailable(name, entry, f"Unknown source kind {kind!r} in {MANIFEST.name}.")

    target = cache_dir() / name
    if target.is_dir() and any(target.iterdir()) and not refresh:
        print(f"{name}: {target}  (cached)")
        return target
    if refresh and target.exists():
        shutil.rmtree(target)

    if kind == "url" and "example.invalid" in source.get("url", ""):
        raise _unavailable(
            name, entry,
            "No download URL has been set for this dataset yet — "
            f"the manifest still has the placeholder {source['url']}.",
        )

    if kind == "zenodo":
        files = _zenodo_files(source["doi"])
        if not files:
            raise _unavailable(name, entry, f"Zenodo record for {source['doi']} lists no files.")
        urls = [u for _, u in files]
    else:
        urls = [source["url"]]

    with tempfile.TemporaryDirectory() as tmp:
        staged = Path(tmp) / "staged"
        staged.mkdir()
        for url in urls:
            archive = Path(tmp) / url.rstrip("/").split("/")[-1]
            try:
                _download(url, archive)
            except Exception as exc:  # network, 404, DNS ...
                raise _unavailable(name, entry, f"Could not download {url}\n  {exc}") from exc

            expected = source.get("sha256")
            if expected:
                actual = _sha256(archive)
                if actual != expected:
                    raise DatasetUnavailable(
                        f"Checksum mismatch for {name}.\n"
                        f"  expected {expected}\n  got      {actual}\n"
                        "The file on the server has changed, or the download was truncated."
                    )
            _extract(archive, staged)

        source_dir = _collapse_single_dir(staged)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source_dir), str(target))

    print(f"{name}: {target}  (downloaded, cached for next time)")
    return target
