"""Build the figures and chart data for the artefacts deck from the sources in temp/.

Run from the repository root:  python3 materials/artefacts/make_images.py

The source photographs and the AMCR-PAS COCO export stay in temp/ (not committed);
the finished figures go to materials/artefacts/img/ and the aggregates the R chunks
in artefacts.qmd read go to materials/artefacts/data/. Both are committed, so the
deck renders on a machine that has never seen temp/.

Conventions (palette, helpers, font handling) follow materials/intro/make_images.py;
the two decks share one image and one colour code for it, deliberately.
"""

import csv
import json
from collections import Counter
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle
import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

SRC = Path("temp")
OUT = Path("materials/artefacts/img")
DATA = Path("materials/artefacts/data")
OUT.mkdir(parents=True, exist_ok=True)
DATA.mkdir(parents=True, exist_ok=True)

# The deck's palette — the same one as the intro deck (see materials/intro/slides.scss).
BLUE = "#2c7be5"
ORANGE = "#c2410c"
INK = "#1c2128"
MUTE = "#6b7280"
LIGHT = "#e5e7eb"
GREEN = "#0e9f6e"
# Monday showed this photograph with these colours. Keep them.
CLASS_COLOURS = {"bead": GREEN, "cross": "#db2777", "rosary/medallion": BLUE}

for f in Path.home().joinpath(".local/share/fonts").glob("AlegreyaSans-*.ttf"):
    font_manager.fontManager.addfont(str(f))
FAMILY = "Alegreya Sans" if any(f.name == "Alegreya Sans" for f in font_manager.fontManager.ttflist) else "sans-serif"
plt.rcParams.update({"font.family": FAMILY, "font.size": 14, "text.color": INK,
                     "axes.edgecolor": MUTE, "savefig.facecolor": "white"})

# --- COCO annotations -------------------------------------------------------

_coco = json.loads((SRC / "amcr-pas_v0.json").read_text())
_cats = {c["id"]: c["name"] for c in _coco["categories"]}


def coco_annotations(stem):
    """Annotations for the image whose file name contains `stem`, as (category, bbox, polygons, attributes)."""
    img = next(i for i in _coco["images"] if stem in i["file_name"])
    anns = [a for a in _coco["annotations"] if a["image_id"] == img["id"]]
    return img, [(_cats[a["category_id"]], a["bbox"],
                  [np.array(s).reshape(-1, 2) for s in a["segmentation"]],
                  a.get("attributes", {})) for a in anns]


def load(name):
    return Image.open(SRC / name).convert("RGB")


