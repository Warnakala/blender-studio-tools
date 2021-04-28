import os
from pathlib import Path
from typing import Optional

import bpy

from . import prefsdata


class CM_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    cachedir_root: bpy.props.StringProperty(  # type: ignore
        name="cache dir",
        default="//cache",
        options={"HIDDEN", "SKIP_SAVE"},
        subtype="DIR_PATH",
    )

    cacheconfig: bpy.props.StringProperty(
        name="Cachefile", get=prefsdata.get_cacheconfig_file
    )

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        box = layout.box()
        box.row().prop(self, "cachedir_root")

    @property
    def cachedir_path(self) -> Optional[Path]:
        if not self.is_cachedir_valid:
            return None
        return Path(os.path.abspath(bpy.path.abspath(self.cachedir_root)))

    @property
    def is_cachedir_valid(self) -> bool:

        # check if file is saved
        if not self.cachedir_root:
            return False

        if not bpy.data.filepath and self.cachedir_root.startswith("//"):
            return False

        return True

    @property
    def is_cacheconfig_valid(self) -> bool:

        # check if file is saved
        if not self.cacheconfig:
            return False

        if not bpy.data.filepath and self.cacheconfig.startswith("//"):
            return False

        return True

    @property
    def cacheconfig_path(self) -> Optional[Path]:
        if not self.is_cacheconfig_valid:
            return None
        return Path(os.path.abspath(bpy.path.abspath(self.cacheconfig)))


def addon_prefs_get(context: bpy.types.Context) -> bpy.types.AddonPreferences:
    """
    shortcut to get cache_manager addon preferences
    """
    return context.preferences.addons["cache_manager"].preferences


# ---------REGISTER ----------

classes = [CM_AddonPreferences]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
