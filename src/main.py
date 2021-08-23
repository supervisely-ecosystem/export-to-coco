import globals as g
import object_detection
import stuff_segmentation
import supervisely_lib as sly


@g.my_app.callback("export_coco")
@sly.timeit
def export_coco(api: sly.Api, task_id, context, state, app_logger):
    if g.isObjectDetection:
        object_detection.start_object_detection()
    elif g.isStuffSegmentation:
        stuff_segmentation.start_stuff_segmentation()

    g.my_app.stop()


def main():
    sly.logger.info("Input arguments", extra={
        "TASK_ID": g.task_id,
        "context.teamId": g.team_id,
        "context.workspaceId": g.workspace_id,
        "context.projectId": g.project_id
    })

    # Run application service
    g.my_app.run(initial_events=[{"command": "export_coco"}])


if __name__ == "__main__":
    sly.main_wrapper("main", main)