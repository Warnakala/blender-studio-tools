# Render Review
Blender Add-on to review renders from Flamenco with the Sequence Editor

## Table of Contents
- [Installation](#installation)
- [Before you get started](#before-you-get-started)
- [Features](#features)

## Installation
1. Download [latest release](../addons/overview) 
2. Launch Blender, navigate to `Edit > Preferences` select `Addons` and then `Install`, 
3. Navigate to the downloaded add-on and select `Install Add-on` 

After install you need to configure the addon in the addon preferences.

## Before you get started

This addon requires a specific folder structure of the rendering pipeline. This structure is defined by <a href="https://flamenco.blender.org">Flamenco</a>

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

## Links

<a href="https://flamenco.blender.org/usage/quickstart/">Flamenco Doc</a>
