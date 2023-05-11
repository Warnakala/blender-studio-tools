
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
import re
from pathlib import Path
from typing import List

# Command line arguments.
parser = argparse.ArgumentParser()
parser.add_argument(
    "path", help="Path to a file or folder on which to perform crawl", type=str,
)

parser.add_argument(
    "--script", help="Path to blender python script to execute inside .blend files during crawl. Execution is skipped if no script is provided", type=str
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
    "--ask",
    help="If --ask is provided there will be no confirmation prompt before running script on .blend files.",
    action="store_true",
)

parser.add_argument(
    "--purge",
    help="Run 'built-in function to purge data-blocks from all .blend files found in crawl.'.",
    action="store_true",
)

parser.add_argument(
    "--exec",
    help="If --exec user must provide blender executable path, OS default blender will not be used if found.", type=str
)



# MAIN LOGIC
def main():
    args = parser.parse_args()
    run_blender_crawl(args)

def cancel_program(message:str):
    print(message)
    sys.exit(0)


def find_executable() -> Path:
    if os.name != 'nt':
        output = subprocess.check_output(['whereis', 'blender']) # TODO Replace with command check syntax
        default_blender_str = f'/{str(output).split(" /")[1]}'
        default_blender_binary =  Path(default_blender_str)
        if default_blender_binary.exists():
            print("Blender Executable location Automatically Detected!")
            return default_blender_binary
    cancel_program("Blender Executable not found please provide --exec argument")

def prompt_confirm(list_length: int):
    file_plural = "files" if list_length > 1 else "file"
    confirm_str = f"Do you want to crawl {list_length} {file_plural}? ([y]es/[n]o)"
    while True:
        user_input = input(confirm_str).lower()
        if not user_input in ["yes", "no", "y", "n"]:
            print("\nPlease enter a valid answer!")
            continue
        if user_input in ["no", "n"]:
            print("\nProcess was canceled.")
            return False
        else:
            return True
        
    


def blender_crawl_file(exec: Path, path: Path, script: Path) -> int:
    # Get cmd list.
    cmd_list = (
        exec.as_posix(),
        path.as_posix(),
        "-b",
        "-P",
        script,
        "--factory-startup",
    )
    p = subprocess.Popen(cmd_list, shell=False)
    return p.wait()


def is_filepath_valid(path: Path) -> None:

    # Check if path is file.
    if not path.is_file():
        cancel_program(f"Not a file: {path.suffix}")

    # Check if path is blend file.
    if path.suffix != ".blend":
        cancel_program(f"Not a blend file: {path.suffix}")



def check_file_exists(file_path_str:str, error_msg:str):
    if file_path_str is None:
        return
    file_path = Path(file_path_str).absolute()
    if file_path.exists():
        return file_path
    else:
        cancel_program(error_msg)

def get_purge_path(purge:bool):
    # Cancel function if user has not supplied purge arg
    if not purge:
        return
    purge_script = os.path.join(Path(__file__).parent.resolve(), "default_scripts", "purge.py")
    return check_file_exists(str(purge_script), "no purge found")

    
def run_blender_crawl(args: argparse.Namespace) -> int:
    # Parse arguments.
    path = Path(args.path).absolute()
    script = check_file_exists(args.script, "No --script was not provided as argument, printed found .blend files, exiting program.")
    purge_path = get_purge_path(args.purge)
    recursive = args.recursive
    exec = args.exec
    regex = args.regex
    ask_for_confirmation = args.ask

    # Collect all possible scripts into list
    scripts = [script for script in [script, purge_path] if script is not None]

    if not path.exists():
        cancel_program(f"Path does not exist: {path.as_posix()}")
    if not exec:
        blende_exec = find_executable()
    else:
        blende_exec = Path(exec).absolute()
    
    if not blende_exec.exists():
        cancel_program("Blender Executable Path is not valid")
        

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
        print(" Found no .blend files to crawl")
        sys.exit(0)

    # Sort.
    files.sort(key=lambda f: f.name)

    for file in files:
        print(f"Found: `{file}`")
    

    if ask_for_confirmation:
        if not prompt_confirm(len(files)):
            sys.exit(0)

    if not scripts:
        cancel_program("No --script was not provided as argument, printed found .blend files, exiting program. BIG")
        sys.exit(0)




    # crawl each file two times.
    for blend_file in files:
        for script in scripts:
            return_code = blender_crawl_file(blende_exec, blend_file, script)
            if return_code != 0:
                cancel_program(f"Blender Crashed on file: {blend_file.as_posix()}")
    return 0


if __name__ == "__main__":
    main()




