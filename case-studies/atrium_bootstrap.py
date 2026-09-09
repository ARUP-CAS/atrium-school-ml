"""Make a notebook run the same way in Colab, on the school JupyterHub, and locally.

Every notebook starts with the same short cell::

    import sys, subprocess, pathlib
    REPO = "https://github.com/ARUP-CAS/atrium-school-ml.git"
    root = next((p for p in [pathlib.Path.cwd(), *pathlib.Path.cwd().parents]
                 if (p / "case-studies" / "atrium_bootstrap.py").exists()), None)
    if root is None:                                   # Colab, or a bare kernel
        root = pathlib.Path("atrium-school-ml").resolve()
        if not root.exists():
            subprocess.run(["git", "clone", "--depth", "1", REPO, str(root)], check=True)
    sys.path.insert(0, str(root / "case-studies"))
    from atrium_bootstrap import setup
    setup("torch", "transformers")

That cell is deliberately self-contained: on Colab nothing of this repository
exists yet when it runs, so it cannot import anything from here until it has
cloned. Everything after the clone lives in this module, so a fix reaches every
notebook at once.

``setup()`` does three things:

* installs only the packages that are actually missing, with the flags that
  suit the platform (``--user`` on the hub, the CPU wheel index for PyTorch off
  Colab);
* points the model cache and the dataset cache somewhere that survives as long
  as the platform allows;
* puts ``case-studies/`` on ``sys.path`` so ``from atrium_data import
  get_dataset`` works from any working directory.
"""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

__all__ = ["setup", "ensure", "where_am_i", "REPO_ROOT"]

_HERE = Path(__file__).resolve().parent
REPO_ROOT = _HERE.parent

#: pip name -> import name, only where the two differ.
_MODULE = {
    "pillow": "PIL",
    "pyyaml": "yaml",
    "opencv-python": "cv2",
    "opencv-python-headless": "cv2",
    "scikit-learn": "sklearn",
    "scikit-image": "skimage",
    "huggingface-hub": "huggingface_hub",
    "pillow-simd": "PIL",
}

#: Installed from the CPU index unless we are on Colab, which ships its own build.
_TORCH_FAMILY = {"torch", "torchvision", "torchaudio"}

_CPU_INDEX = [
    "--index-url", "https://download.pytorch.org/whl/cpu",
    "--extra-index-url", "https://pypi.org/simple",
]

#: Needed by essentially every notebook, so `setup()` always ensures them.
_CORE = ("pillow", "matplotlib", "requests", "pyyaml")


def where_am_i() -> str:
    """Return ``"colab"``, ``"hub"`` or ``"local"``."""
    if "google.colab" in sys.modules:
        return "colab"
    try:
        if importlib.util.find_spec("google.colab") is not None:
            return "colab"
    except (ImportError, ValueError):
        pass
    if os.environ.get("JUPYTERHUB_USER") or Path("/home/jovyan").is_dir():
        return "hub"
    return "local"


def _in_venv() -> bool:
    return sys.prefix != getattr(sys, "base_prefix", sys.prefix)


def _pip(packages: list[str], *, user: bool, extra_args: list[str] | None = None) -> None:
    cmd = [sys.executable, "-m", "pip", "install", "-q"]
    if user:
        cmd.append("--user")
    cmd += (extra_args or []) + packages
    subprocess.run(cmd, check=True)


def _missing(packages) -> list[str]:
    out = []
    for pkg in packages:
        module = _MODULE.get(pkg, pkg.replace("-", "_"))
        try:
            found = importlib.util.find_spec(module) is not None
        except (ImportError, ValueError):
            found = False
        if not found and pkg not in out:
            out.append(pkg)
    return out


def ensure(*packages: str, quiet: bool = False) -> list[str]:
    """Install whichever of ``packages`` are not importable. Returns what it installed."""
    env = where_am_i()
    # --user is what makes an install survive a hub respawn; it is also invalid
    # inside a virtual environment, where a plain install is already persistent.
    user = env == "hub" and not _in_venv()

    missing = _missing(packages)
    if not missing:
        if not quiet:
            print("packages: all present")
        return []

    torch_pkgs = [p for p in missing if p in _TORCH_FAMILY]
    other = [p for p in missing if p not in _TORCH_FAMILY]

    if torch_pkgs:
        # Off Colab, the default PyPI wheel drags in ~2.5 GB of CUDA runtime even
        # on a machine with no NVIDIA card. The CPU index is the whole difference
        # between a one-minute install and a coffee break.
        if not quiet:
            print(f"installing {', '.join(torch_pkgs)} (CPU build) ...")
        _pip(torch_pkgs, user=user, extra_args=None if env == "colab" else _CPU_INDEX)
    if other:
        if not quiet:
            print(f"installing {', '.join(other)} ...")
        _pip(other, user=user)

    # A --user install lands in a directory this interpreter may not have on its
    # path yet; make it importable without a kernel restart.
    if user:
        import site
        user_site = site.getusersitepackages()
        for path in ([user_site] if isinstance(user_site, str) else list(user_site)):
            if path not in sys.path:
                sys.path.append(path)
        importlib.invalidate_caches()

    return missing


def _mount_drive() -> Path | None:
    try:
        from google.colab import drive  # type: ignore
    except ImportError:
        return None
    drive.mount("/content/drive")
    return Path("/content/drive/MyDrive/atrium-school")


def _cache_root(env: str, drive: bool) -> Path:
    if env == "colab":
        if drive:
            mounted = _mount_drive()
            if mounted is not None:
                return mounted
        # Colab's disk is wiped when the runtime is recycled; caching here still
        # saves every re-run within one session.
        return Path("/content/atrium-cache")
    # Hub and local machines both have a home directory that persists.
    return Path.home() / ".cache"


def setup(*packages: str, drive: bool = False, quiet: bool = False) -> Path:
    """Prepare the current runtime and return the repository root.

    ``packages`` are the extras this notebook needs on top of the core four
    (pillow, matplotlib, requests, pyyaml) — e.g. ``setup("torch", "transformers")``.

    ``drive=True`` mounts Google Drive on Colab so model weights and datasets are
    downloaded once instead of once per session. It prompts for authorisation, so
    it is off by default.
    """
    env = where_am_i()

    root = _find_root() or REPO_ROOT
    case_studies = str(root / "case-studies")
    if case_studies not in sys.path:
        sys.path.insert(0, case_studies)

    cache = _cache_root(env, drive)
    os.environ.setdefault("HF_HOME", str(cache / "huggingface"))
    os.environ.setdefault("ATRIUM_CACHE", str(cache / "atrium-school"))
    os.environ.setdefault("ATRIUM_ENV", env)
    (cache / "huggingface").mkdir(parents=True, exist_ok=True)

    ensure(*_CORE, *packages, quiet=quiet)

    if not quiet:
        where = {"colab": "Google Colab", "hub": "JupyterHub", "local": "this machine"}[env]
        print(f"\nrunning on : {where}")
        print(f"repository : {root}")
        print(f"caches in  : {cache}")
        if env == "colab" and not drive:
            print("note       : Colab forgets this cache when the runtime is recycled.\n"
                  "             setup(..., drive=True) keeps it in your Google Drive.")
    return root


def _find_root() -> Path | None:
    """The repository root, whether we were started from it or cloned into it."""
    for candidate in [Path.cwd(), *Path.cwd().parents, REPO_ROOT]:
        if (candidate / "case-studies" / "atrium_data.py").exists():
            return candidate
    return None
