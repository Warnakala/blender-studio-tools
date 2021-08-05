import re
from typing import Union, Dict, List, Any
import bpy
from render_review import vars


def redraw_ui() -> None:
    """
    Forces blender to redraw the UI.
    """
    for screen in bpy.data.screens:
        for area in screen.areas:
            area.tag_redraw()


def get_version(str_value: str, format: type = str) -> Union[str, int, None]:
    match = re.search(vars.VERSION_PATTERN, str_value)
    if match:
        version = match.group()
        if format == str:
            return version
        if format == int:
            return int(version.replace("v", ""))
    return None
