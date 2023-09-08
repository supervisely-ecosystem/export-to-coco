import supervisely as sly
from supervisely.annotation.json_geometries_map import GET_GEOMETRY_FROM_STR
from supervisely.geometry import rectangle, polyline, bitmap, image_rotator
from globals import rectangle_mark
from supervisely.sly_logger import logger
import numpy as np
import cv2


def prepare_meta(meta):
    new_classes = []
    for cls in meta.obj_classes:
        cls: sly.ObjClass
        new_classes.append(cls.clone(geometry_type=GET_GEOMETRY_FROM_STR("polygon")))

    meta = meta.clone(obj_classes=sly.ObjClassCollection(new_classes))
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
    return ann.clone(labels=new_labels)
