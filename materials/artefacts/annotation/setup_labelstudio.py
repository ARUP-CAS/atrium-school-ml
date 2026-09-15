"""Create the two Label Studio projects for the artefacts session and upload the photographs.

Run from the repository root, after select_images.py:

    export LS_URL=http://192.168.x.y:8080     # the Label Studio on the venue network
    export LS_API_KEY=...                     # Account & Settings -> Access Token
    python3 materials/artefacts/annotation/setup_labelstudio.py

Safe to re-run: a project whose title already exists is left alone (its images are not
uploaded twice). Delete the project in the UI to start it over.
"""

import json
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

HERE = Path("materials/artefacts/annotation")
IMAGES = Path("temp/annotation")

CONFIG = (HERE / "labelstudio" / "config.xml").read_text()

HANDS_ON = {
    "title": "Hands-on: AMČR-PAS",
    "description": "Ten photographs from AMČR-PAS. Everyone annotates all ten.",
    "expert_instruction": (
        "<p>Draw a <b>box</b> around each artefact, pick its <b>class</b>, and answer the "
        "questions for that box. Then answer the scale question for the whole photo.</p>"
        "<p>Not sure what something is? <b>Annotate it anyway</b> and write why in the note.</p>"
        "<p>Do not compare with your neighbour.</p>"),
    "show_instruction": True,
    # Community edition hides overlap in the UI, but honours the field: with 1 (the
    # default) the first person to submit a photo takes it out of everyone else's queue.
    "maximum_annotations": 100,
    "enable_empty_annotation": False,
    "sampling": "Sequential sampling",
    "color": "#2c7be5",
}
DEMO = {
    "title": "Demo: rosary",
    "description": "The deck's running example, for the live Label Studio demo.",
    "maximum_annotations": 100,
    "color": "#9ca3af",
}


class LabelStudio:
    def __init__(self, url, key):
        self.url = url.rstrip("/")
        self.s = requests.Session()
        # Personal access tokens (Label Studio 1.14+) are JWT refresh tokens and must be
        # exchanged for a short-lived access token; legacy tokens are used as they are.
        if key.count(".") == 2:
            r = requests.post(f"{self.url}/api/token/refresh", json={"refresh": key}, timeout=30)
            r.raise_for_status()
            self.s.headers["Authorization"] = f"Bearer {r.json()['access']}"
        else:
            self.s.headers["Authorization"] = f"Token {key}"

    def call(self, method, path, **kw):
        r = self.s.request(method, f"{self.url}{path}", timeout=120, **kw)
        if not r.ok:
            sys.exit(f"{method} {path} -> {r.status_code}\n{r.text[:1000]}")
        return r.json() if r.content else None

    def projects(self):
        out, page = [], 1
        while True:
            r = self.call("GET", "/api/projects", params={"page": page, "page_size": 100})
            if isinstance(r, list):          # older versions return a bare list
                return r
            out += r["results"]
            if not r.get("next"):
                return out
            page += 1

    def ensure_project(self, spec, files):
        existing = next((p for p in self.projects() if p["title"] == spec["title"]), None)
        if existing:
            print(f"exists   {spec['title']}  ({existing.get('task_number', '?')} tasks), left alone")
            return existing["id"]
        p = self.call("POST", "/api/projects", json={**spec, "label_config": CONFIG})
        # Upload the photographs themselves: they are stored in Label Studio's own media
        # folder, so the host needs no storage configuration and no access to this machine.
        # One form field per file: the import view keeps only one file per field name.
        # Tasks keep upload order (01 to 10) in the Data Manager. The label stream gives
        # that order only to the first person; with overlap > 1 everyone after gets the
        # ten in a random order ("breadth first"). Fine: it also stops copying.
        handles = {f.name: (f.name, f.open("rb"), "image/jpeg") for f in files}
        try:
            r = self.call("POST", f"/api/projects/{p['id']}/import", files=handles)
        finally:
            for _, fh, _ in handles.values():
                fh.close()
        print(f"created  {spec['title']}  ({r.get('task_count', len(files))} tasks)")
        return p["id"]


def check_labels_match():
    """The CVAT and Label Studio label sets must be the same list, or the demo contradicts
    the hands-on."""
    ls = [l.get("value") for l in ET.fromstring(CONFIG).iter("Label")]
    cvat = [l["name"] for l in json.loads((HERE / "cvat" / "labels.json").read_text())
            if l["type"] != "tag"]
    if ls != cvat:
        sys.exit(f"label mismatch\n  labelstudio: {ls}\n  cvat:        {cvat}")


def main():
    check_labels_match()
    url, key = os.environ.get("LS_URL"), os.environ.get("LS_API_KEY")
    if not (url and key):
        sys.exit("set LS_URL and LS_API_KEY (Account & Settings -> Access Token)")
    hands_on = sorted((IMAGES / "images").glob("*.jpg"))
    demo = sorted((IMAGES / "demo").glob("*.jpg"))
    if len(hands_on) != 10 or not demo:
        sys.exit("run select_images.py first")

    ls = LabelStudio(url, key)
    pid = ls.ensure_project(HANDS_ON, hands_on)
    ls.ensure_project(DEMO, demo)

    print(f"\nhands-on project   {ls.url}/projects/{pid}/data")
    # The invite link lets participants create their own accounts in this organisation.
    try:
        invite = ls.s.get(f"{ls.url}/api/invite", timeout=30).json()
        print(f"participant signup {ls.url}{invite['invite_url']}")
    except (requests.RequestException, KeyError, ValueError):
        print("participant signup  Organization page -> Add People -> copy the invite link")


if __name__ == "__main__":
    main()
