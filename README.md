<div align="center" markdown>
<img src="https://user-images.githubusercontent.com/48913536/183899083-64d7683d-57f9-4f7a-b5f4-bf9e7ffd3246.png"/>


# Export to COCO

<p align="center">
  <a href="#Overview">Overview</a> •
  <a href="#How-To-Use">How To Use</a> •
  <a href="#Results">Results</a>
</p>

[![](https://img.shields.io/badge/supervisely-ecosystem-brightgreen)](https://ecosystem.supervisely.com/apps/supervisely-ecosystem/export-to-coco)
[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervisely.com/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/export-to-coco)
[![views](https://app.supervisely.com/img/badges/views/supervisely-ecosystem/export-to-coco.png)](https://supervisely.com)
[![runs](https://app.supervisely.com/img/badges/runs/supervisely-ecosystem/export-to-coco.png)](https://supervisely.com)

</div>

# Overview

App converts [Supervisely format](https://docs.supervisely.com/data-organization/00_ann_format_navi) project to [COCO format](https://cocodataset.org/#home) as a **downloadable .tar archive**

Application key points:

- Supports **instances.json** from **COCO** format
- Сonverts **Supervisely** polygons, rectangles, bitmaps to **COCO** polygons and bboxes.
- Allow to export **captions** in COCO format

  👉 To exprot captions you need to create `caption` tag to the project (with `any_string` value type) and assign it to images with caption values.
- ⚠️ Сonverts annotations without preserving holes.
  
  👉 To preserve holes in polygons or export polylines it's best to use [Export to COCO mask](https://ecosystem.supervisely.com/apps/export-to-coco-mask)
- Backward compatible with [Import COCO](https://github.com/supervisely-ecosystem/import-coco)

# How to Use

1. Add [Export to COCO](https://ecosystem.supervisely.com/apps/export-to-coco) to your team from Ecosystem

   <img data-key="sly-module-link" data-module-slug="supervisely-ecosystem/export-to-coco" src="https://github.com/supervisely-ecosystem/export-to-coco/assets/57998637/81341c23-8803-4fc0-85e6-06802b833ec8" width="350px" style='padding-bottom: 20px'/>  

2. Run app from the context menu of **Images Project**:

   <img src="https://github.com/supervisely-ecosystem/export-to-coco/assets/57998637/a2a8a28b-0807-4acd-8ca3-f9d5bddf6756"/>

3. Select options in the modal window and press the **RUN** button

   <img src="https://github.com/supervisely-ecosystem/export-to-coco/assets/57998637/b2f3a25a-c7cb-4ef3-beb6-fbbf438c875a" width=60%/>



# Results

After running the application, you will be redirected to the `Tasks` page. Once application processing has finished, your link for downloading will be available. Click on the `file name` to download it.

<img src="https://github.com/supervisely-ecosystem/export-to-coco/assets/57998637/d07089f6-1ca9-4072-ab54-93c4b62a8392"/>

To explore warnings just open `Log` in the `⋮` menu:

<img src="https://github.com/supervisely-ecosystem/export-to-coco/assets/57998637/7eb775a3-973c-4d6c-be87-dbfcc23922c7">

You can also find your converted project in   
`Team Files` -> `tmp` -> `supervisely` -> `export` -> `export-to-COCO` -> `<taskId>_<projectName>.tar`

<img src="https://github.com/supervisely-ecosystem/export-to-coco/assets/57998637/5f4353b3-bbb4-4d48-87df-77dceaea6d96"/>
