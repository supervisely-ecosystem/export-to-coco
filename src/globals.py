import os
import supervisely_lib as sly
from supervisely_lib.io.fs import mkdir

my_app = sly.AppService()
api: sly.Api = my_app.public_api

task_id = os.environ["TASK_ID"]
user_id = os.environ["context.userId"]
team_id = int(os.environ['context.teamId'])
workspace_id = int(os.environ['context.workspaceId'])
project_id = int(os.environ['modal.state.slyProjectId'])

# user = api.user.get_info_by_id(user_id)
user = "Supervisely"
project = api.project.get_info_by_id(project_id)
meta_json = api.project.get_meta(project_id)
meta = sly.ProjectMeta.from_json(meta_json)

storage_dir = os.path.join(my_app.data_dir, "storage_dir")
mkdir(storage_dir, True)

coco_base_dir = os.path.join(storage_dir, project.name)
mkdir(coco_base_dir)
