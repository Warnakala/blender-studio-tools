<<<<<<< HEAD
# blender-crawl
blender-crawl is a command line tools to purge orphan data of blend files via the console.

=======
# blender_crawl
`blender_crawl` is a command line tools to crawl directories for .blend files and execute a provied script.
>>>>>>> upstream/main
## Table of Contents
- [Prerequisite](#prerequisite)
- [Installation](#installation)
- [How to get started](#how-to-get-started)

## Prerequisite
In order to use this tool you need:
<<<<<<< HEAD
- python3

## Run without Installation
1. Clone repository
2. run `cd blender-crawl` to enter directory
3. Run program with `python blender-crawl /directory/`
=======
- Python 3.5+

## Run without Installation
1. Clone this repository with `git clone https://projects.blender.org/studio/blender-studio-pipeline.git`
2. Run `cd blender-studio-pipeline/scripts/blender-crawl` to enter directory
3. Run program with `python blender_crawl /my-folder/` 
>>>>>>> upstream/main

## Installation
Download or clone this repository.
This repository is a command line tool that can be installed with the python packaging manager. 
This script does the following (follow this if you want to do this manually or on another platform):

<<<<<<< HEAD
1. Clone repository
2. Run `cd blender-crawl` to enter directory
3. Install with `python setup.py install`
4. Run with `sudo python -m blender-crawl /directory/`
5. Get help with `sudo python3 -m blender-crawl -h`


## How to get started
Run directly out of repo folder or follow above installation instructions.

Give `blender-crawl` a path to a .blend file or a folder as first argument. 
The detected blend files will be opened in the background, their orphan data will be
purged recursively, the file gets saved and closed again. This will happen twice for each .blend file.

If blender is not installed at the default location of your computer, you need to provide a blender executable
using the --exec flag.

 -  --script        Path to blender python script(s) to execute inside .blend files during crawl. Execution is skipped if no script is provided
 -  -r, --recursive       If -R is provided in combination with a folder path will perform recursive crawl
 -  -f  --filter          Provide a string to filter the found .blend files
 -  -a, --ask             If --ask is provided there will be no confirmation prompt before running script on .blend files.
 -  -p, --purge           Run 'built-in function to purge data-blocks from all .blend files found in crawl.'.
 -  --exec EXEC           If --exec user must provide blender executable path, OS default blender will not be used if found.
  -  -h, --help           show the above help message and exit


=======
1. Clone this repository with `git clone https://projects.blender.org/studio/blender-studio-pipeline.git`
2. Run `cd blender-studio-pipeline/scripts/blender-crawl` to enter directory
3. Install with `python setup.py install`
4. Run with `blender_crawl /my-folder/`
5. Get help with `blender_crawl -h`


## How to get started
Run directly out of repo folder or follow above installation instructions. Give `blender_crawl` a path to a .blend file or a folder as first argument, The detected blend files will be opened in the background, the python script will be executed, and the file closes. If blender is not installed at the default location of your computer, you need to provide a blender executable using the --exec flag.

| Command      | Description |
| ----------- | ----------- |
| --script| Path to blender python script(s) to execute inside .blend files during crawl.|
| -r, --recursive| If provided in combination with a folder path will perform recursive crawl|
| -f  --filter| Provide a string to filter the found .blend files|
| -a, --ask| If provided there will be no confirmation prompt before running script on .blend files.|
| -p, --purge| Run 'built-in function to purge data-blocks from all .blend files found in crawl.'.|
| --exec| If provided user must provide blender executable path, OS default blender will not be used if found.|
| -h, --help| show the above help message and exit|


## Usage Examples

| Action | Command |
| ----------- | ----------- |
|Prints the names of .blends in Current Directory  | `blender_crawl ./` |
|Print the names of .blends Recursively | `blender_crawl /my-folder/ --recursive` | 
|Print only the names of .blends matching a provided string |`blender_crawl /my-folder/ --find string`|
|Run default 'Purge' script on .blends in Current Directory |`blender_crawl /my-folder/ --purge`|
|Run custom script on all .blends in Current Directory |`blender_crawl /my-folder/ --script /my-directory/my-script.py`|
|Ask/Prompt before script execution|`blender_crawl /my-folder/ --script /my-directory/my-script.py --ask`|
|Run with a custom blender executable|`blender_crawl /my-folder/ --exec /path-to-blender-executable/blender`|

>>>>>>> upstream/main
