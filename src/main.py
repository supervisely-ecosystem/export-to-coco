import ast
import json
import os
from distutils.util import strtobool
import asyncio

import supervisely as sly
from dotenv import load_dotenv

import convert_geometry
import functions as f
import workflow as w

# region constants
USER_NAME = "Supervisely"
RECTANGLE_MARK = "converted_from_rectangle"
STORAGE_DIR = os.path.join(os.getcwd(), "storage_dir")
# endregion
sly.fs.mkdir(STORAGE_DIR, remove_content_if_exists=True)

if sly.is_development():
    load_dotenv("local.env")
    load_dotenv(os.path.expanduser("~/supervisely.env"))

# region envvars
team_id = sly.env.team_id()
workspace_id = sly.env.workspace_id()
project_id = sly.env.project_id()
selected_output = os.environ["modal.state.selectedOutput"]
selected_filter = os.environ["modal.state.selectedFilter"]
all_datasets = bool(strtobool(os.getenv("modal.state.allDatasets")))
selected_datasets = ast.literal_eval(os.environ["modal.state.datasets"])
include_captions = bool(strtobool(os.getenv("modal.state.captions")))
# endregion
sly.logger.info(f"Team ID: {team_id}, Workspace ID: {workspace_id}, Project ID: {project_id}")
sly.logger.info(
    f"Selected output: {selected_output}, "
    f"Selected filter: {selected_filter}, "
    f"All datasets: {all_datasets}, "
    f"Selected datasets: {selected_datasets}, "
    f"Included captions: {include_captions}"
)


def export_to_coco(api: sly.Api) -> None:
    project = api.project.get_info_by_id(project_id)
    project_meta = sly.ProjectMeta.from_json(api.project.get_meta(project_id))
    sly.logger.debug("Project meta retrieved...")

    w.workflow_input(api, project.id)

    coco_base_dir = os.path.join(STORAGE_DIR, project.name)
    sly.logger.debug(f"Data in COCO format will be saved to {coco_base_dir}.")

    meta = convert_geometry.prepare_meta(project_meta)
    categories_mapping = f.get_categories_map_from_meta(meta)

    datasets = api.dataset.get_list(project_id, recursive=True)
    if not all_datasets:
        datasets = [dataset for dataset in datasets if dataset.id in selected_datasets]

    sly.logger.debug(f"Will be working with {len(datasets)} datasets.")
    label_id = 0
    caption_id = 0

    for dataset in datasets:
        sly.logger.info(f"Processing dataset {dataset.name}...")
        coco_dataset_dir = os.path.join(coco_base_dir, f"{dataset.id}_{dataset.name}")
        img_dir, ann_dir = f.create_coco_dataset(coco_dataset_dir)

        coco_instances, coco_captions = f.create_coco_ann_templates(
            dataset, USER_NAME, meta, include_captions
        )
        images = api.image.get_list(dataset.id)

        if selected_filter == "annotated":
            images = [image for image in images if image.labels_count > 0 or len(image.tags) > 0]

        ds_progress = sly.Progress(
            f"Converting dataset: {dataset.name}",
            total_cnt=len(images),
            min_report_percent=5,
        )

        dataset_path = os.path.join(img_dir, project.name, dataset.name)
        os.makedirs(dataset_path, exist_ok=True)

        if selected_output == "images":
            image_ids = [image_info.id for image_info in images]
            paths = [os.path.join(dataset_path, image_info.name) for image_info in images]
            if api.server_address.startswith("https://"):
                semaphore = asyncio.Semaphore(100)
            else:
                semaphore = None
            # api._get_default_semaphore()
            coro = api.image.download_paths_async(
                image_ids, paths, semaphore, progress_cb=ds_progress.iters_done_report
            )
            loop = sly.utils.get_or_create_event_loop()
            if loop.is_running():
                future = asyncio.run_coroutine_threadsafe(coro, loop)
                future.result()
            else:
                loop.run_until_complete(coro)

        for batch in sly.batched(images):
            batch_ids = [image_info.id for image_info in batch]
            ann_infos = api.annotation.download_batch(dataset.id, batch_ids)
            anns = []
            sly.logger.info(f"Preparing to convert {len(ann_infos)} annotations...")
            for ann_info, img_info in zip(ann_infos, batch):
                ann = convert_geometry.convert_annotation(
                    ann_info, img_info, project_meta, meta, RECTANGLE_MARK
                )
                anns.append(ann)
            sly.logger.info(f"{len(anns)} annotations converted...")
            coco_instances, label_id, coco_captions, caption_id = f.create_coco_annotation(
                categories_mapping,
                batch,
                anns,
                label_id,
                coco_instances,
                caption_id,
                coco_captions,
                ds_progress,
                include_captions,
                RECTANGLE_MARK,
            )

        # for batch in sly.batched(images):
        #     image_ids = [image_info.id for image_info in batch]
        #     sly.logger.info(f"Working with batch of {len(batch)} images with ids: {image_ids}")

        #     if selected_output == "images":
        #         image_paths = [os.path.join(img_dir, image_info.name) for image_info in batch]
        #         f.download_batch_with_retry(api, dataset.id, image_ids, image_paths)

        #     ann_infos = api.annotation.download_batch(dataset.id, image_ids)
        #     anns = []
        #     sly.logger.info(f"Preparing to convert {len(ann_infos)} annotations...")
        #     for ann_info, img_info in zip(ann_infos, batch):
        #         ann = convert_geometry.convert_annotation(
        #             ann_info, img_info, project_meta, meta, RECTANGLE_MARK
        #         )
        #         anns.append(ann)
        #     sly.logger.info(f"{len(anns)} annotations converted...")
        #     coco_instances, label_id, coco_captions, caption_id = f.create_coco_annotation(
        #         categories_mapping,
        #         batch,
        #         anns,
        #         label_id,
        #         coco_instances,
        #         caption_id,
        #         coco_captions,
        #         ds_progress,
        #         include_captions,
        #         RECTANGLE_MARK,
        #     )
        with open(os.path.join(ann_dir, "instances.json"), "w") as file:
            json.dump(coco_instances, file)
        if coco_captions is not None and include_captions:
            with open(os.path.join(ann_dir, "captions.json"), "w") as file:
                json.dump(coco_captions, file)
        sly.logger.info(f"Dataset [{dataset.name}] processed!")

    total_files = len(sly.fs.list_files_recursively(STORAGE_DIR))
    dir_size = sly.fs.get_directory_size(STORAGE_DIR) / (1024 * 1024)
    dir_size = f"{dir_size:.2f} MB"

    sly.logger.info(f"Total files: {total_files}")
    sly.logger.info(f"Total images: {total_files - len(datasets)}")
    sly.logger.info(f"Total directory size: {dir_size}")

    file_info = sly.output.set_download(coco_base_dir)
    w.workflow_output(api, file_info)


if __name__ == "__main__":
    api = sly.Api.from_env()
    export_to_coco(api)
