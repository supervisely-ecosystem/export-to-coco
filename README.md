<div align="center" markdown>
<img src="https://user-images.githubusercontent.com/48913536/183899083-64d7683d-57f9-4f7a-b5f4-bf9e7ffd3246.png"/>


# Export to COCO

<p align="center">
  <a href="#Overview">Overview</a> •
  <a href="#How-To-Use">How To Use</a> •
  <a href="#Results">Results</a>
</p>

[![](https://img.shields.io/badge/supervisely-ecosystem-brightgreen)](https://ecosystem.supervise.ly/apps/supervisely-ecosystem/export-to-coco)
[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervise.ly/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/export-to-coco)
[![views](https://app.supervise.ly/img/badges/views/supervisely-ecosystem/export-to-coco.png)](https://supervise.ly)
[![runs](https://app.supervise.ly/img/badges/runs/supervisely-ecosystem/export-to-coco.png)](https://supervise.ly)

</div>

# Overview

App converts [Supervisely format](https://docs.supervise.ly/data-organization/00_ann_format_navi) project to [COCO format](https://cocodataset.org/#home) as a **downloadable .tar archive**

Application key points:

- <img src='https://img.shields.io/badge/Version-1.3.0-blue'/>
  
  🔥 Saves **Supervisely** polylines to **COCO** RLE mask that is represented as a 2px line!
- Supports **instances.json** from **COCO** format
- Сonverts **Supervisely** polygons, rectangles, bitmaps to **COCO** polygons and bboxes.
- 👉 Сonverts annotations to polygons without preserving holes. To preserve holes you need to use [Export to COCO mask](https://ecosystem.supervise.ly/apps/export-to-coco-mask)
- Backward compatible with [Import COCO](https://github.com/supervisely-ecosystem/import-coco)

# How to Use

1. Add [Export to COCO](https://ecosystem.supervise.ly/apps/export-to-coco) to your team from Ecosystem.

<img data-key="sly-module-link" data-module-slug="supervisely-ecosystem/export-to-coco" src="https://imgur.com/OxqtYTS.png" width="350px" style='padding-bottom: 20px'/>  

2. Run app from the context menu of **Images Project**:

<img src="https://imgur.com/0JwLqYJ.png" width="100%"/>

3. Select options in the modal window and press the **RUN** button

<div align="center" markdown>
  <img src="https://user-images.githubusercontent.com/48913536/211818281-a98def47-e3b6-4227-868b-78f4a89b5b4e.png" width="70%"/>
</div>


# Results

After running the application, you will be redirected to the `Tasks` page. Once application processing has finished, your link for downloading will be available. Click on the `file name` to download it.

<img src="https://imgur.com/kK1wmN9.png"/>

You can also find your converted project in   
`Team Files` -> `Export to COCO` -> `<taskId>_<projectName>.tar`

<img src="https://imgur.com/CovU9Re.png"/>
