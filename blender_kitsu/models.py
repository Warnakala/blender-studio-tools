from pathlib import Path
from typing import Union, Optional, Dict, List, Tuple

from .logger import ZLoggerFactory

logger = ZLoggerFactory.getLogger(__name__)


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
