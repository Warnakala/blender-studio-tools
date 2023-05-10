
# ***** BEGIN GPL LICENSE BLOCK *****
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
# ***** END GPL LICENCE BLOCK *****
#
# (c) 2021, Blender Foundation


import argparse
import sys
import os
import subprocess
import argparse
import json
import re
from pathlib import Path
from typing import Tuple, List, Any

# Command line arguments.
parser = argparse.ArgumentParser()
parser.add_argument(
    "path", help="Path to a file or folder on which to perform crawl", type=str
)

parser.add_argument(
    "script", help="Name of default script like 'crawl' or path to a valid python script file", type=str
)
parser.add_argument(
    "-R",
    "--recursive",
    help="If -R is provided in combination with a folder path will perform recursive crawl",
    action="store_true",
)

parser.add_argument(
    "--regex",
    help="Provide any regex pattern that will be performed on each found filepath with re.search()",
)

parser.add_argument(
    "--yes",
    help="If --yes is provided there will be no confirmation prompt.",
    action="store_true",
)

parser.add_argument(
    "--exec",
    help="If --exec user must provide blender executable path, OS default blender will not be used if found.",
    action="store_true",
)


# MAIN LOGIC
def main():
    args = parser.parse_args()
    run_blender_crawl(args)

def exception_handler(func):
    def func_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)

        except Exception as error:
            print(
                "# Oops. Seems like you gave some wrong input!"
                f"\n# Error: {error}"
                "\n# Program will be cancelled."
            )
            cancel_program
    return func_wrapper


def cancel_program() -> None:
    print("# Exiting blender-crawl")
    sys.exit(0)

def find_default_blender():
    output = subprocess.check_output(['whereis', 'blender'])
    default_blender_str = f'/{str(output).split(" /")[1]}'
    default_blender_binary =  Path(default_blender_str)
    if default_blender_binary.exists():
        return default_blender_binary

def get_blender_path() -> Path:
    config_path = get_config_path()
    json_obj = load_json(config_path)
    return Path(json_obj["blender_path"])


def get_cmd_list(path: Path, script: Path) -> Tuple[str]:
    cmd_list: Tuple[str] = (
        get_blender_path().as_posix(),
        path.as_posix(),
        "-b",
        "-P",
        script,
        "--factory-startup",
    )
    return cmd_list


def validate_user_input(user_input, options):
    if user_input.lower() in options:
        return True
    else:
        return False


def prompt_confirm(path_list: List[Path]):
    options = ["yes", "no", "y", "n"]
    list_str = "\n".join([p.as_posix() for p in path_list])
    noun = "files" if len(path_list) > 1 else "file"
    confirm_str = f"# Do you want to crawl {len(path_list)} {noun}? ([y]es/[n]o)"
    input_str = "# Files to crawl:" + "\n" + list_str + "\n\n" + confirm_str
    while True:
        user_input = input(input_str)
        if validate_user_input(user_input, options):
            if user_input in ["no", "n"]:
                print("\n# Process was canceled.")
                return False
            else:
                return True
        print("\n# Please enter a valid answer!")
        continue


def blender_crawl_file(path: Path, script: Path) -> int:
    # Get cmd list.
    cmd_list = get_cmd_list(path, script)
    p = subprocess.Popen(cmd_list, shell=False)
    # Stdout, stderr = p.communicate().
    return p.wait()


def is_filepath_valid(path: Path) -> None:

    # Check if path is file.
    if not path.is_file():
        raise Exception(f"Not a file: {path.suffix}")

    # Check if path is blend file.
    if path.suffix != ".blend":
        raise Exception(f"Not a blend file: {path.suffix}")


def get_config_path() -> Path:
    home = Path.home()

    if sys.platform == "win32":
        return home / "blender-crawl/config.json"
    elif sys.platform == "linux":
        return home / ".config/blender-crawl/config.json"
    elif sys.platform == "darwin":
        return home / ".config/blender-crawl/config.json"

