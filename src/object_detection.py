import os
import globals as g
import convert_geometry
import supervisely_lib as sly
from supervisely_lib.io.fs import mkdir
from supervisely_lib.io.json import dump_json_file


def start_object_detection():
    datasets = [ds for ds in g.api.dataset.get_list(g.project_id)]
    for dataset in datasets:
        coco_dataset_dir = os.path.join(g.coco_base_dir, dataset.name)
        mkdir(os.path.join(coco_dataset_dir))
        ann_dir = os.path.join(g.coco_base_dir, 'annotations')
        mkdir(ann_dir)

        images = g.api.image.get_list(dataset.id)
        for batch in sly.batched(images):
            image_ids = [image_info.id for image_info in batch]
            image_names = [image_info.name for image_info in batch]
            image_paths = [os.path.join(coco_dataset_dir, image_info.name) for image_info in batch]
            g.api.image.download_paths(dataset.id, image_ids, image_paths)

            ann_infos = g.api.annotation.download_batch(dataset.id, image_ids)
            anns = [sly.Annotation.from_json(x.annotation, g.meta) for x in ann_infos]

            meta = convert_geometry.prepare_meta(g.meta)
            new_anns = [convert_geometry.convert_annotation(ann, meta) for ann in anns]

            data = dict(
                info=dict(
                    description=None,
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

            for image_info, ann in zip(batch, new_anns):
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
                    segmentation = label.geometry.to_json()["points"]["exterior"]
                    segmentation = [coord for sublist in segmentation for coord in sublist]

                    bbox = label.geometry.to_bbox().to_json()["points"]["exterior"]
                    bbox = [coord for sublist in bbox for coord in sublist]
                    x, y, max_x, max_y = bbox
                    width = max_x - x
                    height = max_y - y
                    bbox = (x, y, width, height)

                    data["annotations"].append(dict(
                        segmentation=[segmentation],
                        area=label.geometry.area,  # wrong?
                        iscrowd=0,
                        image_id=image_info.id,
                        bbox=bbox,
                        category_id=None,
                        id=None,  # label.id?
                    ))

                    data["categories"].append(dict(
                        supercategory=None,
                        id=None,  # label.id?
                        name=label.obj_class.name
                    ))

        dump_json_file(data, os.path.join(ann_dir, f"instances_{dataset.name}.json"))
