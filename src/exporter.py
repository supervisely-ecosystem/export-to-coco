"""Builds the COCO folder tree for a project on local disk."""

from __future__ import annotations

import os

import supervisely as sly

import platform_io
from core.coco import CocoDatasetBuilder, skipped_summary
from settings import Settings

BATCH_SIZE = 100


def export_project(api: sly.Api, project_id: int, settings: Settings, work_dir: str) -> str:
    """Write `<work_dir>/<project name>/<dataset id>_<dataset name>/...` and return the project folder.

    Only reads from the platform; uploading and workflow lineage are the caller's job.
    """
    project = api.project.get_info_by_id(project_id)
    meta = sly.ProjectMeta.from_json(api.project.get_meta(project_id))

    project_dir = os.path.join(work_dir, project.name)
    sly.fs.mkdir(project_dir, remove_content_if_exists=True)

    datasets = platform_io.list_datasets(api, project_id, settings.dataset_ids)
    sly.logger.info(f"Exporting {len(datasets)} dataset(s) of project {project.name!r} to COCO")
    for dataset in datasets:
        export_dataset(api, dataset, meta, settings, os.path.join(project_dir, f"{dataset.id}_{dataset.name}"))
    return project_dir


def export_dataset(
    api: sly.Api, dataset: sly.DatasetInfo, meta: sly.ProjectMeta, settings: Settings, dataset_dir: str
) -> None:
    images = platform_io.list_images(api, dataset.id, settings.only_annotated)
    images_dir = os.path.join(dataset_dir, "images") if settings.export_images else None
    annotations_dir = os.path.join(dataset_dir, "annotations")
    for path in (images_dir, annotations_dir):
        if path is not None:
            sly.fs.mkdir(path)

    builder = CocoDatasetBuilder(dataset, meta, settings.with_captions)
    with sly.tqdm_sly(desc=f"Converting dataset {dataset.name!r}", total=len(images)) as progress:
        for batch in sly.batched(images, BATCH_SIZE):
            anns = platform_io.download_batch(api, dataset.id, batch, meta, images_dir)
            for image, ann in zip(batch, anns, strict=True):
                builder.add(image, ann)
            progress.update(len(batch))

    if builder.skipped:
        sly.logger.warning(
            f"Dataset {dataset.name!r}: shapes COCO cannot express were skipped: "
            + ", ".join(skipped_summary(builder.skipped))
        )
    sly.json.dump_json_file(builder.instances, os.path.join(annotations_dir, "instances.json"))
    if builder.captions is not None:
        sly.json.dump_json_file(builder.captions, os.path.join(annotations_dir, "captions.json"))
    elif settings.with_captions:
        sly.logger.warning("Captions requested, but the project has no image tag 'caption' of type any_string")
