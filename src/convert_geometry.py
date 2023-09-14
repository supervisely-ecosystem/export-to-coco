import supervisely as sly
from supervisely.annotation.json_geometries_map import GET_GEOMETRY_FROM_STR
from supervisely.geometry import rectangle, polyline, bitmap, image_rotator
from globals import rectangle_mark
from supervisely.sly_logger import logger
import numpy as np
import cv2


def prepare_meta(meta: sly.ProjectMeta):
    new_classes = []
    for cls in meta.obj_classes:
        cls: sly.ObjClass
        new_classes.append(cls.clone(geometry_type=GET_GEOMETRY_FROM_STR("polygon")))

    new_tag_metas = []
    captions_tag_meta = meta.get_tag_meta("caption")
    if captions_tag_meta is not None:
        is_applicable = captions_tag_meta.applicable_to != sly.TagApplicableTo.OBJECTS_ONLY
        is_string_type = captions_tag_meta.value_type == sly.TagValueType.ANY_STRING
        if is_applicable and is_string_type:
            new_tag_metas = [captions_tag_meta.clone()]
    meta = meta.clone(obj_classes=sly.ObjClassCollection(new_classes), tag_metas=new_tag_metas)
    return meta


def convert_annotation(ann_info, img_info, src_meta, dst_meta):
    try:
        ann = sly.Annotation.from_json(ann_info.annotation, src_meta)
    except:
        return sly.Annotation(img_info.height, img_info.width)
    new_labels = []
    for lbl in ann.labels:
        try:
            new_cls = dst_meta.obj_classes.get(lbl.obj_class.name)
            if lbl.obj_class.geometry_type == new_cls.geometry_type:
                new_labels.append(lbl)
            else:
                converted_label = lbl.convert(new_cls)
                if lbl.obj_class.geometry_type == polyline.Polyline:
                    raise NotImplementedError
                if lbl.obj_class.geometry_type == rectangle.Rectangle:
                    new_descr = converted_label[0].description + " " + rectangle_mark
                    new_label = converted_label[0].clone(description=new_descr)
                    converted_label.pop()
                    converted_label.append(new_label)
                new_labels.extend(converted_label)
        except NotImplementedError as e:
            logger.warning(
                f"Unsupported conversion of annotation '{lbl.obj_class.geometry_type.name()}' type to '{new_cls.geometry_type.name()}'. Skipping annotation with [ID: {lbl.to_json()['id']}]",
                exc_info=False,
            )
            continue
    new_tags = []
    for tag in ann.img_tags:
        tag_meta = dst_meta.get_tag_meta(tag.meta.name)
        if tag_meta is not None:
            new_tags.append(tag.clone(meta=tag_meta))
    return ann.clone(labels=new_labels, img_tags=new_tags)
