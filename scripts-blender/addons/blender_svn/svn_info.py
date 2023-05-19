from typing import Tuple
from pathlib import Path
import subprocess

from .threaded.execute_subprocess import execute_command

def get_svn_info(path: Path or str) -> Tuple[str, str]:
    """Use the `svn info` command to get the root dir, the URL, and the relative URL."""
    try:
        dirpath_str = str(Path(path).as_posix())
        svn_info = execute_command(dirpath_str, ["svn", "info"])
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode()
        if "is not a working copy" in error_msg:
            return None, None, None
        elif "E200009" in error_msg:
            # If we're in a folder that wasn't yet added to the repo,
            # try again one folder higher.
            parent = path.parent
            if parent == path:
                return None, None
            svn_info = get_svn_info(path.parent)
        else:
            raise e

    lines = svn_info.split("\n")
    root_dir = lines[1].split("Working Copy Root Path: ")[1]
    # On Windows, for some reason the path has a \r character at the end,
    # which breaks absolutely everything.
    root_dir = root_dir.replace("\r", "")

    full_url = lines[2].split("URL: ")[1]
    relative_url = lines[3].split("Relative URL: ")[1][1:]
    base_url = full_url
    if len(relative_url) > 1:
        base_url = full_url.replace(relative_url, "").strip()

    return root_dir, base_url
