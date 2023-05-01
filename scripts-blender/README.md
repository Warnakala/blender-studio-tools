# Blender Add-ons

Most add-ons used in the Blender Studio pipeline.

## blender-kitsu

Add-on used by animation, layout, and editorial department to push video files of shot versions to Kitsu. It also has features that are not directly related to Kitsu but support certain aspects of the Blender Studio Pipeline.

**shot-builder** : tools used by animators or TDs to build .blend files by pulling in shot data from a production's Kitsu database, by linking characters, sets, and props that are used by a given shot. Author: Jeroen Bakker

**anim-setup** : Sub-module that automates the setup of animation within shot_builder. Author: Paul Golter

Author: Paul Golter
Maintainers: Nick Alberelli, Francesco Siddi, Demeter Dzadik


## asset-pipeline

Add-on that manages the Asset Pipeline, used by Modeling, Shading and Rigging departments to be able to work on different aspects of the same asset, primarily characters. Each department works in their own files (char.modeling, char.shading, char.rigging), and push and pull changes from a publish file (char.v001.blend), where all the different data is combined into the final character file.

Most of the actual data transferring code is in a file that is NOT part of the add-on. This file is in the production SVN, under `pro/config/asset_pipeline_config/task_layers.py`.

Author: Paul Golter
Maintainers: Demeter Dzadik, Simon Thommes


## render-review

Add-on to review renders from flamenco with the sequence editor, and push and approve them on Kitsu.

Author: Paul Golter
Maintainer: Demeter Dzadik


## contactsheet

Add-on to create a contactsheet from sequence editor strips.

Author: Paul Golter


## anim-cupboard

Add-on with miscellaneous tools for animators.

Author & Maintainer: Demeter Dzadik


## lighting-overrider

Add-on to create, manage and apply python overrides in a flexible and reliable way as they are used in the lighting process of the Blender Studio pipeline on a shot and sequence level.

Author & Maintainer: Simon Thommes


## blender-svn

Add-on that is intended as a UI for the SVN (Subversion) file versioning system which we use at the studio. Currently doesn't support check-out, but once a check-out is done, it supports all common SVN operations, including resolving conflicts. The currently opened .blend file must be in an SVN repository for the UI to appear.

Author & Maintainer: Demeter Dzadik


## geonode-shapekeys

Add-on used by animators to sculpt on linked and overridden meshes.

Author & Maintainer: Demeter Dzadik


## pose-shape-keys

Add-on used by the rigging department to manage and maintain shapekeys.

Author & Maintainer: Demeter Dzadik


## bone-gizmos

Add-on that attempts to prototype a system for using meshes for the manipulation of armatures. Design task: https://projects.blender.org/blender/blender/issues/92218

Author & Maintainer: Demeter Dzadik


## grease-converter

Add-on that can convert annotations to grease pencil objects and vise versa.

Author: Paul Golter


## cache-manager

Add-on to streamline the alembic cache workflow of assets.

Author: Paul Golter
