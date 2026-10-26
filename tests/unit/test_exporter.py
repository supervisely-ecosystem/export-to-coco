"""export_project end to end against an in-memory stand-in for the API: folder layout and filters."""

import json
import os
from types import SimpleNamespace

import supervisely as sly

from exporter import export_project
from settings import Settings

CLS = sly.ObjClass("box", sly.Rectangle)
META = sly.ProjectMeta(obj_classes=[CLS])


def info(cls, **values):
    return cls(**{**{f: None for f in cls._fields}, **values})


def image(image_id, name, labels_count):
    return info(
        sly.ImageInfo,
        id=image_id,
        name=name,
        width=8,
        height=6,
        labels_count=labels_count,
        tags=[],
        created_at="2024-01-01T00:00:00.000Z",
    )


class FakeApi:
    """Only the calls export_project makes. Datasets 1 (root) and 2 (nested) of project 10."""

    def __init__(self):
        self.datasets = [
            info(sly.DatasetInfo, id=1, name="train", description="", created_at="2024-01-01T00:00:00.000Z"),
            info(sly.DatasetInfo, id=2, name="val", description="", created_at="2024-01-01T00:00:00.000Z"),
        ]
        self.images = {1: [image(11, "a.jpg", 1), image(12, "b.jpg", 0)], 2: [image(21, "c.jpg", 1)]}
        box = sly.Annotation((6, 8), labels=[sly.Label(sly.Rectangle(1, 1, 3, 4), CLS)]).to_json()
        empty = sly.Annotation((6, 8)).to_json()
        self.anns = {11: box, 12: empty, 21: box}

        self.project = SimpleNamespace(
            get_info_by_id=lambda pid: SimpleNamespace(id=pid, name="lemons"),
            get_meta=lambda pid: META.to_json(),
        )
        self.dataset = SimpleNamespace(get_list=lambda pid, recursive: self.datasets)
        self.image = SimpleNamespace(get_list=lambda ds_id: self.images[ds_id], download_paths_async=self._download)
        self.annotation = SimpleNamespace(download_batch_async=self._anns)

    async def _download(self, ids, paths):
        for path in paths:
            with open(path, "wb") as f:
                f.write(b"jpg")

    async def _anns(self, dataset_id, ids):
        return [SimpleNamespace(image_id=i, annotation=self.anns[i]) for i in ids]


def load(path):
    with open(path) as f:
        return json.load(f)


def test_layout_with_images(tmp_path):
    settings = Settings(export_images=True, only_annotated=False, dataset_ids=None, with_captions=False)
    root = export_project(FakeApi(), 10, settings, str(tmp_path))

    assert root == os.path.join(str(tmp_path), "lemons")
    assert sorted(os.listdir(root)) == ["1_train", "2_val"]
    assert sorted(os.listdir(os.path.join(root, "1_train", "images"))) == ["a.jpg", "b.jpg"]
    assert os.listdir(os.path.join(root, "1_train", "annotations")) == ["instances.json"]
    instances = load(os.path.join(root, "1_train", "annotations", "instances.json"))
    assert [i["file_name"] for i in instances["images"]] == ["a.jpg", "b.jpg"]
    assert len(instances["annotations"]) == 1


def test_annotations_only_selected_dataset_annotated_images(tmp_path):
    settings = Settings(export_images=False, only_annotated=True, dataset_ids=(1,), with_captions=False)
    root = export_project(FakeApi(), 10, settings, str(tmp_path))

    assert os.listdir(root) == ["1_train"]
    assert sorted(os.listdir(os.path.join(root, "1_train"))) == ["annotations"]
    instances = load(os.path.join(root, "1_train", "annotations", "instances.json"))
    assert [i["file_name"] for i in instances["images"]] == ["a.jpg"]


def test_unknown_dataset_id_fails(tmp_path):
    settings = Settings(export_images=False, only_annotated=False, dataset_ids=(99,), with_captions=False)
    try:
        export_project(FakeApi(), 10, settings, str(tmp_path))
    except ValueError as e:
        assert "99" in str(e)
    else:
        raise AssertionError("expected ValueError")
