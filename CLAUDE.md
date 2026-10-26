# export-to-coco

Headless export: images project → COCO (`instances.json`, optional `captions.json`) in a `.tar`
set as the task's download link. `MODERNIZE.md` has the behaviour contract and the intentional
changes versus the pre-2026 version.

- Entry: `src/main.py` (`config.json` `main_script`); options from the modal window `src/modal.html`
  arrive as `modal.state.*` and are parsed only in `src/settings.py`.
- Flow: `main.main` → `exporter.export_project` writes the folder tree → `sly.output.set_download`
  archives and uploads it → workflow lineage via `src/platform_io.py` (the only module calling the API).
- Conversion: `src/core/coco.py` (pure, unit-tested) on top of the SDK's `sly_ann_to_coco`; masks become
  polygon groups first, rectangles stay bbox-only with area = bbox w × h, polylines/points are skipped and counted.

Runtime: bare `supervisely/base-py-sdk-hardened:<sdk version>` (Python 3.14), no per-app image because
`dev_requirements.txt` holds only the SDK. Adding a dependency means switching to the per-app image
built by `.github/workflows/build_app_image.yml`.

Keep: the archive layout and file names, `config.json` `name`/`context_menu` (users and Import COCO rely
on them), and SDK within the range `supervisely/versions.json` allows for `min_instance_version`.

Tests: `pytest` (unit, offline, includes an end-to-end run against a fake API) ·
`SLY_CONTRACT_TESTS=1 SLY_CONTRACT_PROJECT_ID=<id> pytest -m contract tests/contract` (real instance, read-only).
