# Annotation projects for the artefacts session

CVAT runs both the demo with SAM and the 16-minute hands-on (everyone annotates the same
ten AMČR-PAS photographs, each in their own project). It runs on the machine on the venue
network at **http://172.16.16.214:8081**; nothing here needs internet access at the
session. Label Studio is only mentioned as an example in the deck; its setup is kept in
section 2 as a fallback.

| file | what it is |
|---|---|
| `select_images.py` | picks the 10 photos from the AMČR-PAS COCO export, downscales them to 1600 px, zips them for CVAT |
| `images.csv` | the 10: record, DOI, reference class, why each one is there (CC BY-NC 4.0 credit) |
| `reference_coco.json` | the original AMČR-PAS annotations for the 10, rescaled to the 1600 px copies |
| `labelstudio/config.xml` | Label Studio labelling interface: 12 classes, 3 attributes, a note |
| `setup_labelstudio.py` | creates both Label Studio projects and uploads the photos |
| `cvat/labels.json` | the same labels for CVAT, pasted into the project's Raw label editor |

Attribute keys and enum values follow the ArchaeoTag schema (`imagetag_schema.json` in
arubrno/archiv-digilab); the question wording is ArchaeoTag's. Booleans are stored as
`yes` / `no` (read them as `true` / `false`), and `unknown` means the person chose
*Can't tell*.

## 1. Build the images (once, on any machine with the dataset)

```sh
python3 materials/artefacts/annotation/select_images.py
```

Reads `~/Documents/fiftyone/datasets/amcr-pas/` (override with `FIFTYONE_ROOT`) and writes
`temp/annotation/`: `images/` (10), `demo/` (the rosary), `cvat-images.zip` (all 11) and
`contact-sheet.jpg`.

## 2. Label Studio (fallback, not used in the session)

1. On the Label Studio host: **Account & Settings → Personal Access Token → Create**.
   Since 1.23, legacy tokens are switched off by default; the script accepts either kind.
2. From the repository root:
   ```sh
   export LS_URL=http://<ip>:8080
   export LS_API_KEY=<token>
   python3 materials/artefacts/annotation/setup_labelstudio.py
   ```
   It creates **Hands-on: AMČR-PAS** (10 tasks) and **Demo: rosary** (1 task), and prints
   the participant signup link. Re-running leaves existing projects alone; delete a project
   in the UI to rebuild it.
3. **Accounts.** Put the printed signup link on the board, as a QR code if you can.
   Participants sign up with their name and any email (e.g. `anna@school`) and a password.
   Label Studio has no badge-name login.
4. Participants open the project and press **Label All Tasks**.

How it behaves (tested on Label Studio 1.23.0, community edition):

- **Everyone gets all 10 photos.** The script sets overlap (`maximum_annotations`) to 100.
  With the default of 1, the first person to submit a photo takes it away from everyone else.
- **Only the first person gets them in order 01–10.** Everyone after gets the ten in a
  random order. That's harmless, and it stops people copying their neighbour.
- A box's questions appear **when the box is selected**: draw it, then click it. Submit is
  blocked until every box has *fragment* and *damage* and the photo has *scale*.
- The note field saves on **Enter**.

**During "Where you disagreed":** open a photo in the Data Manager and click **Compare
All**; every participant's boxes, classes and answers appear side by side. The planted
photos are 04 (pierced coin, recorded as a pendant), 06 (crescent, recorded as a mount)
and 08 (coins fused into a lump).

**Export** (project → Export): **JSON** keeps everything, including who annotated what and
every attribute. **COCO** keeps the boxes and classes but **drops the attributes and the
annotator**. Show both during the demo: it is the three-formats slide's "every conversion
is lossy", live.

## 3. CVAT (demo and hands-on)

Participants open **http://172.16.16.214:8081**, create an account, and set up their own
project and task from the lessons repository (`2-tuesday-artefacts/`), following the
*Set up your project* slide. The steps below are for your demo project.

1. **Projects → + → Create a new project**, name `AMČR-PAS demo`. Under labels, switch to
   **Raw**, replace the content with `cvat/labels.json`, then **Done** and **Submit & Open**.
2. In the project: **+ → Create a new task**, name `hands-on photos`, select files:
   `temp/annotation/cvat-images.zip`. Under **Advanced configuration**, set **Segment size
   4**, which splits the 11 images into **3 jobs**, for the job-split point on the CVAT
   slide. Submit.
3. Assign one job to a colleague's account to show assignment and review.
4. **SAM:** open a job, then **AI Tools → Interactors**. If *Segment Anything* is not in the
   list, the instance has no SAM function deployed; self-hosted CVAT needs nuclio for it.
   Find out **before** the session, not during the demo.

Worth saying during the demo: every attribute's first value is `?`, and that is also the
default. CVAT forces a default, so without a `?` an untouched box looks like a deliberate
answer. That is exactly how the old export ended up with `occluded: false` on all 10 749
annotations: `occluded` is CVAT's own per-shape toggle, and it is off unless someone
switches it on. The classes are type `any`, not `rectangle`, so a mask from SAM can be
given a label.

## Before the session

- [ ] **http://172.16.16.214:8081** opens from a **phone on the venue wifi**, not only
      from the host machine
- [ ] A test account can register, create a project from `labels.json` and a task from
      the ten photos
- [ ] CVAT address on the board / as a QR code
- [ ] CVAT: labels imported, task has 3 jobs, SAM listed under Interactors (or a plan B)
- [ ] The demo projects are empty, so you can annotate the rosary live
