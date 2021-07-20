import subprocess
import os
from typing import List, Union, Tuple, Any, Dict
from pathlib import Path


class SvnRepo:
    def __init__(self, path: Path) -> None:
        self._orig_pwd = Path(os.path.abspath(os.getcwd()))
        self._path = path.absolute()

    @property
    def path(self) -> Path:
        return self._path

    def status(self) -> List[str]:
        output = str(
            subprocess.check_output(
                ["svn status"], shell=True, cwd=self._path.as_posix()
            ),
            "utf-8",
        )
        # split output in string lines
        split = output.split("\n")

        # remove empty lines
        while True:
            try:
                split.remove("")
            except ValueError:
                break
        return split

    def get_modified(self) -> List[Path]:
        output = self.status()
        if not output:
            return []

        path_list: List[Path] = []

        # assemble path list
        for idx, line in enumerate(output):
            if not line.startswith("M"):
                continue
            path = Path(line[5:].strip())
            path_list.append(path)

        return path_list

    def revert(self, relpath_list: List[Path]) -> subprocess.Popen:
        relpath_str_list = " ".join([p.as_posix() for p in relpath_list])
        process = subprocess.Popen(
            (f"svn revert {relpath_str_list}"), shell=True, cwd=self._path.as_posix()
        )
        return process

    def revert_all(self) -> None:
        modified = self.get_modified()
        self.revert(modified)

    def commit(self):
        pass
