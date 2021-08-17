# blender-purge
blender-purge is a command line tools to purge orphan data of blend files via the console.
## Table of Contents
- [Prerequisite](#prerequisite)
- [Installation](#installation)
- [How to get started](#how-to-get-started)
- [Development](#development)

## Prerequisite
In order to use this tool you need:
- python3
- pip
- svn
## Installation
Download or clone this repository.
This repository is a command line tool that can be installed with the python packaging manager.
In the root of this project you can find a `install.sh` script which simplifies this process on linux.

This script does the following (follow this if you want to do this manually or on another platform):

1. Install pip
2. Open a terminal in the root of the project directory
3. Run `python3 setup.py bdist_wheel` which builds a wheel in ./dist
4. Run `pip3 install dist/<name_of_wheel> --user`

Ensure your $PATH variable contains:

Linux:
- `$HOME/.local/lib/python3.8/site-packages`
- `$HOME/.local/bin`

Windows:
- TODO

Open a new console and write `bpurge` to verify successful install.

## How to get started
After install you can write `bpurge` in to the console.

If you use the tool the first time it will ask you to specify a path to a blender executable and a path to the svn project directory, which will be saved in a configuration file:


Windows:
- `$home/blender-purge/config.json`

Linux/MacOs:
- `$home/.config/blender-purge/config.json`


Give `bpurge` a path to a .blend file or a folder as first argument.
The detected blend files will be opened in the background, their orphan data will be
purged recursively, the file gets saved and closed again. This will happen twice for each .blend file.

You can modify the tool by providing these command line arguments:

- first arguments needs to be a path to a .blend file or a folder

- **-R / --recursive**: If -R is provided in combination with a folder path will perform recursive purge.

- **-N / --nocommit**: If -N is provided there will be no svn commit prompt with the purged files.

- **--regex**: Provide any regex pattern that will be performed on each found filepath with re.search().

- **--yes**: If --yes is provided there will be no confirmation prompt.


## Development
In the project root you will find a `pyproject.toml` and `peotry.lock` file.
With `poetry` you can easily generate a virtual env for the project which should get you setup quickly.
Basic Usage: https://python-poetry.org/docs/basic-usage/
