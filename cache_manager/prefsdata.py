from pathlib import Path
from typing import Any


def get_cacheconfig_file(self: Any) -> str:
    if not self.is_cachedir_valid:
        return ""
    return Path(self.cachedir_path).joinpath("cacheconfig").as_posix()
