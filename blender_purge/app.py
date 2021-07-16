import sys
from pathlib import Path
import subprocess
from typing import Tuple, List, Dict, Any, Union, Optional

from . import vars
from .log import LoggerFactory

logger = LoggerFactory.getLogger()


def exception_handler(func):
    def func_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)

        except ValueError as error:
            logger.info(
                "# Oops. Seems like you gave some wrong input!"
                f"\n# Error: {error}"
                "\n# Program will be cancelled."
            )
            cancel_program()

        except RuntimeError as error:
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


def get_cmd_list(path: Path) -> Tuple[str]:
    cmd_list: Tuple[str] = (
        vars.BLENDER_PATH,
        path.as_posix(),
        "-b",
        "-P",
        f"{vars.PURGE_PATH}",
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


def prompt_confirm(path: Path):
    options = ["yes", "no", "y", "n"]
    input_str = f"\n# Do you want to purge this file {path.as_posix()}? ([y]es/[n]o)"
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
    cmd_list: Tuple[str] = (vars.BLENDER_PATH, "-b", "-P", f"{vars.CHECK_PATH}")
    p = subprocess.Popen(cmd_list)
    return p.wait()


@exception_handler
def purge_file(path: Path) -> int:

    # check if path exists
    if not path.exists():
        raise ValueError(f"Path does not exist: {path.as_posix()}")

    # check if path is blend file
    if not path.is_file():
        raise ValueError(f"Not a file: {path.suffix}")

    # check if path is blend file
    if path.suffix != ".blend":
        raise ValueError(f"Not a blend file: {path.suffix}")

    # promp confirm
    if not prompt_confirm(path):
        cancel_program()

    # perform check of correct preference settings
    return_code = run_check()
    if return_code == 1:
        raise RuntimeError(
            "Override auto resync is turned off. Turn it on in the preferences and try again."
        )

    # get cmd list
    cmd_list = get_cmd_list(path)

    # purge each file two times
    for i in range(vars.PURGE_AMOUNT):
        p = subprocess.Popen(cmd_list, shell=False)

        # stdout, stderr = p.communicate()
        return_code = p.wait()

        if return_code != 0:
            raise RuntimeError("Blender Crashed on file: %s", path.as_posix())

    return 0
