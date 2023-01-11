import os
import ast
from distutils.util import strtobool
import supervisely as sly
from supervisely.io.fs import mkdir
from supervisely.app.v1.app_service import AppService
from dotenv import load_dotenv

if sly.is_development():
    load_dotenv("local.env")
    load_dotenv(os.path.expanduser("~/supervisely.env"))

my_app = AppService()
api: sly.Api = my_app.public_api

selected_format = os.environ["modal.state.selectedFormat"]
selected_output = os.environ["modal.state.selectedOutput"]
all_datasets = bool(strtobool(os.getenv("modal.state.allDatasets")))
selected_datasets = ast.literal_eval(os.environ["modal.state.datasets"])

task_id = os.environ["TASK_ID"]
user_id = os.environ["context.userId"]
team_id = int(os.environ["context.teamId"])
workspace_id = int(os.environ["context.workspaceId"])
project_id = int(os.environ["modal.state.slyProjectId"])

# user = api.user.get_info_by_id(user_id)
user_name = "Supervisely"
project = api.project.get_info_by_id(project_id)
meta_json = api.project.get_meta(project_id)
meta = sly.ProjectMeta.from_json(meta_json)

storage_dir = os.path.join(my_app.data_dir, "storage_dir")
mkdir(storage_dir, True)

coco_base_dir = os.path.join(storage_dir, project.name)
mkdir(coco_base_dir)
