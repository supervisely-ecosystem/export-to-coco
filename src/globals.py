import os
import supervisely_lib as sly
from supervisely_lib.io.fs import mkdir

my_app = sly.AppService()
api: sly.Api = my_app.public_api

task_id = os.environ["TASK_ID"]
user_id = os.environ["context.userId"]
team_id = int(os.environ['context.teamId'])
workspace_id = int(os.environ['context.workspaceId'])
project_id = int(os.environ['context.projectId'])

user = api.user.get_info_by_id(user_id)
project = api.project.get_info_by_id(project_id)
meta_json = api.project.get_meta(project_id)
meta = sly.ProjectMeta.from_json(meta_json)


storage_dir = os.path.join(my_app.data_dir, "storage_dir")
coco_base_dir = os.path.join(storage_dir, project.name)
#sly_base_dir = os.path.join(storage_dir, "sly_base_dir")

mkdir(storage_dir, True)
mkdir(coco_base_dir)
#mkdir(sly_base_dir)


isObjectDetection = True
isStuffSegmentation = False
# isKeypointDetection = False
# isPanopticSegmentation = False
# isImageCaptioning = False