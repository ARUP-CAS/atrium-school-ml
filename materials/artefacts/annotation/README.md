# Annotation files for the artefacts session

**CVAT** runs both the live demo with SAM 2 and the 16-minute hands-on. It is on the
venue network at **http://10.10.1.40:8081**. Every participant annotates the same ten
AMČR-PAS photographs in **their own project**, built from the files in the lessons
repository ([atrium-school-ml-lessons](https://github.com/arubrno/atrium-school-ml-lessons),
folder `2-tuesday-artefacts/`). Pulling that repository needs internet access; CVAT
itself does not. Label Studio appears in the deck only as an example; its setup is kept
at the end as a fallback.

| file | what it is |
|---|---|
| `select_images.py` | picks the 10 photos from the AMČR-PAS COCO export, downscales them to 1600 px, and optionally publishes them to the lessons repository |
| `images.csv` | the 10: record, DOI, the AMČR recorder's class, and why each one is there. **Instructor-only**: it holds the answers to the planted photos |
| `reference_coco.json` | the original AMČR-PAS annotations for the 10, rescaled to the 1600 px copies |
| `cvat/labels.json` | the CVAT label set: 12 classes with `fragment`, `damage` and `note`, plus a `photo` tag with `scale` |
| `labelstudio/config.xml`, `setup_labelstudio.py` | the Label Studio fallback (section 5) |

Attribute keys and enum values follow the ArchaeoTag schema (`imagetag_schema.json` in
arubrno/archiv-digilab); the question wording is ArchaeoTag's. Booleans are stored as
`yes` / `no` (read them as `true` / `false`). Every CVAT attribute starts at `?`, meaning
*not answered*; `unknown` means the person looked and could not tell.

## 1. Build the images

From the repository root, on a machine with the dataset:

```sh
LESSONS_DIR=../atrium-school-ml-lessons/2-tuesday-artefacts \
  python3 materials/artefacts/annotation/select_images.py
```

It reads `~/Documents/fiftyone/datasets/amcr-pas/` (override with `FIFTYONE_ROOT`) and
writes `temp/annotation/`: `images/` (the 10), `demo/` (the rosary, for the demo),
`cvat-images.zip` (all 11) and `contact-sheet.jpg` (the 10 with the recorder's boxes, for
checking by eye).

With `LESSONS_DIR` set, it also refreshes what participants download: `images/`,
`labels.json` (a copy of `cvat/labels.json`) and `credits.csv` (file name and DOI only, no
answers). Commit and push the lessons repository afterwards. **After any change to
`cvat/labels.json`, re-run this step**, or the participants' copy goes stale.

## 2. CVAT: the demo

The *CVAT: the demo* slide does live exactly what participants do next, on the rosary:

1. **Projects → + → Create a new project**. Under labels, open the **Raw** tab, replace
   everything with `cvat/labels.json`, then **Done** and **Submit & Open**.
2. **+ → Create a new task**, with `temp/annotation/demo/M202400071N00083F01.jpg` under
   **Select files**, then **Submit & Open**.
3. Open the job. Outline one find with **AI Tools → Interactors → Segment Anything**, give
   it a class, and answer its questions in the objects list.
4. **Export** as **COCO 1.0**: the polygon and the attributes are both in the JSON. If
   there's time, export **YOLO** too: a number and four coordinates, with no attributes and
   no class name.

Worth saying while you do it:

- CVAT forces a default on every attribute. That is why ours start at `?`; otherwise an
  untouched object looks like an answer. That is how the old export ended up with
  `occluded: false` on all 10 749 annotations: `occluded` is CVAT's own per-shape
  toggle, and it's off unless someone switches it on.
- The classes are type `any`, not `rectangle`, so a SAM mask can be given a label.

To show the *projects → tasks → jobs* split, prepare a second task in advance from
`temp/annotation/cvat-images.zip` with **Advanced configuration → Segment size 4**.
That splits the 11 images into 3 jobs, and you can assign one to a colleague.

## 3. CVAT: the hands-on

Participants follow the *Set up your project* and *Annotate* slides; the lessons README
repeats the same steps. In short: create an account on CVAT, create a project from
`labels.json`, create a task from the ten `images/`, open the job, then for each find
outline it, give it a class, and answer `fragment` and `damage`. For each photo, add the
**photo** tag (**Setup tag**) and answer `scale`. **Ctrl+S** saves.

- **Setup is where people get stuck**: they paste `labels.json` after the `[]` already in
  the Raw box instead of replacing it.
- **People miss the scale question.** It is a tag on the whole photo, not on an object;
  point at the tag button once, early.
- **Nothing is shared.** Every project is private, so *What you had to decide* is a show of
  hands, not a screen. The planted photos are **04** (a pierced coin, recorded as a
  pendant), **06** (a crescent, recorded as a mount) and **08** (coins fused into a lump:
  one object or several?). The recorder's answers are in `images.csv`.

## 4. Before the session

- [ ] **http://10.10.1.40:8081** opens from a **phone on the venue wifi**, not only from
      the host machine; CVAT's address is on the board, as a QR code if you can
- [ ] A test account can register, create a project from the lessons repository's
      `labels.json`, and create a task from its ten photos
- [ ] **Segment Anything** is listed under AI Tools → Interactors. Self-hosted CVAT needs
      a nuclio function for it; if it is missing, polygons and boxes still work, but the
      SAM slides need a plan B
- [ ] The lessons repository is pushed, and `2-tuesday-artefacts/` matches this folder
      (section 1)
- [ ] The rosary (`temp/annotation/demo/`) is on the presenting laptop

## 5. Label Studio (fallback, not used in the session)

The same label set as a Label Studio project, in case CVAT is unavailable.

1. On the Label Studio host: **Account & Settings → Personal Access Token → Create**.
   Since 1.23, legacy tokens are switched off by default; the script accepts either kind.
2. From the repository root:
   ```sh
   export LS_URL=http://<ip>:8080
   export LS_API_KEY=<token>
   python3 materials/artefacts/annotation/setup_labelstudio.py
   ```
   It creates **Hands-on: AMČR-PAS** (10 tasks) and **Demo: rosary** (1 task) and prints
   a signup link for participants. Re-running leaves existing projects alone.

How it behaves (tested on Label Studio 1.23.0, community edition):

- **One shared project.** The script sets overlap (`maximum_annotations`) to 100, so
  everyone gets all 10 photos. The first person gets them in order; everyone after gets
  them in a random order.
- A box's questions appear **when the box is selected**, and the note saves on **Enter**.
- **Compare All** on a photo shows every participant's annotations side by side.
- **Export**: JSON keeps every attribute and who annotated what. Label Studio's COCO export
  drops the attributes and the annotator.
