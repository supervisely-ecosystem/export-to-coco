import os
import numpy as np
import supervisely as sly

from supervisely.io.fs import mkdir
from itertools import groupby
from supervisely.geometry import bitmap

import globals as g


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
        categories.append(
            dict(
                supercategory=obj_class.name,
                id=idx + 1,  # supercategory id
                name=obj_class.name,
            )
        )
    return categories


def get_project_contributors():
    pass


def coco_segmentation(segmentation):  # works only with external vertices for now
    segmentation = [float(coord) for sublist in segmentation for coord in sublist]
    return segmentation


def extend_mask_up_to_image(binary_mask, image_shape, origin):
    y, x = origin.col, origin.row
    new_mask = np.zeros(image_shape, dtype=binary_mask.dtype)
    new_mask[x : x + binary_mask.shape[0], y : y + binary_mask.shape[1]] = binary_mask
    return new_mask


def coco_segmentation_rle(segmentation):
    binary_mask = np.asfortranarray(segmentation)
    rle = {"counts": [], "size": list(binary_mask.shape)}
    counts = rle.get("counts")
    for i, (value, elements) in enumerate(groupby(binary_mask.ravel(order="F"))):
        if i == 0 and value == 1:
            counts.append(0)
        counts.append(len(list(elements)))
    return rle


def coco_bbox(bbox):
    bbox = [float(coord) for sublist in bbox for coord in sublist]
    x, y, max_x, max_y = bbox
    width = max_x - x
    height = max_y - y
    bbox = (x, y, width, height)
    return bbox


def create_coco_dataset(coco_dataset_dir):
    mkdir(os.path.join(coco_dataset_dir))
    img_dir = os.path.join(coco_dataset_dir, "images")
    mkdir(img_dir)
    ann_dir = os.path.join(coco_dataset_dir, "annotations")
    mkdir(ann_dir)
    return img_dir, ann_dir


def create_coco_annotation(
    categories_mapping,
    image_infos,
    anns,
    label_id,
    coco_ann,
    caption_id,
    coco_captions,
    progress,
):
    for image_info, ann in zip(image_infos, anns):
        image_coco_ann = dict(
            license="None",
            file_name=image_info.name,
            url="None",  # image_info.full_storage_url,  # coco_url, flickr_url
            height=image_info.height,
            width=image_info.width,
            date_captured=image_info.created_at,
            id=image_info.id,
        )
        coco_ann["images"].append(image_coco_ann)
        if coco_captions is not None and g.include_captions:
            coco_captions["images"].append(image_coco_ann)

        for label in ann.labels:
            if g.rectangle_mark in label.description:
                segmentation = []
            elif label.geometry.name() == bitmap.Bitmap.name():
                segmentation = extend_mask_up_to_image(
                    label.geometry.data,
                    (image_info.height, image_info.width),
                    label.geometry.origin,
                )
                segmentation = coco_segmentation_rle(segmentation)
            else:
                segmentation = label.geometry.to_json()["points"]["exterior"]
                segmentation = [coco_segmentation(segmentation)]

            bbox = label.geometry.to_bbox().to_json()["points"]["exterior"]
            bbox = coco_bbox(bbox)

            label_id += 1
            coco_ann["annotations"].append(
                dict(
                    segmentation=segmentation,  # a list of polygon vertices around the object, but can also be a run-length-encoded (RLE) bit mask
                    area=label.geometry.area,  # Area is measured in pixels (e.g. a 10px by 20px box would have an area of 200)
                    iscrowd=0,  # Is Crowd specifies whether the segmentation is for a single object or for a group/cluster of objects
                    image_id=image_info.id,  # The image id corresponds to a specific image in the dataset
                    bbox=bbox,  # he COCO bounding box format is [top left x position, top left y position, width, height]
                    category_id=categories_mapping[
                        label.obj_class.name
                    ],  # The category id corresponds to a single category specified in the categories section
                    id=label_id,  # Each annotation also has an id (unique to all other annotations in the dataset)
                )
            )
        if coco_captions is not None and g.include_captions:
            for tag in ann.img_tags:
                if (
                    tag.meta.name == "caption"
                    and tag.meta.value_type == sly.TagValueType.ANY_STRING
                ):
                    caption_id += 1
                    coco_captions["annotations"].append(
                        dict(
                            image_id=image_info.id,
                            id=caption_id,
                            caption=tag.value,
                        )
                    )
        progress.iter_done_report()
    return coco_ann, label_id, coco_captions, caption_id


def upload_coco_project(full_archive_name, result_archive, app_logger):
    sly.fs.archive_directory(g.storage_dir, result_archive)
    app_logger.info("Result directory is archived")

    upload_progress = []
    remote_archive_path = os.path.join(
        sly.team_files.RECOMMENDED_EXPORT_PATH, f"export-to-COCO/{full_archive_name}"
    )

    def _print_progress(monitor, upload_progress):
        if len(upload_progress) == 0:
            upload_progress.append(
                sly.Progress(
                    message="Upload {!r}".format(full_archive_name),
                    total_cnt=monitor.len,
                    ext_logger=app_logger,
                    is_size=True,
                )
            )
        upload_progress[0].set_current_value(monitor.bytes_read)

    file_info = g.api.file.upload(
        g.team_id,
        result_archive,
        remote_archive_path,
        lambda m: _print_progress(m, upload_progress),
    )
    app_logger.info("Uploaded to Team Files: {!r}".format(file_info.storage_path))
    g.api.task.set_output_archive(
        g.task_id, file_info.id, full_archive_name, file_url=file_info.storage_path
    )


def create_coco_ann_templates(dataset, user_name, meta: sly.ProjectMeta):
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
        # type="instances",
        annotations=[
            # segmentation, area, iscrowd, image_id, bbox, category_id, id
        ],
        categories=get_categories_from_meta(meta),  # supercategory, id, name
    )

    if not g.include_captions:
        return coco_ann, None
    captions_tag_meta = meta.get_tag_meta("caption")
    if captions_tag_meta is None or captions_tag_meta.value_type != sly.TagValueType.ANY_STRING:
        return coco_ann, None
    coco_captions = dict(
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
        # type="captions",
        annotations=[
            # image_id, id, caption
        ],
    )
    return coco_ann, coco_captions
