"""Build the figures for the intro deck from the source photographs in temp/.

Run from the repository root:  python3 materials/intro/make_images.py
Source photographs and the AMCR-PAS COCO export stay in temp/ (not committed);
the finished figures are written to materials/intro/img/.
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle, ConnectionPatch
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.interpolate import PchipInterpolator
from scipy.stats import gaussian_kde

Image.MAX_IMAGE_PIXELS = None

SRC = Path("temp")
OUT = Path("materials/intro/img")
OUT.mkdir(parents=True, exist_ok=True)

# The deck's palette (see the setup chunk in intro.qmd and slides.scss).
BLUE = "#2c7be5"   # discriminative
ORANGE = "#c2410c"  # generative
INK = "#1c2128"
MUTE = "#6b7280"
LIGHT = "#e5e7eb"
CLASS_COLOURS = {"bead": "#0e9f6e", "cross": "#db2777", "rosary/medallion": BLUE}

for f in Path.home().joinpath(".local/share/fonts").glob("AlegreyaSans-*.ttf"):
    font_manager.fontManager.addfont(str(f))
FAMILY = "Alegreya Sans" if any(f.name == "Alegreya Sans" for f in font_manager.fontManager.ttflist) else "sans-serif"
plt.rcParams.update({"font.family": FAMILY, "font.size": 14, "text.color": INK,
                     "axes.edgecolor": MUTE, "savefig.facecolor": "white"})

# --- COCO annotations -------------------------------------------------------

_coco = json.loads((SRC / "amcr-pas_v0.json").read_text())
_cats = {c["id"]: c["name"] for c in _coco["categories"]}


def coco_annotations(stem):
    """Annotations for the image whose file name contains `stem`, as (category, bbox, polygons)."""
    img = next(i for i in _coco["images"] if stem in i["file_name"])
    anns = [a for a in _coco["annotations"] if a["image_id"] == img["id"]]
    return img, [(_cats[a["category_id"]], a["bbox"],
                  [np.array(s).reshape(-1, 2) for s in a["segmentation"]]) for a in anns]


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


# --- A. What computer vision is ---------------------------------------------

def image_as_array():
    im = load("sherd_02.jpg")
    arr = np.asarray(im)
    crop = arr[60:470, 190:760]                   # sherd, without most of the scale bar
    zy, zx, zs = 118, 150, 36                      # zoom window (in crop coordinates)
    zoom = crop[zy:zy + zs, zx:zx + zs]
    gy, gx, gs = 14, 12, 8                         # the 8 x 8 grid shown as numbers
    grid = zoom[gy:gy + gs, gx:gx + gs]

    fig, axs = plt.subplots(1, 3, figsize=(13.5, 4.8), gridspec_kw={"width_ratios": [1.39, 1, 1]})
    for ax in axs:
        ax.set_xticks([]); ax.set_yticks([])
    a0, a1, a2 = axs

    a0.imshow(crop)
    a0.add_patch(Rectangle((zx - .5, zy - .5), zs, zs, fill=False, ec=BLUE, lw=2))
    a0.set_title("a photograph", fontsize=17, pad=8)
    for s in a0.spines.values(): s.set_visible(False)

    a1.imshow(zoom, interpolation="nearest")
    a1.add_patch(Rectangle((gx - .5, gy - .5), gs, gs, fill=False, ec=BLUE, lw=2))
    a1.set_title(f"{zs} × {zs} pixels of it", fontsize=17, pad=8)
    for s in a1.spines.values(): s.set_color(BLUE); s.set_linewidth(2)

    red = grid[..., 0]
    a2.imshow(grid, interpolation="nearest")
    for (r, c), v in np.ndenumerate(red):
        lum = grid[r, c] @ [0.299, 0.587, 0.114]
        a2.text(c, r, str(v), ha="center", va="center", fontsize=12.5,
                color="white" if lum < 150 else INK, fontweight="medium")
    a2.set_title(f"{gs} × {gs} of those, red channel", fontsize=17, pad=8)
    for s in a2.spines.values(): s.set_color(BLUE); s.set_linewidth(2)

    for (xa, ya), (xb, yb) in [((zx + zs - .5, zy - .5), (-.5, -.5)),
                               ((zx + zs - .5, zy + zs - .5), (-.5, zs - .5))]:
        fig.add_artist(ConnectionPatch((xa, ya), (xb, yb), "data", "data", axesA=a0, axesB=a1, color=BLUE, lw=1, alpha=.6))
    for (xa, ya), (xb, yb) in [((gx + gs - .5, gy - .5), (-.5, -.5)),
                               ((gx + gs - .5, gy + gs - .5), (-.5, gs - .5))]:
        fig.add_artist(ConnectionPatch((xa, ya), (xb, yb), "data", "data", axesA=a1, axesB=a2, color=BLUE, lw=1, alpha=.6))
    fig.subplots_adjust(wspace=0.12)
    save_png(fig, "image-as-array.png", dpi=180)


def semantic_gap():
    im = load("sherd_02.jpg")
    arr = np.asarray(im)[80:430, 200:740]
    grey = arr.astype(float) @ [0.299, 0.587, 0.114]
    mag = np.hypot(ndimage.sobel(grey, 0), ndimage.sobel(grey, 1))
    mag = np.clip(mag / np.percentile(mag, 99.5), 0, 1)

    fig, (a0, a1) = plt.subplots(1, 2, figsize=(11, 3.7))
    a0.imshow(arr)
    a1.imshow(1 - mag, cmap="gray", vmin=0, vmax=1)
    for ax in (a0, a1):
        ax.set_axis_off()
    fig.subplots_adjust(wspace=0.06)
    save_png(fig, "semantic-gap.png", dpi=160)


def data_deluge():
    """Aerial survey, excavation and a 1984 archive photograph, side by side at the same height."""
    h = 900
    tiles = []
    for name, box in [("CDL201000159.tif", None), ("C200913914ADT05281.tif", None), ("P_HP84_16.tif", None)]:
        im = load(name)
        if box: im = im.crop(box)
        tiles.append(im.resize((round(im.width * h / im.height), h), Image.LANCZOS))
    gap = 24
    out = Image.new("RGB", (sum(t.width for t in tiles) + gap * (len(tiles) - 1), h), "white")
    x = 0
    for t in tiles:
        out.paste(t, (x, 0)); x += t.width + gap
    out.save(OUT / "data-deluge.jpg", quality=84, optimize=True, progressive=True)


# --- B. The four task shapes ------------------------------------------------

def task_classification():
    im = load("coin_01.jpg")                     # = M202101534N00243F02, 1024 px wide
    im = im.crop((197, 40, 827, 512))              # 4:3 around the coin
    fig, ax = canvas(*im.size)
    ax.imshow(im)
    ax.add_patch(Rectangle((4, 4), im.width - 9, im.height - 9, fill=False, ec=BLUE, lw=6))
    label_chip(ax, 18, 18, "coin", size=40)
    save_jpg(fig, "task-classification.jpg")


def task_detection():
    im = load("sherd_03.jpg")                     # = M202300087N00510F01, downscaled
    meta, anns = coco_annotations("M202300087N00510F01")
    s = im.width / meta["width"]
    fig, ax = canvas(*im.size)
    ax.imshow(im)
    for cat, (x, y, w, h), _ in anns:
        ax.add_patch(Rectangle((x * s, y * s), w * s, h * s, fill=False, ec=BLUE, lw=2.4))
    label_chip(ax, 12, im.height - 12, f"potsherd × {len(anns)}", size=44, va="bottom")
    save_jpg(fig, "task-detection.jpg")


def task_segmentation():
    im = load("M202400071N00083F01.JPG")
    meta, anns = coco_annotations("M202400071N00083F01")
    x0, y0, x1, y1 = 560, 20, 3800, 2450           # 4:3 around the rosary, scale bar cut off
    im = im.crop((x0, y0, x1, y1)).resize((1024, 768), Image.LANCZOS)
    s = 1024 / (x1 - x0)
    fig, ax = canvas(*im.size)
    ax.imshow(im)
    # Largest first, so the beads and the cross sit on top of the chain.
    for cat, _, polys in sorted(anns, key=lambda a: -a[1][2] * a[1][3]):
        for p in polys:
            q = (p - [x0, y0]) * s
            ax.add_patch(Polygon(q, closed=True, fc=CLASS_COLOURS[cat], ec=CLASS_COLOURS[cat],
                                 alpha=0.55, lw=1.6))
    y = im.height - 20
    x = 22
    for cat in ["rosary/medallion", "bead", "cross"]:
        t = ax.text(x, y, cat, color="white", fontsize=34, fontweight="bold", va="bottom",
                    bbox=dict(boxstyle="round,pad=0.3,rounding_size=0.25", fc=CLASS_COLOURS[cat], ec="none"))
        fig.canvas.draw()
        x = ax.transData.inverted().transform(t.get_window_extent().corners()[-1])[0] + 34
    save_jpg(fig, "task-segmentation.jpg")


def task_keypoints():
    """A vessel drawn in the usual convention: section on the left, exterior on the right.
    4:3 like the three photographs beside it, with labels large enough for a quarter-width column."""
    z = np.array([0, 0.25, 2.0, 4.6, 7.0, 7.9, 8.6, 9.0])          # height
    r = 0.72 * np.array([2.6, 2.9, 4.6, 6.0, 4.6, 3.9, 4.3, 4.7])  # outer radius
    zz = np.linspace(0, 9, 300)
    rr = PchipInterpolator(z, r)(zz)
    t = 0.3                                                         # wall thickness

    fig, ax = canvas(1024, 768)
    ax.set_aspect("equal")
    ax.set_xlim(-5.0, 9.67); ax.set_ylim(-0.9, 10.1)
    # Exterior view (right half), rim line and centre line.
    ax.plot(rr, zz, color=INK, lw=3)
    ax.plot([0, rr[0]], [0, 0], color=INK, lw=3)
    ax.plot([-rr[-1], rr[-1]], [9, 9], color=INK, lw=1.5)
    ax.plot([0, 0], [-0.5, 9.6], color=MUTE, lw=1.5, ls=(0, (6, 3)))
    # Section (left half), filled.
    inner = np.clip(rr - t, 0, None)
    wall = np.vstack([np.column_stack([-rr, zz]), np.column_stack([-inner, zz])[::-1]])
    ax.add_patch(Polygon(wall, closed=True, fc=INK, ec=INK))
    ax.add_patch(Rectangle((-inner[0], 0), inner[0], 0.3, fc=INK, ec=INK))

    at = lambda h: float(rr[np.argmin(np.abs(zz - h))])
    pts = [("rim", rr[-1], 9.0), ("neck", at(7.9), 7.9),
           ("max. Ø", float(rr.max()), float(zz[rr.argmax()])), ("base", rr[0], 0.0)]
    for name, x, y in pts:
        ax.plot(x, y, "o", ms=20, mfc=BLUE, mec="white", mew=3, zorder=5)
        ax.text(x + 0.6, y, name, fontsize=40, color=BLUE, fontweight="bold", va="center", ha="left")
    ax.plot(0, 0, "o", ms=20, mfc=BLUE, mec="white", mew=3, zorder=5)
    save_png(fig, "task-keypoints.png", dpi=100, bbox=False)


# --- E. Diagrams --------------------------------------------------------------

_rng = np.random.default_rng(14)
_A = _rng.multivariate_normal([-1.2, 0.6], [[0.55, 0.2], [0.2, 0.45]], 45)
_B = _rng.multivariate_normal([1.3, -0.5], [[0.5, -0.1], [-0.1, 0.6]], 45)


def _feature_space(ax):
    ax.scatter(*_A.T, s=46, c=INK, edgecolors="white", linewidths=0.8, zorder=3)
    ax.scatter(*_B.T, s=46, facecolors="white", edgecolors=INK, linewidths=1.4, zorder=3)
    ax.set_xlim(-3.6, 3.8); ax.set_ylim(-3.1, 3.0)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ["top", "right"]: ax.spines[s].set_visible(False)
    ax.set_xlabel("feature 1", color=MUTE, fontsize=15)
    ax.set_ylabel("feature 2", color=MUTE, fontsize=15)
    ax.text(-3.3, 2.6, "Neolithic", fontsize=17, fontweight="bold")
    ax.text(3.5, -2.75, "Iron Age", fontsize=17, fontweight="bold", ha="right")


def decision_boundary():
    fig, ax = plt.subplots(figsize=(5.6, 4.4))
    _feature_space(ax)
    xs = np.linspace(-3.6, 3.8, 50)
    ys = 1.05 * xs + 0.1
    ax.fill_between(xs, ys, 3.0, color=BLUE, alpha=0.07, lw=0)
    ax.plot(xs, ys, color=BLUE, lw=3)
    ax.text(2.15, 1.45, "boundary", color=BLUE, fontsize=17, fontweight="bold", ha="left", va="center")
    save_png(fig, "decision-boundary.png")


def density():
    fig, ax = plt.subplots(figsize=(5.6, 4.4))
    _feature_space(ax)
    gx, gy = np.meshgrid(np.linspace(-3.6, 3.8, 200), np.linspace(-3.1, 3.0, 200))
    grid = np.vstack([gx.ravel(), gy.ravel()])
    for pts in (_A, _B):
        kde = gaussian_kde(pts.T)
        dens = kde(grid).reshape(gx.shape)
        ax.contourf(gx, gy, dens, levels=np.linspace(dens.max() * .12, dens.max(), 5), colors=ORANGE, alpha=0.1)
        ax.contour(gx, gy, dens, levels=np.linspace(dens.max() * .12, dens.max(), 5)[:-1],
                   colors=ORANGE, linewidths=1.6)
        new = kde.resample(3, seed=3).T
        ax.scatter(*new.T, s=210, marker="*", c=ORANGE, edgecolors="white", linewidths=1, zorder=4)
    ax.scatter([2.05], [2.72], s=210, marker="*", c=ORANGE, edgecolors="white", linewidths=1)
    ax.text(2.3, 2.72, "sampled", color=ORANGE, fontsize=17, fontweight="bold", ha="left", va="center")
    save_png(fig, "density.png")


def pipeline():
    stages = ["Question", "Data &\nannotation", "Pre-\nprocessing", "Training", "Evaluation", "Interpretation"]
    fig, ax = plt.subplots(figsize=(13, 1.9))
    ax.set_xlim(0, 13); ax.set_ylim(0, 1.9); ax.set_axis_off()
    w, h, gap = 1.86, 1.15, 0.34
    for i, s in enumerate(stages):
        x = 0.1 + i * (w + gap)
        early = i < 2
        ax.add_patch(FancyBboxPatch((x, 0.5), w, h, boxstyle="round,pad=0,rounding_size=0.12",
                                    fc=BLUE if early else "white", ec=BLUE if early else MUTE, lw=2))
        ax.text(x + w / 2, 0.5 + h / 2, s, ha="center", va="center", fontsize=16, linespacing=0.95,
                fontweight="bold", color="white" if early else INK)
        if i < len(stages) - 1:
            ax.add_patch(FancyArrowPatch((x + w + 0.06, 1.075), (x + w + gap - 0.06, 1.075),
                                         arrowstyle="-|>", mutation_scale=18, color=MUTE, lw=2))
    # The first two stages are filled because that is where projects fail; the slide says
    # so in a fragment, so the figure does not spell it out.
    save_png(fig, "pipeline.png")


def discriminative():
    """Image in, label / box / mask out."""
    im = load("sherd_02.jpg")
    meta, anns = coco_annotations("M202300130N00020F01")
    s = im.width / meta["width"]
    crop = (170, 55, 770, 455)
    thumb = np.asarray(im.crop(crop))
    _, (x, y, w, h), polys = anns[0]
    box = (x * s - crop[0], y * s - crop[1], w * s, h * s)
    poly = polys[0] * s - [crop[0], crop[1]]

    # One axes in "slide units": thumbnails are 3.0 x 2.0, titles sit at y = 2.45.
    fig, ax = plt.subplots(figsize=(15.2, 2.9))
    ax.set_xlim(0, 15.2); ax.set_ylim(0, 2.9); ax.set_aspect("equal"); ax.set_axis_off()
    sx = 3.0 / thumb.shape[1]

    def thumbnail(x0, title, colour):
        ax.imshow(thumb, extent=(x0, x0 + 3.0, 0.2, 2.2))
        ax.add_patch(Rectangle((x0, 0.2), 3.0, 2.0, fill=False, ec=LIGHT, lw=1))
        ax.text(x0 + 1.5, 2.45, title, fontsize=18, color=colour, ha="center", va="bottom",
                fontweight="normal" if colour == INK else "bold")
        return lambda px, py: (x0 + px * sx, 2.2 - py * sx)   # pixel -> slide units

    thumbnail(0.0, "image", INK)
    ax.add_patch(FancyBboxPatch((3.8, 0.75), 1.6, 0.9, boxstyle="round,pad=0,rounding_size=0.15", fc=BLUE, ec=BLUE))
    ax.text(4.6, 1.2, "model", color="white", fontsize=20, fontweight="bold", ha="center", va="center")
    for xa, xb in [(3.1, 3.72), (5.48, 6.1)]:
        ax.add_patch(FancyArrowPatch((xa, 1.2), (xb, 1.2), arrowstyle="-|>", mutation_scale=20, color=MUTE, lw=2))

    ax.text(7.2, 1.2, "potsherd", color="white", fontsize=21, fontweight="bold", ha="center", va="center",
            bbox=dict(boxstyle="round,pad=0.4,rounding_size=0.3", fc=BLUE, ec="none"))
    ax.text(7.2, 2.45, "label", fontsize=18, color=BLUE, fontweight="bold", ha="center", va="bottom")
    for x in (8.35, 11.85):
        ax.text(x, 1.2, "or", fontsize=17, color=MUTE, ha="center", va="center", style="italic")

    to_b = thumbnail(8.6, "box", BLUE)
    bx0, by0 = to_b(box[0], box[1]); bx1, by1 = to_b(box[0] + box[2], box[1] + box[3])
    ax.add_patch(Rectangle((bx0, by1), bx1 - bx0, by0 - by1, fill=False, ec=BLUE, lw=3))
    to_m = thumbnail(12.1, "mask", BLUE)
    ax.add_patch(Polygon([to_m(*p) for p in poly], closed=True, fc=BLUE, ec=BLUE, alpha=0.5, lw=2))
    save_png(fig, "discriminative.png", dpi=170)


# --- C. Generative examples ---------------------------------------------------

def gen_restoration():
    """Two before/after pairs from Merizzi et al. 2024 (Heritage Science 12, 41), CC BY 4.0.
    Panels are cut out of the published figures: Fig. 12 (a, original) with (e, DIP-TV + skip),
    and Fig. 17 (c, RGB) with (d, inpainted with the IR mask)."""
    f12 = load("gen-restoration_merizzi2024_fig12.png")
    f17 = load("gen-restoration_merizzi2024_fig17.png")
    panels = [(f12.crop((16, 8, 512, 504)), "damaged"),
              (f12.crop((775, 1425, 1529, 2179)), "inpainted"),
              (f17.crop((3, 843, 760, 1599)), "damaged"),
              (f17.crop((775, 843, 1532, 1599)), "inpainted")]
    fig = plt.figure(figsize=(13, 3.6))
    w, gap, pair_gap = 0.235, 0.012, 0.045
    x = 0.0
    for i, (im, title) in enumerate(panels):
        ax = fig.add_axes([x, 0.0, w, 0.86])
        ax.imshow(im.resize((700, 700), Image.LANCZOS)); ax.set_axis_off()
        ax.set_title(title, fontsize=18, pad=6, color=ORANGE if title == "inpainted" else INK,
                     fontweight="bold" if title == "inpainted" else "normal")
        x += w + (pair_gap if i == 1 else gap)
    save_jpg(fig, "gen-restoration.jpg", dpi=150, bbox=True)



# --- D. Demo ------------------------------------------------------------------

def clip_output():
    """CLIP on two sherds, redrawn large enough to read on a slide.
    The percentages are copied from the notebook's own output (clip_zero_shot.ipynb, sections 4
    and 6; screenshots in temp/notebook_section4_sherd02.png, notebook_section4.png and
    notebook_section6.png)."""
    sensible = ["a photo of a potsherd", "a photo of a stone tool", "a photo of a brooch",
                "a photo of a scale bar", "a photo of a coin"]
    runs = [("Terra sigillata, five options", ("sherd_02.jpg", (215, 95, 715, 470)), list(zip(sensible, [95, 5, 0, 0, 0]))),
            ("Coarse sherd, five options", ("sherd_01.jpg", None), list(zip(sensible, [51, 48, 1, 0, 0]))),
            ("Coarse sherd, only wrong options", ("sherd_01.jpg", None),
             [("a photo of a stone tool", 100), ("a photo of a coin", 0), ("a photo of a bicycle", 0)])]
    fig = plt.figure(figsize=(15, 2.5))
    for k, (title, (photo, box), res) in enumerate(runs):
        x0 = k * 0.34
        im = load(photo).crop(box) if box else load(photo)   # sherd_02 has a wide white margin
        a = fig.add_axes([x0, 0.0, 0.08, 0.84]); a.imshow(im); a.set_axis_off()
        b = fig.add_axes([x0 + 0.205, 0.0, 0.085, 0.84])
        names, vals = zip(*res)
        y = np.arange(len(res))[::-1] + (5 - len(res)) / 2   # same row height, centred
        b.barh(y, vals, color=BLUE, height=0.62)
        for yi, v in zip(y, vals):
            b.text(v + 4, yi, f"{v}%", va="center", fontsize=15, color=MUTE)
        b.set_yticks(y, names, fontsize=15); b.set_xlim(0, 100); b.set_xticks([])
        b.set_ylim(-0.6, 4.6)
        b.tick_params(axis="y", length=0, pad=6)
        for sp in ["top", "right", "bottom"]: b.spines[sp].set_visible(False)
        b.spines["left"].set_color(LIGHT)
        fig.text(x0, 0.9, title, fontsize=18, fontweight="bold", va="bottom",
                 color=ORANGE if k == 2 else INK)
    save_png(fig, "clip-output.png", dpi=170)


if __name__ == "__main__":
    for f in [image_as_array, semantic_gap, data_deluge,
              task_classification, task_detection, task_segmentation, task_keypoints,
              decision_boundary, density, pipeline, discriminative, gen_restoration, clip_output]:
        f()
        print("done", f.__name__)
