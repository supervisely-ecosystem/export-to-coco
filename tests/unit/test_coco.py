from collections import Counter

import numpy as np
import pytest
import supervisely as sly

from core.coco import CocoDatasetBuilder, has_captions, is_annotated, normalize_labels, parse_annotation

H, W = 100, 200

POLY = sly.ObjClass("poly", sly.Polygon)
BOX = sly.ObjClass("box", sly.Rectangle)
MASK = sly.ObjClass("mask", sly.Bitmap)
LINE = sly.ObjClass("line", sly.Polyline)
CAPTION = sly.TagMeta("caption", sly.TagValueType.ANY_STRING)
META = sly.ProjectMeta(obj_classes=[POLY, BOX, MASK, LINE], tag_metas=[CAPTION])


def image_info(image_id=1, name="a.jpg", labels_count=0, tags=()):
    fields = {f: None for f in sly.ImageInfo._fields}
    fields.update(
        id=image_id,
        name=name,
        width=W,
        height=H,
        labels_count=labels_count,
        tags=list(tags),
        created_at="2024-05-06T07:08:09.000Z",
    )
    return sly.ImageInfo(**fields)


def dataset_info():
    fields = {f: None for f in sly.DatasetInfo._fields}
    fields.update(id=7, name="ds", description="demo", created_at="2023-01-02T03:04:05.000Z")
    return sly.DatasetInfo(**fields)


def polygon(points):
    return sly.Polygon([sly.PointLocation(row, col) for col, row in points])


def ann(*labels, tags=()):
    return sly.Annotation((H, W), labels=list(labels), img_tags=list(tags))


def build(*anns, with_captions=False, meta=META):
    builder = CocoDatasetBuilder(dataset_info(), meta, with_captions)
    for idx, a in enumerate(anns, start=1):
        builder.add(image_info(image_id=1000 + idx, name=f"{idx}.jpg"), a)
    return builder


def test_categories_follow_meta_order_starting_at_one():
    cats = build().instances["categories"]
    assert [(c["id"], c["name"], c["supercategory"]) for c in cats] == [
        (1, "poly", "poly"),
        (2, "box", "box"),
        (3, "mask", "mask"),
        (4, "line", "line"),
    ]


def test_dataset_info_and_image_entry():
    builder = build(ann())
    assert builder.instances["info"] == {
        "description": "demo",
        "url": "None",
        "version": "1.0",
        "year": 2023,
        "contributor": "Supervisely",
        "date_created": "2023-01-02T03:04:05.000Z",
    }
    assert builder.instances["licenses"] == [{"url": "None", "id": 0, "name": "None"}]
    assert builder.instances["images"] == [
        {
            "license": "None",
            "file_name": "1.jpg",
            "url": "None",
            "height": H,
            "width": W,
            "date_captured": "2024-05-06T07:08:09.000Z",
            "id": 1,
            "sly_id": 1001,
        }
    ]


def test_polygon_exports_exterior_bbox_and_area():
    label = sly.Label(polygon([(10, 20), (50, 20), (50, 60), (10, 60)]), POLY)
    (obj,) = build(ann(label)).instances["annotations"]
    assert obj["segmentation"] == [[10.0, 20.0, 50.0, 20.0, 50.0, 60.0, 10.0, 60.0]]
    assert obj["bbox"] == [10, 20, 40, 40]
    assert obj["area"] == pytest.approx(1600)
    assert (obj["category_id"], obj["image_id"], obj["id"], obj["iscrowd"]) == (1, 1, 1, 0)


def test_rectangle_is_bbox_only_with_bbox_area():
    label = sly.Label(sly.Rectangle(top=20, left=10, bottom=39, right=19), BOX)
    (obj,) = build(ann(label)).instances["annotations"]
    assert obj["segmentation"] == []
    assert obj["bbox"] == [10, 20, 9, 19]
    assert obj["area"] == 9 * 19
    assert obj["category_id"] == 2


def test_bitmap_with_two_blobs_is_one_object_with_two_polygons():
    mask = np.zeros((H, W), dtype=bool)
    mask[10:20, 10:20] = True
    mask[50:60, 100:120] = True
    (obj,) = build(ann(sly.Label(sly.Bitmap(mask), MASK))).instances["annotations"]
    assert len(obj["segmentation"]) == 2
    assert obj["category_id"] == 3
    x, y, w, h = obj["bbox"]
    assert (x, y) == (10, 10) and x + w == 119 and y + h == 59


def test_unsupported_shapes_are_skipped_and_counted():
    line = sly.Label(sly.Polyline([sly.PointLocation(1, 1), sly.PointLocation(5, 5)]), LINE)
    box = sly.Label(sly.Rectangle(0, 0, 5, 5), BOX)
    builder = build(ann(line, box))
    assert [o["category_id"] for o in builder.instances["annotations"]] == [2]
    assert builder.skipped == Counter({"line": 1})


def test_ids_are_sequential_within_dataset():
    box = sly.Label(sly.Rectangle(0, 0, 5, 5), BOX)
    builder = build(ann(box, box), ann(box))
    assert [i["id"] for i in builder.instances["images"]] == [1, 2]
    assert [(o["id"], o["image_id"]) for o in builder.instances["annotations"]] == [(1, 1), (2, 1), (3, 2)]


def test_captions_written_only_when_requested():
    tagged = ann(tags=[sly.Tag(CAPTION, "a lemon")])
    assert build(tagged).captions is None

    captions = build(tagged, ann(), with_captions=True).captions
    assert [i["id"] for i in captions["images"]] == [1, 2]
    assert captions["annotations"] == [{"image_id": 1, "id": 1, "caption": "a lemon"}]
    assert "categories" not in captions


def test_captions_need_an_image_level_string_tag():
    objects_only = sly.TagMeta("caption", sly.TagValueType.ANY_STRING, applicable_to=sly.TagApplicableTo.OBJECTS_ONLY)
    numeric = sly.TagMeta("caption", sly.TagValueType.ANY_NUMBER)
    assert has_captions(META)
    assert not has_captions(META.clone(tag_metas=[objects_only]))
    assert not has_captions(META.clone(tag_metas=[numeric]))
    assert build(with_captions=True, meta=META.clone(tag_metas=[numeric])).captions is None


def test_existing_binding_key_groups_polygons_into_one_object():
    a = sly.Label(polygon([(0, 0), (10, 0), (10, 10)]), POLY, binding_key="k")
    b = sly.Label(polygon([(50, 50), (60, 50), (60, 60)]), POLY, binding_key="k")
    (obj,) = build(ann(a, b)).instances["annotations"]
    assert len(obj["segmentation"]) == 2


def test_normalize_keeps_native_and_counts_rest():
    skipped = Counter()
    point_cls = sly.ObjClass("pt", sly.Point)
    result = normalize_labels(
        ann(sly.Label(sly.Point(1, 1), point_cls), sly.Label(sly.Rectangle(0, 0, 2, 2), BOX)), skipped
    )
    assert [label.geometry.name() for label in result.labels] == ["rectangle"]
    assert skipped == Counter({"point": 1})


def test_unreadable_annotation_exports_image_without_labels():
    result = parse_annotation({"broken": True}, image_info(), META)
    assert result.img_size == (H, W) and result.labels == []


@pytest.mark.parametrize("labels_count,tags,expected", [(0, (), False), (3, (), True), (0, [{"name": "t"}], True)])
def test_is_annotated(labels_count, tags, expected):
    assert is_annotated(image_info(labels_count=labels_count, tags=tags)) is expected
