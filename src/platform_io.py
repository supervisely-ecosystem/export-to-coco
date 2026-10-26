"""Everything that talks to the Supervisely API."""

from __future__ import annotations

import os
from collections.abc import Sequence

import supervisely as sly

from core.coco import is_annotated, parse_annotation


def list_datasets(api: sly.Api, project_id: int, dataset_ids: Sequence[int] | None) -> list[sly.DatasetInfo]:
    datasets = api.dataset.get_list(project_id, recursive=True)
    if dataset_ids is None:
        return datasets
    wanted = set(dataset_ids)
    found = [ds for ds in datasets if ds.id in wanted]
    missing = wanted - {ds.id for ds in found}
    if missing:
        raise ValueError(f"Datasets {sorted(missing)} are not in project {project_id}")
    return found


def list_images(api: sly.Api, dataset_id: int, only_annotated: bool) -> list[sly.ImageInfo]:
    images = api.image.get_list(dataset_id)
    return [image for image in images if is_annotated(image)] if only_annotated else images


def download_batch(
    api: sly.Api,
    dataset_id: int,
    images: Sequence[sly.ImageInfo],
    meta: sly.ProjectMeta,
    images_dir: str | None,
) -> list[sly.Annotation]:
    """Download annotations (and image files when `images_dir` is set) for one batch."""
    ids = [image.id for image in images]
    if images_dir is not None:
        paths = [os.path.join(images_dir, image.name) for image in images]
        sly.run_coroutine(api.image.download_paths_async(ids, paths))
    ann_infos = sly.run_coroutine(api.annotation.download_batch_async(dataset_id, ids))
    by_id = {info.image_id: info for info in ann_infos}
    return [parse_annotation(by_id[image.id].annotation, image, meta) for image in images]


def register_workflow_input(api: sly.Api, project_id: int) -> None:
    api.app.workflow.add_input_project(project_id)


def register_workflow_output(api: sly.Api, archive: sly.api.file_api.FileInfo | None) -> None:
    """Lineage is a convenience: failing to record it must not fail a finished export."""
    if archive is None:  # outside production set_download only archives locally and returns None
        return
    try:
        settings = sly.WorkflowSettings(
            title=archive.name,
            icon="archive",
            icon_color="#33c94c",
            icon_bg_color="#d9f7e4",
            url=f"/files/{archive.id}/true/?teamId={archive.team_id}",
            url_title="Download",
        )
        api.app.workflow.add_output_file(archive, meta=sly.WorkflowMeta(relation_settings=settings))
    except Exception as e:  # noqa: BLE001
        sly.logger.warning(f"Failed to add the archive to the workflow: {e!r}")
