import sys
from pathlib import Path
import subprocess
from typing import Tuple, List, Dict, Any, Union, Optional

from . import vars
from .log import LoggerFactory

logger = LoggerFactory.getLogger()


def cancel_program() -> None:
    logger.info("# Exiting blender-purge")
    sys.exit(0)


def get_cmd_args() -> Tuple[str]:
    cmd_list: Tuple[str] = (
        vars.BLENDER_PATH,
        "-P",
        "-b",
        f"{vars.SCRIPT_PATH}",
        "--log",
        "*overrides*",
        "--log",
        "-level 4",
    )
    return cmd_list


def purge_file(path: Path) -> int:
    cmd_list = get_cmd_args()

    # purge each file two times
    for i in range(2):
        popen = subprocess.Popen(cmd_list, shell=False)
        popen.wait()

    return 0
