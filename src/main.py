import os
import json
import globals as g
import functions as f
import convert_geometry
import supervisely_lib as sly


@g.my_app.callback("export_to_coco")
@sly.timeit
def export_to_coco(api: sly.Api, task_id, context, state, app_logger):
    meta = convert_geometry.prepare_meta(g.meta)
    categories_mapping = f.get_categories_map_from_meta(meta)
    datasets = [ds for ds in api.dataset.get_list(g.project_id)]
    for dataset in datasets:
        coco_dataset_dir = os.path.join(g.coco_base_dir, dataset.name)
        img_dir, ann_dir = f.create_coco_dataset(coco_dataset_dir)

        coco_ann = {}
        label_id = 0
        images = api.image.get_list(dataset.id)
        ds_progress = sly.Progress('Converting dataset: {}'.format(dataset.name), total_cnt=len(images))
        for batch in sly.batched(images):
            image_ids = [image_info.id for image_info in batch]
            image_paths = [os.path.join(coco_dataset_dir, img_dir, image_info.name) for image_info in batch]
            api.image.download_paths(dataset.id, image_ids, image_paths)

            ann_infos = api.annotation.download_batch(dataset.id, image_ids)
            anns = [sly.Annotation.from_json(x.annotation, g.meta) for x in ann_infos]
            anns = [convert_geometry.convert_annotation(ann, meta) for ann in anns]
            coco_ann = f.create_coco_annotation(meta, categories_mapping, dataset, g.user_name, batch, anns, label_id, coco_ann, ds_progress)
        with open(os.path.join(ann_dir, f"instances.json"), 'w') as file:
            json.dump(coco_ann, file)

    full_archive_name = f"{task_id}_{g.project.name}.tar"
    result_archive = os.path.join(g.storage_dir, full_archive_name)
    f.upload_coco_project(full_archive_name, result_archive, app_logger)
    g.my_app.stop()


def main():
    sly.logger.info("Input arguments", extra={
        "TASK_ID": g.task_id,
        "context.teamId": g.team_id,
        "context.workspaceId": g.workspace_id,
        "context.projectId": g.project_id
    })

    # Run application service
    g.my_app.run(initial_events=[{"command": "export_to_coco"}])


if __name__ == "__main__":
    sly.main_wrapper("main", main)
