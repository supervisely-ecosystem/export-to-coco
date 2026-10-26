"""Supervisely -> COCO conversion for one dataset. Pure: no API calls, no environment, no files."""

from __future__ import annotations

import uuid
from collections import Counter
from typing import Any

import supervisely as sly
from supervisely.convert.image.coco.coco_helper import get_categories_from_meta, sly_ann_to_coco

CAPTION_TAG = "caption"

# exported as is by sly_ann_to_coco
_NATIVE_GEOMETRIES = {sly.Polygon.name(), sly.Rectangle.name(), sly.GraphNodes.name()}
# exported as polygons; all parts of one label stay one COCO object
_TO_POLYGONS = {sly.Bitmap.name(), sly.AlphaMask.name(), sly.Multipolygon.name()}


def has_captions(meta: sly.ProjectMeta) -> bool:
    """Captions come from an image-level string tag named "caption"."""
    tag_meta = meta.get_tag_meta(CAPTION_TAG)
    return (
        tag_meta is not None
        and tag_meta.value_type == sly.TagValueType.ANY_STRING
        and tag_meta.applicable_to != sly.TagApplicableTo.OBJECTS_ONLY
    )


def is_annotated(image: sly.ImageInfo) -> bool:
    return image.labels_count > 0 or len(image.tags) > 0


def parse_annotation(ann_json: dict[str, Any], image: sly.ImageInfo, meta: sly.ProjectMeta) -> sly.Annotation:
    """An unreadable annotation exports the image without labels instead of failing the task."""
    try:
        return sly.Annotation.from_json(ann_json, meta)
    except Exception as e:  # noqa: BLE001 - any malformed figure must not stop the export
        sly.logger.warning(
            f"Image {image.name!r} (id {image.id}): annotation is unreadable, exported without labels: {e}"
        )
        return sly.Annotation((image.height, image.width))


def normalize_labels(ann: sly.Annotation, skipped: Counter) -> sly.Annotation:
    """Keep geometries COCO can express; turn masks into polygon groups; count the rest in `skipped`."""
    labels = []
    for binding_key, group in ann.get_bindings().items():
        for label in group:
            geometry = label.geometry.name()
            if geometry in _NATIVE_GEOMETRIES:
                labels.append(label)
            elif geometry in _TO_POLYGONS:
                polygon_class = label.obj_class.clone(geometry_type=sly.Polygon)
                key = binding_key or uuid.uuid4().hex
                labels.extend(part.clone(binding_key=key) for part in label.convert(polygon_class))
            else:
                skipped[geometry] += 1
    return ann.clone(labels=labels)


class CocoDatasetBuilder:
    """Accumulates one dataset's images into COCO `instances` (and optionally `captions`) dicts."""

    def __init__(self, dataset: sly.DatasetInfo, meta: sly.ProjectMeta, with_captions: bool):
        self._class_ids = {obj_class.name: idx for idx, obj_class in enumerate(meta.obj_classes, start=1)}
        self.instances = _template(dataset)
        self.instances["categories"] = get_categories_from_meta(meta)
        self.captions: dict[str, Any] | None = _template(dataset) if with_captions and has_captions(meta) else None
        self.skipped: Counter = Counter()

    def add(self, image: sly.ImageInfo, ann: sly.Annotation) -> None:
        image_id = len(self.instances["images"]) + 1
        entry = _image_entry(image, image_id)
        self.instances["images"].append(entry)

        objects, captions = sly_ann_to_coco(
            normalize_labels(ann, self.skipped),
            image_id,
            self._class_ids,
            last_label_id=len(self.instances["annotations"]),
            last_caption_id=len(self.captions["annotations"]) if self.captions else 0,
        )
        for obj in objects:
            if not obj["segmentation"] and "keypoints" not in obj:
                # bbox-only object: area of the exported bbox (the SDK counts inclusive pixels)
                obj["area"] = obj["bbox"][2] * obj["bbox"][3]
        self.instances["annotations"].extend(objects)

        if self.captions is not None:
            self.captions["images"].append(entry)
            self.captions["annotations"].extend(captions)


def _template(dataset: sly.DatasetInfo) -> dict[str, Any]:
    return {
        "info": {
            "description": dataset.description,
            "url": "None",
            "version": "1.0",
            "year": int(dataset.created_at[:4]),
            "contributor": "Supervisely",
            "date_created": dataset.created_at,
        },
        "licenses": [{"url": "None", "id": 0, "name": "None"}],
        "images": [],
        "annotations": [],
    }


def _image_entry(image: sly.ImageInfo, image_id: int) -> dict[str, Any]:
    return {
        "license": "None",
        "file_name": image.name,
        "url": "None",
        "height": image.height,
        "width": image.width,
        "date_captured": image.created_at,
        "id": image_id,
        "sly_id": image.id,
    }


def skipped_summary(skipped: Counter) -> list[str]:
    return [f"{count} × {geometry}" for geometry, count in sorted(skipped.items())]
