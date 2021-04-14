import re
from typing import Optional, Union

import bpy

_VERSION_PATTERN = "v\d\d\d"


def get_version(format: type = str) -> Union[str, int, None]:
    if not bpy.data.filepath:
        return None

    match = re.search(_VERSION_PATTERN, bpy.data.filepath)
    if match:
        version = match.group()
        if format == str:
            return version
        if format == int:
            return int(version.replace("v", ""))
    return None


def gen_filename_collection(collection: bpy.types.Collection) -> str:
    return f"{collection.name}.abc"
