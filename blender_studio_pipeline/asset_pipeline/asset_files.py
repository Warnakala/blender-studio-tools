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
# (c) 2021, Blender Foundation - Paul Golter
import re
import logging

from typing import List, Dict, Union, Any, Set, Optional
from pathlib import Path

import bpy

from . import constants

logger = logging.getLogger("BSP")


class AssetFile:
    def __init__(self, asset_path: Path):
        self._path = asset_path
        self._metadata_path = (
            asset_path.parent / f"{asset_path.name}{constants.METADATA_EXT}"
        )

    @property
    def path(self) -> Path:
        return self._path

    def __repr__(self) -> str:
        return self._path.name


class AssetTask(AssetFile):
    """
    Represents a working file.
    """


class AssetPublish(AssetFile):
    """
    Represents a publish file.
    """

    # TODO: overwrite init to load metadata etc.

    pass

    def get_version(self, format: type = str) -> Optional[Union[str, int]]:
        return get_file_version(self.path, format=format)


class AssetDir:
    def __init__(self, path: Path):
        self._path = path
        # Directory name should match asset name
        self._asset_disk_name = path.name

    @property
    def path(self) -> Path:
        return self._path

    @property
    def asset_disk_name(self) -> str:
        return self._asset_disk_name

    @property
    def publish_dir(self) -> Path:
        return self._path / "publish"

    def get_asset_publishes(self) -> List[AssetPublish]:
        # Asset Naming Convention: {asset_name}.{asset_version}.{suffix}
        # TODO: if asset_dir.name == asset.name we could use this logic here
        if not self.publish_dir.exists():
            return []

        blend_files = get_files_by_suffix(self.publish_dir, ".blend")
        asset_publishes: List[AssetPublish] = []

        for file in blend_files:
            file_version = get_file_version(file)
            if not file_version:
                continue

            t = file.stem  # Without suffix
            t = t.replace(f".{file_version}", "")  # Without version string

            # It it matches asset name now, it is an official publish.
            if t != self._asset_disk_name:
                continue

            asset_publishes.append(AssetPublish(file))

        return asset_publishes

    def get_first_publish_path(self) -> Path:
        filename = f"{self.asset_disk_name}.v001.blend"
        return self.publish_dir / filename

    def __repr__(self) -> str:
        publishes = ", ".join(str(a) for a in self.get_asset_publishes())
        return f"{self.asset_disk_name} (Publishes:{str(publishes)})"


def get_asset_disk_name(asset_name: str) -> str:
    """
    Converts Asset Name that is stored on Kitsu to a
    adequate name for the filesystem. Replaces spaces with underscore
    and lowercases all.
    """
    return asset_name.lower().replace(" ", "_")


def get_file_version(path: Path, format: type = str) -> Optional[Union[str, int]]:
    """
    Detects if file has versioning pattern "v000" and returns that version.
    Returns:
        str: if file version exists
        bool: False if no version was detected
    """
    match = re.search("v(\d\d\d)", path.name)
    if not match:
        return None

    version = match.group(0)

    if format == str:
        return version

    elif format == int:
        return int(version.replace("v", ""))

    else:
        raise ValueError(f"Unsupported format {format} expected: int, str.")


def get_files_by_suffix(dir_path: Path, suffix: str) -> List[Path]:
    """
    Returns a list of paths that match the given ext in folder.
    Args:
        ext: String of file extensions eg. ".txt".
    Returns:
        List of Path() objects that match the ext. Returns empty list if no files were found.
    """
    return [p for p in dir_path.iterdir() if p.is_file() and p.suffix == suffix]
