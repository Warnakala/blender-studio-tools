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

logger = logging.getLogger(__name__)


class AssetPublish:
    def __init__(self, asset_path: Path):
        self._path = asset_path
        self._metadata_path = (
            asset_path.parent / f"{asset_path.name}{constants.METADATA_EXT}"
        )

    @property
    def path(self) -> Path:
        return self._path


def get_asset_disk_name(asset_name: str) -> str:
    """
    Converts Asset Name that is stored on Kitsu to a
    adequate name for the filesystem. Replaces spaces with underscore
    and lowercases all.
    """
    return asset_name.lower().replace(" ", "_")


def get_asset_publishes(asset_dir: Path, asset_name: str) -> List[AssetPublish]:
    # Asset Naming Convention: {asset_name}.{asset_version}.{suffix}
    blend_files = get_files_by_suffix(asset_dir, ".blend")
    asset_publishes: List[AssetPublish] = []

    for file in blend_files:
        file_version = get_file_version(file)
        if not file_version:
            continue

        t = file.stem  # Without suffix
        t = t.replace(f".{file_version}", "")  # Without version string

        # It it matches asset name now, it is an official publish.
        if t != asset_name:
            continue

        asset_publishes.append(AssetPublish(file))

    return asset_publishes


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
