# blender_kitsu
blender-kitsu is a Blender addon to interact with Kitsu from within Blender.

## Features
---------
- Addon preferences to set host, email, password
- 3DView: browsing through kitsu data structure to initialize context
- SequenceEditor: Selection sensitive operators, most of them work on multiple strips:
    - Push thumbnail for shot to kitsu
    - Push metadata for shot to kitsu (shotname, description, frame in, frame out)
    - Push create a new shot to (create)
    - Push delete a shot to kitsu
    - Pull Metadadata of shot from kitsu
    - Debug initialized shots that are not linked yet
    - Debug shots that are linked to multiple sequence strips

## Installation
---------
Download or clone this repository.
In the root project folder you will find the 'blender_kitsu' folder. Place this folder in your Blender addons directory or create a sym link to it.

## Plugins
----------
This project uses gazu as a submodule to interact with the gazu data base.
- gazu doc : https://gazu.cg-wire.com/
- dazu repo: https://github.com/cgwire/gazu

## Development
--------
In the project root you will find a `pyproject.toml` and `peotry.lock` file.
With `poetry` you can easily generate a virtual env for the project which should get you setup quickly.
Basic Usage: https://python-poetry.org/docs/basic-usage/

Create a sym link in your blender addons directory to the blender_kitsu folder.
