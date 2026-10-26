# Modernization notes: export-to-coco

Rewrite of `export-to-coco` to the `sly-app-standard` (local pilot, not released).
Base: `origin/master` @ 9167823. Branch `local/modernize`, nothing committed.

## Behaviour contract (kept)

**Entry point.** Context menu of an images project → "Download as" → Export to COCO. Headless
one-shot task, options come from the modal window (`src/modal.html`):

| `modal.state` field | Values | Default | Meaning |
|---|---|---|---|
| `selectedOutput` | `images` / `annotations` | `images` | export images + annotations, or annotations only |
| `selectedFilter` | `all` / `annotated` | `all` | `annotated` keeps images with at least one label or image tag |
| `allDatasets` | bool | `true` | whole project (all nested datasets) |
| `datasets` | list of dataset ids | `[]` | used when `allDatasets` is false |
| `captions` | bool | `false` | also write `captions.json` |

**Output.** One `.tar` archive set as the task's download link (via `sly.output.set_download`,
uploaded to Team Files under the export path for this task). Archive layout:

```
<project name>/
  <dataset id>_<dataset name>/      # one per dataset, nested datasets flattened
    images/<image name>             # only when selectedOutput = images
    annotations/instances.json
    annotations/captions.json       # only with captions on and a valid "caption" tag in the project
```

**instances.json**
- `info`: dataset description, `year`/`date_created` from the dataset's `created_at`, contributor `Supervisely`.
- `licenses`: `[{"url": "None", "id": 0, "name": "None"}]`.
- `images[]`: `license`, `file_name`, `url`, `height`, `width`, `date_captured` (image `created_at`), `id`, `sly_id` (Supervisely image id).
- `categories[]`: every project class in meta order, `id` = position starting at 1, `supercategory` = `name`.
- `annotations[]` by geometry:
  - polygon → `segmentation` = `[[x1, y1, x2, y2, …]]` (exterior only, holes dropped), bbox and area of the polygon;
  - bitmap (and other mask-like geometry) → converted to polygons; all parts of one mask form **one**
    annotation with several polygons, `area` = sum of parts, `bbox` = union;
  - rectangle → `segmentation: []`, `bbox`, `area` = bbox width × height;
  - polyline and other unsupported shapes → skipped with a warning in the task log;
  - labels already grouped by a binding key stay one annotation.
  - `bbox` is `[x, y, width, height]` with width = right − left (Supervisely coordinates are inclusive; the app has always used this convention).
- Unreadable annotation JSON → the image is exported without labels.

**captions.json**: written when captions are on and the project has a `caption` tag of type
`any_string` not limited to objects. Same `info`/`licenses`/`images`; `annotations[]` =
`{image_id, id, caption}` per caption tag on an image.

**Platform side effects.** Workflow lineage: the project as input, the archive as output.
Nothing in the project is modified.

## Intentional changes

1. **Images go to `images/` again.** Since commit 27c7f08 (Dec 2024) images were written to
   `<dataset dir>/<project name>/<dataset name>/` while `images/` stayed empty, which breaks the
   layout that Import COCO and other COCO tools expect (and the README promises).
2. **Ids restart per dataset.** Image, annotation and caption ids now start at 1 in each
   `instances.json`/`captions.json`. They used to continue across datasets because of a module-level
   counter. Each file is a separate COCO dataset, so per-file ids are the standard; `sly_id` keeps the
   link to Supervisely.
3. **Keypoints are exported.** Graph (keypoint) labels were silently skipped; they now become COCO
   keypoint annotations and their categories carry `keypoints`/`skeleton` (SDK `sly_ann_to_coco`).
4. **bbox numbers are ints** (`[10, 20, 9, 19]` instead of `[10.0, 20.0, 9.0, 19.0]`). Same values.
5. **`images/` is created only when images are exported.**
6. **Runs on the hardened image (Python 3.14).** The old code used `distutils.util.strtobool`,
   removed in Python 3.12, so it could not run there.

## Dropped

- `src/globals.py` (commented-out v1 `AppService` code), commented-out RLE/upload helpers,
  unused `download_batch_with_retry`, `get_project_contributors`, `extend_mask_up_to_image`,
  `coco_segmentation_rle` in `src/functions.py`.
- Hand-written COCO object assembly → SDK `supervisely.convert.image.coco.coco_helper.sly_ann_to_coco`
  and `get_categories_from_meta`.
- Manual event-loop juggling → `sly.run_coroutine`.
- `src/workflow.py` → `src/platform_io.py` (same lineage calls).
- `create_venv.sh`, `create_symlink.sh`, `.flake8` → `pyproject.toml` (ruff + pytest config only).

## Versions and image

- **Image: `supervisely/base-py-sdk-hardened:6.74.34`** (was the shared SDK image
  `supervisely/import-export:6.74.34`, kept only for backward compatibility). The app needs nothing
  beyond the SDK (python-dotenv is an SDK dependency), so the bare hardened image is used and no
  per-app image has to be built. Runtime becomes Python 3.14 (was 3.8).
- **SDK stays at 6.74.34** with `instance_version` 6.17.22. CI (`workflows/release.py`,
  `supervisely/versions.json`) only accepts SDK in [6.74.29, 6.74.35) for that instance version;
  moving to 6.74.51 would require `instance_version` ≥ 6.18.3 and drop older instances — a product
  decision, not part of this rewrite.
- CI left as is: `.github/workflows/release.yml` still builds a per-app image (`build-image`, which
  `Supervisely-Release` needs) that the bare hardened image no longer uses — open question for the team
  (see `sly-app-standard`).
- `sly.app.Export` (SDK app template, backward-compatibility code) is not used: `main.py` calls
  `sly.output.set_download` itself, which is all the template added.

## Verification (2026-10-25, dev.internal.supervisely.com, instance 6.18.7)

- **Same output as the old app on real projects.** Old code (`origin/HEAD`, Python 3.11) and new code
  exported the same projects; per dataset the categories, images and every object (matched by Supervisely
  image id: category, segmentation, bbox, area) are identical:
  Lemons (Annotated) #46 (bitmaps, images), Lemons (Bitmap) #26, Lemons (Rectangle) #27,
  Fruits Nested (Annotated) #1317 (9 nested datasets, only-annotated + images), and #1317 with two
  selected datasets + captions on. Image files: old `<ds>/<project>/<dataset>/x.jpg`, new `<ds>/images/x.jpg`
  (intentional change 1). Script: session scratchpad `real_compare/`.
- **Contract tests**: `SLY_CONTRACT_TESTS=1 SLY_CONTRACT_PROJECT_ID=1317 pytest -m contract` — 3 passed
  (includes loading every `instances.json` with pycocotools).
- **In the real image**: `supervisely/base-py-sdk-hardened:6.74.34` (Python 3.14.7, amd64): unit tests
  25/25; full `python src/main.py` with `ENV=production` on a debug task (`create_debug_task`, task 62688):
  archive uploaded to Team Files (`/tmp/supervisely/export/Export to COCO/62688/…tar`), task output set to
  "Download archive", workflow input/output recorded, no errors or warnings.
- Found while doing it: outside production `sly.output.set_download` only archives locally and returns
  `None`; `register_workflow_output` now skips in that case. The workflow API takes the task id from
  `SUPERVISELY_TASK_ID`, not `TASK_ID` (the platform sets both; set both when simulating a task).