def canvas(w_px, h_px, dpi=100):
    fig = plt.figure(figsize=(w_px / dpi, h_px / dpi), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    return fig, ax


def save_jpg(fig, name, dpi=100, bbox=False):
    tmp = OUT / (name + ".tmp.png")
    fig.savefig(tmp, dpi=dpi, **({"bbox_inches": "tight", "pad_inches": 0.05} if bbox else {}))
    plt.close(fig)
    Image.open(tmp).convert("RGB").save(OUT / name, quality=86, optimize=True, progressive=True)
    tmp.unlink()


def save_png(fig, name, dpi=200, bbox=True):
    fig.savefig(OUT / name, dpi=dpi, **({"bbox_inches": "tight", "pad_inches": 0.08} if bbox else {}))
    plt.close(fig)


def label_chip(ax, x, y, text, colour=BLUE, size=15, ha="left", va="top"):
    ax.text(x, y, text, color="white", fontsize=size, fontweight="bold", ha=ha, va=va,
            bbox=dict(boxstyle="round,pad=0.3,rounding_size=0.25", fc=colour, ec="none"))


# The rosary from Monday's segmentation slide: ten annotations, three classes,
# every one of them a polygon. One photograph carries the whole session.
ROSARY = "M202400071N00083F01"
CROP = (560, 20, 3800, 2450)        # 4:3 around the find, scale bar cut off
PANEL = (800, 600)


def _rosary_panel(ax, title):
    x0, y0, x1, y1 = CROP
    im = load(ROSARY + ".JPG").crop(CROP).resize(PANEL, Image.LANCZOS)
    ax.imshow(im)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color(LIGHT); s.set_linewidth(1)
    ax.set_title(title, fontsize=21, pad=7, color=INK, loc="left")
    return PANEL[0] / (x1 - x0)


# --- 1. What "annotated" can mean -------------------------------------------

def annotation_levels():
    """One photograph at four levels of annotation: label, boxes, polygons, attributes."""
    x0, y0 = CROP[0], CROP[1]
    _, anns = coco_annotations(ROSARY)
    big_to_small = sorted(anns, key=lambda a: -a[1][2] * a[1][3])

    fig, axs = plt.subplots(2, 2, figsize=(15.4, 12.0))
    (a, b), (c, d) = axs

    # 1 — an image-level label. One string for the whole photograph.
    _rosary_panel(a, "1 · a label — one string for the photograph")
    label_chip(a, 22, PANEL[1] - 22, "rosary/medallion", size=30, va="bottom")

    # 2 — bounding boxes. Ten of them, one per object.
    s = _rosary_panel(b, f"2 · boxes — {len(anns)} objects, where each one is")
    for cat, (x, y, w, h), _, _ in anns:
        b.add_patch(Rectangle(((x - x0) * s, (y - y0) * s), w * s, h * s,
                              fill=False, ec=CLASS_COLOURS[cat], lw=2.2))

    # 3 — polygons. The same ten objects, to the pixel.
    s = _rosary_panel(c, "3 · polygons — the same objects, to the pixel")
    for cat, _, polys, _ in big_to_small:
        for p in polys:
            c.add_patch(Polygon((p - [x0, y0]) * s, closed=True, fc=CLASS_COLOURS[cat],
                                ec=CLASS_COLOURS[cat], alpha=0.55, lw=1.6))

    # 4 — attributes. What is true of the object beyond its class.
    s = _rosary_panel(d, "4 · attributes — what else is true of it")
    for cat, _, polys, _ in big_to_small:
        for p in polys:
            d.add_patch(Polygon((p - [x0, y0]) * s, closed=True, fill=False,
                                ec=CLASS_COLOURS[cat], lw=2.0, alpha=0.9))
    attrs = anns[0][3]
    lines = [f"{k}: {str(v).lower()}" for k, v in attrs.items()] + ["complete: ?", "corroded: ?", "has scale: ?"]
    # Top-left: the emptiest quarter of this photograph. Anywhere else the panel
    # sits on the cross or the medallion, which are the objects worth seeing.
    d.add_patch(FancyBboxPatch((18, 16), 360, 282, boxstyle="round,pad=8,rounding_size=10",
                               fc="white", ec=LIGHT, lw=1.5, alpha=0.94, zorder=4))
    for i, t in enumerate(lines):
        known = i < len(attrs)
        d.text(42, 54 + i * 44, t, fontsize=23, va="top", zorder=5,
               color=INK if known else ORANGE, fontweight="medium" if known else "bold")

    fig.subplots_adjust(wspace=0.04, hspace=0.13)
    save_jpg(fig, "annotation-levels.jpg", dpi=100, bbox=True)


# --- 2. What a polygon costs ------------------------------------------------

def polygon_cost():
    """Every vertex of every polygon on one photograph, and what that is in clicks."""
    x0, y0, x1, y1 = CROP
    _, anns = coco_annotations(ROSARY)
    verts = sum(len(p) for _, _, polys, _ in anns for p in polys)

    im = load(ROSARY + ".JPG").crop(CROP).resize((1280, 960), Image.LANCZOS)
    s = 1280 / (x1 - x0)
    fig, ax = canvas(1280, 960)
    ax.imshow(im)
    for cat, _, polys, _ in sorted(anns, key=lambda a: -a[1][2] * a[1][3]):
        for p in polys:
            q = (p - [x0, y0]) * s
            ax.add_patch(Polygon(q, closed=True, fill=False, ec=CLASS_COLOURS[cat], lw=1.8, alpha=0.85))
            ax.plot(q[:, 0], q[:, 1], "o", ms=5.5, mfc="white", mec=CLASS_COLOURS[cat], mew=1.8,
                    linestyle="none", zorder=4)
    label_chip(ax, 22, 938, f"{len(anns)} objects · {verts} vertices · {verts} clicks by hand",
               colour=INK, size=31, va="bottom")
    save_jpg(fig, "polygon-cost.jpg")
    return verts


# --- 3. The long tail -------------------------------------------------------

def category_tables():
    """Write the aggregates the R chunks in artefacts.qmd chart, so the 18 MB JSON
    is never opened at render time."""
    cnt = Counter(_cats[a["category_id"]] for a in _coco["annotations"])
    total = sum(cnt.values())

    with (DATA / "category_counts.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["category", "n", "pct"])
        for name, n in cnt.most_common():
            w.writerow([name, n, round(100 * n / total, 2)])

    n_imgs = len(_coco["images"])
    with_ann = len({a["image_id"] for a in _coco["annotations"]})
    declared = len(_coco["categories"])
    used = len(cnt)
    top5 = sum(n for _, n in cnt.most_common(5))
    small = [n for n in cnt.values() if n < 50]

    rows = [
        ("images", n_imgs),
        ("images_with_annotations", with_ann),
        ("annotations", total),
        ("categories_declared", declared),
        ("categories_used", used),
        ("categories_never_used", declared - used),
        ("fibula", cnt["fibula"]),
        ("coin", cnt["coin"]),
        ("fibula_coin_pct", round(100 * (cnt["fibula"] + cnt["coin"]) / total, 1)),
        ("top5_pct", round(100 * top5 / total, 1)),
        ("categories_under_50", len(small)),
        ("under_50_pct", round(100 * sum(small) / total, 1)),
        ("max_annotations_per_image", max(Counter(a["image_id"] for a in _coco["annotations"]).values())),
    ]
    with (DATA / "dataset_summary.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["key", "value"])
        w.writerows(rows)
    return dict(rows)


# --- 4. One annotation, three formats ---------------------------------------

def format_example():
    """The same annotation written out as COCO, YOLO and Pascal VOC, so the slide
    quotes real numbers rather than invented ones."""
    meta, anns = coco_annotations(ROSARY)
    cat, (x, y, w, h), polys, attrs = next(a for a in anns if a[0] == "cross")
    W, H = meta["width"], meta["height"]
    # YOLO: class index, then the box as centre-x, centre-y, width, height, all
    # normalised to the image. The class *name* is not in the file.
    yolo = f"2 {(x + w / 2) / W:.6f} {(y + h / 2) / H:.6f} {w / W:.6f} {h / H:.6f}"
    # Pascal VOC: absolute corners, one XML file per image.
    voc = (f"<object>\n  <name>{cat}</name>\n  <bndbox>\n"
           f"    <xmin>{round(x)}</xmin> <ymin>{round(y)}</ymin>\n"
           f"    <xmax>{round(x + w)}</xmax> <ymax>{round(y + h)}</ymax>\n"
           f"  </bndbox>\n</object>")
    poly = polys[0]
    coco = {"id": "…", "image_id": "…", "category_id": "…",
            "bbox": [round(v, 1) for v in (x, y, w, h)],
            "area": round(w * h, 1),
            "segmentation": [[round(v, 1) for v in poly[:3].reshape(-1)] + ["…"]],
            "iscrowd": 0, "attributes": attrs}
    (DATA / "format_example.txt").write_text(
        f"image: {meta['file_name']}  {W} x {H}\n"
        f"category: {cat}   vertices: {len(poly)}\n\n"
        f"--- COCO (one entry in `annotations`) ---\n{json.dumps(coco, indent=2)}\n\n"
        f"--- YOLO ({Path(meta['file_name']).stem}.txt) ---\n{yolo}\n\n"
        f"--- Pascal VOC ({Path(meta['file_name']).stem}.xml) ---\n{voc}\n")
    return yolo, len(poly)


# --- 5. Mapping between vocabularies ----------------------------------------

def skos_crosswalk():
    """Three vocabularies, one concept, and the three ways they fail to line up.

    Term labels are real (AMCR-PAS categories are taken from the COCO file); the
    identifiers belong on the slide only once they have been checked against the
    live vocabularies — see the prerequisites in the session plan.
    """
    W, H = 1620, 780
    fig, ax = canvas(W, H)
    ax.set_xlim(0, W); ax.set_ylim(H, 0)

    HALF = 178
    cols = [(200, "AMČR-PAS", BLUE, ["fibula", "clothing pin", "buckle"]),
            (810, "another dataset", ORANGE, ["brooch", "pin", "buckle/strap-end"]),
            (1420, "Getty AAT", MUTE, ["fibulae (fasteners)", "pins (fasteners)", "buckles"])]
    ys = [268, 428, 588]

    for x, title, colour, terms in cols:
        ax.text(x, 168, title, fontsize=30, fontweight="bold", color=colour, ha="center")
        for y, t in zip(ys, terms):
            ax.add_patch(FancyBboxPatch((x - HALF, y - 33), 2 * HALF, 66,
                                        boxstyle="round,pad=0,rounding_size=10",
                                        fc="white", ec=colour, lw=2.2))
            ax.text(x, y, t, fontsize=24, ha="center", va="center", color=INK)

    def arrow(col_a, col_b, y, text, colour, style="<|-|>", dashed=False):
        x1, x2 = cols[col_a][0] + HALF, cols[col_b][0] - HALF
        ax.add_patch(FancyArrowPatch((x1, y), (x2, y), arrowstyle=style, mutation_scale=17,
                                     lw=2, color=colour, shrinkA=6, shrinkB=6,
                                     linestyle=(0, (5, 3)) if dashed else "solid"))
        ax.text((x1 + x2) / 2, y - 26, text, fontsize=20, ha="center", va="center",
                color=colour, style="italic",
                bbox=dict(boxstyle="round,pad=0.18", fc="white", ec="none"))

    arrow(0, 1, ys[0], "skos:exactMatch", GREEN)
    arrow(1, 2, ys[0], "skos:closeMatch", MUTE)
    arrow(0, 1, ys[1], "skos:closeMatch", MUTE)
    arrow(1, 2, ys[1], "skos:closeMatch", MUTE)
    # The row that does not line up: one label covering two kinds of object.
    arrow(0, 1, ys[2], "skos:broadMatch", ORANGE, style="-|>")
    arrow(1, 2, ys[2], "?", ORANGE, style="-", dashed=True)
    ax.text(810, 690, "“buckle/strap-end” is two objects in one label — no mapping recovers which",
            fontsize=20, ha="center", color=ORANGE, style="italic")

    ax.text(W / 2, 62, "One concept, three vocabularies", fontsize=32, fontweight="bold",
            ha="center", color=INK)
    save_png(fig, "skos-crosswalk.png", dpi=110, bbox=True)


if __name__ == "__main__":
    summary = category_tables()
    verts = polygon_cost()
    yolo, n_poly = format_example()
    annotation_levels()
    skos_crosswalk()
    print(f"figures  -> {OUT}")
    print(f"data     -> {DATA}")
    print(f"vertices on the rosary photograph: {verts}")
    print(f"cross polygon: {n_poly} vertices; YOLO line: {yolo}")
    for k, v in summary.items():
        print(f"  {k:32} {v}")
