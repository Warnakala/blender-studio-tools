import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple, Any

import bpy

from blender_kitsu.logger import LoggerFactory


logger = LoggerFactory.getLogger(name=__name__)


class KITSU_OT_open_path(bpy.types.Operator):
    """"""

    bl_idname = "kitsu.open_path"
    bl_label = "Open"

    filepath: bpy.props.StringProperty(  # type: ignore
        name="Filepath",
        description="Filepath that will be opened in explorer",
        default="",
    )

    def execute(self, context: bpy.types.Context) -> Set[str]:

        if not self.filepath:
            self.report({"ERROR"}, "Can't open empty path in explorer.")
            return {"CANCELLED"}

        filepath = Path(self.filepath)
        if filepath.is_file():
            filepath = filepath.parent

        if not filepath.exists():
            filepath = self._find_latest_existing_folder(filepath)

        if sys.platform == "darwin":
            subprocess.check_call(["open", filepath.as_posix()])

        elif sys.platform == "linux2" or sys.platform == "linux":
            subprocess.check_call(["xdg-open", filepath.as_posix()])

        elif sys.platform == "win32":
            subprocess.check_call(["explorer", filepath.as_posix()])

        else:
            self.report(
                {"ERROR"}, f"Can't open explorer. Unsupported platform {sys.platform}"
            )
            return {"CANCELLED"}

        return {"FINISHED"}

    def _find_latest_existing_folder(self, path: Path) -> Path:
        if path.exists() and path.is_dir():
            return path
        else:
            return self._find_latest_existing_folder(path.parent)


# ---------REGISTER ----------

classes = [KITSU_OT_open_path]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
