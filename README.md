<div align="center" markdown>
<img src="https://i.imgur.com/wDdLM8H.png"/>


# Export to COCO

<p align="center">
  <a href="#Overview">Overview</a> •
  <a href="#How-To-Use">How To Use</a> •
  <a href="#Results">Results</a>
</p>

[![](https://img.shields.io/badge/supervisely-ecosystem-brightgreen)](https://ecosystem.supervise.ly/apps/supervisely-ecosystem/export-to-coco)
[![](https://img.shields.io/badge/slack-chat-green.svg?logo=slack)](https://supervise.ly/slack)
![GitHub release (latest SemVer)](https://img.shields.io/github/v/release/supervisely-ecosystem/export-to-coco)
[![views](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/export-to-coco&counter=views&label=views)](https://supervise.ly)
[![used by teams](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/export-to-coco&counter=downloads&label=used%20by%20teams)](https://supervise.ly)
[![runs](https://app.supervise.ly/public/api/v3/ecosystem.counters?repo=supervisely-ecosystem/export-to-coco&counter=runs&label=runs&123)](https://supervise.ly)

</div>

# Overview

App converts [Supervisely format](https://docs.supervise.ly/data-organization/00_ann_format_navi) project to [COCO format](https://cocodataset.org/#home) as **downloadable .tar archive**

Application key points:  
- Supports only **Object Detection** from **COCO** format
- Backward compatible with [Import COCO](https://github.com/supervisely-ecosystem/import-coco) (**WIP**)


# How to Use
1. Add [Export to COCO](https://ecosystem.supervise.ly/apps/export-to-coco) to your team from Ecosystem.

<img data-key="sly-module-link" data-module-slug="supervisely-ecosystem/export-to-coco" src="https://imgur.com/XLOsIRN.png" width="350px" style='padding-bottom: 20px'/>  

2. Run app from the context menu of **Images Project**:

<img src="https://imgur.com/Pda1KsZ.png" width="100%"/>

# Results

After running the application, you will be redirected to the `Tasks` page. Once application processing has finished, your link for downloading will be available. Click on the `file name` to download it.

<img src="https://i.imgur.com/4oE9sxi.png"/>

You can also find your converted project in   
`Team Files` -> `Export to COCO` -> `<taskId>_<projectName>.tar`

<img src="https://i.imgur.com/3pDolxh.png"/>
