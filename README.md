# blezou
Blezou is a Blender addon to interact with the gazou data base from within Blender.

## Features
---------
- Addon preferences to set host, email, password
- 3DView: browsing through gazou data structure to initialize context
- SequenceEditor: set metadata for each sequence strips
- SequenceEditor: sync metadata for sequence strips and update backend (create/update shots)

## Prerequisite
------------
The following tools are needed for installation
- Git

## Installation
---------
This project contains 'gazu' as a git submobule. If you simply download this repo the blezou/gazu folder will be empty.
Because of that the easiest way for now is to clone the repo with the following command to resolve all submodules:

-  ```git clone --recurse-submodules https://gitlab.com/blender/blezou.git```

In the root project folder you will find the 'blezou' folder. Place this folder in your Blender addons directory or create a sym link to it.

## Plugins
----------
This project uses gazu as a submodule to interact with the gazou data base.
- gazu doc : https://gazu.cg-wire.com/
- dazu repo: https://github.com/cgwire/gazu

## Development
--------
In the project root you will find a `pyproject.toml` and `peotry.lock` file.
With `poetry` you can easily generate a virtual env for the project which should get you setup quickly.
Basic Usage: https://python-poetry.org/docs/basic-usage/

Create a sym link in your blender addons directory to the blezou folder.