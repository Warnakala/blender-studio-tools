import sys
import subprocess
import argparse
import json
import re
from pathlib import Path
from typing import Tuple, List, Dict, Any, Union, Optional

from blender_purge import vars
from blender_purge.svn import SvnRepo
from blender_purge.log import LoggerFactory
from blender_purge.exception import SomethingWentWrongException, WrongInputException

logger = LoggerFactory.getLogger()


def exception_handler(func):
    def func_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)

        except WrongInputException as error:
            logger.info(
                "# Oops. Seems like you gave some wrong input!"
                f"\n# Error: {error}"
                "\n# Program will be cancelled."
            )
            cancel_program()

        except SomethingWentWrongException as error:
            logger.info(
                "# Oops. Something went wrong during the execution of the Program!"
                f"\n# Error: {error}"
                "\n# Program will be cancelled."
            )
            cancel_program()

    return func_wrapper


def cancel_program() -> None:
    logger.info("# Exiting blender-purge")
    sys.exit(0)


def get_blender_path() -> Path:
    config_path = get_config_path()
    json_obj = load_json(config_path)
    return Path(json_obj["blender_path"])


def get_project_root_path() -> Path:
    config_path = get_config_path()
    json_obj = load_json(config_path)
    return Path(json_obj["project_root"])


def get_cmd_list(path: Path) -> Tuple[str]:
    cmd_list: Tuple[str] = (
        get_blender_path().as_posix(),
        path.as_posix(),
        "-b",
        "-P",
        f"{vars.PURGE_PATH}",
        "--factory-startup",
    )
    return cmd_list


"""
        "--log",
        "*overrides*",
        "--log",
        "-level 1",
"""


def validate_user_input(user_input, options):
    if user_input.lower() in options:
        return True
    else:
        return False


def prompt_confirm(path_list: List[Path]):
    options = ["yes", "no", "y", "n"]
    list_str = "\n".join([p.as_posix() for p in path_list])
    noun = "files" if len(path_list) > 1 else "file"
    confirm_str = f"# Do you want to purge {len(path_list)} {noun}? ([y]es/[n]o)"
    input_str = "# Files to purge:" + "\n" + list_str + "\n\n" + confirm_str
    while True:
        user_input = input(input_str)
        if validate_user_input(user_input, options):
            if user_input in ["no", "n"]:
                logger.info("\n# Process was canceled.")
                return False
            else:
                return True
        logger.info("\n# Please enter a valid answer!")
        continue


def run_check():
    cmd_list: Tuple[str] = (
        get_blender_path().as_posix(),
        "-b",
        "-P",
        f"{vars.CHECK_PATH}",
    )
    p = subprocess.Popen(cmd_list)
    return p.wait()


def purge_file(path: Path) -> int:
    # get cmd list
    cmd_list = get_cmd_list(path)
    p = subprocess.Popen(cmd_list, shell=False)
    # stdout, stderr = p.communicate()
    return p.wait()


def is_filepath_valid(path: Path) -> None:

    # check if path is file
    if not path.is_file():
        raise WrongInputException(f"Not a file: {path.suffix}")

    # check if path is blend file
    if path.suffix != ".blend":
        raise WrongInputException(f"Not a blend file: {path.suffix}")


def get_config_path() -> Path:
    home = Path.home()

    if sys.platform == "win32":
        return home / "blender-purge/config.json"
    elif sys.platform == "linux":
        return home / ".config/blender-purge/config.json"
    elif sys.platform == "darwin":
        return home / ".config/blender-purge/config.json"


def create_config_file(config_path: Path) -> None:
    if config_path.exists():
        return
    try:
        with open(config_path.as_posix(), "w") as file:
            json.dump({}, file)
    except:
        raise SomethingWentWrongException(
            f"# Something went wrong creating config file at: {config_path.as_posix()}"
        )

    logger.info(f"# Created config file at: {config_path.as_posix()}")


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
            logger.error("# Invalid input")
            continue
        if path.exists():
            return path.absolute()
        else:
            logger.info("# Path does not exist")


def input_filepath(question: str) -> Path:
    while True:
        path = input_path(question)
        if not path.is_file():
            continue
        return path


def setup_config() -> None:
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    blender_path = input_filepath("# Path to Blender binary: ")
    project_root = input_path("# Path to SVN project root: ")
    obj = {
        "blender_path": blender_path.as_posix(),
        "project_root": project_root.as_posix(),
    }
    save_to_json(obj, config_path)
    logger.info("Updatet config at:  %s", config_path.as_posix())


def is_config_valid() -> bool:
    keys = ["blender_path", "project_root"]
    config_path = get_config_path()
    json_obj = load_json(config_path)
    for key in keys:
        if key not in json_obj:
            return False
        if not json_obj[key]:
            return False
    return True


@exception_handler
def purge(args: argparse.Namespace) -> int:

    # parse arguments
    path = Path(args.path).absolute()
    recursive = args.recursive
    config_path = get_config_path()
    no_commit = args.nocommit
    regex = args.regex

    # check config file
    if not config_path.exists():
        logger.info("# Seems like you are starting blender-purge for the first time!")
        logger.info("# Some things needs to be configured")
        setup_config()
    else:
        if not is_config_valid():
            logger.info("# Config file at: %s is not valid", config_path.as_posix())
            logger.info("# Please set it up again")
            setup_config()

    # check user input
    if not path:
        raise WrongInputException("Please provide a path as first argument")

    if not path.exists():
        raise WrongInputException(f"Path does not exist: {path.as_posix()}")

    # vars
    files = []

    # collect files to purge
    # if dir
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
    # if just one file
    else:
        is_filepath_valid(path)
        files.append(path)

    # apply regex
    if regex:
        to_remove: List[Path] = []
        for p in files:
            match = re.search(regex, p.as_posix())
            if not match:
                to_remove.append(p)

        for p in to_remove:
            files.remove(p)

    # can only happen on folder here
    if not files:
        logger.info("# Found no .blend files to purge")
        cancel_program()

    # sort
    files.sort(key=lambda f: f.name)

    # prompt confirm
    if not prompt_confirm(files):
        cancel_program()

    """
    # perform check of correct preference settings
    return_code = run_check()
    if return_code == 1:
        raise SomethingWentWrongException(
            "Override auto resync is turned off. Turn it on in the preferences and try again."
        )
    """

    # purge each file two times
    for blend_file in files:
        for i in range(vars.PURGE_AMOUNT):
            return_code = purge_file(blend_file)
            if return_code != 0:
                raise SomethingWentWrongException(
                    f"Blender Crashed on file: {blend_file.as_posix()}",
                )

    # commit to svn
    if no_commit:
        return 0

    project_root = get_project_root_path()
    svn_repo = SvnRepo(project_root)
    file_rel = [p.relative_to(project_root) for p in files]
    svn_repo.commit(file_rel)
    return 0
