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
        # Split output in string lines.
        split = output.split("\n")

        # Remove empty lines.
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

        # Assemble path list.
        for idx, line in enumerate(output):
            if not line.startswith("M"):
                continue
            path = Path(line[5:].strip())

            # If no suffix supplied append all files.
            if suffix == ".*":
                path_list.append(path)
            # If suffix supplied only collect files that match.
            else:
                if path.suffix == suffix:
                    path_list.append(path)

        return path_list

    def revert(self, relpath_list: List[Path]) -> subprocess.Popen:
        arg_list = " ".join([p.as_posix() for p in relpath_list])
        process = subprocess.call(
            (f"svn revert {arg_list}"), shell=True, cwd=self._path.as_posix()
        )
        return process

    def revert_all(self) -> None:
        modified = self.get_modified()
        self.revert(modified)

    def commit(self, relpath_list: List[Path]) -> Optional[subprocess.Popen]:
        if not relpath_list:
            return None

        cmd_list = f'svn commit {" ".join([p.as_posix() for p in relpath_list])}'
        process = subprocess.call(cmd_list, shell=True, cwd=self._path.as_posix())
        return process

    def get_untracked(self) -> List[Path]:
        output = self.status()
        if not output:
            return []

        path_list: List[Path] = []

        # Assemble path list.
        for idx, line in enumerate(output):
            if not line.startswith("?"):
                continue
            path = Path(line[5:].strip())
            path_list.append(path)

        return path_list


if __name__ == "__main__":
    # Test status.
    repo = SvnRepo(Path("/media/data/sprites"))
    modified = repo.get_modified()
    print(modified)
    repo.commit(modified[:2])
