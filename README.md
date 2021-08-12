# contactsheet
Blender addon to create a contactsheet from sequence editor strips.

## Installation
Download or clone this repository.
In the root project folder you will find the 'contactsheet' folder. Place this folder in your Blender addons directory or create a symlink to it.

## Features
After the addon is enabled you will find a `Contactsheet` tab in the Sequence Editor Toolbar.
The 'Make Contactsheet' operator creates a temporary scene and arranges the previously selected sequences in a grid.
If no sequences were selected it takes a continuous row of the top most sequences.
The operator name always shows you how many sequences will be used.
You can overwrite the resolution of the contactsheet by adjusting the X and Y sliders.
The number of rows and columns is automatically calculated. It can also be overwritten by toggling the lock button.

## Development
In the project root you will find a `pyproject.toml` and `peotry.lock` file.
With `poetry` you can easily generate a virtual env for the project which should get you setup quickly.
Basic Usage: https://python-poetry.org/docs/basic-usage/

Create a sym link in your Blender addons directory to the contactsheet/contactsheet folder.
