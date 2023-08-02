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

- Supports **instances.json** from **COCO** format
- Сonverts **Supervisely** polygons, rectangles, bitmaps to **COCO** polygons and bboxes.
- <div>⚠️ Сonverts annotations without preserving holes.
  
  👉 To preserve holes in polygones or export polylines it's best to use  [Export to COCO mask](https://ecosystem.supervise.ly/apps/export-to-coco-mask)</div>
- Backward compatible with [Import COCO](https://github.com/supervisely-ecosystem/import-coco)

# How to Use

1. Add [Export to COCO](https://ecosystem.supervise.ly/apps/export-to-coco) to your team from Ecosystem

   <img data-key="sly-module-link" data-module-slug="supervisely-ecosystem/export-to-coco" src="https://github.com/supervisely-ecosystem/export-to-coco/assets/57998637/bfa7283a-9b71-4f88-ae2c-edc63fc848d2" width="350px" style='padding-bottom: 20px'/>  

2. Run app from the context menu of **Images Project**:

   <img src="https://github.com/supervisely-ecosystem/export-to-coco/assets/57998637/a2a8a28b-0807-4acd-8ca3-f9d5bddf6756"/>

3. Select options in the modal window and press the **RUN** button

   <img src="https://github.com/supervisely-ecosystem/export-to-coco/assets/57998637/b2f3a25a-c7cb-4ef3-beb6-fbbf438c875a" width=60%/>



# Results

After running the application, you will be redirected to the `Tasks` page. Once application processing has finished, your link for downloading will be available. Click on the `file name` to download it.

<img src="https://github.com/supervisely-ecosystem/export-to-coco/assets/57998637/d07089f6-1ca9-4072-ab54-93c4b62a8392"/>

To explore warnings just open `Log` in the `⋮` menu:

<img width="724" alt="logs" src="https://github.com/supervisely-ecosystem/export-to-coco/assets/57998637/7eb775a3-973c-4d6c-be87-dbfcc23922c7">

You can also find your converted project in   
`Team Files` -> `tmp` -> `supervisely` -> `export` -> `export-to-COCO` -> `<taskId>_<projectName>.tar`

<img src="https://github.com/supervisely-ecosystem/export-to-coco/assets/57998637/5f4353b3-bbb4-4d48-87df-77dceaea6d96"/>
