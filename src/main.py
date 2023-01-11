import json
import os

import supervisely as sly

import convert_geometry
import functions as f
import globals as g


@g.my_app.callback("export_to_coco")
@sly.timeit
def export_to_coco(api: sly.Api, task_id, context, state, app_logger):
    meta = convert_geometry.prepare_meta(g.meta)
    categories_mapping = f.get_categories_map_from_meta(meta)
    if g.all_datasets:
        datasets = list(api.dataset.get_list(g.project_id))
    else:
        datasets = [g.api.dataset.get_info_by_id(dataset_id) for dataset_id in g.selected_datasets]
    label_id = 0

    for dataset in datasets:
        sly.logger.info(f"processing {dataset.name}...")
        coco_dataset_dir = os.path.join(g.coco_base_dir, dataset.name)
        img_dir, ann_dir = f.create_coco_dataset(coco_dataset_dir)

        coco_ann = {}
        images = api.image.get_list(dataset.id)

        if g.selected_filter == "annotated":
            images = [image for image in images if image.labels_count > 0 or len(image.tags) > 0]

        ds_progress = sly.Progress(
            f"Converting dataset: {dataset.name}",
            total_cnt=len(images),
            min_report_percent=5,
        )
        for batch in sly.batched(images):
            image_ids = [image_info.id for image_info in batch]

            if g.selected_output == "images":
                image_paths = [
                    os.path.join(coco_dataset_dir, img_dir, image_info.name) for image_info in batch
                ]
                api.image.download_paths(dataset.id, image_ids, image_paths)

            ann_infos = api.annotation.download_batch(dataset.id, image_ids)
            anns = [sly.Annotation.from_json(x.annotation, g.meta) for x in ann_infos]
            anns = [convert_geometry.convert_annotation(ann, meta) for ann in anns]
            coco_ann, label_id = f.create_coco_annotation(
                meta,
                categories_mapping,
                dataset,
                g.user_name,
                batch,
                anns,
                label_id,
                coco_ann,
                ds_progress,
            )
        with open(os.path.join(ann_dir, "instances.json"), "w") as file:
            json.dump(coco_ann, file)

        sly.logger.info(f"dataset {dataset.name} processed!")

    full_archive_name = f"{task_id}_{g.project.name}.tar"
    result_archive = os.path.join(g.my_app.data_dir, full_archive_name)
    f.upload_coco_project(full_archive_name, result_archive, app_logger)
    g.my_app.stop()


def main():
    sly.logger.info(
        "Input arguments",
        extra={
            "TASK_ID": g.task_id,
            "context.teamId": g.team_id,
            "context.workspaceId": g.workspace_id,
            "context.projectId": g.project_id,
            "allDatasets": g.all_datasets,
            "selectedDatasets": g.selected_datasets,
            "selectedFilter": g.selected_filter,
            "selectedOutput": g.selected_output,
        },
    )

    # Run application service
    g.my_app.run(initial_events=[{"command": "export_to_coco"}])


if __name__ == "__main__":
    sly.main_wrapper("main", main)
