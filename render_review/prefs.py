import os
import bpy
from pathlib import Path
from typing import Optional, Dict, List

import bpy


class RR_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    farm_output_dir: bpy.props.StringProperty(  # type: ignore
        name="Farm Output Directory",
        default="/render/sprites/farm_output",
        subtype="DIR_PATH",
    )

    frame_storage_dir: bpy.props.StringProperty(  # type: ignore
        name="Frame Storage Directory",
        default="/render/sprites/frame_storage",
        subtype="DIR_PATH",
    )

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        box = layout.box()
        box.label(text="Filepaths", icon="FILEBROWSER")

        # farm outpur dir
        box.row().prop(self, "farm_output_dir")

        if not self.farm_output_dir:
            row = box.row()
            row.label(text="Please specify the Farm Output Directory", icon="ERROR")

        if not bpy.data.filepath and self.farm_output_dir.startswith("//"):
            row = box.row()
            row.label(
                text="In order to use a relative path the current file needs to be saved.",
                icon="ERROR",
            )

        # frame storage dir
        box.row().prop(self, "frame_storage_dir")

        if not self.frame_storage_dir:
            row = box.row()
            row.label(text="Please specify the Frame Storage Directory", icon="ERROR")

        if not bpy.data.filepath and self.frame_storage_dir.startswith("//"):
            row = box.row()
            row.label(
                text="In order to use a relative path the current file needs to be saved.",
                icon="ERROR",
            )

    @property
    def frame_storage_path(self) -> Optional[Path]:
        if not self.is_frame_storage_valid:
            return None
        return Path(os.path.abspath(bpy.path.abspath(self.frame_storage_dir)))

    @property
    def is_frame_storage_valid(self) -> bool:

        # check if file is saved
        if not self.frame_storage_dir:
            return False

        if not bpy.data.filepath and self.frame_storage_dir.startswith("//"):
            return False

        return True

    @property
    def farm_output_path(self) -> Optional[Path]:
        if not self.is_farm_output_valid:
            return None
        return Path(os.path.abspath(bpy.path.abspath(self.farm_output_dir)))

    @property
    def is_farm_output_valid(self) -> bool:

        # check if file is saved
        if not self.farm_output_dir:
            return False

        if not bpy.data.filepath and self.farm_output_dir.startswith("//"):
            return False

        return True


def addon_prefs_get(context: bpy.types.Context) -> bpy.types.AddonPreferences:
    """
    shortcut to get addon preferences
    """
    return context.preferences.addons["render_review"].preferences


# ---------REGISTER ----------

classes = [RR_AddonPreferences]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
