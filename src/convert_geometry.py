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


def convert_annotation(ann: sly.Annotation, dst_meta):
    new_labels = []
    for lbl in ann.labels:
        try:
            new_cls = dst_meta.obj_classes.get(lbl.obj_class.name)
            if lbl.obj_class.geometry_type == new_cls.geometry_type:
                new_labels.append(lbl)
            else:
                converted_label = lbl.convert(new_cls)
                if lbl.obj_class.geometry_type == polyline.Polyline:
                    new_mask = np.zeros(ann.img_size, dtype=np.uint8)
                    polyline_points = lbl.geometry.rotate(
                        image_rotator.ImageRotator(ann.img_size[::-1], 90)
                    )
                    polyline_points = polyline_points.flipud(ann.img_size)
                    polyline_points = polyline_points.exterior_np
                    new_mask = cv2.polylines(
                        new_mask,
                        [polyline_points],
                        isClosed=False,
                        color=255,
                        thickness=2,
                    )

                    new_geometry = bitmap.Bitmap(new_mask)
                    cloned_obj_class = new_cls.clone(geometry_type=bitmap.Bitmap)
                    new_label = lbl.clone(
                        geometry=new_geometry,
                        obj_class=cloned_obj_class,
                    )

                    new_labels.extend([new_label])
                    continue
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
