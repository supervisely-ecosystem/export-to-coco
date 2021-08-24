import os
import json
import globals as g
import convert_geometry
import supervisely_lib as sly
from supervisely_lib.io.fs import mkdir


def start_object_detection(app_logger):
    meta = convert_geometry.prepare_meta(g.meta)
    obj_classes = meta.obj_classes
    class_mapping = {}
    for idx, obj_class in enumerate(obj_classes):
        class_mapping[obj_class.name] = idx + 1

    datasets = [ds for ds in g.api.dataset.get_list(g.project_id)]
    for dataset in datasets:
        coco_dataset_dir = os.path.join(g.coco_base_dir, dataset.name)
        mkdir(os.path.join(coco_dataset_dir))
        img_dir = os.path.join(coco_dataset_dir, 'images')
        mkdir(img_dir)
        ann_dir = os.path.join(coco_dataset_dir, 'annotations')
        mkdir(ann_dir)

        data = {}
        ann_id = 0
        images = g.api.image.get_list(dataset.id)
        ds_progress = sly.Progress('Converting dataset: {}'.format(dataset.name), total_cnt=len(images))
        for batch in sly.batched(images):
            image_ids = [image_info.id for image_info in batch]
            image_paths = [os.path.join(coco_dataset_dir, img_dir, image_info.name) for image_info in batch]
            g.api.image.download_paths(dataset.id, image_ids, image_paths)

            ann_infos = g.api.annotation.download_batch(dataset.id, image_ids)
            anns = [sly.Annotation.from_json(x.annotation, g.meta) for x in ann_infos]
            anns = [convert_geometry.convert_annotation(ann, meta) for ann in anns]

            data = dict(
                info=dict(
                    description=dataset.description,
                    url=None,
                    version=1.0,
                    year=dataset.created_at[:4],
                    contributor=g.user.name,
                    date_created=dataset.created_at,
                ),
                licenses=[dict(url=None, id=0, name=None, )],
                images=[
                    # license, url, file_name, height, width, date_captured, id
                ],
                type="instances",
                annotations=[
                    # segmentation, area, iscrowd, image_id, bbox, category_id, id
                ],
                categories=[
                    # supercategory, id, name
                ],
            )

            for image_info, ann in zip(batch, anns):
                data["images"].append(dict(
                    license=None,
                    url=image_info.full_storage_url,  # coco_url, flickr_url
                    filename=image_info.name,
                    height=image_info.height,
                    width=image_info.width,
                    date_captured=image_info.created_at,
                    id=image_info.id,
                ))

                for label in ann.labels:
                    #label_mapping = {}
                    #for idx, obj_class in enumerate(obj_classes):
                    #    class_mapping[obj_class.name] = idx + 1

                    segmentation = label.geometry.to_json()["points"]["exterior"]
                    segmentation = [coord for sublist in segmentation for coord in sublist]

                    bbox = label.geometry.to_bbox().to_json()["points"]["exterior"]
                    bbox = [coord for sublist in bbox for coord in sublist]
                    x, y, max_x, max_y = bbox
                    width = max_x - x
                    height = max_y - y
                    bbox = (x, y, width, height)
                    ann_id += 1

                    data["annotations"].append(dict(
                        segmentation=[segmentation],
                        area=label.geometry.area,                         # Area is measured in pixels (e.g. a 10px by 20px box would have an area of 200)
                        iscrowd=0,                                        # Is Crowd specifies whether the segmentation is for a single object or for a group/cluster of objects
                        image_id=image_info.id,                           # The image id corresponds to a specific image in the dataset
                        bbox=bbox,                                        # he COCO bounding box format is [top left x position, top left y position, width, height]
                        category_id=class_mapping[label.obj_class.name],  # The category id corresponds to a single category specified in the categories section
                        id=ann_id,                                        # Each annotation also has an id (unique to all other annotations in the dataset)
                    ))

                    data["categories"].append(dict(
                        supercategory=label.obj_class.name,
                        id=class_mapping[label.obj_class.name],  # supercategory id
                        name=label.obj_class.name
                    ))
                ds_progress.iter_done_report()
        with open(os.path.join(ann_dir, f"instances_{dataset.name}.json"), 'w') as file:
            json.dump(data, file)

    full_archive_name = str(g.task_id) + '_' + g.project.name + ".tar"
    result_archive = os.path.join(g.storage_dir, full_archive_name)

    sly.fs.archive_directory(g.coco_base_dir, result_archive)
    app_logger.info("Result directory is archived")

    upload_progress = []
    remote_archive_path = f"/Export to COCO/{full_archive_name}"
    def _print_progress(monitor, upload_progress):
        if len(upload_progress) == 0:
            upload_progress.append(sly.Progress(message="Upload {!r}".format(full_archive_name),
                                                total_cnt=monitor.len,
                                                ext_logger=app_logger,
                                                is_size=True))
        upload_progress[0].set_current_value(monitor.bytes_read)

    file_info = g.api.file.upload(g.team_id, result_archive, remote_archive_path,
                                lambda m: _print_progress(m, upload_progress))
    app_logger.info("Uploaded to Team-Files: {!r}".format(file_info.full_storage_url))
    g.api.task.set_output_archive(g.task_id, file_info.id, full_archive_name, file_url=file_info.full_storage_url)

