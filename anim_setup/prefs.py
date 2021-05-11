import os
from pathlib import Path
from typing import Union, Optional, Any, Dict, Set

import bpy


class AS_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    project_root: bpy.props.StringProperty(  # type: ignore
        name="Project Root",
        default="",
        options={"HIDDEN", "SKIP_SAVE"},
        subtype="DIR_PATH",
    )
    dropbox_root: bpy.props.StringProperty(  # type: ignore
        name="Dropbox Root",
        default="",
        options={"HIDDEN", "SKIP_SAVE"},
        subtype="DIR_PATH",
    )

    def draw(self, context: bpy.types.Context) -> None:
        layout = self.layout
        box = layout.box()
        box.row().prop(self, "project_root")

        if not self.project_root:
            row = box.row()
            row.label(text="Please specify the project root directory.", icon="ERROR")

        if not bpy.data.filepath and self.project_root.startswith("//"):
            row = box.row()
            row.label(
                text="In order to use a relative path as root cache directory the current file needs to be saved.",
                icon="ERROR",
            )

        box.row().prop(self, "dropbox_root")

        if not self.dropbox_root:
            row = box.row()
            row.label(text="Please specify the dropbox root directory.", icon="ERROR")

        if not bpy.data.filepath and self.dropbox_root.startswith("//"):
            row = box.row()
            row.label(
                text="In order to use a relative path as dropbox root directory the current file needs to be saved.",
                icon="ERROR",
            )

    @property
    def project_root_path(self) -> Optional[Path]:
        if not self.is_project_root_valid:
            return None
        return Path(os.path.abspath(bpy.path.abspath(self.project_root)))

    @property
    def is_project_root_valid(self) -> bool:

        # check if file is saved
        if not self.project_root:
            return False

        if not bpy.data.filepath and self.project_root.startswith("//"):
            return False

        return True

    @property
    def dropbox_root_path(self) -> Optional[Path]:
        if not self.is_dropbox_root_valid:
            return None
        return Path(os.path.abspath(bpy.path.abspath(self.dropbox_root)))

    @property
    def is_dropbox_root_valid(self) -> bool:

        # check if file is saved
        if not self.dropbox_root:
            return False

        if not bpy.data.filepath and self.dropbox_root.startswith("//"):
            return False

        return True

    @property
    def is_editorial_valid(self) -> bool:
        if not self.is_dropbox_root_valid:
            return False

        return self.dropbox_root_path.joinpath(
            "shared/sprites/editorial/export"
        ).exists()

    @property
    def editorial_path(self) -> Optional[Path]:
        if not self.is_editorial_valid:
            return None
        return Path(self.dropbox_root_path.joinpath("shared/sprites/editorial/export"))

    @property
    def previs_root_path(self) -> Optional[Path]:
        if not self.is_project_root_valid:
            return None

        previs_path = self.project_root_path / "previz"

        if not previs_path.exists():
            return None

        return previs_path

    @property
    def camera_rig_path(self) -> Optional[Path]:
        if not self.is_project_root_valid:
            return None

        camera_rig_path = self.project_root_path / "pro/lib/cam/camera_rig.blend"

        if not camera_rig_path.exists():
            return None

        return camera_rig_path


def addon_prefs_get(context: bpy.types.Context) -> bpy.types.AddonPreferences:
    """
    shortcut to get cache_manager addon preferences
    """
    return context.preferences.addons["anim_setup"].preferences


# ---------REGISTER ----------

classes = [AS_AddonPreferences]


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
