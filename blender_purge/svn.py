import subprocess
import os
from typing import List, Union, Tuple, Any, Dict, Optional
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

    def get_modified(self, suffix: str = ".*") -> List[Path]:
        output = self.status()
        if not output:
            return []

        path_list: List[Path] = []

        # assemble path list
        for idx, line in enumerate(output):
            if not line.startswith("M"):
                continue
            path = Path(line[5:].strip())

            # if no suffix supplied append all files
            if suffix == ".*":
                path_list.append(path)
            # if suffix supplied only collect files that match
            else:
                if path.suffix == suffix:
                    path_list.append(path)

        return path_list

    def revert(self, relpath_list: List[Path]) -> subprocess.Popen:
        arg_list = " ".join([p.as_posix() for p in relpath_list])
        process = subprocess.Popen(
            (f"svn revert {arg_list}"), shell=True, cwd=self._path.as_posix()
        )
        return process

    def revert_all(self) -> None:
        modified = self.get_modified()
        self.revert(modified)

    def commit(self, relpath_list: List[Path]) -> Optional[subprocess.Popen]:
        if not relpath_list:
            return None

        base = ["svn commit"]
        base.extend([p.as_posix() for p in relpath_list])
        print(base)
        # base.append('-m "test commit')
        process = subprocess.call(base, shell=True, cwd=self._path.as_posix())
        return process

    def get_untracked(self) -> List[Path]:
        output = self.status()
        if not output:
            return []

        path_list: List[Path] = []

        # assemble path list
        for idx, line in enumerate(output):
            if not line.startswith("?"):
                continue
            path = Path(line[5:].strip())
            path_list.append(path)

        return path_list


if __name__ == "__main__":
    # test status
    repo = SvnRepo(Path("/media/data/sprites"))
    modified = repo.get_modified()
    print(modified)
    repo.commit(modified)
