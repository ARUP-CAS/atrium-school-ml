"""Pick, downscale and package the photographs for the hands-on annotation projects.

Run from the repository root:  python3 materials/artefacts/annotation/select_images.py

Reads the AMČR-PAS COCO export and its photographs from the FiftyOne copy of the dataset
(FIFTYONE_ROOT, default ~/Documents/fiftyone), and writes:

  temp/annotation/images/        the 10 hands-on photographs, 1600 px long edge
  temp/annotation/demo/          the rosary, for the live demo
  temp/annotation/cvat-images.zip  all 11, for the CVAT task
  temp/annotation/contact-sheet.jpg  the 10 with their reference boxes, for checking by eye
  materials/artefacts/annotation/images.csv          what was picked and why (committed)
  materials/artefacts/annotation/reference_coco.json the original annotations for the 10,
                                                     rescaled to the downscaled images

Photographs are CC BY-NC 4.0 and stay in temp/ (not committed); images.csv carries the DOIs.

With LESSONS_DIR set (the lessons repository's 2-tuesday-artefacts/ folder), it also
refreshes what participants download: images/, labels.json and credits.csv.
"""

import csv
import json
import os
import re
import shutil
import zipfile
from collections import defaultdict
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

Image.MAX_IMAGE_PIXELS = None

FIFTYONE = Path(os.environ.get("FIFTYONE_ROOT", Path.home() / "Documents/fiftyone"))
COCO = FIFTYONE / "datasets/amcr-pas/amcr-pas_v0.filtered.json"
HERE = Path("materials/artefacts/annotation")
OUT = Path("temp/annotation")
LONG_EDGE = 1600

# The ten photographs, in Data Manager order: two easy ones first, the planted
# ambiguities in the middle. (Only the first person through the label stream gets this
# order; see setup_labelstudio.py.) Three scales are drawn-on "0–5 cm" bars rather than
# rulers in the frame, which is its own small disagreement for the scale question.
PICKS = [
    ("M202400098N00219F01", "a whole fibula; the easy start"),
    ("M202400071N00009F01", "three coins; a group, several boxes"),
    ("C202109132N00575F01", "a fibula missing its pin; fragment or damaged?"),
    ("M202101534N00375F02", "PLANTED: a pierced coin, recorded as a pendant"),
    ("M202301170N00252F01", "a buckle frame"),
    ("M202300130N00146F02", "PLANTED: a crescent recorded as a mount; reads as a pendant"),
    ("M202105244N00015F01", "rings, one lying inside another; circle/ring or finger ring, and occlusion"),
    ("M202105567N00005F01", "PLANTED: coins fused into a corroded lump; how many objects?"),
    ("M202400071N00027F02", "a spur with its rowel, a buckle and fittings; which parts get their own box?"),
    ("M202301170N00112F01", "a pin head the recorder marked unrecognizable"),
]
DEMO = "M202400071N00083F01"  # the rosary, the deck's running example


def record_id(stem):
    """M202400071N00083F01 -> M-202400071-N00083 (the AMČR record; F01 is the file)."""
    m = re.fullmatch(r"([A-Z])(\d{9})(N\d{5})F\d{2}", stem)
    return f"{m[1]}-{m[2]}-{m[3]}"


def downscale(src, dst):
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    s = min(1.0, LONG_EDGE / max(im.size))
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, quality=85, optimize=True, progressive=True)
    return im, s


def main():
    coco = json.loads(COCO.read_text())
    cats = {c["id"]: c["name"] for c in coco["categories"]}
    by_stem = {Path(i["file_name"]).stem: i for i in coco["images"]}
    anns = defaultdict(list)
    for a in coco["annotations"]:
        anns[a["image_id"]].append(a)

    rows, ref_images, ref_anns, thumbs = [], [], [], []
    for n, (stem, why) in enumerate(PICKS, 1):
        img = by_stem[stem]
        name = f"{n:02d}_{stem}.jpg"
        im, s = downscale(FIFTYONE / img["file_name"], OUT / "images" / name)
        own = anns[img["id"]]
        rid = record_id(stem)
        rows.append({
            "order": n, "file": name, "record": rid, "doi": f"https://doi.org/10.71928/{rid}",
            "reference_classes": "; ".join(sorted({cats[a["category_id"]] for a in own})),
            "objects": len(own),
            "unrecognizable": sum(a.get("attributes", {}).get("recognizable") == "false" for a in own),
            "why": why,
        })
        ref_images.append({"id": n, "file_name": name, "width": im.width, "height": im.height})
        for a in own:
            ref_anns.append({"id": len(ref_anns) + 1, "image_id": n, "category_id": a["category_id"],
                             "bbox": [round(v * s, 1) for v in a["bbox"]],
                             "attributes": a.get("attributes", {})})
        thumbs.append((im, [(a["bbox"], s) for a in own], f"{n:02d} {rows[-1]['reference_classes']}"))

    downscale(Path("temp") / f"{DEMO}.JPG", OUT / "demo" / f"{DEMO}.jpg")

    with (HERE / "images.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)
    used = {a["category_id"] for a in ref_anns}
    (HERE / "reference_coco.json").write_text(json.dumps({
        "info": {"description": "AMČR-PAS reference annotations for the hands-on images, "
                                "rescaled to the 1600 px copies. Source: amcr-pas_v0.json."},
        "images": ref_images,
        "categories": [{"id": i, "name": cats[i]} for i in sorted(used)],
        "annotations": ref_anns,
    }, ensure_ascii=False, indent=1))

    with zipfile.ZipFile(OUT / "cvat-images.zip", "w") as z:
        for p in sorted((OUT / "images").glob("*.jpg")) + [OUT / "demo" / f"{DEMO}.jpg"]:
            z.write(p, p.name)

    contact_sheet(thumbs, OUT / "contact-sheet.jpg")
    for r in rows:
        print(f"{r['order']:>2}  {r['record']}  {r['reference_classes']:<32} {r['why']}")
    if os.environ.get("LESSONS_DIR"):
        publish(rows, Path(os.environ["LESSONS_DIR"]))


def publish(rows, dst):
    """Copy what participants download into the lessons repository. No reference classes
    and no 'why' column: the planted answers must not be in the participants' folder."""
    (dst / "images").mkdir(parents=True, exist_ok=True)
    for r in rows:
        shutil.copyfile(OUT / "images" / r["file"], dst / "images" / r["file"])
    shutil.copyfile(HERE / "cvat" / "labels.json", dst / "labels.json")
    with (dst / "credits.csv").open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["filename", "doi"])
        w.writerows([r["file"], r["doi"]] for r in rows)
    print(f"published -> {dst}")


def contact_sheet(thumbs, dst, cols=5, tw=340):
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 15)
    except OSError:
        font = ImageFont.load_default()
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * (tw + 26)), "white")
    d = ImageDraw.Draw(sheet)
    for k, (im, boxes, label) in enumerate(thumbs):
        t = tw / max(im.size)
        x, y = (k % cols) * tw, (k // cols) * (tw + 26)
        sheet.paste(im.resize((round(im.width * t), round(im.height * t))), (x, y))
        for (bx, by, bw, bh), s in boxes:
            d.rectangle([x + bx * s * t, y + by * s * t, x + (bx + bw) * s * t, y + (by + bh) * s * t],
                        outline=(220, 38, 38), width=2)
        d.text((x + 4, y + tw + 4), label[:40], fill="black", font=font)
    sheet.save(dst, quality=85)


if __name__ == "__main__":
    main()
