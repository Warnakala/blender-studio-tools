import re

from pathlib import Path
from typing import Union, Optional, Dict, List, Tuple

from blender_kitsu import bkglobals
from blender_kitsu.logger import LoggerFactory

logger = LoggerFactory.getLogger(__name__)


class FolderListModel:
    def __init__(self):
        self.__root_path: Optional[Path] = None
        self.__folders: List[str] = []
        self.__appended: List[str] = []
        self.__combined: List[str] = []

    def rowCount(self) -> int:
        return len(self.__combined)

    def data(self, row: int) -> Optional[str]:
        if len(self.__combined) > 0:
            return self.__combined[row]

        return None

    @property
    def root_path(self) -> Optional[Path]:
        return self.__root_path

    @root_path.setter
    def root_path(self, path: Path) -> None:

        if not path or not path.absolute().exists():
            logger.debug("FolderListModel: Path does not exist: %s", str(path))
            self.reset()
        else:
            self.__root_path = path
            logger.debug("FolderListModel: Root path  was set to %s", path.as_posix())
            self.__load_dir(self.__root_path)

    def reset(self) -> None:
        self.__root_path = None
        self.__folders.clear()
        self.__appended.clear()
        self.__update_combined()

    def reload(self) -> None:
        self.__folders.clear()
        self.__appended.clear()
        self.root_path = self.__root_path

    def __load_dir(self, path: Path) -> None:
        self.__folders = self.__detect_folders(path)
        self.__appended.clear()
        self.__update_combined()

    def __detect_folders(self, path: Path) -> List[str]:
        if path.exists() and path.is_dir():
            # iterate through directory and return all pathes that are dirs, only return their name
            return sorted(
                [str(x.name) for x in path.iterdir() if x.is_dir()], reverse=True
            )
        else:
            return []

    def append_item(self, item: str) -> None:
        self.__appended.append(item)
        self.__update_combined()

    def __update_combined(self) -> None:
        self.__combined.clear()
        self.__combined.extend(
            sorted(list(set(self.__folders + self.__appended)), reverse=True)
        )

    @property
    def items(self) -> List[str]:
        return self.__combined

    @property
    def items_as_enum_list(self) -> List[Tuple[str, str, str]]:
        return [(item, item, "") for item in self.__combined]


class FileListModel:
    def __init__(self):
        self.__root_path: Optional[Path] = None
        self.__files: List[str] = []
        self.__appended: List[str] = []
        self.__combined: List[str] = []

    def rowCount(self) -> int:
        return len(self.__combined)

    def data(self, row: int) -> Optional[str]:
        if len(self.__combined) > 0:
            return self.__combined[row]

        return None

    @property
    def root_path(self) -> Optional[Path]:
        return self.__root_path

    @root_path.setter
    def root_path(self, path: Path) -> None:

        if not path or not path.absolute().exists():
            logger.debug("FileListModel: Path does not exist: %s", str(path))
            self.reset()
        else:
            self.__root_path = path
            # logger.debug("FileListModel: Root path  was set to %s", path.as_posix())
            self.__load_dir(self.__root_path)

    def reset(self) -> None:
        self.__root_path = None
        self.__files.clear()
        self.__appended.clear()
        self.__update_combined()

    def reload(self) -> None:
        self.__files.clear()
        self.__appended.clear()
        self.root_path = self.__root_path

    def __load_dir(self, path: Path) -> None:
        self.__files = self.__detect_files(path)
        self.__appended.clear()
        self.__update_combined()

    def __detect_files(self, path: Path) -> List[str]:
        if path.exists() and path.is_dir():
            # iterate through directory and return all pathes that are files, only return their name
            return sorted(
                [str(x.name) for x in path.iterdir() if x.is_file()], reverse=True
            )
        else:
            return []

    def append_item(self, item: str) -> None:
        self.__appended.append(item)
        self.__update_combined()

    def __update_combined(self) -> None:
        self.__combined.clear()
        self.__combined.extend(
            sorted(list(set(self.__files + self.__appended)), reverse=True)
        )

    @property
    def items(self) -> List[str]:
        return self.__combined

    @property
    def items_as_paths(self) -> List[Path]:
        if not self.__root_path:
            return []
        return [self.__root_path.joinpath(item).absolute() for item in self.items]

    @property
    def items_as_enum_list(self) -> List[Tuple[str, str, str]]:
        return [(item, item, "") for item in self.__combined]

    @property
    def items_as_path_enum_list(self) -> List[Tuple[str, str, str]]:
        return [(item.as_posix(), item.name, "") for item in self.items_as_paths]

    @property
    def versions(self) -> List[str]:
        return [self._get_version(i) for i in self.__combined if self._get_version(i)]

    @property
    def versions_as_enum_list(self) -> List[Tuple[str, str, str]]:
        return [(v, v, "") for v in self.versions]

    def _get_version(self, str_value: str, format: type = str) -> Union[str, int, None]:
        match = re.search(bkglobals.VERSION_PATTERN, str_value)
        if match:
            version = match.group()
            if format == str:
                return version
            if format == int:
                return int(version.replace("v", ""))
        return None
