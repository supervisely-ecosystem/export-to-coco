import os
import globals as g
import supervisely_lib as sly
from supervisely_lib.io.fs import mkdir


def get_categories_map_from_meta(meta):
    obj_classes = meta.obj_classes
    categories_mapping = {}
    for idx, obj_class in enumerate(obj_classes):
        categories_mapping[obj_class.name] = idx + 1
    return categories_mapping


def get_categories_from_meta(meta):
    obj_classes = meta.obj_classes
    categories = []
    for idx, obj_class in enumerate(obj_classes):
        categories.append(dict(
            supercategory=obj_class.name,
            id=idx + 1,  # supercategory id
            name=obj_class.name
        ))
    return categories


def coco_segmentation(segmentation):  # works only with external vertices for now
    segmentation = [coord for sublist in segmentation for coord in sublist]
    return segmentation


def coco_bbox(bbox):
    bbox = [coord for sublist in bbox for coord in sublist]
    x, y, max_x, max_y = bbox
    width = max_x - x
    height = max_y - y
    bbox = (x, y, width, height)
    return bbox


def create_coco_dataset(coco_dataset_dir):
    mkdir(os.path.join(coco_dataset_dir))
    img_dir = os.path.join(coco_dataset_dir, 'images')
    mkdir(img_dir)
    ann_dir = os.path.join(coco_dataset_dir, 'annotations')
    mkdir(ann_dir)
    return img_dir, ann_dir


def create_coco_annotation(meta, categories_mapping, dataset, user_name, image_infos, anns, label_id, progress):
    coco_ann = dict(
        info=dict(
            description=dataset.description,
            url="None",
            version=str(1.0),
            year=int(dataset.created_at[:4]),
            contributor=user_name,
            date_created=dataset.created_at,
        ),
        licenses=[dict(url="None", id=0, name="None")],
        images=[
            # license, url, file_name, height, width, date_captured, id
        ],
        #type="instances",
        annotations=[
            # segmentation, area, iscrowd, image_id, bbox, category_id, id
        ],
        categories=get_categories_from_meta(meta)  # supercategory, id, name
    )
    sdfsc = []
    for image_info, ann in zip(image_infos, anns):

        sdfsc.append(image_info.id)
        coco_ann["images"].append(dict(
            license="None",
            file_name=image_info.name,
            url=image_info.full_storage_url,  # coco_url, flickr_url
            height=image_info.height,
            width=image_info.width,
            date_captured=image_info.created_at,
            id=image_info.id
        ))

        for label in ann.labels:
            segmentation = label.geometry.to_json()["points"]["exterior"]
            segmentation = coco_segmentation(segmentation)

            bbox = label.geometry.to_bbox().to_json()["points"]["exterior"]
            bbox = coco_bbox(bbox)

            label_id += 1
            coco_ann["annotations"].append(dict(
                segmentation=[segmentation],                            # a list of polygon vertices around the object, but can also be a run-length-encoded (RLE) bit mask
                area=label.geometry.area,                               # Area is measured in pixels (e.g. a 10px by 20px box would have an area of 200)
                iscrowd=0,                                              # Is Crowd specifies whether the segmentation is for a single object or for a group/cluster of objects
                image_id=image_info.id,                                 # The image id corresponds to a specific image in the dataset
                bbox=bbox,                                              # he COCO bounding box format is [top left x position, top left y position, width, height]
                category_id=categories_mapping[label.obj_class.name],   # The category id corresponds to a single category specified in the categories section
                id=label_id,                                            # Each annotation also has an id (unique to all other annotations in the dataset)
            ))
    progress.iters_done_report(len(image_infos))
    return coco_ann


def upload_coco_project(full_archive_name, result_archive, app_logger):
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
