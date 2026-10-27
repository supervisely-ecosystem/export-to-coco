"""Export to COCO: headless task started from an images project's "Download as" menu."""

import os

import supervisely as sly
from dotenv import load_dotenv

import platform_io
from exporter import export_project
from settings import Settings


def main() -> None:
    if not sly.is_production():
        load_dotenv("local.env")
        load_dotenv(os.path.expanduser("~/supervisely.env"))

    settings = Settings.from_env()
    project_id = sly.env.project_id()
    sly.logger.info(f"Export settings: {settings}")
    api = sly.Api.from_env()

    platform_io.register_workflow_input(api, project_id)
    project_dir = export_project(api, project_id, settings, sly.app.get_data_dir())
    archive = sly.output.set_download(project_dir)  # archives the folder, uploads it, sets the task's download link
    platform_io.register_workflow_output(api, archive)


if __name__ == "__main__":
    sly.main_wrapper("main", main)
