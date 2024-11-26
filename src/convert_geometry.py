import supervisely as sly
from supervisely.annotation.json_geometries_map import GET_GEOMETRY_FROM_STR
from supervisely import Bitmap, Polyline, Rectangle
from supervisely.sly_logger import logger
from typing import List
import uuid

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


def convert_w_binding_key(
    label: sly.Label, new_obj_class: sly.ObjClass, binding_key: str
) -> List[sly.Label]:
    """
    Convert geometries with a binding key (used only for bitmap labels for further grouping)
    """

    if binding_key is None and label.geometry.name() == sly.Bitmap.name():
        binding_key = uuid.uuid4().hex

    return [label.clone(binding_key=binding_key) for label in label.convert(new_obj_class)]


def convert_annotation(ann_info, img_info, src_meta, dst_meta, rectangle_mark):
    try:
        ann = sly.Annotation.from_json(ann_info.annotation, src_meta)
    except Exception as e:
        sly.logger.debug(f"Exception while creating sly.Annotation from JSON: {e}")
        return sly.Annotation((img_info.height, img_info.width))
    new_labels = []

    groups = ann.get_bindings()
    for binding_key, labels in groups.items():
        for label in labels:
            try:
                new_cls = dst_meta.obj_classes.get(label.obj_class.name)
                if label.obj_class.geometry_type == new_cls.geometry_type:
                    new_labels.append(label)
                else:
                    converted_label = convert_w_binding_key(label, new_cls, binding_key)
                    if label.obj_class.geometry_type == Polyline:
                        raise NotImplementedError("Shape Polyline is not supported")
                    if label.obj_class.geometry_type == Rectangle:
                        new_descr = converted_label[0].description + " " + rectangle_mark
                        new_label = converted_label[0].clone(description=new_descr)
                        converted_label.pop()
                        converted_label.append(new_label)
                    new_labels.extend(converted_label)
            except NotImplementedError:
                logger.warning(
                    f"Unsupported conversion of annotation '{label.obj_class.geometry_type.name()}' type to '{new_cls.geometry_type.name()}'. Skipping annotation with [ID: {label.to_json()['id']}]",
                    exc_info=False,
                )
                continue
    new_tags = []
    for tag in ann.img_tags:
        tag_meta = dst_meta.get_tag_meta(tag.meta.name)
        if tag_meta is not None:
            new_tags.append(tag.clone(meta=tag_meta))
    return ann.clone(labels=new_labels, img_tags=new_tags)
