# Project Description

This project contains add-ons and standalone tools that are used by the Blender Animation Studio.

## blender-kitsu

Add-on used by animation, layout, and editorial department to push video files of shot versions to Kitsu. It also has features that are not directly related to Kitsu but support certain aspects of the Blender Studio Pipeline.

Author: Paul Golter  
Maintainers: Francesco Siddi, Demeter Dzadik

## asset-pipeline

Add-on that manages the Asset Pipeline, used by Modeling, Shading and Rigging departments to be able to work on different aspects of the same asset, primarily characters. Each department works in their own files (char.modeling, char.shading, char.rigging), and push and pull changes from a publish file (char.v001.blend), where all the different data is combined into the final character file.

Most of the actual data transferring code is in a file that is NOT part of the add-on. This file is in the production SVN, under `pro/config/asset_pipeline_config/task_layers.py`.

Author: Paul Golter  
Maintainers: Demeter Dzadik, Simon Thommes

## shot-builder

Add-on used by animators or TDs to build .blend files by pulling in shot data from a production's Kitsu database, by linking characters, sets, and props that are used by a given shot.

Author & Maintainer: Jeroen Bakker

## blender-media-viewer

Blender Application Template that makes Blender usable as a Video-Player, Image and Text-Viewer. We currently use this at the weeklies to present our work every Friday.

Author: Paul Golter  
Maintainers: Francesco Siddi, Demeter Dzadik

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

## freesound-credits
Snippet to generate credits for sounds taken from freesound.org in a VSE sequence.

Author & Maintainer: Francesco Siddi

## grease-converter

Add-on that can convert annotations to grease pencil objects and vise versa.

Author: Paul Golter

## anim-setup

Add-on that automates the setup of animation scenes for the Sprite-Fright project.

Author: Paul Golter

## blender-purge

Command line tool to purge orphan data of many blend files via the console.

Author: Paul Golter

## cache-manager

Add-on to streamline the alembic cache workflow of assets.

Author: Paul Golter