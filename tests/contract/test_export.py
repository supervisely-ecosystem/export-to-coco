"""Runs the export against a real instance for every case in cases/.

Opt-in: SLY_CONTRACT_TESTS=1, credentials in ~/supervisely.env (SERVER_ADDRESS, API_TOKEN) and
SLY_CONTRACT_PROJECT_ID pointing at an images project in a dedicated test workspace. The project is
only read; output goes to a pytest tmp dir and nothing is uploaded.

    SLY_CONTRACT_TESTS=1 SLY_CONTRACT_PROJECT_ID=123 pytest -m contract tests/contract
"""

import glob
import json
import os

import pytest
import supervisely as sly
from dotenv import dotenv_values, load_dotenv

from exporter import export_project
from settings import Settings

CASES = sorted(glob.glob(os.path.join(os.path.dirname(__file__), "..", "..", "cases", "*.env")))

pytestmark = [
    pytest.mark.contract,
    pytest.mark.skipif(os.getenv("SLY_CONTRACT_TESTS") != "1", reason="contract tests are opt-in"),
]


@pytest.fixture(scope="module")
def api():
    load_dotenv(os.path.expanduser("~/supervisely.env"))
    return sly.Api.from_env()


@pytest.fixture(scope="module")
def project_id():
    return int(os.environ["SLY_CONTRACT_PROJECT_ID"])


@pytest.mark.parametrize("case", CASES, ids=os.path.basename)
def test_case_produces_valid_coco(case, api, project_id, tmp_path):
    env = dict(dotenv_values(case))
    if env.get("modal.state.allDatasets", "True").lower() == "false":
        env["modal.state.datasets"] = str([api.dataset.get_list(project_id, recursive=True)[0].id])
    settings = Settings.from_env(env)

    project_dir = export_project(api, project_id, settings, str(tmp_path))

    meta = sly.ProjectMeta.from_json(api.project.get_meta(project_id))
    dataset_dirs = sorted(os.listdir(project_dir))
    assert dataset_dirs, "one folder per exported dataset"
    for name in dataset_dirs:
        ds_dir = os.path.join(project_dir, name)
        with open(os.path.join(ds_dir, "annotations", "instances.json")) as f:
            instances = json.load(f)
        assert [c["name"] for c in instances["categories"]] == [c.name for c in meta.obj_classes]
        if settings.export_images:
            exported = set(os.listdir(os.path.join(ds_dir, "images")))
            assert exported == {i["file_name"] for i in instances["images"]}
        else:
            assert not os.path.exists(os.path.join(ds_dir, "images"))
        try:
            from pycocotools.coco import COCO
        except ImportError:
            continue
        COCO(os.path.join(ds_dir, "annotations", "instances.json"))  # loads = structurally valid
