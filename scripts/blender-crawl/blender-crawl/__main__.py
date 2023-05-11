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
    "path",
    help="Path to a file(s) or folder(s) on which to perform crawl",
    nargs='+'
)

parser.add_argument(
    "--script",
    help="Path to blender python script(s) to execute inside .blend files during crawl. Execution is skipped if no script is provided",
    nargs='+',
)
parser.add_argument(
    "-r",
    "--recursive",
    help="If -R is provided in combination with a folder path will perform recursive crawl",
    action="store_true",
)

parser.add_argument(
    "-f",
    "--filter",
    help="Provide a string to filter the found .blend files", 
)

parser.add_argument(
    "-a",
    "--ask",
    help="If --ask is provided there will be no confirmation prompt before running script on .blend files.",
    action="store_true",
)

parser.add_argument(
    "-p",
    "--purge",
    help="Run 'built-in function to purge data-blocks from all .blend files found in crawl.'.",
    action="store_true",
)

parser.add_argument(
    "--exec",
    help="If --exec user must provide blender executable path, OS default blender will not be used if found.",
    type=str,
)


def cancel_program(message: str):
    print(message)
    sys.exit(0)


def find_executable() -> Path:
    if os.name != 'nt':
        output = subprocess.run(
            ['which', 'blender'], capture_output=True, encoding="utf-8"
        )
        if output.returncode == 0:
            # Returncode includes \n in string to indicate a new line
            return Path(output.stdout.strip('\n'))
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


def is_filepath_blend(path: Path) -> None:
    # Check if path is file.
    if not path.is_file():
        cancel_program(f"Not a file: {path.suffix}")

    # Check if path is blend file.
    if path.suffix != ".blend":
        cancel_program(f"Not a blend file: {path.suffix}")


def check_file_exists(file_path_str: str, error_msg: str):
    if file_path_str is None:
        return
    file_path = Path(file_path_str).absolute()
    if file_path.exists():
        return file_path
    else:
        cancel_program(error_msg)


def get_purge_path(purge: bool):
    # Cancel function if user has not supplied purge arg
    if not purge:
        return
    purge_script = os.path.join(
        Path(__file__).parent.resolve(), "default_scripts", "purge.py"
    )
    return check_file_exists(str(purge_script), "no purge found")


def main() -> int:
    import sys

    # TODO Safely get 'default_purge' path set by setup.py, Debug why this doesn't work
    # module = sys.modules['__main__']
    # https://stackoverflow.com/questions/6028000/how-to-read-a-static-file-from-inside-a-python-package
    # print(pkg_resources.resource_stream("blender-crawl", 'default_purge')) 
    # print(module)
    
    """Crawl blender files in a directory and run a provided scripts"""
    # Parse arguments.
    args = parser.parse_args()    
    purge_path = get_purge_path(args.purge)
    recursive = args.recursive
    exec = args.exec
    regex = args.filter
    script_input = args.script
    ask_for_confirmation = args.ask

    scripts = []
    if script_input:
        for script in script_input:
            script_name = check_file_exists(
            script,
            "No --script was not provided as argument, printed found .blend files, exiting program.",
        )   
            scripts.append(script_name)
                
    # Purge is optional so it can be none
    if purge_path is not None:
        scripts.append(purge_path)
    
    if not exec:
        blender_exec = find_executable()
    else:
        blender_exec = Path(exec).absolute()
        if not blender_exec.exists():
            cancel_program("Blender Executable Path is not valid")

    # Vars.
    files = []
    for item in args.path:
        file_path = Path(item).absolute()
        if not file_path.exists():
            cancel_program(f"Path does not exist: {file_path.as_posix()}")

        # Collect files to crawl
        # if dir.
        if file_path.is_dir():
            if recursive:
                blend_files = [
                    f for f in file_path.glob("**/*") if f.is_file() and f.suffix == ".blend"
                ]
            else:
                blend_files = [
                    f for f in file_path.iterdir() if f.is_file() and f.suffix == ".blend"
                ]
            files.extend(blend_files)
        # If just one file.
        else:
            is_filepath_blend(file_path)
            files.append(file_path)

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
        cancel_program(
            "No valid script files were found. Exiting program."
        )
        sys.exit(0)

    # crawl each file two times.
    for blend_file in files:
        for script in scripts:
            cmd_list = (
            blender_exec.as_posix(),
            blend_file.as_posix(),
            "-b",
            "-P",
            script,
            "--factory-startup",
            )
            process = subprocess.Popen(cmd_list, shell=False)
            if process.wait() != 0:
                cancel_program(f"Blender Crashed on file: {blend_file.as_posix()}")
    return 0

if __name__ == "__main__":
    main()
