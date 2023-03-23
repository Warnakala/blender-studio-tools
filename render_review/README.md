# render-review
Blender Add-on to review renders from Flamenco with the Sequence Editor

## Table of Contents
- [Installation](#installation)
- [Before you get started](#before-you-get-started)
- [Features](#features)
- [Development](#development)

## Installation
Download or clone this repository.
In the root project folder you will find the 'render_review' folder. Place this folder in your Blender addons directory or create a sym link to it.

After install you need to configure the addon in the addon preferences.

## Before you get started

This addon requires a specific folder structure of the rendering pipeline. This structure is defined by <a href="https://www.flamenco.io">Flamenco</a>

If you have a different folder structure the addon might not work as
expected.

## Features
- Quickly load all versions of a shot or a whole sequence that was rendered with Flamenco in to the Sequence Editor
- Inspect EXR's of selected sequence strip with one click
- Approve render which copies data from the farm_output to the shot_frames folder
- Push a render to the edit which uses the existing .mp4 preview or creates it with ffmpeg
and copies it over to the shot_preview folder with automatic versioning incrementation
- Creation of metadata.json files on approving renders and pushing renders to edit to keep track where a file came from
- Connection to `blender-kitsu` addon, that can be enabled and extends the functionality of some operators
## Development
In the project root you will find a `pyproject.toml` and `peotry.lock` file.
With `poetry` you can easily generate a virtual env for the project which should get you setup quickly.
Basic Usage: https://python-poetry.org/docs/basic-usage/

## Links

<a href="https://www.flamenco.io/docs/">Flamenco Doc</a>