def load_json(path: Path) -> Any:
    with open(path.as_posix(), "r") as file:
        obj = json.load(file)
    return obj


def save_to_json(obj: Any, path: Path) -> None:
    with open(path.as_posix(), "w") as file:
        json.dump(obj, file, indent=4)


def input_path(question: str) -> Path:
    while True:
        user_input = input(question)
        try:
            path = Path(user_input)
        except:
            print("ERROR:# Invalid input")
            continue
        if path.exists():
            return path.absolute()
        else:
            print("# Path does not exist")


def input_filepath(question: str) -> Path:
    while True:
        path = input_path(question)
        if not path.is_file():
            continue
        return path


def setup_config(find_blender_exec) -> None:
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    default_blender_path = find_default_blender()
    if (not(find_blender_exec) and default_blender_path):
        blender_path = default_blender_path
    else:
        blender_path = input_filepath("# Path to Blender binary: ")   
        
    obj = {
        "blender_path": blender_path.as_posix(),
    }
    save_to_json(obj, config_path)
    print("Updatet config at:  %s", config_path.as_posix())


def is_config_valid() -> bool:
    keys = ["blender_path",]
    config_path = get_config_path()
    json_obj = load_json(config_path)
    for key in keys:
        if key not in json_obj:
            return False
        if not json_obj[key]:
            return False
    return True

def get_default_scipt(script_input:str):
    if script_input == "purge":
        folder = Path(os.path.abspath(__file__)).parent
        default_scripts = folder.joinpath("default_scripts")
        return default_scripts.joinpath("purge.py").absolute()
    return Path(script_input).absolute()

@exception_handler
def run_blender_crawl(args: argparse.Namespace) -> int:

    # Parse arguments.
    path = Path(args.path).absolute()
    script = get_default_scipt(args.script)
    recursive = args.recursive
    find_blender_exec = args.exec
    config_path = get_config_path()
    regex = args.regex
    yes = args.yes

    # Check config file.
    if not config_path.exists() or find_blender_exec:
        print("# Seems like you are starting blender-crawl for the first time!")
        print("# Some things needs to be configured")
        setup_config(find_blender_exec)
    else:
        if not is_config_valid():
            print("# Config file at: %s is not valid", config_path.as_posix())
            print("# Please set it up again")
            setup_config(find_blender_exec)

    # Check user input.
    if not path:
        raise Exception("Please provide a path as first argument")
    
    if not script.exists():
        raise Exception("Please provide a valid python script as second argument")

    if not path.exists():
        raise Exception(f"Path does not exist: {path.as_posix()}")

    # Vars.
    files = []

    # Collect files to crawl
    # if dir.
    if path.is_dir():
        if recursive:
            blend_files = [
                f for f in path.glob("**/*") if f.is_file() and f.suffix == ".blend"
            ]
        else:
            blend_files = [
                f for f in path.iterdir() if f.is_file() and f.suffix == ".blend"
            ]
        files.extend(blend_files)
    # If just one file.
    else:
        is_filepath_valid(path)
        files.append(path)

    # Apply regex.
    if regex:
        to_remove: List[Path] = []
        for p in files:
            match = re.search(regex, p.as_posix())
            if not match:
                to_remove.append(p)

        for p in to_remove:
            files.remove(p)

    # Can only happen on folder here.
    if not files:
        print("# Found no .blend files to crawl")
        cancel_program()

    # Sort.
    files.sort(key=lambda f: f.name)

    # Prompt confirm.
    if not yes:
        if not prompt_confirm(files):
            cancel_program()


    # crawl each file two times.
    CRAWL_AMOUNT = 2 # TODO Figure out why this is here and remove if not needed
    for blend_file in files:
        for i in range(CRAWL_AMOUNT):
            return_code = blender_crawl_file(blend_file, script)
            if return_code != 0:
                raise Exception(
                    f"Blender Crashed on file: {blend_file.as_posix()}",
                )
    return 0


if __name__ == "__main__":
    main()




