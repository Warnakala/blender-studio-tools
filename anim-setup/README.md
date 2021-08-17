# anim-setup
anim-setup is a Blender Add-on that automates the setup of animation scenes for the Sprite-Fright project.
## Installation
Download or clone this repository.
In the root project folder you will find the 'anim_setup' folder. Place this folder in your Blender addons directory or create a sym link to it.

After install you need to configure the addon in the addon preferences.

## Features
The addon relies on the correct naming of asset and camera actions in the corresponding previs file of the shot.
Check the <a href="https://www.notion.so/Animation-Setup-Checklist-ba4d044ec2354b8baae2b3472b757569"> Animation Setup Checklist</a>.

Operators of the addon:
- Setup Workspace for animation
- Load latest edit from edit export directory
- Import camera action from the previs file
- Import actions for found assets from previs file
- Shift animation of camera and asset actions to start at layout cut in
- Create missing actions for found assets in scene

## Development
In the project root you will find a `pyproject.toml` and `peotry.lock` file.
With `poetry` you can easily generate a virtual env for the project which should get you setup quickly.
Basic Usage: https://python-poetry.org/docs/basic-usage/
