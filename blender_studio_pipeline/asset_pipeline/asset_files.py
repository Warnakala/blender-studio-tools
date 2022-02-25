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
import shutil
import logging

from typing import List, Dict, Union, Any, Set, Optional
from pathlib import Path

import bpy

from . import constants
from .builder import metadata
from .builder.metadata import MetadataTreeAsset

logger = logging.getLogger("BSP")


class FailedToIncrementLatestPublish(Exception):
    pass


class FailedToLoadMetadata(Exception):
    pass


class AssetFile:
    def __init__(self, asset_path: Path):
        self._path = asset_path
        self._metadata_path = (
            asset_path.parent / f"{asset_path.stem}{constants.METADATA_EXT}"
        )
        self._metadata: Optional[MetadataTreeAsset] = None
        self._load_metadata()

    @property
    def path(self) -> Path:
        return self._path

    @property
    def metadata_path(self) -> Path:
        return self._metadata_path

    @property
    def metadata(self) -> MetadataTreeAsset:
        return self._metadata

    def write_metadata(self) -> None:
        metadata.write_asset_metadata_tree_to_file(self.metadata_path, self.metadata)

    def reload_metadata(self) -> None:
        if not self.metadata_path.exists():
            raise FailedToLoadMetadata(
                f"Metadata file does not exist: {self.metadata_path.as_posix()}"
            )
        self._load_metadata()

    @property
    def pickle_path(self) -> Path:
        return self.path.parent / f"{self.path.stem}.pickle"

    def __repr__(self) -> str:
        return self._path.name

    def _load_metadata(self) -> None:
        # Make AssetPublish initializeable even tough
        # metadata file does not exist.
        # Its handy to use this class for in the 'future'
        # existing files, to query paths etc.
        if not self.metadata_path.exists():
            logger.info(
                f"Metadata file does not exist: {self.metadata_path.as_posix()}"
            )
            return

        self._metadata = metadata.load_asset_metadata_tree_from_file(self.metadata_path)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AssetFile):
            raise NotImplementedError()

        return bool(self.path == other.path)

    def __hash__(self) -> int:
        return hash(self.path)


class AssetTask(AssetFile):
    """
    Represents a working file.
    """


class AssetPublish(AssetFile):
    """
    Represents a publish file.
    """

    def get_version(self, format: type = str) -> Optional[Union[str, int]]:
        return get_file_version(self.path, format=format)

    def unlink(self) -> None:
        """
        Caution: This will delete the file and the metadata file of this asset publish on disk.
        """
        self.metadata_path.unlink()
        self.path.unlink()


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

        # Sort asset publishes after their 'version' ascending -> v001, v002, v003
        def get_publish_version(asset_publish: AssetPublish) -> int:
            return asset_publish.get_version(format=int)

        asset_publishes.sort(key=get_publish_version)
        return asset_publishes

    def increment_latest_publish(self) -> AssetPublish:
        asset_publishes = self.get_asset_publishes()
        if not asset_publishes:
            raise FailedToIncrementLatestPublish(
                f"No publishes available in: {self.publish_dir.as_posix()}"
            )

        latest_publish = asset_publishes[-1]
        new_version = f"v{(latest_publish.get_version(format=int)+1):03}"

        # Duplicate blend and metadata file.
        # Have metadata_path first so new_path is the one with .blend.
        for path in [latest_publish.metadata_path, latest_publish.path]:
            new_name = path.name.replace(latest_publish.get_version(), new_version)
            new_path = latest_publish.path.parent / new_name

            if new_path.exists():
                raise FailedToIncrementLatestPublish(
                    f"Already exists: {new_path.as_posix()}"
                )

            shutil.copy(path, new_path)
            logger.info(f"Copied: {path.name} to: {new_path.name}")

        return AssetPublish(new_path)

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
